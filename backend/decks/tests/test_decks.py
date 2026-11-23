"""Pruebas de HU-E08-01 y HU-E13-04 (mazos)."""
from datetime import datetime, timezone as tz

from django.test import TestCase
from django.utils import timezone

from analytics.models import Event
from content.models import Word
from decks.models import Deck, DeckWord
from decks.services import build_system_decks
from hanzi_backend.testing import answer, at, client_for, make_level, make_word, set_param, start, student

DAY1 = datetime(2026, 12, 1, 15, 0, tzinfo=tz.utc)


class E08Decks(TestCase):
    def test_e08_01_system_decks_partition_level(self):
        set_param("system_deck_size", {"1": 25, "2": 25, "3": 30, "4": 40, "5": 50, "6": 60})
        make_level(1, 60)
        make_level(3, 65, start=60)
        summary = build_system_decks()
        self.assertEqual((summary[1], summary[3]), (3, 3))
        sizes = {(d.hsk_level, d.index): d.entries.count() for d in Deck.objects.all()}
        self.assertEqual(sizes, {(1, 1): 25, (1, 2): 25, (1, 3): 10, (3, 1): 30, (3, 2): 30, (3, 3): 5})
        for w in Word.objects.all():
            self.assertEqual(DeckWord.objects.filter(word=w).count(), 1)
        first = list(Deck.objects.get(hsk_level=1, index=1).entries.values_list("word__syllabus_order", flat=True))
        self.assertEqual(first, list(range(1, 26)))

    def test_e08_01_build_system_decks_idempotent(self):
        make_level(1, 30)
        build_system_decks()
        ids = list(Deck.objects.values_list("pk", flat=True))
        build_system_decks()
        self.assertEqual(list(Deck.objects.values_list("pk", flat=True)), ids)
        self.assertEqual(DeckWord.objects.count(), 30)

    def test_e08_01_deck_counts(self):
        make_level(1, 5)
        make_word(1, 6, "龙", publish=None)
        build_system_decks()
        user = student()
        c = client_for(user)
        deck = Deck.objects.get(hsk_level=1, index=1)
        with at(DAY1):
            s = start(c, "recognition", deck.pk).json()["session"]
            answer(c, s, 0)
            d = c.get(f"/api/v1/decks/{deck.pk}").json()
        self.assertEqual((d["deck"]["size"], d["deck"]["published"]), (6, 5))
        self.assertEqual(d["deck"]["counts"]["recognition"], {"due": 0, "new": 4})
        self.assertEqual([w["badge"] for w in d["words"]], ["scheduled", "new", "new", "new", "new", "in_review"])
        self.assertTrue(Event.objects.filter(name="deck_viewed").exists())

    def test_e08_01_level_shows_published_over_total(self):
        make_level(1, 4)
        make_word(1, 5, "龙", publish=None)
        build_system_decks()
        levels = client_for(student()).get("/api/v1/levels").json()
        self.assertEqual((levels[0]["total"], levels[0]["published"], levels[0]["decks"]), (5, 4, 1))

    def test_e08_01_locked_levels_show_unlocking_plan(self):
        make_level(4, 3)
        build_system_decks()
        c = client_for(student())
        lv4 = c.get("/api/v1/levels").json()[3]
        self.assertEqual((lv4["locked"], lv4["unlocking_plan"]), (True, "pro"))
        decks = c.get("/api/v1/decks?level=4").json()
        self.assertEqual((len(decks), decks[0]["locked"], decks[0]["unlocking_plan"]), (1, True, "pro"))


class E13RetiredWord(TestCase):
    def test_e13_04_retired_word_leaves_decks_and_queues(self):
        words = make_level(1, 4)
        build_system_decks()
        user = student()
        c = client_for(user)
        with at(DAY1):
            s = start(c).json()["session"]
            answer(c, s, 0)
        words[0].retired_at = timezone.now()
        words[0].save()
        build_system_decks()
        self.assertFalse(DeckWord.objects.filter(word=words[0]).exists())
        with at(DAY1.replace(day=20)):
            s2 = start(c, force=True).json()["session"]
        self.assertNotIn(str(words[0].pk), [x["unit"] for x in s2["cards"]])
        from scheduling.models import ReviewLog

        self.assertTrue(ReviewLog.objects.filter(unit_key=str(words[0].pk)).exists())  # historial conservado
