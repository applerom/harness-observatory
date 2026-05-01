# FILE: src/observatory/explain/service.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: Deterministic explain AgentJob service for per-Insight explanations.
# PRD_REF: docs/PRD.md §14.2 Job types
# WHY_REF: docs/why-graph.xml#MOD-EXPLAIN-SERVICE
# SCOPE: explain AgentJob creation; prompt rendering; RevisionNote persistence; raw log persistence; semantic event logging
# INVARIANTS:
# - v0.7a explain jobs do not invoke a real model.
# - Explanations are appended as RevisionNotes and do not replace the original Insight body.
# - AgentJob.produced_artifact_ids contains the explained Insight id for Job Dashboard traceability.
# START_MODULE_MAP:
# - ExplainJobService: creates deterministic explain AgentJobs and RevisionNotes.
# - create_explain_job: convenience wrapper using the default service.
# :END_MODULE_MAP
# :END_MODULE_CONTRACT

from dataclasses import dataclass
from pathlib import Path

from sqlmodel import Session, select

from observatory.models import AgentJob, EvidenceItem, Insight, PromptTemplate, RevisionNote, utc_now
from observatory.runtime.semantic_log import SemanticLogWriter


DEFAULT_LOG_DIR = Path("live-sessions")
EXPLAIN_TEMPLATE_NAME = "insight-explain-v0.7a"
EXPLAIN_TEMPLATE_VERSION = "0.7a"
EXPLAIN_RUNNER_NAME = "deterministic"
EXPLAIN_RUNNER_VERSION = "explain-v0.7a"
EXPLAIN_MODEL = "deterministic-explain-v0.7a"


@dataclass(frozen=True, slots=True)
class ExplainJobResult:
    """IDs created by one deterministic explain job run."""

    job_id: int
    revision_note_id: int


class ExplainJobService:
    """Create a deterministic explanation for an existing Insight."""

    def __init__(
        self,
        log_dir: Path = DEFAULT_LOG_DIR,
        semantic_log: SemanticLogWriter | None = None,
    ) -> None:
        self.log_dir = log_dir
        self.semantic_log = semantic_log or SemanticLogWriter(log_dir / "semantic-events.jsonl")

    # START_EXPLAIN_JOB:
    def create_explain_job(
        self,
        session: Session,
        insight: Insight,
        trigger: str = "manual",
        evidence_item_ids: list[int] | None = None,
    ) -> AgentJob:
        if insight.id is None:
            raise ValueError("Insight must be persisted before it can be explained")

        template = ensure_explain_prompt_template(session)
        evidence_items = load_evidence_for_insight(session, insight, evidence_item_ids)
        explanation = deterministic_explanation(insight, evidence_items)
        prompt_text = render_explain_prompt(template, insight, evidence_items)
        now = utc_now()

        note = RevisionNote(
            insight_id=insight.id,
            note=explanation,
            created_by=EXPLAIN_RUNNER_NAME,
            created_at=now,
        )
        job = AgentJob(
            type="explain",
            target_kind="Insight",
            target_id=insight.id,
            prompt_template_id=template.id,
            prompt_text=prompt_text,
            model=EXPLAIN_MODEL,
            runner_name=EXPLAIN_RUNNER_NAME,
            runner_version=EXPLAIN_RUNNER_VERSION,
            trigger=trigger,
            status="done",
            created_at=now,
            started_at=now,
            finished_at=now,
            produced_artifact_ids=[insight.id],
        )
        session.add(note)
        session.add(job)
        session.commit()
        session.refresh(note)
        session.refresh(job)

        job.stdout_log_path = write_explain_log(
            self.log_dir,
            job,
            insight,
            evidence_items,
            explanation,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        self.semantic_log.emit(
            level="info",
            code="explain_job_done",
            anchor="START_EXPLAIN_JOB",
            expected="Deterministic explain job stores a RevisionNote and raw log",
            actual=f"created explanation for Insight {insight.id}",
            job_id=job.id,
            component="ExplainJobService",
            metadata={
                "insight_id": insight.id,
                "revision_note_id": note.id,
                "evidence_item_ids": [item.id for item in evidence_items if item.id is not None],
            },
        )
        return job

    # :END_EXPLAIN_JOB


def create_explain_job(
    session: Session,
    insight: Insight,
    trigger: str = "manual",
    evidence_item_ids: list[int] | None = None,
) -> AgentJob:
    """Create one explain job with the default deterministic service."""
    return ExplainJobService().create_explain_job(
        session,
        insight,
        trigger=trigger,
        evidence_item_ids=evidence_item_ids,
    )


def ensure_explain_prompt_template(session: Session) -> PromptTemplate:
    existing = session.exec(
        select(PromptTemplate)
        .where(PromptTemplate.name == EXPLAIN_TEMPLATE_NAME)
        .where(PromptTemplate.version == EXPLAIN_TEMPLATE_VERSION)
    ).first()
    if existing is not None:
        return existing

    template = PromptTemplate(
        name=EXPLAIN_TEMPLATE_NAME,
        type="explain",
        version=EXPLAIN_TEMPLATE_VERSION,
        expected_artifact_kind="revision-note",
        body=(
            "Explain why Insight #{insight_id} says: {short_title}. "
            "Use the Insight body and EvidenceItems. Keep the explanation compact."
        ),
        notes="v0.7a deterministic local explanation; no model invocation.",
    )
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


def load_evidence_for_insight(
    session: Session,
    insight: Insight,
    evidence_item_ids: list[int] | None = None,
) -> list[EvidenceItem]:
    if insight.id is None:
        return []
    evidence_by_id: dict[int, EvidenceItem] = {
        item.id: item
        for item in session.exec(select(EvidenceItem).where(EvidenceItem.insight_id == insight.id)).all()
        if item.id is not None
    }
    for evidence_id in evidence_item_ids or []:
        evidence = session.get(EvidenceItem, evidence_id)
        if evidence is None or evidence.id is None:
            continue
        if evidence_is_contextual_for_insight(evidence, insight):
            evidence_by_id[evidence.id] = evidence
    evidence_items = list(evidence_by_id.values())
    evidence_items.sort(key=lambda item: item.id or 0)
    return evidence_items


def evidence_is_contextual_for_insight(evidence: EvidenceItem, insight: Insight) -> bool:
    if evidence.insight_id == insight.id:
        return True
    if insight.topic_id is not None and evidence.topic_id == insight.topic_id:
        return True
    if insight.harness_id is not None and evidence.harness_id == insight.harness_id:
        return True
    return False


def render_explain_prompt(
    template: PromptTemplate,
    insight: Insight,
    evidence_items: list[EvidenceItem],
) -> str:
    evidence_summary = "; ".join(item.claim_summary for item in evidence_items) or "no linked evidence"
    return (
        template.body.format(
            insight_id=insight.id,
            short_title=insight.short_title,
        )
        + f"\n\nInsight body: {insight.body}\nEvidence summary: {evidence_summary}"
    )


def deterministic_explanation(insight: Insight, evidence_items: list[EvidenceItem]) -> str:
    body = compact_text(insight.body)
    if not evidence_items:
        return (
            f"Explanation: The Insight claims \"{insight.short_title}\" because its body says "
            f"{body}. No linked EvidenceItems are present yet, so treat this as an agent explanation "
            "that still needs proof review."
        )

    evidence_text = "; ".join(evidence_phrase(item) for item in evidence_items[:3])
    extra_count = len(evidence_items) - 3
    suffix = f" It also has {extra_count} additional linked EvidenceItem(s)." if extra_count > 0 else ""
    return (
        f"Explanation: The Insight claims \"{insight.short_title}\" because its body says {body}. "
        f"The linked proof points to {evidence_text}.{suffix}"
    )


def evidence_phrase(evidence: EvidenceItem) -> str:
    location = evidence.file_path or evidence.source_location or "an imported source"
    if evidence.line_number is not None and evidence.file_path:
        location = f"{location}:{evidence.line_number}"
    return f"{compact_text(evidence.claim_summary)} ({location})"


def compact_text(value: str, limit: int = 180) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def write_explain_log(
    log_dir: Path,
    job: AgentJob,
    insight: Insight,
    evidence_items: list[EvidenceItem],
    explanation: str,
) -> str:
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"agent-job-{job.id or 0:05d}.log"
    evidence_ids = ", ".join(str(item.id) for item in evidence_items if item.id is not None)
    path.write_text(
        "\n".join(
            [
                "# Explain job",
                f"insight_id: {insight.id}",
                f"evidence_item_ids: {evidence_ids or 'none'}",
                "runner: deterministic",
                "",
                explanation,
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path.as_posix()
