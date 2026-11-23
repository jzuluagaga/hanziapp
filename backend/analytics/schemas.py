"""
Catálogo cerrado de eventos (07-eventos-y-metricas.md §2 y §3).

Cada evento declara sus campos propios. Emitir un campo no declarado es un error
(Q-14): así ningún evento puede llevar nombre, correo, texto libre ni audio.
"""

COMMON_FIELDS = (
    "event_id", "occurred_at", "account_key", "cohort", "ui_language", "study_language",
    "plan", "local_day", "client", "app_version",
)

SCHEMAS: dict[str, frozenset[str]] = {k: frozenset(v) for k, v in {
    # Cuenta y datos
    "account_registered": ["has_cohort"],
    "login_succeeded": ["method"],
    "login_failed": ["reason"],
    "password_reset_completed": [],
    "policy_accepted": ["policy_version"],
    "consent_changed": ["purpose", "granted"],
    "profile_updated": ["fields"],
    "account_deleted": ["days_since_signup"],
    # Estudio
    "home_viewed": ["due_recognition", "due_listening", "due_writing", "new_available"],
    "session_started": ["session_id", "skill", "scope", "kind", "queue_size", "due_count", "new_count"],
    "session_empty": ["skill", "reason"],
    "answer_recorded": [
        "session_id", "skill", "session_kind", "item_kind", "hsk_level", "grade", "counted",
        "is_first_ever", "is_reinforcement", "days_since_last", "scheduled_days", "response_ms",
        "mode", "stroke_misses", "hint_used", "threshold", "replays",
    ],
    "new_limit_reached": ["skill", "limit"],
    "session_completed": ["session_id", "skill", "kind", "answered", "passed", "failed", "duration_s"],
    "session_resumed": [
        "session_id", "skill", "position", "skipped_already_reviewed", "hours_since_last_answer", "same_client",
    ],
    "session_discarded": ["session_id", "skill", "position", "queue_size"],
    "session_expired": ["session_id", "skill", "position", "queue_size"],
    "answer_delivery_delayed": ["attempts", "delay_s"],
    "answer_rejected_stale": ["session_id"],
    "audio_played": ["context", "target", "auto"],
    "audio_failed": ["context", "target"],
    "writing_hint_shown": ["auto"],
    "writing_char_abandoned": ["strokes_done", "mode"],
    # Explorar y organizar
    "search_performed": ["query_kind", "result_count"],
    "word_viewed": ["hsk_level", "editorial", "from"],
    "stroke_order_played": [],
    "content_report_submitted": ["element", "hsk_level"],
    "deck_viewed": ["deck_kind", "hsk_level"],
    # Progreso y derechos
    "progress_viewed": [],
    "day_closed": ["status", "due_at_close"],
    "streak_changed": ["length", "change"],
    "entitlement_denied": ["capability", "surface"],
    # Operación
    "content_published": ["layer", "language", "origin", "hsk_level", "replaces_published"],
    "content_unpublished": ["layer", "language", "hsk_level"],
    "content_report_resolved": ["outcome", "days_open"],
    # Reservados (§3): definidos, nada los emite en V1
    "guest_started": ["answers_before_signup"],
    "guest_converted": ["answers_before_signup"],
    "answer_undone": ["session_id", "skill"],
    "paywall_viewed": ["capability", "surface"],
    "purchase_completed": ["product", "duration_days"],
    "grant_expired": ["product", "duration_days"],
    "reminder_sent": [],
    "quota_consumed": ["capability", "units", "result"],
    "feature_paused_by_budget": ["capability"],
    "voice_recording_stored": ["duration_ms"],
    "voice_recording_deleted": ["reason"],
}.items()}

# Eventos que nacen en el navegador y llegan por POST /events (Docs/10-api.md §7).
CLIENT_EVENTS = frozenset({
    "audio_played", "audio_failed", "stroke_order_played", "writing_hint_shown", "writing_char_abandoned",
})

# Nombres de campo que nunca pueden aparecer en un esquema (R-DAT-07).
FORBIDDEN_FIELDS = frozenset({
    "name", "first_name", "last_name", "email", "password", "query", "q", "text", "comment",
    "ip", "ip_address", "user_agent", "audio", "transcript",
})
