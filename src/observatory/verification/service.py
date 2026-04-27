# FILE: src/observatory/verification/service.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Record manual/fake verify job outcomes and derive confidence labels.
# PRD_REF: docs/PRD.md §24 v0.5
# WHY_REF: docs/why-graph.xml#MOD-VERIFY-SERVICE
# SCOPE: verify AgentJob creation; EvidenceItem verification metadata; ObservationReview pass history; Insight and ComparisonCell confidence derivation
# INVARIANTS:
# - Verification pass recording is deterministic and does not call real Codex/Claude runners.
# - Any dispute pass marks affected EvidenceItem, Insight, and ComparisonCell confidence as disputed.
# - Two supporting passes with no dispute mark affected Insight and ComparisonCell confidence as corroborated.
# START_MODULE_MAP:
# - VerificationPass: compact UI/service DTO for one verification outcome.
# - VerificationJobService: writes AgentJob(type="verify") and applies derived labels.
# - verification_passes_for_items: reads ObservationReview JSON history into per-pass DTOs.
# :END_MODULE_MAP
# :END_MODULE_CONTRACT

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, cast

from sqlmodel import Session, select

from observatory.models import AgentJob, ComparisonCell, EvidenceItem, Insight, ObservationReview


VerificationOutcome = Literal["support", "dispute"]
TERMINAL_CONFIDENCE_STATUSES = {"human-verified", "historical", "corrected"}


@dataclass(frozen=True, slots=True)
class VerificationPass:
    evidence_item_id: int
    insight_id: int
    outcome: VerificationOutcome
    verifier_agent: str
    job_id: int | None
    reviewed_at: datetime
    note: str | None = None


class VerificationJobService:
    """Persist deterministic verification outcomes without invoking a real runner."""

    # START_VERIFY_JOB:
    def record_pass(
        self,
        session: Session,
        *,
        insight_id: int,
        evidence_item_id: int,
        outcome: VerificationOutcome,
        verifier_agent: str,
        model: str | None = None,
        runner_name: str | None = None,
        note: str | None = None,
    ) -> AgentJob:
        insight = session.get(Insight, insight_id)
        evidence = session.get(EvidenceItem, evidence_item_id)
        if insight is None:
            raise ValueError(f"Insight {insight_id} was not found")
        if evidence is None:
            raise ValueError(f"EvidenceItem {evidence_item_id} was not found")
        if evidence.insight_id is not None and evidence.insight_id != insight.id:
            raise ValueError(
                f"EvidenceItem {evidence_item_id} is linked to Insight {evidence.insight_id}, "
                f"not Insight {insight_id}"
            )
        if evidence.insight_id is None:
            evidence.insight_id = insight.id

        now = utc_now()
        job = AgentJob(
            type="verify",
            target_kind="Insight",
            target_id=insight.id,
            model=model,
            runner_name=runner_name or verifier_agent,
            trigger="manual",
            status="done",
            created_at=now,
            started_at=now,
            finished_at=now,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        evidence.verification_passes += 1
        evidence.verifier_agents = [*evidence.verifier_agents, verifier_agent]
        evidence.confidence = confidence_from_verification_passes(
            [
                *verification_passes_for_evidence(session, evidence.id or 0),
                VerificationPass(
                    evidence_item_id=evidence.id or 0,
                    insight_id=insight.id or 0,
                    outcome=outcome,
                    verifier_agent=verifier_agent,
                    job_id=job.id,
                    reviewed_at=now,
                    note=note,
                ),
            ]
        )
        session.add(evidence)

        review = ObservationReview(
            reviewed_at=now,
            reviewer=verifier_agent,
            source_snapshot=f"verify-job:{job.id}",
            change_summary=(
                f"Verification pass {outcome} for EvidenceItem {evidence.id} "
                f"on Insight {insight.id}."
            ),
            affected_artifacts=[
                {
                    "kind": "verification_pass",
                    "job_id": job.id,
                    "insight_id": insight.id,
                    "evidence_item_id": evidence.id,
                    "outcome": outcome,
                    "verifier_agent": verifier_agent,
                    "note": note,
                }
            ],
        )
        session.add(review)
        session.commit()
        session.refresh(review)

        job.produced_artifact_ids = [
            artifact_id for artifact_id in (insight.id, evidence.id) if artifact_id is not None
        ]
        session.add(job)
        session.commit()

        refresh_derived_confidence(session, insight)
        session.refresh(job)
        return job

    # :END_VERIFY_JOB


def refresh_derived_confidence(session: Session, insight: Insight) -> None:
    evidence_items = list(
        session.exec(select(EvidenceItem).where(EvidenceItem.insight_id == insight.id)).all()
    )
    passes = verification_passes_for_items(session, evidence_items)
    confidence = confidence_from_verification_passes(passes)
    if insight.status not in TERMINAL_CONFIDENCE_STATUSES:
        insight.status = confidence_to_insight_status(confidence)
    insight.confidence_band = confidence
    session.add(insight)

    if insight.harness_id is not None and insight.topic_id is not None:
        update_cell_confidence(session, insight.harness_id, insight.topic_id, confidence)
    else:
        affected_pairs = {
            (item.harness_id, item.topic_id)
            for item in evidence_items
            if item.harness_id is not None and item.topic_id is not None
        }
        for harness_id, topic_id in affected_pairs:
            update_cell_confidence(session, harness_id or 0, topic_id or 0, confidence)
    session.commit()


def update_cell_confidence(
    session: Session,
    harness_id: int,
    topic_id: int,
    confidence: str,
) -> None:
    cell = session.exec(
        select(ComparisonCell)
        .where(ComparisonCell.harness_id == harness_id)
        .where(ComparisonCell.topic_id == topic_id)
    ).first()
    if cell is None:
        return
    cell.confidence_band = confidence
    cell.updated_at = utc_now()
    session.add(cell)


def confidence_to_insight_status(confidence: str) -> str:
    if confidence == "disputed":
        return "disputed"
    if confidence == "corroborated":
        return "corroborated"
    return "proposed"


def confidence_from_verification_passes(passes: list[VerificationPass]) -> str:
    supports = sum(1 for pass_ in passes if pass_.outcome == "support")
    disputes = sum(1 for pass_ in passes if pass_.outcome == "dispute")
    return confidence_from_pass_counts(supports=supports, disputes=disputes)


def confidence_from_pass_counts(*, supports: int, disputes: int) -> str:
    if disputes > 0:
        return "disputed"
    if supports >= 2:
        return "corroborated"
    if supports == 1:
        return "proposed"
    return "unverified"


def verification_passes_for_evidence(session: Session, evidence_item_id: int) -> list[VerificationPass]:
    return verification_passes_for_items(
        session,
        [item for item in [session.get(EvidenceItem, evidence_item_id)] if item is not None],
    )


def verification_passes_for_items(
    session: Session,
    evidence_items: list[EvidenceItem],
) -> list[VerificationPass]:
    evidence_ids = {item.id for item in evidence_items if item.id is not None}
    if not evidence_ids:
        return []
    passes: list[VerificationPass] = []
    reviews = sorted(
        session.exec(select(ObservationReview)).all(),
        key=lambda review: review.reviewed_at,
    )
    for review in reviews:
        for artifact in review.affected_artifacts:
            if artifact.get("kind") != "verification_pass":
                continue
            evidence_item_id = _int_or_none(artifact.get("evidence_item_id"))
            insight_id = _int_or_none(artifact.get("insight_id"))
            outcome = artifact.get("outcome")
            verifier_agent = artifact.get("verifier_agent")
            if (
                evidence_item_id not in evidence_ids
                or insight_id is None
                or outcome not in {"support", "dispute"}
                or not isinstance(verifier_agent, str)
            ):
                continue
            note_value = artifact.get("note")
            passes.append(
                VerificationPass(
                    evidence_item_id=evidence_item_id,
                    insight_id=insight_id,
                    outcome=cast(VerificationOutcome, outcome),
                    verifier_agent=verifier_agent,
                    job_id=_int_or_none(artifact.get("job_id")),
                    reviewed_at=review.reviewed_at,
                    note=note_value if isinstance(note_value, str) else None,
                )
            )
    return passes


def _int_or_none(value: object) -> int | None:
    if isinstance(value, int):
        return value
    return None


def utc_now() -> datetime:
    return datetime.now(UTC)
