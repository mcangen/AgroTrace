"""Contratos de entrada y salida de la API."""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models import (
    AgentKind,
    AgentStatus,
    CertificationStandard,
    EventType,
    ProductStatus,
    UserRole,
)
from app.schemas.base import ORMModel  # noqa: F401 -- re-exportado para `from app.schemas import ORMModel`
from app.schemas.certification import PublicCertificationBadge  # noqa: F401 -- usado por PassportOut


# --- Auth ------------------------------------------------------------------


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=160)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORMModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# --- Fincas ----------------------------------------------------------------


class FarmCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    owner_name: str | None = Field(default=None, max_length=160)
    municipality: str | None = Field(default=None, max_length=120)
    department: str | None = Field(default=None, max_length=120)
    country: str = "Colombia"
    altitude_m: int | None = Field(default=None, ge=0, le=6000)
    area_ha: float | None = Field(default=None, ge=0)
    description: str | None = None


class FarmUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    owner_name: str | None = None
    municipality: str | None = None
    department: str | None = None
    country: str | None = None
    altitude_m: int | None = Field(default=None, ge=0, le=6000)
    area_ha: float | None = Field(default=None, ge=0)
    description: str | None = None


class FarmOut(ORMModel):
    id: int
    name: str
    owner_name: str | None
    municipality: str | None
    department: str | None
    country: str
    altitude_m: int | None
    area_ha: float | None
    description: str | None
    location: str
    latitude: float | None = None
    longitude: float | None = None
    created_at: datetime
    product_count: int = 0


# --- Productos -------------------------------------------------------------


class ProductCreate(BaseModel):
    farm_id: int
    name: str = Field(min_length=2, max_length=160)
    variety: str | None = Field(default=None, max_length=120)
    description: str | None = None
    status: ProductStatus = ProductStatus.GROWING
    responsable: str | None = Field(default=None, max_length=160)
    insumos: str | None = None
    post_cosecha: str | None = None
    planting_date: date | None = None
    harvest_date: date | None = None


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    variety: str | None = None
    description: str | None = None
    status: ProductStatus | None = None
    responsable: str | None = None
    insumos: str | None = None
    post_cosecha: str | None = None
    planting_date: date | None = None
    harvest_date: date | None = None
    directory_listed: bool | None = None


class ProductOut(ORMModel):
    id: int
    farm_id: int
    public_id: str
    name: str
    variety: str | None
    description: str | None
    status: ProductStatus
    responsable: str | None
    insumos: str | None
    post_cosecha: str | None
    planting_date: date | None
    harvest_date: date | None
    directory_listed: bool = False
    created_at: datetime

    farm_name: str = ""
    farm_location: str = ""
    event_count: int = 0
    reputation_score: float = 4.0
    has_story: bool = False
    passport_url: str = ""
    published_certification_standards: list[CertificationStandard] = Field(
        default_factory=list
    )

    @field_validator("published_certification_standards", mode="before")
    @classmethod
    def _decode_published_standards(cls, value: object) -> object:
        """El ORM guarda esto como JSON-en-texto (mismo patron que TraceEvent.payload);
        hay que decodificarlo ANTES de que Pydantic intente validarlo como lista,
        o `model_validate(product)` falla con la fila cruda."""
        if isinstance(value, str):
            return json.loads(value)
        return value


# --- Eventos ---------------------------------------------------------------


class EventCreate(BaseModel):
    event_type: EventType
    payload: dict[str, Any] = Field(default_factory=dict)
    note: str | None = None
    occurred_at: datetime | None = None
    # Fotos ya subidas (POST /products/{id}/photos) que se sellan con el evento.
    photo_ids: list[int] = Field(default_factory=list)


class PhotoOut(ORMModel):
    id: int
    product_id: int
    event_id: int | None
    filename: str
    content_type: str
    size_bytes: int
    sha256: str
    caption: str | None
    created_at: datetime
    url: str = ""
    # False si el archivo en disco ya no coincide con la huella sellada.
    integrity_ok: bool = True


class EventOut(ORMModel):
    id: int
    product_id: int
    sequence: int
    event_type: EventType
    payload: dict[str, Any]
    note: str | None
    payload_hash: str
    prev_hash: str
    chain_hash: str
    recorded_by: str | None
    occurred_at: datetime
    photos: list[PhotoOut] = Field(default_factory=list)


class VerificationOut(BaseModel):
    valid: bool
    total_events: int
    broken_at_sequence: int | None
    broken_event_id: int | None
    verified_at: datetime
    message: str


# --- Pasaporte -------------------------------------------------------------


class PassportOut(BaseModel):
    public_id: str
    product_name: str
    variety: str | None
    farm_name: str
    owner_name: str | None
    location: str
    altitude_m: int | None
    status: ProductStatus
    planting_date: date | None
    harvest_date: date | None

    story_es: str | None
    story_en: str | None
    export_title_es: str | None
    export_title_en: str | None
    export_body_es: str | None
    export_body_en: str | None
    tasting_notes: str | None
    reputation_score: float
    ai_model: str | None
    ai_generated_at: datetime | None

    events: list[EventOut]
    verification: VerificationOut
    qr_url: str
    # Insignias de certificacion que el productor eligio hacer publicas. El
    # diagnostico completo (brechas, hoja de ruta) nunca sale de aqui.
    certifications: list[PublicCertificationBadge] = Field(default_factory=list)


# --- IA --------------------------------------------------------------------


class AiStatusOut(BaseModel):
    enabled: bool
    backend: str
    model: str
    model_pro: str
    reason: str | None


class StoryOut(BaseModel):
    story_es: str
    story_en: str
    tasting_notes: str
    generated_by_ai: bool


class ExportSheetOut(BaseModel):
    title_es: str
    title_en: str
    body_es: str
    body_en: str
    generated_by_ai: bool


class InsightItemOut(BaseModel):
    title: str
    detail: str
    severity: str


class InsightsOut(BaseModel):
    summary: str
    quality_score: float
    items: list[InsightItemOut]
    generated_by_ai: bool


class AssistantRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    product_id: int | None = None


class AssistantOut(BaseModel):
    answer: str
    generated_by_ai: bool


class AgentRunOut(ORMModel):
    id: int
    product_id: int | None
    agent: AgentKind
    status: AgentStatus
    model: str | None
    latency_ms: int | None
    tokens_in: int | None
    tokens_out: int | None
    detail: str | None
    created_at: datetime


# --- Dashboard -------------------------------------------------------------


class TimelinePoint(BaseModel):
    date: date
    count: int


class EventTypeSlice(BaseModel):
    event_type: str
    count: int


class DashboardOut(BaseModel):
    farm_count: int
    product_count: int
    event_count: int
    chains_valid: int
    chains_broken: int
    avg_reputation: float
    ai_runs: int
    ai_success_rate: float
    events_last_30_days: list[TimelinePoint]
    events_by_type: list[EventTypeSlice]
    recent_events: list[EventOut]
    recent_agent_runs: list[AgentRunOut]


# --- Clima -------------------------------------------------------------------


class WeatherDayOut(BaseModel):
    date: date
    temp_min: float | None
    temp_max: float | None
    precipitation_mm: float | None
    precipitation_probability: int | None


class WeatherAlertOut(BaseModel):
    severity: str
    title: str
    detail: str


class WeatherOut(BaseModel):
    farm_id: int
    farm_name: str
    location: str
    latitude: float
    longitude: float
    timezone: str
    days: list[WeatherDayOut]
    alerts: list[WeatherAlertOut]


# --- Mensajes de compradores --------------------------------------------------


class InquiryCreate(BaseModel):
    """Lo envia un comprador desde el pasaporte publico, sin sesion."""

    buyer_name: str = Field(min_length=2, max_length=160)
    buyer_email: EmailStr
    buyer_country: str | None = Field(default=None, max_length=120)
    message: str = Field(min_length=10, max_length=2000)


class InquiryOut(ORMModel):
    id: int
    product_id: int
    buyer_name: str
    buyer_email: EmailStr
    buyer_country: str | None
    message: str
    read_at: datetime | None
    created_at: datetime
    product_name: str = ""


# --- Certificacion -----------------------------------------------------------
# Archivo propio (backend/app/schemas/certification.py): agrupa el catalogo de
# preguntas y el resultado del diagnostico, un dominio bastante distinto del
# resto de este archivo. Se re-exporta aqui para mantener la convencion de
# import `from app.schemas import (...)` que usan los demas routers.

from app.schemas.certification import (  # noqa: E402, F401
    CertificationAssessmentCreate,
    CertificationAssessmentOut,
    CertOptionOut,
    CertQuestionOut,
    CertSectionOut,
    CertStandardOut,
    CriticalGapOut,
    PublishCertificationRequest,
    RoadmapStepOut,
    SectionScoreOut,
)


# --- Directorio publico -------------------------------------------------------


class DirectoryEntryOut(BaseModel):
    public_id: str
    product_name: str
    variety: str | None
    farm_name: str
    location: str
    status: ProductStatus
    reputation_score: float
    has_story: bool
    thumbnail_url: str | None = None
