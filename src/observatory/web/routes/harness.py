# FILE: src/observatory/web/routes/harness.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Harness list, dossier, and v0.2a manual refresh entry point.
# PRD_REF: docs/PRD.md §26.2, §1162
# WHY_REF: docs/why-graph.xml#MOD-WEB-ROUTES-HARNESS
# SCOPE: harness index; harness dossier; OpenCode refresh trigger
# INVARIANTS:
# - Insight content renders above EvidenceItem proof controls.
# - EvidenceItem proof is collapsed by default behind the exact label "Show the proof".
# - Only OpenCode dispatches refresh jobs in v0.2a; other harnesses remain disabled.
# :END_MODULE_CONTRACT

from dataclasses import dataclass
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from observatory import db
from observatory.jobs.service import RefreshJobService, RefreshNotAvailableError
from observatory.models import ComparisonCell, EvidenceItem, Harness, Insight, Topic
from observatory.runners.base import AgentRunner
from observatory.runners.claude import ClaudeRunner


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATE_DIR)
router = APIRouter(prefix="/harnesses", tags=["harnesses"])


@dataclass(frozen=True)
class HarnessTopicSection:
    topic: Topic
    cell: ComparisonCell | None
    insights: list[Insight]
    evidence_items: list[EvidenceItem]


def get_refresh_runner() -> AgentRunner:
    return ClaudeRunner()


# START_ROUTE_HARNESS_LIST:
@router.get("", response_class=HTMLResponse)
def harness_list(request: Request, session: Session = Depends(db.get_session)) -> HTMLResponse:
    harnesses = session.exec(select(Harness).order_by(Harness.name)).all()
    return templates.TemplateResponse(
        request,
        "harness/list.html",
        {
            "active_nav": "harnesses",
            "harnesses": harnesses,
        },
    )


# :END_ROUTE_HARNESS_LIST


# START_ROUTE_HARNESS_DOSSIER:
@router.get("/{slug}", response_class=HTMLResponse)
def harness_dossier(
    slug: str,
    request: Request,
    session: Session = Depends(db.get_session),
) -> HTMLResponse:
    harness = session.exec(select(Harness).where(Harness.slug == slug)).first()
    if harness is None:
        raise HTTPException(status_code=404, detail="Harness not found")

    sections = _harness_topic_sections(session, harness)
    harness_insights = session.exec(
        select(Insight).where(Insight.harness_id == harness.id).order_by(Insight.short_title)
    ).all()
    return templates.TemplateResponse(
        request,
        "harness/dossier.html",
        {
            "active_nav": "harnesses",
            "harness": harness,
            "refresh_enabled": harness.slug == "opencode",
            "sections": sections,
            "harness_insights": harness_insights,
        },
    )


def _harness_topic_sections(session: Session, harness: Harness) -> list[HarnessTopicSection]:
    cells = list(session.exec(select(ComparisonCell).where(ComparisonCell.harness_id == harness.id)).all())
    evidence_topic_ids = {
        topic_id
        for topic_id in session.exec(
            select(EvidenceItem.topic_id).where(EvidenceItem.harness_id == harness.id)
        ).all()
        if topic_id is not None
    }
    topic_ids = {cell.topic_id for cell in cells} | evidence_topic_ids
    sections: list[HarnessTopicSection] = []
    for topic_id in sorted(topic_ids):
        topic = session.get(Topic, topic_id)
        if topic is None:
            continue
        cell = next((candidate for candidate in cells if candidate.topic_id == topic_id), None)
        topic_insights = session.exec(select(Insight).where(Insight.topic_id == topic_id)).all()
        insights = sorted(
            [insight for insight in topic_insights if insight.harness_id is None],
            key=lambda insight: insight.short_title,
        )
        evidence_items = list(
            session.exec(
                select(EvidenceItem)
                .where(EvidenceItem.harness_id == harness.id)
                .where(EvidenceItem.topic_id == topic_id)
            ).all()
        )
        evidence_items.sort(key=lambda item: item.id or 0)
        sections.append(
            HarnessTopicSection(
                topic=topic,
                cell=cell,
                insights=insights,
                evidence_items=evidence_items,
            )
        )
    return sections


# :END_ROUTE_HARNESS_DOSSIER


# START_ROUTE_HARNESS_REFRESH:
@router.post("/{slug}/refresh", response_class=RedirectResponse)
def refresh_harness(
    slug: str,
    session: Session = Depends(db.get_session),
    runner: AgentRunner = Depends(get_refresh_runner),
) -> RedirectResponse:
    harness = session.exec(select(Harness).where(Harness.slug == slug)).first()
    if harness is None:
        raise HTTPException(status_code=404, detail="Harness not found")
    try:
        job = RefreshJobService(runner).refresh_harness(session, harness)
    except RefreshNotAvailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return RedirectResponse(url=f"/jobs/{job.id}", status_code=303)


# :END_ROUTE_HARNESS_REFRESH


# START_ROUTE_HARNESS_ASK_WHY:
# Ask-agent-why is intentionally deferred until PRD §24 v0.7.
# :END_ROUTE_HARNESS_ASK_WHY
