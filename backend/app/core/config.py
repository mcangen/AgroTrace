"""Configuracion central de la aplicacion, leida del entorno o de `.env`."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_prefix="AGROTRACE_",
        extra="ignore",
    )

    app_name: str = "AgroTrace API"
    api_prefix: str = "/api/v1"
    environment: str = "development"

    secret_key: str = "dev-only-change-me"
    access_token_ttl_minutes: int = 60 * 24 * 7

    database_url: str = f"sqlite:///{(BACKEND_DIR / 'agrotrace.db').as_posix()}"
    # NoDecode evita que pydantic-settings intente leer la variable como JSON:
    # queremos aceptar la forma comoda "a,b,c" en el .env.
    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    public_web_url: str = "http://localhost:5173"

    # Gemini / Vertex AI.
    # GEMINI_API_KEY es el nombre que usan el SDK y la documentacion de Google, y
    # va sin el prefijo AGROTRACE_. Un validation_alias explicito es lo que hace
    # que pydantic-settings lo busque tal cual, saltandose el env_prefix: sin
    # esto la clave del .env se ignora en silencio.
    gemini_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "GEMINI_API_KEY",
            "GOOGLE_API_KEY",
            "AGROTRACE_GEMINI_API_KEY",
        ),
    )
    # `gemini-flash-latest` es un alias que Google mantiene apuntando al ultimo
    # flash estable; evita que la app se rompa cuando retiran una version
    # concreta, que es justo lo que paso con gemini-2.5-flash.
    gemini_model: str = "gemini-flash-latest"
    gemini_model_pro: str = "gemini-pro-latest"
    # Si el modelo principal da un error transitorio (503 por demanda, 429 por
    # cuota), se reintenta y despues se cae a este, mas pequeno y con mas holgura.
    gemini_model_fallback: str = "gemini-3.1-flash-lite"
    gemini_max_retries: int = 3
    # Tope por llamada individual y presupuesto total de la operacion completa
    # (todos los reintentos y ambos modelos). Sin el segundo, una caida del
    # servicio dejaria la peticion HTTP colgada varios minutos.
    gemini_timeout_seconds: int = 20
    gemini_deadline_seconds: int = 45
    use_vertex: bool = False
    gcp_project: str = ""
    gcp_location: str = "us-central1"

    # Correo saliente (notificaciones de mensajes de compradores, recuperar
    # contrasena). Sin `smtp_host` la app sigue funcionando: los correos se
    # registran en el log en vez de enviarse, igual que Gemini cae a un
    # respaldo cuando no hay API key.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "AgroTrace <no-responder@agrotrace.local>"
    smtp_use_tls: bool = True

    seed_demo: bool = True

    # Almacenamiento de fotos compatible con S3 (Cloudflare R2 recomendado: capa
    # gratuita real, sin costo de egreso). Sin `s3_bucket` configurado, las fotos
    # se guardan en disco local (`backend/uploads/`) -- funciona bien para
    # desarrollo, pero la mayoria de plataformas en la nube borran ese disco en
    # cada despliegue, asi que produccion necesita esto configurado.
    s3_endpoint_url: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_bucket: str = ""
    s3_region: str = "auto"
    # URL publica desde la que se sirven los objetos (el dominio r2.dev del
    # bucket, o un dominio propio conectado a el).
    s3_public_base_url: str = ""

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("database_url", mode="after")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        """Render (y varias plataformas) entregan `postgres://`, pero
        SQLAlchemy 2.x con el driver psycopg3 espera `postgresql+psycopg://`.
        Normalizarlo aqui evita tener que acordarse de arreglarlo a mano en
        cada variable de entorno de cada plataforma."""
        if value.startswith("postgres://"):
            return "postgresql+psycopg://" + value[len("postgres://") :]
        if value.startswith("postgresql://"):
            return "postgresql+psycopg://" + value[len("postgresql://") :]
        return value

    @property
    def ai_enabled(self) -> bool:
        """True cuando hay credenciales suficientes para llamar al modelo."""
        if self.use_vertex:
            return bool(self.gcp_project)
        return bool(self.gemini_api_key)

    @property
    def email_enabled(self) -> bool:
        return bool(self.smtp_host)

    @property
    def s3_enabled(self) -> bool:
        return bool(
            self.s3_endpoint_url
            and self.s3_access_key_id
            and self.s3_secret_access_key
            and self.s3_bucket
            and self.s3_public_base_url
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
