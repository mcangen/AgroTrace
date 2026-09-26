"""CRUD de fincas del usuario autenticado."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession, owned_farm
from app.api.serializers import farm_to_out
from app.models import Farm, Product
from app.schemas import (
    FarmCreate,
    FarmOut,
    FarmUpdate,
    WeatherAlertOut,
    WeatherDayOut,
    WeatherOut,
)
from app.services import weather as weather_service

router = APIRouter(prefix="/farms", tags=["fincas"])


def _resolve_coordinates(farm: Farm) -> None:
    """Completa lat/lon desde el municipio si la finca aun no las tiene.

    Silencioso a proposito: si el geocodificador no responde o no encuentra el
    municipio, la finca se guarda igual y simplemente no habra pronostico.
    """
    if farm.latitude is not None and farm.longitude is not None:
        return
    if not farm.municipality:
        return
    coords = weather_service.geocode(farm.municipality, farm.department, farm.country)
    if coords:
        farm.latitude, farm.longitude = coords


@router.get("", response_model=list[FarmOut])
def list_farms(db: DbSession, user: CurrentUser) -> list[FarmOut]:
    rows = db.execute(
        select(Farm, func.count(Product.id))
        .outerjoin(Product, Product.farm_id == Farm.id)
        .where(Farm.owner_id == user.id)
        .group_by(Farm.id)
        .order_by(Farm.created_at.asc())
    ).all()
    return [farm_to_out(farm, total) for farm, total in rows]


@router.post("", response_model=FarmOut, status_code=status.HTTP_201_CREATED)
def create_farm(payload: FarmCreate, db: DbSession, user: CurrentUser) -> FarmOut:
    farm = Farm(owner_id=user.id, **payload.model_dump())
    _resolve_coordinates(farm)
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm_to_out(farm, 0)


@router.get("/{farm_id}", response_model=FarmOut)
def get_farm(farm_id: int, db: DbSession, user: CurrentUser) -> FarmOut:
    return farm_to_out(owned_farm(db, user, farm_id))


@router.patch("/{farm_id}", response_model=FarmOut)
def update_farm(
    farm_id: int, payload: FarmUpdate, db: DbSession, user: CurrentUser
) -> FarmOut:
    farm = owned_farm(db, user, farm_id)
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(farm, field, value)

    # Si cambio la ubicacion, las coordenadas viejas ya no sirven.
    if {"municipality", "department", "country"} & changes.keys():
        farm.latitude = None
        farm.longitude = None
        _resolve_coordinates(farm)

    db.commit()
    db.refresh(farm)
    return farm_to_out(farm)


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_farm(farm_id: int, db: DbSession, user: CurrentUser) -> None:
    db.delete(owned_farm(db, user, farm_id))
    db.commit()


@router.get("/{farm_id}/clima", response_model=WeatherOut)
def farm_weather(farm_id: int, db: DbSession, user: CurrentUser) -> WeatherOut:
    """Pronostico a 7 dias y alertas derivadas para la finca."""
    farm = owned_farm(db, user, farm_id)

    if farm.latitude is None or farm.longitude is None:
        _resolve_coordinates(farm)
        if farm.latitude is None or farm.longitude is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "No se pudo ubicar la finca en el mapa. Revisa que el municipio y el "
                    "departamento esten bien escritos."
                ),
            )
        db.commit()

    report = weather_service.forecast(farm.latitude, farm.longitude)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de clima no respondio. Intentalo de nuevo en un momento.",
        )

    return WeatherOut(
        farm_id=farm.id,
        farm_name=farm.name,
        location=farm.location,
        latitude=report.latitude,
        longitude=report.longitude,
        timezone=report.timezone,
        days=[WeatherDayOut(**vars(d)) for d in report.days],
        alerts=[WeatherAlertOut(**vars(a)) for a in report.alerts],
    )
