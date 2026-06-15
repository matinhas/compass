"""add source_type, source_instance, external_id to captures

Revision ID: 003
Revises: 002
Create Date: 2026-06-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("captures", sa.Column("source_type", sa.String(), nullable=True))
    op.add_column("captures", sa.Column("source_instance", sa.String(), nullable=True))
    op.add_column("captures", sa.Column("external_id", sa.String(), nullable=True))

    op.execute(
        "UPDATE captures SET source_type = 'manual', source_instance = 'compass' WHERE source_type IS NULL"
    )

    op.create_index("ix_captures_external_id", "captures", ["external_id"])


def downgrade() -> None:
    op.drop_index("ix_captures_external_id", table_name="captures")
    op.drop_column("captures", "external_id")
    op.drop_column("captures", "source_instance")
    op.drop_column("captures", "source_type")
