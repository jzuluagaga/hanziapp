"""Día, racha y progreso (HU-E09-01, HU-E09-02)."""
from __future__ import annotations

from datetime import date, timedelta

from django.db import transaction

from analytics.services import emit
from content.models import Word
from content.services.reading import characters_of, published_counts, published_word_ids, syllabus_totals
from entitlements.services import allowed_levels
from scheduling.models import ReviewState
from scheduling.services import is_learned, pending_units_on
from users.services import local_day, profile_of

from .models import ActiveDay, DayRecord, StreakRecord

MAX_CLOSE_DAYS = 400


def _record(account) -> StreakRecord:
    rec, _ = StreakRecord.objects.get_or_create(account=account)
    return rec


def is_active(account, day: date) -> bool:
    return ActiveDay.objects.filter(account=account, day=day).exists()


def current_streak(account, today: date | None = None) -> int:
    """R-PRO-04: días activos desde el último fallado; exento no suma ni rompe; hoy no es fallado."""
    today = today or local_day(account)
    count = 1 if is_active(account, today) else 0
    expected = today - timedelta(days=1)
    for day, status in DayRecord.objects.filter(account=account, day__lt=today).order_by("-day").values_list("day", "status"):
        if day != expected or status == DayRecord.Status.MISSED:
            break  # un hueco (día sin cerrar o antes de la cuenta) corta la racha
        if status == DayRecord.Status.ACTIVE:
            count += 1
        expected = day - timedelta(days=1)
    return count


def streak(account) -> dict:
    today = local_day(account)
    cur = current_streak(account, today)
    return {"current": cur, "max": max(_record(account).max_streak, cur), "today_active": is_active(account, today)}


def on_answer_recorded(sender, account, counted, local_day, **kwargs) -> None:
    if not counted:
        return
    _, created = ActiveDay.objects.get_or_create(account=account, day=local_day)
    if created:
        close_days(account)  # la racha necesita los días anteriores cerrados
        length = current_streak(account, local_day)
        rec = _record(account)
        if length > rec.max_streak:
            rec.max_streak = length
            rec.save(update_fields=["max_streak"])
        emit("streak_changed", account, local_day=local_day, length=length, change="extended")


def _studiable(account):
    """«Que pudiera estudiar» con el plan y el idioma vigentes al cerrar (R-PRO-09)."""
    lang = profile_of(account).study_language_id
    ids = Word.objects.filter(hsk_level__in=allowed_levels(account), retired_at__isnull=True).values_list("pk", flat=True)
    words = published_word_ids(lang, ids)
    chars = {ch for h in Word.objects.filter(pk__in=words).values_list("hanzi", flat=True) for ch in characters_of(h)}
    return lambda skill, unit: (unit in chars) if skill == "writing" else (unit.isdigit() and int(unit) in words)


@transaction.atomic
def close_days(account) -> int:
    """Cierra los días pasados sin estado. Lo hace la tarea programada o, si no corrió, el primer acceso."""
    today = local_day(account)
    yesterday = today - timedelta(days=1)
    rec = StreakRecord.objects.select_for_update().get_or_create(account=account)[0]
    start = rec.last_closed_day + timedelta(days=1) if rec.last_closed_day else local_day(account, account.date_joined)
    start = max(start, yesterday - timedelta(days=MAX_CLOSE_DAYS))
    if start > yesterday:
        return 0
    studiable = None
    closed = 0
    d = start
    while d <= yesterday:
        if not DayRecord.objects.filter(account=account, day=d).exists():
            before = current_streak(account, d)  # racha al empezar ese día, sin contarlo
            if is_active(account, d):
                status, due = DayRecord.Status.ACTIVE, 0
            else:
                studiable = studiable or _studiable(account)
                due = pending_units_on(account, d, studiable)
                status = DayRecord.Status.MISSED if due else DayRecord.Status.EXEMPT
            DayRecord.objects.create(account=account, day=d, status=status, due_at_close=due)
            emit("day_closed", account, local_day=d, status=status, due_at_close=due)
            if status == DayRecord.Status.MISSED and before > 0:
                emit("streak_changed", account, local_day=d, length=0, change="broken")
            closed += 1
        d += timedelta(days=1)
    rec.last_closed_day = yesterday
    rec.max_streak = max(rec.max_streak, current_streak(account, today))
    rec.save(update_fields=["last_closed_day", "max_streak"])
    return closed


def progress_summary(account) -> dict:
    """R-PRO-05, R-PRO-06: cada palabra y carácter una vez; solo contenido vigente."""
    lang = profile_of(account).study_language_id
    vigentes = dict(Word.objects.filter(retired_at__isnull=True).values_list("pk", "hsk_level"))
    learned_by_level = {n: 0 for n in range(1, 7)}
    learned_words = 0
    for st in ReviewState.objects.filter(account=account, skill="recognition"):
        level = vigentes.get(int(st.unit_key)) if st.unit_key.isdigit() else None
        if level and is_learned(st):
            learned_words += 1
            learned_by_level[level] += 1
    learned_chars = sum(1 for st in ReviewState.objects.filter(account=account, skill="writing") if is_learned(st))
    totals, published = syllabus_totals(), published_counts(lang)
    days = list(DayRecord.objects.filter(account=account).order_by("-day").values("day", "status")[:56])
    return {
        "learned_words": learned_words, "learned_chars": learned_chars,
        "levels": [{"level": n, "total": totals[n], "published": published[n], "learned": learned_by_level[n]}
                   for n in range(1, 7)],
        "streak": streak(account), "days": days,
    }


def delete_account_data(account) -> None:
    ActiveDay.objects.filter(account=account).delete()
    DayRecord.objects.filter(account=account).delete()
    StreakRecord.objects.filter(account=account).delete()
