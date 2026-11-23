from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from content.models import (
    AudioAsset, Example, ExampleTranslation, LanguageContentVersion, Origin, Sense, SenseTranslation,
    ThirdPartyGloss, Word, WordBaseVersion,
)
from content.pipeline.pinyin import a_pinyin
from content.services.environment import text_hash
from ops.models import Parameter

VOICE = "test-voice"
HSK1 = [("我", "wǒ"), ("你", "nǐ"), ("水", "shuǐ"), ("茶", "chá"), ("妈妈", "māma"), ("吗", "ma"), ("喝", "hē"),
        ("好", "hǎo"), ("很", "hěn"), ("他", "tā"), ("看", "kàn"), ("书", "shū"), ("人", "rén")]


def setup_syllabus():
    Parameter.objects.update_or_create(key="content.audio_voice", defaults={"value": VOICE})
    words = {}
    for i, (h, p) in enumerate(HSK1, start=1):
        words[h] = Word.objects.create(hanzi=h, pinyin=p, hsk_level=1, syllabus_order=i)
    ThirdPartyGloss.objects.create(word=words["喝"], source="test", position=0, pos_raw="verb", gloss="to drink")
    return words


def add_audio(*texts):
    for t in texts:
        AudioAsset.objects.get_or_create(text_hash=text_hash(t), spoken_language="zh", voice=VOICE,
                                         defaults={"text": t, "file": f"zh/{VOICE}/{text_hash(t)}.mp3"})


GOOD_EXAMPLES = ["我喝水。", "妈妈喝茶。", "你喝吗？"]
GOOD_TRANSLATIONS = ["Yo bebo agua.", "Mamá bebe té.", "¿Tú bebes?"]


def make_base(word, examples=GOOD_EXAMPLES, pos="verb", origin=Origin.GENERATED, audio=True):
    base = WordBaseVersion.objects.create(word=word, origin=origin)
    sense = Sense.objects.create(base_version=base, position=0, pos=pos)
    for i, zh in enumerate(examples):
        Example.objects.create(sense=sense, position=i, text_zh=zh, pinyin=a_pinyin(zh))
    if audio:
        add_audio(word.hanzi, *examples)
    return base


def make_language(base, code="es", meaning="beber", translations=GOOD_TRANSLATIONS):
    lcv = LanguageContentVersion.objects.create(word=base.word, language_id=code, base_version=base, origin=Origin.GENERATED)
    for s in base.senses.all():
        SenseTranslation.objects.create(language_version=lcv, sense=s, text=meaning)
        for e, t in zip(s.examples.order_by("position"), translations):
            ExampleTranslation.objects.create(language_version=lcv, example=e, text=t, source_text=e.text_zh)
    return lcv


def editor():
    user = get_user_model().objects.create_user(email="editor@example.com", password="x", username="editor")
    user.user_permissions.add(Permission.objects.get(codename="manage_content"))
    return get_user_model().objects.get(pk=user.pk)
