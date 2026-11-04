"""add open study rooms

Una sala es una `study_sessions` sin match: cualquiera puede crearla o unirse.

Revision ID: 0006
Revises: 0005
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, Sequence[str], None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("study_sessions", "match_id", existing_type=sa.Uuid(), nullable=True)
    op.add_column("study_sessions", sa.Column("title", sa.String(length=120), server_default="", nullable=False))
    op.alter_column("study_sessions", "title", server_default=None)
    op.add_column("study_sessions", sa.Column("created_by_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        op.f("fk_study_sessions_created_by_id_users"),
        "study_sessions",
        "users",
        ["created_by_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_table(
        "session_participants",
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["study_sessions.id"],
            name=op.f("fk_session_participants_session_id_study_sessions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_session_participants_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("session_id", "user_id", name=op.f("pk_session_participants")),
    )
    op.create_index(op.f("ix_session_participants_user_id"), "session_participants", ["user_id"])
    op.execute("ALTER TABLE session_participants ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_table("session_participants")
    op.drop_constraint(op.f("fk_study_sessions_created_by_id_users"), "study_sessions", type_="foreignkey")
    op.drop_column("study_sessions", "created_by_id")
    op.drop_column("study_sessions", "title")
    op.execute("DELETE FROM study_sessions WHERE match_id IS NULL")
    op.alter_column("study_sessions", "match_id", existing_type=sa.Uuid(), nullable=False)
