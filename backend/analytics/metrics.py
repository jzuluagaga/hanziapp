"""
Métricas del tablero (07-eventos-y-metricas.md §4, HU-E14-01).

Se calculan solo con la tabla de eventos, por cohorte. "Activado" es una cuenta
con al menos una respuesta contada.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from .models import Event

INTERVAL_BUCKETS = [("1", 1, 1), ("2-6", 2, 6), ("7-20", 7, 20), ("21+", 21, 10**9)]


def _accounts():
    """{account_key: {"cohort", "registered": date, "active": set[date]}} de las cuentas activadas."""
    accounts: dict = {}
    for e in Event.objects.filter(name="account_registered", account_key__isnull=False).only(
        "account_key", "cohort", "local_day",
    ):
        accounts[e.account_key] = {"cohort": e.cohort or "—", "registered": e.local_day, "active": set()}
    for key, day in Event.objects.filter(
        name="answer_recorded", props__counted=True, account_key__isnull=False,
    ).values_list("account_key", "local_day"):
        if key in accounts and day:
            accounts[key]["active"].add(day)
    return {k: v for k, v in accounts.items() if v["active"] and v["registered"]}


def _by_cohort(rows: dict) -> dict[str, list]:
    out = defaultdict(list)
    for a in rows.values():
        out[a["cohort"]].append(a)
        out["(todas)"].append(a)
    return out


def _ratio(num: int, den: int) -> dict:
    return {"num": num, "den": den, "pct": round(100 * num / den, 1) if den else None}


def retention_by_day(days=(1, 7, 28)) -> dict[str, dict[int, dict]]:
    """M-03: activados con día activo exactamente el día N desde su registro."""
    result = {}
    for cohort, accounts in _by_cohort(_accounts()).items():
        result[cohort] = {
            n: _ratio(sum(1 for a in accounts if a["registered"] + timedelta(days=n) in a["active"]), len(accounts))
            for n in days
        }
    return result


def week4_retention() -> dict[str, dict]:
    """M-02: activados con algún día activo entre el 22 y el 28 desde su registro."""
    result = {}
    for cohort, accounts in _by_cohort(_accounts()).items():
        hits = 0
        for a in accounts:
            window = {a["registered"] + timedelta(days=n) for n in range(22, 29)}
            hits += bool(window & a["active"])
        result[cohort] = _ratio(hits, len(accounts))
    return result


def accuracy_by_interval() -> dict[str, dict[str, dict]]:
    """M-04: pass ÷ contadas sin refuerzos, por tramo de intervalo programado y habilidad."""
    counts: dict = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    rows = Event.objects.filter(name="answer_recorded", props__counted=True).values_list("props", flat=True)
    for p in rows:
        if p.get("is_reinforcement"):
            continue
        days = p.get("scheduled_days") or 0
        bucket = next((label for label, lo, hi in INTERVAL_BUCKETS if lo <= days <= hi), None)
        if bucket is None:
            continue
        cell = counts[p.get("skill", "?")][bucket]
        cell[1] += 1
        cell[0] += p.get("grade") == "pass"
    return {skill: {b: _ratio(*buckets[b]) for b, _, _ in INTERVAL_BUCKETS} for skill, buckets in counts.items()}


def day_mix() -> dict[str, int]:
    """M-14: reparto de días cerrados."""
    out = {"active": 0, "exempt": 0, "missed": 0}
    for status in Event.objects.filter(name="day_closed").values_list("props__status", flat=True):
        if status in out:
            out[status] += 1
    return out


def summary(today: date | None = None) -> dict:
    return {
        "retention": retention_by_day(),
        "week4": week4_retention(),
        "accuracy": accuracy_by_interval(),
        "days": day_mix(),
        "buckets": [b for b, _, _ in INTERVAL_BUCKETS],
    }
