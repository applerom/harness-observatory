# FILE: src/observatory/web/routes/curation.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Curation Queue for proposed, disputed, and unverified Insights.
# PRD_REF: docs/PRD.md §11.7, §24
# WHY_REF: docs/why-graph.xml#FEAT-CURATION-QUEUE
# SCOPE: list curation-needed Insights; quick status labelling actions
# INVARIANTS:
# - This is not an approval gate; proposed Insights remain visible elsewhere.
# - Actions update confidence/status labels only and do not delete agent output.
# :END_MODULE_CONTRACT

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from observatory import db
from observatory.models import Insight, RevisionNote


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATE_DIR)
router = APIRouter(prefix="/curation", tags=["curation"])
ALLOWED_CURATION_STATUSES = {
    "human-verified": "verified",
    "disputed": "disputed",
    "historical": "historical",
}
RESTORABLE_INSIGHT_STATUSES = {
    "proposed",
    "corroborated",
    "disputed",
    "human-verified",
    "historical",
    "corrected",
}
RESTORABLE_CONFIDENCE_BANDS = {
    "unverified",
    "corroborated",
    "disputed",
    "verified",
    "historical",
}
CURATION_VISIBLE_STATUSES = {"proposed", "disputed"}


@dataclass(frozen=True)
class CurationInsightView:
    insight: Insight
    harness_label: str
    topic_label: str
    evidence_count: int


def _read_feedback(request: Request) -> dict[str, str] | None:
    feedback_type = request.query_params.get("feedback")
    if feedback_type not in {"changed", "undone"}:
        return None

    insight_id = request.query_params.get("insight_id")
    insight_title = request.query_params.get("insight_title")
    previous_status = request.query_params.get("previous_status")
    previous_confidence = request.query_params.get("previous_confidence")
    new_status = request.query_params.get("new_status")
    new_confidence = request.query_params.get("new_confidence")
    if (
        insight_id is None
        or insight_title is None
        or previous_status is None
        or previous_confidence is None
        or new_status is None
        or new_confidence is None
    ):
        return None
    return {
        "feedback_type": feedback_type,
        "insight_id": insight_id,
        "insight_title": insight_title,
        "previous_status": previous_status,
        "previous_confidence": previous_confidence,
        "new_status": new_status,
        "new_confidence": new_confidence,
    }


# START_ROUTE_CURATION_LIST:
@router.get("", response_class=HTMLResponse)
def curation_queue(request: Request, session: Session = Depends(db.get_session)) -> HTMLResponse:
    insights = sorted(
        session.exec(select(Insight)).all(),
        key=lambda insight: insight.agent_authored_at,
        reverse=True,
    )
    queue_items = [
        CurationInsightView(
            insight=insight,
            harness_label=insight.harness.name if insight.harness is not None else "Any harness",
            topic_label=insight.topic.name if insight.topic is not None else "No topic label",
            evidence_count=len(insight.evidence_items),
        )
        for insight in insights
        if insight.status in CURATION_VISIBLE_STATUSES or insight.confidence_band == "unverified"
    ]
    return templates.TemplateResponse(
        request,
        "curation/index.html",
        {
            "active_nav": "curation",
            "queue_items": queue_items,
            "feedback": _read_feedback(request),
        },
    )


# :END_ROUTE_CURATION_LIST


# START_ROUTE_CURATION_ACTION:
@router.post("/{insight_id}/status", response_class=RedirectResponse)
def update_insight_status(
    insight_id: int,
    status: str = Form(...),
    session: Session = Depends(db.get_session),
) -> RedirectResponse:
    if status not in ALLOWED_CURATION_STATUSES:
        raise HTTPException(status_code=400, detail="Unsupported curation status")
    insight = session.get(Insight, insight_id)
    if insight is None:
        raise HTTPException(status_code=404, detail="Insight not found")

    previous_status = insight.status
    previous_confidence = insight.confidence_band
    insight.status = status
    insight.confidence_band = ALLOWED_CURATION_STATUSES[status]
    note = RevisionNote(
        insight_id=insight.id,
        created_by="curation-ui",
        note=(
            "Curation status changed "
            f"from {previous_status}/{previous_confidence} "
            f"to {insight.status}/{insight.confidence_band}."
        ),
    )
    session.add_all([insight, note])
    session.commit()
    return RedirectResponse(
        url="/curation?"
        + urlencode(
            {
                "feedback": "changed",
                "insight_id": insight.id,
                "insight_title": insight.short_title,
                "previous_status": previous_status,
                "previous_confidence": previous_confidence,
                "new_status": insight.status,
                "new_confidence": insight.confidence_band,
            }
        ),
        status_code=303,
    )


# :END_ROUTE_CURATION_ACTION


# START_ROUTE_CURATION_UNDO:
@router.post("/{insight_id}/undo", response_class=RedirectResponse)
def undo_insight_status(
    insight_id: int,
    previous_status: str = Form(...),
    previous_confidence: str = Form(...),
    new_status: str = Form(...),
    new_confidence: str = Form(...),
    session: Session = Depends(db.get_session),
) -> RedirectResponse:
    if not (previous_status.strip() and previous_confidence.strip()):
        raise HTTPException(status_code=400, detail="Missing previous curation state")

    insight = session.get(Insight, insight_id)
    if insight is None:
        raise HTTPException(status_code=404, detail="Insight not found")

    current_status = insight.status
    current_confidence = insight.confidence_band
    restored_status = previous_status.strip()
    restored_confidence = previous_confidence.strip()
    if restored_status not in RESTORABLE_INSIGHT_STATUSES:
        raise HTTPException(status_code=400, detail="Unsupported previous curation status")
    if restored_confidence not in RESTORABLE_CONFIDENCE_BANDS:
        raise HTTPException(status_code=400, detail="Unsupported previous confidence band")

    insight.status = restored_status
    insight.confidence_band = restored_confidence
    note = RevisionNote(
        insight_id=insight.id,
        created_by="curation-ui",
        note=(
            "Curation status restored by undo: "
            f"from {current_status}/{current_confidence} "
            f"to {insight.status}/{insight.confidence_band}."
        ),
    )
    session.add_all([insight, note])
    session.commit()
    return RedirectResponse(
        url="/curation?"
        + urlencode(
            {
                "feedback": "undone",
                "insight_id": insight.id,
                "insight_title": insight.short_title,
                "previous_status": restored_status,
                "previous_confidence": restored_confidence,
                "new_status": current_status,
                "new_confidence": current_confidence,
            }
        ),
        status_code=303,
    )
# :END_ROUTE_CURATION_UNDO
