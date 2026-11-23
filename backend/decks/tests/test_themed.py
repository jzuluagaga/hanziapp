"""Mazos por tema (D-49, 08-contenido.md §7)."""
from django.test import TestCase

from content.models import WordTheme
from decks.models import Deck
from decks.services import build_system_decks
from decks.themed import plan_level
from hanzi_backend.testing import make_level, set_param

TAX = {"themes": [
    {"key": "a", "subthemes": [{"key": "a1"}, {"key": "a2"}, {"key": "a3"}]},
    {"key": "b", "subthemes": [{"key": "b1"}]},
    {"key": "c", "subthemes": [{"key": "c1"}, {"key": "c2"}]},
]}


def ids(n, start=0):
    return list(range(start, start + n))


def names(plan):
    return [(g.keys, g.part, len(g.words)) for g in plan]


class Plan(TestCase):
    def test_e08_01_whole_theme_in_band_is_one_deck(self):
        plan = plan_level(TAX, {"a1": ids(10), "a2": ids(10, 100), "b1": ids(20, 200)}, target=25)
        self.assertEqual(names(plan), [(["a"], None, 20), (["b"], None, 20)])

    def test_e08_01_big_theme_splits_by_subtheme(self):
        plan = plan_level(TAX, {"c1": ids(20), "c2": ids(20, 100)}, target=25)
        self.assertEqual(names(plan), [(["c1"], None, 20), (["c2"], None, 20)])

    def test_e08_01_small_subtheme_joins_neighbor(self):
        plan = plan_level(TAX, {"a1": ids(4), "a2": ids(25, 100), "a3": ids(20, 200)}, target=25)
        self.assertEqual(names(plan), [(["a1", "a2"], None, 29), (["a3"], None, 20)])

    def test_e08_01_spread_subtheme_names_theme_parts(self):
        plan = plan_level(TAX, {"a1": ids(4), "a2": ids(60, 100)}, target=25)
        self.assertTrue(all(g.keys == ["a"] for g in plan))
        self.assertEqual([g.part for g in plan], list(range(1, len(plan) + 1)))
        self.assertEqual(sum(len(g.words) for g in plan), 64)

    def test_e08_01_tiny_theme_joins_next_theme(self):
        plan = plan_level(TAX, {"a1": ids(5), "b1": ids(15, 100), "c1": ids(20, 200)}, target=25)
        self.assertEqual(names(plan)[0], (["a", "b"], None, 20))

    def test_e08_01_no_deck_below_absolute_minimum(self):
        plan = plan_level(TAX, {"c1": ids(3), "c2": ids(37, 100)}, target=25)
        self.assertTrue(all(len(g.words) >= 8 for g in plan))
        self.assertEqual(sum(len(g.words) for g in plan), 40)


class Build(TestCase):
    def setUp(self):
        set_param("system_deck_size", {"1": 25, "2": 25, "3": 30, "4": 40, "5": 50, "6": 60})
        self.words = make_level(1, 30)

    def test_e08_01_syllabus_order_until_level_fully_approved(self):
        for w in self.words[:29]:
            WordTheme.objects.create(word=w, subtheme="food_drink", status="approved")
        build_system_decks([1])
        self.assertEqual(list(Deck.objects.filter(hsk_level=1).values_list("theme_keys", flat=True)), [[], []])

    def test_e08_01_system_decks_by_theme(self):
        for i, w in enumerate(self.words):
            WordTheme.objects.create(word=w, subtheme="food_drink" if i < 20 else "family", status="approved")
        build_system_decks([1])
        decks = list(Deck.objects.filter(hsk_level=1, retired_at__isnull=True).order_by("index"))
        self.assertEqual([d.theme_keys for d in decks], [["people"], ["daily_life"]])
        self.assertEqual([d.entries.count() for d in decks], [10, 20])
        build_system_decks([1])  # repetible: mismos ids
        self.assertEqual([d.pk for d in Deck.objects.filter(hsk_level=1, retired_at__isnull=True).order_by("index")],
                         [d.pk for d in decks])
