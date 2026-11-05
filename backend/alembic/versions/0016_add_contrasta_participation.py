"""add contrasta reactions and predictions

Solo añade tablas: las salas y rondas existentes siguen igual.

Revision ID: 0016
Revises: 0015
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0016"
down_revision: Union[str, Sequence[str], None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_TABLES = ("contrasta_reactions", "contrasta_predictions")


def upgrade() -> None:
    op.create_table(
        "contrasta_reactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("round_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["round_id"], ["contrasta_rounds.id"], name=op.f("fk_contrasta_reactions_round_id_contrasta_rounds"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_contrasta_reactions_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contrasta_reactions")),
        sa.UniqueConstraint("round_id", "user_id", name="uq_contrasta_reactions_one_per_user"),
    )
    op.create_table(
        "contrasta_predictions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("round_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["round_id"], ["contrasta_rounds.id"], name=op.f("fk_contrasta_predictions_round_id_contrasta_rounds"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_contrasta_predictions_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contrasta_predictions")),
        sa.UniqueConstraint("round_id", "user_id", name="uq_contrasta_predictions_one_per_user"),
    )
    for table in NEW_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    for table in reversed(NEW_TABLES):
        op.drop_table(table)
