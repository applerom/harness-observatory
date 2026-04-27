# FILE: src/observatory/web/routes/dashboard.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Home dashboard route and tiny HTMX partial for the v0.1 read-only web surface.
# PRD_REF: docs/PRD.md §11.1, §26.2, §26.6
# WHY_REF: docs/why-graph.xml MOD-WEB-ROUTES-DASHBOARD
# SCOPE: dashboard page; database counts; HTMX proof-of-life partial
# INVARIANTS:
# - Routes are read-only and do not dispatch AgentJobs or background work.
# - Counts are zero-safe real database aggregates.
# :END_MODULE_CONTRACT

from pathlib import Path
from typing import TypedDict

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from observatory import db
from observatory.models import Harness, Insight, Topic


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATE_DIR)
router = APIRouter()


class DashboardCounts(TypedDict):
    """Aggregate counts shown on the v0.1 dashboard."""

    harnesses: int
    topics: int
    insights: int


def _dashboard_counts(session: Session) -> DashboardCounts:
    return {
        "harnesses": len(session.exec(select(Harness.id)).all()),
        "topics": len(session.exec(select(Topic.id)).all()),
        "insights": len(session.exec(select(Insight.id)).all()),
    }


# START_ROUTE_DASHBOARD:
@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(db.get_session)) -> HTMLResponse:
    """Render the v0.1 home dashboard."""
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "active_nav": "dashboard",
            "counts": _dashboard_counts(session),
        },
    )


@router.get("/partials/dashboard/pulse", response_class=HTMLResponse)
async def dashboard_pulse() -> HTMLResponse:
    """Return a tiny HTMX partial without touching persistent state."""
    return HTMLResponse('<span class="text-emerald-700">HTMX partial rendered from the server.</span>')


# :END_ROUTE_DASHBOARD
