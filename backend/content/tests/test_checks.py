from django.test import SimpleTestCase

from content.pipeline.checks import (
    BaseContext, ExampleData, LanguageContext, SenseData, TranslationData, check_base, check_language,
)
from content.pipeline.pinyin import a_pinyin

HSK1 = {"我", "你", "他", "她", "是", "学生", "老师", "很", "好", "吗", "的", "书", "看", "喝", "茶", "水", "人",
        "爱", "家", "们", "我们", "妈妈", "爸爸", "大", "小", "朋友", "有", "没", "一", "个", "在", "哪儿", "去", "吃", "饭"}


def ex(zh):
    return ExampleData(zh, a_pinyin(zh))


def ctx(**kw):
    base = dict(hanzi="喝", hsk_level=1, allowed_words=HSK1, known_words=HSK1, max_chars=12,
                level_tolerance=1, audio_voice="v1", audio_texts=set())
    base.update(kw)
    return BaseContext(**base)


def results(senses, **kw):
    return {code: (ok, detail) for code, ok, detail in check_base(senses, ctx(**kw))}


GOOD = [SenseData("verb", [ex("我喝水。"), ex("妈妈喝茶。"), ex("你喝吗？")])]


class BaseChecksTests(SimpleTestCase):
    def test_good_draft_passes_everything_but_audio(self):
        r = results(GOOD)
        self.assertEqual([c for c, (ok, _) in r.items() if not ok], ["audio_present"])

    def test_audio_present(self):
        texts = {"喝", "我喝水。", "妈妈喝茶。", "你喝吗？"}
        self.assertTrue(results(GOOD, audio_texts=texts)["audio_present"][0])
        self.assertFalse(results(GOOD, audio_voice=None)["audio_present"][0])

    def test_word_in_example(self):
        r = results([SenseData("verb", [ex("我喝水。"), ex("我吃饭。"), ex("你喝吗？")])])
        self.assertFalse(r["word_in_example"][0])

    def test_hanzi_only(self):
        r = results([SenseData("verb", [ex("我喝2杯水。"), ex("妈妈喝茶。"), ex("你喝吗?")])])
        self.assertFalse(r["example_hanzi_only"][0])
        self.assertIn("'2'", r["example_hanzi_only"][1])
        self.assertIn("'?'", r["example_hanzi_only"][1])

    def test_pinyin_matches(self):
        bad = [SenseData("verb", [ExampleData("我喝水。", "wǒ hē"), ex("妈妈喝茶。"), ExampleData("你喝吗？", "")])]
        r = results(bad)
        self.assertFalse(r["example_pinyin_matches"][0])
        self.assertIn("sin pinyin", r["example_pinyin_matches"][1])

    def test_length_and_missing_parameter(self):
        long = [SenseData("verb", [ex("我和我的好朋友们都很爱喝大杯的茶。"), ex("妈妈喝茶。"), ex("你喝吗？")])]
        self.assertFalse(results(long)["example_length"][0])
        self.assertFalse(results(GOOD, max_chars=None)["example_length"][0])

    def test_example_level_with_tolerance(self):
        one_out = [SenseData("verb", [ex("我喝咖啡。"), ex("妈妈喝茶。"), ex("你喝吗？")])]
        two_out = [SenseData("verb", [ex("我在公园喝咖啡。"), ex("妈妈喝茶。"), ex("你喝吗？")])]
        self.assertTrue(results(one_out)["example_level"][0])
        self.assertFalse(results(two_out)["example_level"][0])
        self.assertFalse(results(GOOD, level_tolerance=None)["example_level"][0])

    def test_examples_distinct_across_senses(self):
        dup = [SenseData("verb", [ex("我喝水。"), ex("妈妈喝茶。"), ex("你喝吗？")]),
               SenseData("noun", [ex("我喝水。"), ex("他喝茶吗？"), ex("我们喝吧。")])]
        self.assertFalse(results(dup)["examples_distinct"][0])

    def test_sense_count(self):
        self.assertFalse(results([])["sense_count"][0])
        self.assertFalse(results([SenseData("", GOOD[0].examples)])["sense_count"][0])
        self.assertFalse(results([SenseData("verb", GOOD[0].examples[:2])])["sense_count"][0])
        self.assertFalse(results([SenseData("verb", GOOD[0].examples, reading="mā")])["sense_count"][0])


def lang(senses, examples, glosses=("to drink",), foreign=frozenset({"the", "of", "to", "is"})):
    c = LanguageContext("es", [s[0] for s in senses], [e[0] for e in examples], set(foreign), list(glosses))
    return {code: (ok, d) for code, ok, d in check_language(TranslationData(senses, examples), c)}


class LanguageChecksTests(SimpleTestCase):
    EXAMPLES = [(1, "我喝水。", "Yo bebo agua.", "我喝水。")]

    def test_good(self):
        r = lang([(10, "beber")], self.EXAMPLES)
        self.assertTrue(all(ok for ok, _ in r.values()), r)

    def test_translation_language(self):
        self.assertFalse(lang([(10, "to drink")], self.EXAMPLES)["translation_language"][0])
        self.assertFalse(lang([(10, "beber 喝")], self.EXAMPLES)["translation_language"][0])
        self.assertFalse(lang([(10, "hē")], self.EXAMPLES)["translation_language"][0])
        # Español con tildes y palabras que coinciden con el inglés no son fallo.
        self.assertTrue(lang([(10, "taxi")], [(1, "我喝水。", "Hola, profesor. ¿Qué tal?", "我喝水。")])["translation_language"][0])

    def test_translation_complete_and_stale(self):
        self.assertFalse(lang([(10, "")], self.EXAMPLES)["translation_complete"][0])
        stale = [(1, "我喝茶。", "Yo bebo agua.", "我喝水。")]
        r = lang([(10, "beber")], stale)
        self.assertFalse(r["translation_complete"][0])
        self.assertIn("cambió", r["translation_complete"][1])

    def test_not_third_party_copy(self):
        g = ("measure word for books, magazines",)
        self.assertFalse(lang([(10, "Measure word for books")], self.EXAMPLES, glosses=g)["not_third_party_copy"][0])
        self.assertTrue(lang([(10, "taxi")], self.EXAMPLES, glosses=("taxi",))["not_third_party_copy"][0])


class SenseReadingCheckTests(SimpleTestCase):
    def test_target_must_keep_sense_reading(self):
        c = ctx(hanzi="好")
        bad = [SenseData("verb", [ExampleData("他好吃。", "tā hǎo chī."), ExampleData("他好运动。", "tā hào yùn dòng."),
                                   ExampleData("他好学。", "tā hào xué.")], reading="hào")]
        r = {code: (ok, d) for code, ok, d in check_base(bad, c)}
        self.assertFalse(r["example_pinyin_matches"][0])
        self.assertIn("no se lee 'hào'", r["example_pinyin_matches"][1])


class SyllabusReadingCheckTests(SimpleTestCase):
    def test_single_char_entry_keeps_its_syllabus_reading(self):
        # 只 como entrada "zhǐ" (adverbio): un ejemplo con el clasificador zhī no la ilustra.
        c = ctx(hanzi="只")
        c.syllabus_pinyin = "zhǐ"
        bad = [SenseData("adverb", [ex("我只有一个。"), ExampleData("我有一只猫。", "wǒ yǒu yì zhī māo."), ex("他只喝水。")])]
        r = {code: (ok, d) for code, ok, d in check_base(bad, c)}
        self.assertFalse(r["example_pinyin_matches"][0])
        self.assertIn("ejemplo 2", r["example_pinyin_matches"][1])

    def test_yi_bu_are_left_to_tone_sandhi(self):
        c = ctx(hanzi="不")
        c.syllabus_pinyin = "bù"
        good = [SenseData("adverb", [ex("我不去。"), ex("他不喝茶。"), ex("你不是学生吗？")])]
        r = {code: (ok, d) for code, ok, d in check_base(good, c)}
        self.assertTrue(r["example_pinyin_matches"][0], r["example_pinyin_matches"][1])
