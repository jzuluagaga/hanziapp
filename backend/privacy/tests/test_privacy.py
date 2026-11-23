"""Pruebas de HU-E10-02 y HU-E10-03."""
from datetime import timedelta

from django.apps import apps
from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.utils import timezone

from analytics.models import AccountKey, Event
from content.models import ContentReport
from hanzi_backend.testing import answer, client_for, set_param, setup_catalog, start, student
from ops.models import AuditLog
from ops.services import audit
from privacy.models import Consent, VoiceRecording
from privacy.services import purge_voice_recordings

User = get_user_model()


class E10Consents(TestCase):
    def setUp(self):
        setup_catalog(level1=3, level2=0, level3=0)
        self.user = student()
        self.c = client_for(self.user)

    def test_e10_02_new_policy_version_blocks_until_accepted(self):
        set_param("data_policy_version", "2027-01")
        r = self.c.get("/api/v1/today")
        self.assertEqual((r.status_code, r.json()["error"]), (428, "policy_required"))
        self.assertTrue(self.c.get("/api/v1/me").json()["policy"]["required"])
        self.assertEqual(self.c.post("/api/v1/me/policy/accept", {"version": "2026-11"}, format="json").json()["error"],
                         "policy_version_mismatch")
        r = self.c.post("/api/v1/me/policy/accept", {"version": "2027-01"}, format="json").json()
        self.assertEqual(r, {"current": "2027-01", "accepted": "2027-01", "required": False})
        self.assertEqual(self.c.get("/api/v1/today").status_code, 200)

    def test_e10_02_consents_independent_and_revocable(self):
        r = self.c.put("/api/v1/me/consents/reminder_email", {"granted": True}, format="json").json()
        self.assertEqual(r, {"general": True, "reminder_email": True, "voice_recording": False})
        r = self.c.put("/api/v1/me/consents/reminder_email", {"granted": False}, format="json").json()
        self.assertFalse(r["reminder_email"])
        history = list(Consent.objects.filter(account=self.user, purpose="reminder_email").values_list("granted", flat=True))
        self.assertEqual(history, [False, True, False])
        self.assertEqual(self.c.put("/api/v1/me/consents/general", {"granted": False}, format="json").json()["error"],
                         "consent_required")
        self.assertEqual(Event.objects.filter(name="consent_changed").count(), 2)

    def test_e10_02_voice_consent_exists_off_by_default(self):
        self.assertEqual(self.c.get("/api/v1/me").json()["consents"]["voice_recording"], False)
        self.assertTrue(Consent.objects.filter(account=self.user, purpose="voice_recording", granted=False).exists())

    def test_retention_jobs(self):
        now = timezone.now()
        set_param("voice_retention_days", 30)
        self.c.put("/api/v1/me/consents/voice_recording", {"granted": True}, format="json")
        old = VoiceRecording.objects.create(account=self.user, storage_key="ficticio/1", created_at=now - timedelta(days=31),
                                            expires_at=now - timedelta(days=1))
        fresh = VoiceRecording.objects.create(account=self.user, storage_key="ficticio/2", created_at=now,
                                              expires_at=now + timedelta(days=30))
        self.assertEqual(purge_voice_recordings(now), 1)
        old.refresh_from_db()
        self.assertEqual(old.deletion_reason, "retention")
        self.c.put("/api/v1/me/consents/voice_recording", {"granted": False}, format="json")  # revocar
        self.assertEqual(purge_voice_recordings(now + timedelta(days=6)), 0)
        self.assertEqual(purge_voice_recordings(now + timedelta(days=7, minutes=1)), 1)
        fresh.refresh_from_db()
        self.assertEqual(fresh.deletion_reason, "revocation")


class E10Deletion(TestCase):
    def setUp(self):
        self.words = setup_catalog(level1=3, level2=0, level3=0)
        self.user = student(cohort="clase-a")
        self.c = client_for(self.user)
        s = start(self.c).json()["session"]
        answer(self.c, s, 0)
        self.c.get("/api/v1/today")
        self.c.post(f"/api/v1/words/{self.words[1][0].pk}/reports", {"element": "meaning", "comment": "raro"}, format="json")
        audit(self.user, "test_action", self.words[1][0], "motivo")

    def delete(self, password="clave-segura-123"):
        return self.c.delete("/api/v1/me", {"password": password}, format="json")

    def test_account_deletion_leaves_no_trace(self):
        uid = self.user.pk
        self.assertEqual(self.delete().status_code, 204)
        leftovers = []
        for model in apps.get_models():
            for f in model._meta.get_fields():
                if getattr(f, "related_model", None) is User and f.concrete and not f.many_to_many:
                    if model.objects.filter(**{f.attname: uid}).exists():
                        leftovers.append(f"{model.__name__}.{f.name}")
        self.assertEqual(leftovers, [])
        self.assertFalse(User.objects.filter(pk=uid).exists())
        with connection.cursor() as cur:  # tampoco el correo en tablas de texto
            cur.execute("SELECT COUNT(*) FROM users_loginfailure WHERE email = %s", ["ana@example.com"])
            self.assertEqual(cur.fetchone()[0], 0)

    def test_e10_03_events_unlinked(self):
        key = AccountKey.objects.get(account=self.user).key
        n = Event.objects.filter(account_key=key).count()
        self.delete()
        self.assertEqual(Event.objects.filter(account_key=key).count(), 0)
        self.assertGreaterEqual(Event.objects.exclude(account_key__isnull=True).count(), n)
        self.assertTrue(Event.objects.filter(name="account_deleted").exists())

    def test_e10_03_wrong_password_keeps_account(self):
        r = self.delete("incorrecta")
        self.assertEqual(r.json()["error"], "invalid_credentials")
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_e10_03_audit_and_reports_unlinked(self):
        self.delete()
        self.assertTrue(AuditLog.objects.filter(action="test_action", actor__isnull=True).exists())
        self.assertTrue(ContentReport.objects.filter(account__isnull=True, comment="raro").exists())
