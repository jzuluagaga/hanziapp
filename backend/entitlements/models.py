"""
Módulo `entitlements` (09-arquitectura.md §2 y §6): capacidades, planes,
concesiones, límites, cuotas y consumos. Reglas R-DER.

Capacidades (R-DER-02):
- acceso: `study.level.N` → true/false
- límite: `decks.own.max` → entero
- cuota: `pronunciation.assess` → {"amount": n, "period": "day" | "month" | "none"}
"""
from django.conf import settings
from django.db import models
from django.db.models import Q


class Plan(models.Model):
    """Conjunto de capacidades con sus valores, como dato y versionado (R-DER-03)."""

    code = models.CharField(max_length=20)
    version = models.PositiveIntegerField(default=1)
    is_current = models.BooleanField(default=True)
    capabilities = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code", "-version"]
        constraints = [
            models.UniqueConstraint(fields=["code", "version"], name="plan_unique_version"),
            models.UniqueConstraint(fields=["code"], condition=Q(is_current=True), name="plan_one_current"),
        ]

    def __str__(self):
        return f"{self.code} v{self.version}{' (vigente)' if self.is_current else ''}"


class Grant(models.Model):
    """Concesión: única vía por la que una cuenta obtiene derechos (R-DER-04)."""

    class Origin(models.TextChoices):
        DEFAULT = "default", "plan por defecto"
        PURCHASE = "purchase", "compra"
        PROMO = "promo", "promoción"
        MANUAL = "manual", "manual"

    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="grants")
    origin = models.CharField(max_length=10, choices=Origin.choices)
    plan_code = models.CharField(max_length=20, blank=True, help_text="Plan entero; rige su versión vigente.")
    capabilities = models.JSONField(default=dict, blank=True, help_text="Capacidades sueltas, además del plan.")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField(null=True, blank=True, help_text="Vacío = perpetua.")
    reason = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["account", "starts_at"]

    def __str__(self):
        return f"{self.account_id}: {self.plan_code or 'capacidades'} ({self.origin})"


class UsageRecord(models.Model):
    """Consumo de una cuota (R-DER-09). Reserva y confirmación comparten identificador."""

    class Status(models.TextChoices):
        RESERVED = "reserved", "reservado"
        CONFIRMED = "confirmed", "confirmado"
        REVERTED = "reverted", "revertido"

    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="usage_records")
    capability = models.CharField(max_length=60)
    client_id = models.UUIDField()
    units = models.PositiveIntegerField(default=1)
    cost_usd = models.DecimalField(max_digits=8, decimal_places=4, default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.RESERVED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["account", "client_id"], name="usage_unique_client_id")]
