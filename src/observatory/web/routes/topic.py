# FILE: src/observatory/web/routes/topic.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Read-only topic list and dossier routes for imported observatory data.
# PRD_REF: docs/PRD.md §26.2
# WHY_REF: docs/why-graph.xml#MOD-WEB-ROUTES-TOPIC
# SCOPE: topic index; topic dossier with harness coverage and evidence-rich insights
# INVARIANTS:
# - Insight content renders above EvidenceItem proof controls.
# - EvidenceItem proof is collapsed by default behind the exact label "Show the proof".
# - v0.1 routes are read-only and do not create AgentJobs.
# :END_MODULE_CONTRACT

from dataclasses import dataclass
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from observatory import db
from observatory.models import ComparisonCell, EvidenceItem, Harness, Insight, Topic
from observatory.verification.service import confidence_from_verification_passes, verification_passes_for_items
from observatory.web.revision_notes import revision_notes_by_insight_id


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATE_DIR)
router = APIRouter(prefix="/topics", tags=["topics"])


@dataclass(frozen=True)
class TopicListRow:
    topic: Topic
    coverage_count: int


@dataclass(frozen=True)
class TopicHarnessSection:
    harness: Harness
    cell: ComparisonCell | None
    evidence_items: list[EvidenceItem]


# START_ROUTE_TOPIC_LIST:
@router.get("", response_class=HTMLResponse)
def topic_list(request: Request, session: Session = Depends(db.get_session)) -> HTMLResponse:
    topics = session.exec(select(Topic).order_by(Topic.name)).all()
    rows = [
        TopicListRow(topic=topic, coverage_count=_topic_coverage_count(session, topic))
        for topic in topics
    ]
    return templates.TemplateResponse(
        request,
        "topic/list.html",
        {
            "active_nav": "topics",
            "rows": rows,
        },
    )


def _topic_coverage_count(session: Session, topic: Topic) -> int:
    cell_harness_ids = {
        harness_id
        for harness_id in session.exec(
            select(ComparisonCell.harness_id).where(ComparisonCell.topic_id == topic.id)
        ).all()
    }
    evidence_harness_ids = {
        harness_id
        for harness_id in session.exec(
            select(EvidenceItem.harness_id).where(EvidenceItem.topic_id == topic.id)
        ).all()
        if harness_id is not None
    }
    return len(cell_harness_ids | evidence_harness_ids)


# :END_ROUTE_TOPIC_LIST


# START_ROUTE_TOPIC_DOSSIER:
@router.get("/{slug}", response_class=HTMLResponse)
def topic_dossier(
    slug: str,
    request: Request,
    session: Session = Depends(db.get_session),
) -> HTMLResponse:
    topic = session.exec(select(Topic).where(Topic.slug == slug)).first()
    if topic is None:
        raise HTTPException(status_code=404, detail="Topic not found")

    insights = session.exec(
        select(Insight).where(Insight.topic_id == topic.id).order_by(Insight.short_title)
    ).all()
    sections = _topic_harness_sections(session, topic)
    return templates.TemplateResponse(
        request,
        "topic/dossier.html",
        {
            "active_nav": "topics",
            "topic": topic,
            "insights": insights,
            "sections": sections,
            "revision_notes_by_insight": revision_notes_by_insight_id(session, list(insights)),
        },
    )


def _topic_harness_sections(session: Session, topic: Topic) -> list[TopicHarnessSection]:
    cells = list(session.exec(select(ComparisonCell).where(ComparisonCell.topic_id == topic.id)).all())
    evidence_harness_ids = {
        harness_id
        for harness_id in session.exec(
            select(EvidenceItem.harness_id).where(EvidenceItem.topic_id == topic.id)
        ).all()
        if harness_id is not None
    }
    harness_ids = {cell.harness_id for cell in cells} | evidence_harness_ids
    sections: list[TopicHarnessSection] = []
    for harness_id in sorted(harness_ids):
        harness = session.get(Harness, harness_id)
        if harness is None:
            continue
        cell = next((candidate for candidate in cells if candidate.harness_id == harness_id), None)
        evidence_items = list(
            session.exec(
                select(EvidenceItem)
                .where(EvidenceItem.topic_id == topic.id)
                .where(EvidenceItem.harness_id == harness_id)
            ).all()
        )
        evidence_items.sort(key=lambda item: item.id or 0)
        if cell is not None:
            derived_confidence = confidence_from_verification_passes(
                verification_passes_for_items(session, evidence_items)
            )
            if derived_confidence != "unverified":
                cell.confidence_band = derived_confidence
        sections.append(TopicHarnessSection(harness=harness, cell=cell, evidence_items=evidence_items))
    return sections


# :END_ROUTE_TOPIC_DOSSIER
