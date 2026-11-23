"""Servicios de `privacy` (HU-E10-02, HU-E10-03)."""
from __future__ import annotations

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from analytics.services import emit, unlink_account
from hanzi_backend.exception_handlers import ApiError
from ops import params

from .models import PURPOSES, Consent, PolicyAcceptance, VoiceRecording
from .registry import deleters

PURPOSE_CODES = [p for p, _ in PURPOSES]


def current_policy() -> str:
    return params.value("data_policy_version")


def accepted_policy(account) -> str | None:
    return PolicyAcceptance.objects.filter(account=account).values_list("version", flat=True).first()


def policy_required(account) -> bool:
    return accepted_policy(account) != current_policy()


def accept_policy(account, version: str) -> None:
    if version != current_policy():
        raise ApiError("policy_version_mismatch")
    PolicyAcceptance.objects.create(account=account, version=version)
    emit("policy_accepted", account, policy_version=version)


def consents(account) -> dict[str, bool]:
    out = {p: False for p in PURPOSE_CODES}
    for c in Consent.objects.filter(account=account).order_by("created_at", "pk"):
        out[c.purpose] = c.granted
    return out


def set_consent(account, purpose: str, granted: bool, *, emit_event: bool = True) -> dict[str, bool]:
    if purpose not in PURPOSE_CODES:
        raise ApiError("not_found", 404)
    if purpose == "general" and not granted:
        raise ApiError("consent_required")  # retirarlo es eliminar la cuenta (HU-E10-03)
    if consents(account).get(purpose) == granted and Consent.objects.filter(account=account, purpose=purpose).exists():
        return consents(account)
    Consent.objects.create(account=account, purpose=purpose, granted=granted, policy_version=current_policy())
    if emit_event:
        emit("consent_changed", account, purpose=purpose, granted=granted)
    if purpose == "voice_recording" and not granted:
        schedule_voice_purge(account)
    return consents(account)


def on_account_created(sender, account, policy_version, consents: dict, **kwargs) -> None:
    PolicyAcceptance.objects.create(account=account, version=policy_version)
    emit("policy_accepted", account, policy_version=policy_version)
    for purpose in PURPOSE_CODES:
        Consent.objects.create(account=account, purpose=purpose, granted=bool(consents.get(purpose)),
                               policy_version=policy_version)


# ───────────────────────────── Voz (R-DAT-08): tareas de conservación con datos ficticios en V1

def schedule_voice_purge(account) -> None:
    """Revocar el consentimiento: todas sus grabaciones vencen en `voice_revocation_purge_days`."""
    limit = timezone.now() + timedelta(days=params.value("voice_revocation_purge_days"))
    VoiceRecording.objects.filter(account=account, deleted_at__isnull=True, expires_at__gt=limit).update(expires_at=limit)


def purge_voice_recordings(now=None) -> int:
    now = now or timezone.now()
    due = VoiceRecording.objects.filter(deleted_at__isnull=True, expires_at__lte=now)
    n = 0
    for rec in due:
        revoked = not consents(rec.account).get("voice_recording")
        # Aquí se borraría el objeto del contenedor privado (V4).
        rec.deleted_at = now
        rec.deletion_reason = "revocation" if revoked else "retention"
        rec.save(update_fields=["deleted_at", "deletion_reason"])
        emit("voice_recording_deleted", rec.account, reason=rec.deletion_reason)
        n += 1
    return n


# ───────────────────────────── Eliminación de cuenta (R-DAT-06)

@transaction.atomic
def delete_account(account, password: str) -> None:
    if not account.check_password(password or ""):
        raise ApiError("invalid_credentials", 401)
    days = (timezone.now() - account.date_joined).days
    emit("account_deleted", account, days_since_signup=days)
    for deleter in deleters().values():
        deleter(account)
    unlink_account(account)  # después de emitir: también este evento queda sin vínculo
    VoiceRecording.objects.filter(account=account).delete()
    Consent.objects.filter(account=account).delete()
    PolicyAcceptance.objects.filter(account=account).delete()
    account.delete()  # cascada: perfil, concesiones, consumos; auditoría y reportes quedan con vínculo nulo
