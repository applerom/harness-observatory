import asyncio
import json
from collections.abc import AsyncIterator, Generator
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from observatory import db
from observatory.live.service import stream_live_job
from observatory.models import (
    AgentJob,
    ComparisonCell,
    EvidenceItem,
    Harness,
    Insight,
    RefreshSchedule,
    RevisionNote,
    Topic,
)
from observatory.runners.base import AgentContext, AgentEvent, AgentResult
from observatory.web.app import create_app
from observatory.web.routes.harness import get_refresh_runner_factory
from observatory.web.routes.live import get_live_runner_factory


class FakeRefreshRunner:
    name = "fake"
    version = "test"

    async def run(self, context: AgentContext) -> AgentResult:
        return AgentResult(status="done", output=f"Refreshed {context.target_kind} {context.target_id}")

    async def _empty_stream(self) -> AsyncIterator[AgentEvent]:
        if False:
            yield AgentEvent(kind="noop", message="")

    def stream(self, context: AgentContext) -> AsyncIterator[AgentEvent]:
        return self._empty_stream()


class FakeLiveRunner:
    name = "fake-live"
    version = "test"

    async def run(self, context: AgentContext) -> AgentResult:
        return AgentResult(status="done", output=f"Live run {context.job_id}")

    async def _stream_events(self) -> AsyncIterator[AgentEvent]:
        yield AgentEvent(kind="stdout", message="first live chunk")
        yield AgentEvent(kind="stdout", message="second live chunk")
        yield AgentEvent(kind="status", message="done")

    def stream(self, context: AgentContext) -> AsyncIterator[AgentEvent]:
        return self._stream_events()


class CancellingLiveRunner:
    name = "cancel-live"
    version = "test"

    async def run(self, context: AgentContext) -> AgentResult:
        return AgentResult(status="failed", output=f"Cancelled {context.job_id}")

    async def _stream_events(self) -> AsyncIterator[AgentEvent]:
        yield AgentEvent(kind="stdout", message="partial live chunk")
        raise asyncio.CancelledError

    def stream(self, context: AgentContext) -> AsyncIterator[AgentEvent]:
        return self._stream_events()


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.chdir(tmp_path)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_minimal_data(session)

    def override_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app = create_app()
    app.state.test_engine = engine
    app.dependency_overrides[db.get_session] = override_session
    app.dependency_overrides[get_refresh_runner_factory] = lambda: lambda _runner_name: FakeRefreshRunner()
    app.dependency_overrides[get_live_runner_factory] = lambda: lambda _runner_name: FakeLiveRunner()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def seed_minimal_data(session: Session) -> None:
    harness = Harness(
        name="OpenCode",
        slug="opencode",
        language="TypeScript",
        source_model="multi-provider",
        status_note="imported",
        local_upstream_path=".",
    )
    codex = Harness(
        name="Codex CLI",
        slug="codex-cli",
        language="Rust",
        source_model="OpenAI",
        status_note="imported",
        local_upstream_path=".",
    )
    topic = Topic(
        name="Instruction Files",
        slug="instruction-files",
        definition="Project instructions enter different runtime channels.",
        why_it_matters="Channel placement changes authority.",
    )
    session.add_all([harness, codex, topic])
    session.commit()

    insight = Insight(
        short_title="Instruction files change authority",
        body="OpenCode places project instructions into a stronger runtime channel.",
        why_it_matters="The same filename does not imply the same control plane.",
        topic_id=topic.id,
    )
    cell = ComparisonCell(
        harness_id=harness.id,
        topic_id=topic.id,
        state="present",
        cell_summary="Instruction files are loaded into the system path.",
    )
    session.add_all([insight, cell])
    session.commit()

    evidence = EvidenceItem(
        claim_summary="Instruction file loader cites the system path.",
        evidence_class="markdown-citation",
        source_location="`src/session.ts:2`",
        file_path="src/session.ts",
        line_number=2,
        exact_citation="`src/session.ts:2`",
        code_snippet="loadProjectInstructions(system_context)",
        harness_id=harness.id,
        topic_id=topic.id,
        insight_id=insight.id,
    )
    session.add(evidence)
    session.commit()


def test_dashboard_route_returns_real_counts(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Dashboard" in response.text
    assert "Harnesses" in response.text
    assert "Topics" in response.text
    assert "Insights" in response.text
    assert ">1</p>" in response.text


def test_dashboard_htmx_partial_returns_html(client: TestClient) -> None:
    response = client.get("/partials/dashboard/pulse", headers={"HX-Request": "true"})

    assert response.status_code == 200
    assert "HTMX partial rendered from the server" in response.text


def test_harness_list_and_dossier_render_imported_data(client: TestClient) -> None:
    list_response = client.get("/harnesses")
    dossier_response = client.get("/harnesses/opencode")
    codex_dossier_response = client.get("/harnesses/codex-cli")

    assert list_response.status_code == 200
    assert "OpenCode" in list_response.text
    assert "Codex CLI" in list_response.text
    assert "multi-provider" in list_response.text
    assert dossier_response.status_code == 200
    assert "Instruction Files" in dossier_response.text
    assert "Refresh target: OpenCode" in dossier_response.text
    assert "Run with Codex" in dossier_response.text
    assert "Run with Claude" in dossier_response.text
    assert 'action="/harnesses/opencode/refresh"' in dossier_response.text
    assert codex_dossier_response.status_code == 200
    assert "Refresh target: Codex CLI" in codex_dossier_response.text
    assert 'action="/harnesses/codex-cli/refresh"' in codex_dossier_response.text


def test_topic_list_and_dossier_render_imported_data(client: TestClient) -> None:
    list_response = client.get("/topics")
    dossier_response = client.get("/topics/instruction-files")

    assert list_response.status_code == 200
    assert "Instruction Files" in list_response.text
    assert "Harness coverage" in list_response.text
    assert dossier_response.status_code == 200
    assert "Project instructions enter different runtime channels." in dossier_response.text
    assert "OpenCode" in dossier_response.text
    assert "present" in dossier_response.text


def test_matrix_and_htmx_cell_render_imported_data(client: TestClient) -> None:
    matrix_response = client.get("/matrix")
    cell_response = client.get(
        "/matrix/cells/opencode/instruction-files",
        headers={"HX-Request": "true"},
    )

    assert matrix_response.status_code == 200
    assert "Harness x Topic" in matrix_response.text
    assert 'hx-get="/matrix/cells/opencode/instruction-files"' in matrix_response.text
    assert "not yet verified" in matrix_response.text
    assert cell_response.status_code == 200
    assert "Expanded cell" in cell_response.text
    assert "Instruction files change authority" in cell_response.text
    assert "loadProjectInstructions(system_context)" in cell_response.text


def test_show_the_proof_appears_below_insight_text(client: TestClient) -> None:
    response = client.get("/matrix/cells/opencode/instruction-files")

    assert response.status_code == 200
    insight_index = response.text.index("OpenCode places project instructions")
    proof_index = response.text.index("Show the proof")
    evidence_index = response.text.index("loadProjectInstructions(system_context)")
    assert insight_index < proof_index < evidence_index


def test_opencode_refresh_creates_job_and_raw_log(client: TestClient) -> None:
    response = client.post("/harnesses/opencode/refresh", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/jobs/1"

    detail_response = client.get("/jobs/1")
    log_response = client.get("/jobs/1/log")
    jobs_response = client.get("/jobs")

    assert detail_response.status_code == 200
    assert "Job #1" in detail_response.text
    assert "done" in detail_response.text
    assert "Harness: OpenCode" in detail_response.text
    assert "fake test" in detail_response.text
    assert log_response.status_code == 200
    assert "Refreshed Harness 1" in log_response.text
    assert "runner_result" not in log_response.text
    assert jobs_response.status_code == 200
    assert "Job Dashboard" in jobs_response.text
    assert "#1" in jobs_response.text


def test_non_opencode_refresh_creates_job_and_redirects(client: TestClient) -> None:
    response = client.post("/harnesses/codex-cli/refresh", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/jobs/1"

    detail_response = client.get("/jobs/1")
    log_response = client.get("/jobs/1/log")

    assert detail_response.status_code == 200
    assert "Job #1" in detail_response.text
    assert "Harness: Codex CLI" in detail_response.text
    assert "fake test" in detail_response.text
    assert log_response.status_code == 200
    assert "Refreshed Harness 2" in log_response.text


def test_job_detail_renders_semantic_trace_for_job(client: TestClient) -> None:
    response = client.post("/harnesses/opencode/refresh", follow_redirects=False)
    assert response.status_code == 303

    semantic_log = Path("live-sessions") / "semantic-events.jsonl"
    semantic_log.parent.mkdir(parents=True, exist_ok=True)
    semantic_log.write_text(
        "\n".join(
            [
                "{not-json",
                json.dumps(
                    {
                        "job_id": 2,
                        "level": "error",
                        "code": "wrong_job",
                        "anchor": "START_JOB_REFRESH",
                        "expected": "filtered out",
                        "actual": "filtered out",
                        "component": "RefreshJobService",
                    }
                ),
                json.dumps(
                    {
                        "job_id": 1,
                        "level": "info",
                        "code": "target_cwd_preflight_succeeded",
                        "anchor": "START_JOB_REFRESH",
                        "expected": "target cwd is available before runner execution",
                        "actual": "target cwd available: .",
                        "component": "RefreshJobService",
                    }
                ),
                json.dumps(
                    {
                        "job_id": "1",
                        "level": "info",
                        "code": "runner_result",
                        "anchor": "START_JOB_REFRESH",
                        "expected": "runner returns a terminal AgentResult",
                        "actual": "runner status: done",
                        "component": "RefreshJobService",
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )

    detail_response = client.get("/jobs/1")
    log_response = client.get("/jobs/1/log")

    assert detail_response.status_code == 200
    assert "Semantic Trace" in detail_response.text
    assert "target_cwd_preflight_succeeded" in detail_response.text
    assert "runner_result" in detail_response.text
    assert "START_JOB_REFRESH" in detail_response.text
    assert "runner returns a terminal AgentResult" in detail_response.text
    assert "runner status: done" in detail_response.text
    assert "RefreshJobService" in detail_response.text
    assert "wrong_job" not in detail_response.text
    assert detail_response.text.index("target_cwd_preflight_succeeded") < detail_response.text.index(
        "runner_result"
    )
    assert log_response.status_code == 200
    assert "runner_result" not in log_response.text


def test_job_detail_semantic_trace_empty_state_when_file_missing(client: TestClient) -> None:
    response = client.post("/harnesses/opencode/refresh", follow_redirects=False)
    assert response.status_code == 303

    semantic_log = Path("live-sessions") / "semantic-events.jsonl"
    if semantic_log.exists():
        semantic_log.unlink()

    detail_response = client.get("/jobs/1")

    assert detail_response.status_code == 200
    assert "Semantic Trace" in detail_response.text
    assert "No semantic events recorded for this job yet." in detail_response.text


def test_job_dashboard_empty_state(client: TestClient) -> None:
    response = client.get("/jobs")

    assert response.status_code == 200
    assert "Refresh schedules" in response.text
    assert "No refresh schedules configured yet." in response.text
    assert "No AgentJobs yet" in response.text


def test_job_dashboard_renders_refresh_schedule_metadata(client: TestClient) -> None:
    app = cast(Any, client.app)
    with Session(app.state.test_engine) as session:
        harness = session.exec(select(Harness).where(Harness.slug == "opencode")).one()
        schedule = RefreshSchedule(
            harness_id=harness.id or 0,
            enabled=True,
            runner_name="codex",
            interval_minutes=120,
            status="idle",
        )
        session.add(schedule)
        session.commit()

    response = client.get("/jobs")

    assert response.status_code == 200
    assert "Refresh schedules" in response.text
    assert "OpenCode" in response.text
    assert "codex" in response.text
    assert "120 min" in response.text
    assert "not scheduled" in response.text
    assert "idle" in response.text


def test_curation_queue_lists_unverified_insights_and_actions_write_revision_note(
    client: TestClient,
) -> None:
    queue_response = client.get("/curation")

    assert queue_response.status_code == 200
    assert "Unverified Insights" in queue_response.text
    assert "Instruction files change authority" in queue_response.text
    assert "Any harness" in queue_response.text
    assert "Instruction Files" in queue_response.text
    assert "1 evidence" in queue_response.text
    assert "Mark corrected" not in queue_response.text

    invalid_action_response = client.post(
        "/curation/1/status",
        data={"status": "corrected"},
        follow_redirects=False,
    )
    assert invalid_action_response.status_code == 400

    action_response = client.post(
        "/curation/1/status",
        data={"status": "disputed"},
        follow_redirects=False,
    )
    assert action_response.status_code == 303
    assert action_response.headers["location"] == "/curation"

    app = cast(Any, client.app)
    with Session(app.state.test_engine) as session:
        insight = session.get(Insight, 1)
        revisions = session.exec(select(RevisionNote)).all()

    assert insight is not None
    assert insight.status == "disputed"
    assert insight.confidence_band == "disputed"
    assert len(revisions) == 1
    assert revisions[0].insight_id == 1
    assert "from proposed/unverified to disputed/disputed" in (revisions[0].note or "")

    disputed_queue_response = client.get("/curation")
    assert disputed_queue_response.status_code == 200
    assert "Instruction files change authority" in disputed_queue_response.text
    assert "disputed" in disputed_queue_response.text


def test_live_studio_create_detail_and_stream_lifecycle(client: TestClient) -> None:
    form_response = client.get("/live")
    assert form_response.status_code == 200
    assert "Live Agent Studio" in form_response.text
    assert "OpenCode" in form_response.text
    assert "CodexRunner" in form_response.text

    create_response = client.post(
        "/live",
        data={
            "harness_id": "1",
            "runner_name": "codex",
            "task_prompt": "Find a live teaching detail.",
        },
        follow_redirects=False,
    )
    assert create_response.status_code == 303
    assert create_response.headers["location"] == "/live/1"

    detail_response = client.get("/live/1")
    assert detail_response.status_code == 200
    assert "Live Job #1" in detail_response.text
    assert "Harness: OpenCode" in detail_response.text
    assert "fake-live test" in detail_response.text
    assert "queued" in detail_response.text
    assert "Find a live teaching detail." in detail_response.text
    assert 'href="/jobs/1/log"' in detail_response.text

    app = cast(Any, client.app)
    with Session(app.state.test_engine) as session:
        job_before_stream = session.get(AgentJob, 1)
    assert job_before_stream is not None
    assert job_before_stream.status == "queued"
    assert job_before_stream.prompt_text == "Find a live teaching detail."
    assert job_before_stream.stdout_log_path is None

    with client.stream("GET", "/live/1/stream") as stream_response:
        stream_text = stream_response.read().decode("utf-8")

    assert stream_response.status_code == 200
    assert 'event: status\ndata: {"message": "running", "job_status": "running"}' in stream_text
    assert "first live chunk" in stream_text
    assert "second live chunk" in stream_text
    assert stream_text.index("first live chunk") < stream_text.index("second live chunk")
    assert 'event: status\ndata: {"message": "done", "job_status": "done"}' in stream_text

    with Session(app.state.test_engine) as session:
        job_after_stream = session.get(AgentJob, 1)

    assert job_after_stream is not None
    assert job_after_stream.status == "done"
    assert job_after_stream.stdout_log_path is not None
    log_text = Path(job_after_stream.stdout_log_path).read_text(encoding="utf-8")
    assert "first live chunk" in log_text
    assert "second live chunk" in log_text

    semantic_events = [
        json.loads(line)
        for line in (Path("live-sessions") / "semantic-events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [event["code"] for event in semantic_events] == [
        "live_job_running",
        "live_target_cwd_preflight_succeeded",
        "live_runner_stream_result",
    ]
    assert semantic_events[-1]["anchor"] == "START_ROUTE_LIVE_STREAM"
    assert semantic_events[-1]["actual"] == "runner stream status: done"


def test_live_stream_cancellation_marks_job_failed(client: TestClient) -> None:
    create_response = client.post(
        "/live",
        data={
            "harness_id": "1",
            "runner_name": "codex",
            "task_prompt": "Find a cancellable detail.",
        },
        follow_redirects=False,
    )
    assert create_response.status_code == 303

    async def consume_cancelled_stream() -> list[str]:
        app = cast(Any, client.app)
        with Session(app.state.test_engine) as session:
            chunks: list[str] = []
            async for chunk in stream_live_job(
                session,
                job_id=1,
                runner_factory=lambda _runner_name: CancellingLiveRunner(),
            ):
                chunks.append(chunk)
            return chunks

    chunks = asyncio.run(consume_cancelled_stream())
    assert "partial live chunk" in "".join(chunks)

    app = cast(Any, client.app)
    with Session(app.state.test_engine) as session:
        job = session.get(AgentJob, 1)

    assert job is not None
    assert job.status == "failed"
    assert job.error_message == "Live stream cancelled before terminal runner status"
    assert job.stdout_log_path is not None
    log_text = Path(job.stdout_log_path).read_text(encoding="utf-8")
    assert "partial live chunk" in log_text
    assert "Live stream cancelled before terminal runner status" in log_text

    semantic_events = [
        json.loads(line)
        for line in (Path("live-sessions") / "semantic-events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert semantic_events[-1]["code"] == "live_runner_stream_cancelled"
