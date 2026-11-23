"""
Módulo `progress` (09-arquitectura.md §2): estado del día, racha y avance (R-PRO).

`progress` escucha a `study` (señal `answer_recorded`) y no al revés. El estado
de un día se fija una vez al cerrarse y no se recalcula (R-PRO-09).
"""
from django.conf import settings
from django.db import models


class ActiveDay(models.Model):
    """Día con al menos una respuesta que cambió un estado de repaso (R-PRO-03)."""

    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="active_days")
    day = models.DateField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["account", "day"], name="active_day_unique")]


class DayRecord(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "activo"
        EXEMPT = "exempt", "exento"
        MISSED = "missed", "fallado"

    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="day_records")
    day = models.DateField()
    status = models.CharField(max_length=6, choices=Status.choices)
    due_at_close = models.PositiveIntegerField(default=0)
    closed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-day"]
        constraints = [models.UniqueConstraint(fields=["account", "day"], name="day_record_unique")]


class StreakRecord(models.Model):
    account = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="streak_record")
    max_streak = models.PositiveIntegerField(default=0)
    last_closed_day = models.DateField(null=True, blank=True)
