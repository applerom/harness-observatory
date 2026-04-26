"""Add per-harness refresh schedules.

Revision ID: 20260426_0002
Revises: 20260426_0001
Create Date: 2026-04-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260426_0002"
down_revision: str | None = "20260426_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "refreshschedule",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("harness_id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("runner_name", sa.String(), nullable=False),
        sa.Column("interval_minutes", sa.Integer(), nullable=False),
        sa.Column("next_run_at", sa.DateTime(), nullable=True),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("last_job_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["harness_id"], ["harness.id"]),
        sa.ForeignKeyConstraint(["last_job_id"], ["agentjob.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("harness_id"),
    )
    op.create_index(op.f("ix_refreshschedule_enabled"), "refreshschedule", ["enabled"], unique=False)
    op.create_index(op.f("ix_refreshschedule_harness_id"), "refreshschedule", ["harness_id"], unique=False)
    op.create_index(op.f("ix_refreshschedule_next_run_at"), "refreshschedule", ["next_run_at"], unique=False)
    op.create_index(op.f("ix_refreshschedule_runner_name"), "refreshschedule", ["runner_name"], unique=False)
    op.create_index(op.f("ix_refreshschedule_status"), "refreshschedule", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_refreshschedule_status"), table_name="refreshschedule")
    op.drop_index(op.f("ix_refreshschedule_runner_name"), table_name="refreshschedule")
    op.drop_index(op.f("ix_refreshschedule_next_run_at"), table_name="refreshschedule")
    op.drop_index(op.f("ix_refreshschedule_harness_id"), table_name="refreshschedule")
    op.drop_index(op.f("ix_refreshschedule_enabled"), table_name="refreshschedule")
    op.drop_table("refreshschedule")
