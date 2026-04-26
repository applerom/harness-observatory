import json
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from observatory.jobs.service import RefreshJobService
from observatory.models import AgentJob, EvidenceItem, Harness, Insight, Topic
from observatory.runners.base import AgentContext, AgentEvent, AgentResult


FIXTURE = Path(__file__).parent / "fixtures" / "agent-job-00003-sample.log"


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


class SuccessfulRunner:
    name = "successful"
    version = "test"

    async def run(self, _context: AgentContext) -> AgentResult:
        return AgentResult(status="done", output=FIXTURE.read_text(encoding="utf-8"))

    async def _empty_stream(self) -> AsyncIterator[AgentEvent]:
        if False:
            yield AgentEvent(kind="noop", message="")

    def stream(self, context: AgentContext) -> AsyncIterator[AgentEvent]:
        return self._empty_stream()


class RecordingRunner:
    name = "recording"
    version = "test"

    def __init__(self) -> None:
        self.called = False

    async def run(self, _context: AgentContext) -> AgentResult:
        self.called = True
        return AgentResult(status="done", output=FIXTURE.read_text(encoding="utf-8"))

    async def _empty_stream(self) -> AsyncIterator[AgentEvent]:
        if False:
            yield AgentEvent(kind="noop", message="")

    def stream(self, context: AgentContext) -> AsyncIterator[AgentEvent]:
        return self._empty_stream()


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_refresh_service_parses_successful_job_log_into_artifacts(tmp_path: Path) -> None:
    with make_session() as session:
        harness = Harness(
            name="OpenCode",
            slug="opencode",
            local_upstream_path=".",
        )
        prompt_topic = Topic(name="Prompt System", slug="prompt-system")
        session.add_all([harness, prompt_topic])
        session.commit()
        session.refresh(harness)

        job = RefreshJobService(SuccessfulRunner(), log_dir=tmp_path).refresh_harness(session, harness)
        persisted_job = session.get(AgentJob, job.id)
        insights = session.exec(select(Insight)).all()
        evidence_items = session.exec(select(EvidenceItem)).all()

    assert persisted_job is not None
    assert persisted_job.status == "done"
    assert persisted_job.stdout_log_path is not None
    assert Path(persisted_job.stdout_log_path).is_file()
    assert persisted_job.produced_artifact_ids
    assert len(insights) == 1
    assert insights[0].status == "proposed"
    assert len(evidence_items) == 6
    assert {item.insight_id for item in evidence_items} == {insights[0].id}
    semantic_events = read_semantic_events(tmp_path)
    assert [event["code"] for event in semantic_events] == [
        "job_queued",
        "job_running",
        "target_cwd_preflight_succeeded",
        "runner_result",
        "parser_succeeded",
    ]


def test_refresh_service_marks_parser_failure_failed_and_appends_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raising_parser(_session: Session, _job: AgentJob) -> None:
        raise ValueError("bad parser shape")

    monkeypatch.setattr("observatory.jobs.service.parse_job_log", raising_parser)

    with make_session() as session:
        harness = Harness(
            name="OpenCode",
            slug="opencode",
            local_upstream_path=".",
        )
        session.add(harness)
        session.commit()
        session.refresh(harness)

        job = RefreshJobService(SuccessfulRunner(), log_dir=tmp_path).refresh_harness(session, harness)
        persisted_job = session.get(AgentJob, job.id)
        insights = session.exec(select(Insight)).all()
        evidence_items = session.exec(select(EvidenceItem)).all()

    assert persisted_job is not None
    assert persisted_job.status == "failed"
    assert persisted_job.stdout_log_path is not None
    assert persisted_job.error_message is not None
    assert "Parser failed after successful runner output: ValueError: bad parser shape" in (
        persisted_job.error_message
    )

    log_text = Path(persisted_job.stdout_log_path).read_text(encoding="utf-8")
    assert "## Summary" in log_text
    assert "[parser error]" in log_text
    assert "ValueError: bad parser shape" in log_text
    assert log_text.index("## Summary") < log_text.index("[parser error]")
    assert insights == []
    assert evidence_items == []
    semantic_events = read_semantic_events(tmp_path)
    assert semantic_events[-1]["code"] == "parser_failed"
    assert "ValueError: bad parser shape" in str(semantic_events[-1]["actual"])


def test_refresh_service_marks_unexpected_runner_exception_failed_without_parsing(
    tmp_path: Path,
) -> None:
    with make_session() as session:
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
        insights = session.exec(select(Insight)).all()
        evidence_items = session.exec(select(EvidenceItem)).all()

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
    assert insights == []
    assert evidence_items == []
    semantic_events = read_semantic_events(tmp_path)
    assert semantic_events[-1]["code"] == "runner_result"
    assert semantic_events[-1]["level"] == "error"


def test_refresh_service_fails_missing_target_cwd_before_runner_call(tmp_path: Path) -> None:
    runner = RecordingRunner()

    with make_session() as session:
        harness = Harness(
            name="OpenCode",
            slug="opencode",
            local_upstream_path=str(tmp_path / "missing-opencode"),
        )
        session.add(harness)
        session.commit()
        session.refresh(harness)

        job = RefreshJobService(runner, log_dir=tmp_path).refresh_harness(session, harness)
        persisted_job = session.get(AgentJob, job.id)
        insights = session.exec(select(Insight)).all()
        evidence_items = session.exec(select(EvidenceItem)).all()

    assert persisted_job is not None
    assert persisted_job.status == "failed"
    assert persisted_job.stdout_log_path is not None
    assert persisted_job.error_message is not None
    assert "harness.local_upstream_path does not exist" in persisted_job.error_message
    assert not runner.called
    log_text = Path(persisted_job.stdout_log_path).read_text(encoding="utf-8")
    assert "Target cwd preflight failed" in log_text
    assert insights == []
    assert evidence_items == []
    semantic_events = read_semantic_events(tmp_path)
    assert [event["code"] for event in semantic_events] == [
        "job_queued",
        "job_running",
        "target_cwd_preflight_failed",
    ]


def read_semantic_events(log_dir: Path) -> list[dict[str, object]]:
    event_path = log_dir / "semantic-events.jsonl"
    return [
        json.loads(line)
        for line in event_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
