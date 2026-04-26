import json
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from observatory.explain.service import ExplainJobService
from observatory.models import AgentJob, EvidenceItem, Insight, RevisionNote


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_explain_service_creates_done_job_revision_log_and_events(tmp_path: Path) -> None:
    with make_session() as session:
        insight = Insight(
            short_title="Instruction files change authority",
            body="OpenCode places project instructions into a stronger runtime channel.",
            why_it_matters="The same filename does not imply the same control plane.",
        )
        session.add(insight)
        session.commit()
        session.refresh(insight)
        insight_id = insight.id or 0

        evidence = EvidenceItem(
            claim_summary="Instruction file loader cites the system path.",
            file_path="src/session.ts",
            line_number=2,
            insight_id=insight_id,
        )
        session.add(evidence)
        session.commit()

        job = ExplainJobService(log_dir=tmp_path).create_explain_job(session, insight)
        revisions = session.exec(select(RevisionNote)).all()
        stored_job = session.get(AgentJob, job.id)

    assert stored_job is not None
    assert stored_job.type == "explain"
    assert stored_job.status == "done"
    assert stored_job.target_kind == "Insight"
    assert stored_job.target_id == insight_id
    assert stored_job.runner_name == "deterministic"
    assert stored_job.model == "deterministic-explain-v0.7a"
    assert stored_job.started_at is not None
    assert stored_job.finished_at is not None
    assert stored_job.prompt_text is not None
    assert "Insight body: OpenCode places project instructions" in stored_job.prompt_text
    assert stored_job.produced_artifact_ids == [insight_id]
    assert stored_job.stdout_log_path is not None
    assert Path(stored_job.stdout_log_path).is_file()

    assert len(revisions) == 1
    assert revisions[0].insight_id == insight_id
    assert revisions[0].created_by == "deterministic"
    assert "Instruction files change authority" in (revisions[0].note or "")
    assert "src/session.ts:2" in (revisions[0].note or "")

    log_text = Path(stored_job.stdout_log_path).read_text(encoding="utf-8")
    assert "# Explain job" in log_text
    assert f"insight_id: {insight_id}" in log_text
    assert "Instruction file loader cites the system path." in log_text

    semantic_events = read_semantic_events(tmp_path)
    assert [event["code"] for event in semantic_events] == ["explain_job_done"]
    assert semantic_events[0]["anchor"] == "START_EXPLAIN_JOB"
    assert semantic_events[0]["component"] == "ExplainJobService"


def test_explain_service_rejects_unpersisted_insight(tmp_path: Path) -> None:
    with make_session() as session:
        insight = Insight(short_title="Draft", body="Draft body.")

        with pytest.raises(ValueError, match="persisted"):
            ExplainJobService(log_dir=tmp_path).create_explain_job(session, insight)


def read_semantic_events(log_dir: Path) -> list[dict[str, Any]]:
    event_path = log_dir / "semantic-events.jsonl"
    return [
        json.loads(line)
        for line in event_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
