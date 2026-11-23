"""Construcción y lectura de mazos (HU-E08-01)."""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from content.models import Word
from ops import params

from .models import Deck, DeckWord


def _themed_plan(level: int, ids: list[int]):
    """Plan por tema si todas las palabras vigentes del nivel tienen su subtema aprobado; si no, None."""
    from content.models import WordTheme
    from content.services.themes import taxonomy

    from .themed import plan_level

    approved = dict(WordTheme.objects.filter(word_id__in=ids, status=WordTheme.Status.APPROVED)
                    .values_list("word_id", "subtheme"))
    if not ids or len(approved) < len(ids):
        return None
    by_sub: dict[str, list[int]] = {}
    for wid in ids:  # ids ya va en el orden del sílabo
        by_sub.setdefault(approved[wid], []).append(wid)
    return plan_level(taxonomy(), by_sub, int(params.per_level("system_deck_size", level)))


def _save_deck(level: int, index: int, word_ids: list[int], theme_keys: list[str], part) -> None:
    deck, _ = Deck.objects.get_or_create(kind=Deck.Kind.SYSTEM, hsk_level=level, index=index)
    fields = {"retired_at": None, "theme_keys": theme_keys, "part": part}
    if any(getattr(deck, k) != v for k, v in fields.items()):
        for k, v in fields.items():
            setattr(deck, k, v)
        deck.save(update_fields=list(fields))
    current = list(deck.entries.order_by("position").values_list("word_id", flat=True))
    if current != word_ids:
        deck.entries.all().delete()
        DeckWord.objects.bulk_create([DeckWord(deck=deck, word_id=w, position=i) for i, w in enumerate(word_ids)])


@transaction.atomic
def build_system_decks(levels=None) -> dict[int, int]:
    """Arma los mazos del sistema de cada nivel: por tema si el nivel tiene todos sus temas
    aprobados (D-49); si no, en tramos de `system_deck_size` en el orden del sílabo (D-43).
    Repetible: conserva el identificador de cada mazo (nivel, índice) y retira los que sobran.
    Devuelve {nivel: número de mazos}."""
    levels = levels or range(1, 7)
    summary = {}
    for level in levels:
        size = int(params.per_level("system_deck_size", level))
        ids = list(Word.objects.filter(hsk_level=level, retired_at__isnull=True)
                   .order_by("syllabus_order").values_list("pk", flat=True))
        plan = _themed_plan(level, ids)
        if plan is not None:  # D-49: mazos por tema
            chunks = [g.words for g in plan]
            for index, g in enumerate(plan, start=1):
                _save_deck(level, index, g.words, g.keys, g.part)
        else:  # D-43: tramos en el orden del sílabo mientras el nivel no tenga sus temas aprobados
            chunks = [ids[i:i + size] for i in range(0, len(ids), size)]
            for index, chunk in enumerate(chunks, start=1):
                _save_deck(level, index, chunk, [], None)
        extra = Deck.objects.filter(kind=Deck.Kind.SYSTEM, hsk_level=level, index__gt=len(chunks))
        DeckWord.objects.filter(deck__in=extra).delete()
        extra.filter(retired_at__isnull=True).update(retired_at=timezone.now())
        # Una palabra retirada sale de los mazos del sistema (R-CON-11 c).
        DeckWord.objects.filter(deck__kind=Deck.Kind.SYSTEM, deck__hsk_level=level, word__retired_at__isnull=False).delete()
        summary[level] = len(chunks)
    return summary


def system_decks(levels=None):
    qs = Deck.objects.filter(kind=Deck.Kind.SYSTEM, retired_at__isnull=True)
    if levels is not None:
        qs = qs.filter(hsk_level__in=list(levels))
    return qs.order_by("hsk_level", "index")


def deck_word_ids(deck: Deck) -> list[int]:
    return list(deck.entries.filter(word__retired_at__isnull=True).order_by("position").values_list("word_id", flat=True))


def system_word_ids(levels) -> list[int]:
    """Palabras de los mazos del sistema de esos niveles, en orden de nivel, mazo y posición (R-REP-08)."""
    return list(DeckWord.objects.filter(deck__kind=Deck.Kind.SYSTEM, deck__retired_at__isnull=True,
                                        deck__hsk_level__in=list(levels), word__retired_at__isnull=True)
                .order_by("deck__hsk_level", "deck__index", "position").values_list("word_id", flat=True))


def deck_of_words(word_ids) -> dict[int, Deck]:
    out = {}
    for e in DeckWord.objects.filter(deck__kind=Deck.Kind.SYSTEM, word_id__in=list(word_ids)).select_related("deck"):
        out[e.word_id] = e.deck
    return out
