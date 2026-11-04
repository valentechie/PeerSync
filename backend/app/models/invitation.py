from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, str_enum


class InvitationStatus(str, Enum):
    PENDING = "pending"
    # Se conserva para que no se pueda volver a insistir a la misma persona en esa sala.
    DECLINED = "declined"


class RoomInvitation(Base):
    __tablename__ = "room_invitations"
    __table_args__ = (
        UniqueConstraint("session_id", "invitee_id", name="uq_room_invitations_one_per_person"),
        CheckConstraint("inviter_id <> invitee_id", name="not_self"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("study_sessions.id", ondelete="CASCADE"))
    inviter_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    invitee_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    status: Mapped[InvitationStatus] = mapped_column(
        str_enum(InvitationStatus, "invitation_status"), default=InvitationStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
