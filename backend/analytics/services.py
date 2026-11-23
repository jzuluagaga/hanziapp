"""
Emisión de eventos (HU-E00-02).

`emit` valida el esquema y escribe el evento en la transacción en curso: si el
hecho se revierte, el evento también. Nunca acepta campos no declarados.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .context import current_app_version, current_client
from .models import AccountKey, Event
from .schemas import SCHEMAS


class EventSchemaError(ValueError):
    pass


def account_key(account) -> uuid.UUID:
    key, _ = AccountKey.objects.get_or_create(account=account)
    return key.key


def _scalar(value):
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)) and all(isinstance(v, str) for v in value):
        return list(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    raise EventSchemaError(f"Valor no admitido en un evento: {type(value).__name__}")


def emit(name: str, account=None, *, occurred_at: datetime | None = None, local_day: date | None = None,
         client: str | None = None, **props) -> Event:
    schema = SCHEMAS.get(name)
    if schema is None:
        raise EventSchemaError(f"Evento fuera del catálogo: {name}")
    extra = set(props) - schema
    if extra:
        raise EventSchemaError(f"Campos no declarados en {name}: {sorted(extra)}")

    occurred_at = occurred_at or timezone.now()
    common = {"cohort": "", "ui_language": "", "study_language": "", "plan": "", "account_key": None}
    if account is not None and getattr(account, "pk", None):
        from entitlements.services import plan_name
        from users.services import local_day as account_local_day, profile_of

        profile = profile_of(account)
        common.update(
            account_key=account_key(account),
            cohort=account.cohort or "",
            ui_language=profile.ui_language_id,
            study_language=profile.study_language_id,
            plan=plan_name(account),
        )
        if local_day is None:
            local_day = account_local_day(account, occurred_at)

    with transaction.atomic():
        return Event.objects.create(
            name=name,
            occurred_at=occurred_at,
            local_day=local_day,
            client=client or current_client(),
            app_version=current_app_version() or settings.APP_VERSION,
            props={k: _scalar(v) for k, v in props.items()},
            **common,
        )


def unlink_account(account) -> None:
    """Al eliminar una cuenta, sus eventos pasan a un seudónimo aleatorio (R-DAT-06)."""
    key = AccountKey.objects.filter(account=account).first()
    if key is None:
        return
    Event.objects.filter(account_key=key.key).update(account_key=uuid.uuid4())
    key.delete()
