"""Pruebas de E02 y E10-01 (Docs/historias/)."""
from datetime import datetime, timedelta, timezone as tz

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.test import TestCase, override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from analytics.models import Event
from entitlements.models import Grant
from hanzi_backend.testing import at, client_for, make_level, set_param, student
from languages.models import Language
from ops import params
from privacy.models import Consent, PolicyAcceptance
from scheduling.models import ReviewState
from users.services import local_day

User = get_user_model()
DAY1 = datetime(2026, 12, 1, 15, 0, tzinfo=tz.utc)


def register(client, **over):
    body = {"name": "Ana Pérez", "email": "ana@example.com", "password": "clave-segura-123",
            "policy_version": params.value("data_policy_version"), "is_adult": True, "reminder_consent": False}
    body.update(over)
    return client.post("/api/v1/auth/register", body, format="json")


class E02Register(TestCase):
    def test_e02_01_requires_policy_and_adult(self):
        c = client_for()
        self.assertEqual(register(c, policy_version="").json()["error"], "policy_not_accepted")
        self.assertEqual(register(c, is_adult=False).json()["error"], "adult_required")
        self.assertFalse(User.objects.exists())

    def test_e02_01_creates_account_profile_grant_consents(self):
        r = register(client_for(), timezone="America/Lima")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(set(r.json()), {"access", "refresh"})
        u = User.objects.get()
        self.assertEqual((u.profile.name, u.profile.ui_language_id, u.profile.study_language_id, u.profile.timezone),
                         ("Ana Pérez", "es", "es", "America/Lima"))
        self.assertEqual(u.profile.new_limit_recognition, 10)
        self.assertEqual(Grant.objects.get(account=u).plan_code, "free")
        self.assertEqual(PolicyAcceptance.objects.get(account=u).version, params.value("data_policy_version"))
        current = {c.purpose: c.granted for c in Consent.objects.filter(account=u)}
        self.assertEqual(current, {"general": True, "reminder_email": False, "voice_recording": False})
        self.assertEqual(set(Event.objects.values_list("name", flat=True)), {"account_registered", "policy_accepted"})

    def test_e02_01_cohort_saved_and_in_events(self):
        register(client_for(), cohort="confucio-2026a")
        u = User.objects.get()
        self.assertEqual(u.cohort, "confucio-2026a")
        self.assertTrue(Event.objects.filter(name="account_registered", cohort="confucio-2026a", props__has_cohort=True).exists())

    def test_e02_01_duplicate_email_rejected(self):
        register(client_for())
        r = register(client_for(), email="ANA@example.com")
        self.assertEqual(r.json()["error"], "email_taken")
        self.assertEqual(User.objects.count(), 1)

    def test_e02_01_weak_password_rejected(self):
        r = register(client_for(), password="123")
        self.assertEqual(r.json()["error"], "weak_password")
        self.assertFalse(User.objects.exists())


class E02Access(TestCase):
    def setUp(self):
        self.user = student()

    def login(self, password="clave-segura-123", email="ana@example.com"):
        return client_for().post("/api/v1/auth/login", {"email": email, "password": password}, format="json")

    def test_e02_02_login_returns_tokens(self):
        r = self.login()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(set(r.json()), {"access", "refresh"})
        c = client_for()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['access']}")
        self.assertEqual(c.get("/api/v1/me").json()["account"]["email"], "ana@example.com")
        self.assertTrue(Event.objects.filter(name="login_succeeded", props__method="password").exists())

    def test_login_lockout(self):
        for _ in range(4):
            self.assertEqual(self.login("mala").json()["error"], "invalid_credentials")
        self.assertEqual(self.login("mala").status_code, 423)
        self.assertEqual(self.login().json()["error"], "account_locked")  # también con la clave correcta
        # Un correo inexistente recibe exactamente los mismos mensajes.
        msgs = [self.login("x", "nadie@example.com").json()["error"] for _ in range(6)]
        self.assertEqual(msgs, ["invalid_credentials"] * 4 + ["account_locked"] * 2)
        with at(datetime.now(tz.utc) + timedelta(minutes=16)):
            self.assertEqual(self.login().status_code, 200)
        self.assertFalse(Event.objects.filter(name="login_failed", account_key__isnull=False).exists())

    def test_e02_02_suspended_account_cannot_login(self):
        self.user.suspended_at = datetime.now(tz.utc)
        self.user.save()
        r = self.login()
        self.assertEqual((r.status_code, r.json()["error"]), (403, "account_suspended"))
        self.assertTrue(Grant.objects.filter(account=self.user).exists())

    def test_e02_02_password_reset_flow(self):
        c = client_for()
        self.assertEqual(c.post("/api/v1/auth/password-reset", {"email": "nadie@example.com"}, format="json").json(), {"ok": True})
        self.assertEqual(c.post("/api/v1/auth/password-reset", {"email": "ana@example.com"}, format="json").json(), {"ok": True})
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = PasswordResetTokenGenerator().make_token(self.user)
        body = {"uid": uid, "token": token, "new_password": "otra-clave-segura-9"}
        self.assertEqual(c.post("/api/v1/auth/password-reset/confirm", body, format="json").status_code, 200)
        self.assertEqual(c.post("/api/v1/auth/password-reset/confirm", body, format="json").json()["error"], "reset_link_invalid")
        self.assertEqual(self.login("otra-clave-segura-9").status_code, 200)
        self.assertTrue(Event.objects.filter(name="password_reset_completed").exists())

    @override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "rl"}})
    def test_rate_limit_auth_endpoints(self):
        from rest_framework.settings import api_settings
        from rest_framework.throttling import SimpleRateThrottle

        old = SimpleRateThrottle.THROTTLE_RATES
        SimpleRateThrottle.THROTTLE_RATES = {**api_settings.DEFAULT_THROTTLE_RATES, "auth": "3/min"}
        try:
            codes = [self.login("x").status_code for _ in range(4)]
            reset = client_for().post("/api/v1/auth/password-reset", {"email": "a@b.co"}, format="json")
        finally:
            SimpleRateThrottle.THROTTLE_RATES = old
        self.assertEqual(codes[-1], 429)
        self.assertEqual(reset.json()["error"], "rate_limited")

    def test_password_hasher(self):
        self.assertTrue(self.user.password.startswith(("pbkdf2_sha256$", "argon2")))


class E10Profile(TestCase):
    def setUp(self):
        self.user = student()
        self.c = client_for(self.user)

    def patch(self, **body):
        return self.c.patch("/api/v1/me/profile", body, format="json")

    def test_e10_01_update_profile_within_ranges(self):
        r = self.patch(name="Ana María", new_limit_recognition=25, new_limit_writing=0, theme="dark")
        self.assertEqual(r.status_code, 200)
        self.assertEqual((r.json()["name"], r.json()["new_limit_recognition"], r.json()["theme"]), ("Ana María", 25, "dark"))
        bad = self.patch(new_limit_recognition=51).json()
        self.assertEqual(bad["error"], "limit_out_of_range")
        self.assertEqual(bad["detail"]["max"], 50)
        self.assertEqual(self.patch(new_limit_writing=31).json()["error"], "limit_out_of_range")

    def test_e10_01_inactive_language_rejected(self):
        self.assertEqual(self.patch(study_language="en").json()["error"], "language_inactive")
        self.assertEqual(self.patch(ui_language="en").json()["error"], "language_inactive")
        Language.objects.filter(code="en").update(is_study_active=True)
        self.assertEqual(self.patch(study_language="en").status_code, 200)

    def test_e10_01_study_language_change_keeps_states(self):
        from decks.services import build_system_decks
        from hanzi_backend.testing import publish_word, start

        words = make_level(1, 3)
        publish_word(words[0], "en")
        build_system_decks()
        ReviewState.objects.create(account=self.user, skill="recognition", unit_key=str(words[1].pk), word=words[1],
                                   stability=3, difficulty=5, fsrs_state=2, due_at=DAY1, due_day=DAY1.date(),
                                   last_review_at=DAY1 - timedelta(days=3), last_review_day=(DAY1 - timedelta(days=3)).date())
        Language.objects.filter(code="en").update(is_study_active=True)
        self.patch(study_language="en")
        with at(DAY1):
            s = start(self.c).json()["session"]
        self.assertEqual([c["unit"] for c in s["cards"]], [str(words[0].pk)])  # solo lo publicado en inglés
        self.assertEqual(ReviewState.objects.filter(account=self.user).count(), 1)

    def test_e10_01_timezone_change_applies_next_day(self):
        with at(DAY1):  # 10:00 en Bogotá
            self.patch(timezone="Asia/Shanghai")
            self.assertEqual(local_day(self.user), DAY1.date())  # hoy sigue con la zona anterior
        self.user.refresh_from_db()
        # Mañana a las 05:00 de Bogotá rige ya Shanghái (18:00 allí).
        tomorrow = datetime(2026, 12, 2, 10, 0, tzinfo=tz.utc)
        self.assertEqual(local_day(self.user, tomorrow), datetime(2026, 12, 2).date())
        self.assertEqual(local_day(self.user, DAY1 - timedelta(days=5)), (DAY1 - timedelta(days=5)).date())

    def test_e10_01_profile_event_has_field_names_only(self):
        self.patch(name="Secreto", new_limit_recognition=20)
        e = Event.objects.get(name="profile_updated")
        self.assertEqual(e.props, {"fields": ["new_limit_recognition", "name"]})
        self.assertNotIn("Secreto", str(e.props))
