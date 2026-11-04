"""Compatibilidad entre estudiantes: reglas puras, sin LLM ni base de datos.

Puntuación sobre 100:
  - Hasta 40 por lo que puedes aprender: parte de lo que buscas que el otro ofrece.
  - Hasta 40 por lo que puedes enseñar: parte de lo que el otro busca que tú ofreces.
  - Hasta 20 por reputación. Sin valoraciones cuenta como 3/5, para no hundir a
    quien acaba de llegar ni darle ventaja sobre quien tiene buenas valoraciones.
"""

from collections.abc import Iterable
from dataclasses import dataclass

COVERAGE_WEIGHT = 40
REPUTATION_WEIGHT = 20
MAX_REPUTATION = 5
NEUTRAL_REPUTATION = 3.0


@dataclass(frozen=True)
class MatchScore:
    score: int
    learn_points: int
    teach_points: int
    reputation_points: int
    they_teach_you: list[str]
    you_teach_them: list[str]

    @property
    def is_complementary(self) -> bool:
        return bool(self.they_teach_you or self.you_teach_them)

    @property
    def shared_skills(self) -> int:
        return len(self.they_teach_you) + len(self.you_teach_them)


def _round(value: float) -> int:
    # round() de Python redondea 0.5 al par; aquí interesa una regla fácil de explicar.
    return int(value + 0.5)


def _overlap(wanted: Iterable[str], offered: Iterable[str]) -> list[str]:
    available = {skill.lower() for skill in offered}
    return sorted((skill for skill in wanted if skill.lower() in available), key=str.lower)


def _coverage_points(matched: list[str], wanted: Iterable[str]) -> int:
    total = len(set(skill.lower() for skill in wanted))
    return _round(COVERAGE_WEIGHT * len(matched) / total) if total else 0


def score_match(
    my_offering: Iterable[str],
    my_seeking: Iterable[str],
    their_offering: Iterable[str],
    their_seeking: Iterable[str],
    their_reputation: float | None,
) -> MatchScore:
    they_teach_you = _overlap(my_seeking, their_offering)
    you_teach_them = _overlap(their_seeking, my_offering)
    learn_points = _coverage_points(they_teach_you, my_seeking)
    teach_points = _coverage_points(you_teach_them, their_seeking)
    reputation = NEUTRAL_REPUTATION if their_reputation is None else their_reputation
    reputation_points = _round(REPUTATION_WEIGHT * reputation / MAX_REPUTATION)
    return MatchScore(
        score=learn_points + teach_points + reputation_points,
        learn_points=learn_points,
        teach_points=teach_points,
        reputation_points=reputation_points,
        they_teach_you=they_teach_you,
        you_teach_them=you_teach_them,
    )
