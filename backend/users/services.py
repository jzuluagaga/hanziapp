"""
Servicios de `accounts`: registro, acceso, perfil y día local del estudiante.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from analytics.services import emit
from hanzi_backend.exception_handlers import ApiError
from languages.models import Language
from ops import params

from .models import LoginFailure, Profile
from .signals import account_created

User = get_user_model()

DEFAULT_TIMEZONE = "America/Bogota"


# ───────────────────────────── Perfil y día local

def _default_language() -> Language:
    return (Language.objects.filter(is_study_active=True, is_ui_active=True).order_by("code").first()
            or Language.objects.get(code="es"))


def profile_of(account) -> Profile:
    try:
        return account.profile
    except Profile.DoesNotExist:
        lang = _default_language()
        profile, _ = Profile.objects.get_or_create(
            account=account,
            defaults={
                "ui_language": lang, "study_language": lang,
                "new_limit_recognition": params.value("new_limit_recognition")["default"],
                "new_limit_writing": params.value("new_limit_writing")["default"],
            },
        )
        account.profile = profile
        return profile


def valid_timezone(name: str) -> bool:
    try:
        ZoneInfo(name)
        return True
    except (ZoneInfoNotFoundError, ValueError):
        return False


def timezone_at(account, at: datetime) -> ZoneInfo:
    p = profile_of(account)
    if p.previous_timezone and p.timezone_changed_at and at < p.timezone_changed_at:
        return ZoneInfo(p.previous_timezone)
    return ZoneInfo(p.timezone)


def local_day(account, at: datetime | None = None) -> date:
    """Día del estudiante: su zona horaria con corte a `day_rollover_hour` (R-PRO-01)."""
    at = at or timezone.now()
    rollover = params.value("day_rollover_hour")
    return (at.astimezone(timezone_at(account, at)) - timedelta(hours=rollover)).date()


def day_start(account, day: date) -> datetime:
    """Instante UTC en que empieza un día local."""
    rollover = params.value("day_rollover_hour")
    # Se resuelve con la zona vigente al mediodía de ese día, para cubrir el cambio de zona.
    probe = datetime.combine(day, time(12), tzinfo=ZoneInfo("UTC"))
    tz = timezone_at(account, probe)
    return datetime.combine(day, time(rollover), tzinfo=tz).astimezone(ZoneInfo("UTC"))


def change_timezone(profile: Profile, new_tz: str) -> None:
    """R-PRO-02: la zona nueva rige desde el inicio del día siguiente, con la zona anterior."""
    if new_tz == profile.timezone:
        return
    account = profile.account
    tomorrow = local_day(account) + timedelta(days=1)
    changes_at = day_start(account, tomorrow)
    profile.previous_timezone = profile.timezone
    profile.timezone = new_tz
    profile.timezone_changed_at = changes_at


# ───────────────────────────── Registro (HU-E02-01)

@transaction.atomic
def register(*, name: str, email: str, password: str, policy_version: str, is_adult: bool,
             reminder_consent: bool = False, cohort: str = "", tz: str = "") -> User:
    if params.value("signup_mode") != "open":
        raise ApiError("signup_closed", 403)
    if policy_version != params.value("data_policy_version"):
        raise ApiError("policy_not_accepted")
    if not is_adult:
        raise ApiError("adult_required")
    email = User.objects.normalize_email(email).strip().lower()
    if User.objects.filter(email__iexact=email).exists():
        raise ApiError("email_taken")
    try:
        validate_password(password, user=User(email=email, first_name=name))
    except ValidationError as e:
        raise ApiError("weak_password", codes=[err.code for err in e.error_list])
    try:
        user = User.objects.create_user(email=email, password=password, first_name=name[:150],
                                        cohort=(cohort or "")[:60])
    except IntegrityError:
        raise ApiError("email_taken")
    profile = profile_of(user)
    profile.name = name.strip()[:80]
    if tz and valid_timezone(tz):
        profile.timezone = tz
    profile.save()

    account_created.send(sender=User, account=user, policy_version=policy_version,
                         consents={"general": True, "reminder_email": bool(reminder_consent), "voice_recording": False})
    emit("account_registered", user, has_cohort=bool(user.cohort))
    return user


# ───────────────────────────── Acceso (HU-E02-02)

def _lock_state(email: str) -> bool:
    window = timezone.now() - timedelta(minutes=params.value("login_window_min"))
    failures = list(LoginFailure.objects.filter(email=email, at__gte=window).order_by("-at").values_list("at", flat=True))
    if len(failures) < params.value("login_max_failures"):
        return False
    return failures[0] + timedelta(minutes=params.value("login_lock_min")) > timezone.now()


def login(email: str, password: str) -> User:
    """Devuelve la cuenta o lanza la clave de error. Nunca revela si el correo existe (R-CTA-08)."""
    email = (email or "").strip().lower()
    if _lock_state(email):
        emit("login_failed", reason="locked")
        raise ApiError("account_locked", 423)
    user = User.objects.filter(email__iexact=email).first()
    if user is None or not user.check_password(password or ""):
        LoginFailure.objects.create(email=email)
        locked = _lock_state(email)
        emit("login_failed", reason="locked" if locked else "bad_credentials")
        raise ApiError("account_locked" if locked else "invalid_credentials", 423 if locked else 401)
    if user.suspended_at or not user.is_active:
        emit("login_failed", reason="suspended")
        raise ApiError("account_suspended", 403)
    LoginFailure.objects.filter(email=email).delete()
    user.last_login = timezone.now()
    user.save(update_fields=["last_login"])
    emit("login_succeeded", user, method="password")
    return user


def suspend(account, actor, reason: str) -> None:
    from ops.services import audit

    account.suspended_at = timezone.now()
    account.suspension_reason = reason
    account.save(update_fields=["suspended_at", "suspension_reason"])
    audit(actor, "account_suspended", account, reason)


def reactivate(account, actor, reason: str) -> None:
    from ops.services import audit

    account.suspended_at = None
    account.save(update_fields=["suspended_at"])
    audit(actor, "account_reactivated", account, reason)


def delete_account_data(account) -> None:
    """Lo que `accounts` guarda aparte de la cuenta (registro de borrado de `privacy`)."""
    LoginFailure.objects.filter(email__iexact=account.email).delete()
