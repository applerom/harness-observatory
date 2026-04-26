from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from observatory import db
from observatory.models import ComparisonCell, EvidenceItem, Harness, Insight, Topic
from observatory.web.app import create_app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
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
    )
    topic = Topic(
        name="Instruction Files",
        slug="instruction-files",
        definition="Project instructions enter different runtime channels.",
        why_it_matters="Channel placement changes authority.",
    )
    session.add_all([harness, topic])
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

    assert list_response.status_code == 200
    assert "OpenCode" in list_response.text
    assert "multi-provider" in list_response.text
    assert dossier_response.status_code == 200
    assert "Instruction Files" in dossier_response.text
    assert "Refresh" in dossier_response.text
    assert "Agent jobs available from v0.2" in dossier_response.text


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
