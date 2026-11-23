"""Construcción y lectura de mazos (HU-E08-01)."""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from content.models import Word
from ops import params

from .models import Deck, DeckWord


@transaction.atomic
def build_system_decks(levels=None) -> dict[int, int]:
    """Parte cada nivel en tramos de `system_deck_size` palabras vigentes, en el orden del sílabo.
    Repetible: conserva el identificador de cada mazo (nivel, índice) y retira los que sobran.
    Devuelve {nivel: número de mazos}."""
    levels = levels or range(1, 7)
    summary = {}
    for level in levels:
        size = int(params.per_level("system_deck_size", level))
        ids = list(Word.objects.filter(hsk_level=level, retired_at__isnull=True)
                   .order_by("syllabus_order").values_list("pk", flat=True))
        chunks = [ids[i:i + size] for i in range(0, len(ids), size)]
        for index, chunk in enumerate(chunks, start=1):
            deck, _ = Deck.objects.get_or_create(kind=Deck.Kind.SYSTEM, hsk_level=level, index=index)
            if deck.retired_at:
                deck.retired_at = None
                deck.save(update_fields=["retired_at"])
            current = list(deck.entries.order_by("position").values_list("word_id", flat=True))
            if current != chunk:
                deck.entries.all().delete()
                DeckWord.objects.bulk_create([DeckWord(deck=deck, word_id=w, position=i) for i, w in enumerate(chunk)])
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
