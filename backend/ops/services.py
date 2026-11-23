from typing import Any

from .models import AuditLog, Parameter

_MISSING = object()


def get_param(key: str, default: Any = _MISSING) -> Any:
    try:
        return Parameter.objects.get(key=key).value
    except Parameter.DoesNotExist:
        if default is _MISSING:
            raise KeyError(f"Falta el parámetro '{key}' en ops.Parameter")
        return default


def audit(actor, action: str, target, reason: str = "", **data) -> AuditLog:
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "pk", None) else None,
        action=action,
        target_type=target.__class__.__name__,
        target_id=str(target.pk),
        reason=reason,
        data=data,
    )
