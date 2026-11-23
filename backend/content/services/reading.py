"""
Lecturas de contenido para estudiantes (09-arquitectura.md §5).

Todo lo de aquí consulta solo versiones publicadas: un borrador no puede
filtrarse por un descuido en una consulta. Una palabra está publicada en un
idioma si su base y su contenido en ese idioma están publicados y el contenido
traduce esa base (R-CON-04, R-IDI-06). La glosa de terceros nunca sale de aquí
(R-CON-02).
"""
from __future__ import annotations

import re
import unicodedata
from collections import defaultdict

from django.conf import settings

from ops.services import get_param

from ..models import (
    AudioAsset, Character, Example, ExampleTranslation, LanguageContentVersion, Sense, SenseTranslation,
    VersionStatus, Word,
)
from .environment import text_hash

HAN = re.compile(r"[㐀-鿿豈-﫿]")


def characters_of(hanzi: str) -> list[str]:
    seen: list[str] = []
    for ch in hanzi:
        if HAN.match(ch) and ch not in seen:
            seen.append(ch)
    return seen


def chars_without_strokes(chars) -> set[str]:
    return set(Character.objects.filter(char__in=list(chars), has_stroke_data=False).values_list("char", flat=True))


def _published_versions(lang: str, word_ids=None):
    qs = LanguageContentVersion.objects.filter(
        language_id=lang, status=VersionStatus.PUBLISHED,
        base_version__status=VersionStatus.PUBLISHED, word__retired_at__isnull=True,
    )
    if word_ids is not None:
        qs = qs.filter(word_id__in=list(word_ids))
    return qs


def published_word_ids(lang: str, word_ids=None) -> set[int]:
    return set(_published_versions(lang, word_ids).values_list("word_id", flat=True))


def syllabus_totals() -> dict[int, int]:
    out = {n: 0 for n in range(1, 7)}
    for level in Word.objects.filter(retired_at__isnull=True).values_list("hsk_level", flat=True):
        out[level] += 1
    return out


def published_counts(lang: str) -> dict[int, int]:
    out = {n: 0 for n in range(1, 7)}
    for level in _published_versions(lang).values_list("word__hsk_level", flat=True):
        out[level] += 1
    return out


# ───────────────────────────── Audio (R-CON-13, R-IDI-08)

def _audio_url(file: str) -> str:
    if file.startswith("tts:") or file.startswith("http"):
        return file  # `tts:` solo existe en desarrollo (dev_publish_sample)
    return f"{settings.AUDIO_BASE_URL.rstrip('/')}/{file}" if settings.AUDIO_BASE_URL else file


def audio_urls(texts) -> dict[str, str]:
    """Audio en chino por texto; prefiere la voz vigente."""
    texts = [t for t in set(texts) if t]
    if not texts:
        return {}
    voice = get_param("content.audio_voice", None)
    by_hash = {text_hash(t): t for t in texts}
    found: dict[str, tuple[bool, str]] = {}
    for a in AudioAsset.objects.filter(text_hash__in=list(by_hash), spoken_language="zh"):
        text = by_hash[a.text_hash]
        preferred = a.voice == voice
        if text not in found or (preferred and not found[text][0]):
            found[text] = (preferred, _audio_url(a.file))
    return {t: url for t, (_, url) in found.items()}


def words_with_audio(word_ids) -> set[int]:
    words = dict(Word.objects.filter(pk__in=list(word_ids)).values_list("pk", "hanzi"))
    urls = audio_urls(words.values())
    return {pk for pk, hanzi in words.items() if hanzi in urls}


# ───────────────────────────── Fichas

def _syllabus_payload(w: Word) -> dict:
    return {
        "id": str(w.pk), "hanzi": w.hanzi, "pinyin": w.pinyin, "level": w.hsk_level, "order": w.syllabus_order,
        "editorial": "in_review", "senses": [], "examples": [], "characters": characters_of(w.hanzi), "audio": None,
    }


def word_payloads(word_ids, lang: str) -> dict[int, dict]:
    """Ficha de cada palabra (Docs/10-api.md §5), con pocas consultas."""
    word_ids = list(word_ids)
    words = {w.pk: w for w in Word.objects.filter(pk__in=word_ids)}
    out = {pk: _syllabus_payload(w) for pk, w in words.items()}
    versions = {v.word_id: v for v in _published_versions(lang, word_ids).only("pk", "word_id", "base_version_id")}
    if not versions:
        return out
    base_ids = [v.base_version_id for v in versions.values()]
    senses = defaultdict(list)
    for s in Sense.objects.filter(base_version_id__in=base_ids).order_by("base_version_id", "position"):
        senses[s.base_version_id].append(s)
    examples = defaultdict(list)
    for e in Example.objects.filter(sense__base_version_id__in=base_ids).order_by("sense__position", "position"):
        examples[e.sense_id].append(e)
    lv_ids = [v.pk for v in versions.values()]
    sense_tr = {(t.language_version_id, t.sense_id): t.text for t in SenseTranslation.objects.filter(language_version_id__in=lv_ids)}
    ex_tr = {(t.language_version_id, t.example_id): t.text for t in ExampleTranslation.objects.filter(language_version_id__in=lv_ids)}
    texts = [words[pk].hanzi for pk in versions] + [e.text_zh for lst in examples.values() for e in lst]
    audio = audio_urls(texts)
    for pk, v in versions.items():
        p = out[pk]
        p["editorial"] = "published"
        p["audio"] = audio.get(words[pk].hanzi)
        for s in senses[v.base_version_id]:
            p["senses"].append({"pos": s.pos, "meaning": sense_tr.get((v.pk, s.pk), ""), "reading": s.reading})
            for e in examples[s.pk]:
                p["examples"].append({"zh": e.text_zh, "pinyin": e.pinyin, "translation": ex_tr.get((v.pk, e.pk), ""),
                                      "audio": audio.get(e.text_zh)})
    return out


def first_meanings(word_ids, lang: str) -> dict[int, str]:
    """Primer significado publicado de cada palabra, para listas y opciones de escucha."""
    out: dict[int, str] = {}
    rows = SenseTranslation.objects.filter(
        language_version__in=_published_versions(lang, word_ids),
    ).order_by("language_version__word_id", "sense__position").values_list("language_version__word_id", "text")
    for word_id, text in rows:
        out.setdefault(word_id, text)
    return out


# ───────────────────────────── Búsqueda (HU-E07-01, R-IDI-07)

def normalize(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower()).replace("ü", "u")
    return "".join(c for c in s if unicodedata.category(c) != "Mn").strip()


def _compact(s: str) -> str:
    return re.sub(r"[\s'’·\-0-9]", "", normalize(s))


def search(q: str, lang: str, limit: int = 50) -> tuple[str, list[int]]:
    """Devuelve el tipo de consulta y los ids ordenados por relevancia."""
    q = q.strip()
    if not q:
        return "meaning", []
    if HAN.search(q):
        ids = list(Word.objects.filter(retired_at__isnull=True, hanzi__contains=q)
                   .order_by("hsk_level", "syllabus_order").values_list("pk", flat=True)[:limit])
        return "hanzi", ids

    exact_py = q.lower().replace(" ", "")
    qc, qm = _compact(q), normalize(q)
    scores: dict[int, tuple[int, int, int]] = {}
    pinyin_hit = False
    for pk, py, level, order in Word.objects.filter(retired_at__isnull=True).values_list(
            "pk", "pinyin", "hsk_level", "syllabus_order"):
        score = 0
        if py.lower().replace(" ", "").replace("'", "") == exact_py:
            score = 100
        elif _compact(py) == qc:
            score = 80
        elif len(qc) >= 2 and _compact(py).startswith(qc):
            score = 50
        if score:
            pinyin_hit = True
            scores[pk] = (score, level, order)
    if len(qm) >= 2:
        rows = SenseTranslation.objects.filter(language_version__in=_published_versions(lang)).values_list(
            "language_version__word_id", "text", "language_version__word__hsk_level",
            "language_version__word__syllabus_order")
        for pk, text, level, order in rows:
            t = normalize(text)
            parts = [p.strip() for p in re.split(r"[;,()]", t)]
            score = 90 if qm in parts else (40 if qm in t else 0)
            if score and score > scores.get(pk, (0,))[0]:
                scores[pk] = (score, level, order)
    ranked = sorted(scores, key=lambda pk: (-scores[pk][0], scores[pk][1], scores[pk][2]))
    kind = "pinyin" if pinyin_hit and all(scores[pk][0] in (100, 80, 50) for pk in ranked[:1]) else "meaning"
    return kind, ranked[:limit]
