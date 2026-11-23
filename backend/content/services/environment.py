"""
Datos compartidos que necesitan la generación y las validaciones: vocabulario
del sílabo, léxico de pinyin, parámetros por nivel y audio disponible. Se
calcula una vez por comando y se pasa a cada palabra.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from languages.models import Language
from ops.services import get_param

from ..models import AudioAsset, Word
from ..pipeline.pinyin import syllabus_lexicon


@dataclass
class ContentEnvironment:
    words_by_level: dict[int, set[str]]
    known_words: set[str]
    pinyin_lexicon: dict[str, list[str]]
    max_chars: dict[str, int]
    level_tolerance: dict[str, int]
    max_similarity: float
    examples_per_sense: int
    audio_voice: str | None
    audio_hashes: set[str]
    function_words: dict[str, set[str]]

    def allowed_words(self, level: int) -> set[str]:
        out: set[str] = set()
        for lvl, words in self.words_by_level.items():
            if lvl <= level:
                out |= words
        return out

    def level_param(self, mapping: dict[str, int], level: int) -> int | None:
        value = mapping.get(str(level))
        return int(value) if value is not None else None

    def audio_texts(self, texts: list[str]) -> set[str]:
        return {t for t in texts if text_hash(t) in self.audio_hashes}

    def foreign_words(self, language_code: str) -> set[str]:
        own = self.function_words.get(language_code, set())
        others: set[str] = set()
        for code, words in self.function_words.items():
            if code != language_code:
                others |= words
        return others - own


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_environment() -> ContentEnvironment:
    # Por nivel: si una palabra está en dos niveles con lecturas distintas (结果 jiéguǒ HSK 4 /
    # jiēguǒ HSK 6), el léxico usa la del nivel más bajo; la otra entrada la fija como objetivo.
    words = list(Word.objects.filter(retired_at__isnull=True)
                 .order_by("hsk_level", "syllabus_order").values_list("hanzi", "pinyin", "hsk_level"))
    by_level: dict[int, set[str]] = {}
    for hanzi, _, level in words:
        by_level.setdefault(level, set()).add(hanzi)
    voice = get_param("content.audio_voice", None)
    hashes = set(
        AudioAsset.objects.filter(spoken_language="zh", voice=voice).values_list("text_hash", flat=True)
    ) if voice else set()
    return ContentEnvironment(
        words_by_level=by_level,
        known_words={h for h, _, _ in words},
        pinyin_lexicon=syllabus_lexicon((h, p) for h, p, _ in words),
        max_chars=get_param("content.example_max_chars", {}),
        level_tolerance=get_param("content.example_level_tolerance", {}),
        max_similarity=float(get_param("content.examples_max_similarity", 0.75)),
        examples_per_sense=int(get_param("content.examples_per_sense", 3)),
        audio_voice=voice,
        audio_hashes=hashes,
        function_words={
            lang.code: {w.lower() for w in (lang.function_words or [])}
            for lang in Language.objects.all()
        },
    )
