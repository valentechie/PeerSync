"""Puntuación de afinidad entre dos personas: reglas puras, sin LLM ni base de datos.

Cada punto sale de algo que se puede enseñar a la persona, así que el resultado
es reproducible y siempre se puede explicar. El máximo posible es 100.
"""

from typing import Literal

from app.ai.skillswap.studies import StudyRelation

Strength = Literal["strong", "good", "possible"]

SAME_STUDY_POINTS = 35
SIMILAR_STUDY_POINTS = 20
INTEREST_POINTS = 15
MAX_COUNTED_INTERESTS = 3
ROOM_POINTS = 10
MAX_COUNTED_ROOMS = 2

STRONG_FROM = 60
GOOD_FROM = 35


def connection_score(relation: StudyRelation | None, shared_interests: int, shared_rooms: int) -> int:
    study_points = {StudyRelation.DIRECT: SAME_STUDY_POINTS, StudyRelation.SIMILAR: SIMILAR_STUDY_POINTS}
    return (
        study_points.get(relation, 0)
        + INTEREST_POINTS * min(shared_interests, MAX_COUNTED_INTERESTS)
        + ROOM_POINTS * min(shared_rooms, MAX_COUNTED_ROOMS)
    )


def connection_strength(score: int) -> Strength:
    if score >= STRONG_FROM:
        return "strong"
    return "good" if score >= GOOD_FROM else "possible"
