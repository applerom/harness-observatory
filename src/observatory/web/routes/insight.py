# FILE: src/observatory/web/routes/insight.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Insight Library routes for retrieval, filtering, engagement generation, and explain jobs.
# PRD_REF: docs/PRD.md §11.6, §24 v0.6, §24 v0.7
# WHY_REF: docs/why-graph.xml#MOD-WEB-ROUTES-INSIGHTS
# SCOPE: library list; audience/format filters; deterministic engagement action; deterministic explain action
# INVARIANTS:
# - Insight Library renders published DB Insights directly; it is not an approval queue.
# - Engagement and explain actions delegate to deterministic services and make no model calls.
# :END_MODULE_CONTRACT

from dataclasses import dataclass
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from observatory import db
from observatory.engagement.service import create_engagement_job
from observatory.explain.service import create_explain_job
from observatory.models import Insight
from observatory.web.revision_notes import revision_notes_by_insight_id


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATE_DIR)
router = APIRouter(prefix="/insights", tags=["insights"])


@dataclass(frozen=True)
class InsightLibraryItem:
    insight: Insight
    harness_label: str
    topic_label: str
    evidence_count: int


# START_ROUTE_INSIGHT_LIBRARY:
@router.get("", response_class=HTMLResponse)
def insight_library(
    request: Request,
    audience: str | None = Query(default=None),
    format: str | None = Query(default=None),
    session: Session = Depends(db.get_session),
) -> HTMLResponse:
    statement = select(Insight)
    if audience:
        statement = statement.where(Insight.audience == audience)
    if format:
        statement = statement.where(Insight.format == format)

    insights = sorted(
        session.exec(statement).all(),
        key=lambda insight: insight.agent_authored_at,
        reverse=True,
    )
    items = [
        InsightLibraryItem(
            insight=insight,
            harness_label=insight.harness.name if insight.harness is not None else "Any harness",
            topic_label=insight.topic.name if insight.topic is not None else "No topic label",
            evidence_count=len(insight.evidence_items),
        )
        for insight in insights
    ]
    audiences = sorted(
        {
            value
            for value in session.exec(select(Insight.audience)).all()
            if value is not None and value
        }
    )
    formats = sorted({value for value in session.exec(select(Insight.format)).all() if value})
    return templates.TemplateResponse(
        request,
        "insight/index.html",
        {
            "active_nav": "insights",
            "items": items,
            "revision_notes_by_insight": revision_notes_by_insight_id(session, insights),
            "audiences": audiences,
            "formats": formats,
            "selected_audience": audience or "",
            "selected_format": format or "",
        },
    )


# :END_ROUTE_INSIGHT_LIBRARY


# START_ROUTE_INSIGHT_ENGAGEMENT:
@router.post("/{insight_id}/engagement", response_class=RedirectResponse)
def generate_insight_engagement(
    insight_id: int,
    session: Session = Depends(db.get_session),
) -> RedirectResponse:
    insight = session.get(Insight, insight_id)
    if insight is None:
        raise HTTPException(status_code=404, detail="Insight not found")
    create_engagement_job(session, insight)
    return RedirectResponse(url="/insights", status_code=303)


# :END_ROUTE_INSIGHT_ENGAGEMENT


# START_ROUTE_INSIGHT_EXPLAIN:
@router.post("/{insight_id}/explain", response_class=RedirectResponse)
def explain_insight(
    insight_id: int,
    request: Request,
    evidence_item_ids: list[int] | None = Form(default=None),
    session: Session = Depends(db.get_session),
) -> RedirectResponse:
    insight = session.get(Insight, insight_id)
    if insight is None:
        raise HTTPException(status_code=404, detail="Insight not found")
    create_explain_job(session, insight, evidence_item_ids=evidence_item_ids or [])
    redirect_url = request.headers.get("referer") or "/insights"
    return RedirectResponse(url=redirect_url, status_code=303)


# :END_ROUTE_INSIGHT_EXPLAIN
