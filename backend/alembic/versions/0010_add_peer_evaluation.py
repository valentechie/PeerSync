"""add peer evaluation criteria

Una sala puede tener más de dos personas: cada una valora a cada una de las demás.

Revision ID: 0010
Revises: 0009
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0010"
down_revision: Union[str, Sequence[str], None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CRITERIA = ("clarity", "listening", "preparation")


def upgrade() -> None:
    op.drop_constraint("uq_session_reviews_one_per_reviewer", "session_reviews", type_="unique")
    op.create_unique_constraint(
        "uq_session_reviews_one_per_pair", "session_reviews", ["session_id", "reviewer_id", "reviewee_id"]
    )
    for criterion in CRITERIA:
        op.add_column("session_reviews", sa.Column(criterion, sa.Integer(), nullable=False))
        op.create_check_constraint(
            op.f(f"ck_session_reviews_{criterion}_range"), "session_reviews", f"{criterion} BETWEEN 1 AND 5"
        )


def downgrade() -> None:
    for criterion in CRITERIA:
        op.drop_constraint(op.f(f"ck_session_reviews_{criterion}_range"), "session_reviews", type_="check")
        op.drop_column("session_reviews", criterion)
    op.drop_constraint("uq_session_reviews_one_per_pair", "session_reviews", type_="unique")
    op.execute(
        "DELETE FROM session_reviews a USING session_reviews b "
        "WHERE a.session_id = b.session_id AND a.reviewer_id = b.reviewer_id AND a.id > b.id"
    )
    op.create_unique_constraint(
        "uq_session_reviews_one_per_reviewer", "session_reviews", ["session_id", "reviewer_id"]
    )
