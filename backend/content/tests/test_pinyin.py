from django.test import SimpleTestCase

from content.pipeline.pinyin import a_pinyin, pinyin_mismatches, split_word_pinyin, syllabus_lexicon

LEX = syllabus_lexicon([
    ("学生", "xuéshēng"), ("那边", "nàbiān"), ("外边", "wàibian"), ("对不起", "duìbuqǐ"),
    ("一点儿", "yìdiǎnr"), ("女儿", "nǚ’ér"), ("衣服", "yīfu"), ("好看", "hǎokàn"),
])


class PinyinTests(SimpleTestCase):
    def check(self, zh, expected, **kw):
        self.assertEqual(a_pinyin(zh, LEX, **kw), expected)

    def test_neutral_tone_from_dictionary(self):
        self.check("爸爸妈妈", "bà ba mā ma")
        self.check("我的朋友", "wǒ de péng you")

    def test_syllabus_pinyin_wins_inside_examples(self):
        # R-CON-01: el pinyin de una palabra del sílabo es el del sílabo.
        self.check("他是学生。", "tā shì xué shēng.")
        self.check("在那边。", "zài nà biān.")
        self.check("在外边。", "zài wài bian.")
        self.check("对不起。", "duì bu qǐ.")

    def test_yi_bu_sandhi(self):
        self.check("一个人", "yí gè rén")
        self.check("一起", "yì qǐ")
        self.check("我不去。", "wǒ bú qù.")
        self.check("不好", "bù hǎo")
        self.check("好不好？", "hǎo bu hǎo?")
        self.check("第一次", "dì yī cì")
        self.check("一月一号", "yī yuè yī hào")
        self.check("十一点", "shí yī diǎn")
        self.check("看一看", "kàn yi kàn")

    def test_particles_by_function(self):
        self.check("他慢慢地走。", "tā màn màn de zǒu.")
        self.check("他跑得很快。", "tā pǎo de hěn kuài.")
        self.check("我得走了。", "wǒ děi zǒu le.")
        self.check("她穿着红裙子。", "tā chuān zhe hóng qún zi.")
        self.check("他很着急。", "tā hěn zháo jí.")
        self.check("这只猫", "zhè zhī māo")
        self.check("我只有一个。", "wǒ zhǐ yǒu yí gè.")

    def test_erhua(self):
        self.check("你去哪儿？", "nǐ qù nǎr?")
        self.check("有一点儿冷。", "yǒu yì diǎnr lěng.")
        self.check("我女儿", "wǒ nǚ ér")

    def test_punctuation_and_non_chinese_keep_alignment(self):
        self.check("他说：“你好。”", "tā shuō: \"nǐ hǎo.\"")
        self.check("我们10点见。", "wǒ men 10 diǎn jiàn.")

    def test_sense_reading_applies_to_target_only(self):
        self.check("他好运动。", "tā hào yùn dòng.", target=("好", "hào"))
        self.check("她好看。", "tā hǎo kàn.", target=("好", "hào"))

    def test_entry_reading_inside_unknown_segments(self):
        # Lectura del sílabo de una entrada de un carácter (重 chóng, 为 wéi) dentro de
        # segmentos que el diccionario no conoce; si el diccionario respalda otra
        # lectura (天空, 认为), manda el diccionario.
        kw = {"target_in_compounds": False}
        self.check("我要重写。", "wǒ yào chóng xiě.", target=("重", "chóng"), **kw)
        self.check("他被选为班长。", "tā bèi xuǎn wéi bān zhǎng.", target=("为", "wéi"), **kw)
        self.check("天空很蓝，我有空。", "tiān kōng hěn lán, wǒ yǒu kòng.", target=("空", "kòng"), **kw)
        self.check("这个箱子很重。", "zhè ge xiāng zi hěn zhòng.", target=("重", "zhòng"), **kw)

    def test_separated_target_keeps_syllabus_reading(self):
        # Verbo separable: 理发 lǐfà partido en 理一次发 sigue leyendo 发 fà.
        self.check("他每个月理一次发。", "tā měi gè yuè lǐ yí cì fà.", target=("理发", "lǐfà"))
        self.check("我去理发。", "wǒ qù lǐ fà.", target=("理发", "lǐfà"))

    def test_wei2_and_di4(self):
        self.check("大家称他为老张。", "dà jiā chēng tā wéi lǎo zhāng.")
        self.check("他被选为班长。", "tā bèi xuǎn wéi bān zhǎng.")
        self.check("他为很多人所喜爱。", "tā wéi hěn duō rén suǒ xǐ ài.")
        self.check("我为你高兴。", "wǒ wèi nǐ gāo xìng.")
        self.check("这块地很大。", "zhè kuài dì hěn dà.")
        self.check("他慢慢地走。", "tā màn màn de zǒu.")
        self.check("孩子们哈哈地笑。", "hái zi men hā hā de xiào.")
        self.check("他从小好学。", "tā cóng xiǎo hào xué.", target=("好", "hào"), target_in_compounds=False)

    def test_guo_aspect_after_negation_in_syllabus_word(self):
        lex = syllabus_lexicon([("穿过", "chuānguò")])
        self.assertEqual(a_pinyin("我还没穿过。", lex), "wǒ hái méi chuān guo.")
        self.assertEqual(a_pinyin("他穿过了沙漠。", lex), "tā chuān guò le shā mò.")

    def test_syllabus_tone_of_yi_and_potential_deliao(self):
        lex = syllabus_lexicon([("一流", "yīliú"), ("得了", "déle")])
        self.assertEqual(a_pinyin("服务是一流的。", lex), "fú wù shì yī liú de.")
        self.assertEqual(a_pinyin("你吃得了吗？", lex), "nǐ chī de liǎo ma?")
        self.assertEqual(a_pinyin("他得了第一名。", lex), "tā dé le dì yī míng.")

    def test_guo_aspect_inside_glued_segments(self):
        self.check("他当过兵，也打过仗。", "tā dāng guo bīng, yě dǎ guo zhàng.")
        self.check("他走过来了。", "tā zǒu guò lái le.")
        self.check("我们经过一个公园。", "wǒ men jīng guò yí gè gōng yuán.")

    def test_split_word_pinyin(self):
        self.assertEqual(split_word_pinyin("那边", "nàbiān"), ["na4", "bian1"])
        self.assertEqual(split_word_pinyin("一点儿", "yìdiǎnr"), ["yi4", "dian3", "er5"])
        self.assertEqual(split_word_pinyin("谁", "shéi/shuí"), ["shei2"])
        self.assertIsNone(split_word_pinyin("好", "mā"))

    def test_mismatches(self):
        self.assertEqual(pinyin_mismatches("你去哪儿？", "nǐ qù nǎr?"), [])
        self.assertTrue(pinyin_mismatches("妈", "mǎ"))
        self.assertTrue(pinyin_mismatches("我们见", "wǒ jiàn"))
        self.assertTrue(pinyin_mismatches("咖啡", "kāfēi"))  # una sílaba por carácter


class GuoParticleTests(SimpleTestCase):
    def test_guo(self):
        self.assertEqual(a_pinyin("我去过北京。"), "wǒ qù guo běi jīng.")
        self.assertEqual(a_pinyin("你吃过饺子吗？"), "nǐ chī guo jiǎo zi ma?")
        self.assertEqual(a_pinyin("我很难过。"), "wǒ hěn nán guò.")
        self.assertEqual(a_pinyin("过马路要小心。")[:2], "gu")
        self.assertIn("guò mǎ", a_pinyin("过马路要小心。"))
