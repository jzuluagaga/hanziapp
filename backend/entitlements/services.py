"""
Único punto de decisión "¿puede esta cuenta hacer esto?" (R-DER-01, HU-E11-01).

La cola de estudio, los mazos y cualquier función de pago llaman aquí. La
interfaz recibe el resultado para mostrar candados, pero no decide.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.utils import timezone

from analytics.services import emit
from ops import params

from .models import Grant, Plan, UsageRecord

LEVELS = range(1, 7)
QUOTA_PERIODS = {"day", "month", "none"}


class QuotaExceeded(Exception):
    pass


class FeaturePaused(Exception):
    pass


# ───────────────────────────── Derechos vigentes

def _merge(into: dict, caps: dict) -> None:
    """Unión de capacidades; ante dos valores de un límite o cuota rige el mayor (R-DER-04)."""
    for cap, val in caps.items():
        cur = into.get(cap)
        if cur is None:
            into[cap] = val
        elif isinstance(val, bool):
            into[cap] = bool(cur) or val
        elif isinstance(val, dict):
            better = not isinstance(cur, dict) or val.get("amount", 0) > cur.get("amount", 0)
            into[cap] = val if better else cur
        else:
            into[cap] = max(cur, val)


def active_grants(account, at: datetime | None = None):
    at = at or timezone.now()
    return Grant.objects.filter(account=account, starts_at__lte=at).filter(Q(ends_at__isnull=True) | Q(ends_at__gt=at))


def entitlements(account, at: datetime | None = None) -> dict:
    """Derechos vigentes de una cuenta. Sin caché: el efecto de una concesión es inmediato (R-DER-13)."""
    if account is None or not getattr(account, "pk", None):
        return {}
    grants = list(active_grants(account, at))
    plans = {p.code: p.capabilities for p in Plan.objects.filter(is_current=True, code__in={g.plan_code for g in grants})}
    caps: dict = {}
    for g in grants:
        if g.plan_code:
            _merge(caps, plans.get(g.plan_code, {}))
        _merge(caps, g.capabilities or {})
    return caps


def can(account, capability: str) -> bool:
    return bool(entitlements(account).get(capability, False))


def allowed_levels(account) -> list[int]:
    caps = entitlements(account)
    return [n for n in LEVELS if caps.get(f"study.level.{n}")]


def limit(account, capability: str) -> int:
    return int(entitlements(account).get(capability, 0) or 0)


def plan_name(account) -> str:
    """Nombre comercial de la concesión de mayor alcance, para eventos e interfaz."""
    codes = set(active_grants(account).exclude(plan_code="").values_list("plan_code", flat=True))
    return "pro" if "pro" in codes else ("free" if "free" in codes else (sorted(codes)[0] if codes else ""))


def unlocking_plan(level: int) -> str | None:
    """Plan más barato que desbloquea un nivel (R-DER-11)."""
    for code in ("free", "pro"):
        plan = Plan.objects.filter(code=code, is_current=True).first()
        if plan and plan.capabilities.get(f"study.level.{level}"):
            return code
    return None


def deny(account, capability: str, surface: str) -> None:
    emit("entitlement_denied", account, capability=capability, surface=surface)


# ───────────────────────────── Concesiones

def grant_default(account) -> Grant:
    """Concesión por defecto de toda cuenta registrada (R-DER-05)."""
    return Grant.objects.create(account=account, origin=Grant.Origin.DEFAULT, plan_code="free", starts_at=timezone.now())


def grant_manual(account, actor, *, plan_code: str = "", capabilities: dict | None = None,
                 ends_at: datetime | None = None, reason: str) -> Grant:
    """Concesión manual: solo el dueño, con motivo, en el registro de auditoría (R-DER-12)."""
    from ops.services import audit

    if not actor.has_perm("users.owner"):
        raise PermissionError("Solo el dueño concede acceso.")
    if not reason.strip():
        raise ValueError("Una concesión manual exige motivo.")
    g = Grant.objects.create(account=account, origin=Grant.Origin.MANUAL, plan_code=plan_code,
                             capabilities=capabilities or {}, starts_at=timezone.now(), ends_at=ends_at,
                             reason=reason, created_by=actor)
    audit(actor, "grant_created", g, reason, plan=plan_code, ends_at=ends_at.isoformat() if ends_at else None)
    return g


# ───────────────────────────── Cuotas (R-DER-09) y freno de costos (R-DER-10)

def _period_start(period: str, now: datetime) -> datetime | None:
    if period == "day":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "month":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return None


def feature_available(capability: str) -> bool:
    """Interruptor global y tope de gasto mensual del producto."""
    if not params.value("costly_features_enabled").get(capability, False):
        return False
    budget = Decimal(str(params.value("monthly_budget_usd").get(capability, 0)))
    start = _period_start("month", timezone.now())
    spent = UsageRecord.objects.filter(capability=capability, created_at__gte=start).exclude(
        status=UsageRecord.Status.REVERTED).aggregate(s=Sum("cost_usd"))["s"] or Decimal(0)
    return spent < budget


def quota_remaining(account, capability: str) -> int:
    quota = entitlements(account).get(capability)
    if not isinstance(quota, dict):
        return 0
    start = _period_start(quota.get("period", "none"), timezone.now())
    used = UsageRecord.objects.filter(account=account, capability=capability).exclude(status=UsageRecord.Status.REVERTED)
    if start:
        used = used.filter(created_at__gte=start)
    return int(quota.get("amount", 0)) - (used.aggregate(s=Sum("units"))["s"] or 0)


def reserve(account, capability: str, client_id: uuid.UUID, units: int = 1, cost_usd: Decimal = Decimal(0)) -> UsageRecord:
    """Reserva un consumo. Repetir el mismo identificador devuelve la misma reserva."""
    existing = UsageRecord.objects.filter(account=account, client_id=client_id).first()
    if existing:
        return existing
    if not feature_available(capability):
        emit("feature_paused_by_budget", account, capability=capability)
        raise FeaturePaused(capability)
    if quota_remaining(account, capability) < units:
        raise QuotaExceeded(capability)
    try:
        with transaction.atomic():
            return UsageRecord.objects.create(account=account, capability=capability, client_id=client_id,
                                              units=units, cost_usd=cost_usd)
    except IntegrityError:
        return UsageRecord.objects.get(account=account, client_id=client_id)


def confirm(record: UsageRecord) -> UsageRecord:
    if record.status == UsageRecord.Status.RESERVED:
        record.status = UsageRecord.Status.CONFIRMED
        record.save(update_fields=["status", "updated_at"])
        emit("quota_consumed", record.account, capability=record.capability, units=record.units, result="ok")
    return record


def revert(record: UsageRecord) -> UsageRecord:
    """Si el servicio externo falla, el consumo se revierte (R-DER-09)."""
    if record.status != UsageRecord.Status.REVERTED:
        record.status = UsageRecord.Status.REVERTED
        record.save(update_fields=["status", "updated_at"])
        emit("quota_consumed", record.account, capability=record.capability, units=record.units, result="reverted")
    return record
