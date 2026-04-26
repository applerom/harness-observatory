# FILE: src/observatory/abstracts/service.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Deterministic abstract AgentJob service for teaching artifacts.
# PRD_REF: docs/PRD.md §24 v0.4b
# WHY_REF: docs/why-graph.xml#MOD-ABSTRACT-SERVICE
# SCOPE: abstract job creation; template artifact generation; raw log persistence; semantic event logging
# INVARIANTS:
# - Abstract jobs do not invoke a real model in the v0.4b slice.
# - Produced teaching artifacts stay linked to the source harness/topic context when available.
# - RevisionNote records the source EvidenceItem ids and producing abstract job id.
# START_MODULE_MAP:
# - AbstractJobService: creates deterministic abstract AgentJobs and produced Insight artifacts.
# - AbstractJobResult: compact result ids for callers/tests.
# :END_MODULE_MAP
# :END_MODULE_CONTRACT

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlmodel import Session

from observatory.models import AgentJob, EvidenceItem, Insight, RevisionNote
from observatory.runtime.semantic_log import SemanticLogWriter


DEFAULT_LOG_DIR = Path("live-sessions")
ABSTRACT_RUNNER_NAME = "TemplateAbstractGenerator"
ABSTRACT_RUNNER_VERSION = "v0.4b"
ABSTRACT_MODEL = "deterministic-template-v0.4b"


@dataclass(frozen=True, slots=True)
class AbstractJobResult:
    """IDs created by one deterministic abstract job run."""

    job_id: int
    artifact_insight_ids: tuple[int, ...]
    revision_note_ids: tuple[int, ...]


class AbstractJobService:
    """Create a deterministic abstract teaching artifact from existing evidence."""

    def __init__(
        self,
        log_dir: Path = DEFAULT_LOG_DIR,
        semantic_log: SemanticLogWriter | None = None,
    ) -> None:
        self.log_dir = log_dir
        self.semantic_log = semantic_log or SemanticLogWriter(log_dir / "semantic-events.jsonl")

    # START_ABSTRACT_JOB:
    def create_abstract_job(
        self,
        session: Session,
        *,
        insight_id: int,
        evidence_item_ids: list[int],
        trigger: str = "manual",
        parent_job_id: int | None = None,
    ) -> AbstractJobResult:
        source_insight = session.get(Insight, insight_id)
        if source_insight is None:
            raise ValueError(f"Insight {insight_id} does not exist")

        evidence_items = load_evidence_items(session, evidence_item_ids)
        if not evidence_items:
            raise ValueError("At least one source EvidenceItem is required")

        job = AgentJob(
            type="abstract",
            target_kind="Insight",
            target_id=source_insight.id,
            model=ABSTRACT_MODEL,
            runner_name=ABSTRACT_RUNNER_NAME,
            runner_version=ABSTRACT_RUNNER_VERSION,
            trigger=trigger,
            parent_job_id=parent_job_id,
            status="queued",
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        self.emit_event(
            level="info",
            code="abstract_job_queued",
            expected="AgentJob(type='abstract') is queued for an existing Insight",
            actual=f"queued abstract job {job.id}",
            job=job,
            metadata={"source_insight_id": source_insight.id, "source_evidence_ids": evidence_item_ids},
        )

        job.started_at = utc_now()
        job.status = "running"
        session.add(job)
        session.commit()
        session.refresh(job)
        self.emit_event(
            level="info",
            code="abstract_job_running",
            expected="Deterministic template generation starts without a model call",
            actual=f"running abstract job {job.id}",
            job=job,
        )

        artifact = build_mermaid_artifact(source_insight, evidence_items)
        artifact.agent_runner = ABSTRACT_RUNNER_NAME
        artifact.agent_model = ABSTRACT_MODEL
        session.add(artifact)
        session.commit()
        session.refresh(artifact)

        note = RevisionNote(
            insight_id=artifact.id,
            created_by=ABSTRACT_RUNNER_NAME,
            note=(
                f"Produced by abstract job #{job.id}; source EvidenceItem ids: "
                f"{', '.join(str(evidence_id) for evidence_id in evidence_item_ids)}."
            ),
        )
        session.add(note)

        job.finished_at = utc_now()
        job.status = "done"
        job.produced_artifact_ids = [artifact.id or 0]
        job.stdout_log_path = write_abstract_log(self.log_dir, job, source_insight, evidence_items, artifact)
        session.add(job)
        session.commit()
        session.refresh(job)
        session.refresh(note)

        self.emit_event(
            level="info",
            code="abstract_artifact_created",
            expected="Abstract job produces a teaching artifact Insight and RevisionNote",
            actual=f"created mermaid Insight {artifact.id}",
            job=job,
            metadata={
                "artifact_insight_id": artifact.id,
                "revision_note_id": note.id,
                "source_evidence_ids": evidence_item_ids,
            },
        )

        return AbstractJobResult(
            job_id=job.id or 0,
            artifact_insight_ids=(artifact.id or 0,),
            revision_note_ids=(note.id or 0,),
        )

    def emit_event(
        self,
        *,
        level: str,
        code: str,
        expected: str,
        actual: str,
        job: AgentJob,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.semantic_log.emit(
            level=level,
            code=code,
            anchor="START_ABSTRACT_JOB",
            expected=expected,
            actual=actual,
            job_id=job.id,
            component="AbstractJobService",
            metadata=metadata,
        )

    # :END_ABSTRACT_JOB


def utc_now() -> datetime:
    return datetime.now(UTC)


def load_evidence_items(session: Session, evidence_item_ids: list[int]) -> list[EvidenceItem]:
    evidence_items: list[EvidenceItem] = []
    for evidence_id in evidence_item_ids:
        evidence = session.get(EvidenceItem, evidence_id)
        if evidence is None:
            raise ValueError(f"EvidenceItem {evidence_id} does not exist")
        evidence_items.append(evidence)
    return evidence_items


def build_mermaid_artifact(source_insight: Insight, evidence_items: list[EvidenceItem]) -> Insight:
    harness_id = source_insight.harness_id or first_non_none(item.harness_id for item in evidence_items)
    topic_id = source_insight.topic_id or first_non_none(item.topic_id for item in evidence_items)
    source_label = mermaid_label(source_insight.short_title)
    evidence_lines = [
        f"    source --> evidence_{index}[\"{mermaid_label(evidence.claim_summary)}\"]"
        for index, evidence in enumerate(evidence_items, start=1)
    ]
    body = "\n".join(
        [
            "flowchart TD",
            f"    source[\"{source_label}\"]",
            *evidence_lines,
            "    source --> teaching[\"Higher-level teaching artifact\"]",
        ]
    )
    return Insight(
        short_title=f"Teaching diagram: {source_insight.short_title}",
        body=body,
        why_it_matters="Turns source evidence into a compact artifact a lecturer can explain first.",
        teaching_value="Use this diagram before expanding the source proof.",
        lecturer_note=(
            "Deterministic v0.4b artifact generated from existing EvidenceItems; no model call."
        ),
        format="mermaid_diagram",
        audience=source_insight.audience or "student-introductory",
        status="proposed",
        confidence_band="unverified",
        harness_id=harness_id,
        topic_id=topic_id,
    )


def first_non_none(values: Iterable[int | None]) -> int | None:
    for value in values:
        if isinstance(value, int):
            return value
    return None


def mermaid_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', "'").replace("\n", " ")[:80]


def write_abstract_log(
    log_dir: Path,
    job: AgentJob,
    source_insight: Insight,
    evidence_items: list[EvidenceItem],
    artifact: Insight,
) -> str:
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"agent-job-{job.id or 0:05d}.log"
    evidence_ids = ", ".join(str(item.id) for item in evidence_items)
    path.write_text(
        "\n".join(
            [
                "# Abstract job",
                f"source_insight_id: {source_insight.id}",
                f"source_evidence_item_ids: {evidence_ids}",
                f"produced_insight_id: {artifact.id}",
                "generator: deterministic-template-v0.4b",
                "",
                artifact.body,
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path.as_posix()
