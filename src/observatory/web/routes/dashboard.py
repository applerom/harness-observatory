# FILE: src/observatory/web/routes/dashboard.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Home dashboard route and tiny HTMX partial for the v0.1 web skeleton.
# PRD_REF: docs/PRD.md §11.1, §26.2, §26.6
# WHY_REF: docs/why-graph.xml MOD-WEB-ROUTES-DASHBOARD
# SCOPE: dashboard page; placeholder counts; HTMX proof-of-life partial
# INVARIANTS:
# - Routes are read-only and do not dispatch AgentJobs or background work.
# - Counts are zero-safe placeholders until model/database integration lands.
# :END_MODULE_CONTRACT

from pathlib import Path
from typing import TypedDict

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATE_DIR)
router = APIRouter()


class DashboardCounts(TypedDict):
    """Placeholder aggregate counts shown on the v0.1 dashboard."""

    harnesses: int
    topics: int
    insights: int


def _dashboard_counts(request: Request) -> DashboardCounts:
    counts = getattr(request.app.state, "dashboard_counts", {})
    return {
        "harnesses": int(counts.get("harnesses", 0)),
        "topics": int(counts.get("topics", 0)),
        "insights": int(counts.get("insights", 0)),
    }


# START_ROUTE_DASHBOARD:
@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    """Render the v0.1 home dashboard."""
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "active_nav": "dashboard",
            "counts": _dashboard_counts(request),
        },
    )


@router.get("/partials/dashboard/pulse", response_class=HTMLResponse)
async def dashboard_pulse() -> HTMLResponse:
    """Return a tiny HTMX partial without touching persistent state."""
    return HTMLResponse(
        '<span class="text-emerald-700">HTMX partial rendered; data wiring arrives in Task D.</span>'
    )


# :END_ROUTE_DASHBOARD


# START_ROUTE_LIVE_STUDIO:
# Live Agent Studio is intentionally absent in v0.1; PRD §26.2 limits this slice
# to read-only dashboard navigation and placeholder counts.
# :END_ROUTE_LIVE_STUDIO
