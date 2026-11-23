"""Pruebas de HU-E00-02, HU-E14-01 y eventos del navegador."""
from datetime import date, datetime, timedelta, timezone as tz

from django.contrib.auth.models import Permission
from django.db import transaction
from django.test import TestCase

from analytics.metrics import accuracy_by_interval, retention_by_day, week4_retention
from analytics.models import AccountKey, Event
from analytics.schemas import FORBIDDEN_FIELDS, SCHEMAS
from analytics.services import EventSchemaError, emit
from hanzi_backend.testing import client_for, student


class E00Analytics(TestCase):
    def setUp(self):
        self.user = student(cohort="clase-a")

    def test_e00_02_events_carry_common_fields(self):
        e = client_for(self.user).post("/api/v1/events", {"name": "audio_played", "props": {"context": "card", "target": "word"}},
                                       format="json", HTTP_X_CLIENT="mobile_web", HTTP_X_APP_VERSION="1.2.3")
        self.assertEqual(e.status_code, 202)
        ev = Event.objects.get(name="audio_played")
        self.assertEqual((ev.cohort, ev.ui_language, ev.study_language, ev.plan, ev.client, ev.app_version),
                         ("clase-a", "es", "es", "free", "mobile_web", "1.2.3"))
        self.assertIsNotNone(ev.local_day)
        self.assertEqual(ev.account_key, AccountKey.objects.get(account=self.user).key)

    def test_event_schemas_have_no_pii(self):
        for name, fields in SCHEMAS.items():
            self.assertFalse(fields & FORBIDDEN_FIELDS, name)
        with self.assertRaises(EventSchemaError):
            emit("search_performed", self.user, query_kind="meaning", result_count=1, query="secreto")
        with self.assertRaises(EventSchemaError):
            emit("evento_inventado", self.user)

    def test_e00_02_event_rolls_back_with_fact(self):
        try:
            with transaction.atomic():
                emit("progress_viewed", self.user)
                raise RuntimeError("el hecho falla")
        except RuntimeError:
            pass
        self.assertFalse(Event.objects.filter(name="progress_viewed").exists())

    def test_e00_02_account_key_is_pseudonymous(self):
        emit("progress_viewed", self.user)
        key = str(AccountKey.objects.get(account=self.user).key)
        self.assertNotEqual(key, str(self.user.pk))
        self.assertNotIn(self.user.email.split("@")[0], key)
        other = student("beto@example.com")
        emit("progress_viewed", other)
        self.assertNotEqual(key, str(AccountKey.objects.get(account=other).key))

    def test_e00_02_client_events_whitelist(self):
        c = client_for(self.user)
        self.assertEqual(c.post("/api/v1/events", {"name": "session_completed", "props": {}}, format="json").json()["error"],
                         "event_not_allowed")
        self.assertEqual(c.post("/api/v1/events", {"name": "audio_played", "props": {"comment": "x"}}, format="json").status_code, 400)

    def test_e05_03_hint_event_schema(self):
        c = client_for(self.user)
        self.assertEqual(c.post("/api/v1/events", {"name": "writing_hint_shown", "props": {"auto": True}}, format="json").status_code, 202)
        self.assertEqual(Event.objects.get(name="writing_hint_shown").props, {"auto": True})
        self.assertEqual(c.post("/api/v1/events", {"name": "writing_hint_shown", "props": {"char": "我"}}, format="json").status_code, 400)

    def test_e07_03_stroke_event_accepted(self):
        r = client_for(self.user).post("/api/v1/events", {"name": "stroke_order_played"}, format="json")
        self.assertEqual(r.status_code, 202)
        self.assertTrue(Event.objects.filter(name="stroke_order_played").exists())


class E14Dashboard(TestCase):
    """Métricas calculadas solo con eventos, como en producción."""

    def _account(self, key_day: date, active_offsets, cohort="a"):
        import uuid

        key = uuid.uuid4()
        Event.objects.create(name="account_registered", occurred_at=datetime.now(tz.utc), account_key=key, cohort=cohort,
                             local_day=key_day, props={"has_cohort": True})
        for off in active_offsets:
            Event.objects.create(name="answer_recorded", occurred_at=datetime.now(tz.utc), account_key=key, cohort=cohort,
                                 local_day=key_day + timedelta(days=off), props={"counted": True, "skill": "recognition"})
        return key

    def test_e14_01_retention_by_day(self):
        d = date(2026, 12, 1)
        self._account(d, [0, 1, 7])
        self._account(d, [0, 28])
        self._account(d, [])  # nunca se activó: no cuenta
        r = retention_by_day()["a"]
        self.assertEqual((r[1]["num"], r[7]["num"], r[28]["num"], r[1]["den"]), (1, 1, 1, 2))

    def test_e14_01_week4_retention(self):
        d = date(2026, 12, 1)
        self._account(d, [0, 22])
        self._account(d, [0, 29])
        self._account(d, [0], cohort="b")
        w = week4_retention()
        self.assertEqual(w["a"]["pct"], 50.0)
        self.assertEqual(w["b"]["pct"], 0.0)
        self.assertEqual(w["(todas)"]["den"], 3)

    def test_e14_01_accuracy_by_interval(self):
        base = {"counted": True, "skill": "recognition", "is_reinforcement": False}
        rows = [(1, "pass"), (1, "fail"), (3, "pass"), (30, "pass"), (0, "pass")]
        for days, grade in rows:
            Event.objects.create(name="answer_recorded", occurred_at=datetime.now(tz.utc), props={**base, "scheduled_days": days, "grade": grade})
        Event.objects.create(name="answer_recorded", occurred_at=datetime.now(tz.utc),
                             props={**base, "scheduled_days": 1, "grade": "fail", "is_reinforcement": True})
        acc = accuracy_by_interval()["recognition"]
        self.assertEqual((acc["1"]["num"], acc["1"]["den"]), (1, 2))
        self.assertEqual((acc["2-6"]["pct"], acc["21+"]["pct"], acc["7-20"]["den"]), (100.0, 100.0, 0))

    def test_e14_01_dashboard_staff_only(self):
        user = student()
        self.client.force_login(user)
        self.assertNotEqual(self.client.get("/admin/analytics/").status_code, 200)
        user.is_staff = True
        user.save()
        self.assertEqual(self.client.get("/admin/analytics/").status_code, 403)
        user.user_permissions.add(Permission.objects.get(codename="view_dashboard"))
        self.assertEqual(self.client.get("/admin/analytics/").status_code, 200)
