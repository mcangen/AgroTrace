"""Tokens de recuperacion de contrasena: un solo uso, expiran en una hora.

El token crudo solo existe en el enlace que recibe el usuario por correo; en
la base solo se guarda su huella SHA-256 (`models.PasswordResetToken`).
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import PasswordResetToken, User

TOKEN_TTL = timedelta(hours=1)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _aware(dt: datetime) -> datetime:
    """SQLite no guarda el offset de zona horaria: un `datetime` que vuelve de
    la base llega "naive" aunque se haya escrito en UTC. Como todo en esta app
    se escribe con `datetime.now(timezone.utc)`, es seguro asumir UTC al
    releerlo -- sin esto, compararlo con un `now()` aware lanza TypeError."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def create_reset_token(db: Session, user: User) -> str:
    """Genera un token nuevo e invalida cualquier otro que siguiera vigente.

    Asi no quedan varios enlaces de recuperacion validos al mismo tiempo si el
    usuario pidio el correo mas de una vez.
    """
    now = datetime.now(timezone.utc)
    pending = db.scalars(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
    )
    for old in pending:
        old.used_at = now

    raw_token = secrets.token_urlsafe(32)
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=_hash(raw_token),
            expires_at=now + TOKEN_TTL,
        )
    )
    return raw_token


def consume_reset_token(db: Session, raw_token: str) -> User | None:
    """Valida el token y lo marca usado. None si es invalido, vencido o repetido."""
    now = datetime.now(timezone.utc)
    record = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == _hash(raw_token))
    )
    if record is None or record.used_at is not None or _aware(record.expires_at) <= now:
        return None

    record.used_at = now
    return db.get(User, record.user_id)
