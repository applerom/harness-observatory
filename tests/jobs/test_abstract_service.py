import json
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from observatory.abstracts.service import AbstractJobService
from observatory.models import AgentJob, EvidenceItem, Harness, Insight, RevisionNote, Topic


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_abstract_service_creates_job_artifact_revision_log_and_events(tmp_path: Path) -> None:
    with make_session() as session:
        harness = Harness(name="OpenCode", slug="opencode")
        topic = Topic(name="Instruction Files", slug="instruction-files")
        session.add_all([harness, topic])
        session.commit()
        session.refresh(harness)
        session.refresh(topic)
        harness_id = harness.id
        topic_id = topic.id

        source_insight = Insight(
            short_title="Instruction files change authority",
            body="Project instructions enter a strong runtime channel.",
            harness_id=harness_id,
            topic_id=topic_id,
        )
        session.add(source_insight)
        session.commit()
        session.refresh(source_insight)
        source_insight_id = source_insight.id

        evidence = EvidenceItem(
            claim_summary="Instruction loader cites the system path.",
            evidence_class="code-citation",
            source_location="src/session.ts:2",
            harness_id=harness_id,
            topic_id=topic_id,
            insight_id=source_insight_id,
        )
        session.add(evidence)
        session.commit()
        session.refresh(evidence)
        evidence_id = evidence.id

        result = AbstractJobService(log_dir=tmp_path).create_abstract_job(
            session,
            insight_id=source_insight_id or 0,
            evidence_item_ids=[evidence_id or 0],
        )

        job = session.get(AgentJob, result.job_id)
        artifact = session.get(Insight, result.artifact_insight_ids[0])
        revision = session.get(RevisionNote, result.revision_note_ids[0])
        all_evidence = session.exec(select(EvidenceItem)).all()

    assert job is not None
    assert job.type == "abstract"
    assert job.status == "done"
    assert job.target_kind == "Insight"
    assert job.target_id == source_insight_id
    assert job.runner_name == "TemplateAbstractGenerator"
    assert job.produced_artifact_ids == [result.artifact_insight_ids[0]]
    assert job.stdout_log_path is not None
    assert Path(job.stdout_log_path).is_file()

    assert artifact is not None
    assert artifact.format == "mermaid_diagram"
    assert artifact.harness_id == harness_id
    assert artifact.topic_id == topic_id
    assert "flowchart TD" in artifact.body
    assert "Instruction loader cites the system path." in artifact.body

    assert revision is not None
    assert revision.insight_id == artifact.id
    assert f"abstract job #{job.id}" in (revision.note or "")
    assert f"source EvidenceItem ids: {evidence_id}" in (revision.note or "")
    assert all_evidence == [evidence]

    log_text = Path(job.stdout_log_path).read_text(encoding="utf-8")
    assert f"source_insight_id: {source_insight_id}" in log_text
    assert f"source_evidence_item_ids: {evidence_id}" in log_text
    assert f"produced_insight_id: {artifact.id}" in log_text

    semantic_events = read_semantic_events(tmp_path)
    assert [event["code"] for event in semantic_events] == [
        "abstract_job_queued",
        "abstract_job_running",
        "abstract_artifact_created",
    ]
    assert all(event["anchor"] == "START_ABSTRACT_JOB" for event in semantic_events)


def test_abstract_service_uses_evidence_context_when_source_insight_is_unscoped(
    tmp_path: Path,
) -> None:
    with make_session() as session:
        harness = Harness(name="Codex CLI", slug="codex-cli")
        topic = Topic(name="Prompt System", slug="prompt-system")
        session.add_all([harness, topic])
        session.commit()
        session.refresh(harness)
        session.refresh(topic)
        harness_id = harness.id
        topic_id = topic.id

        source_insight = Insight(short_title="Prompt routing matters", body="Prompt routing matters.")
        session.add(source_insight)
        session.commit()
        session.refresh(source_insight)
        source_insight_id = source_insight.id

        evidence = EvidenceItem(
            claim_summary="Prompt routing evidence.",
            harness_id=harness_id,
            topic_id=topic_id,
            insight_id=source_insight_id,
        )
        session.add(evidence)
        session.commit()
        session.refresh(evidence)
        evidence_id = evidence.id

        result = AbstractJobService(log_dir=tmp_path).create_abstract_job(
            session,
            insight_id=source_insight_id or 0,
            evidence_item_ids=[evidence_id or 0],
        )
        artifact = session.get(Insight, result.artifact_insight_ids[0])

    assert artifact is not None
    assert artifact.harness_id == harness_id
    assert artifact.topic_id == topic_id


def test_abstract_service_rejects_missing_evidence(tmp_path: Path) -> None:
    with make_session() as session:
        source_insight = Insight(short_title="Source", body="Source body.")
        session.add(source_insight)
        session.commit()
        session.refresh(source_insight)

        with pytest.raises(ValueError, match="At least one source EvidenceItem is required"):
            AbstractJobService(log_dir=tmp_path).create_abstract_job(
                session,
                insight_id=source_insight.id or 0,
                evidence_item_ids=[],
            )


def read_semantic_events(log_dir: Path) -> list[dict[str, Any]]:
    event_path = log_dir / "semantic-events.jsonl"
    return [
        json.loads(line)
        for line in event_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
