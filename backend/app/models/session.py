from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, Uuid, func
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


class TeachBackActivityStatus(str, Enum):
    PENDING = "pending"
    DECLINED = "declined"
    CANCELLED = "cancelled"
    ACTIVE = "active"
    COMPLETED = "completed"
    STOPPED = "stopped"


class ComparisonStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"


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
    """Sin `activity_id` es una explicación independiente; con él, un turno de una actividad de Contrasta."""

    __tablename__ = "teachback_submissions"
    __table_args__ = (UniqueConstraint("activity_id", "turn", name="uq_teachback_submissions_activity_turn"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("study_sessions.id", ondelete="CASCADE"), index=True)
    explainer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    concept: Mapped[str] = mapped_column(String(200))
    explanation: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    activity_id: Mapped[UUID | None] = mapped_column(ForeignKey("teachback_activities.id", ondelete="CASCADE"), index=True)
    turn: Mapped[int | None] = mapped_column(Integer)


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
    # Con pareja, solo esas dos personas participan y ven las respuestas. Sin ella, la ronda
    # sigue las reglas de siempre: todos los miembros activos y sin recorrido guiado.
    pair_a_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    pair_b_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    conclusion: Mapped[str | None] = mapped_column(Text)
    conclusion_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    conclusion_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    conclusion_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finish_requested_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ContrastaAnswer(Base):
    """Oculta al compañero hasta que la ronda pase a `revealed`. Lo aplica el servicio."""

    __tablename__ = "contrasta_answers"
    __table_args__ = (UniqueConstraint("round_id", "user_id", name="uq_contrasta_answers_one_per_user"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    round_id: Mapped[UUID] = mapped_column(ForeignKey("contrasta_rounds.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    answer: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContrastaComparison(Base):
    """Comparación con IA, pedida expresamente y única por ronda aunque la pidan los dos a la vez."""

    __tablename__ = "contrasta_comparisons"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    round_id: Mapped[UUID] = mapped_column(ForeignKey("contrasta_rounds.id", ondelete="CASCADE"), unique=True)
    requested_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    status: Mapped[ComparisonStatus] = mapped_column(str_enum(ComparisonStatus, "contrasta_comparison_status"))
    result: Mapped[dict | None] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ContrastaCard(Base):
    """Pista o comprobación de StudyMind pedida dentro de una ronda."""

    __tablename__ = "contrasta_cards"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    round_id: Mapped[UUID] = mapped_column(ForeignKey("contrasta_rounds.id", ondelete="CASCADE"), index=True)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(10))
    request: Mapped[str] = mapped_column(Text)
    result: Mapped[dict] = mapped_column(JSON)
    # Antes de revelar, lo que escribe un estudiante podría delatar su respuesta.
    private: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TeachBackActivity(Base):
    """Propuesta y actividad TeachBack de una pareja. Nace pendiente: uno solo no la impone."""

    __tablename__ = "teachback_activities"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    round_id: Mapped[UUID] = mapped_column(ForeignKey("contrasta_rounds.id", ondelete="CASCADE"), index=True)
    proposer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    partner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    concept: Mapped[str] = mapped_column(String(200))
    status: Mapped[TeachBackActivityStatus] = mapped_column(
        str_enum(TeachBackActivityStatus, "teachback_activity_status"), default=TeachBackActivityStatus.PENDING
    )
    # Turno 1: explica quien propone. Turno 2: explica su pareja.
    turn: Mapped[int] = mapped_column(Integer, default=1)
    skip_requested_by_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    # Sugerencias de IA por turno. Son formativas: no hay nota.
    feedback: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ContrastaCheck(Base):
    """Comprobación individual breve. No tiene nota ni solución: no mide objetivamente nada."""

    __tablename__ = "contrasta_checks"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    round_id: Mapped[UUID] = mapped_column(ForeignKey("contrasta_rounds.id", ondelete="CASCADE"), unique=True)
    author_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    question: Mapped[str] = mapped_column(Text)
    # "ai" o "peer": el frontend indica siempre de dónde viene la pregunta.
    source: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContrastaCheckAnswer(Base):
    """Oculta al compañero hasta que respondan los dos. Lo aplica el servicio."""

    __tablename__ = "contrasta_check_answers"
    __table_args__ = (UniqueConstraint("check_id", "user_id", name="uq_contrasta_check_answers_one_per_user"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    check_id: Mapped[UUID] = mapped_column(ForeignKey("contrasta_checks.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    answer: Mapped[str] = mapped_column(Text)
    reflection: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContrastaReaction(Base):
    """Reacción a la respuesta revelada del compañero. Una por persona: cambiarla la sustituye."""

    __tablename__ = "contrasta_reactions"
    __table_args__ = (UniqueConstraint("round_id", "user_id", name="uq_contrasta_reactions_one_per_user"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    round_id: Mapped[UUID] = mapped_column(ForeignKey("contrasta_rounds.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # "agree", "doubt" o "convince".
    kind: Mapped[str] = mapped_column(String(10))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ContrastaPrediction(Base):
    """Qué cree cada uno que responderá el otro. Oculta hasta revelar y nunca llega a la IA."""

    __tablename__ = "contrasta_predictions"
    __table_args__ = (UniqueConstraint("round_id", "user_id", name="uq_contrasta_predictions_one_per_user"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    round_id: Mapped[UUID] = mapped_column(ForeignKey("contrasta_rounds.id", ondelete="CASCADE"))
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
