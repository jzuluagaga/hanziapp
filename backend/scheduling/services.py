"""Servicio de `scheduling`: aplicar una respuesta contada y consultar estados."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from django.db import transaction

from ops import params
from users.services import local_day

from .fsrs_adapter import Memory, Scheduler
from .models import ReviewLog, ReviewState


@dataclass
class ReviewResult:
    state: ReviewState
    was_new: bool
    days_since_last: int
    scheduled_days: int


def states_for(account, skill: str, unit_keys=None) -> dict[str, ReviewState]:
    qs = ReviewState.objects.filter(account=account, skill=skill)
    if unit_keys is not None:
        qs = qs.filter(unit_key__in=[str(k) for k in unit_keys])
    return {s.unit_key: s for s in qs}


def is_learned(state: ReviewState | None) -> bool:
    """R-REP-12: valor derivado; puede dejar de cumplirse tras un «No recordé»."""
    return state is not None and state.stability >= params.value("learned_stability_days")


@transaction.atomic
def apply_review(account, skill: str, unit_key: str, grade: str, at: datetime, *, word_id: int | None = None) -> ReviewResult:
    """Calcula y guarda el estado nuevo. Quien llama decide si la respuesta cuenta (R-REP-05)."""
    unit_key = str(unit_key)
    prev = ReviewState.objects.select_for_update().filter(account=account, skill=skill, unit_key=unit_key).first()
    memory = None if prev is None else Memory(prev.stability, prev.difficulty, prev.fsrs_state, prev.due_at, prev.last_review_at)
    new = Scheduler(skill).review(memory, grade, at)
    today = local_day(account, at)
    due_day = local_day(account, new.due_at)
    days_since = (today - prev.last_review_day).days if prev else 0
    scheduled = (prev.due_day - prev.last_review_day).days if prev else 0
    state = prev or ReviewState(account=account, skill=skill, unit_key=unit_key, word_id=word_id)
    state.stability, state.difficulty, state.fsrs_state = new.stability, new.difficulty, new.fsrs_state
    state.due_at, state.due_day = new.due_at, due_day
    state.last_review_at, state.last_review_day = at, today
    state.reps = (prev.reps if prev else 0) + 1
    state.lapses = (prev.lapses if prev else 0) + (grade == "fail" and prev is not None)
    if grade == "pass" and not state.first_pass_day:
        state.first_pass_day = today
    state.save()
    ReviewLog.objects.create(account=account, skill=skill, unit_key=unit_key, grade=grade, reviewed_at=at,
                             review_day=today, elapsed_days=days_since, scheduled_days=scheduled,
                             stability_after=new.stability, difficulty_after=new.difficulty, due_day_after=due_day)
    return ReviewResult(state=state, was_new=prev is None, days_since_last=days_since, scheduled_days=scheduled)


def pending_units_on(account, day: date, studiable=None) -> int:
    """Cuántas unidades estaban pendientes el día `day`, reconstruido con el historial:
    una unidad lo estaba si su último repaso anterior a ese día la programó para ese día o antes.
    `studiable(skill, unit_key) -> bool` filtra lo que el plan y el idioma permitían."""
    latest: dict[tuple[str, str], date] = {}
    for skill, unit, due_after in (ReviewLog.objects.filter(account=account, review_day__lt=day)
                                   .order_by("skill", "unit_key", "reviewed_at")
                                   .values_list("skill", "unit_key", "due_day_after")):
        latest[(skill, unit)] = due_after
    return sum(1 for (skill, unit), due in latest.items()
               if due <= day and (studiable is None or studiable(skill, unit)))


def delete_account_data(account) -> None:
    ReviewLog.objects.filter(account=account).delete()
    ReviewState.objects.filter(account=account).delete()
