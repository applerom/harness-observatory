# FILE: src/observatory/web/routes/matrix.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Read-only harness x topic matrix and HTMX cell expansion route.
# PRD_REF: docs/PRD.md §26.2
# WHY_REF: docs/why-graph.xml#MOD-WEB-ROUTES-MATRIX
# SCOPE: full matrix grid; per-cell partial; current confidence labels
# INVARIANTS:
# - Matrix cells show imported state and current confidence text.
# - Expanded cells render Insight above collapsed EvidenceItem proof.
# - Expanded cell detail renders verification pass history without creating AgentJobs.
# :END_MODULE_CONTRACT

import html
import re
from dataclasses import dataclass
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from observatory import db
from observatory.models import ComparisonCell, EvidenceItem, Harness, Insight, RevisionNote, Topic
from observatory.verification.service import VerificationPass, verification_passes_for_items
from observatory.web.revision_notes import revision_notes_by_insight_id


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATE_DIR)
router = APIRouter(prefix="/matrix", tags=["matrix"])


@dataclass(frozen=True)
class MatrixRow:
    harness: Harness
    cells: list[ComparisonCell | None]


@dataclass(frozen=True)
class MatrixCellDetail:
    harness: Harness
    topic: Topic
    cell: ComparisonCell | None
    cell_summary_html: str | None
    insights: list[Insight]
    evidence_items: list[EvidenceItem]
    verification_passes: list[VerificationPass]
    insight_body_html_by_id: dict[int, str]
    insight_why_html_by_id: dict[int, str]
    evidence_claim_html_by_id: dict[int, str]
    evidence_citation_html_by_id: dict[int, str]


# START_ROUTE_MATRIX_FULL:
@router.get("", response_class=HTMLResponse)
def matrix(request: Request, session: Session = Depends(db.get_session)) -> HTMLResponse:
    harnesses = session.exec(select(Harness).order_by(Harness.name)).all()
    topics = session.exec(select(Topic).order_by(Topic.name)).all()
    cells = session.exec(select(ComparisonCell)).all()
    rows = [
        MatrixRow(
            harness=harness,
            cells=[
                next(
                    (
                        cell
                        for cell in cells
                        if cell.harness_id == harness.id and cell.topic_id == topic.id
                    ),
                    None,
                )
                for topic in topics
            ],
        )
        for harness in harnesses
    ]
    return templates.TemplateResponse(
        request,
        "matrix/index.html",
        {
            "active_nav": "matrix",
            "topics": topics,
            "rows": rows,
        },
    )


# :END_ROUTE_MATRIX_FULL


# START_ROUTE_MATRIX_CELL_EXPAND:
@router.get("/cells/{harness_slug}/{topic_slug}", response_class=HTMLResponse)
def matrix_cell_expand(
    harness_slug: str,
    topic_slug: str,
    request: Request,
    session: Session = Depends(db.get_session),
) -> HTMLResponse:
    detail = _matrix_cell_detail(session, harness_slug, topic_slug)
    revision_notes = revision_notes_by_insight_id(session, detail.insights)
    compacted_notes = _dedupe_latest_revision_notes(revision_notes)
    return templates.TemplateResponse(
        request,
        "matrix/_cell_detail.html",
        {
            "detail": detail,
            "revision_notes_by_insight": compacted_notes,
        },
    )


def _matrix_cell_detail(session: Session, harness_slug: str, topic_slug: str) -> MatrixCellDetail:
    harness = session.exec(select(Harness).where(Harness.slug == harness_slug)).first()
    topic = session.exec(select(Topic).where(Topic.slug == topic_slug)).first()
    if harness is None or topic is None:
        raise HTTPException(status_code=404, detail="Matrix cell not found")
    cell = session.exec(
        select(ComparisonCell)
        .where(ComparisonCell.harness_id == harness.id)
        .where(ComparisonCell.topic_id == topic.id)
    ).first()
    topic_insights = session.exec(select(Insight).where(Insight.topic_id == topic.id)).all()
    insights = _dedupe_insights_sorted(
        [insight for insight in topic_insights if insight.harness_id in (None, harness.id)]
    )
    evidence_items = list(
        session.exec(
            select(EvidenceItem)
            .where(EvidenceItem.harness_id == harness.id)
            .where(EvidenceItem.topic_id == topic.id)
        ).all()
    )
    evidence_items.sort(key=lambda item: item.id or 0)
    verification_passes = verification_passes_for_items(session, evidence_items)
    insight_body_html_by_id = {
        insight.id: rendered
        for insight in insights
        if insight.id is not None
        if (rendered := _render_inline_markup(insight.body)) is not None
    }
    insight_why_html_by_id = {
        insight.id: rendered
        for insight in insights
        if insight.id is not None
        if (rendered := _render_inline_markup(insight.why_it_matters)) is not None
    }
    evidence_claim_html_by_id = {
        item.id: rendered
        for item in evidence_items
        if item.id is not None
        if (rendered := _render_inline_markup(item.claim_summary)) is not None
    }
    evidence_citation_html_by_id = {
        item.id: rendered
        for item in evidence_items
        if item.id is not None
        if (rendered := _render_inline_markup(item.exact_citation)) is not None
    }
    return MatrixCellDetail(
        harness=harness,
        topic=topic,
        cell=cell,
        cell_summary_html=_render_inline_markup(cell.cell_summary if cell else None),
        insights=insights,
        evidence_items=evidence_items,
        verification_passes=verification_passes,
        insight_body_html_by_id=insight_body_html_by_id,
        insight_why_html_by_id=insight_why_html_by_id,
        evidence_claim_html_by_id=evidence_claim_html_by_id,
        evidence_citation_html_by_id=evidence_citation_html_by_id,
    )


def _render_inline_markup(value: str | None) -> str | None:
    if not value:
        return None
    escaped = html.escape(value)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return escaped


def _dedupe_latest_revision_notes(
    notes_by_insight: dict[int, list[RevisionNote]],
) -> dict[int, list[RevisionNote]]:
    deduped: dict[int, list[RevisionNote]] = {}
    for insight_id, notes in notes_by_insight.items():
        latest_by_note: dict[str | None, RevisionNote] = {}
        for note in sorted(notes, key=lambda note: note.created_at):
            latest_by_note[note.note] = note
        deduped_notes = list(latest_by_note.values())
        deduped_notes.sort(key=lambda note: note.created_at, reverse=True)
        deduped[insight_id] = deduped_notes[:1]
    return deduped


def _dedupe_insights_sorted(insights: list[Insight]) -> list[Insight]:
    deduped: list[Insight] = []
    seen_keys: set[tuple[str, str]] = set()
    for insight in sorted(insights, key=lambda insight: insight.short_title):
        key = (insight.short_title, insight.body or "")
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(insight)
    return deduped


# :END_ROUTE_MATRIX_CELL_EXPAND
