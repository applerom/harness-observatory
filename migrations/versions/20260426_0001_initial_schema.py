"""Initial v0.1 schema.

Revision ID: 20260426_0001
Revises:
Create Date: 2026-04-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260426_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "harness",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("upstream_url", sa.String(), nullable=True),
        sa.Column("local_upstream_path", sa.String(), nullable=True),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("source_model", sa.String(), nullable=True),
        sa.Column("status_note", sa.String(), nullable=True),
        sa.Column("last_review_date", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_harness_name"), "harness", ["name"], unique=False)
    op.create_index(op.f("ix_harness_slug"), "harness", ["slug"], unique=False)

    op.create_table(
        "ecosystemobject",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("upstream_url", sa.String(), nullable=True),
        sa.Column("local_upstream_path", sa.String(), nullable=True),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("status_note", sa.String(), nullable=True),
        sa.Column("last_review_date", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_ecosystemobject_kind"), "ecosystemobject", ["kind"], unique=False)
    op.create_index(op.f("ix_ecosystemobject_name"), "ecosystemobject", ["name"], unique=False)
    op.create_index(op.f("ix_ecosystemobject_slug"), "ecosystemobject", ["slug"], unique=False)

    op.create_table(
        "topic",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("definition", sa.String(), nullable=True),
        sa.Column("why_it_matters", sa.String(), nullable=True),
        sa.Column("body_markdown", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_topic_name"), "topic", ["name"], unique=False)
    op.create_index(op.f("ix_topic_slug"), "topic", ["slug"], unique=False)

    op.create_table(
        "feature",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("status_note", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_feature_name"), "feature", ["name"], unique=False)
    op.create_index(op.f("ix_feature_slug"), "feature", ["slug"], unique=False)

    op.create_table(
        "source",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("local_path", sa.String(), nullable=True),
        sa.Column("commit_sha", sa.String(), nullable=True),
        sa.Column("version", sa.String(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "lens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lens_name"), "lens", ["name"], unique=False)
    op.create_index(op.f("ix_lens_slug"), "lens", ["slug"], unique=False)

    op.create_table(
        "prompttemplate",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("expected_artifact_kind", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_prompttemplate_name"), "prompttemplate", ["name"], unique=False)
    op.create_index(op.f("ix_prompttemplate_type"), "prompttemplate", ["type"], unique=False)

    op.create_table(
        "observationreview",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=False),
        sa.Column("reviewer", sa.String(), nullable=True),
        sa.Column("source_snapshot", sa.String(), nullable=True),
        sa.Column("change_summary", sa.String(), nullable=True),
        sa.Column("affected_artifacts", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "mediaattachment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("path_or_url", sa.String(), nullable=False),
        sa.Column("caption", sa.String(), nullable=True),
        sa.Column("attached_to_kind", sa.String(), nullable=False),
        sa.Column("attached_to_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_mediaattachment_attached_to_id"), "mediaattachment", ["attached_to_id"], unique=False)
    op.create_index(op.f("ix_mediaattachment_attached_to_kind"), "mediaattachment", ["attached_to_kind"], unique=False)

    op.create_table(
        "insight",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("short_title", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("why_it_matters", sa.String(), nullable=True),
        sa.Column("teaching_value", sa.String(), nullable=True),
        sa.Column("lecturer_note", sa.String(), nullable=True),
        sa.Column("format", sa.String(), nullable=False),
        sa.Column("audience", sa.String(), nullable=True),
        sa.Column("engagement_hook", sa.String(), nullable=True),
        sa.Column("joke_or_telegram_seed", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("confidence_band", sa.String(), nullable=False),
        sa.Column("agent_authored_at", sa.DateTime(), nullable=False),
        sa.Column("agent_model", sa.String(), nullable=True),
        sa.Column("agent_runner", sa.String(), nullable=True),
        sa.Column("first_observed_by", sa.String(), nullable=True),
        sa.Column("body_markdown", sa.String(), nullable=True),
        sa.Column("harness_id", sa.Integer(), nullable=True),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("feature_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["feature_id"], ["feature.id"]),
        sa.ForeignKeyConstraint(["harness_id"], ["harness.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["topic.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_insight_audience"), "insight", ["audience"], unique=False)
    op.create_index(op.f("ix_insight_confidence_band"), "insight", ["confidence_band"], unique=False)
    op.create_index(op.f("ix_insight_feature_id"), "insight", ["feature_id"], unique=False)
    op.create_index(op.f("ix_insight_format"), "insight", ["format"], unique=False)
    op.create_index(op.f("ix_insight_harness_id"), "insight", ["harness_id"], unique=False)
    op.create_index(op.f("ix_insight_short_title"), "insight", ["short_title"], unique=False)
    op.create_index(op.f("ix_insight_status"), "insight", ["status"], unique=False)
    op.create_index(op.f("ix_insight_topic_id"), "insight", ["topic_id"], unique=False)

    op.create_table(
        "evidenceitem",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("claim_summary", sa.String(), nullable=False),
        sa.Column("evidence_class", sa.String(), nullable=True),
        sa.Column("source_type", sa.String(), nullable=True),
        sa.Column("source_location", sa.String(), nullable=True),
        sa.Column("file_path", sa.String(), nullable=True),
        sa.Column("line_number", sa.Integer(), nullable=True),
        sa.Column("exact_citation", sa.String(), nullable=True),
        sa.Column("paraphrased_note", sa.String(), nullable=True),
        sa.Column("code_snippet", sa.String(), nullable=True),
        sa.Column("code_snippet_pulled_at", sa.DateTime(), nullable=True),
        sa.Column("verification_passes", sa.Integer(), nullable=False),
        sa.Column("verifier_agents", sa.JSON(), nullable=True),
        sa.Column("confidence", sa.String(), nullable=True),
        sa.Column("observed_from", sa.DateTime(), nullable=True),
        sa.Column("observed_to", sa.DateTime(), nullable=True),
        sa.Column("reviewer", sa.String(), nullable=True),
        sa.Column("harness_id", sa.Integer(), nullable=True),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("insight_id", sa.Integer(), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["harness_id"], ["harness.id"]),
        sa.ForeignKeyConstraint(["insight_id"], ["insight.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["source.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["topic.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evidenceitem_evidence_class"), "evidenceitem", ["evidence_class"], unique=False)
    op.create_index(op.f("ix_evidenceitem_harness_id"), "evidenceitem", ["harness_id"], unique=False)
    op.create_index(op.f("ix_evidenceitem_insight_id"), "evidenceitem", ["insight_id"], unique=False)
    op.create_index(op.f("ix_evidenceitem_source_id"), "evidenceitem", ["source_id"], unique=False)
    op.create_index(op.f("ix_evidenceitem_topic_id"), "evidenceitem", ["topic_id"], unique=False)

    op.create_table(
        "comparisoncell",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("harness_id", sa.Integer(), nullable=False),
        sa.Column("topic_id", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("cell_summary", sa.String(), nullable=True),
        sa.Column("confidence_band", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["harness_id"], ["harness.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["topic.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("harness_id", "topic_id"),
    )
    op.create_index(op.f("ix_comparisoncell_confidence_band"), "comparisoncell", ["confidence_band"], unique=False)
    op.create_index(op.f("ix_comparisoncell_harness_id"), "comparisoncell", ["harness_id"], unique=False)
    op.create_index(op.f("ix_comparisoncell_state"), "comparisoncell", ["state"], unique=False)
    op.create_index(op.f("ix_comparisoncell_topic_id"), "comparisoncell", ["topic_id"], unique=False)

    op.create_table(
        "revisionnote",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("insight_id", sa.Integer(), nullable=True),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["insight_id"], ["insight.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_revisionnote_insight_id"), "revisionnote", ["insight_id"], unique=False)

    op.create_table(
        "score",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("lens_id", sa.Integer(), nullable=True),
        sa.Column("harness_id", sa.Integer(), nullable=True),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("rationale", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["harness_id"], ["harness.id"]),
        sa.ForeignKeyConstraint(["lens_id"], ["lens.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["topic.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_score_harness_id"), "score", ["harness_id"], unique=False)
    op.create_index(op.f("ix_score_lens_id"), "score", ["lens_id"], unique=False)
    op.create_index(op.f("ix_score_topic_id"), "score", ["topic_id"], unique=False)

    op.create_table(
        "agentjob",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("target_kind", sa.String(), nullable=True),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("prompt_template_id", sa.Integer(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("runner_name", sa.String(), nullable=True),
        sa.Column("runner_version", sa.String(), nullable=True),
        sa.Column("trigger", sa.String(), nullable=True),
        sa.Column("parent_job_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("stdout_log_path", sa.String(), nullable=True),
        sa.Column("produced_artifact_ids", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("cost_estimate", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["parent_job_id"], ["agentjob.id"]),
        sa.ForeignKeyConstraint(["prompt_template_id"], ["prompttemplate.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agentjob_status"), "agentjob", ["status"], unique=False)
    op.create_index(op.f("ix_agentjob_type"), "agentjob", ["type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_agentjob_type"), table_name="agentjob")
    op.drop_index(op.f("ix_agentjob_status"), table_name="agentjob")
    op.drop_table("agentjob")
    op.drop_index(op.f("ix_score_topic_id"), table_name="score")
    op.drop_index(op.f("ix_score_lens_id"), table_name="score")
    op.drop_index(op.f("ix_score_harness_id"), table_name="score")
    op.drop_table("score")
    op.drop_index(op.f("ix_revisionnote_insight_id"), table_name="revisionnote")
    op.drop_table("revisionnote")
    op.drop_index(op.f("ix_comparisoncell_topic_id"), table_name="comparisoncell")
    op.drop_index(op.f("ix_comparisoncell_state"), table_name="comparisoncell")
    op.drop_index(op.f("ix_comparisoncell_harness_id"), table_name="comparisoncell")
    op.drop_index(op.f("ix_comparisoncell_confidence_band"), table_name="comparisoncell")
    op.drop_table("comparisoncell")
    op.drop_index(op.f("ix_evidenceitem_topic_id"), table_name="evidenceitem")
    op.drop_index(op.f("ix_evidenceitem_source_id"), table_name="evidenceitem")
    op.drop_index(op.f("ix_evidenceitem_insight_id"), table_name="evidenceitem")
    op.drop_index(op.f("ix_evidenceitem_harness_id"), table_name="evidenceitem")
    op.drop_index(op.f("ix_evidenceitem_evidence_class"), table_name="evidenceitem")
    op.drop_table("evidenceitem")
    op.drop_index(op.f("ix_insight_topic_id"), table_name="insight")
    op.drop_index(op.f("ix_insight_status"), table_name="insight")
    op.drop_index(op.f("ix_insight_short_title"), table_name="insight")
    op.drop_index(op.f("ix_insight_harness_id"), table_name="insight")
    op.drop_index(op.f("ix_insight_format"), table_name="insight")
    op.drop_index(op.f("ix_insight_feature_id"), table_name="insight")
    op.drop_index(op.f("ix_insight_confidence_band"), table_name="insight")
    op.drop_index(op.f("ix_insight_audience"), table_name="insight")
    op.drop_table("insight")
    op.drop_index(op.f("ix_mediaattachment_attached_to_kind"), table_name="mediaattachment")
    op.drop_index(op.f("ix_mediaattachment_attached_to_id"), table_name="mediaattachment")
    op.drop_table("mediaattachment")
    op.drop_table("observationreview")
    op.drop_index(op.f("ix_prompttemplate_type"), table_name="prompttemplate")
    op.drop_index(op.f("ix_prompttemplate_name"), table_name="prompttemplate")
    op.drop_table("prompttemplate")
    op.drop_index(op.f("ix_lens_slug"), table_name="lens")
    op.drop_index(op.f("ix_lens_name"), table_name="lens")
    op.drop_table("lens")
    op.drop_table("source")
    op.drop_index(op.f("ix_feature_slug"), table_name="feature")
    op.drop_index(op.f("ix_feature_name"), table_name="feature")
    op.drop_table("feature")
    op.drop_index(op.f("ix_topic_slug"), table_name="topic")
    op.drop_index(op.f("ix_topic_name"), table_name="topic")
    op.drop_table("topic")
    op.drop_index(op.f("ix_ecosystemobject_slug"), table_name="ecosystemobject")
    op.drop_index(op.f("ix_ecosystemobject_name"), table_name="ecosystemobject")
    op.drop_index(op.f("ix_ecosystemobject_kind"), table_name="ecosystemobject")
    op.drop_table("ecosystemobject")
    op.drop_index(op.f("ix_harness_slug"), table_name="harness")
    op.drop_index(op.f("ix_harness_name"), table_name="harness")
    op.drop_table("harness")

