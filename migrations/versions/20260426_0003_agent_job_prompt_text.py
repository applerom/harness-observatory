"""Add exact runtime prompt text to AgentJob.

Revision ID: 20260426_0003
Revises: 20260426_0002
Create Date: 2026-04-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260426_0003"
down_revision: str | None = "20260426_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("agentjob", sa.Column("prompt_text", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("agentjob", "prompt_text")
