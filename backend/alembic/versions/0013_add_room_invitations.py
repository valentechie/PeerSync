"""add room invitations

Revision ID: 0013
Revises: 0012
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0013"
down_revision: Union[str, Sequence[str], None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "room_invitations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("inviter_id", sa.Uuid(), nullable=False),
        sa.Column("invitee_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'declined')", name=op.f("ck_room_invitations_invitation_status")),
        sa.CheckConstraint("inviter_id <> invitee_id", name=op.f("ck_room_invitations_not_self")),
        sa.ForeignKeyConstraint(
            ["session_id"], ["study_sessions.id"], name=op.f("fk_room_invitations_session_id_study_sessions"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["inviter_id"], ["users.id"], name=op.f("fk_room_invitations_inviter_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["invitee_id"], ["users.id"], name=op.f("fk_room_invitations_invitee_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_room_invitations")),
        sa.UniqueConstraint("session_id", "invitee_id", name="uq_room_invitations_one_per_person"),
    )
    op.create_index(op.f("ix_room_invitations_invitee_id"), "room_invitations", ["invitee_id"])
    op.execute("ALTER TABLE room_invitations ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_table("room_invitations")
