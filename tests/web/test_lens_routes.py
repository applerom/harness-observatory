from collections.abc import Generator
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from observatory import db
from observatory.models import ComparisonCell, EvidenceItem, Harness, Insight, Score, Topic
from observatory.web.app import create_app


@pytest.fixture()
def lens_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.chdir(tmp_path)
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_route_data(session)

    def override_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app = create_app()
    app.state.test_engine = engine
    app.dependency_overrides[db.get_session] = override_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_lens_page_seeds_and_renders_default_lenses(lens_client: TestClient) -> None:
    response = lens_client.get("/lenses")

    assert response.status_code == 200
    assert "Scores by lens" in response.text
    assert "Research" in response.text
    assert "Lecturer" in response.text
    assert "Practical Selection" in response.text
    assert "Ecosystem" in response.text
    assert "not a universal ranking" in response.text
    assert "No scores yet" in response.text


def test_lens_refresh_action_writes_scores_and_redirects(lens_client: TestClient) -> None:
    response = lens_client.post("/lenses/refresh", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/lenses?refreshed=1"

    page = lens_client.get(response.headers["location"])
    assert page.status_code == 200
    assert "Lens scores refreshed from current DB signals." in page.text
    assert "OpenCode" in page.text
    assert "Instruction Files" in page.text
    assert "state=present; confidence=unverified; evidence=1; insights=1" in page.text

    test_engine = cast(Engine, cast(Any, lens_client.app).state.test_engine)
    with Session(test_engine) as session:
        scores = session.exec(select(Score)).all()

    assert len(scores) == 4


def seed_route_data(session: Session) -> None:
    harness = Harness(name="OpenCode", slug="opencode", local_upstream_path=".")
    topic = Topic(name="Instruction Files", slug="instruction-files")
    session.add_all([harness, topic])
    session.commit()

    insight = Insight(
        short_title="Instruction files change authority",
        body="Instruction files enter a stronger runtime channel.",
        harness_id=harness.id,
        topic_id=topic.id,
    )
    cell = ComparisonCell(
        harness_id=harness.id,
        topic_id=topic.id,
        state="present",
        confidence_band="unverified",
    )
    evidence = EvidenceItem(
        claim_summary="Instruction loader cites the system path.",
        evidence_class="markdown-citation",
        file_path="src/session.ts",
        harness_id=harness.id,
        topic_id=topic.id,
        insight_id=insight.id,
    )
    session.add_all([insight, cell, evidence])
    session.commit()
