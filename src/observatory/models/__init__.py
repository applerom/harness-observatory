# FILE: src/observatory/models/__init__.py
# VERSION: 2026-04-26
# START_MODULE_CONTRACT:
# PURPOSE: SQLModel entity definitions for the observatory database.
# PRD_REF: docs/PRD.md §7, §24 v1.0-minimal, §24 v1.1, §26.1
# WHY_REF: docs/why-graph.xml#MOD-MODELS
# SCOPE: core entity tables; runtime job/schedule tables; curation/explanation/scoring/export support tables
# INVARIANTS:
# - Insight is the agent-produced abstraction; EvidenceItem is the proof layer under it.
# - Schema stays intentionally nullable where importer or agent-output certainty is not guaranteed.
# - AgentJob is the audit trail for runtime and deterministic jobs; status labels must not overstate job findings.
# START_MODULE_MAP:
# - Harness: primary coding harness under study.
# - Topic: stable axis of comparison.
# - Feature: dynamic product capability.
# - EvidenceItem: proof citation or note backing an Insight.
# - Insight: primary agent-produced finding.
# - ComparisonCell: matrix state for a Harness and Topic.
# - Source: upstream source snapshot or document.
# - MediaAttachment: optional media linked to an Insight or EvidenceItem.
# - EcosystemObject: non-harness object in the agent tooling ecosystem.
# - AgentJob: audit trail for runtime and deterministic agent-job-shaped invocations.
# - RefreshSchedule: per-harness refresh cadence consumed by the scheduler slice.
# - PromptTemplate: versioned prompt template table.
# - RevisionNote: explanation/correction/historical note table.
# - ObservationReview: concrete review event table.
# - Lens: interpretation or scoring frame.
# - Score: lens-based score table.
# :END_MODULE_MAP
# :END_MODULE_CONTRACT

from datetime import UTC, datetime

from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.types import JSON
from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)


# START_MODELS_HARNESS:
class Harness(SQLModel, table=True):
    """Primary agentic coding harness under study."""

    __table_args__ = (UniqueConstraint("slug"),)

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    slug: str = Field(index=True)
    upstream_url: str | None = None
    local_upstream_path: str | None = None
    language: str | None = None
    source_model: str | None = None
    status_note: str | None = None
    last_review_date: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    evidence_items: list["EvidenceItem"] = Relationship(back_populates="harness")
    insights: list["Insight"] = Relationship(back_populates="harness")
    comparison_cells: list["ComparisonCell"] = Relationship(back_populates="harness")


class EcosystemObject(SQLModel, table=True):
    """Related non-harness ecosystem object such as an agent tool or protocol."""

    __table_args__ = (UniqueConstraint("slug"),)

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    slug: str = Field(index=True)
    kind: str = Field(index=True)
    upstream_url: str | None = None
    local_upstream_path: str | None = None
    language: str | None = None
    status_note: str | None = None
    last_review_date: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


# :END_MODELS_HARNESS


# START_MODELS_TOPIC:
class Topic(SQLModel, table=True):
    """Stable comparison axis used by dossiers and the matrix."""

    __table_args__ = (UniqueConstraint("slug"),)

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    slug: str = Field(index=True)
    definition: str | None = None
    why_it_matters: str | None = None
    body_markdown: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    evidence_items: list["EvidenceItem"] = Relationship(back_populates="topic")
    insights: list["Insight"] = Relationship(back_populates="topic")
    comparison_cells: list["ComparisonCell"] = Relationship(back_populates="topic")


class Feature(SQLModel, table=True):
    """Dynamic product capability that may appear or disappear across harnesses."""

    __table_args__ = (UniqueConstraint("slug"),)

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    slug: str = Field(index=True)
    description: str | None = None
    status_note: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


# :END_MODELS_TOPIC


# START_MODELS_INSIGHT:
class Insight(SQLModel, table=True):
    """Primary agent-produced abstraction shown above its proof."""

    id: int | None = Field(default=None, primary_key=True)
    short_title: str = Field(index=True)
    body: str
    why_it_matters: str | None = None
    teaching_value: str | None = None
    lecturer_note: str | None = None
    format: str = Field(default="text", index=True)
    audience: str | None = Field(default=None, index=True)
    engagement_hook: str | None = None
    joke_or_telegram_seed: str | None = None
    status: str = Field(default="proposed", index=True)
    confidence_band: str = Field(default="unverified", index=True)
    agent_authored_at: datetime = Field(default_factory=utc_now)
    agent_model: str | None = None
    agent_runner: str | None = None
    first_observed_by: str | None = None
    body_markdown: str | None = None
    harness_id: int | None = Field(default=None, foreign_key="harness.id", index=True)
    topic_id: int | None = Field(default=None, foreign_key="topic.id", index=True)
    feature_id: int | None = Field(default=None, foreign_key="feature.id", index=True)

    harness: Harness | None = Relationship(back_populates="insights")
    topic: Topic | None = Relationship(back_populates="insights")
    evidence_items: list["EvidenceItem"] = Relationship(back_populates="insight")


class RevisionNote(SQLModel, table=True):
    """Lightweight future table for historical annotations and corrections."""

    id: int | None = Field(default=None, primary_key=True)
    insight_id: int | None = Field(default=None, foreign_key="insight.id", index=True)
    note: str | None = None
    created_by: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


# :END_MODELS_INSIGHT


# START_MODELS_EVIDENCE:
class Source(SQLModel, table=True):
    """Upstream source document, repository, or snapshot cited by evidence."""

    id: int | None = Field(default=None, primary_key=True)
    name: str
    source_type: str | None = None
    url: str | None = None
    local_path: str | None = None
    commit_sha: str | None = None
    version: str | None = None
    retrieved_at: datetime | None = None

    evidence_items: list["EvidenceItem"] = Relationship(back_populates="source")


class EvidenceItem(SQLModel, table=True):
    """Atomic proof item beneath an Insight."""

    id: int | None = Field(default=None, primary_key=True)
    claim_summary: str
    evidence_class: str | None = Field(default=None, index=True)
    source_type: str | None = None
    source_location: str | None = None
    file_path: str | None = None
    line_number: int | None = None
    exact_citation: str | None = None
    paraphrased_note: str | None = None
    code_snippet: str | None = None
    code_snippet_pulled_at: datetime | None = None
    verification_passes: int = 0
    verifier_agents: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    confidence: str | None = None
    observed_from: datetime | None = None
    observed_to: datetime | None = None
    reviewer: str | None = None
    harness_id: int | None = Field(default=None, foreign_key="harness.id", index=True)
    topic_id: int | None = Field(default=None, foreign_key="topic.id", index=True)
    insight_id: int | None = Field(default=None, foreign_key="insight.id", index=True)
    source_id: int | None = Field(default=None, foreign_key="source.id", index=True)
    created_at: datetime = Field(default_factory=utc_now)

    harness: Harness | None = Relationship(back_populates="evidence_items")
    topic: Topic | None = Relationship(back_populates="evidence_items")
    insight: Insight | None = Relationship(back_populates="evidence_items")
    source: Source | None = Relationship(back_populates="evidence_items")


class MediaAttachment(SQLModel, table=True):
    """Optional media attached to an Insight or EvidenceItem."""

    id: int | None = Field(default=None, primary_key=True)
    kind: str
    path_or_url: str
    caption: str | None = None
    attached_to_kind: str = Field(index=True)
    attached_to_id: int = Field(index=True)
    created_at: datetime = Field(default_factory=utc_now)


# :END_MODELS_EVIDENCE


class ComparisonCell(SQLModel, table=True):
    """Matrix outcome for a harness/topic pair."""

    __table_args__ = (UniqueConstraint("harness_id", "topic_id"),)

    id: int | None = Field(default=None, primary_key=True)
    harness_id: int = Field(foreign_key="harness.id", index=True)
    topic_id: int = Field(foreign_key="topic.id", index=True)
    state: str = Field(default="unknown", index=True)
    cell_summary: str | None = None
    confidence_band: str = Field(default="unverified", index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    harness: Harness | None = Relationship(back_populates="comparison_cells")
    topic: Topic | None = Relationship(back_populates="comparison_cells")


class ObservationReview(SQLModel, table=True):
    """Concrete review event for source snapshots and changed findings."""

    id: int | None = Field(default=None, primary_key=True)
    reviewed_at: datetime = Field(default_factory=utc_now)
    reviewer: str | None = None
    source_snapshot: str | None = None
    change_summary: str | None = None
    affected_artifacts: list[dict[str, object]] = Field(default_factory=list, sa_column=Column(JSON))


class Lens(SQLModel, table=True):
    """Scoring or interpretation frame."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    slug: str = Field(index=True)
    description: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class Score(SQLModel, table=True):
    """Future lens-based score; no universal single winner score is implied."""

    __table_args__ = (UniqueConstraint("lens_id", "harness_id", "topic_id"),)

    id: int | None = Field(default=None, primary_key=True)
    lens_id: int | None = Field(default=None, foreign_key="lens.id", index=True)
    harness_id: int | None = Field(default=None, foreign_key="harness.id", index=True)
    topic_id: int | None = Field(default=None, foreign_key="topic.id", index=True)
    value: float | None = None
    rationale: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


# START_MODELS_AGENT_JOB:
class PromptTemplate(SQLModel, table=True):
    """Versioned prompt template for AgentJob types."""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    type: str = Field(index=True)
    version: str
    body: str
    expected_artifact_kind: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    notes: str | None = None


class AgentJob(SQLModel, table=True):
    """Audit trail row for runtime and deterministic agent-job-shaped invocations."""

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    type: str = Field(index=True)
    target_kind: str | None = None
    target_id: int | None = None
    prompt_template_id: int | None = Field(default=None, foreign_key="prompttemplate.id")
    prompt_text: str | None = None
    model: str | None = None
    runner_name: str | None = None
    runner_version: str | None = None
    trigger: str | None = None
    parent_job_id: int | None = Field(default=None, foreign_key="agentjob.id")
    status: str = Field(default="queued", index=True)
    stdout_log_path: str | None = None
    produced_artifact_ids: list[int] = Field(default_factory=list, sa_column=Column(JSON))
    error_message: str | None = None
    cost_estimate: float | None = None


class RefreshSchedule(SQLModel, table=True):
    """Per-harness refresh cadence for the first APScheduler slice."""

    __table_args__ = (UniqueConstraint("harness_id"),)

    id: int | None = Field(default=None, primary_key=True)
    harness_id: int = Field(foreign_key="harness.id", index=True)
    enabled: bool = Field(default=False, index=True)
    runner_name: str = Field(default="codex", index=True)
    interval_minutes: int = Field(default=1440)
    next_run_at: datetime | None = Field(default=None, index=True)
    last_run_at: datetime | None = None
    last_job_id: int | None = Field(default=None, foreign_key="agentjob.id")
    status: str = Field(default="idle", index=True)
    note: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


# :END_MODELS_AGENT_JOB


__all__ = [
    "AgentJob",
    "ComparisonCell",
    "EcosystemObject",
    "EvidenceItem",
    "Feature",
    "Harness",
    "Insight",
    "Lens",
    "MediaAttachment",
    "ObservationReview",
    "PromptTemplate",
    "RefreshSchedule",
    "RevisionNote",
    "Score",
    "Source",
    "Topic",
]
