from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Index, Integer, Uuid, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, str_enum


class MatchStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class MatchRequest(Base):
    __tablename__ = "match_requests"
    __table_args__ = (
        CheckConstraint("requester_id <> receiver_id", name="not_self"),
        CheckConstraint("score BETWEEN 0 AND 100", name="score_range"),
        Index(
            "uq_match_requests_pending_pair",
            "requester_id",
            "receiver_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
            sqlite_where=text("status = 'pending'"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    requester_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    receiver_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[MatchStatus] = mapped_column(str_enum(MatchStatus, "match_status"), default=MatchStatus.PENDING)
    # Copia del cálculo determinista al solicitar: permite explicar por qué se sugirió.
    score: Mapped[int] = mapped_column(Integer)
    score_breakdown: Mapped[dict[str, Any]] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
