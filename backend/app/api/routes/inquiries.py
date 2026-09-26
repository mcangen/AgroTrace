"""Bandeja de mensajes de compradores.

Los mensajes los crea el pasaporte publico (`routes/passport.py`); aqui solo se
leen y se marcan como leidos, siempre filtrados por las fincas del usuario.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.api.serializers import inquiry_to_out
from app.models import BuyerInquiry, Farm, Product
from app.schemas import InquiryOut

router = APIRouter(prefix="/inquiries", tags=["mensajes"])


def _owned_inquiry_query(user_id: int):
    """Mensajes que pertenecen a lotes de fincas del usuario."""
    return (
        select(BuyerInquiry)
        .join(Product, Product.id == BuyerInquiry.product_id)
        .join(Farm, Farm.id == Product.farm_id)
        .where(Farm.owner_id == user_id)
    )


@router.get("", response_model=list[InquiryOut])
def list_inquiries(
    db: DbSession, user: CurrentUser, unread_only: bool = False
) -> list[InquiryOut]:
    query = (
        _owned_inquiry_query(user.id)
        .options(selectinload(BuyerInquiry.product))
        .order_by(BuyerInquiry.created_at.desc())
    )
    if unread_only:
        query = query.where(BuyerInquiry.read_at.is_(None))
    return [inquiry_to_out(i) for i in db.scalars(query)]


@router.get("/unread-count", response_model=int)
def unread_count(db: DbSession, user: CurrentUser) -> int:
    subquery = _owned_inquiry_query(user.id).where(BuyerInquiry.read_at.is_(None)).subquery()
    return db.scalar(select(func.count()).select_from(subquery)) or 0


@router.post("/{inquiry_id}/read", response_model=InquiryOut)
def mark_read(inquiry_id: int, db: DbSession, user: CurrentUser) -> InquiryOut:
    inquiry = db.scalar(
        _owned_inquiry_query(user.id)
        .where(BuyerInquiry.id == inquiry_id)
        .options(selectinload(BuyerInquiry.product))
    )
    if inquiry is None:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado.")

    if inquiry.read_at is None:
        inquiry.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(inquiry)
    return inquiry_to_out(inquiry)


@router.delete("/{inquiry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inquiry(inquiry_id: int, db: DbSession, user: CurrentUser) -> None:
    inquiry = db.scalar(_owned_inquiry_query(user.id).where(BuyerInquiry.id == inquiry_id))
    if inquiry is None:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado.")
    db.delete(inquiry)
    db.commit()
