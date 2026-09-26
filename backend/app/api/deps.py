"""Dependencias compartidas por los routers: autenticacion y control de acceso."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Farm, Product, User

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ] = None,
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales invalidas o sesion expirada.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    payload = decode_access_token(credentials.credentials)
    if not payload or not payload.get("sub"):
        raise unauthorized

    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise unauthorized from None

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def owned_farm(db: Session, user: User, farm_id: int) -> Farm:
    """Devuelve la finca solo si pertenece al usuario autenticado."""
    farm = db.scalar(select(Farm).where(Farm.id == farm_id, Farm.owner_id == user.id))
    if farm is None:
        raise HTTPException(status_code=404, detail="Finca no encontrada.")
    return farm


def owned_product(db: Session, user: User, product_id: int) -> Product:
    """Devuelve el producto solo si su finca pertenece al usuario autenticado."""
    product = db.scalar(
        select(Product).join(Farm).where(Product.id == product_id, Farm.owner_id == user.id)
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado.")
    return product
