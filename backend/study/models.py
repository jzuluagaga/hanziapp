"""
Módulo `study` (09-arquitectura.md §2): sesiones, colas, respuestas y
reanudación. Reglas R-SES y R-ESC.

La cola se calcula al iniciar y se guarda con su orden (R-SES-02); nunca se
recalcula (R-SES-06). Cada respuesta lleva un identificador de cliente único
por cuenta, garantizado por la base (R-SES-03).
"""
import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from scheduling.models import GRADES, SKILLS


class StudySession(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "en curso"
        COMPLETED = "completed", "completada"
        DISCARDED = "discarded", "descartada"
        EXPIRED = "expired", "caducada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="study_sessions")
    scope_type = models.CharField(max_length=10, choices=[("all_due", "todos los pendientes"), ("deck", "mazo")])
    deck = models.ForeignKey("decks.Deck", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    scope_key = models.CharField(max_length=30, help_text="'all_due' o 'deck:<id>' (R-SES-05).")
    skill = models.CharField(max_length=12, choices=SKILLS)
    kind = models.CharField(max_length=10, choices=[("scheduled", "programada"), ("free", "repaso libre")], default="scheduled")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    chain = models.BooleanField(default=False, help_text="Forma parte de «Estudiar hoy» (R-SES-12).")
    position = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-last_activity_at"]
        constraints = [
            models.UniqueConstraint(fields=["account", "skill", "scope_key"], condition=Q(status="active"),
                                    name="one_active_session_per_scope_skill"),
        ]


class SessionCard(models.Model):
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name="cards")
    position = models.PositiveIntegerField()
    unit_kind = models.CharField(max_length=10, choices=[("word", "palabra"), ("character", "carácter")])
    unit_key = models.CharField(max_length=20)
    word = models.ForeignKey("content.Word", on_delete=models.PROTECT, related_name="+", help_text="Palabra de contexto.")
    is_new = models.BooleanField(default=False)
    is_reinforcement = models.BooleanField(default=False)
    result = models.CharField(max_length=8, null=True, blank=True,
                              choices=[("pass", "Recordé"), ("fail", "No recordé"), ("skipped", "ya repasada")])
    answered_at = models.DateTimeField(null=True, blank=True)
    choices = models.JSONField(null=True, blank=True, help_text="Escucha: ids de las cuatro opciones.")

    class Meta:
        ordering = ["session", "position"]
        indexes = [models.Index(fields=["session", "position"])]


class Answer(models.Model):
    """Historial de respuestas: solo crece (R-REP-13)."""

    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="answers")
    client_id = models.UUIDField()
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name="answers")
    card = models.ForeignKey(SessionCard, on_delete=models.CASCADE, related_name="answers")
    skill = models.CharField(max_length=12, choices=SKILLS)
    unit_key = models.CharField(max_length=20)
    grade = models.CharField(max_length=4, choices=GRADES)
    counted = models.BooleanField(help_text="Cambió el estado de repaso (R-REP-05, R-ESC-02).")
    introduced_new = models.BooleanField(default=False, help_text="Consumió el límite de nuevas (R-REP-06).")
    is_reinforcement = models.BooleanField(default=False)
    answered_at = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)
    local_day = models.DateField()
    response_ms = models.PositiveIntegerField(null=True, blank=True)
    mode = models.CharField(max_length=8, blank=True, help_text="Escritura: guided o recall.")
    stroke_misses = models.PositiveSmallIntegerField(null=True, blank=True)
    hint_used = models.BooleanField(null=True, blank=True)
    threshold = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Umbral vigente (R-ESC-04).")
    replays = models.PositiveSmallIntegerField(null=True, blank=True)
    choice = models.CharField(max_length=20, blank=True)
    voided = models.BooleanField(default=False, help_text="Anulada por «deshacer» (V2); nunca se borra.")
    response = models.JSONField(default=dict, help_text="Lo que se devolvió, para repetirlo ante un reenvío.")

    class Meta:
        ordering = ["received_at"]
        constraints = [models.UniqueConstraint(fields=["account", "client_id"], name="answer_unique_client_id")]
        indexes = [models.Index(fields=["account", "skill", "local_day"])]
