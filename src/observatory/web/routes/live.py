# FILE: src/observatory/web/routes/live.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Live Agent Studio routes and SSE stream endpoint.
# PRD_REF: docs/PRD.md §11.8, §24
# WHY_REF: docs/why-graph.xml#FEAT-LIVE-AGENT-STUDIO
# SCOPE: studio form; live AgentJob creation; detail page; EventSource stream
# INVARIANTS:
# - GET routes render only; runner execution starts only from /live/{job_id}/stream.
# - Runner execution stays behind the AgentRunner.stream abstraction.
# :END_MODULE_CONTRACT

from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from observatory import db
from observatory.live.service import create_live_discover_job, stream_live_job
from observatory.models import AgentJob, Harness
from observatory.runners.base import AgentRunner
from observatory.web.routes.harness import make_refresh_runner
from observatory.web.routes.jobs import _job_view


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATE_DIR)
router = APIRouter(prefix="/live", tags=["live"])

LiveRunnerFactory = Callable[[str], AgentRunner]


def make_live_runner(runner_name: str) -> AgentRunner:
    return make_refresh_runner(runner_name)


def get_live_runner_factory() -> LiveRunnerFactory:
    return make_live_runner


# START_ROUTE_LIVE_STUDIO:
# START_ROUTE_LIVE_START:
@router.get("", response_class=HTMLResponse)
def live_studio(request: Request, session: Session = Depends(db.get_session)) -> HTMLResponse:
    harnesses = session.exec(select(Harness).order_by(Harness.name)).all()
    return templates.TemplateResponse(
        request,
        "live/index.html",
        {
            "active_nav": "live",
            "harnesses": harnesses,
        },
    )


@router.post("", response_class=RedirectResponse)
def create_live_job(
    harness_id: int = Form(...),
    runner_name: str = Form(default="codex"),
    task_prompt: str = Form(...),
    session: Session = Depends(db.get_session),
    runner_factory: LiveRunnerFactory = Depends(get_live_runner_factory),
) -> RedirectResponse:
    harness = session.get(Harness, harness_id)
    if harness is None:
        raise HTTPException(status_code=404, detail="Harness not found")
    if not task_prompt.strip():
        raise HTTPException(status_code=400, detail="Task prompt is required")
    runner = runner_factory(runner_name)
    job = create_live_discover_job(
        session,
        harness=harness,
        runner=runner,
        task_prompt=task_prompt,
    )
    return RedirectResponse(url=f"/live/{job.id}", status_code=303)


# :END_ROUTE_LIVE_START


@router.get("/{job_id}", response_class=HTMLResponse)
def live_job_detail(
    job_id: int,
    request: Request,
    session: Session = Depends(db.get_session),
) -> HTMLResponse:
    job = session.get(AgentJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="AgentJob not found")
    return templates.TemplateResponse(
        request,
        "live/detail.html",
        {
            "active_nav": "live",
            "job_view": _job_view(session, job),
        },
    )


# START_ROUTE_LIVE_STREAM:
@router.get("/{job_id}/stream")
async def live_job_stream(
    job_id: int,
    session: Session = Depends(db.get_session),
    runner_factory: LiveRunnerFactory = Depends(get_live_runner_factory),
) -> StreamingResponse:
    return StreamingResponse(
        stream_live_job(session, job_id=job_id, runner_factory=runner_factory),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# :END_ROUTE_LIVE_STREAM
# :END_ROUTE_LIVE_STUDIO
