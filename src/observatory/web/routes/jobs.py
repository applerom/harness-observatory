# FILE: src/observatory/web/routes/jobs.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Read-only Job Dashboard for v0.2a AgentJob lifecycle visibility.
# PRD_REF: docs/PRD.md §11.9, §24, §1162
# WHY_REF: docs/why-graph.xml#UC-JOB-DASHBOARD
# SCOPE: job list; job detail; raw log view
# INVARIANTS:
# - Dashboard exposes raw logs but does not parse them into Insights.
# - Missing log files render a clear 404 instead of crashing.
# :END_MODULE_CONTRACT

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from observatory import db
from observatory.models import AgentJob


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATE_DIR)
router = APIRouter(prefix="/jobs", tags=["jobs"])


# START_ROUTE_JOBS_LIST:
@router.get("", response_class=HTMLResponse)
def job_list(request: Request, session: Session = Depends(db.get_session)) -> HTMLResponse:
    jobs = sorted(session.exec(select(AgentJob)).all(), key=lambda job: job.created_at, reverse=True)
    return templates.TemplateResponse(
        request,
        "jobs/index.html",
        {
            "active_nav": "jobs",
            "jobs": jobs,
        },
    )


# :END_ROUTE_JOBS_LIST


# START_ROUTE_JOBS_DETAIL:
@router.get("/{job_id}", response_class=HTMLResponse)
def job_detail(
    job_id: int,
    request: Request,
    session: Session = Depends(db.get_session),
) -> HTMLResponse:
    job = session.get(AgentJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="AgentJob not found")
    return templates.TemplateResponse(
        request,
        "jobs/detail.html",
        {
            "active_nav": "jobs",
            "job": job,
        },
    )


# :END_ROUTE_JOBS_DETAIL


# START_ROUTE_JOBS_LOG:
@router.get("/{job_id}/log", response_class=PlainTextResponse)
def job_log(job_id: int, session: Session = Depends(db.get_session)) -> PlainTextResponse:
    job = session.get(AgentJob, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="AgentJob not found")
    if not job.stdout_log_path:
        raise HTTPException(status_code=404, detail="AgentJob has no raw log yet")
    log_path = Path(job.stdout_log_path)
    if not log_path.exists():
        raise HTTPException(status_code=404, detail="AgentJob raw log file is missing")
    return PlainTextResponse(log_path.read_text(encoding="utf-8"))


# :END_ROUTE_JOBS_LOG
