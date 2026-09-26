"""Almacenamiento de fotos de evidencia.

Dos backends posibles, elegidos automaticamente segun la configuracion:

- **Local** (por defecto): los archivos viven en disco (`backend/uploads/`).
  Perfecto para desarrollo, pero la mayoria de plataformas en la nube borran
  ese disco en cada despliegue -- no sirve para produccion sin un volumen
  persistente.
- **S3-compatible** (si `settings.s3_enabled`): sube a un bucket compatible con
  S3 (Cloudflare R2 es la recomendacion, por su capa gratuita real sin costo de
  egreso) y la foto se sirve directo desde ahi, sin pasar por este backend.

En ambos casos, lo que vive en la base es la huella SHA-256 de la foto, que
ademas se sella dentro del payload del evento -- ver `services/trace.py`. El
nombre/clave del archivo es esa misma huella, no el nombre original que mando
el navegador: evita colisiones, evita traversal de rutas, y hace que subir dos
veces la misma foto no duplique nada.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from app.core.config import BACKEND_DIR, settings

UPLOAD_DIR = BACKEND_DIR / "uploads"
S3_PREFIX = "photos"

# Solo formatos de imagen que un navegador muestra sin plugins. Nada de SVG:
# puede traer scripts embebidos y se sirve desde nuestro propio dominio.
ALLOWED_CONTENT_TYPES: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAX_BYTES = 8 * 1024 * 1024  # 8 MB: suficiente para una foto de celular


class PhotoError(ValueError):
    """Problema con el archivo recibido (tipo, tamano o contenido). Se
    traduce a un 400 en la API -- nunca un fallo de la infraestructura de
    almacenamiento, esos se dejan propagar como error de servidor."""


def ensure_upload_dir() -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    return UPLOAD_DIR


def store_photo(content: bytes, content_type: str) -> tuple[str, str]:
    """Guarda la imagen y devuelve (sha256, nombre_o_clave).

    Lanza `PhotoError` si el tipo no esta permitido, si excede el tamano
    maximo o si el contenido no es realmente una imagen.
    """
    if content_type not in ALLOWED_CONTENT_TYPES:
        permitidos = ", ".join(sorted(ALLOWED_CONTENT_TYPES))
        raise PhotoError(f"Formato no permitido. Usa uno de: {permitidos}.")

    if not content:
        raise PhotoError("El archivo llego vacio.")

    if len(content) > MAX_BYTES:
        mb = len(content) / (1024 * 1024)
        raise PhotoError(f"La imagen pesa {mb:.1f} MB; el maximo son 8 MB.")

    _assert_is_real_image(content)

    digest = hashlib.sha256(content).hexdigest()
    stored_name = f"{digest}{ALLOWED_CONTENT_TYPES[content_type]}"

    if settings.s3_enabled:
        _store_photo_s3(content, content_type, stored_name)
    else:
        _store_photo_local(content, stored_name)

    return digest, stored_name


def _store_photo_local(content: bytes, stored_name: str) -> None:
    ensure_upload_dir()
    path = UPLOAD_DIR / stored_name
    if not path.exists():  # misma foto subida dos veces: no se reescribe
        path.write_bytes(content)


def _s3_client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        region_name=settings.s3_region,
    )


def _store_photo_s3(content: bytes, content_type: str, stored_name: str) -> None:
    from botocore.exceptions import ClientError

    client = _s3_client()
    key = f"{S3_PREFIX}/{stored_name}"

    try:
        client.head_object(Bucket=settings.s3_bucket, Key=key)
        return  # el objeto ya existe con esa clave (= su propio hash): no se resube
    except ClientError as exc:
        status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        if status != 404:
            raise  # error real (credenciales, red, permisos) -- no ocultarlo como 400

    client.put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=content,
        ContentType=content_type,
        CacheControl="public, max-age=31536000, immutable",
    )


def _assert_is_real_image(content: bytes) -> None:
    """No basta con confiar en el content-type que declara el navegador."""
    try:
        from io import BytesIO

        from PIL import Image

        with Image.open(BytesIO(content)) as image:
            image.verify()
    except PhotoError:
        raise
    except Exception as exc:
        raise PhotoError("El archivo no es una imagen valida.") from exc


def stored_name_for(sha256: str, content_type: str) -> str:
    """Reconstruye el nombre/clave a partir de lo que si guarda la base.

    Asi no hace falta una columna extra: es determinista.
    """
    return f"{sha256}{ALLOWED_CONTENT_TYPES.get(content_type, '.jpg')}"


def photo_url(sha256: str, content_type: str) -> str:
    """URL publica desde la que se sirve la foto.

    Si hay almacenamiento S3-compatible configurado, apunta directo al bucket
    (sin pasar por este backend). Si no, apunta a la ruta local que sirve
    `api/routes/media.py`.
    """
    stored_name = stored_name_for(sha256, content_type)
    if settings.s3_enabled:
        return f"{settings.s3_public_base_url.rstrip('/')}/{S3_PREFIX}/{stored_name}"
    return f"/api/v1/media/photos/{stored_name}"


def photo_path(stored_name: str) -> Path:
    """Ruta en disco de una foto guardada localmente.

    `stored_name` siempre lo genera `store_photo` (hash + extension), pero se
    valida igual antes de tocar el sistema de archivos: nunca se confia en un
    nombre que pudo llegar desde fuera.
    """
    candidate = (UPLOAD_DIR / stored_name).resolve()
    if candidate.parent != UPLOAD_DIR.resolve():
        raise PhotoError("Ruta de archivo invalida.")
    return candidate


def verify_stored_photo(stored_name: str, expected_sha256: str) -> bool:
    """True si el archivo guardado todavia coincide con la huella sellada.

    En modo S3 se asume True sin verificar: la clave del objeto ES su propio
    hash (misma convencion "escribir una vez" que en local), asi que sustituir
    el contenido sin cambiar la clave requiere credenciales del bucket, no solo
    acceso al disco -- y re-descargar cada foto en cada vista para verificarla
    seria lento y costoso en trafico. El chequeo real de "el archivo en disco
    coincide con lo sellado" solo tiene sentido, y solo se hace, en modo local.
    """
    if settings.s3_enabled:
        return True

    try:
        path = photo_path(stored_name)
    except PhotoError:
        return False
    if not path.is_file():
        return False
    return hashlib.sha256(path.read_bytes()).hexdigest() == expected_sha256
