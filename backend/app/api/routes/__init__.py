"""Ensamblado de los routers de la version 1 de la API."""

from fastapi import APIRouter

from app.api.routes import (
    ai,
    auth,
    certification,
    dashboard,
    directory,
    farms,
    inquiries,
    media,
    passport,
    products,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(farms.router)
api_router.include_router(products.router)
api_router.include_router(dashboard.router)
api_router.include_router(ai.router)
api_router.include_router(certification.router)
api_router.include_router(inquiries.router)
api_router.include_router(media.router)
api_router.include_router(directory.router)
api_router.include_router(passport.router)

__all__ = ["api_router"]
