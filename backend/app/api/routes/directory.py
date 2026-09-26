"""Directorio publico de productores.

Lista los lotes que sus dueños marcaron explicitamente como visibles (opt-in,
por lote -- `Product.directory_listed`). Sin autenticacion: es la puerta de
entrada para un comprador que no tiene el QR de un lote en particular.
"""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.api.serializers import directory_entry_to_out
from app.models import Product, ProductPassport, TraceEvent
from app.schemas import DirectoryEntryOut

router = APIRouter(prefix="/public/directory", tags=["directorio publico"])


@router.get("", response_model=list[DirectoryEntryOut])
def list_directory(db: DbSession) -> list[DirectoryEntryOut]:
    products = db.scalars(
        select(Product)
        .where(Product.directory_listed.is_(True))
        .join(ProductPassport, isouter=True)
        .options(
            selectinload(Product.farm),
            selectinload(Product.passport),
            selectinload(Product.events).selectinload(TraceEvent.photos),
        )
        .order_by(ProductPassport.reputation_score.desc().nulls_last(), Product.created_at.desc())
    )
    return [directory_entry_to_out(p) for p in products]
