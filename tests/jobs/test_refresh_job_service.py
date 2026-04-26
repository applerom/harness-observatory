from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from observatory.jobs.service import RefreshJobService
from observatory.models import AgentJob, Harness
from observatory.runners.base import AgentContext, AgentEvent, AgentResult


class RaisingRunner:
    name = "raising"
    version = "test"

    async def run(self, context: AgentContext) -> AgentResult:
        raise RuntimeError(f"boom for job {context.job_id}")

    async def _empty_stream(self) -> AsyncIterator[AgentEvent]:
        if False:
            yield AgentEvent(kind="noop", message="")

    def stream(self, context: AgentContext) -> AsyncIterator[AgentEvent]:
        return self._empty_stream()


def test_refresh_service_marks_unexpected_runner_exception_failed(tmp_path: Path) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        harness = Harness(
            name="OpenCode",
            slug="opencode",
            local_upstream_path=".",
        )
        session.add(harness)
        session.commit()
        session.refresh(harness)

        job = RefreshJobService(RaisingRunner(), log_dir=tmp_path).refresh_harness(session, harness)
        persisted_job = session.get(AgentJob, job.id)

    assert persisted_job is not None
    assert persisted_job.status == "failed"
    assert persisted_job.started_at is not None
    assert persisted_job.finished_at is not None
    assert persisted_job.stdout_log_path is not None
    assert "RuntimeError: boom for job" in (persisted_job.error_message or "")
    assert Path(persisted_job.stdout_log_path).is_file()
    assert "RuntimeError: boom for job" in Path(persisted_job.stdout_log_path).read_text(
        encoding="utf-8"
    )
