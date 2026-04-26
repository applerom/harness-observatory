import json
from collections.abc import AsyncIterator, Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from observatory import db
from observatory.models import ComparisonCell, EvidenceItem, Harness, Insight, Topic
from observatory.runners.base import AgentContext, AgentEvent, AgentResult
from observatory.web.app import create_app
from observatory.web.routes.harness import get_refresh_runner_factory


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
    app.dependency_overrides[db.get_session] = override_session
    app.dependency_overrides[get_refresh_runner_factory] = lambda: lambda _runner_name: FakeRefreshRunner()
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
    assert "No AgentJobs yet" in response.text
