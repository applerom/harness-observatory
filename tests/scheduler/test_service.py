from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from observatory.models import Harness, RefreshSchedule
from observatory.scheduler.service import (
    compute_next_run_at,
    register_enabled_schedules,
    scheduler_enabled_from_env,
)


class FakeScheduler:
    def __init__(self) -> None:
        self.jobs: list[dict[str, Any]] = []

    def add_job(self, func: Callable[..., object], **kwargs: Any) -> object:
        self.jobs.append({"func": func, **kwargs})
        return kwargs["id"]


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_scheduler_enabled_from_env_is_opt_in() -> None:
    assert scheduler_enabled_from_env(None) is False
    assert scheduler_enabled_from_env("false") is False
    assert scheduler_enabled_from_env("1") is True
    assert scheduler_enabled_from_env("TRUE") is True


def test_compute_next_run_uses_future_next_run() -> None:
    now = datetime(2026, 4, 26, 12, 0, tzinfo=UTC)
    future = now + timedelta(minutes=15)
    schedule = RefreshSchedule(
        harness_id=1,
        enabled=True,
        interval_minutes=60,
        next_run_at=future,
    )

    assert compute_next_run_at(schedule, now=now) == future


def test_compute_next_run_moves_missed_schedule_forward() -> None:
    now = datetime(2026, 4, 26, 12, 0, tzinfo=UTC)
    schedule = RefreshSchedule(
        harness_id=1,
        enabled=True,
        interval_minutes=30,
        last_run_at=now - timedelta(hours=2),
    )

    assert compute_next_run_at(schedule, now=now) == now + timedelta(minutes=30)


def test_register_enabled_schedules_adds_interval_jobs_without_calling_them() -> None:
    calls: list[int] = []

    def fake_job(schedule_id: int) -> None:
        calls.append(schedule_id)

    now = datetime(2026, 4, 26, 12, 0, tzinfo=UTC)
    fake_scheduler = FakeScheduler()

    with make_session() as session:
        harness = Harness(name="OpenCode", slug="opencode")
        disabled_harness = Harness(name="Codex CLI", slug="codex-cli")
        session.add_all([harness, disabled_harness])
        session.commit()

        enabled = RefreshSchedule(
            harness_id=harness.id or 0,
            enabled=True,
            runner_name="codex",
            interval_minutes=45,
            status="idle",
        )
        disabled = RefreshSchedule(
            harness_id=disabled_harness.id or 0,
            enabled=False,
            runner_name="claude",
            interval_minutes=60,
            status="idle",
        )
        session.add_all([enabled, disabled])
        session.commit()

        registered = register_enabled_schedules(session, fake_scheduler, fake_job, now=now)
        stored_schedule = session.exec(
            select(RefreshSchedule).where(RefreshSchedule.enabled == True)  # noqa: E712
        ).one()

    assert calls == []
    assert len(registered) == 1
    assert registered[0].job_id == "refresh-schedule-1"
    assert registered[0].next_run_at == now + timedelta(minutes=45)
    assert stored_schedule.next_run_at == (now + timedelta(minutes=45)).replace(tzinfo=None)
    assert len(fake_scheduler.jobs) == 1
    assert fake_scheduler.jobs[0]["trigger"] == "interval"
    assert fake_scheduler.jobs[0]["minutes"] == 45
    assert fake_scheduler.jobs[0]["kwargs"] == {"schedule_id": 1}
