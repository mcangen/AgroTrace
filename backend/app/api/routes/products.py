"""Productos (lotes trazables) y su cadena de eventos."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession, owned_farm, owned_product
from app.api.serializers import event_to_out, photo_to_out, product_to_out
from app.models import EventPhoto, EventType, Farm, Product
from app.schemas import (
    EventCreate,
    EventOut,
    PhotoOut,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    VerificationOut,
)
from app.services import photos as photo_service
from app.services import trace
from app.services.qr import passport_qr_png
from app.services.report import build_traceability_report

router = APIRouter(prefix="/products", tags=["productos"])


@router.get("", response_model=list[ProductOut])
def list_products(
    db: DbSession, user: CurrentUser, farm_id: int | None = None
) -> list[ProductOut]:
    query = (
        select(Product)
        .join(Farm)
        .where(Farm.owner_id == user.id)
        .options(selectinload(Product.farm), selectinload(Product.passport))
        .order_by(Product.created_at.desc())
    )
    if farm_id is not None:
        query = query.where(Product.farm_id == farm_id)

    products = list(db.scalars(query))
    counts = trace.count_events(db, [p.id for p in products])
    return [product_to_out(p, counts.get(p.id, 0)) for p in products]


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: DbSession, user: CurrentUser) -> ProductOut:
    farm = owned_farm(db, user, payload.farm_id)

    data = payload.model_dump(exclude={"farm_id"})
    product = Product(
        farm_id=farm.id,
        public_id=trace.build_public_id(db, payload.name),
        **data,
    )
    db.add(product)
    db.flush()

    # Todo lote nace con un evento: el registro mismo es el primer eslabon.
    trace.record_event(
        db,
        product=product,
        event_type=EventType.REGISTRO_INICIAL,
        payload={
            "producto": product.name,
            "variedad": product.variety or "",
            "finca": farm.name,
            "ubicacion": farm.location,
            "responsable": product.responsable or "",
            "fecha_siembra": str(product.planting_date) if product.planting_date else "",
            "fecha_cosecha": str(product.harvest_date) if product.harvest_date else "",
        },
        recorded_by=user.full_name,
    )
    db.commit()
    db.refresh(product)
    return product_to_out(product, 1)


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: DbSession, user: CurrentUser) -> ProductOut:
    product = owned_product(db, user, product_id)
    return product_to_out(product)


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int, payload: ProductUpdate, db: DbSession, user: CurrentUser
) -> ProductOut:
    product = owned_product(db, user, product_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product_to_out(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: DbSession, user: CurrentUser) -> None:
    db.delete(owned_product(db, user, product_id))
    db.commit()


# --- Cadena de trazabilidad ------------------------------------------------


@router.get("/{product_id}/events", response_model=list[EventOut])
def list_product_events(product_id: int, db: DbSession, user: CurrentUser) -> list[EventOut]:
    owned_product(db, user, product_id)
    return [event_to_out(e, verify_photos=True) for e in trace.list_events(db, product_id)]


@router.post(
    "/{product_id}/events", response_model=EventOut, status_code=status.HTTP_201_CREATED
)
def create_product_event(
    product_id: int, payload: EventCreate, db: DbSession, user: CurrentUser
) -> EventOut:
    product = owned_product(db, user, product_id)

    photos: list[EventPhoto] = []
    if payload.photo_ids:
        photos = list(
            db.scalars(
                select(EventPhoto).where(
                    EventPhoto.id.in_(payload.photo_ids),
                    EventPhoto.product_id == product_id,
                    EventPhoto.event_id.is_(None),
                )
            )
        )
        if len(photos) != len(set(payload.photo_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Alguna foto no existe, no pertenece a este lote o ya fue sellada.",
            )

    event = trace.record_event(
        db,
        product=product,
        event_type=payload.event_type,
        payload=payload.payload,
        note=payload.note,
        recorded_by=user.full_name,
        occurred_at=payload.occurred_at,
        photos=photos,
    )
    db.commit()
    db.refresh(event)
    return event_to_out(event)


# --- Fotos de evidencia -----------------------------------------------------


@router.post(
    "/{product_id}/photos", response_model=PhotoOut, status_code=status.HTTP_201_CREATED
)
async def upload_product_photo(
    product_id: int,
    db: DbSession,
    user: CurrentUser,
    file: UploadFile = File(...),
    caption: str | None = Form(default=None),
) -> PhotoOut:
    """Sube una foto y la deja lista para sellarse junto a un evento.

    La foto se sube primero y el evento se sella despues con su huella dentro
    del payload: ese orden es lo que hace que la evidencia quede amarrada a la
    cadena y no se pueda sustituir luego sin que se note.
    """
    owned_product(db, user, product_id)

    content = await file.read()
    try:
        digest, _ = photo_service.store_photo(content, file.content_type or "")
    except photo_service.PhotoError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    photo = EventPhoto(
        product_id=product_id,
        filename=(file.filename or "foto")[:255],
        content_type=file.content_type or "image/jpeg",
        size_bytes=len(content),
        sha256=digest,
        caption=(caption or None),
        uploaded_by=user.full_name,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo_to_out(photo)


@router.delete("/{product_id}/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_unsealed_photo(
    product_id: int, photo_id: int, db: DbSession, user: CurrentUser
) -> None:
    """Descarta una foto que aun no se ha sellado en ningun evento.

    Una foto ya sellada no se puede borrar: su huella es parte de la cadena.
    """
    owned_product(db, user, product_id)
    photo = db.scalar(
        select(EventPhoto).where(
            EventPhoto.id == photo_id, EventPhoto.product_id == product_id
        )
    )
    if photo is None:
        raise HTTPException(status_code=404, detail="Foto no encontrada.")
    if photo.event_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esta foto ya esta sellada en la cadena y no puede eliminarse.",
        )
    db.delete(photo)
    db.commit()


# --- Reporte PDF ------------------------------------------------------------


@router.get("/{product_id}/reporte.pdf", response_class=Response)
def product_report_pdf(product_id: int, db: DbSession, user: CurrentUser) -> Response:
    product = owned_product(db, user, product_id)
    events = trace.list_events(db, product_id)
    verification = trace.verify_chain(db, product_id)

    pdf = build_traceability_report(product, events, verification, product.passport)
    filename = f"trazabilidad-{product.public_id}.pdf"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{product_id}/verify", response_model=VerificationOut)
def verify_product_chain(product_id: int, db: DbSession, user: CurrentUser) -> VerificationOut:
    owned_product(db, user, product_id)
    return VerificationOut(**trace.verify_chain(db, product_id))


@router.get("/{product_id}/qr.png", response_class=Response)
def product_qr(product_id: int, db: DbSession, user: CurrentUser) -> Response:
    product = owned_product(db, user, product_id)
    return Response(
        content=passport_qr_png(product.public_id),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"},
    )
