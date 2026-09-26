"""Datos de demostracion: una cuenta lista para entrar y ver la app con contenido.

Solo corre si la base esta vacia, asi que no pisa datos reales.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import EventType, Farm, Product, ProductStatus, User, UserRole
from app.services import trace

log = logging.getLogger(__name__)

DEMO_EMAIL = "demo@agrotrace.co"
DEMO_PASSWORD = "agrotrace2026"


def seed_demo(db: Session) -> None:
    if db.scalar(select(User.id).limit(1)):
        return

    user = User(
        email=DEMO_EMAIL,
        password_hash=hash_password(DEMO_PASSWORD),
        full_name="Maria Perez",
        role=UserRole.FARMER,
    )
    db.add(user)
    db.flush()

    finca = Farm(
        owner_id=user.id,
        name="Finca La Esperanza",
        owner_name="Familia Perez",
        municipality="Cienaga",
        department="Magdalena",
        country="Colombia",
        altitude_m=600,
        area_ha=12.5,
        description=(
            "Finca familiar en la vertiente norte de la Sierra Nevada de Santa Marta. "
            "Tres generaciones cultivando cacao y cafe bajo sombra."
        ),
    )
    palmar = Farm(
        owner_id=user.id,
        name="El Palmar",
        owner_name="Familia Perez",
        municipality="Aracataca",
        department="Magdalena",
        country="Colombia",
        altitude_m=340,
        area_ha=6.0,
        description="Lote de banano y platano en tierra caliente.",
    )
    db.add_all([finca, palmar])
    db.flush()

    cacao = _product(
        db,
        farm=finca,
        name="Cacao fino de aroma",
        variety="CCN-51",
        status=ProductStatus.READY,
        responsable="Familia Perez",
        insumos="Compost propio, ceniza de cascarilla, sin agroquimicos de sintesis",
        post_cosecha="Fermentacion en cajones de madera 6 dias, secado solar en marquesina",
        description="Cultivado a 600 msnm bajo sombra de arboles nativos.",
    )
    _chain(
        db,
        cacao,
        user.full_name,
        [
            (EventType.SIEMBRA, 180, {"area_m2": 2000, "variedad": "CCN-51", "altitud_m": 600, "plantulas": 850}),
            (EventType.FERTILIZACION, 120, {"insumo": "Compost propio", "dosis_kg_ha": 400, "metodo": "Aplicacion manual al plato"}),
            (EventType.CONTROL_FITOSANITARIO, 90, {"objetivo": "Monilia", "metodo": "Poda sanitaria y remocion manual", "quimicos": "ninguno"}),
            (EventType.COSECHA, 45, {"kg": 320, "calidad": "Grado A", "mazorcas": 4200, "cosechado_por": "Familia Perez"}),
            (EventType.POST_COSECHA, 38, {"proceso": "Fermentacion", "dias": 6, "recipiente": "Cajones de cedro", "temperatura_max_c": 48}),
            (EventType.SECADO, 30, {"metodo": "Solar en marquesina", "dias": 6, "humedad_final_pct": 7.0}),
            (EventType.CONTROL_CALIDAD, 20, {"prueba_corte": "85% bien fermentado", "humedad_pct": 7.0, "granos_defectuosos_pct": 2.1}),
            (EventType.EMPAQUE, 10, {"sacos": 7, "kg_por_saco": 45, "empaque": "Yute con liner", "lote": "LE-2026-003"}),
        ],
    )

    cafe = _product(
        db,
        farm=finca,
        name="Cafe de altura lavado",
        variety="Castillo",
        status=ProductStatus.PROCESSING,
        responsable="Jose Perez",
        insumos="Abono organico, control manual de arvenses",
        post_cosecha="Beneficio humedo, fermentacion 18 h, secado en marquesina",
        description="Cafe arabigo sembrado entre 1.100 y 1.300 msnm.",
    )
    _chain(
        db,
        cafe,
        user.full_name,
        [
            (EventType.SIEMBRA, 160, {"area_m2": 5000, "variedad": "Castillo", "densidad_plantas_ha": 5000}),
            (EventType.LABOR_CULTURAL, 100, {"labor": "Desyerba manual", "jornales": 8}),
            (EventType.COSECHA, 25, {"kg_cereza": 1800, "pase": "Segundo", "maduracion_pct": 96}),
            (EventType.POST_COSECHA, 22, {"proceso": "Beneficio humedo", "fermentacion_h": 18, "lavado": "Tres enjuagues"}),
            (EventType.SECADO, 15, {"metodo": "Marquesina", "dias": 9, "humedad_final_pct": 10.5}),
        ],
    )

    banano = _product(
        db,
        farm=palmar,
        name="Banano criollo",
        variety="Gros Michel",
        status=ProductStatus.HARVESTED,
        responsable="Luis Perez",
        insumos="Materia organica, manejo integrado de sigatoka",
        post_cosecha="Desmane, lavado y empaque en campo",
        description="Variedad criolla en recuperacion, cultivo asociado con platano.",
    )
    _chain(
        db,
        banano,
        user.full_name,
        [
            (EventType.SIEMBRA, 240, {"area_m2": 8000, "variedad": "Gros Michel", "colinos": 1200}),
            (EventType.CONTROL_FITOSANITARIO, 60, {"objetivo": "Sigatoka negra", "metodo": "Deshoje sanitario", "quimicos": "ninguno"}),
            (EventType.COSECHA, 8, {"racimos": 210, "kg": 4100, "calibre_promedio": 42}),
        ],
    )

    db.commit()
    log.info(
        "Datos de demostracion creados. Entra con %s / %s", DEMO_EMAIL, DEMO_PASSWORD
    )


def _product(db: Session, *, farm: Farm, name: str, **kwargs) -> Product:
    product = Product(farm_id=farm.id, public_id=trace.build_public_id(db, name), name=name, **kwargs)
    db.add(product)
    db.flush()
    return product


def _chain(
    db: Session,
    product: Product,
    author: str,
    steps: list[tuple[EventType, int, dict]],
) -> None:
    """Registra la secuencia de eventos fechada hacia atras desde hoy.

    Las fechas de siembra y cosecha del producto se derivan de los eventos que
    acaban de sellarse, no se escriben a mano: si la ficha dijera una fecha y la
    cadena otra, los datos de demostracion serian incoherentes.
    """
    now = datetime.now(timezone.utc)
    for event_type, days_ago, payload in steps:
        occurred_at = now - timedelta(days=days_ago)
        trace.record_event(
            db,
            product=product,
            event_type=event_type,
            payload=payload,
            recorded_by=author,
            occurred_at=occurred_at,
        )
        if event_type is EventType.SIEMBRA:
            product.planting_date = occurred_at.date()
        elif event_type is EventType.COSECHA:
            product.harvest_date = occurred_at.date()
