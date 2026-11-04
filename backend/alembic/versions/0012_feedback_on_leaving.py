"""feedback on leaving a room

La sala se cierra cuando se va la última persona, y al salir se evalúa a los demás
con barras de 0 a 10. Sustituye a la votación y al feedback de sala de la 0011.
Las filas de participantes se conservan al salir: de ellas salen las evaluaciones pendientes.

Revision ID: 0012
Revises: 0011
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0012"
down_revision: Union[str, Sequence[str], None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_CRITERIA = ("clarity", "listening", "preparation")
NEW_CRITERIA = ("punctuality", "treatment", "participation", "clarity")


def upgrade() -> None:
    op.drop_table("room_feedback")
    op.drop_column("session_participants", "wants_to_close")
    op.add_column("session_participants", sa.Column("left_at", sa.DateTime(timezone=True), nullable=True))

    op.drop_constraint(op.f("ck_session_reviews_rating_range"), "session_reviews", type_="check")
    op.create_check_constraint(op.f("ck_session_reviews_rating_range"), "session_reviews", "rating BETWEEN 0 AND 5")
    for criterion in OLD_CRITERIA:
        op.drop_constraint(op.f(f"ck_session_reviews_{criterion}_range"), "session_reviews", type_="check")
        op.drop_column("session_reviews", criterion)
    for criterion in NEW_CRITERIA:
        op.add_column("session_reviews", sa.Column(criterion, sa.Integer(), nullable=False))
        op.create_check_constraint(
            op.f(f"ck_session_reviews_{criterion}_range"), "session_reviews", f"{criterion} BETWEEN 0 AND 10"
        )


def downgrade() -> None:
    op.execute("DELETE FROM session_reviews")
    for criterion in NEW_CRITERIA:
        op.drop_constraint(op.f(f"ck_session_reviews_{criterion}_range"), "session_reviews", type_="check")
        op.drop_column("session_reviews", criterion)
    for criterion in OLD_CRITERIA:
        op.add_column("session_reviews", sa.Column(criterion, sa.Integer(), nullable=False))
        op.create_check_constraint(
            op.f(f"ck_session_reviews_{criterion}_range"), "session_reviews", f"{criterion} BETWEEN 1 AND 5"
        )
    op.drop_constraint(op.f("ck_session_reviews_rating_range"), "session_reviews", type_="check")
    op.create_check_constraint(op.f("ck_session_reviews_rating_range"), "session_reviews", "rating BETWEEN 1 AND 5")

    op.execute("DELETE FROM session_participants WHERE left_at IS NOT NULL")
    op.drop_column("session_participants", "left_at")
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
