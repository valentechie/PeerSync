from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Index, String, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, str_enum


class SkillKind(str, Enum):
    OFFERING = "offering"
    SEEKING = "seeking"


class Skill(Base):
    __tablename__ = "skills"
    # "React" y "react" son la misma habilidad; el matching depende de ello.
    __table_args__ = (Index("uq_skills_name_lower", text("lower(name)"), unique=True),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100))


class UserSkill(Base):
    __tablename__ = "user_skills"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True, index=True)
    kind: Mapped[SkillKind] = mapped_column(str_enum(SkillKind, "skill_kind"), primary_key=True)
