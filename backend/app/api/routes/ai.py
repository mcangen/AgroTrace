"""Endpoints que disparan los agentes de Gemini."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.ai import agents
from app.ai.client import gemini
from app.api.deps import CurrentUser, DbSession, owned_product
from app.models import AgentRun, Farm, Product
from app.schemas import (
    AgentRunOut,
    AiStatusOut,
    AssistantOut,
    AssistantRequest,
    ExportSheetOut,
    InsightsOut,
    StoryOut,
)
from app.services import trace

router = APIRouter(prefix="/ai", tags=["ia"])


@router.get("/status", response_model=AiStatusOut)
def ai_status() -> AiStatusOut:
    return AiStatusOut(**gemini.status())


@router.post("/products/{product_id}/story", response_model=StoryOut)
def generate_story(product_id: int, db: DbSession, user: CurrentUser) -> StoryOut:
    product = owned_product(db, user, product_id)
    events = trace.list_events(db, product_id)
    output, from_model = agents.run_storytelling(db, product, events)
    return StoryOut(**output.model_dump(), generated_by_ai=from_model)


@router.post("/products/{product_id}/export-sheet", response_model=ExportSheetOut)
def generate_export_sheet(
    product_id: int, db: DbSession, user: CurrentUser
) -> ExportSheetOut:
    product = owned_product(db, user, product_id)
    events = trace.list_events(db, product_id)
    output, from_model = agents.run_export_sheet(db, product, events)
    return ExportSheetOut(**output.model_dump(), generated_by_ai=from_model)


@router.post("/products/{product_id}/insights", response_model=InsightsOut)
def generate_insights(product_id: int, db: DbSession, user: CurrentUser) -> InsightsOut:
    product = owned_product(db, user, product_id)
    events = trace.list_events(db, product_id)
    output, from_model = agents.run_insights(db, product, events)
    return InsightsOut(**output.model_dump(), generated_by_ai=from_model)


@router.post("/assistant", response_model=AssistantOut)
def ask_assistant(
    payload: AssistantRequest, db: DbSession, user: CurrentUser
) -> AssistantOut:
    """Responde preguntas abiertas sobre un lote concreto o sobre toda la operacion."""
    if payload.product_id is not None:
        product = owned_product(db, user, payload.product_id)
        context = agents.build_context(product, trace.list_events(db, product.id))
    else:
        products = list(
            db.scalars(
                select(Product)
                .join(Farm)
                .where(Farm.owner_id == user.id)
                .options(selectinload(Product.farm))
                .order_by(Product.created_at.desc())
                .limit(20)
            )
        )
        counts = trace.count_events(db, [p.id for p in products])
        lines = [f"=== OPERACION DE {user.full_name.upper()} ==="]
        for product in products:
            lines.append(
                f"- {product.name} ({product.variety or 'sin variedad'}) "
                f"en {product.farm.name}, {product.farm.location} | "
                f"estado {product.status.value} | {counts.get(product.id, 0)} eventos"
            )
        if not products:
            lines.append("- (el productor aun no tiene lotes registrados)")
        context = "\n".join(lines)

    answer, used_fallback = agents.run_assistant(db, context, payload.question)
    return AssistantOut(answer=answer, generated_by_ai=not used_fallback)


@router.get("/runs", response_model=list[AgentRunOut])
def list_agent_runs(db: DbSession, user: CurrentUser, limit: int = 25) -> list[AgentRunOut]:
    """Ultimas ejecuciones de agentes sobre lotes del usuario."""
    product_ids = list(
        db.scalars(select(Product.id).join(Farm).where(Farm.owner_id == user.id))
    )
    runs = list(
        db.scalars(
            select(AgentRun)
            .where(AgentRun.product_id.in_(product_ids) | AgentRun.product_id.is_(None))
            .order_by(AgentRun.created_at.desc())
            .limit(min(limit, 100))
        )
    )
    return [AgentRunOut.model_validate(r) for r in runs]
