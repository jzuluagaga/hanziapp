"""
Sesiones y respuestas (flujos 1 y 2 de 09-arquitectura.md).
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from analytics.services import emit
from content.models import Word
from content.services.reading import published_word_ids, word_payloads
from decks.models import Deck
from entitlements.services import allowed_levels, deny
from hanzi_backend.exception_handlers import ApiError
from ops import params
from scheduling.services import apply_review, states_for
from users.services import local_day, profile_of

from .models import Answer, SessionCard, StudySession
from .queue import build_queue, introduced_today, new_limit
from .signals import answer_recorded

SKILLS = ("recognition", "listening", "writing")


class StaleCard(Exception):
    def __init__(self, session):
        self.session = session


# ───────────────────────────── Representación (Docs/10-api.md §6)

def _card_payload(c: SessionCard) -> dict:
    return {"position": c.position, "unit": c.unit_key, "unit_kind": c.unit_kind, "word_id": str(c.word_id),
            "is_new": c.is_new, "is_reinforcement": c.is_reinforcement, "result": c.result,
            "choices": [str(x) for x in c.choices] if c.choices else None}


def summary_of(session: StudySession) -> dict:
    """Aciertos y fallos de las primeras respuestas, sin refuerzos (HU-E03-04)."""
    cards = [c for c in session.cards.all() if not c.is_reinforcement and c.result in ("pass", "fail")]
    return {"answered": len(cards), "passed": sum(c.result == "pass" for c in cards),
            "failed": sum(c.result == "fail" for c in cards)}


def session_summary(session: StudySession) -> dict:
    total = session.cards.count()
    return {"id": str(session.id), "scope": _scope(session), "skill": session.skill, "kind": session.kind,
            "status": session.status, "chain": session.chain, "position": session.position, "total": total,
            "done": session.cards.exclude(result__isnull=True).count(), "last_activity_at": session.last_activity_at}


def _scope(session):
    if not session.deck_id:
        return {"type": "all_due"}
    return {"type": "deck", "deck_id": str(session.deck_id), "level": session.deck.hsk_level, "index": session.deck.index}


def session_payload(session: StudySession) -> dict:
    cards = list(session.cards.order_by("position"))
    lang = profile_of(session.account).study_language_id
    word_ids = {c.word_id for c in cards} | {int(x) for c in cards for x in (c.choices or [])}
    words = word_payloads(word_ids, lang)
    return {
        "id": str(session.id), "scope": _scope(session), "skill": session.skill, "kind": session.kind,
        "status": session.status, "chain": session.chain, "position": session.position,
        "started_at": session.started_at, "cards": [_card_payload(c) for c in cards],
        "words": {str(k): v for k, v in words.items()}, "summary": summary_of(session),
    }


# ───────────────────────────── Iniciar (HU-E03-01)

def _listening_choices(word_id: int, level: int, pool: list[int], seed: str) -> list[int]:
    """La correcta y tres palabras publicadas del mismo nivel, en orden fijo (HU-E04-02)."""
    rng = random.Random(seed)
    others = [w for w in pool if w != word_id]
    picks = rng.sample(others, min(3, len(others))) + [word_id]
    rng.shuffle(picks)
    return picks


@dataclass
class StartResult:
    kind: str  # started | conflict | empty
    session: StudySession | None = None
    reason: str | None = None


def active_sessions(account):
    return StudySession.objects.filter(account=account, status=StudySession.Status.ACTIVE)


@transaction.atomic
def start_session(account, *, skill: str, deck: Deck | None = None, chain: bool = False, force: bool = False) -> StartResult:
    if skill not in SKILLS:
        raise ApiError("invalid_input", field="skill")
    scope_key = f"deck:{deck.pk}" if deck else "all_due"
    existing = active_sessions(account).filter(skill=skill, scope_key=scope_key).first()
    if existing:
        if not force:
            return StartResult("conflict", existing)  # R-SES-05
        discard(existing)
    if deck is not None and deck.kind == "system" and deck.hsk_level not in allowed_levels(account):
        deny(account, f"study.level.{deck.hsk_level}", "session")

    queue, reason = build_queue(account, skill, deck)
    if not queue:
        emit("session_empty", account, skill=skill, reason=reason)
        return StartResult("empty", reason=reason)

    session = StudySession.objects.create(account=account, scope_type="deck" if deck else "all_due", deck=deck,
                                          scope_key=scope_key, skill=skill, chain=chain)
    pools: dict[int, list[int]] = {}
    if skill == "listening":
        level_of = dict(Word.objects.filter(pk__in=[s.word_id for s in queue]).values_list("pk", "hsk_level"))
        lang = profile_of(account).study_language_id
        for level in set(level_of.values()):
            ids = Word.objects.filter(hsk_level=level, retired_at__isnull=True).values_list("pk", flat=True)
            pools[level] = sorted(published_word_ids(lang, ids))
    SessionCard.objects.bulk_create([
        SessionCard(session=session, position=i, unit_kind=s.unit_kind, unit_key=s.unit_key, word_id=s.word_id,
                    is_new=s.is_new,
                    choices=_listening_choices(s.word_id, level_of[s.word_id], pools[level_of[s.word_id]],
                                               f"{session.id}:{i}") if skill == "listening" else None)
        for i, s in enumerate(queue)
    ])
    emit("session_started", account, session_id=session.id, skill=skill, scope=session.scope_type, kind=session.kind,
         queue_size=len(queue), due_count=sum(not s.is_new for s in queue), new_count=sum(s.is_new for s in queue))
    return StartResult("started", session)


# ───────────────────────────── Reanudar y descartar (HU-E06-02)

@transaction.atomic
def resume(session: StudySession, same_client: bool | None = None) -> StudySession:
    """R-SES-06: sigue en la primera sin responder; lo ya repasado hoy por otra vía se salta."""
    session = StudySession.objects.select_for_update().get(pk=session.pk)
    if session.status != StudySession.Status.ACTIVE:
        return session
    account = session.account
    today = local_day(account)
    pending = list(session.cards.filter(result__isnull=True, is_reinforcement=False))
    states = states_for(account, session.skill, [c.unit_key for c in pending])
    skipped = 0
    for c in pending:
        st = states.get(c.unit_key)
        if st and st.last_review_day >= today:
            c.result = "skipped"
            c.save(update_fields=["result"])
            skipped += 1
    last = session.answers.order_by("-received_at").values_list("received_at", flat=True).first()
    _advance(session)
    emit("session_resumed", account, session_id=session.id, skill=session.skill, position=session.position,
         skipped_already_reviewed=skipped,
         hours_since_last_answer=round((timezone.now() - last).total_seconds() / 3600, 1) if last else None,
         same_client=same_client)
    return session


def discard(session: StudySession) -> StudySession:
    """R-SES-08: lo ya respondido es definitivo."""
    if session.status == StudySession.Status.ACTIVE:
        session.status = StudySession.Status.DISCARDED
        session.ended_at = timezone.now()
        session.save(update_fields=["status", "ended_at"])
        emit("session_discarded", session.account, session_id=session.id, skill=session.skill,
             position=session.position, queue_size=session.cards.count())
    return session


def expire_sessions(now: datetime | None = None) -> int:
    now = now or timezone.now()
    limit = now - timedelta(days=params.value("session_ttl_days"))
    n = 0
    for session in StudySession.objects.filter(status=StudySession.Status.ACTIVE, last_activity_at__lt=limit):
        with transaction.atomic():
            session.status = StudySession.Status.EXPIRED
            session.ended_at = now
            session.save(update_fields=["status", "ended_at"])
            emit("session_expired", session.account, session_id=session.id, skill=session.skill,
                 position=session.position, queue_size=session.cards.count())
        n += 1
    return n


def _advance(session: StudySession) -> None:
    nxt = session.cards.filter(result__isnull=True).order_by("position").first()
    now = timezone.now()
    if nxt is None:
        if session.status == StudySession.Status.ACTIVE:
            session.status = StudySession.Status.COMPLETED
            session.ended_at = now
            s = summary_of(session)
            emit("session_completed", session.account, session_id=session.id, skill=session.skill, kind=session.kind,
                 answered=s["answered"], passed=s["passed"], failed=s["failed"],
                 duration_s=int((now - session.started_at).total_seconds()))
        session.position = session.cards.count()
    else:
        session.position = nxt.position
    session.save(update_fields=["status", "ended_at", "position"])


# ───────────────────────────── Responder (flujo 1, HU-E00-01, HU-E06-01)

def _writing_grade(misses: int, hint: bool) -> tuple[str, int]:
    """R-ESC-03: el sistema califica, no el estudiante."""
    threshold = int(params.value("writing_max_stroke_misses"))
    return ("pass" if not hint and misses <= threshold else "fail"), threshold


def _clamp_time(client_at: datetime | None, session: StudySession, now: datetime) -> datetime:
    """R-SES-11: la hora del dispositivo solo vale entre el inicio de la sesión y la recepción."""
    if client_at and session.started_at <= client_at <= now:
        return client_at
    return now


def record_answer(account, data: dict) -> dict:
    """Aplica una respuesta una sola vez. `data` viene validado por la vista."""
    existing = Answer.objects.filter(account=account, client_id=data["client_id"]).first()
    if existing:
        return existing.response  # reenvío: mismo resultado, sin efecto (R-SES-03)
    try:
        return _record_answer(account, data)
    except StaleCard as e:
        emit("answer_rejected_stale", account, session_id=e.session.id)  # fuera de la transacción revertida
        raise
    except IntegrityError:
        # Otro envío con el mismo identificador ganó la carrera: devolver lo guardado.
        return Answer.objects.get(account=account, client_id=data["client_id"]).response


@transaction.atomic
def _record_answer(account, data: dict) -> dict:
    session = StudySession.objects.select_for_update().filter(pk=data["session_id"], account=account).first()
    if session is None:
        raise ApiError("not_found", 404)
    card = session.cards.filter(position=data["position"]).first()
    if (session.status != StudySession.Status.ACTIVE or card is None or card.unit_key != str(data["unit"])
            or card.result is not None):
        raise StaleCard(session)  # R-SES-07: gana la primera respuesta

    now = timezone.now()
    at = _clamp_time(data.get("answered_at"), session, now)
    today = local_day(account, at)
    skill = session.skill
    writing = data.get("writing") or {}
    mode = writing.get("mode", "recall") if skill == "writing" else ""
    threshold = misses = hint = None
    if skill == "writing":
        misses, hint = int(writing.get("stroke_misses", 0)), bool(writing.get("hint_used", False))
        grade, threshold = _writing_grade(misses, hint)
    elif skill == "listening":
        grade = "pass" if str(data.get("choice", "")) == str(card.word_id) else "fail"
    else:
        grade = data["grade"]

    guided = mode == "guided"
    counted = session.kind == "scheduled" and not card.is_reinforcement and not guided  # R-ESC-02
    prev = states_for(account, skill, [card.unit_key]).get(card.unit_key)
    if prev and prev.last_review_day >= today:
        counted = False  # R-REP-05, R-REP-09: solo la primera respuesta del día
    result = apply_review(account, skill, card.unit_key, grade, at,
                          word_id=card.word_id if card.unit_kind == "word" else None) if counted else None
    introduced = bool(result and result.was_new)

    cards_added = []
    if not guided:  # la práctica con guía no consume la tarjeta (R-ESC-06)
        card.result, card.answered_at = grade, at
        card.save(update_fields=["result", "answered_at"])
        if grade == "fail":  # R-REP-05: refuerzo tras `reinforce_gap` tarjetas
            total = session.cards.count()
            insert_at = min(card.position + 1 + int(params.value("reinforce_gap")), total)
            for c in session.cards.filter(position__gte=insert_at).order_by("-position"):
                SessionCard.objects.filter(pk=c.pk).update(position=F("position") + 1)
            added = SessionCard.objects.create(session=session, position=insert_at, unit_kind=card.unit_kind,
                                               unit_key=card.unit_key, word_id=card.word_id, is_reinforcement=True,
                                               choices=card.choices)
            cards_added.append(_card_payload(added))
        session.last_activity_at = now
        session.save(update_fields=["last_activity_at"])
        _advance(session)

    response = {
        "answer": {"client_id": str(data["client_id"]), "grade": grade, "counted": counted, "introduced_new": introduced},
        "session": {"status": session.status, "position": session.position, "cards_added": cards_added},
    }
    Answer.objects.create(
        account=account, client_id=data["client_id"], session=session, card=card, skill=skill, unit_key=card.unit_key,
        grade=grade, counted=counted, introduced_new=introduced, is_reinforcement=card.is_reinforcement,
        answered_at=at, local_day=today, response_ms=data.get("response_ms"), mode=mode, stroke_misses=misses,
        hint_used=hint, threshold=threshold, replays=data.get("replays"), choice=str(data.get("choice") or ""),
        response=response,
    )
    level = Word.objects.filter(pk=card.word_id).values_list("hsk_level", flat=True).first()
    extra = {"mode": mode, "stroke_misses": misses, "hint_used": hint, "threshold": threshold} if skill == "writing" else {}
    if skill == "listening":
        extra["replays"] = data.get("replays")
    emit("answer_recorded", account, occurred_at=now, local_day=today, session_id=session.id, skill=skill,
         session_kind=session.kind, item_kind="character" if card.unit_kind == "character" else "word",
         hsk_level=level, grade=grade, counted=counted, is_first_ever=prev is None and counted,
         is_reinforcement=card.is_reinforcement,
         days_since_last=result.days_since_last if result else None,
         scheduled_days=result.scheduled_days if result else None, response_ms=data.get("response_ms"), **extra)
    attempts = int(data.get("attempts") or 1)
    if attempts > 1:
        first = data.get("first_attempt_at") or at
        emit("answer_delivery_delayed", account, attempts=attempts, delay_s=max(0, int((now - first).total_seconds())))
    limit = new_limit(account, skill)
    if introduced and limit is not None and introduced_today(account, skill, today) == limit:
        emit("new_limit_reached", account, skill=skill, limit=limit)
    answer_recorded.send(sender=Answer, account=account, counted=counted, local_day=today, skill=skill)
    return response


def recent_decks(account, n: int = 6) -> list[dict]:
    """Mazos estudiados hace poco, con lo pendiente en lectura, para «Hoy»."""
    from decks.services import deck_word_ids

    from .queue import counts

    seen: list[int] = []
    for deck_id in (StudySession.objects.filter(account=account, deck__isnull=False)
                    .order_by("-last_activity_at").values_list("deck_id", flat=True)[:50]):
        if deck_id not in seen:
            seen.append(deck_id)
        if len(seen) == n:
            break
    out = []
    for deck in Deck.objects.filter(pk__in=seen, retired_at__isnull=True):
        ids = deck_word_ids(deck)
        first = Word.objects.filter(pk=ids[0]).values_list("hanzi", flat=True).first() if ids else ""
        out.append({"id": str(deck.pk), "level": deck.hsk_level, "index": deck.index, "sample": (first or "")[:1],
                    "recognition": counts(account, "recognition", deck)})
    return sorted(out, key=lambda d: seen.index(int(d["id"])))


def total_counted(account) -> int:
    return Answer.objects.filter(account=account, counted=True, voided=False).count()


def delete_account_data(account) -> None:
    Answer.objects.filter(account=account).delete()
    SessionCard.objects.filter(session__account=account).delete()
    StudySession.objects.filter(account=account).delete()
