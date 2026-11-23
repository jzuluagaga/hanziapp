from django.conf import settings
from django.db import models


class Parameter(models.Model):
    """
    Parámetro ajustable (03-reglas-de-negocio.md §11). Vive en configuración, no
    en el código; cambiarlo queda en el registro de auditoría.
    """

    key = models.CharField(max_length=100, primary_key=True)
    value = models.JSONField(null=True, blank=True)
    rule = models.CharField(max_length=60, blank=True, help_text="Regla o documento que lo cita.")
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["key"]

    def __str__(self):
        return f"{self.key} = {self.value!r}"


class AuditLog(models.Model):
    """Acción del editor o del dueño sobre contenido, cuentas o concesiones (R-DAT-10)."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="audit_entries",
    )
    action = models.CharField(max_length=60)
    target_type = models.CharField(max_length=60)
    target_id = models.CharField(max_length=60)
    reason = models.TextField(blank=True)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["target_type", "target_id"])]

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.action} {self.target_type}:{self.target_id}"
