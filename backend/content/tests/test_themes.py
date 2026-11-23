"""Clasificación por temas (D-49). Ninguna prueba llama a la API: el cliente es simulado."""
import json
from types import SimpleNamespace

from django.test import TestCase

from content.models import WordTheme
from content.services import themes
from hanzi_backend.testing import make_level


def fake_message(items):
    return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="text", text=json.dumps({"items": items}))],
                           usage=SimpleNamespace(input_tokens=100, output_tokens=50, cache_read_input_tokens=0,
                                                 cache_creation_input_tokens=0))


class FakeClient:
    def __init__(self, answer):
        self.answer = answer
        self.messages = SimpleNamespace(create=self.create)
        self.requests = []

    def create(self, **req):
        self.requests.append(req)
        ids = [int(line.split(" | ")[0]) for line in req["messages"][0]["content"].splitlines()[1:]]
        return fake_message(self.answer(ids))


class Themes(TestCase):
    def setUp(self):
        self.words = make_level(1, 60)

    def test_taxonomy_has_11_themes_and_46_unique_subthemes(self):
        keys = themes.subtheme_keys()
        self.assertEqual((len(themes.taxonomy()["themes"]), len(keys), len(set(keys))), (11, 46, 46))

    def test_request_uses_closed_list_and_chunks_by_level(self):
        make_level(2, 10, start=60)
        groups = themes.chunks(themes.select_words())
        self.assertEqual([len(g) for g in groups], [50, 10, 10])
        req = themes.build_request(groups[0], "claude-sonnet-5-5")
        enum = req["output_config"]["format"]["schema"]["properties"]["items"]["items"]["properties"]["subtheme"]["enum"]
        self.assertEqual(enum, themes.subtheme_keys())
        self.assertIn("cache_control", req["system"][0])

    def test_sync_stores_drafts_and_rerun_skips_classified(self):
        client = FakeClient(lambda ids: [{"id": i, "subtheme": "food_drink", "doubtful": i % 2 == 0} for i in ids])
        r = themes.run_sync(client, themes.select_words(), "m", log=lambda *_: None)
        self.assertEqual((r["stored"], r["problems"]), (60, []))
        self.assertEqual(WordTheme.objects.filter(status="draft").count(), 60)
        self.assertEqual(themes.select_words(), [])  # repetir no vuelve a pedir lo clasificado

    def test_store_rejects_foreign_repeated_and_missing_ids(self):
        ids = [w.pk for w in self.words[:3]]
        data = {"items": [{"id": ids[0], "subtheme": "family", "doubtful": False},
                          {"id": ids[0], "subtheme": "family", "doubtful": False},
                          {"id": 999999, "subtheme": "family", "doubtful": False}]}
        stored, problems = themes.store(ids, data, {})
        self.assertEqual(stored, 1)
        self.assertEqual(len(problems), 3)  # repetido, ajeno y dos sin respuesta

    def test_approved_never_overwritten(self):
        w = self.words[0]
        WordTheme.objects.create(word=w, subtheme="family", status="approved")
        themes.store([w.pk], {"items": [{"id": w.pk, "subtheme": "food_drink", "doubtful": False}]}, {})
        self.assertEqual(WordTheme.objects.get(word=w).subtheme, "family")
        self.assertNotIn(w, themes.select_words(regenerate=True))
