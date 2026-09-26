"""Agregados que alimentan el panel principal."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.api.serializers import event_to_out
from app.models import AgentRun, AgentStatus, Farm, Product, ProductPassport, TraceEvent
from app.schemas import (
    AgentRunOut,
    DashboardOut,
    EventTypeSlice,
    TimelinePoint,
)
from app.services import trace

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardOut)
def summary(db: DbSession, user: CurrentUser) -> DashboardOut:
    farm_ids = list(db.scalars(select(Farm.id).where(Farm.owner_id == user.id)))
    product_ids = (
        list(db.scalars(select(Product.id).where(Product.farm_id.in_(farm_ids))))
        if farm_ids
        else []
    )

    if not product_ids:
        return DashboardOut(
            farm_count=len(farm_ids),
            product_count=0,
            event_count=0,
            chains_valid=0,
            chains_broken=0,
            avg_reputation=0.0,
            ai_runs=0,
            ai_success_rate=0.0,
            events_last_30_days=_empty_timeline(),
            events_by_type=[],
            recent_events=[],
            recent_agent_runs=[],
        )

    event_count = (
        db.scalar(
            select(func.count(TraceEvent.id)).where(TraceEvent.product_id.in_(product_ids))
        )
        or 0
    )

    # La verificacion recalcula la cadena en Python, asi que se hace lote por lote.
    valid = sum(1 for pid in product_ids if trace.verify_chain(db, pid)["valid"])

    avg_reputation = (
        db.scalar(
            select(func.avg(ProductPassport.reputation_score)).where(
                ProductPassport.product_id.in_(product_ids)
            )
        )
        or 0.0
    )

    runs = list(
        db.scalars(
            select(AgentRun)
            .where(AgentRun.product_id.in_(product_ids) | AgentRun.product_id.is_(None))
            .order_by(AgentRun.created_at.desc())
        )
    )
    ok_runs = sum(1 for r in runs if r.status == AgentStatus.OK)

    recent_events = list(
        db.scalars(
            select(TraceEvent)
            .where(TraceEvent.product_id.in_(product_ids))
            .order_by(TraceEvent.occurred_at.desc())
            .limit(12)
        )
    )

    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    windowed = list(
        db.scalars(
            select(TraceEvent).where(
                TraceEvent.product_id.in_(product_ids), TraceEvent.occurred_at >= cutoff
            )
        )
    )
    per_day = Counter(e.occurred_at.date() for e in windowed)
    timeline = _empty_timeline()
    for point in timeline:
        point.count = per_day.get(point.date, 0)

    all_events = db.scalars(
        select(TraceEvent.event_type).where(TraceEvent.product_id.in_(product_ids))
    )
    by_type = Counter(t.value for t in all_events)

    return DashboardOut(
        farm_count=len(farm_ids),
        product_count=len(product_ids),
        event_count=event_count,
        chains_valid=valid,
        chains_broken=len(product_ids) - valid,
        avg_reputation=round(float(avg_reputation), 2),
        ai_runs=len(runs),
        ai_success_rate=round(ok_runs / len(runs), 3) if runs else 0.0,
        events_last_30_days=timeline,
        events_by_type=[
            EventTypeSlice(event_type=name, count=count)
            for name, count in by_type.most_common()
        ],
        recent_events=[event_to_out(e) for e in recent_events],
        recent_agent_runs=[AgentRunOut.model_validate(r) for r in runs[:8]],
    )


def _empty_timeline() -> list[TimelinePoint]:
    today = date.today()
    return [TimelinePoint(date=today - timedelta(days=i), count=0) for i in range(29, -1, -1)]
