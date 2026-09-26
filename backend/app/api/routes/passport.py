"""Pasaporte publico del producto: lo que ve quien escanea el QR.

Sin autenticacion a proposito. Expone solo campos publicables: nada de correos,
identificadores internos de usuario ni datos de la cuenta.
"""

from __future__ import annotations

import json
import time

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.api.serializers import certification_badge_to_out, event_to_out
from app.core.config import settings
from app.models import BuyerInquiry, CertificationAssessment, CertificationStandard, Farm, Product
from app.schemas import InquiryCreate, PassportOut, VerificationOut
from app.services import email as email_service
from app.services import trace
from app.services.certification_data import CERT_STANDARDS
from app.services.qr import passport_qr_png

router = APIRouter(prefix="/public/passport", tags=["pasaporte publico"])

# Freno basico anti-spam para el unico endpoint que escribe sin sesion.
# En memoria del proceso: suficiente para un despliegue de una instancia; si
# esto crece a varias replicas hay que moverlo a Redis o a un rate limiter real.
_INQUIRY_WINDOW_SECONDS = 3600
_INQUIRY_MAX_PER_WINDOW = 5
_inquiry_hits: dict[str, list[float]] = {}


def _check_inquiry_rate(ip: str) -> None:
    now = time.monotonic()
    hits = [t for t in _inquiry_hits.get(ip, []) if now - t < _INQUIRY_WINDOW_SECONDS]
    if len(hits) >= _INQUIRY_MAX_PER_WINDOW:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados mensajes desde esta conexion. Intentalo mas tarde.",
        )
    hits.append(now)
    _inquiry_hits[ip] = hits


def _published_badges(db: DbSession, product: Product) -> list:
    """Insignias de certificacion que el productor eligio publicar.

    Por cada estandar publicado, se muestra el intento MAS RECIENTE (no uno
    fijo): asi si el productor repite el diagnostico y mejora su puntaje, el
    pasaporte se actualiza solo, sin que tenga que volver a publicar.
    """
    standards_raw = json.loads(product.published_certification_standards or "[]")
    if not standards_raw:
        return []

    badges = []
    for raw in standards_raw:
        try:
            standard = CertificationStandard(raw)
        except ValueError:
            continue
        assessment = db.scalar(
            select(CertificationAssessment)
            .where(
                CertificationAssessment.product_id == product.id,
                CertificationAssessment.standard == standard,
            )
            .order_by(CertificationAssessment.created_at.desc())
            .limit(1)
        )
        if assessment is not None:
            badges.append(certification_badge_to_out(assessment, CERT_STANDARDS[standard]))
    return badges


@router.get("/{public_id}", response_model=PassportOut)
def get_passport(public_id: str, db: DbSession) -> PassportOut:
    product = db.scalar(
        select(Product)
        .where(Product.public_id == public_id)
        .options(selectinload(Product.farm), selectinload(Product.passport))
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Pasaporte no encontrado.")

    passport = product.passport
    events = trace.list_events(db, product.id)

    return PassportOut(
        public_id=product.public_id,
        product_name=product.name,
        variety=product.variety,
        farm_name=product.farm.name,
        owner_name=product.farm.owner_name,
        location=product.farm.location,
        altitude_m=product.farm.altitude_m,
        status=product.status,
        planting_date=product.planting_date,
        harvest_date=product.harvest_date,
        story_es=passport.story_es if passport else None,
        story_en=passport.story_en if passport else None,
        export_title_es=passport.export_title_es if passport else None,
        export_title_en=passport.export_title_en if passport else None,
        export_body_es=passport.export_body_es if passport else None,
        export_body_en=passport.export_body_en if passport else None,
        tasting_notes=passport.tasting_notes if passport else None,
        reputation_score=passport.reputation_score if passport else 4.0,
        ai_model=passport.ai_model if passport else None,
        ai_generated_at=passport.ai_generated_at if passport else None,
        events=[event_to_out(e, verify_photos=True) for e in events],
        verification=VerificationOut(**trace.verify_chain(db, product.id)),
        qr_url=f"/api/v1/public/passport/{product.public_id}/qr.png",
        certifications=_published_badges(db, product),
    )


@router.get("/{public_id}/qr.png", response_class=Response)
def get_passport_qr(public_id: str, db: DbSession) -> Response:
    exists = db.scalar(select(Product.id).where(Product.public_id == public_id))
    if not exists:
        raise HTTPException(status_code=404, detail="Pasaporte no encontrado.")
    return Response(
        content=passport_qr_png(public_id),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"},
    )


def _send_inquiry_email(to: str, buyer_name: str, buyer_country: str | None,
                         product_name: str, message: str) -> None:
    inbox_link = f"{settings.public_web_url.rstrip('/')}/panel/mensajes"
    origen = f" ({buyer_country})" if buyer_country else ""
    email_service.send(
        to=to,
        subject=f"Nuevo mensaje sobre {product_name} · AgroTrace",
        text_body=(
            f"{buyer_name}{origen} te escribió desde el pasaporte público de "
            f"«{product_name}»:\n\n"
            f'"{message}"\n\n'
            f"Responde desde tu bandeja de mensajes: {inbox_link}"
        ),
    )


@router.post("/{public_id}/contacto", status_code=status.HTTP_202_ACCEPTED)
def create_inquiry(
    public_id: str,
    payload: InquiryCreate,
    request: Request,
    background: BackgroundTasks,
    db: DbSession,
) -> dict[str, str]:
    """Un comprador escribe al productor desde el pasaporte publico.

    Es el unico endpoint de escritura sin sesion de toda la API, asi que va con
    limite por IP. La respuesta no revela nada del productor: solo confirma.
    """
    _check_inquiry_rate(request.client.host if request.client else "desconocido")

    product = db.scalar(
        select(Product)
        .where(Product.public_id == public_id)
        .options(selectinload(Product.farm).selectinload(Farm.owner))
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Pasaporte no encontrado.")

    buyer_name = payload.buyer_name.strip()
    buyer_country = (payload.buyer_country or "").strip() or None
    message = payload.message.strip()

    db.add(
        BuyerInquiry(
            product_id=product.id,
            buyer_name=buyer_name,
            buyer_email=str(payload.buyer_email).strip().lower(),
            buyer_country=buyer_country,
            message=message,
        )
    )
    db.commit()

    owner = product.farm.owner
    if owner is not None:
        background.add_task(
            _send_inquiry_email, owner.email, buyer_name, buyer_country, product.name, message
        )

    return {"message": "Tu mensaje fue enviado al productor."}
