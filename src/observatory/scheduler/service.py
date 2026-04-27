# FILE: src/observatory/scheduler/service.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Small APScheduler-facing service for per-harness refresh schedules.
# PRD_REF: docs/PRD.md §24 v0.3
# WHY_REF: docs/why-graph.xml#FEAT-CRON-SCHEDULER
# SCOPE: next-run computation; enabled schedule registration; env-gated startup helper
# INVARIANTS:
# - Importing this module never starts a scheduler.
# - Registration accepts an injected job callable so tests do not invoke real runners.
# - Missed or unset run times are moved forward instead of firing immediately on startup.
# :END_MODULE_CONTRACT

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from sqlmodel import Session, select

from observatory.models import RefreshSchedule

SCHEDULER_ENABLED_ENV = "OBSERVATORY_SCHEDULER_ENABLED"
TRUE_ENV_VALUES = frozenset({"1", "true", "yes", "on"})


# START_SCHEDULER_SERVICE:
class SchedulerLike(Protocol):
    def add_job(self, func: Callable[..., object], **kwargs: Any) -> object:
        """Subset of APScheduler's add_job API used by this slice."""
        ...


@dataclass(frozen=True, slots=True)
class RegisteredSchedule:
    schedule_id: int
    job_id: str
    next_run_at: datetime


RefreshJobCallable = Callable[..., object]


def scheduler_enabled_from_env(value: str | None) -> bool:
    return (value or "").strip().lower() in TRUE_ENV_VALUES


# START_SCHEDULER_COMPUTE_NEXT_RUN:
def compute_next_run_at(
    schedule: RefreshSchedule,
    *,
    now: datetime | None = None,
) -> datetime:
    current_time = now or datetime.now(UTC)
    interval = timedelta(minutes=max(schedule.interval_minutes, 1))
    explicit_next = _ensure_aware(schedule.next_run_at)
    if explicit_next is not None and explicit_next > current_time:
        return explicit_next

    last_run_at = _ensure_aware(schedule.last_run_at)
    if last_run_at is not None and last_run_at + interval > current_time:
        return last_run_at + interval

    return current_time + interval


# :END_SCHEDULER_COMPUTE_NEXT_RUN


# START_SCHEDULER_REGISTER:
def register_enabled_schedules(
    session: Session,
    scheduler: SchedulerLike,
    job_callable: RefreshJobCallable,
    *,
    now: datetime | None = None,
) -> list[RegisteredSchedule]:
    schedules = session.exec(
        select(RefreshSchedule).where(RefreshSchedule.enabled == True)  # noqa: E712
    ).all()
    registered: list[RegisteredSchedule] = []
    for schedule in schedules:
        if schedule.id is None:
            continue
        next_run_at = compute_next_run_at(schedule, now=now)
        schedule.next_run_at = next_run_at
        schedule.updated_at = datetime.now(UTC)
        session.add(schedule)
        job_id = scheduler_job_id(schedule)
        scheduler.add_job(
            job_callable,
            trigger="interval",
            minutes=max(schedule.interval_minutes, 1),
            id=job_id,
            replace_existing=True,
            next_run_time=next_run_at,
            kwargs={"schedule_id": schedule.id},
        )
        registered.append(
            RegisteredSchedule(
                schedule_id=schedule.id,
                job_id=job_id,
                next_run_at=next_run_at,
            )
        )
    session.commit()
    return registered


def scheduler_job_id(schedule: RefreshSchedule) -> str:
    return f"refresh-schedule-{schedule.id}"


# :END_SCHEDULER_REGISTER


def _ensure_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


# :END_SCHEDULER_SERVICE
