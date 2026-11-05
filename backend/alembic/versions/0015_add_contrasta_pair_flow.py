"""add contrasta pair flow

Solo añade tablas y columnas opcionales: las salas y rondas existentes siguen igual.

Revision ID: 0015
Revises: 0014
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0015"
down_revision: Union[str, Sequence[str], None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_TABLES = (
    "contrasta_comparisons",
    "contrasta_cards",
    "teachback_activities",
    "contrasta_checks",
    "contrasta_check_answers",
)
ROUND_USER_COLUMNS = ("pair_a_id", "pair_b_id", "conclusion_by_id", "finish_requested_by_id")


def upgrade() -> None:
    for column in ROUND_USER_COLUMNS:
        op.add_column("contrasta_rounds", sa.Column(column, sa.Uuid(), nullable=True))
        op.create_foreign_key(
            op.f(f"fk_contrasta_rounds_{column}_users"), "contrasta_rounds", "users", [column], ["id"], ondelete="SET NULL"
        )
    op.add_column("contrasta_rounds", sa.Column("conclusion", sa.Text(), nullable=True))
    op.add_column("contrasta_rounds", sa.Column("conclusion_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contrasta_rounds", sa.Column("conclusion_confirmed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contrasta_rounds", sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "contrasta_comparisons",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("round_id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_id", sa.Uuid(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("pending", "ready", "failed", name="contrasta_comparison_status", native_enum=False, create_constraint=True, length=20),
            nullable=False,
        ),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["round_id"], ["contrasta_rounds.id"], name=op.f("fk_contrasta_comparisons_round_id_contrasta_rounds"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_id"], ["users.id"], name=op.f("fk_contrasta_comparisons_requested_by_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contrasta_comparisons")),
        sa.UniqueConstraint("round_id", name=op.f("uq_contrasta_comparisons_round_id")),
    )
    op.create_table(
        "contrasta_cards",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("round_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("request", sa.Text(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("private", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["round_id"], ["contrasta_rounds.id"], name=op.f("fk_contrasta_cards_round_id_contrasta_rounds"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], name=op.f("fk_contrasta_cards_author_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contrasta_cards")),
    )
    op.create_index(op.f("ix_contrasta_cards_round_id"), "contrasta_cards", ["round_id"], unique=False)
    op.create_table(
        "teachback_activities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("round_id", sa.Uuid(), nullable=False),
        sa.Column("proposer_id", sa.Uuid(), nullable=False),
        sa.Column("partner_id", sa.Uuid(), nullable=False),
        sa.Column("concept", sa.String(length=200), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "declined", "cancelled", "active", "completed", "stopped", name="teachback_activity_status", native_enum=False, create_constraint=True, length=20),
            nullable=False,
        ),
        sa.Column("turn", sa.Integer(), nullable=False),
        sa.Column("skip_requested_by_id", sa.Uuid(), nullable=True),
        sa.Column("feedback", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["round_id"], ["contrasta_rounds.id"], name=op.f("fk_teachback_activities_round_id_contrasta_rounds"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["proposer_id"], ["users.id"], name=op.f("fk_teachback_activities_proposer_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["partner_id"], ["users.id"], name=op.f("fk_teachback_activities_partner_id_users"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skip_requested_by_id"], ["users.id"], name=op.f("fk_teachback_activities_skip_requested_by_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_teachback_activities")),
    )
    op.create_index(op.f("ix_teachback_activities_round_id"), "teachback_activities", ["round_id"], unique=False)
    op.create_table(
        "contrasta_checks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("round_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["round_id"], ["contrasta_rounds.id"], name=op.f("fk_contrasta_checks_round_id_contrasta_rounds"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], name=op.f("fk_contrasta_checks_author_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contrasta_checks")),
        sa.UniqueConstraint("round_id", name=op.f("uq_contrasta_checks_round_id")),
    )
    op.create_table(
        "contrasta_check_answers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("check_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("reflection", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["check_id"], ["contrasta_checks.id"], name=op.f("fk_contrasta_check_answers_check_id_contrasta_checks"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_contrasta_check_answers_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_contrasta_check_answers")),
        sa.UniqueConstraint("check_id", "user_id", name="uq_contrasta_check_answers_one_per_user"),
    )

    op.add_column("teachback_submissions", sa.Column("activity_id", sa.Uuid(), nullable=True))
    op.add_column("teachback_submissions", sa.Column("turn", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk_teachback_submissions_activity_id_teachback_activities"),
        "teachback_submissions",
        "teachback_activities",
        ["activity_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(op.f("ix_teachback_submissions_activity_id"), "teachback_submissions", ["activity_id"], unique=False)
    op.create_unique_constraint("uq_teachback_submissions_activity_turn", "teachback_submissions", ["activity_id", "turn"])

    for table in NEW_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_constraint("uq_teachback_submissions_activity_turn", "teachback_submissions", type_="unique")
    op.drop_index(op.f("ix_teachback_submissions_activity_id"), table_name="teachback_submissions")
    op.drop_constraint(op.f("fk_teachback_submissions_activity_id_teachback_activities"), "teachback_submissions", type_="foreignkey")
    op.drop_column("teachback_submissions", "turn")
    op.drop_column("teachback_submissions", "activity_id")
    for table in reversed(NEW_TABLES):
        op.drop_table(table)
    for column in ("finished_at", "conclusion_confirmed_at", "conclusion_at", "conclusion"):
        op.drop_column("contrasta_rounds", column)
    for column in ROUND_USER_COLUMNS:
        op.drop_constraint(op.f(f"fk_contrasta_rounds_{column}_users"), "contrasta_rounds", type_="foreignkey")
        op.drop_column("contrasta_rounds", column)
