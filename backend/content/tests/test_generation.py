import json
from types import SimpleNamespace

from django.core.management import call_command
from django.test import TestCase

from content.models import Example, LanguageContentVersion, Sense, VersionStatus, WordBaseVersion
from content.services.editorial import publish_base, publish_language
from content.services.environment import build_environment
from content.services.generation import (
    GenerationError, build_request, parse_message, run_sync, select_targets,
)
from content.services.validation import failed_codes
from languages.models import Language
from ops.models import Parameter

from .helpers import add_audio, editor, make_base, make_language, setup_syllabus


def message(payload, stop_reason="end_turn"):
    return SimpleNamespace(stop_reason=stop_reason,
                           content=[SimpleNamespace(type="text", text=json.dumps(payload, ensure_ascii=False))])


class FakeClient:
    """Imita client.messages.create devolviendo respuestas preparadas por palabra."""

    def __init__(self, responses):
        self.responses = responses
        self.calls = []
        self.messages = self

    def create(self, **params):
        self.calls.append(params)
        user = params["messages"][0]["content"]
        hanzi = user.split("\n")[0].removeprefix("Word: ")
        return self.responses[hanzi](params) if callable(self.responses[hanzi]) else self.responses[hanzi]


FULL_HE = {"senses": [{
    "source_gloss": 1, "pos": "verb", "reading": "", "meaning": "beber",
    "examples": [{"zh": "我喝水。", "translation": "Yo bebo agua."},
                 {"zh": "妈妈喝茶。", "translation": "Mamá bebe té."},
                 {"zh": "你喝吗？", "translation": "¿Tú bebes?"}],
}]}


class GenerationTests(TestCase):
    def setUp(self):
        self.words = setup_syllabus()
        Parameter.objects.update_or_create(key="content.example_max_chars", defaults={"value": {"1": 12}})
        Parameter.objects.update_or_create(key="content.example_level_tolerance", defaults={"value": {"1": 1}})
        self.es = Language.objects.get(code="es")
        self.word = self.words["喝"]

    def test_full_mode_creates_base_and_language_drafts_with_computed_pinyin(self):
        targets, _ = select_targets([self.word], self.es)
        self.assertEqual(targets[0].mode, "full")
        summary = run_sync(FakeClient({"喝": message(FULL_HE)}), targets, self.es, build_environment(), "m", log=lambda *_: None)
        self.assertEqual(summary["stored"], 1)
        base = WordBaseVersion.objects.get(word=self.word)
        self.assertEqual((base.status, base.origin), (VersionStatus.DRAFT, "generated"))
        self.assertEqual(Example.objects.get(sense__base_version=base, position=1).pinyin, "mā ma hē chá.")
        sense = Sense.objects.get(base_version=base)
        self.assertEqual(sense.source_gloss.gloss, "to drink")
        add_audio("喝", "我喝水。", "妈妈喝茶。", "你喝吗？")
        lang = LanguageContentVersion.objects.get(word=self.word, language=self.es)
        from content.services.validation import validate_base, validate_language
        validate_base(base)
        validate_language(lang)
        self.assertEqual(failed_codes(base), [])
        self.assertEqual(failed_codes(lang), [])

    def test_empty_example_from_model_is_dropped(self):
        payload = json.loads(json.dumps(FULL_HE))
        payload["senses"][0]["examples"].insert(1, {"zh": "", "translation": ""})
        targets, _ = select_targets([self.word], self.es)
        run_sync(FakeClient({"喝": message(payload)}), targets, self.es, build_environment(), "m", log=lambda *_: None)
        base = WordBaseVersion.objects.get(word=self.word)
        self.assertEqual([e.text_zh for e in Example.objects.filter(sense__base_version=base).order_by("position")],
                         ["我喝水。", "妈妈喝茶。", "你喝吗？"])

    def test_request_shape(self):
        targets, _ = select_targets([self.word], self.es)
        req = build_request(targets[0], self.es, build_environment(), "claude-sonnet-5-5", "medium")
        self.assertEqual(req["output_config"]["format"]["type"], "json_schema")
        self.assertEqual(req["system"][0]["cache_control"], {"type": "ephemeral"})
        system = req["system"][0]["text"]
        self.assertIn("Spanish", system)
        self.assertIn("at most 12 Chinese characters", system)
        self.assertIn("妈妈", system)  # vocabulario permitido
        self.assertIn("to drink", req["messages"][0]["content"])

    def test_rerun_does_not_duplicate(self):
        # HU-E13-02: repetirlo no duplica nada
        env = build_environment()
        run_sync(FakeClient({"喝": message(FULL_HE)}), select_targets([self.word], self.es)[0], self.es, env, "m", log=lambda *_: None)
        targets, skipped = select_targets([self.word], self.es)
        self.assertEqual(targets, [])
        self.assertEqual(len(skipped), 1)

    def test_imported_base_is_kept_unless_explicitly_replaced(self):
        base = make_base(self.word, origin="imported")
        make_language(base)
        self.assertEqual(select_targets([self.word], self.es)[0], [])
        targets, _ = select_targets([self.word], self.es, regenerate=True)
        self.assertEqual((targets[0].mode, targets[0].base_version), ("translate", base))
        targets, _ = select_targets([self.word], self.es, replace_base_drafts=True)
        self.assertEqual(targets[0].mode, "full")
        run_sync(FakeClient({"喝": message(FULL_HE)}), targets, self.es, build_environment(), "m",
                 log=lambda *_: None, replace_base_drafts=True)
        self.assertEqual(WordBaseVersion.objects.get(word=self.word).origin, "generated")

    def test_published_base_is_never_regenerated(self):
        user = editor()
        base = make_base(self.word)
        publish_base(base, user)
        targets, _ = select_targets([self.word], self.es, replace_base_drafts=True)
        self.assertEqual((targets[0].mode, targets[0].base_version), ("translate", base))

    def test_truncated_or_refused_responses_are_failures(self):
        with self.assertRaises(GenerationError):
            parse_message(message(FULL_HE, stop_reason="max_tokens"))
        with self.assertRaises(GenerationError):
            parse_message(SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="thinking")]))

    def test_new_language_only_translates_published_base(self):
        # 08-contenido.md §8 / R-IDI-10: sin acepciones ni ejemplos nuevos, sin tocar código.
        user = editor()
        base = make_base(self.word)
        publish_base(base, user)
        publish_language(make_language(base, "es"), user)
        xx = Language.objects.create(code="xx", name="Xx", generation_name="Testish",
                                     function_words=["zz"])
        targets, _ = select_targets([self.word], xx)
        self.assertEqual((targets[0].mode, targets[0].base_version), ("translate", base))

        sense = base.senses.get()
        examples = list(sense.examples.order_by("position"))
        payload = {"senses": [{"sense_id": sense.pk, "meaning": "drinko",
                               "examples": [{"sentence_id": e.pk, "translation": f"t{e.pk}"} for e in examples]}]}
        client = FakeClient({"喝": message(payload)})
        run_sync(client, targets, xx, build_environment(), "m", log=lambda *_: None)
        self.assertIn("Testish", client.calls[0]["system"][0]["text"])
        self.assertEqual(WordBaseVersion.objects.filter(word=self.word).count(), 1)
        lang = LanguageContentVersion.objects.get(word=self.word, language=xx)
        self.assertEqual(lang.base_version, base)
        self.assertEqual(failed_codes(lang), [])
        publish_language(lang, user)


class CommandTests(TestCase):
    def test_load_syllabus_is_idempotent_and_keeps_ids(self):
        import tempfile
        rows = [{"no": 1, "simplified": "爱", "pinyin_pdf": "ai", "hsk_level": 1,
                 "senses": [{"sense_index": 0, "pos_raw": "verb", "translation_en": "to love", "is_primary": True}]}]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False)
        call_command("load_syllabus", f.name, gloss_source="mb", verbosity=0, stdout=open("/dev/null", "w"))
        from content.models import ThirdPartyGloss, Word
        word = Word.objects.get()
        rows[0]["pinyin_pdf"] = "ài"  # corrección de un dato del sílabo
        with open(f.name, "w", encoding="utf-8") as g:
            json.dump(rows, g, ensure_ascii=False)
        call_command("load_syllabus", f.name, gloss_source="mb", stdout=open("/dev/null", "w"))
        word_after = Word.objects.get()
        self.assertEqual((word_after.pk, word_after.pinyin), (word.pk, "ài"))  # R-CON-03: mismo id
        self.assertEqual(ThirdPartyGloss.objects.count(), 1)


class EffortTests(GenerationTests):
    def test_effort_goes_in_output_config(self):
        targets, _ = select_targets([self.word], self.es)
        req = build_request(targets[0], self.es, build_environment(), "claude-sonnet-5-5", "low")
        self.assertEqual(req["output_config"]["effort"], "low")
        self.assertNotIn("thinking", req)  # Sonnet 5.5: adaptativo por defecto; "disabled" sería un 400


class HomographTests(GenerationTests):
    def test_other_entries_with_same_characters_are_listed(self):
        from content.models import ThirdPartyGloss, Word
        other = Word.objects.create(hanzi="喝", pinyin="hè", hsk_level=2, syllabus_order=99)
        ThirdPartyGloss.objects.create(word=other, source="test", position=0, gloss="to shout")
        targets, _ = select_targets([self.word], self.es)
        user = build_request(targets[0], self.es, build_environment(), "m")["messages"][0]["content"]
        self.assertIn("Other syllabus entries", user)
        self.assertIn("to shout", user)


class TargetReadingTests(GenerationTests):
    def test_single_char_entry_uses_its_syllabus_reading(self):
        from content.models import Word
        from content.services.validation import example_pinyin
        dei = Word.objects.create(hanzi="得", pinyin="děi", hsk_level=3, syllabus_order=87)
        de2 = Word.objects.create(hanzi="地", pinyin="dì", hsk_level=3, syllabus_order=89)
        env = build_environment()
        self.assertEqual(example_pinyin("你得早点儿睡觉。", dei, "", env), "nǐ děi zǎo diǎnr shuì jiào.")
        self.assertEqual(example_pinyin("地上有水。", de2, "", env), "dì shang yǒu shuǐ.")
        self.assertEqual(example_pinyin("他好运动。", self.words["好"], "hào", env), "tā hào yùn dòng.")


class EntryWordInsideCompoundTests(GenerationTests):
    def test_particle_rules_do_not_override_the_entry_word(self):
        from content.models import Word
        from content.services.validation import example_pinyin
        de = Word.objects.create(hanzi="得", pinyin="dé", hsk_level=3, syllabus_order=83)
        self.assertIn("dé le", example_pinyin("他在比赛中得了第一名。", de, "", build_environment()))
