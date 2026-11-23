"""
Parámetros ajustables con su valor inicial (03-reglas-de-negocio.md §11).

`value(key)` devuelve la fila de `ops.Parameter` si existe y, si no, el valor
inicial de esta tabla. Así un parámetro nuevo funciona sin cargar datos, y
cambiarlo en el panel queda en el registro de auditoría (R-DAT-10).
"""
from typing import Any

from django.core.cache import cache

from .models import Parameter

DEFAULTS: dict[str, Any] = {
    # Cuentas
    "signup_mode": "open",                       # R-CTA-10
    "login_max_failures": 5,                     # R-CTA-08
    "login_window_min": 15,
    "login_lock_min": 15,
    # Mazos y sesiones
    "system_deck_size": {"1": 25, "2": 25, "3": 30, "4": 40, "5": 50, "6": 60},  # R-MAZ-02, D-43
    "session_max_cards": 50,                     # R-SES-02
    "session_ttl_days": 7,                       # R-SES-08
    "reinforce_gap": 3,                          # R-REP-05
    # Repaso
    "fsrs_target_retention": 0.90,               # R-REP-02
    "new_limit_recognition": {"default": 10, "min": 0, "max": 50},  # R-REP-06
    "new_limit_writing": {"default": 5, "min": 0, "max": 30},
    "new_limit_max": 50,                         # R-PRO-07
    "learned_stability_days": 21,                # R-REP-12
    "writing_max_stroke_misses": 2,              # R-ESC-03
    "auto_hint_after_misses": 3,                 # R-ESC-05
    # Día y hábito
    "day_rollover_hour": 4,                      # R-PRO-01
    # Mazos propios y planes
    "own_deck_max_words": 500,                   # R-MAZ-04
    # Datos personales
    "data_policy_version": "2026-11",            # R-DAT-01
    "voice_retention_days": 30,                  # R-DAT-08
    "voice_revocation_purge_days": 7,
    # Freno de costos (R-DER-10)
    "costly_features_enabled": {"pronunciation.assess": False},
    "monthly_budget_usd": {"pronunciation.assess": 0},
}

_CACHE_KEY = "ops.param.{}"


def value(key: str) -> Any:
    cached = cache.get(_CACHE_KEY.format(key), default=_MISSING)
    if cached is not _MISSING:
        return cached
    row = Parameter.objects.filter(pk=key).values_list("value", flat=True).first()
    if row is None and not Parameter.objects.filter(pk=key).exists():
        if key not in DEFAULTS:
            raise KeyError(f"Parámetro desconocido: {key}")
        result = DEFAULTS[key]
    else:
        result = row
    cache.set(_CACHE_KEY.format(key), result, timeout=30)
    return result


def per_level(key: str, level: int) -> Any:
    """Valor por nivel de un parámetro guardado como {"1": …, "2": …}."""
    mapping = value(key)
    return mapping.get(str(level), mapping.get(level))


def forget(key: str) -> None:
    cache.delete(_CACHE_KEY.format(key))


_MISSING = object()
