# FILE: src/observatory/web/app.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: FastAPI application factory for the web surface.
# PRD_REF: docs/PRD.md §20, §24, §26.2, §26.6
# WHY_REF: docs/why-graph.xml MOD-WEB-APP
# SCOPE: app construction; router registration; static asset mounting; env-gated scheduler lifespan
# INVARIANTS:
# - create_app is side-effect light and safe for uvicorn --factory and TestClient.
# - Scheduler startup is opt-in by env and never happens at import time.
# :END_MODULE_CONTRACT

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore[import-untyped]
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session

from observatory import db
from observatory.jobs.service import RefreshJobService
from observatory.models import Harness, RefreshSchedule
from observatory.scheduler.service import (
    SCHEDULER_ENABLED_ENV,
    compute_next_run_at,
    register_enabled_schedules,
    scheduler_enabled_from_env,
)
from observatory.web.routes.harness import make_refresh_runner
from observatory.web.routes import register_routes


PACKAGE_ROOT = Path(__file__).resolve().parent


# START_APP_FACTORY:
def create_app() -> FastAPI:
    """Create and configure the Harness Observatory FastAPI app."""
    app = FastAPI(title="Harness Observatory", version="0.1.0", lifespan=app_lifespan)

    # START_APP_DB_INIT:
    # Persistent schema creation is owned by Alembic/importer commands; the app only
    # opens read-only sessions against the configured local SQLite database.
    # :END_APP_DB_INIT

    static_dir = PACKAGE_ROOT / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # START_APP_ROUTERS:
    register_routes(app)
    # :END_APP_ROUTERS

    return app


# :END_APP_FACTORY


# START_APP_SCHEDULER:
@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncIterator[None]:
    scheduler: Any | None = None
    if scheduler_enabled_from_env(os.getenv(SCHEDULER_ENABLED_ENV)):
        scheduler = BackgroundScheduler(timezone="UTC")
        with Session(db.engine) as session:
            register_enabled_schedules(session, scheduler, _run_scheduled_refresh)
        scheduler.start()
        app.state.scheduler = scheduler
    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)


def _run_scheduled_refresh(schedule_id: int) -> None:
    with Session(db.engine) as session:
        schedule = session.get(RefreshSchedule, schedule_id)
        if schedule is None or not schedule.enabled:
            return
        harness = session.get(Harness, schedule.harness_id)
        if harness is None:
            schedule.status = "failed"
            schedule.note = "Scheduled harness no longer exists"
            schedule.updated_at = datetime.now(UTC)
            session.add(schedule)
            session.commit()
            return
        runner = make_refresh_runner(schedule.runner_name)
        job = RefreshJobService(runner).refresh_harness(session, harness, trigger="cron")
        now = datetime.now(UTC)
        schedule.last_run_at = now
        schedule.last_job_id = job.id
        schedule.status = job.status
        schedule.note = job.error_message
        schedule.next_run_at = compute_next_run_at(schedule, now=now)
        schedule.updated_at = now
        session.add(schedule)
        session.commit()


# :END_APP_SCHEDULER
