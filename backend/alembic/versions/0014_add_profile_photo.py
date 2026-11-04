"""add profile photo

Revision ID: 0014
Revises: 0013
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0014"
down_revision: Union[str, Sequence[str], None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("photo_data", sa.LargeBinary(), nullable=True))
    op.add_column("profiles", sa.Column("photo_type", sa.String(length=20), nullable=True))
    op.add_column("profiles", sa.Column("photo_version", sa.Integer(), server_default="0", nullable=False))


def downgrade() -> None:
    op.drop_column("profiles", "photo_version")
    op.drop_column("profiles", "photo_type")
    op.drop_column("profiles", "photo_data")
