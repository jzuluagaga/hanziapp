"""
Ejecuta las validaciones de 08-contenido.md §3 sobre una versión y guarda el
resultado (R-CON-06: se vuelven a ejecutar cada vez que el borrador se edita).
"""
from __future__ import annotations

from django.db import transaction

from ..models import (
    Example, LanguageContentVersion, ThirdPartyGloss, ValidationResult, WordBaseVersion,
)
from ..pipeline.checks import (
    BASE_CODES, LANGUAGE_CODES, BaseContext, ExampleData, LanguageContext, SenseData,
    TranslationData, check_base, check_language,
)
from ..pipeline.pinyin import a_pinyin
from .environment import ContentEnvironment, build_environment


def target_reading(word, reading: str) -> str:
    """
    Lectura de la palabra en los ejemplos de una acepción: la propia de la acepción
    o, en palabras de un carácter, la de su entrada del sílabo (得 dé / děi / de son
    entradas distintas). 一 y 不 se dejan a las reglas de cambio de tono.
    """
    if reading:
        return reading
    if len(word.hanzi) == 1 and word.hanzi not in "一不":
        return word.pinyin
    if len(word.hanzi) == 2:
        return word.pinyin  # ya está en el léxico; sirve cuando el ejemplo la separa (理一次发)
    return ""


def example_pinyin(text_zh: str, word, reading: str, env: ContentEnvironment) -> str:
    """Pinyin canónico de un ejemplo: léxico del sílabo + lectura de la palabra en esa acepción."""
    r = target_reading(word, reading)
    # La lectura propia de una acepción vale también dentro de compuestos (好学 hàoxué);
    # la del sílabo, solo cuando la palabra aparece sola (前边 sigue siendo qiánbian).
    return a_pinyin(text_zh, env.pinyin_lexicon, target=(word.hanzi, r) if r else None,
                    target_in_compounds=bool(reading))


def _base_data(version: WordBaseVersion) -> list[SenseData]:
    senses = version.senses.prefetch_related("examples").order_by("position")
    return [
        SenseData(
            pos=s.pos, reading=s.reading, ref=s.pk,
            examples=[ExampleData(e.text_zh, e.pinyin, e.pk) for e in s.examples.order_by("position")],
        )
        for s in senses
    ]


def base_context(version: WordBaseVersion, env: ContentEnvironment, senses: list[SenseData]) -> BaseContext:
    word = version.word
    texts = [word.hanzi] + [e.text_zh for s in senses for e in s.examples]
    return BaseContext(
        hanzi=word.hanzi,
        syllabus_pinyin=word.pinyin,
        hsk_level=word.hsk_level,
        allowed_words=env.allowed_words(word.hsk_level),
        known_words=env.known_words,
        max_chars=env.level_param(env.max_chars, word.hsk_level),
        level_tolerance=env.level_param(env.level_tolerance, word.hsk_level),
        max_similarity=env.max_similarity,
        examples_per_sense=env.examples_per_sense,
        audio_voice=env.audio_voice,
        audio_texts=env.audio_texts(texts),
    )


@transaction.atomic
def validate_base(version: WordBaseVersion, env: ContentEnvironment | None = None) -> list[ValidationResult]:
    env = env or build_environment()
    senses = _base_data(version)
    results = check_base(senses, base_context(version, env, senses))
    version.validations.all().delete()
    return ValidationResult.objects.bulk_create(
        [ValidationResult(base_version=version, code=c, passed=p, detail=d) for c, p, d in results]
    )


@transaction.atomic
def validate_language(version: LanguageContentVersion, env: ContentEnvironment | None = None) -> list[ValidationResult]:
    env = env or build_environment()
    base = version.base_version
    sense_ids = list(base.senses.order_by("position").values_list("pk", flat=True))
    examples = list(Example.objects.filter(sense__base_version=base).order_by("sense__position", "position"))
    current = {e.pk: e.text_zh for e in examples}
    data = TranslationData(
        senses=[(t.sense_id, t.text) for t in version.sense_translations.all()],
        examples=[
            (t.example_id, current.get(t.example_id), t.text, t.source_text)
            for t in version.example_translations.all()
        ],
    )
    ctx = LanguageContext(
        language_code=version.language_id,
        sense_refs=sense_ids,
        example_refs=[e.pk for e in examples],
        foreign_words=env.foreign_words(version.language_id),
        glosses=list(ThirdPartyGloss.objects.filter(word=version.word).values_list("gloss", flat=True)),
    )
    results = check_language(data, ctx)
    version.validations.all().delete()
    return ValidationResult.objects.bulk_create(
        [ValidationResult(language_version=version, code=c, passed=p, detail=d) for c, p, d in results]
    )


def failed_codes(version) -> list[str]:
    """Códigos fallidos o ausentes de la última validación guardada."""
    expected = BASE_CODES if isinstance(version, WordBaseVersion) else LANGUAGE_CODES
    passed = {v.code for v in version.validations.all() if v.passed}
    return [c for c in expected if c not in passed]
