"""
Validaciones automáticas de un borrador (08-contenido.md §3). Cada una tiene
el código que ve el editor. Son funciones puras: reciben los datos del
borrador y su contexto y devuelven (código, aprobada, detalle).

Capa base: word_in_example, example_hanzi_only, example_pinyin_matches,
example_length, example_level, examples_distinct, sense_count, audio_present.
Capa de idioma: translation_language, translation_complete, not_third_party_copy.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any

from ..pos import POS_KEYS
from .pinyin import (
    CHINESE_PUNCTUATION, is_chinese_char, pinyin_mismatches, split_syllables, split_word_pinyin,
)
from .vocabulary import out_of_level_words

Result = tuple[str, bool, str]

BASE_CODES = [
    "word_in_example", "example_hanzi_only", "example_pinyin_matches", "example_length",
    "example_level", "examples_distinct", "sense_count", "audio_present",
]
LANGUAGE_CODES = ["translation_language", "translation_complete", "not_third_party_copy"]


@dataclass
class ExampleData:
    text_zh: str
    pinyin: str = ""
    ref: Any = None


@dataclass
class SenseData:
    pos: str
    examples: list[ExampleData]
    reading: str = ""
    ref: Any = None


@dataclass
class BaseContext:
    hanzi: str
    hsk_level: int
    allowed_words: set[str]          # palabras del sílabo de ese nivel o inferiores
    known_words: set[str]            # todas las palabras del sílabo cargadas
    max_chars: int | None            # content.example_max_chars[nivel]
    level_tolerance: int | None      # content.example_level_tolerance[nivel]
    max_similarity: float = 0.75     # content.examples_max_similarity
    examples_per_sense: int = 3      # content.examples_per_sense
    audio_voice: str | None = None   # content.audio_voice
    audio_texts: set[str] = field(default_factory=set)  # textos con audio en esa voz
    syllabus_pinyin: str = ""       # pinyin del sílabo de esta entrada


@dataclass
class TranslationData:
    senses: list[tuple[Any, str]]                 # (ref de la acepción, significado)
    examples: list[tuple[Any, str, str, str]]     # (ref del ejemplo, chino actual, traducción, chino traducido)


@dataclass
class LanguageContext:
    language_code: str
    sense_refs: list[Any]            # acepciones de la base que debe traducir
    example_refs: list[Any]          # ejemplos de la base que debe traducir
    foreign_words: set[str]          # palabras funcionales de otros idiomas que no son del propio
    glosses: list[str]               # glosas de terceros de la palabra


def _hanzi_count(text: str) -> int:
    return sum(1 for c in text if is_chinese_char(c))


def _fmt(items: list[str], limit: int = 6) -> str:
    extra = f" (+{len(items) - limit} más)" if len(items) > limit else ""
    return "; ".join(items[:limit]) + extra


def _target_read_as(hanzi: str, reading: str, example: ExampleData) -> bool:
    """¿Alguna aparición de la palabra se lee, en el pinyin del ejemplo, con la lectura de la acepción?"""
    want = split_word_pinyin(hanzi, reading)
    chars = [c for c in example.text_zh if is_chinese_char(c)]
    syls = split_syllables(example.pinyin)
    if not want or len(chars) != len(syls):
        return True  # con erhua no se puede alinear carácter a carácter; lo cubre pinyin_mismatches
    def same(got: str, exp: str) -> bool:
        # El tono neutro de la misma sílaba es su lectura átona (外边 wàibian), no otra palabra.
        return got == exp or (got[:-1] == exp[:-1] and got.endswith("5"))

    text = "".join(chars)
    start = text.find(hanzi)
    while start >= 0:
        got = syls[start:start + len(hanzi)]
        if len(got) == len(want) and all(same(g, w) for g, w in zip(got, want)):
            return True
        start = text.find(hanzi, start + 1)
    return False


def _all_examples(senses: list[SenseData]):
    for si, s in enumerate(senses):
        for ei, e in enumerate(s.examples):
            yield si, ei, e


def check_base(senses: list[SenseData], ctx: BaseContext) -> list[Result]:
    results: list[Result] = []

    # word_in_example
    bad = [f"acepción {si + 1}, ejemplo {ei + 1}" for si, ei, e in _all_examples(senses) if ctx.hanzi not in e.text_zh]
    results.append(("word_in_example", not bad, f"No contienen '{ctx.hanzi}': {_fmt(bad)}" if bad else ""))

    # example_hanzi_only
    bad = []
    for si, ei, e in _all_examples(senses):
        extra = sorted({c for c in e.text_zh if not is_chinese_char(c) and c not in CHINESE_PUNCTUATION})
        if extra:
            bad.append(f"acepción {si + 1}, ejemplo {ei + 1}: {' '.join(repr(c) for c in extra)}")
    results.append(("example_hanzi_only", not bad, f"Caracteres no permitidos (solo hanzi y puntuación china): {_fmt(bad)}" if bad else ""))

    # example_pinyin_matches
    bad = []
    for si, ei, e in _all_examples(senses):
        if not e.pinyin.strip():
            bad.append(f"acepción {si + 1}, ejemplo {ei + 1}: sin pinyin")
            continue
        problems = pinyin_mismatches(e.text_zh, e.pinyin)
        reading = senses[si].reading or (
            ctx.syllabus_pinyin if len(ctx.hanzi) == 1 and ctx.hanzi not in "一不" else ""
        )
        if not problems and reading and not _target_read_as(ctx.hanzi, reading, e):
            problems = [f"'{ctx.hanzi}' no se lee '{reading}' en este ejemplo (¿forma otra palabra?)"]
        if problems:
            bad.append(f"acepción {si + 1}, ejemplo {ei + 1}: {', '.join(problems)}")
    results.append(("example_pinyin_matches", not bad, _fmt(bad) if bad else ""))

    # example_length
    if ctx.max_chars is None:
        results.append(("example_length", False, f"Falta fijar content.example_max_chars para HSK {ctx.hsk_level}"))
    else:
        bad = [
            f"acepción {si + 1}, ejemplo {ei + 1}: {_hanzi_count(e.text_zh)} caracteres"
            for si, ei, e in _all_examples(senses) if _hanzi_count(e.text_zh) > ctx.max_chars
        ]
        results.append(("example_length", not bad, f"Superan {ctx.max_chars} caracteres: {_fmt(bad)}" if bad else ""))

    # example_level
    if ctx.level_tolerance is None:
        results.append(("example_level", False, f"Falta fijar content.example_level_tolerance para HSK {ctx.hsk_level}"))
    else:
        bad = []
        for si, ei, e in _all_examples(senses):
            outside = out_of_level_words(e.text_zh, ctx.hanzi, ctx.allowed_words, ctx.known_words)
            if len(outside) > ctx.level_tolerance:
                bad.append(f"acepción {si + 1}, ejemplo {ei + 1}: {'、'.join(outside)}")
        results.append((
            "example_level", not bad,
            f"Más de {ctx.level_tolerance} palabra(s) por encima de HSK {ctx.hsk_level}: {_fmt(bad)}" if bad else "",
        ))

    # examples_distinct (todos los ejemplos de la palabra, entre acepciones)
    flat = [(si, ei, e.text_zh.replace(ctx.hanzi, "＊")) for si, ei, e in _all_examples(senses)]
    bad = []
    for i in range(len(flat)):
        for j in range(i + 1, len(flat)):
            ratio = SequenceMatcher(None, flat[i][2], flat[j][2]).ratio()
            if ratio > ctx.max_similarity:
                bad.append(
                    f"acepción {flat[i][0] + 1} ej. {flat[i][1] + 1} ≈ acepción {flat[j][0] + 1} ej. {flat[j][1] + 1} ({ratio:.2f})"
                )
    results.append(("examples_distinct", not bad, f"Ejemplos con la misma plantilla: {_fmt(bad)}" if bad else ""))

    # sense_count
    bad = []
    if not senses:
        bad.append("no hay acepciones")
    for si, s in enumerate(senses):
        if s.pos not in POS_KEYS:
            bad.append(f"acepción {si + 1}: sin categoría gramatical")
        if s.reading and split_word_pinyin(ctx.hanzi, s.reading) is None:
            bad.append(f"acepción {si + 1}: la lectura '{s.reading}' no corresponde a '{ctx.hanzi}'")
        if len(s.examples) != ctx.examples_per_sense:
            bad.append(f"acepción {si + 1}: {len(s.examples)} ejemplos (se esperan {ctx.examples_per_sense})")
    results.append(("sense_count", not bad, _fmt(bad) if bad else ""))

    # audio_present
    if not ctx.audio_voice:
        results.append(("audio_present", False, "No hay voz configurada (content.audio_voice) ni audio generado"))
    else:
        missing = [t for t in [ctx.hanzi] + [e.text_zh for _, _, e in _all_examples(senses)] if t not in ctx.audio_texts]
        results.append(("audio_present", not missing, f"Sin audio: {_fmt(missing)}" if missing else ""))

    return results


# ---------------------------------------------------------------------------
# Capa de idioma
# ---------------------------------------------------------------------------

_PINYIN_MARKS = set("āēīōūǖǎěǐǒǔǚǘǜ")  # macrón y carón: ningún idioma de estudio los usa
_WORD_RE = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*", re.UNICODE)  # "Xi'an" es una palabra


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text)).strip()


def check_language(data: TranslationData, ctx: LanguageContext) -> list[Result]:
    results: list[Result] = []
    texts = [("significado", t) for _, t in data.senses] + [("traducción", t) for _, _, t, _ in data.examples]

    # translation_language
    bad = []
    for kind, text in texts:
        if any(is_chinese_char(c) for c in text):
            bad.append(f"{kind} con caracteres chinos: {text!r}")
        elif _PINYIN_MARKS & set(text):
            bad.append(f"{kind} con pinyin: {text!r}")
        else:
            leaked = sorted({w for w in _WORD_RE.findall(text.lower()) if w in ctx.foreign_words})
            if leaked:
                bad.append(f"{kind} con palabras de otro idioma ({', '.join(leaked)}): {text!r}")
    results.append(("translation_language", not bad, _fmt(bad) if bad else ""))

    # translation_complete
    bad = []
    by_sense = {ref: t for ref, t in data.senses}
    by_example = {ref: (cur, t, src) for ref, cur, t, src in data.examples}
    for i, ref in enumerate(ctx.sense_refs):
        if not by_sense.get(ref, "").strip():
            bad.append(f"acepción {i + 1} sin significado")
    for i, ref in enumerate(ctx.example_refs):
        cur, t, src = by_example.get(ref, (None, "", ""))
        if not t.strip():
            bad.append(f"ejemplo {i + 1} sin traducción")
        elif cur is not None and src != cur:
            bad.append(f"ejemplo {i + 1}: el chino cambió después de traducirlo ({src!r} → {cur!r})")
    results.append(("translation_complete", not bad, _fmt(bad) if bad else ""))

    # not_third_party_copy: copia literal de una frase de la glosa. Una o dos
    # palabras iguales ("taxi", "hospital") no son copia de una redacción ajena.
    phrases = {_normalize(p) for g in ctx.glosses for p in re.split(r"[;,()]", g) if p.strip()}
    phrases = {p for p in phrases if p}
    bad = []
    for _, meaning in data.senses:
        m = _normalize(meaning)
        for p in phrases:
            n = len(p.split())
            if (n >= 3 and p in m) or (n >= 2 and m == p):
                bad.append(f"{meaning!r} copia la glosa {p!r}")
                break
    results.append(("not_third_party_copy", not bad, _fmt(bad) if bad else ""))

    return results
