"""add classification columns

Revision ID: 002
Revises: 001
Create Date: 2026-06-14

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("captures", sa.Column("classification_type", sa.String(), nullable=True))
    op.add_column("captures", sa.Column("classification_domain", sa.String(), nullable=True))
    op.add_column("captures", sa.Column("classification_priority", sa.String(), nullable=True))
    op.add_column("captures", sa.Column("classification_confidence", sa.Integer(), nullable=True))
    op.add_column("captures", sa.Column("classification_reasoning", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("captures", "classification_reasoning")
    op.drop_column("captures", "classification_confidence")
    op.drop_column("captures", "classification_priority")
    op.drop_column("captures", "classification_domain")
    op.drop_column("captures", "classification_type")
