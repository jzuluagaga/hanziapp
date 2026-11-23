"""
Adaptador de FSRS detrás de una interfaz (R-REP-02). Sesiones y progreso no
conocen la librería: solo `Scheduler.review`.

- Solo dos calificaciones: Recordé → Good, No recordé → Again (R-REP-03).
- Sin pasos de aprendizaje: los intervalos son días; el refuerzo dentro de la
  sesión lo hace `study` (R-REP-05).
- Sin aleatoriedad, para que las secuencias de referencia sean reproducibles (Q-22).
- Parámetros y retención por habilidad desde `ops` (`fsrs.parameters.<skill>`).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from fsrs import Card, Rating, Scheduler as _FsrsScheduler, State

from ops.services import get_param

RATING = {"pass": Rating.Good, "fail": Rating.Again}
LIBRARY_VERSION = "6.3.3"


@dataclass(frozen=True)
class Memory:
    stability: float
    difficulty: float
    fsrs_state: int
    due_at: datetime
    last_review_at: datetime | None


class Scheduler:
    def __init__(self, skill: str):
        from ops import params

        kwargs = {
            "desired_retention": float(params.value("fsrs_target_retention")),
            "learning_steps": (), "relearning_steps": (), "enable_fuzzing": False,
        }
        custom = get_param(f"fsrs.parameters.{skill}", None)
        if custom:
            kwargs["parameters"] = tuple(custom)
        self._fsrs = _FsrsScheduler(**kwargs)

    def review(self, prev: Memory | None, grade: str, at: datetime) -> Memory:
        if grade not in RATING:
            raise ValueError(f"Calificación no admitida: {grade}")
        card = Card(card_id=1) if prev is None else Card(
            card_id=1, state=State(prev.fsrs_state), step=None, stability=prev.stability,
            difficulty=prev.difficulty, due=prev.due_at.astimezone(timezone.utc),
            last_review=prev.last_review_at.astimezone(timezone.utc) if prev.last_review_at else None,
        )
        card, _ = self._fsrs.review_card(card, RATING[grade], at.astimezone(timezone.utc))
        return Memory(card.stability, card.difficulty, int(card.state), card.due, card.last_review)
