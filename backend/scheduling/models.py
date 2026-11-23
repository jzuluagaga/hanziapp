"""
Módulo `scheduling` (09-arquitectura.md §2): estados de repaso e historial.

No sabe de sesiones ni de mazos: recibe "esta cuenta respondió esto sobre este
ítem en esta habilidad" y devuelve el estado nuevo. El estado es genérico: una
fila por cuenta, habilidad y unidad (palabra o carácter), R-REP-01.
"""
from django.conf import settings
from django.db import models

SKILLS = [("recognition", "lectura"), ("listening", "escucha"), ("writing", "escritura")]
GRADES = [("pass", "Recordé"), ("fail", "No recordé")]


class ReviewState(models.Model):
    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review_states")
    skill = models.CharField(max_length=12, choices=SKILLS)
    unit_key = models.CharField(max_length=20, help_text="Id de la palabra (lectura y escucha) o el carácter (escritura).")
    word = models.ForeignKey("content.Word", null=True, blank=True, on_delete=models.CASCADE, related_name="+",
                             help_text="Palabra de la unidad; vacío en escritura.")
    stability = models.FloatField()
    difficulty = models.FloatField()
    fsrs_state = models.PositiveSmallIntegerField()
    due_at = models.DateTimeField()
    due_day = models.DateField(help_text="Día local en que vence (R-REP-04).")
    last_review_at = models.DateTimeField()
    last_review_day = models.DateField()
    reps = models.PositiveIntegerField(default=0)
    lapses = models.PositiveIntegerField(default=0)
    first_pass_day = models.DateField(null=True, blank=True, help_text="Primer «Recordé» (habilita escucha, R-REP-07).")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["account", "skill", "unit_key"], name="review_state_unique")]
        indexes = [models.Index(fields=["account", "skill", "due_day"])]

    def __str__(self):
        return f"{self.account_id} {self.skill}:{self.unit_key} → {self.due_day}"


class ReviewLog(models.Model):
    """Historial de cambios de estado. Solo crece (R-REP-13); base para optimizar FSRS."""

    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="review_logs")
    skill = models.CharField(max_length=12, choices=SKILLS)
    unit_key = models.CharField(max_length=20)
    grade = models.CharField(max_length=4, choices=GRADES)
    reviewed_at = models.DateTimeField()
    review_day = models.DateField()
    elapsed_days = models.IntegerField(help_text="Días reales desde el repaso anterior; 0 si es el primero.")
    scheduled_days = models.IntegerField(help_text="Intervalo que estaba programado; 0 si es el primero.")
    stability_after = models.FloatField()
    difficulty_after = models.FloatField()
    due_day_after = models.DateField()

    class Meta:
        ordering = ["reviewed_at"]
        indexes = [models.Index(fields=["account", "skill", "unit_key", "review_day"])]
