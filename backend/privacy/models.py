"""
Módulo `privacy` (09-arquitectura.md §2): política, consentimientos, eliminación
y grabaciones de voz. Reglas R-DAT.
"""
from django.conf import settings
from django.db import models

PURPOSES = [("general", "general"), ("reminder_email", "recordatorios por correo"), ("voice_recording", "grabación de voz")]


class PolicyAcceptance(models.Model):
    """Cada aceptación guarda versión y fecha (R-DAT-01)."""

    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="policy_acceptances")
    version = models.CharField(max_length=20)
    accepted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-accepted_at"]


class Consent(models.Model):
    """Historial de consentimientos por finalidad (R-DAT-02). El vigente es el último de cada finalidad."""

    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="consents")
    purpose = models.CharField(max_length=20, choices=PURPOSES)
    granted = models.BooleanField()
    policy_version = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "pk"]


class VoiceRecording(models.Model):
    """Preparación de voz (D-37, R-DAT-08): sin interfaz hasta V4. Contenedor privado, sin dirección pública."""

    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="voice_recordings")
    storage_key = models.CharField(max_length=300)
    created_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    deleted_at = models.DateTimeField(null=True, blank=True)
    deletion_reason = models.CharField(max_length=12, blank=True)
