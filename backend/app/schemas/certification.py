"""Contratos del diagnostico de certificacion.

Archivo propio en vez de ampliar `schemas/__init__.py`: el catalogo de
preguntas por si solo son varias clases anidadas (opcion, pregunta, seccion,
estandar) mas las del resultado del diagnostico, y agrupan un dominio bastante
distinto del resto (auth, fincas, IA generica, dashboard).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models import CertificationStandard, CertificationVerdict
from app.schemas.base import ORMModel

_VALID_ANSWER_VALUES = {"yes", "partial", "no"}


# --- Catalogo (GET /certification/standards) --------------------------------


class CertOptionOut(BaseModel):
    value: str
    label: str


class CertQuestionOut(BaseModel):
    id: str
    text: str
    critical: bool
    options: list[CertOptionOut]


class CertSectionOut(BaseModel):
    id: str
    name: str
    questions: list[CertQuestionOut]


class CertStandardOut(BaseModel):
    key: CertificationStandard
    name: str
    badge: str
    color: str
    sections: list[CertSectionOut]
    total_questions: int


# --- Envio de un diagnostico -------------------------------------------------


class CertificationAssessmentCreate(BaseModel):
    standard: CertificationStandard
    answers: dict[str, str]

    @field_validator("answers")
    @classmethod
    def _validate_answer_values(cls, value: dict[str, str]) -> dict[str, str]:
        invalid = sorted(set(value.values()) - _VALID_ANSWER_VALUES)
        if invalid:
            raise ValueError(
                f"Valores de respuesta invalidos: {invalid}. "
                f"Deben ser uno de {sorted(_VALID_ANSWER_VALUES)}."
            )
        return value


# --- Resultado ---------------------------------------------------------------


class SectionScoreOut(BaseModel):
    id: str
    name: str
    score: int
    yes: int
    partial: int
    no: int


class CriticalGapOut(BaseModel):
    id: str
    text: str


class RoadmapStepOut(BaseModel):
    title: str
    detail: str
    priority: str


class CertificationAssessmentOut(ORMModel):
    id: int
    product_id: int
    standard: CertificationStandard
    overall_score: int
    verdict: CertificationVerdict
    section_scores: list[SectionScoreOut]
    critical_gaps: list[CriticalGapOut]
    roadmap_summary: str | None
    roadmap_steps: list[RoadmapStepOut]
    generated_by_ai: bool
    created_at: datetime


# --- Publicacion en el pasaporte publico -------------------------------------


class PublishCertificationRequest(BaseModel):
    standard: CertificationStandard
    published: bool


class PublicCertificationBadge(BaseModel):
    """Lo unico del diagnostico que llega al pasaporte publico, y solo si el
    productor lo publico explicitamente: estandar, veredicto y puntaje. Nunca
    las brechas criticas ni la hoja de ruta -- eso sigue siendo privado."""

    standard: CertificationStandard
    standard_name: str
    badge: str
    color: str
    verdict: CertificationVerdict
    overall_score: int
    assessed_at: datetime
