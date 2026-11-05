import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.deepseek_client import LLM_FAILURES
from app.ai.studymind import hint_generator
from app.models.user import User
from app.schemas.ai import StudyMindRead
from app.services import room_service

logger = logging.getLogger(__name__)


def request_help(db: Session, user: User, room_id: UUID, difficulty: str, step: int) -> StudyMindRead:
    """Cada ayuda nace de una petición explícita: nunca se infiere un bloqueo."""
    room = room_service.get_open_member_room(db, user, room_id)
    topic = room.objective or room.title
    # Libera la conexión: la llamada a la IA puede tardar y no necesita la base de datos.
    db.rollback()

    source = "ai"
    try:
        output = hint_generator.next_help(topic, difficulty, step)
    except LLM_FAILURES as exc:
        logger.warning("StudyMind sin IA: %s", type(exc).__name__)
        source = "fallback"
        output = hint_generator.prepared_help(step)
    return StudyMindRead(source=source, step=step, **output.model_dump())
