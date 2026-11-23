"""
Módulo `analytics` (09-arquitectura.md §2): eventos y consultas del tablero.

Los eventos se escriben en la misma transacción que el hecho que miden (D-41) y
nunca llevan datos personales (R-DAT-07). La cuenta se identifica con un
seudónimo aleatorio que no es su id ni se deriva de su correo.
"""
import uuid

from django.conf import settings
from django.db import models


class AccountKey(models.Model):
    account = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="analytics_key")
    key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    def __str__(self):
        return str(self.key)


class Event(models.Model):
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=60, db_index=True)
    occurred_at = models.DateTimeField(db_index=True)
    account_key = models.UUIDField(null=True, blank=True, db_index=True)
    cohort = models.CharField(max_length=60, blank=True)
    ui_language = models.CharField(max_length=10, blank=True)
    study_language = models.CharField(max_length=10, blank=True)
    plan = models.CharField(max_length=20, blank=True)
    local_day = models.DateField(null=True, blank=True)
    client = models.CharField(max_length=20, blank=True)
    app_version = models.CharField(max_length=20, blank=True)
    props = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["occurred_at"]
        indexes = [models.Index(fields=["name", "account_key"])]
        permissions = [("view_dashboard", "Dueño: ver el tablero de retención")]

    def __str__(self):
        return f"{self.occurred_at:%Y-%m-%d %H:%M} {self.name}"
