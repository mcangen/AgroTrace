"""Diagnostico de certificacion (Fairtrade / Rainforest Alliance).

Privado: todo aqui vive detras de `owned_product`, nunca se expone en el
pasaporte publico. Ver `app.services.certification_data` para el catalogo de
preguntas y `app.services.certification_scoring` para el motor de puntuacion.
"""

from __future__ import annotations

import json
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.ai import agents
from app.api.deps import CurrentUser, DbSession, owned_product
from app.api.serializers import certification_assessment_to_out
from app.models import CertificationAssessment, CertificationStandard
from app.schemas import (
    CertificationAssessmentCreate,
    CertificationAssessmentOut,
    CertOptionOut,
    CertQuestionOut,
    CertSectionOut,
    CertStandardOut,
    PublishCertificationRequest,
)
from app.services import trace
from app.services.certification_data import CERT_STANDARDS, CertStandardDef, flat_questions
from app.services.certification_scoring import score_assessment

router = APIRouter(tags=["certificacion"])


def _standard_to_out(standard_def: CertStandardDef) -> CertStandardOut:
    return CertStandardOut(
        key=standard_def.key,
        name=standard_def.name,
        badge=standard_def.badge,
        color=standard_def.color,
        sections=[
            CertSectionOut(
                id=section.id,
                name=section.name,
                questions=[
                    CertQuestionOut(
                        id=q.id,
                        text=q.text,
                        critical=q.critical,
                        options=[CertOptionOut(value=o.value, label=o.label) for o in q.options],
                    )
                    for q in section.questions
                ],
            )
            for section in standard_def.sections
        ],
        total_questions=len(flat_questions(standard_def)),
    )


@router.get("/certification/standards", response_model=list[CertStandardOut])
def list_standards() -> list[CertStandardOut]:
    return [_standard_to_out(d) for d in CERT_STANDARDS.values()]


@router.post(
    "/products/{product_id}/certification/assessments",
    response_model=CertificationAssessmentOut,
    status_code=status.HTTP_201_CREATED,
)
def submit_assessment(
    product_id: int,
    payload: CertificationAssessmentCreate,
    db: DbSession,
    user: CurrentUser,
) -> CertificationAssessmentOut:
    product = owned_product(db, user, product_id)
    standard_def = CERT_STANDARDS[payload.standard]

    required_ids = {q.id for q in flat_questions(standard_def)}
    missing = required_ids - payload.answers.keys()
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Faltan {len(missing)} de {len(required_ids)} respuestas para "
                f"completar el diagnostico de {standard_def.name}."
            ),
        )

    scoring = score_assessment(standard_def, payload.answers)
    events = trace.list_events(db, product_id)
    roadmap, from_model = agents.run_certification_roadmap(
        db, product, events, standard_def, scoring, payload.answers
    )

    assessment = CertificationAssessment(
        product_id=product.id,
        standard=payload.standard,
        answers=json.dumps(payload.answers, ensure_ascii=False, sort_keys=True),
        overall_score=scoring.overall_score,
        verdict=scoring.verdict,
        section_scores=json.dumps(
            [asdict(s) for s in scoring.section_scores], ensure_ascii=False
        ),
        critical_gaps=json.dumps(
            [asdict(g) for g in scoring.critical_gaps], ensure_ascii=False
        ),
        roadmap_summary=roadmap.summary,
        roadmap_steps=json.dumps(
            [step.model_dump() for step in roadmap.steps], ensure_ascii=False
        ),
        generated_by_ai=from_model,
        created_by=user.full_name,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return certification_assessment_to_out(assessment)


@router.get(
    "/products/{product_id}/certification/assessments",
    response_model=list[CertificationAssessmentOut],
)
def list_assessments(
    product_id: int,
    db: DbSession,
    user: CurrentUser,
    standard: CertificationStandard | None = None,
) -> list[CertificationAssessmentOut]:
    owned_product(db, user, product_id)

    query = (
        select(CertificationAssessment)
        .where(CertificationAssessment.product_id == product_id)
        .order_by(CertificationAssessment.created_at.desc())
    )
    if standard is not None:
        query = query.where(CertificationAssessment.standard == standard)

    assessments = db.scalars(query).all()
    return [certification_assessment_to_out(a) for a in assessments]


@router.get(
    "/products/{product_id}/certification/assessments/latest",
    response_model=CertificationAssessmentOut | None,
)
def latest_assessment(
    product_id: int,
    standard: CertificationStandard,
    db: DbSession,
    user: CurrentUser,
) -> CertificationAssessmentOut | None:
    owned_product(db, user, product_id)

    assessment = db.scalar(
        select(CertificationAssessment)
        .where(
            CertificationAssessment.product_id == product_id,
            CertificationAssessment.standard == standard,
        )
        .order_by(CertificationAssessment.created_at.desc())
        .limit(1)
    )
    return certification_assessment_to_out(assessment) if assessment else None


@router.post("/products/{product_id}/certification/publish", response_model=list[CertificationStandard])
def set_certification_published(
    product_id: int,
    payload: PublishCertificationRequest,
    db: DbSession,
    user: CurrentUser,
) -> list[CertificationStandard]:
    """Publica o retira la insignia de un estandar en el pasaporte publico.

    Nunca publica el diagnostico completo -- solo el veredicto y el puntaje
    del intento mas reciente para ese estandar (ver `certification_badge_to_out`
    y `routes/passport.py::_published_badges`). Exige que exista al menos un
    intento para el estandar antes de dejarlo publicar algo que no existe.
    """
    product = owned_product(db, user, product_id)

    if payload.published:
        has_attempt = db.scalar(
            select(CertificationAssessment.id).where(
                CertificationAssessment.product_id == product_id,
                CertificationAssessment.standard == payload.standard,
            )
        )
        if has_attempt is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Primero completa un diagnóstico de este estándar para poder publicarlo.",
            )

    current = set(json.loads(product.published_certification_standards or "[]"))
    if payload.published:
        current.add(payload.standard.value)
    else:
        current.discard(payload.standard.value)

    product.published_certification_standards = json.dumps(sorted(current))
    db.commit()
    return sorted(current)
