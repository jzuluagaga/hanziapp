"""Pruebas de HU-E11-01 y del freno de costos (Q-29)."""
import uuid
from datetime import datetime, timedelta, timezone as tz
from decimal import Decimal

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

from analytics.models import Event
from decks.models import Deck
from entitlements import services
from entitlements.models import Grant, Plan, UsageRecord
from hanzi_backend.testing import at, client_for, set_param, setup_catalog, start, student

DAY1 = datetime(2026, 12, 1, 15, 0, tzinfo=tz.utc)


class E11Engine(TestCase):
    def setUp(self):
        self.user = student()

    def test_e11_01_default_free_grant(self):
        self.assertEqual(services.allowed_levels(self.user), [1, 2])
        self.assertEqual(services.limit(self.user, "decks.own.max"), 10)
        self.assertEqual(services.plan_name(self.user), "free")
        self.assertFalse(services.can(self.user, "study.level.3"))

    def test_e11_01_plan_is_data(self):
        free = Plan.objects.get(code="free", is_current=True)
        free.is_current = False
        free.save()
        Plan.objects.create(code="free", version=2, capabilities={**free.capabilities, "study.level.3": True})
        self.assertEqual(services.allowed_levels(self.user), [1, 2, 3])

    def test_e11_01_grants_union_and_expiry(self):
        now = timezone.now()
        Grant.objects.create(account=self.user, origin="promo", capabilities={"study.level.4": True, "decks.own.max": 50},
                             starts_at=now - timedelta(days=1), ends_at=now + timedelta(days=1))
        Grant.objects.create(account=self.user, origin="promo", capabilities={"study.level.5": True},
                             starts_at=now - timedelta(days=9), ends_at=now - timedelta(days=1))  # vencida
        Grant.objects.create(account=self.user, origin="promo", capabilities={"study.level.6": True},
                             starts_at=now + timedelta(days=1))  # futura
        self.assertEqual(services.allowed_levels(self.user), [1, 2, 4])
        self.assertEqual(services.limit(self.user, "decks.own.max"), 50)  # rige el mayor

    def test_e11_01_new_grant_immediate(self):
        self.assertFalse(services.can(self.user, "study.level.6"))
        owner = student("dueno@example.com")
        owner.user_permissions.add(Permission.objects.get(codename="owner"))
        owner = type(owner).objects.get(pk=owner.pk)
        services.grant_manual(self.user, owner, plan_code="pro", ends_at=timezone.now() + timedelta(days=90),
                              reason="Probador de la clase A")
        self.assertTrue(services.can(self.user, "study.level.6"))
        self.assertEqual(services.plan_name(self.user), "pro")
        with self.assertRaises(PermissionError):
            services.grant_manual(owner, self.user, plan_code="pro", reason="x")

    def test_e11_01_queue_respects_entitlements(self):
        words = setup_catalog(level1=3, level2=0, level3=3)
        c = client_for(self.user)
        hsk3 = Deck.objects.get(kind="system", hsk_level=3, index=1)
        with at(DAY1):
            r = start(c, "recognition", hsk3.pk).json()
            self.assertEqual(r["empty_reason"], "locked")
            s = start(c).json()["session"]
        self.assertEqual({card["unit"] for card in s["cards"]}, {str(w.pk) for w in words[1]})
        self.assertEqual(Event.objects.get(name="entitlement_denied").props, {"capability": "study.level.3", "surface": "session"})
        levels = c.get("/api/v1/levels").json()
        self.assertEqual([lv["locked"] for lv in levels], [False, False, True, True, True, True])

    def test_e11_01_quota_reserve_confirm_revert(self):
        set_param("costly_features_enabled", {"pronunciation.assess": True})
        set_param("monthly_budget_usd", {"pronunciation.assess": 100})
        Grant.objects.create(account=self.user, origin="manual", starts_at=timezone.now(),
                             capabilities={"pronunciation.assess": {"amount": 2, "period": "month"}}, reason="t")
        cid = uuid.uuid4()
        r1 = services.reserve(self.user, "pronunciation.assess", cid)
        r2 = services.reserve(self.user, "pronunciation.assess", cid)  # reintento
        self.assertEqual(r1.pk, r2.pk)
        self.assertEqual(services.quota_remaining(self.user, "pronunciation.assess"), 1)
        services.revert(r1)  # el servicio externo falló
        self.assertEqual(services.quota_remaining(self.user, "pronunciation.assess"), 2)
        services.confirm(services.reserve(self.user, "pronunciation.assess", uuid.uuid4()))
        services.confirm(services.reserve(self.user, "pronunciation.assess", uuid.uuid4()))
        with self.assertRaises(services.QuotaExceeded):
            services.reserve(self.user, "pronunciation.assess", uuid.uuid4())


class CostBrake(TestCase):
    def test_global_budget_pauses_feature(self):
        user = student()
        Grant.objects.create(account=user, origin="manual", starts_at=timezone.now(),
                             capabilities={"pronunciation.assess": {"amount": 100, "period": "month"}}, reason="t")
        with self.assertRaises(services.FeaturePaused):  # interruptor apagado por defecto
            services.reserve(user, "pronunciation.assess", uuid.uuid4())
        set_param("costly_features_enabled", {"pronunciation.assess": True})
        set_param("monthly_budget_usd", {"pronunciation.assess": 1})
        services.confirm(services.reserve(user, "pronunciation.assess", uuid.uuid4(), cost_usd=Decimal("1.00")))
        with self.assertRaises(services.FeaturePaused):  # tope de gasto alcanzado
            services.reserve(user, "pronunciation.assess", uuid.uuid4())
        self.assertTrue(Event.objects.filter(name="feature_paused_by_budget").exists())
        self.assertEqual(client_for(user).get("/api/v1/me").status_code, 200)  # lo demás sigue funcionando
        self.assertEqual(UsageRecord.objects.count(), 1)


class E00Usage(TestCase):
    def test_e00_01_usage_record_applies_once(self):
        user = student()
        set_param("costly_features_enabled", {"pronunciation.assess": True})
        set_param("monthly_budget_usd", {"pronunciation.assess": 10})
        Grant.objects.create(account=user, origin="manual", starts_at=timezone.now(),
                             capabilities={"pronunciation.assess": {"amount": 5, "period": "month"}}, reason="t")
        cid = uuid.uuid4()
        for _ in range(3):
            services.confirm(services.reserve(user, "pronunciation.assess", cid))
        self.assertEqual(UsageRecord.objects.filter(account=user).count(), 1)
        self.assertEqual(services.quota_remaining(user, "pronunciation.assess"), 4)
        self.assertEqual(Event.objects.filter(name="quota_consumed").count(), 1)
