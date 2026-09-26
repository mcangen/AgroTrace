"""Punto de entrada de la API de AgroTrace."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.api.routes import api_router
from app.core.config import BACKEND_DIR, settings
from app.db.session import Base, SessionLocal, engine

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)-7s %(name)s: %(message)s"
)
log = logging.getLogger("agrotrace")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Importar los modelos registra las tablas en el metadata antes de crearlas.
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    if settings.seed_demo:
        from app.db.seed import seed_demo

        with SessionLocal() as db:
            seed_demo(db)

    from app.ai.client import gemini

    status = gemini.status()
    if status["enabled"]:
        log.info("IA activa: %s (%s)", status["model"], status["backend"])
    else:
        log.warning("IA en modo respaldo: %s", status["reason"])

    yield


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description=(
        "Trazabilidad agricola verificable con cadena de hashes SHA-256 y "
        "agentes de IA sobre Gemini."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health", tags=["sistema"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


# --- Frontend --------------------------------------------------------------
# En produccion, un solo servicio sirve API + frontend: evita CORS entre
# dominios y no hay que cablear una URL de backend en el build del frontend.
# Si `frontend/dist` no existe (desarrollo local con `npm run dev` en su propio
# puerto, o un backend que todavia no tiene el build), esto simplemente no se
# registra y el backend sigue funcionando solo como API.
FRONTEND_DIST = (BACKEND_DIR.parent / "frontend" / "dist").resolve()

if FRONTEND_DIST.is_dir():
    log.info("Sirviendo el build del frontend desde %s", FRONTEND_DIST)

    # DEBE quedar registrada al final: Starlette prueba las rutas en el orden
    # en que se agregaron, y las de settings.api_prefix ya se registraron
    # arriba, asi que siempre ganan para las peticiones que si les pertenecen.
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        # Una ruta /api/... que no matcheo ningun endpoint real es un 404 de
        # la API, no la pagina principal del frontend.
        if full_path.startswith(settings.api_prefix.lstrip("/") + "/") or full_path == settings.api_prefix.lstrip("/"):
            return JSONResponse({"detail": "No encontrado."}, status_code=404)

        candidate = (FRONTEND_DIST / full_path).resolve()
        # .resolve() ya colapsa cualquier "..", pero se verifica explicitamente
        # que el resultado siga dentro de FRONTEND_DIST antes de servirlo.
        if candidate.is_file() and FRONTEND_DIST in (candidate, *candidate.parents):
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    log.info(
        "No hay build del frontend en %s; este backend sirve solo la API.",
        FRONTEND_DIST,
    )
