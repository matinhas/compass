"""add attention_required and attention_reason to captures

Revision ID: 004
Revises: 003
Create Date: 2026-06-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("captures", sa.Column("attention_required", sa.Boolean(), nullable=True))
    op.add_column("captures", sa.Column("attention_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("captures", "attention_reason")
    op.drop_column("captures", "attention_required")
