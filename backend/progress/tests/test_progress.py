"""Pruebas de HU-E09-01 y HU-E09-02."""
from datetime import date, datetime, timedelta, timezone as tz

from django.test import TestCase

from analytics.models import Event
from hanzi_backend.testing import answer, at, client_for, set_param, setup_catalog, start, student
from progress.models import ActiveDay, DayRecord
from progress.services import close_days, current_streak, progress_summary, streak
from scheduling.models import ReviewState
from users.services import local_day

BOGOTA_10AM = lambda d: datetime(2026, 12, d, 15, 0, tzinfo=tz.utc)  # noqa: E731


class E09Streak(TestCase):
    def setUp(self):
        setup_catalog(level1=12, level2=0, level3=0)
        with at(BOGOTA_10AM(1)):
            self.user = student()
        self.c = client_for(self.user)
        self.user.profile.new_limit_recognition = 3
        self.user.profile.save()

    def study(self, d):
        with at(BOGOTA_10AM(d)):
            s = start(self.c, force=True).json()
            if s.get("session"):
                answer(self.c, s["session"], 0)

    def test_e09_02_local_day_rollover(self):
        late = datetime(2026, 12, 3, 6, 30, tzinfo=tz.utc)  # 1:30 a. m. en Bogotá
        self.assertEqual(local_day(self.user, late), date(2026, 12, 2))
        self.assertEqual(local_day(self.user, late + timedelta(hours=3)), date(2026, 12, 3))  # 4:30 a. m.

    def test_e09_02_day_classification(self):
        self.study(1)  # activo; aprende 1 palabra con primer repaso a los 2 días
        with at(BOGOTA_10AM(6)):
            close_days(self.user)
        status = dict(DayRecord.objects.values_list("day", "status"))
        self.assertEqual(status[date(2026, 12, 1)], "active")
        self.assertEqual(status[date(2026, 12, 2)], "exempt")  # nada pendiente (las nuevas no obligan)
        self.assertEqual(status[date(2026, 12, 3)], "missed")  # la palabra vencía ese día
        self.assertEqual(status[date(2026, 12, 5)], "missed")
        self.assertEqual(DayRecord.objects.get(day=date(2026, 12, 3)).due_at_close, 1)

    def test_e09_02_streak_rules(self):
        for d, s in [(1, "active"), (2, "exempt"), (3, "active"), (4, "missed"), (5, "active"), (6, "exempt"), (7, "active")]:
            DayRecord.objects.create(account=self.user, day=date(2026, 12, d), status=s)
        ActiveDay.objects.create(account=self.user, day=date(2026, 12, 8))
        self.assertEqual(current_streak(self.user, date(2026, 12, 8)), 3)  # 5, 7 y hoy; el exento no suma ni rompe
        self.assertEqual(current_streak(self.user, date(2026, 12, 4)), 2)

    def test_e09_02_day_status_fixed_once(self):
        with at(BOGOTA_10AM(3)):
            close_days(self.user)
        before = dict(DayRecord.objects.values_list("day", "status"))
        ActiveDay.objects.create(account=self.user, day=date(2026, 12, 2))  # llega tarde algo que lo cambiaría
        with at(BOGOTA_10AM(4)):
            close_days(self.user)
        after = dict(DayRecord.objects.values_list("day", "status"))
        self.assertEqual(after[date(2026, 12, 2)], before[date(2026, 12, 2)])
        self.assertEqual(Event.objects.filter(name="day_closed", local_day=date(2026, 12, 2)).count(), 1)

    def test_e09_02_today_never_missed_before_close(self):
        self.study(1)
        with at(BOGOTA_10AM(3)):  # hoy vence la palabra y aún no estudia
            today = self.c.get("/api/v1/today").json()
        self.assertFalse(DayRecord.objects.filter(day=date(2026, 12, 3)).exists())
        self.assertEqual(today["streak"]["current"], 1)
        self.assertFalse(today["streak"]["today_active"])
        self.study(3)
        self.assertTrue(Event.objects.filter(name="streak_changed", props__change="extended").exists())


class E09Progress(TestCase):
    def setUp(self):
        self.words = setup_catalog(level1=4, level2=2, level3=0)
        self.user = student()

    def state(self, word, stability, skill="recognition", unit=None):
        now = datetime(2026, 12, 1, tzinfo=tz.utc)
        return ReviewState.objects.create(account=self.user, skill=skill, unit_key=unit or str(word.pk),
                                          word=word if skill != "writing" else None, stability=stability, difficulty=5,
                                          fsrs_state=2, due_at=now, due_day=now.date(), last_review_at=now,
                                          last_review_day=now.date())

    def test_e09_01_learned_threshold(self):
        self.state(self.words[1][0], 21)
        self.state(self.words[1][1], 20.9)
        self.state(None, 30, "writing", "爱")
        p = progress_summary(self.user)
        self.assertEqual((p["learned_words"], p["learned_chars"]), (1, 1))

    def test_e09_01_counts_each_word_once(self):
        from decks.models import Deck

        w = self.words[1][0]
        Deck.objects.create(kind="system", hsk_level=1, index=40).entries.create(word=w, position=0)
        self.state(w, 30)
        retired = self.words[1][1]
        self.state(retired, 30)
        retired.retired_at = datetime(2026, 12, 1, tzinfo=tz.utc)
        retired.save()
        self.assertEqual(progress_summary(self.user)["learned_words"], 1)

    def test_e09_01_level_progress(self):
        self.state(self.words[2][0], 40)
        lv2 = progress_summary(self.user)["levels"][1]
        self.assertEqual(lv2, {"level": 2, "total": 2, "published": 2, "learned": 1})
        r = client_for(self.user).get("/api/v1/progress").json()
        self.assertEqual(r["levels"][1]["learned"], 1)
        self.assertTrue(Event.objects.filter(name="progress_viewed").exists())

    def test_e09_01_learned_can_be_lost(self):
        from scheduling.services import apply_review

        st = self.state(self.words[1][0], 30)
        st.last_review_at = datetime(2026, 11, 1, tzinfo=tz.utc)
        st.save()
        self.assertEqual(progress_summary(self.user)["learned_words"], 1)
        apply_review(self.user, "recognition", st.unit_key, "fail", datetime(2026, 12, 1, 15, tzinfo=tz.utc))
        self.assertEqual(progress_summary(self.user)["learned_words"], 0)
