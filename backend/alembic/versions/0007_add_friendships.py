"""add friendships

Cada pareja tiene una sola fila, con sus dos usuarios en orden fijo.

Revision ID: 0007
Revises: 0006
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: Union[str, Sequence[str], None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "friendships",
        sa.Column("user_a_id", sa.Uuid(), nullable=False),
        sa.Column("user_b_id", sa.Uuid(), nullable=False),
        sa.Column("requester_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'accepted')", name=op.f("ck_friendships_friendship_status")),
        sa.CheckConstraint("user_a_id <> user_b_id", name=op.f("ck_friendships_not_self")),
        sa.ForeignKeyConstraint(["user_a_id"], ["users.id"], name=op.f("fk_friendships_user_a_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_b_id"], ["users.id"], name=op.f("fk_friendships_user_b_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], name=op.f("fk_friendships_requester_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_a_id", "user_b_id", name=op.f("pk_friendships")),
    )
    op.create_index(op.f("ix_friendships_user_b_id"), "friendships", ["user_b_id"])
    op.execute("ALTER TABLE friendships ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_table("friendships")
