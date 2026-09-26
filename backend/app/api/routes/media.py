"""Entrega de archivos subidos (fotos de evidencia).

Sin autenticacion a proposito: estas mismas fotos se muestran en el pasaporte
publico del lote. El nombre del archivo es su huella SHA-256, asi que no es
adivinable y una foto solo se alcanza si alguien ya tiene el enlace.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services import photos as photo_service

router = APIRouter(prefix="/media", tags=["media"])

_EXTENSION_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


@router.get("/photos/{stored_name}")
def get_photo(stored_name: str) -> FileResponse:
    try:
        path = photo_service.photo_path(stored_name)
    except photo_service.PhotoError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not path.is_file():
        raise HTTPException(status_code=404, detail="Foto no encontrada.")

    media_type = _EXTENSION_MEDIA_TYPES.get(path.suffix.lower(), "application/octet-stream")
    return FileResponse(
        path,
        media_type=media_type,
        # El contenido es inmutable: el nombre del archivo es su propio hash.
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
