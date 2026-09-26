"""Modelo de datos de AgroTrace.

Seis entidades:
  User          -> quien opera la plataforma (duenno de finca, operario, comprador)
  Farm          -> la finca; un usuario puede tener varias
  Product       -> un lote/producto trazable de una finca
  TraceEvent    -> cada hecho registrado, sellado en la cadena SHA-256
  Passport      -> la cara publica del producto, enriquecida por los agentes Gemini
  AgentRun      -> bitacora de cada ejecucion de un agente de IA
  CertificationAssessment -> diagnostico privado de listura para una certificacion
"""

from __future__ import annotations

import enum
from datetime import date, datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    FARMER = "FARMER"
    OPERATOR = "OPERATOR"
    BUYER = "BUYER"


class ProductStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    GROWING = "GROWING"
    HARVESTED = "HARVESTED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    EXPORTED = "EXPORTED"


class EventType(str, enum.Enum):
    REGISTRO_INICIAL = "REGISTRO_INICIAL"
    SIEMBRA = "SIEMBRA"
    LABOR_CULTURAL = "LABOR_CULTURAL"
    FERTILIZACION = "FERTILIZACION"
    CONTROL_FITOSANITARIO = "CONTROL_FITOSANITARIO"
    COSECHA = "COSECHA"
    POST_COSECHA = "POST_COSECHA"
    SECADO = "SECADO"
    CONTROL_CALIDAD = "CONTROL_CALIDAD"
    EMPAQUE = "EMPAQUE"
    CERTIFICACION = "CERTIFICACION"
    DESPACHO = "DESPACHO"


class AgentKind(str, enum.Enum):
    STORYTELLING = "STORYTELLING"
    EXPORT_SHEET = "EXPORT_SHEET"
    INSIGHTS = "INSIGHTS"
    ASSISTANT = "ASSISTANT"
    CERTIFICATION = "CERTIFICATION"


class CertificationStandard(str, enum.Enum):
    FAIRTRADE = "FAIRTRADE"
    RAINFOREST_ALLIANCE = "RAINFOREST_ALLIANCE"


class CertificationVerdict(str, enum.Enum):
    READY = "READY"
    ALMOST_READY = "ALMOST_READY"
    NOT_READY = "NOT_READY"


class AgentStatus(str, enum.Enum):
    OK = "OK"
    FALLBACK = "FALLBACK"
    ERROR = "ERROR"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(160))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.FARMER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    farms: Mapped[list["Farm"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class PasswordResetToken(Base):
    """Token de un solo uso para restablecer contrasena.

    Se guarda el hash SHA-256 del token, nunca el valor crudo: si alguien
    llegara a leer la tabla, no podria reconstruir un enlace de recuperacion
    valido a partir de lo que ve.
    """

    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    owner_name: Mapped[str | None] = mapped_column(String(160), default=None)
    municipality: Mapped[str | None] = mapped_column(String(120), default=None)
    department: Mapped[str | None] = mapped_column(String(120), default=None)
    country: Mapped[str] = mapped_column(String(80), default="Colombia")
    altitude_m: Mapped[int | None] = mapped_column(Integer, default=None)
    area_ha: Mapped[float | None] = mapped_column(Float, default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    # Coordenadas para el pronostico del clima. Se resuelven automaticamente
    # desde municipio/departamento al guardar la finca, o se pueden fijar a mano.
    latitude: Mapped[float | None] = mapped_column(Float, default=None)
    longitude: Mapped[float | None] = mapped_column(Float, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    owner: Mapped[User] = relationship(back_populates="farms")
    products: Mapped[list["Product"]] = relationship(
        back_populates="farm", cascade="all, delete-orphan"
    )

    @property
    def location(self) -> str:
        parts = [self.municipality, self.department, self.country]
        return ", ".join(p for p in parts if p)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id", ondelete="CASCADE"), index=True)
    public_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    variety: Mapped[str | None] = mapped_column(String(120), default=None)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus), default=ProductStatus.GROWING
    )
    responsable: Mapped[str | None] = mapped_column(String(160), default=None)
    insumos: Mapped[str | None] = mapped_column(Text, default=None)
    post_cosecha: Mapped[str | None] = mapped_column(Text, default=None)
    planting_date: Mapped[date | None] = mapped_column(Date, default=None)
    harvest_date: Mapped[date | None] = mapped_column(Date, default=None)
    # El productor decide, lote por lote, si aparece en el directorio publico.
    directory_listed: Mapped[bool] = mapped_column(Boolean, default=False)
    # JSON de CertificationStandard: que diagnosticos de certificacion decidio
    # publicar como insignia en su pasaporte. El detalle del diagnostico (brechas,
    # hoja de ruta) sigue siendo siempre privado -- solo el veredicto y el
    # puntaje se hacen publicos, y unicamente si el productor lo elige.
    published_certification_standards: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    farm: Mapped[Farm] = relationship(back_populates="products")
    events: Mapped[list["TraceEvent"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="TraceEvent.sequence",
    )
    passport: Mapped["ProductPassport | None"] = relationship(
        back_populates="product", cascade="all, delete-orphan", uselist=False
    )
    certification_assessments: Mapped[list["CertificationAssessment"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="CertificationAssessment.created_at.desc()",
    )
    inquiries: Mapped[list["BuyerInquiry"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="BuyerInquiry.created_at.desc()",
    )


class TraceEvent(Base):
    __tablename__ = "trace_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    # Posicion en la cadena; hace el orden deterministico aunque dos eventos
    # compartan timestamp (el proyecto original ordenaba solo por fecha).
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType))
    payload: Mapped[str] = mapped_column(Text, default="{}")
    note: Mapped[str | None] = mapped_column(Text, default=None)
    payload_hash: Mapped[str] = mapped_column(String(64))
    prev_hash: Mapped[str] = mapped_column(String(64))
    chain_hash: Mapped[str] = mapped_column(String(64), index=True)
    recorded_by: Mapped[str | None] = mapped_column(String(160), default=None)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    product: Mapped[Product] = relationship(back_populates="events")
    photos: Mapped[list["EventPhoto"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class EventPhoto(Base):
    """Foto de respaldo de un evento de trazabilidad.

    La huella SHA-256 del archivo se sella dentro del payload del evento, asi
    que la foto queda amarrada a la cadena: si alguien reemplaza el archivo en
    disco, su hash deja de coincidir con el que quedo sellado y la evidencia
    se delata sola.
    """

    __tablename__ = "event_photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    # Nulo mientras la foto esta subida pero el evento todavia no se sella.
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("trace_events.id", ondelete="CASCADE"), index=True, default=None
    )
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), index=True)
    caption: Mapped[str | None] = mapped_column(String(255), default=None)
    uploaded_by: Mapped[str | None] = mapped_column(String(160), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    event: Mapped["TraceEvent | None"] = relationship(back_populates="photos")


class ProductPassport(Base):
    __tablename__ = "product_passports"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), unique=True, index=True
    )
    public_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)

    story_es: Mapped[str | None] = mapped_column(Text, default=None)
    story_en: Mapped[str | None] = mapped_column(Text, default=None)
    export_title_es: Mapped[str | None] = mapped_column(String(255), default=None)
    export_title_en: Mapped[str | None] = mapped_column(String(255), default=None)
    export_body_es: Mapped[str | None] = mapped_column(Text, default=None)
    export_body_en: Mapped[str | None] = mapped_column(Text, default=None)
    tasting_notes: Mapped[str | None] = mapped_column(Text, default=None)
    reputation_score: Mapped[float] = mapped_column(Float, default=4.0)

    ai_model: Mapped[str | None] = mapped_column(String(120), default=None)
    ai_generated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    product: Mapped[Product] = relationship(back_populates="passport")


class AgentRun(Base):
    """Bitacora de cada llamada a Gemini: alimenta el panel de actividad de IA."""

    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True, default=None
    )
    agent: Mapped[AgentKind] = mapped_column(Enum(AgentKind))
    status: Mapped[AgentStatus] = mapped_column(Enum(AgentStatus))
    model: Mapped[str | None] = mapped_column(String(120), default=None)
    latency_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    tokens_in: Mapped[int | None] = mapped_column(Integer, default=None)
    tokens_out: Mapped[int | None] = mapped_column(Integer, default=None)
    detail: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class CertificationAssessment(Base):
    """Un intento de autodiagnostico de certificacion sobre un lote.

    Es privado (solo el panel del agricultor, nunca el pasaporte publico) e
    inmutable una vez calculado -- se guarda historial completo en vez de
    sobreescribir, para que el productor vea su progreso entre intentos.
    """

    __tablename__ = "certification_assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    standard: Mapped[CertificationStandard] = mapped_column(
        Enum(CertificationStandard), index=True
    )

    answers: Mapped[str] = mapped_column(Text)  # JSON {question_id: "yes"|"partial"|"no"}
    overall_score: Mapped[int] = mapped_column(Integer)
    verdict: Mapped[CertificationVerdict] = mapped_column(Enum(CertificationVerdict))
    section_scores: Mapped[str] = mapped_column(Text)  # JSON [{id,name,score,yes,partial,no}]
    critical_gaps: Mapped[str] = mapped_column(Text)  # JSON [{id,text}]

    roadmap_summary: Mapped[str | None] = mapped_column(Text, default=None)
    roadmap_steps: Mapped[str | None] = mapped_column(Text, default=None)  # JSON [{title,detail,priority}]
    generated_by_ai: Mapped[bool] = mapped_column(Boolean, default=False)

    created_by: Mapped[str | None] = mapped_column(String(160), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )

    product: Mapped[Product] = relationship(back_populates="certification_assessments")


class BuyerInquiry(Base):
    """Mensaje que un comprador envia desde el pasaporte publico de un lote.

    Es la unica entidad que puede crear alguien sin sesion, asi que el endpoint
    que la escribe valida y limita con cuidado (ver `api/routes/passport.py`).
    """

    __tablename__ = "buyer_inquiries"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    buyer_name: Mapped[str] = mapped_column(String(160))
    buyer_email: Mapped[str] = mapped_column(String(255))
    buyer_country: Mapped[str | None] = mapped_column(String(120), default=None)
    message: Mapped[str] = mapped_column(Text)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )

    product: Mapped[Product] = relationship(back_populates="inquiries")
