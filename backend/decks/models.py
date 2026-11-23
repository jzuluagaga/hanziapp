"""
Módulo `decks` (09-arquitectura.md §2): mazos del sistema y propios (R-MAZ).

Un mazo del sistema es un tramo de palabras consecutivas de un nivel, en el
orden del sílabo, con tamaño por nivel (R-MAZ-02, D-43). Su nombre es una clave
("HSK 1 · Parte 3"), así que no hay nada que traducir (R-IDI-09).
"""
from django.conf import settings
from django.db import models
from django.db.models import Q


class Deck(models.Model):
    class Kind(models.TextChoices):
        SYSTEM = "system", "del sistema"
        OWN = "own", "propio"

    kind = models.CharField(max_length=10, choices=Kind.choices)
    hsk_level = models.PositiveSmallIntegerField(null=True, blank=True)
    index = models.PositiveSmallIntegerField(null=True, blank=True, help_text="1, 2, 3… dentro del nivel.")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="own_decks")
    name = models.CharField(max_length=60, blank=True, help_text="Solo mazos propios (V2).")
    retired_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["kind", "hsk_level", "index"]
        constraints = [
            models.UniqueConstraint(fields=["hsk_level", "index"], condition=Q(kind="system"), name="system_deck_unique"),
            models.CheckConstraint(
                condition=(Q(kind="system") & Q(owner__isnull=True) & Q(hsk_level__isnull=False))
                | (Q(kind="own") & Q(owner__isnull=False)),
                name="deck_kind_consistent",
            ),
        ]

    def __str__(self):
        return f"HSK {self.hsk_level} · Parte {self.index}" if self.kind == "system" else self.name


class DeckWord(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="entries")
    word = models.ForeignKey("content.Word", on_delete=models.CASCADE, related_name="deck_entries")
    position = models.PositiveIntegerField()

    class Meta:
        ordering = ["deck", "position"]
        constraints = [models.UniqueConstraint(fields=["deck", "word"], name="deck_word_once")]
