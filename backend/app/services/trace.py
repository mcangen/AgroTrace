"""Registro y verificacion de eventos de trazabilidad."""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from secrets import randbelow

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import EventPhoto, EventType, Product, ProductPassport, TraceEvent
from app.services.hash_chain import GENESIS, chain_hash, payload_hash


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "producto")
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii").lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
    return cleaned or "producto"


def build_public_id(db: Session, product_name: str) -> str:
    """Slug legible + sufijo aleatorio, reintentando hasta que sea unico."""
    base = slugify(product_name)
    for _ in range(12):
        candidate = f"{base}-{randbelow(1_000_000):06d}"
        exists = db.scalar(select(Product.id).where(Product.public_id == candidate))
        if not exists:
            return candidate
    raise RuntimeError("No se pudo generar un identificador publico unico")


def record_event(
    db: Session,
    *,
    product: Product,
    event_type: EventType,
    payload: dict | None = None,
    note: str | None = None,
    recorded_by: str | None = None,
    occurred_at: datetime | None = None,
    photos: list[EventPhoto] | None = None,
) -> TraceEvent:
    """Sella un evento nuevo al final de la cadena del producto.

    El payload se serializa con claves ordenadas: el hash debe depender del
    contenido, no del orden en que llego el JSON.

    Si el evento trae fotos, sus huellas SHA-256 entran al payload ANTES de
    calcular el hash. Asi la evidencia grafica queda amarrada a la cadena: si
    despues alguien reemplaza el archivo en disco, su huella deja de coincidir
    con la que quedo sellada.
    """
    last = db.scalar(
        select(TraceEvent)
        .where(TraceEvent.product_id == product.id)
        .order_by(TraceEvent.sequence.desc())
        .limit(1)
    )
    prev_hash = last.chain_hash if last else GENESIS
    sequence = (last.sequence + 1) if last else 0

    sealed_payload = dict(payload or {})
    if photos:
        sealed_payload["fotos_sha256"] = [p.sha256 for p in photos]

    payload_json = json.dumps(sealed_payload, ensure_ascii=False, sort_keys=True)

    event = TraceEvent(
        product_id=product.id,
        sequence=sequence,
        event_type=event_type,
        payload=payload_json,
        note=note,
        payload_hash=payload_hash(payload_json),
        prev_hash=prev_hash,
        chain_hash=chain_hash(payload_json, prev_hash),
        recorded_by=recorded_by,
        occurred_at=occurred_at or datetime.now(timezone.utc),
    )
    db.add(event)
    db.flush()

    for photo in photos or []:
        photo.event_id = event.id

    _bump_reputation(db, product)
    return event


def _bump_reputation(db: Session, product: Product) -> None:
    """Cada evento registrado sube levemente la reputacion, con techo en 5.0."""
    passport = product.passport
    if passport is None:
        passport = ProductPassport(product_id=product.id, public_id=product.public_id)
        db.add(passport)
        db.flush()
        product.passport = passport
    passport.reputation_score = round(min(5.0, (passport.reputation_score or 4.0) + 0.1), 1)


def list_events(db: Session, product_id: int) -> list[TraceEvent]:
    return list(
        db.scalars(
            select(TraceEvent)
            .where(TraceEvent.product_id == product_id)
            .order_by(TraceEvent.sequence.asc())
        )
    )


def verify_chain(db: Session, product_id: int) -> dict:
    """Recalcula la cadena completa y reporta el primer eslabon roto."""
    events = list_events(db, product_id)

    if not events:
        return {
            "valid": True,
            "total_events": 0,
            "broken_at_sequence": None,
            "broken_event_id": None,
            "verified_at": datetime.now(timezone.utc),
            "message": "Sin eventos registrados.",
        }

    expected_prev = GENESIS
    for event in events:
        expected_chain = chain_hash(event.payload, expected_prev)
        if event.prev_hash != expected_prev or event.chain_hash != expected_chain:
            return {
                "valid": False,
                "total_events": len(events),
                "broken_at_sequence": event.sequence,
                "broken_event_id": event.id,
                "verified_at": datetime.now(timezone.utc),
                "message": (
                    f"La cadena se rompe en el evento #{event.sequence} "
                    f"({event.event_type.value}). El contenido fue alterado despues del sellado."
                ),
            }
        expected_prev = event.chain_hash

    return {
        "valid": True,
        "total_events": len(events),
        "broken_at_sequence": None,
        "broken_event_id": None,
        "verified_at": datetime.now(timezone.utc),
        "message": f"Cadena integra: {len(events)} eventos verificados.",
    }


def count_events(db: Session, product_ids: list[int]) -> dict[int, int]:
    if not product_ids:
        return {}
    rows = db.execute(
        select(TraceEvent.product_id, func.count(TraceEvent.id))
        .where(TraceEvent.product_id.in_(product_ids))
        .group_by(TraceEvent.product_id)
    ).all()
    return {product_id: total for product_id, total in rows}
