"""add close votes and room feedback

Revision ID: 0011
Revises: 0010
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0011"
down_revision: Union[str, Sequence[str], None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "session_participants",
        sa.Column("wants_to_close", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_table(
        "room_feedback",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name=op.f("ck_room_feedback_rating_range")),
        sa.ForeignKeyConstraint(
            ["session_id"], ["study_sessions.id"], name=op.f("fk_room_feedback_session_id_study_sessions"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_room_feedback_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_room_feedback")),
        sa.UniqueConstraint("session_id", "user_id", name="uq_room_feedback_one_per_user"),
    )
    op.execute("ALTER TABLE room_feedback ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_table("room_feedback")
    op.drop_column("session_participants", "wants_to_close")
