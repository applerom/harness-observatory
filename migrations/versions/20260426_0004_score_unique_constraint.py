"""Add unique score tuple constraint.

Revision ID: 20260426_0004
Revises: 20260426_0003
Create Date: 2026-04-26
"""

from collections.abc import Sequence

from alembic import op

revision: str = "20260426_0004"
down_revision: str | None = "20260426_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM score
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM score
            GROUP BY lens_id, harness_id, topic_id
        )
        """
    )
    with op.batch_alter_table("score") as batch_op:
        batch_op.create_unique_constraint(
            "uq_score_lens_harness_topic",
            ["lens_id", "harness_id", "topic_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("score") as batch_op:
        batch_op.drop_constraint("uq_score_lens_harness_topic", type_="unique")
