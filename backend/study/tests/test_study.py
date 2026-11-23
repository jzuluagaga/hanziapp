"""Pruebas de E03, E04, E05 y E06 (Docs/historias/)."""
import uuid
from datetime import datetime, timedelta, timezone as tz

from django.db import IntegrityError, transaction
from django.test import TestCase

from analytics.models import Event
from content.models import Character, Word
from decks.models import Deck
from hanzi_backend.testing import answer, at, client_for, make_level, make_word, set_param, setup_catalog, start, student
from scheduling.models import ReviewState
from study.models import Answer, StudySession
from study.services import expire_sessions

DAY1 = datetime(2026, 12, 1, 15, 0, tzinfo=tz.utc)  # 10:00 en Bogotá


class Base(TestCase):
    def setUp(self):
        self.words = setup_catalog()
        self.user = student()
        self.c = client_for(self.user)

    def started(self, skill="recognition", deck_id=None, **kw):
        r = start(self.c, skill, deck_id, **kw)
        self.assertEqual(r.status_code, 201, r.content)
        return r.json()["session"]

    def run_through(self, session, grade="pass"):
        while session["status"] == "active":
            r = answer(self.c, session, grade=grade)
            self.assertEqual(r.status_code, 200, r.content)
            session = self.c.get(f"/api/v1/sessions/{session['id']}").json()["session"]
        return session

    def first_deck(self, level=1):
        return Deck.objects.get(kind="system", hsk_level=level, index=1)


class E03TodayAndQueue(Base):
    def test_e03_01_today_counts_by_skill(self):
        with at(DAY1):
            r = self.c.get("/api/v1/today").json()
        # Free: HSK 1 (30) + HSK 2 (10) publicados; nuevas limitadas a 10 en lectura y 5 en escritura.
        self.assertEqual(r["counts"]["recognition"], {"due": 0, "new": 10})
        self.assertEqual(r["counts"]["listening"], {"due": 0, "new": 0})
        self.assertEqual(r["counts"]["writing"]["new"], 5)
        self.assertTrue(Event.objects.filter(name="home_viewed").exists())

    def test_e03_01_queue_order_and_cap(self):
        set_param("session_max_cards", 12)
        set_param("new_limit_recognition", {"default": 10, "min": 0, "max": 50})
        user = self.user
        # Tres pendientes con distinto atraso: la más atrasada primero.
        w = self.words[1]
        for word, days in ((w[20], 1), (w[21], 5), (w[22], 3)):
            ReviewState.objects.create(account=user, skill="recognition", unit_key=str(word.pk), word=word, stability=2,
                                       difficulty=5, fsrs_state=2, due_at=DAY1, due_day=(DAY1 - timedelta(days=days)).date(),
                                       last_review_at=DAY1 - timedelta(days=9), last_review_day=(DAY1 - timedelta(days=9)).date(), reps=1)
        with at(DAY1):
            s = self.started()
        units = [c["unit"] for c in s["cards"]]
        self.assertEqual(units[:3], [str(w[21].pk), str(w[22].pk), str(w[20].pk)])
        self.assertEqual(len(units), 12)
        self.assertEqual(units[3], str(w[0].pk))  # nuevas en el orden del mazo
        self.assertTrue(all(c["is_new"] for c in s["cards"][3:]))

    def test_e03_01_empty_session_reason(self):
        locked_deck = Deck.objects.get(kind="system", hsk_level=3, index=1)
        with at(DAY1):
            r = start(self.c, "recognition", locked_deck.pk)
            self.assertEqual(r.json(), {"session": None, "empty_reason": "locked"})
            r = start(self.c, "listening")
            self.assertEqual(r.json()["empty_reason"], "nothing_due")
            set_param("new_limit_recognition", {"default": 0, "min": 0, "max": 50})
            self.user.profile.new_limit_recognition = 0
            self.user.profile.save()
            self.assertEqual(start(self.c, "recognition").json()["empty_reason"], "new_limit_reached")
        draft_only = make_word(1, 99, "龙", publish=None)
        deck = Deck.objects.create(kind="system", hsk_level=1, index=50)
        deck.entries.create(word=draft_only, position=0)
        with at(DAY1):
            self.assertEqual(start(self.c, "recognition", deck.pk).json()["empty_reason"], "in_review")
        self.assertEqual(StudySession.objects.count(), 0)
        self.assertEqual(Event.objects.filter(name="session_empty").count(), 4)

    def test_e03_01_queue_is_frozen_at_start(self):
        with at(DAY1):
            s = self.started(deck_id=self.first_deck().pk)
            before = [c["unit"] for c in s["cards"]]
            make_word(1, 200, "新")  # contenido nuevo publicado después de iniciar
            after = [c["unit"] for c in self.c.get(f"/api/v1/sessions/{s['id']}").json()["session"]["cards"]]
        self.assertEqual(before, after)

    def test_e03_01_all_due_new_words_follow_system_decks(self):
        set_param("new_limit_recognition", {"default": 50, "min": 0, "max": 50})
        self.user.profile.new_limit_recognition = 50
        self.user.profile.save()
        with at(DAY1):
            s = self.started()
        expected = [str(w.pk) for w in self.words[1] + self.words[2]]  # HSK 3 no está en Free
        self.assertEqual([c["unit"] for c in s["cards"]], expected[:40])


class E03Reading(Base):
    def test_e03_02_grades_map_to_good_and_again(self):
        from fsrs import Rating

        from scheduling.fsrs_adapter import RATING

        self.assertEqual(RATING, {"pass": Rating.Good, "fail": Rating.Again})
        with at(DAY1):
            s = self.started()
            r = answer(self.c, s, grade="easy")
        self.assertEqual(r.status_code, 400)

    def test_e03_02_failed_card_reinforced_without_state_change(self):
        with at(DAY1):
            s = self.started()
            unit = s["cards"][0]["unit"]
            r = answer(self.c, s, 0, "fail").json()
            added = r["session"]["cards_added"]
            self.assertEqual(len(added), 1)
            self.assertEqual(added[0]["position"], 4)  # tras reinforce_gap = 3 tarjetas
            self.assertTrue(added[0]["is_reinforcement"])
            state_after_fail = ReviewState.objects.get(account=self.user, skill="recognition", unit_key=unit)
            s = self.c.get(f"/api/v1/sessions/{s['id']}").json()["session"]
            for pos in (1, 2, 3):
                answer(self.c, s, pos, "pass")
            r = answer(self.c, s, 4, "pass").json()
            self.assertFalse(r["answer"]["counted"])
        state = ReviewState.objects.get(pk=state_after_fail.pk)
        self.assertEqual((state.reps, state.stability), (state_after_fail.reps, state_after_fail.stability))

    def test_e03_02_only_first_answer_of_day_counts(self):
        deck = self.first_deck()
        with at(DAY1):
            s_all = self.started()  # creada antes: también contiene la primera palabra del mazo
            s_deck = self.started(deck_id=deck.pk)
            unit = s_deck["cards"][0]["unit"]
            self.assertEqual(s_all["cards"][0]["unit"], unit)
            self.assertTrue(answer(self.c, s_deck, 0, "pass").json()["answer"]["counted"])
            self.assertFalse(answer(self.c, s_all, 0, "fail").json()["answer"]["counted"])
        state = ReviewState.objects.get(unit_key=unit, skill="recognition")
        self.assertEqual((state.reps, state.lapses), (1, 0))
        self.assertEqual(Answer.objects.filter(unit_key=unit).count(), 2)

    def test_fsrs_adapter_reference_vectors(self):
        from scheduling.fsrs_adapter import LIBRARY_VERSION, Scheduler

        import fsrs

        self.assertEqual(LIBRARY_VERSION, "6.3.3")
        self.assertEqual(getattr(fsrs, "__version__", LIBRARY_VERSION), LIBRARY_VERSION)
        # Batería generada con fsrs 6.3.3, pasos vacíos y sin aleatoriedad. Al subir la librería se regenera.
        vectors = {
            ("pass", "pass", "fail", "pass"): [2, 11, 2, 5],
            ("fail", "pass", "pass"): [1, 2, 6],
            ("pass", "pass", "pass"): [2, 11, 46],
        }
        for seq, intervals in vectors.items():
            sch, mem, t, got = Scheduler("recognition"), None, DAY1, []
            for g in seq:
                mem = sch.review(mem, g, t)
                got.append(round((mem.due_at - t).total_seconds() / 86400))
                t = mem.due_at
            self.assertEqual(got, intervals, seq)

    def test_e03_02_unpublished_words_never_queued(self):
        draft = make_word(1, 300, "草", publish=None)
        english_only = make_word(1, 301, "花", publish="en")
        from decks.services import build_system_decks

        build_system_decks()
        set_param("new_limit_recognition", {"default": 50, "min": 0, "max": 50})
        self.user.profile.new_limit_recognition = 50
        self.user.profile.save()
        with at(DAY1):
            s = self.started()
        units = {c["unit"] for c in s["cards"]}
        self.assertNotIn(str(draft.pk), units)
        self.assertNotIn(str(english_only.pk), units)


class E03NewWords(Base):
    def test_e03_03_new_limit_across_decks(self):
        self.user.profile.new_limit_recognition = 4
        self.user.profile.save()
        with at(DAY1):
            s = self.started(deck_id=self.first_deck(1).pk)
            self.assertEqual(len(s["cards"]), 4)
            self.run_through(s)
            r = start(self.c, "recognition", self.first_deck(2).pk).json()
        self.assertEqual(r["empty_reason"], "new_limit_reached")

    def test_e03_03_new_limit_reached_event(self):
        self.user.profile.new_limit_recognition = 2
        self.user.profile.save()
        with at(DAY1):
            self.run_through(self.started())
        ev = Event.objects.filter(name="new_limit_reached")
        self.assertEqual(ev.count(), 1)
        self.assertEqual(ev.first().props, {"skill": "recognition", "limit": 2})

    def test_e03_03_limit_change_applies_now(self):
        self.user.profile.new_limit_recognition = 2
        self.user.profile.save()
        with at(DAY1):
            self.run_through(self.started())
            r = self.c.patch("/api/v1/me/profile", {"new_limit_recognition": 5}, format="json")
            self.assertEqual(r.status_code, 200)
            s = self.started()
        self.assertEqual(len(s["cards"]), 3)


class E03Summary(Base):
    def test_e03_04_completion_summary(self):
        self.user.profile.new_limit_recognition = 3
        self.user.profile.save()
        with at(DAY1):
            s = self.started()
            answer(self.c, s, 0, "fail")
            s = self.run_through(self.c.get(f"/api/v1/sessions/{s['id']}").json()["session"])
        self.assertEqual(s["status"], "completed")
        self.assertEqual(s["summary"], {"answered": 3, "passed": 2, "failed": 1})
        self.assertEqual(Event.objects.get(name="session_completed").props["failed"], 1)

    def test_e03_04_answers_final_after_discard(self):
        with at(DAY1):
            s = self.started()
            answer(self.c, s, 0, "pass")
            self.c.post(f"/api/v1/sessions/{s['id']}/discard")
            today = self.c.get("/api/v1/today").json()
        self.assertEqual(ReviewState.objects.filter(account=self.user).count(), 1)
        self.assertTrue(today["streak"]["today_active"])


class E04Listening(Base):
    def _learn(self, n=5):
        self.user.profile.new_limit_recognition = n
        self.user.profile.save()
        with at(DAY1):
            self.run_through(self.started())

    def test_e04_01_card_payload_includes_audio_urls(self):
        silent = make_word(1, 400, "静", audio=False)
        with at(DAY1):
            s = self.started()
        w = s["words"][s["cards"][0]["word_id"]]
        self.assertTrue(w["audio"].endswith(".mp3"))
        self.assertTrue(all(e["audio"] for e in w["examples"]))
        from content.services.reading import word_payloads

        self.assertIsNone(word_payloads([silent.pk], "es")[silent.pk]["audio"])

    def test_e04_02_listening_eligibility(self):
        silent = self.words[1][1]
        from content.models import AudioAsset
        from content.services.environment import text_hash

        AudioAsset.objects.filter(text_hash=text_hash(silent.hanzi)).delete()
        self._learn(5)
        with at(DAY1):
            self.assertEqual(start(self.c, "listening").json()["empty_reason"], "nothing_due")  # primer «Recordé» hoy
        with at(DAY1 + timedelta(days=1)):
            s = self.started("listening")
        units = [c["unit"] for c in s["cards"]]
        self.assertEqual(len(units), 4)
        self.assertNotIn(str(silent.pk), units)

    def test_e04_02_choices_from_same_level(self):
        self._learn(3)
        with at(DAY1 + timedelta(days=1)):
            s = self.started("listening")
            card = s["cards"][0]
            self.assertEqual(len(card["choices"]), 4)
            self.assertIn(card["word_id"], card["choices"])
            self.assertTrue(all(Word.objects.get(pk=c).hsk_level == 1 for c in card["choices"]))
            self.assertTrue(all(c in s["words"] for c in card["choices"]))
            wrong = next(c for c in card["choices"] if c != card["word_id"])
            r = answer(self.c, s, 0, "pass", choice=wrong).json()
            self.assertEqual(r["answer"]["grade"], "fail")  # el servidor decide
            s = self.c.get(f"/api/v1/sessions/{s['id']}").json()["session"]
            card = next(c for c in s["cards"] if c["position"] == s["position"])
            r = answer(self.c, s, card["position"], "fail", choice=card["word_id"]).json()
        self.assertEqual(r["answer"]["grade"], "pass")

    def test_e04_02_listening_has_own_state(self):
        self._learn(1)
        rec = ReviewState.objects.get(account=self.user, skill="recognition")
        with at(DAY1 + timedelta(days=1)):
            s = self.started("listening")
            answer(self.c, s, 0, choice=s["cards"][0]["word_id"])
        self.assertTrue(ReviewState.objects.filter(account=self.user, skill="listening", unit_key=rec.unit_key).exists())
        self.assertEqual(ReviewState.objects.get(pk=rec.pk).reps, 1)

    def test_e04_02_no_new_limit_for_listening(self):
        self._learn(10)
        self.user.profile.new_limit_recognition = 1
        self.user.profile.save()
        with at(DAY1 + timedelta(days=1)):
            s = self.started("listening")
        self.assertEqual(len(s["cards"]), 10)


class E05Writing(Base):
    def test_e05_01_guided_does_not_change_state(self):
        with at(DAY1):
            s = self.started("writing")
            r = answer(self.c, s, 0, writing={"mode": "guided", "stroke_misses": 0, "hint_used": False}).json()
            today = self.c.get("/api/v1/today").json()
        self.assertFalse(r["answer"]["counted"])
        self.assertEqual(r["session"]["position"], 0)  # la tarjeta sigue esperando la respuesta de memoria
        self.assertFalse(ReviewState.objects.filter(account=self.user, skill="writing").exists())
        self.assertFalse(today["streak"]["today_active"])
        self.assertEqual(Answer.objects.get().mode, "guided")

    def test_e05_01_chars_without_strokes_skipped(self):
        first = self.words[1][0]
        Character.objects.filter(char=first.hanzi).update(has_stroke_data=False)
        from study.queue import candidates

        with at(DAY1):
            c = candidates(self.user, "writing", apply_limit=False)
        self.assertEqual(c.no_strokes, 1)
        self.assertNotIn(first.hanzi, [x.unit_key for x in c.fresh])

    def test_e05_02_server_decides_writing_grade(self):
        with at(DAY1):
            s = self.started("writing")
            r1 = answer(self.c, s, 0, "fail", writing={"mode": "recall", "stroke_misses": 2, "hint_used": False}).json()
            r2 = answer(self.c, s, 1, "pass", writing={"mode": "recall", "stroke_misses": 3, "hint_used": False}).json()
        self.assertEqual((r1["answer"]["grade"], r2["answer"]["grade"]), ("pass", "fail"))

    def test_e05_02_answer_stores_threshold(self):
        set_param("writing_max_stroke_misses", 4)
        with at(DAY1):
            s = self.started("writing")
            answer(self.c, s, 0, writing={"mode": "recall", "stroke_misses": 4, "hint_used": False})
        a = Answer.objects.get()
        self.assertEqual((a.stroke_misses, a.hint_used, a.threshold, a.grade), (4, False, 4, "pass"))

    def test_e05_02_char_asked_once_per_queue(self):
        a = make_word(1, 500, "大人")
        b = make_word(1, 501, "人口")
        deck = Deck.objects.create(kind="system", hsk_level=1, index=60)
        deck.entries.create(word=a, position=0)
        deck.entries.create(word=b, position=1)
        self.user.profile.new_limit_writing = 30
        self.user.profile.save()
        with at(DAY1):
            s = self.started("writing", deck_id=deck.pk)
        self.assertEqual([c["unit"] for c in s["cards"]], ["大", "人", "口"])

    def test_e05_02_only_writing_list_characters(self):
        listed = make_word(1, 700, "山水", writing=False)
        Character.objects.update_or_create(char="山", defaults={"writing_level": 1})
        Character.objects.update_or_create(char="水", defaults={"writing_level": 3})  # se pide desde HSK 3
        unlisted = make_word(1, 701, "龟", writing=False)  # no está en la lista de escritura
        deck = Deck.objects.create(kind="system", hsk_level=1, index=70)
        deck.entries.create(word=listed, position=0)
        deck.entries.create(word=unlisted, position=1)
        with at(DAY1):
            s = self.started("writing", deck_id=deck.pk)
        self.assertEqual([c["unit"] for c in s["cards"]], ["山"])

    def test_e05_03_hint_means_fail(self):
        with at(DAY1):
            s = self.started("writing")
            r = answer(self.c, s, 0, "pass", writing={"mode": "recall", "stroke_misses": 0, "hint_used": True}).json()
        self.assertEqual(r["answer"]["grade"], "fail")


class E06Saving(Base):
    def test_e06_01_client_time_clamped(self):
        with at(DAY1):
            s = self.started()
        with at(DAY1 + timedelta(minutes=10)):
            answer(self.c, s, 0, answered_at=(DAY1 + timedelta(minutes=5)).isoformat())
            answer(self.c, s, 1, answered_at=(DAY1 - timedelta(days=3)).isoformat())
            answer(self.c, s, 2, answered_at=(DAY1 + timedelta(days=3)).isoformat())
        times = list(Answer.objects.order_by("received_at").values_list("answered_at", flat=True))
        self.assertEqual(times, [DAY1 + timedelta(minutes=5), DAY1 + timedelta(minutes=10), DAY1 + timedelta(minutes=10)])

    def test_e06_01_delayed_delivery_event(self):
        with at(DAY1):
            s = self.started()
        with at(DAY1 + timedelta(seconds=90)):
            answer(self.c, s, 0, attempts=4, first_attempt_at=DAY1.isoformat())
        e = Event.objects.get(name="answer_delivery_delayed")
        self.assertEqual(e.props, {"attempts": 4, "delay_s": 90})

    def test_e06_02_one_active_session_per_scope_and_skill(self):
        with at(DAY1):
            s = self.started()
            r = start(self.c)
            self.assertEqual(r.status_code, 409)
            self.assertEqual(r.json()["session"]["id"], s["id"])
            self.started("writing")  # otra habilidad sí
            forced = self.started(force=True)
        self.assertNotEqual(forced["id"], s["id"])
        self.assertEqual(StudySession.objects.get(pk=s["id"]).status, "discarded")
        with self.assertRaises(IntegrityError), transaction.atomic():
            StudySession.objects.create(account=self.user, scope_type="all_due", scope_key="all_due", skill="recognition")

    def test_e06_02_resume_at_first_unanswered(self):
        with at(DAY1):
            s = self.started()
            order = [c["unit"] for c in s["cards"]]
            answer(self.c, s, 0)
            answer(self.c, s, 1)
            make_word(1, 600, "又")
            r = self.c.post(f"/api/v1/sessions/{s['id']}/resume", {"same_client": True}, format="json").json()["session"]
        self.assertEqual(r["position"], 2)
        self.assertEqual([c["unit"] for c in r["cards"]], order)

    def test_e06_02_resume_skips_already_reviewed(self):
        deck = self.first_deck()
        with at(DAY1):
            s_all = self.started()
            s_deck = self.started(deck_id=deck.pk)
            answer(self.c, s_deck, 0)
            answer(self.c, s_deck, 1)
            r = self.c.post(f"/api/v1/sessions/{s_all['id']}/resume", format="json").json()["session"]
        self.assertEqual([c["result"] for c in r["cards"][:3]], ["skipped", "skipped", None])
        self.assertEqual(r["position"], 2)
        self.assertEqual(Event.objects.get(name="session_resumed").props["skipped_already_reviewed"], 2)

    def test_e06_02_discard_keeps_answers(self):
        with at(DAY1):
            s = self.started()
            answer(self.c, s, 0)
            self.c.post(f"/api/v1/sessions/{s['id']}/discard")
            r = answer(self.c, s, 1)
        self.assertEqual(r.status_code, 409)
        self.assertEqual(Answer.objects.count(), 1)
        self.assertEqual(ReviewState.objects.count(), 1)

    def test_e06_02_session_expires_after_ttl(self):
        with at(DAY1):
            s = self.started()
        self.assertEqual(expire_sessions(DAY1 + timedelta(days=6)), 0)
        self.assertEqual(expire_sessions(DAY1 + timedelta(days=8)), 1)
        self.assertEqual(StudySession.objects.get(pk=s["id"]).status, "expired")
        self.assertTrue(Event.objects.filter(name="session_expired").exists())

    def test_e06_02_resumable_across_days(self):
        with at(DAY1):
            s = self.started()
            answer(self.c, s, 0)
        with at(DAY1 + timedelta(days=1)):
            s = self.c.post(f"/api/v1/sessions/{s['id']}/resume", format="json").json()["session"]
            answer(self.c, s, 1)
        days = list(Answer.objects.order_by("received_at").values_list("local_day", flat=True))
        self.assertEqual(days, [DAY1.date(), (DAY1 + timedelta(days=1)).date()])

    def test_e06_03_resume_from_other_device(self):
        other_device = client_for(self.user)
        with at(DAY1):
            s = self.started()
            answer(self.c, s, 0)
            r = other_device.post(f"/api/v1/sessions/{s['id']}/resume", {"same_client": False}, format="json").json()
        self.assertEqual(r["session"]["position"], 1)

    def test_e06_03_stale_answer_rejected_with_position(self):
        with at(DAY1):
            s = self.started()
            first = answer(self.c, s, 0, "pass")
            second = answer(client_for(self.user), s, 0, "fail")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 409)
        self.assertEqual(second.json()["error"], "stale_card")
        self.assertEqual(second.json()["session"]["position"], 1)
        self.assertEqual(Answer.objects.count(), 1)
        self.assertTrue(Event.objects.filter(name="answer_rejected_stale").exists())


class E00Idempotency(Base):
    def test_e00_01_same_client_id_applies_once(self):
        with at(DAY1):
            s = self.started()
            card = s["cards"][0]
            body = {"client_id": str(uuid.uuid4()), "session_id": s["id"], "position": 0, "unit": card["unit"], "grade": "fail"}
            r1 = self.c.post("/api/v1/answers", body, format="json").json()
            r2 = self.c.post("/api/v1/answers", body, format="json").json()
        self.assertEqual(r1, r2)
        self.assertEqual(Answer.objects.count(), 1)
        self.assertEqual(ReviewState.objects.get().reps, 1)
        self.assertEqual(Event.objects.filter(name="answer_recorded").count(), 1)

    def test_e00_01_client_id_unique_in_database(self):
        with at(DAY1):
            s = self.started()
            answer(self.c, s, 0)
        a = Answer.objects.get()
        a.pk = None
        with self.assertRaises(IntegrityError), transaction.atomic():
            a.save()

    def test_e00_01_client_id_scoped_to_account(self):
        other = student("beto@example.com")
        c2 = client_for(other)
        cid = str(uuid.uuid4())
        with at(DAY1):
            for client in (self.c, c2):
                s = start(client).json()["session"]
                r = client.post("/api/v1/answers", {"client_id": cid, "session_id": s["id"], "position": 0,
                                                    "unit": s["cards"][0]["unit"], "grade": "pass"}, format="json")
                self.assertEqual(r.status_code, 200)
        self.assertEqual(Answer.objects.filter(client_id=cid).count(), 2)

    def test_answers_exactly_once_under_chaos(self):
        import random

        set_param("session_max_cards", 50)
        users = [self.user] + [student(f"u{i}@example.com") for i in range(24)]
        rng = random.Random(7)
        sent = 0
        with at(DAY1):
            for u in users:
                u.profile.new_limit_recognition = 50
                u.profile.save()
                cl = client_for(u)
                s = start(cl).json()["session"]
                queue = [c for c in s["cards"]]
                bodies = []
                for c in queue:
                    bodies.append({"client_id": str(uuid.uuid4()), "session_id": s["id"], "position": c["position"],
                                   "unit": c["unit"], "grade": "pass"})
                # Reenvíos, duplicados y respuestas repetidas desordenadas tras el envío original.
                stream = []
                for b in bodies:
                    stream.append(b)
                    stream += [b] * rng.randint(0, 2)
                for b in stream:
                    cl.post("/api/v1/answers", b, format="json")
                for b in rng.sample(bodies, len(bodies)):
                    cl.post("/api/v1/answers", b, format="json")
                sent += len(bodies)
        self.assertEqual(Answer.objects.count(), sent)
        self.assertEqual(ReviewState.objects.count(), sent)
        self.assertEqual(sent, 1000)
