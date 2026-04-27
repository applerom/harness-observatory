from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from observatory import db
from observatory.models import ComparisonCell, Harness, Insight, Topic
from observatory.web.app import create_app


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
        harness = Harness(name="OpenCode", slug="opencode", language="TypeScript")
        topic = Topic(name="Instruction Files", slug="instruction-files")
        session.add_all([harness, topic])
        session.commit()
        session.refresh(harness)
        session.refresh(topic)
        session.add(
            ComparisonCell(
                harness_id=harness.id or 0,
                topic_id=topic.id or 0,
                state="present",
                cell_summary="Instruction files are present.",
            )
        )
        session.add(
            Insight(
                short_title="Instruction file hook",
                body="Instruction files make a useful teaching hook.",
                engagement_hook="Wait for instruction files.",
                harness_id=harness.id,
                topic_id=topic.id,
            )
        )
        session.commit()

    def override_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app = create_app()
    app.dependency_overrides[db.get_session] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_exports_page_renders_empty_state(client: TestClient) -> None:
    response = client.get("/exports")

    assert response.status_code == 200
    assert "Generated Markdown Exports" in response.text
    assert "No generated Markdown files yet." in response.text
    assert 'action="/exports/generate"' in response.text


def test_exports_generate_action_writes_files_and_redirects(client: TestClient, tmp_path: Path) -> None:
    source = tmp_path / "harness-architecture"
    (source / "registry").mkdir(parents=True)
    (source / "registry" / "harnesses.md").write_text("# Harnesses\n", encoding="utf-8")

    response = client.post(
        "/exports/generate",
        data={"legacy_source_path": source.as_posix()},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/exports?generated=1"
    assert (tmp_path / "generated-docs" / "comparison-report.md").exists()
    assert (tmp_path / "generated-docs" / "legacy-data" / "ARCHIVE-MANIFEST.md").exists()

    page = client.get("/exports?generated=1")
    assert page.status_code == 200
    assert "Export generation completed" in page.text
    assert "comparison-report.md" in page.text
    assert "legacy-data/ARCHIVE-MANIFEST.md" in page.text
