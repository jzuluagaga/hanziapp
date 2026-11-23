"""Utilidades para las pruebas de los módulos de estudio."""
from __future__ import annotations

import uuid
from contextlib import contextmanager
from datetime import datetime, timezone as dt_timezone
from unittest import mock

from django.utils import timezone
from rest_framework.test import APIClient

from content.models import (
    AudioAsset, Example, ExampleTranslation, LanguageContentVersion, Origin, Sense, SenseTranslation,
    ThirdPartyGloss, VersionStatus, Word, WordBaseVersion,
)
from content.services.environment import text_hash
from decks.services import build_system_decks
from ops import params
from ops.models import Parameter

HANZI = "爱八爸杯北本不菜茶吃出大的点电东都读对多儿二饭飞分服高个工狗汉好号喝和很后话回会火鸡几家叫姐今九开看块来老了冷里六吗买猫么没妹门们米名明那男你年娘牛女朋漂苹七钱前请去热人认日三商上少谁什生师十时是书水睡说四岁他她太天听同外玩我五午西喜下先现想小些写谢星学一衣医椅有雨语月在再怎张这中钟住字子昨作坐做"


def set_param(key, value):
    Parameter.objects.update_or_create(key=key, defaults={"value": value})
    params.forget(key)


def make_word(level: int, order: int, hanzi: str, *, publish: str | None = "es", audio: bool = True,
              meaning: str | None = None, examples: int = 1, gloss: str | None = None) -> Word:
    word = Word.objects.create(hanzi=hanzi, pinyin=f"py{level}{order}", hsk_level=level, syllabus_order=order)
    if gloss:
        ThirdPartyGloss.objects.create(word=word, source="test", position=0, gloss=gloss)
    if publish:
        publish_word(word, publish, audio=audio, meaning=meaning, examples=examples)
    return word


def publish_word(word: Word, lang: str = "es", *, audio: bool = True, meaning: str | None = None, examples: int = 1):
    base = word.base_versions.filter(status=VersionStatus.PUBLISHED).first()
    if base is None:
        base = WordBaseVersion.objects.create(word=word, origin=Origin.MANUAL, status=VersionStatus.PUBLISHED,
                                              published_at=timezone.now())
        sense = Sense.objects.create(base_version=base, position=0, pos="n")
        for i in range(examples):
            Example.objects.create(sense=sense, position=i, text_zh=f"{word.hanzi}好{i}。", pinyin="x")
    lcv = LanguageContentVersion.objects.create(word=word, language_id=lang, base_version=base, origin=Origin.MANUAL,
                                                status=VersionStatus.PUBLISHED, published_at=timezone.now())
    for s in base.senses.all():
        SenseTranslation.objects.create(language_version=lcv, sense=s, text=meaning or f"{lang}-{word.hanzi}")
        for e in s.examples.all():
            ExampleTranslation.objects.create(language_version=lcv, example=e, text=f"{lang} ej {e.position}",
                                              source_text=e.text_zh)
    if audio:
        for t in [word.hanzi] + [e.text_zh for s in base.senses.all() for e in s.examples.all()]:
            AudioAsset.objects.get_or_create(text_hash=text_hash(t), spoken_language="zh", voice="v",
                                             defaults={"text": t, "file": f"zh/v/{text_hash(t)}.mp3"})
    return lcv


def make_level(level: int, n: int, *, start: int = 0, **kw) -> list[Word]:
    return [make_word(level, i + 1, HANZI[(start + i) % len(HANZI)] + ("" if start + i < len(HANZI) else str(i)), **kw)
            for i in range(n)]


def student(email="ana@example.com", *, cohort="", name="Ana", tz="America/Bogota"):
    from users.services import register

    return register(name=name, email=email, password="clave-segura-123", policy_version=params.value("data_policy_version"),
                    is_adult=True, cohort=cohort, tz=tz)


def client_for(user=None) -> APIClient:
    c = APIClient()
    if user is not None:
        c.force_authenticate(user)
    return c


def setup_catalog(level1=30, level2=10, level3=5):
    words = {1: make_level(1, level1), 2: make_level(2, level2, start=level1), 3: make_level(3, level3, start=level1 + level2)}
    build_system_decks()
    return words


@contextmanager
def at(when: datetime):
    """Fija la hora del servidor."""
    if when.tzinfo is None:
        when = when.replace(tzinfo=dt_timezone.utc)
    with mock.patch("django.utils.timezone.now", return_value=when):
        yield when


def answer(client, session: dict, position: int | None = None, grade: str = "pass", **extra):
    pos = session["position"] if position is None else position
    card = next(c for c in session["cards"] if c["position"] == pos)
    body = {"client_id": str(uuid.uuid4()), "session_id": session["id"], "position": pos, "unit": card["unit"],
            "grade": grade, **extra}
    return client.post("/api/v1/answers", body, format="json")


def start(client, skill="recognition", deck_id=None, **extra):
    scope = {"type": "deck", "deck_id": str(deck_id)} if deck_id else {"type": "all_due"}
    return client.post("/api/v1/sessions", {"scope": scope, "skill": skill, **extra}, format="json")
