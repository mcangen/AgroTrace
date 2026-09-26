"""Registro, inicio de sesion y perfil del usuario."""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User, UserRole
from app.schemas import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenOut,
    UserOut,
)
from app.services import email as email_service
from app.services import password_reset

log = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue(user: User) -> TokenOut:
    token = create_access_token(str(user.id), extra={"email": user.email})
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession) -> TokenOut:
    email = payload.email.lower().strip()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una cuenta con ese correo.",
        )

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        role=UserRole.FARMER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    # La cuenta nace sin finca a proposito: crearla es el primer paso de la
    # guia de bienvenida en el panel, no algo que se genera en su nombre.
    return _issue(user)


@router.post("/login", response_model=TokenOut)
def login(payload: LoginRequest, db: DbSession) -> TokenOut:
    user = db.scalar(select(User).where(User.email == payload.email.lower().strip()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contrasena incorrectos.",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cuenta desactivada.")
    return _issue(user)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


_GENERIC_FORGOT_MESSAGE = (
    "Si ese correo tiene una cuenta, enviamos instrucciones para restablecer la contraseña."
)


def _send_reset_email(to: str, full_name: str, raw_token: str) -> None:
    link = f"{settings.public_web_url.rstrip('/')}/restablecer?token={raw_token}"
    email_service.send(
        to=to,
        subject="Restablecer tu contraseña · AgroTrace",
        text_body=(
            f"Hola {full_name},\n\n"
            "Recibimos una solicitud para restablecer tu contraseña de AgroTrace.\n"
            f"Abre este enlace para elegir una nueva (vence en 1 hora):\n{link}\n\n"
            "Si no fuiste tú, ignora este correo: tu contraseña actual sigue funcionando."
        ),
    )


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
def forgot_password(
    payload: ForgotPasswordRequest, background: BackgroundTasks, db: DbSession
) -> dict[str, str]:
    """Siempre responde igual, exista o no la cuenta: evita que alguien use
    este endpoint para averiguar qué correos están registrados."""
    user = db.scalar(select(User).where(User.email == payload.email.lower().strip()))
    if user is not None and user.is_active:
        raw_token = password_reset.create_reset_token(db, user)
        db.commit()
        background.add_task(_send_reset_email, user.email, user.full_name, raw_token)
    return {"message": _GENERIC_FORGOT_MESSAGE}


@router.post("/reset-password", response_model=TokenOut)
def reset_password(payload: ResetPasswordRequest, db: DbSession) -> TokenOut:
    user = password_reset.consume_reset_token(db, payload.token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El enlace no es válido o ya expiró. Solicita uno nuevo.",
        )
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    db.refresh(user)
    # Deja al usuario con sesión iniciada: acaba de demostrar control del correo.
    return _issue(user)
