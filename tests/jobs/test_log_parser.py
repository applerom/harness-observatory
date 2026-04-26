from pathlib import Path

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

import observatory.jobs.log_parser as log_parser
from observatory.jobs.log_parser import parse_job_log, parse_refresh_report
from observatory.models import AgentJob, EvidenceItem, Harness, Insight, Topic


FIXTURE = Path(__file__).parent / "fixtures" / "agent-job-00003-sample.log"


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_parse_refresh_report_extracts_summary_insight_and_evidence_paths() -> None:
    report = parse_refresh_report(FIXTURE.read_text(encoding="utf-8"))

    assert report is not None
    assert report.short_title == "OpenCode refresh found curriculum-focused changes"
    assert "March 27, 2026" in report.body
    assert len(report.evidence) == 6
    assert report.evidence[1].file_path == "architecture/prompt-system.md"
    assert report.evidence[1].line_number == 62
    assert report.evidence[1].topic_slug == "prompt-system"


def test_parse_job_log_creates_proposed_insight_and_evidence_rows(tmp_path: Path) -> None:
    log_path = tmp_path / "agent-job-00003.log"
    log_path.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")

    with make_session() as session:
        harness = Harness(name="OpenCode", slug="opencode")
        prompt_topic = Topic(name="Prompt System", slug="prompt-system")
        file_editing_topic = Topic(name="File Editing", slug="file-editing")
        session.add_all([harness, prompt_topic, file_editing_topic])
        session.commit()
        session.refresh(harness)
        harness_id = harness.id
        prompt_topic_id = prompt_topic.id
        file_editing_topic_id = file_editing_topic.id

        job = AgentJob(
            type="refresh",
            target_kind="Harness",
            target_id=harness_id,
            model="gpt-5.4",
            runner_name="CodexRunner",
            status="done",
            stdout_log_path=log_path.as_posix(),
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        result = parse_job_log(session, job)
        session.refresh(job)
        produced_artifact_ids = job.produced_artifact_ids
        duplicate_result = parse_job_log(session, job)

        insights = session.exec(select(Insight)).all()
        evidence_items = session.exec(select(EvidenceItem)).all()

    assert len(result.insight_ids) == 1
    assert len(result.evidence_item_ids) == 6
    assert produced_artifact_ids == [*result.insight_ids, *result.evidence_item_ids]
    assert duplicate_result.insight_ids == ()
    assert duplicate_result.evidence_item_ids == ()
    assert len(insights) == 1
    assert insights[0].status == "proposed"
    assert insights[0].confidence_band == "unverified"
    assert insights[0].agent_runner == "CodexRunner"
    assert insights[0].agent_model == "gpt-5.4"
    assert insights[0].harness_id == harness_id
    assert len(evidence_items) == 6
    assert {item.insight_id for item in evidence_items} == {insights[0].id}
    assert all(item.harness_id == harness_id for item in evidence_items)
    assert all(item.source_type == "raw-job-log" for item in evidence_items)
    assert all(item.source_location for item in evidence_items)
    assert all(item.file_path for item in evidence_items)
    assert all(item.verifier_agents == ["CodexRunner"] for item in evidence_items)

    prompt_evidence = next(
        item for item in evidence_items if item.file_path == "architecture/prompt-system.md"
    )
    assert prompt_evidence.topic_id == prompt_topic_id
    assert prompt_evidence.line_number == 62

    edit_evidence = next(
        item for item in evidence_items if item.file_path == "series/insert-edit-strategies.md"
    )
    assert edit_evidence.topic_id == file_editing_topic_id


def test_parse_job_log_rolls_back_if_evidence_creation_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    log_path = tmp_path / "agent-job-00003.log"
    log_path.write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")

    with make_session() as session:
        harness = Harness(name="OpenCode", slug="opencode")
        session.add(harness)
        session.commit()
        session.refresh(harness)

        job = AgentJob(
            type="refresh",
            target_kind="Harness",
            target_id=harness.id,
            model="gpt-5.4",
            runner_name="CodexRunner",
            status="done",
            stdout_log_path=log_path.as_posix(),
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        def failing_evidence_item(**_kwargs: object) -> EvidenceItem:
            raise RuntimeError("simulated evidence failure")

        monkeypatch.setattr(log_parser, "EvidenceItem", failing_evidence_item)

        with pytest.raises(RuntimeError, match="simulated evidence failure"):
            parse_job_log(session, job)

        assert session.exec(select(Insight)).all() == []
        assert session.exec(select(EvidenceItem)).all() == []
        session.refresh(job)
        assert job.produced_artifact_ids == []

        monkeypatch.setattr(log_parser, "EvidenceItem", EvidenceItem)
        retry_result = parse_job_log(session, job)

        assert len(retry_result.insight_ids) == 1
        assert len(retry_result.evidence_item_ids) == 6
        assert len(session.exec(select(Insight)).all()) == 1
        assert len(session.exec(select(EvidenceItem)).all()) == 6
