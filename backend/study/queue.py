"""
Construcción de colas (HU-E03-01, HU-E03-03, HU-E04-02, HU-E05-02).

Orden (R-REP-08): pendientes de la más atrasada a la menos, luego nuevas en el
orden del mazo hasta el límite diario, con tope `session_max_cards` (R-SES-02).
Solo entran palabras publicadas en el idioma de estudio (R-CON-10) y de niveles
que el motor de derechos permite (R-DER-01).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from content.models import Word
from content.services.reading import (
    chars_without_strokes, characters_of, published_word_ids, words_with_audio, writing_levels,
)
from decks.services import deck_word_ids, system_word_ids
from entitlements.services import allowed_levels
from ops import params
from scheduling.services import states_for
from users.services import local_day, profile_of

from .models import Answer

NEW_LIMIT_PARAM = {"recognition": "new_limit_recognition", "writing": "new_limit_writing"}


@dataclass
class CardSpec:
    unit_kind: str
    unit_key: str
    word_id: int
    is_new: bool


@dataclass
class Candidates:
    due: list[CardSpec] = field(default_factory=list)
    fresh: list[CardSpec] = field(default_factory=list)  # ya recortadas al límite del día
    fresh_before_limit: int = 0
    in_review: int = 0
    locked: int = 0
    no_strokes: int = 0


def new_limit(account, skill: str) -> int | None:
    """Límite del perfil; la escucha no tiene límite propio (R-REP-07)."""
    p = profile_of(account)
    return {"recognition": p.new_limit_recognition, "writing": p.new_limit_writing}.get(skill)


def introduced_today(account, skill: str, today: date) -> int:
    return Answer.objects.filter(account=account, skill=skill, local_day=today, introduced_new=True, voided=False).count()


def scope_word_ids(account, deck=None) -> tuple[list[int], int]:
    """Palabras del alcance en orden, sin las bloqueadas; y cuántas se bloquearon."""
    levels = allowed_levels(account)
    if deck is None:
        return system_word_ids(levels), 0
    ids = deck_word_ids(deck)
    if deck.kind == "system":
        return (ids, 0) if deck.hsk_level in levels else ([], len(ids))
    level_of = dict(Word.objects.filter(pk__in=ids).values_list("pk", "hsk_level"))
    allowed = [w for w in ids if level_of.get(w) in levels]
    return allowed, len(ids) - len(allowed)


def candidates(account, skill: str, deck=None, today: date | None = None, apply_limit: bool = True) -> Candidates:
    today = today or local_day(account)
    lang = profile_of(account).study_language_id
    ids, locked = scope_word_ids(account, deck)
    c = Candidates(locked=locked)
    published = published_word_ids(lang, ids)
    due: list[tuple[date, CardSpec]] = []
    fresh: list[CardSpec] = []

    if skill == "writing":
        hanzi = dict(Word.objects.filter(pk__in=ids).values_list("pk", "hanzi"))
        chars_by_word = {w: characters_of(hanzi.get(w, "")) for w in ids}
        all_chars = {ch for lst in chars_by_word.values() for ch in lst}
        # R-ESC-10: solo los caracteres de la lista de escritura, desde su nivel y dentro del plan.
        wl = writing_levels(all_chars)
        allowed = set(allowed_levels(account))
        cap = deck.hsk_level if deck is not None and deck.kind == "system" else max(allowed, default=0)
        missing = chars_without_strokes(all_chars)
        states = states_for(account, "writing", all_chars)
        seen: set[str] = set()
        for w in ids:
            if w not in published:
                c.in_review += 1
                continue
            for ch in chars_by_word[w]:
                level = wl.get(ch)
                if ch in seen or level is None or level > cap or level not in allowed:
                    continue  # R-ESC-08 (una vez por cola) y R-ESC-10
                seen.add(ch)
                if ch in missing:
                    c.no_strokes += 1  # R-CON-12
                    continue
                st = states.get(ch)
                if st is None:
                    fresh.append(CardSpec("character", ch, w, True))
                elif st.due_day <= today:
                    due.append((st.due_day, CardSpec("character", ch, w, False)))
    else:
        states = states_for(account, skill, ids)
        if skill == "listening":
            rec = states_for(account, "recognition", ids)
            with_audio = words_with_audio(published)
        for w in ids:
            if w not in published:
                c.in_review += 1
                continue
            if skill == "listening":
                first = rec.get(str(w))
                # R-REP-07: desde el día siguiente al primer «Recordé» en lectura; R-CON-13: con audio.
                if w not in with_audio or first is None or first.first_pass_day is None or first.first_pass_day >= today:
                    continue
            st = states.get(str(w))
            if st is None:
                fresh.append(CardSpec("word", str(w), w, True))
            elif st.due_day <= today:
                due.append((st.due_day, CardSpec("word", str(w), w, False)))

    due.sort(key=lambda x: x[0])  # estable: a igual atraso, el orden del mazo
    c.due = [spec for _, spec in due]
    if skill == "writing" and deck is None:
        # En «todos los pendientes», los caracteres nuevos siguen los niveles de la lista de escritura.
        order = {spec.unit_key: i for i, spec in enumerate(fresh)}
        fresh.sort(key=lambda spec: (wl.get(spec.unit_key, 99), order[spec.unit_key]))
    c.fresh_before_limit = len(fresh)
    limit = new_limit(account, skill)
    if apply_limit and limit is not None:
        fresh = fresh[:max(0, limit - introduced_today(account, skill, today))]
    c.fresh = fresh
    return c


def build_queue(account, skill: str, deck=None) -> tuple[list[CardSpec], str | None]:
    c = candidates(account, skill, deck)
    queue = (c.due + c.fresh)[:params.value("session_max_cards")]
    if queue:
        return queue, None
    # R-SES-10: decir por qué no hay sesión.
    if c.fresh_before_limit > 0:
        return [], "new_limit_reached"
    if deck is not None and c.locked > 0 and c.in_review == 0:
        return [], "locked"
    if deck is not None and c.in_review > 0:
        return [], "in_review"
    return [], "nothing_due"


def counts(account, skill: str, deck=None) -> dict:
    c = candidates(account, skill, deck)
    return {"due": len(c.due), "new": len(c.fresh)}
