from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, str_enum


class SessionStatus(str, Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ContrastaStatus(str, Enum):
    INDIVIDUAL = "individual"
    REVEALED = "revealed"


class StudySession(Base):
    """Sala de estudio. Sin `match_id` es una sala abierta, con sus `SessionParticipant`;
    con `match_id`, sus participantes son los dos usuarios del match."""

    __tablename__ = "study_sessions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    match_id: Mapped[UUID | None] = mapped_column(ForeignKey("match_requests.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(120), default="")
    created_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    objective: Mapped[str] = mapped_column(String(300), default="")
    status: Mapped[SessionStatus] = mapped_column(str_enum(SessionStatus, "session_status"), default=SessionStatus.SCHEDULED)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SessionParticipant(Base):
    __tablename__ = "session_participants"

    session_id: Mapped[UUID] = mapped_column(ForeignKey("study_sessions.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # La fila se conserva al salir: de ella salen las evaluaciones que esa persona debe.
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SessionReview(Base):
    """Valoración entre compañeros; la reputación es la media de `rating`."""

    __tablename__ = "session_reviews"
    __table_args__ = (
        UniqueConstraint("session_id", "reviewer_id", "reviewee_id", name="uq_session_reviews_one_per_pair"),
        CheckConstraint("rating BETWEEN 0 AND 5", name="rating_range"),
        CheckConstraint("punctuality BETWEEN 0 AND 10", name="punctuality_range"),
        CheckConstraint("treatment BETWEEN 0 AND 10", name="treatment_range"),
        CheckConstraint("participation BETWEEN 0 AND 10", name="participation_range"),
        CheckConstraint("clarity BETWEEN 0 AND 10", name="clarity_range"),
        CheckConstraint("reviewer_id <> reviewee_id", name="not_self"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("study_sessions.id", ondelete="CASCADE"))
    reviewer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    reviewee_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    punctuality: Mapped[int] = mapped_column(Integer)
    treatment: Mapped[int] = mapped_column(Integer)
    participation: Mapped[int] = mapped_column(Integer)
    clarity: Mapped[int] = mapped_column(Integer)
    # Sin uso: la evaluación ya no pide escribir.
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StudyMindHint(Base):
    """Cada fila nace de una petición explícita; no se guardan señales de comportamiento."""

    __tablename__ = "studymind_hints"
    __table_args__ = (CheckConstraint("level BETWEEN 1 AND 3", name="level_range"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("study_sessions.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    question: Mapped[str] = mapped_column(Text)
    level: Mapped[int] = mapped_column(Integer)
    hint: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TeachBackSubmission(Base):
    __tablename__ = "teachback_submissions"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("study_sessions.id", ondelete="CASCADE"), index=True)
    explainer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    concept: Mapped[str] = mapped_column(String(200))
    explanation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TeachBackPeerReview(Base):
    __tablename__ = "teachback_peer_reviews"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    submission_id: Mapped[UUID] = mapped_column(ForeignKey("teachback_submissions.id", ondelete="CASCADE"), unique=True)
    reviewer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    comment: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TeachBackAIFeedback(Base):
    """`peer_review_id` obligatorio: sin revisión de un compañero no puede existir
    feedback de IA. Sin columna de nota: es formativo, no una calificación."""

    __tablename__ = "teachback_ai_feedback"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    peer_review_id: Mapped[UUID] = mapped_column(ForeignKey("teachback_peer_reviews.id", ondelete="CASCADE"), unique=True)
    correctness: Mapped[str] = mapped_column(Text)
    clarity: Mapped[str] = mapped_column(Text)
    completeness: Mapped[str] = mapped_column(Text)
    examples: Mapped[str] = mapped_column(Text)
    uncertainty: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContrastaRound(Base):
    __tablename__ = "contrasta_rounds"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("study_sessions.id", ondelete="CASCADE"), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    status: Mapped[ContrastaStatus] = mapped_column(str_enum(ContrastaStatus, "contrasta_status"), default=ContrastaStatus.INDIVIDUAL)
    revealed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContrastaAnswer(Base):
    """Oculta al compañero hasta que la ronda pase a `revealed`. Lo aplica el servicio."""

    __tablename__ = "contrasta_answers"
    __table_args__ = (UniqueConstraint("round_id", "user_id", name="uq_contrasta_answers_one_per_user"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    round_id: Mapped[UUID] = mapped_column(ForeignKey("contrasta_rounds.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    answer: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
