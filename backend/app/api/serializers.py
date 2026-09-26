"""Conversion de entidades a los esquemas de salida de la API."""

from __future__ import annotations

import json

from app.models import BuyerInquiry, CertificationAssessment, EventPhoto, Farm, Product, TraceEvent
from app.schemas import (
    CertificationAssessmentOut,
    DirectoryEntryOut,
    EventOut,
    FarmOut,
    InquiryOut,
    PhotoOut,
    ProductOut,
    PublicCertificationBadge,
)
from app.services import photos as photo_service
from app.services.certification_data import CertStandardDef
from app.services.qr import passport_url


def photo_to_out(photo: EventPhoto, verify: bool = False) -> PhotoOut:
    """`verify` relee el archivo en disco para comprobar su huella.

    Se hace solo donde importa (la vista de un lote o el pasaporte publico), no
    en listados masivos: implica leer cada imagen completa.
    """
    stored = photo_service.stored_name_for(photo.sha256, photo.content_type)
    out = PhotoOut.model_validate(photo)
    out.url = photo_service.photo_url(photo.sha256, photo.content_type)
    out.integrity_ok = (
        photo_service.verify_stored_photo(stored, photo.sha256) if verify else True
    )
    return out


def event_to_out(event: TraceEvent, verify_photos: bool = False) -> EventOut:
    try:
        payload = json.loads(event.payload or "{}")
    except json.JSONDecodeError:
        payload = {"raw": event.payload}
    if not isinstance(payload, dict):
        payload = {"value": payload}

    return EventOut(
        id=event.id,
        product_id=event.product_id,
        sequence=event.sequence,
        event_type=event.event_type,
        payload=payload,
        note=event.note,
        payload_hash=event.payload_hash,
        prev_hash=event.prev_hash,
        chain_hash=event.chain_hash,
        recorded_by=event.recorded_by,
        occurred_at=event.occurred_at,
        photos=[photo_to_out(p, verify=verify_photos) for p in event.photos],
    )


def inquiry_to_out(inquiry: BuyerInquiry) -> InquiryOut:
    out = InquiryOut.model_validate(inquiry)
    out.product_name = inquiry.product.name if inquiry.product else ""
    return out


def farm_to_out(farm: Farm, product_count: int | None = None) -> FarmOut:
    out = FarmOut.model_validate(farm)
    out.location = farm.location
    out.product_count = product_count if product_count is not None else len(farm.products)
    return out


def product_to_out(product: Product, event_count: int | None = None) -> ProductOut:
    out = ProductOut.model_validate(product)
    out.farm_name = product.farm.name
    out.farm_location = product.farm.location
    out.event_count = event_count if event_count is not None else len(product.events)
    passport = product.passport
    out.reputation_score = passport.reputation_score if passport else 4.0
    out.has_story = bool(passport and passport.story_es)
    out.passport_url = passport_url(product.public_id)
    return out


def directory_entry_to_out(product: Product) -> DirectoryEntryOut:
    passport = product.passport
    thumbnail = None
    for event in reversed(product.events):
        if event.photos:
            thumbnail = photo_to_out(event.photos[-1]).url
            break

    return DirectoryEntryOut(
        public_id=product.public_id,
        product_name=product.name,
        variety=product.variety,
        farm_name=product.farm.name,
        location=product.farm.location,
        status=product.status,
        reputation_score=passport.reputation_score if passport else 4.0,
        has_story=bool(passport and passport.story_es),
        thumbnail_url=thumbnail,
    )


def certification_badge_to_out(
    assessment: CertificationAssessment, standard_def: CertStandardDef
) -> PublicCertificationBadge:
    return PublicCertificationBadge(
        standard=assessment.standard,
        standard_name=standard_def.name,
        badge=standard_def.badge,
        color=standard_def.color,
        verdict=assessment.verdict,
        overall_score=assessment.overall_score,
        assessed_at=assessment.created_at,
    )


def certification_assessment_to_out(
    assessment: CertificationAssessment,
) -> CertificationAssessmentOut:
    """`section_scores`/`critical_gaps`/`roadmap_steps` viven como JSON-texto en
    la fila (mismo patron que `TraceEvent.payload`), asi que no se puede armar
    el schema con `model_validate(assessment)` directo."""
    return CertificationAssessmentOut(
        id=assessment.id,
        product_id=assessment.product_id,
        standard=assessment.standard,
        overall_score=assessment.overall_score,
        verdict=assessment.verdict,
        section_scores=json.loads(assessment.section_scores),
        critical_gaps=json.loads(assessment.critical_gaps),
        roadmap_summary=assessment.roadmap_summary,
        roadmap_steps=json.loads(assessment.roadmap_steps or "[]"),
        generated_by_ai=assessment.generated_by_ai,
        created_at=assessment.created_at,
    )
