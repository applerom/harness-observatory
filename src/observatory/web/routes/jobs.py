# FILE: src/observatory/web/routes/jobs.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Read-only Job Dashboard for AgentJob lifecycle and semantic trace visibility.
# PRD_REF: docs/PRD.md §11.9, §24, §1162
# WHY_REF: docs/why-graph.xml#UC-JOB-DASHBOARD
# SCOPE: job list; schedule list; job detail; raw log view
# INVARIANTS:
# - Dashboard exposes raw logs but does not parse them into Insights.
# - Missing log files render a clear 404 instead of crashing.
# :END_MODULE_CONTRACT

import json
from dataclasses import dataclass
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from observatory import db
from observatory.models import AgentJob, Harness, RefreshSchedule
from observatory.runtime.semantic_log import DEFAULT_SEMANTIC_EVENT_LOG


TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATE_DIR)
router = APIRouter(prefix="/jobs", tags=["jobs"])


@dataclass(frozen=True)
class JobView:
    job: AgentJob
    target_label: str
    runner_label: str


@dataclass(frozen=True)
class SemanticEventView:
    level: str
    code: str
    anchor: str
    expected: str
    actual: str
    component: str


@dataclass(frozen=True)
class ScheduleView:
    schedule: RefreshSchedule
    harness_label: str


def _job_view(session: Session, job: AgentJob) -> JobView:
    target_label = f"{job.target_kind or 'unknown'} {job.target_id or ''}".strip()
    if job.target_kind == "Harness" and job.target_id is not None:
        harness = session.get(Harness, job.target_id)
        if harness is not None:
            target_label = f"Harness: {harness.name}"
    runner_label = f"{job.runner_name or 'unknown'} {job.runner_version or ''}".strip()
    return JobView(job=job, target_label=target_label, runner_label=runner_label)


def _schedule_view(session: Session, schedule: RefreshSchedule) -> ScheduleView:
    harness_label = f"Harness {schedule.harness_id}"
    harness = session.get(Harness, schedule.harness_id)
    if harness is not None:
        harness_label = harness.name
    return ScheduleView(schedule=schedule, harness_label=harness_label)


# START_ROUTE_JOBS_SEMANTIC_EVENTS:
def _semantic_events_for_job(
    job_id: int,
    path: Path = DEFAULT_SEMANTIC_EVENT_LOG,
    limit: int = 20,
) -> list[SemanticEventView]:
    if not path.exists():
        return []

    events: list[SemanticEventView] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        raw_job_id = payload.get("job_id")
        if not isinstance(raw_job_id, int | str):
            continue
        try:
            event_job_id = int(raw_job_id)
        except ValueError:
            continue
        if event_job_id != job_id:
            continue
        events.append(
            SemanticEventView(
                level=str(payload.get("level") or ""),
                code=str(payload.get("code") or ""),
                anchor=str(payload.get("anchor") or ""),
                expected=str(payload.get("expected") or ""),
                actual=str(payload.get("actual") or ""),
                component=str(payload.get("component") or ""),
            )
        )
    return events[-limit:]


# :END_ROUTE_JOBS_SEMANTIC_EVENTS


# START_ROUTE_JOBS_LIST:
@router.get("", response_class=HTMLResponse)
def job_list(request: Request, session: Session = Depends(db.get_session)) -> HTMLResponse:
    jobs = sorted(session.exec(select(AgentJob)).all(), key=lambda job: job.created_at, reverse=True)
    job_views = [_job_view(session, job) for job in jobs]
    schedules = sorted(
        session.exec(select(RefreshSchedule)).all(),
        key=lambda schedule: (schedule.next_run_at is None, str(schedule.next_run_at or "")),
    )
    schedule_views = [_schedule_view(session, schedule) for schedule in schedules]
    return templates.TemplateResponse(
        request,
        "jobs/index.html",
        {
            "active_nav": "jobs",
            "job_views": job_views,
            "schedule_views": schedule_views,
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
            "job_view": _job_view(session, job),
            "semantic_events": _semantic_events_for_job(job_id),
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
