"""add study to profiles

Revision ID: 0008
Revises: 0007
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008"
down_revision: Union[str, Sequence[str], None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("study_code", sa.String(length=60), nullable=True))
    op.create_index(op.f("ix_profiles_study_code"), "profiles", ["study_code"])


def downgrade() -> None:
    op.drop_index(op.f("ix_profiles_study_code"), table_name="profiles")
    op.drop_column("profiles", "study_code")
