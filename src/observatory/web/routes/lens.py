# FILE: src/observatory/web/routes/lens.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Lens scoring web routes.
# PRD_REF: docs/PRD.md §15, §24.1
# WHY_REF: docs/why-graph.xml MOD-WEB-ROUTES-LENSES
# SCOPE: list Lens rows, render Score matrix rows, trigger deterministic refresh
# INVARIANTS:
# - UI presents per-lens scores only and does not compute a universal winner.
# - Refresh action delegates scoring to observatory.lenses.service.
# :END_MODULE_CONTRACT

from dataclasses import dataclass
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from observatory import db
from observatory.lenses.service import refresh_lens_scores, seed_default_lenses
from observatory.models import Harness, Lens, Score, Topic


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATE_DIR)
router = APIRouter(prefix="/lenses", tags=["lenses"])


@dataclass(frozen=True)
class LensScoreRow:
    harness: Harness
    topic: Topic
    scores: list[Score | None]


# START_ROUTE_LENS_LIST:
@router.get("", response_class=HTMLResponse)
def lens_list(request: Request, session: Session = Depends(db.get_session)) -> HTMLResponse:
    seed_default_lenses(session)
    lenses = list(session.exec(select(Lens).order_by(Lens.name)).all())
    rows = _score_rows(session, lenses)
    refreshed = request.query_params.get("refreshed") == "1"
    return templates.TemplateResponse(
        request,
        "lens/index.html",
        {
            "active_nav": "lenses",
            "lenses": lenses,
            "rows": rows,
            "refreshed": refreshed,
        },
    )


# :END_ROUTE_LENS_LIST


# START_ROUTE_LENS_REFRESH:
@router.post("/refresh")
def lens_refresh(session: Session = Depends(db.get_session)) -> RedirectResponse:
    refresh_lens_scores(session)
    return RedirectResponse("/lenses?refreshed=1", status_code=303)


# :END_ROUTE_LENS_REFRESH


def _score_rows(session: Session, lenses: list[Lens]) -> list[LensScoreRow]:
    scores = session.exec(select(Score)).all()
    harness_ids = {score.harness_id for score in scores if score.harness_id is not None}
    topic_ids = {score.topic_id for score in scores if score.topic_id is not None}
    harnesses = [
        harness
        for harness in session.exec(select(Harness).order_by(Harness.name)).all()
        if harness.id in harness_ids
    ]
    topics = [
        topic for topic in session.exec(select(Topic).order_by(Topic.name)).all() if topic.id in topic_ids
    ]
    rows: list[LensScoreRow] = []
    for harness in harnesses:
        for topic in topics:
            row_scores = [
                next(
                    (
                        score
                        for score in scores
                        if score.lens_id == lens.id
                        and score.harness_id == harness.id
                        and score.topic_id == topic.id
                    ),
                    None,
                )
                for lens in lenses
            ]
            if any(score is not None for score in row_scores):
                rows.append(LensScoreRow(harness=harness, topic=topic, scores=row_scores))
    return rows
