"""Motor de base de datos y dependencia de sesion."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# check_same_thread solo aplica a SQLite, donde FastAPI atiende desde varios hilos.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    future=True,
    # Un Postgres administrado (Render, Neon, etc.) puede cerrar conexiones
    # ociosas por su cuenta; sin esto, la primera consulta despues de un rato
    # de inactividad fallaria con "connection already closed" en vez de que
    # el pool detecte la conexion muerta y abra una nueva. No afecta a SQLite.
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
