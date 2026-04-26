# FILE: src/observatory/web/routes/matrix.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Read-only harness x topic matrix and HTMX cell expansion route.
# PRD_REF: docs/PRD.md §26.2
# WHY_REF: docs/why-graph.xml#MOD-WEB-ROUTES-MATRIX
# SCOPE: full matrix grid; per-cell partial; confidence placeholder labels
# INVARIANTS:
# - Matrix cells show imported state and v0.1 confidence placeholder text.
# - Expanded cells render Insight above collapsed EvidenceItem proof.
# - v0.1 expansion is read-only HTMX; no AgentJob or edit action is available.
# :END_MODULE_CONTRACT

from dataclasses import dataclass
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from observatory import db
from observatory.models import ComparisonCell, EvidenceItem, Harness, Insight, Topic


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
    insights: list[Insight]
    evidence_items: list[EvidenceItem]


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
    return templates.TemplateResponse(
        request,
        "matrix/_cell_detail.html",
        {"detail": detail},
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
    insights = sorted(
        [insight for insight in topic_insights if insight.harness_id is None],
        key=lambda insight: insight.short_title,
    )
    evidence_items = list(
        session.exec(
            select(EvidenceItem)
            .where(EvidenceItem.harness_id == harness.id)
            .where(EvidenceItem.topic_id == topic.id)
        ).all()
    )
    evidence_items.sort(key=lambda item: item.id or 0)
    return MatrixCellDetail(
        harness=harness,
        topic=topic,
        cell=cell,
        insights=insights,
        evidence_items=evidence_items,
    )


# :END_ROUTE_MATRIX_CELL_EXPAND
