from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from observatory.models import (
    AgentJob,
    ComparisonCell,
    EvidenceItem,
    Harness,
    Insight,
    ObservationReview,
    Topic,
)
from observatory.verification.service import VerificationJobService


def test_support_passes_corroborate_evidence_insight_and_cell() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        insight, evidence = seed_verification_target(session)

        service = VerificationJobService()
        first_job = service.record_pass(
            session,
            insight_id=insight.id or 0,
            evidence_item_id=evidence.id or 0,
            outcome="support",
            verifier_agent="fake-codex",
            model="test-model",
            runner_name="fake-runner",
            note="Citation still supports the claim.",
        )
        second_job = service.record_pass(
            session,
            insight_id=insight.id or 0,
            evidence_item_id=evidence.id or 0,
            outcome="support",
            verifier_agent="fake-claude",
        )

        stored_evidence = session.get(EvidenceItem, evidence.id)
        stored_insight = session.get(Insight, insight.id)
        stored_cell = session.exec(select(ComparisonCell)).one()
        jobs = sorted(session.exec(select(AgentJob)).all(), key=lambda job: job.id or 0)
        reviews = sorted(
            session.exec(select(ObservationReview)).all(),
            key=lambda review: review.id or 0,
        )

    assert first_job.type == "verify"
    assert first_job.status == "done"
    assert first_job.target_kind == "Insight"
    assert second_job.produced_artifact_ids == [insight.id, evidence.id]
    assert [job.type for job in jobs] == ["verify", "verify"]
    assert stored_evidence is not None
    assert stored_evidence.verification_passes == 2
    assert stored_evidence.verifier_agents == ["fake-codex", "fake-claude"]
    assert stored_evidence.confidence == "corroborated"
    assert stored_insight is not None
    assert stored_insight.status == "corroborated"
    assert stored_insight.confidence_band == "corroborated"
    assert stored_cell.confidence_band == "corroborated"
    assert len(reviews) == 2
    assert reviews[0].reviewer == "fake-codex"
    assert reviews[0].affected_artifacts[0]["outcome"] == "support"
    assert reviews[0].affected_artifacts[0]["note"] == "Citation still supports the claim."


def test_dispute_pass_overrides_prior_support() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        insight, evidence = seed_verification_target(session)
        service = VerificationJobService()

        service.record_pass(
            session,
            insight_id=insight.id or 0,
            evidence_item_id=evidence.id or 0,
            outcome="support",
            verifier_agent="fake-codex",
        )
        service.record_pass(
            session,
            insight_id=insight.id or 0,
            evidence_item_id=evidence.id or 0,
            outcome="dispute",
            verifier_agent="fake-claude",
            note="The cited file no longer contains the behavior.",
        )

        stored_evidence = session.get(EvidenceItem, evidence.id)
        stored_insight = session.get(Insight, insight.id)
        stored_cell = session.exec(select(ComparisonCell)).one()
        reviews = sorted(
            session.exec(select(ObservationReview)).all(),
            key=lambda review: review.id or 0,
        )

    assert stored_evidence is not None
    assert stored_evidence.verification_passes == 2
    assert stored_evidence.confidence == "disputed"
    assert stored_insight is not None
    assert stored_insight.status == "disputed"
    assert stored_insight.confidence_band == "disputed"
    assert stored_cell.confidence_band == "disputed"
    assert reviews[-1].affected_artifacts[0]["outcome"] == "dispute"
    assert reviews[-1].affected_artifacts[0]["note"] == "The cited file no longer contains the behavior."


def test_verification_links_orphan_evidence_before_deriving_confidence() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        insight, evidence = seed_verification_target(session)
        evidence.insight_id = None
        session.add(evidence)
        session.commit()

        service = VerificationJobService()
        service.record_pass(
            session,
            insight_id=insight.id or 0,
            evidence_item_id=evidence.id or 0,
            outcome="support",
            verifier_agent="fake-codex",
        )
        service.record_pass(
            session,
            insight_id=insight.id or 0,
            evidence_item_id=evidence.id or 0,
            outcome="support",
            verifier_agent="fake-claude",
        )

        stored_evidence = session.get(EvidenceItem, evidence.id)
        stored_insight = session.get(Insight, insight.id)
        stored_cell = session.exec(select(ComparisonCell)).one()

    assert stored_evidence is not None
    assert stored_evidence.insight_id == insight.id
    assert stored_evidence.confidence == "corroborated"
    assert stored_insight is not None
    assert stored_insight.confidence_band == "corroborated"
    assert stored_cell.confidence_band == "corroborated"


def seed_verification_target(session: Session) -> tuple[Insight, EvidenceItem]:
    harness = Harness(name="OpenCode", slug="opencode")
    topic = Topic(name="Instruction Files", slug="instruction-files")
    session.add_all([harness, topic])
    session.commit()

    insight = Insight(
        short_title="Instruction files change authority",
        body="OpenCode places instructions into a stronger channel.",
        harness_id=harness.id,
        topic_id=topic.id,
    )
    cell = ComparisonCell(
        harness_id=harness.id or 0,
        topic_id=topic.id or 0,
        state="present",
    )
    session.add_all([insight, cell])
    session.commit()

    evidence = EvidenceItem(
        claim_summary="Instruction loading uses the system path.",
        harness_id=harness.id,
        topic_id=topic.id,
        insight_id=insight.id,
    )
    session.add(evidence)
    session.commit()
    session.refresh(insight)
    session.refresh(evidence)
    return insight, evidence
