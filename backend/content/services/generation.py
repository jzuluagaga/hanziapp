"""
Paso 4 de 08-contenido.md §2 (`generate_drafts`): genera borradores con la API
de Claude y los guarda con su origen "generated". Repetirlo no duplica nada
(HU-E13-02): una palabra que ya tiene contenido en ese idioma se omite, y lo
publicado nunca se toca.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone

from languages.models import Language

from ..models import (
    Example, ExampleTranslation, GenerationJob, LanguageContentVersion, Origin, Sense,
    SenseTranslation, ThirdPartyGloss, VersionStatus, Word, WordBaseVersion,
)
from ..pipeline import prompts
from ..pipeline.pinyin import split_word_pinyin
from .editorial import draft_base, draft_language, published_base, published_language
from .environment import ContentEnvironment
from .validation import example_pinyin, validate_base, validate_language

MAX_TOKENS = 16000


class GenerationError(Exception):
    pass


@dataclass
class Target:
    word: Word
    mode: str                                # "full" | "translate"
    base_version: WordBaseVersion | None     # base a traducir (modo translate)


def _replaceable(base: WordBaseVersion, language: Language, any_origin: bool) -> bool:
    """¿Se puede rehacer este borrador de base? Solo si ningún otro idioma lo usa, y
    si es importado o manual, solo cuando se pide expresamente."""
    if base.language_versions.exclude(language=language).exists():
        return False
    return any_origin or base.origin == Origin.GENERATED


def select_targets(words, language: Language, regenerate: bool = False,
                   replace_base_drafts: bool = False) -> tuple[list[Target], list[tuple[Word, str]]]:
    """
    Decide qué generar para cada palabra. Devuelve (objetivos, omitidas con motivo).

    - Sin opciones: solo palabras sin contenido en ese idioma.
    - regenerate: rehace el borrador de ese idioma (y la base si es generada).
    - replace_base_drafts: rehace también bases en borrador importadas o manuales.
    Lo publicado nunca se toca: sobre una base publicada solo se traduce.
    """
    regenerate = regenerate or replace_base_drafts
    targets, skipped = [], []
    for word in words:
        has_language = draft_language(word, language.code) or published_language(word, language.code)
        if has_language and not regenerate:
            skipped.append((word, f"ya tiene contenido en '{language.code}'"))
            continue
        b_draft, b_pub = draft_base(word), published_base(word)
        if b_draft:
            replace = regenerate and b_pub is None and _replaceable(b_draft, language, replace_base_drafts)
            targets.append(Target(word, "full", None) if replace else Target(word, "translate", b_draft))
        elif b_pub:
            targets.append(Target(word, "translate", b_pub))
        else:
            targets.append(Target(word, "full", None))
    return targets, skipped


def _system_prompt(target: Target, language: Language, env: ContentEnvironment) -> str:
    name = language.generation_name or language.name
    if target.mode == "translate":
        return prompts.translate_system_prompt(name, language.generation_style)
    level = target.word.hsk_level
    max_chars = env.level_param(env.max_chars, level)
    tolerance = env.level_param(env.level_tolerance, level)
    if max_chars is None or tolerance is None:
        raise GenerationError(
            f"Faltan content.example_max_chars / content.example_level_tolerance para HSK {level}: "
            "se fijan al preparar el nivel (08-contenido.md §3)."
        )
    allowed = sorted(env.allowed_words(level))
    return prompts.full_system_prompt(name, language.generation_style, level, allowed, max_chars, tolerance)


def build_request(target: Target, language: Language, env: ContentEnvironment, model: str,
                  effort: str | None = None) -> dict:
    word = target.word
    glosses = list(word.third_party_glosses.order_by("source", "position"))
    if target.mode == "translate":
        senses = target.base_version.senses.prefetch_related("examples").order_by("position")
        user = prompts.translate_user_message(word.hanzi, word.pinyin, word.hsk_level, glosses, senses)
        schema = prompts.TRANSLATE_SCHEMA
    else:
        homographs = Word.objects.filter(hanzi=word.hanzi, retired_at__isnull=True).exclude(pk=word.pk)
        user = prompts.full_user_message(word.hanzi, word.pinyin, word.hsk_level, glosses, homographs)
        schema = prompts.FULL_SCHEMA
    return {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "system": [{"type": "text", "text": _system_prompt(target, language, env), "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user}],
        "output_config": {
            "format": {"type": "json_schema", "schema": schema},
            **({"effort": effort} if effort else {}),
        },
    }


def custom_id(target: Target) -> str:
    return f"w{target.word.pk}-{target.mode}"


def parse_message(message) -> dict:
    """Extrae el JSON de una respuesta. Lanza GenerationError con el motivo si no sirve."""
    if message.stop_reason in ("max_tokens", "refusal"):
        raise GenerationError(f"stop_reason={message.stop_reason}")
    texts = [b.text for b in message.content if getattr(b, "type", None) == "text"]
    if not texts:
        raise GenerationError(f"sin bloque de texto (stop_reason={message.stop_reason})")
    try:
        return json.loads(texts[-1])
    except json.JSONDecodeError as e:
        raise GenerationError(f"JSON inválido: {e}") from e


@transaction.atomic
def store_full(word: Word, language: Language, data: dict, env: ContentEnvironment, meta: dict,
               replace_base_drafts: bool = False) -> LanguageContentVersion:
    word = Word.objects.select_for_update().get(pk=word.pk)
    if published_base(word):
        raise GenerationError("la palabra ya tiene base publicada: solo se puede traducir")
    old = draft_base(word)
    if old:
        if not _replaceable(old, language, replace_base_drafts):
            raise GenerationError("ya existe un borrador de base que no se puede reemplazar")
        old.language_versions.all().delete()
        old.delete()
    stale = draft_language(word, language.code)
    if stale:
        stale.delete()
    glosses = list(ThirdPartyGloss.objects.filter(word=word).order_by("source", "position"))
    base = WordBaseVersion.objects.create(word=word, origin=Origin.GENERATED, generation_meta=meta)
    lang = LanguageContentVersion.objects.create(
        word=word, language=language, base_version=base, origin=Origin.GENERATED, generation_meta=meta,
    )
    for si, s in enumerate(data.get("senses", [])):
        reading = (s.get("reading") or "").strip()
        if reading and split_word_pinyin(word.hanzi, reading) == split_word_pinyin(word.hanzi, word.pinyin):
            reading = ""  # igual que el sílabo: no hace falta
        gi = s.get("source_gloss", -1)
        sense = Sense.objects.create(
            base_version=base, position=si, pos=s.get("pos", ""), reading=reading,
            source_gloss=glosses[gi - 1] if isinstance(gi, int) and 1 <= gi <= len(glosses) else None,
        )
        SenseTranslation.objects.create(language_version=lang, sense=sense, text=(s.get("meaning") or "").strip())
        # El modelo a veces devuelve un ejemplo vacío además de los tres pedidos: se descarta.
        examples = [ex for ex in s.get("examples", []) if (ex.get("zh") or "").strip()]
        for ei, ex in enumerate(examples):
            zh = (ex.get("zh") or "").strip()
            example = Example.objects.create(
                sense=sense, position=ei, text_zh=zh, pinyin=example_pinyin(zh, word, reading, env),
            )
            ExampleTranslation.objects.create(
                language_version=lang, example=example, text=(ex.get("translation") or "").strip(), source_text=zh,
            )
    validate_base(base, env)
    validate_language(lang, env)
    return lang


@transaction.atomic
def store_translation(word: Word, language: Language, base: WordBaseVersion, data: dict,
                      env: ContentEnvironment, meta: dict) -> LanguageContentVersion:
    word = Word.objects.select_for_update().get(pk=word.pk)
    stale = draft_language(word, language.code)
    if stale:
        stale.delete()
    lang = LanguageContentVersion.objects.create(
        word=word, language=language, base_version=base, origin=Origin.GENERATED, generation_meta=meta,
    )
    senses = {s.pk: s for s in base.senses.all()}
    examples = {e.pk: e for e in Example.objects.filter(sense__base_version=base)}
    unknown = []
    for s in data.get("senses", []):
        sense = senses.get(s.get("sense_id"))
        if sense is None:
            unknown.append(f"sense {s.get('sense_id')}")
            continue
        SenseTranslation.objects.get_or_create(
            language_version=lang, sense=sense, defaults={"text": (s.get("meaning") or "").strip()},
        )
        for ex in s.get("examples", []):
            example = examples.get(ex.get("sentence_id"))
            if example is None or example.sense_id != sense.pk:
                unknown.append(f"sentence {ex.get('sentence_id')}")
                continue
            ExampleTranslation.objects.get_or_create(
                language_version=lang, example=example,
                defaults={"text": (ex.get("translation") or "").strip(), "source_text": example.text_zh},
            )
    if unknown:
        lang.generation_meta = {**meta, "ignored_ids": unknown}
        lang.save(update_fields=["generation_meta"])
    validate_language(lang, env)  # translation_complete marca lo que falte
    return lang


def store_result(target_info: dict, language: Language, data: dict, env: ContentEnvironment, meta: dict):
    word = Word.objects.get(pk=target_info["word_id"])
    if target_info["mode"] == "translate":
        base = WordBaseVersion.objects.get(pk=target_info["base_version_id"])
        if base.status == VersionStatus.ARCHIVED:
            raise GenerationError("la base cambió mientras se generaba")
        return store_translation(word, language, base, data, env, meta)
    return store_full(word, language, data, env, meta, target_info.get("replace_base_drafts", False))


# ---------------------------------------------------------------------------
# Envío a la API
# ---------------------------------------------------------------------------

def request_map(targets: list[Target], replace_base_drafts: bool = False) -> dict:
    return {
        custom_id(t): {"word_id": t.word.pk, "mode": t.mode,
                       "base_version_id": t.base_version.pk if t.base_version else None,
                       "replace_base_drafts": replace_base_drafts}
        for t in targets
    }


def submit_batch(client, targets: list[Target], language: Language, env: ContentEnvironment, model: str,
                 replace_base_drafts: bool = False, effort: str | None = None) -> GenerationJob:
    requests = [{"custom_id": custom_id(t), "params": build_request(t, language, env, model, effort)} for t in targets]
    batch = client.messages.batches.create(requests=requests)
    return GenerationJob.objects.create(
        batch_id=batch.id, language=language, model=model, effort=effort or "", prompt_version=prompts.PROMPT_VERSION,
        request_map=request_map(targets, replace_base_drafts),
    )


def collect_batch(client, job: GenerationJob, env: ContentEnvironment) -> dict:
    stored, failures = 0, []
    for result in client.messages.batches.results(job.batch_id):
        info = job.request_map.get(result.custom_id)
        if info is None:
            continue
        meta = {"model": job.model, "effort": job.effort, "prompt_version": job.prompt_version, "batch_id": job.batch_id,
                "custom_id": result.custom_id}
        try:
            if result.result.type != "succeeded":
                raise GenerationError(f"resultado {result.result.type}: {getattr(result.result, 'error', '')}")
            store_result(info, job.language, parse_message(result.result.message), env, meta)
            stored += 1
        except GenerationError as e:
            failures.append({"custom_id": result.custom_id, "word_id": info["word_id"], "reason": str(e)})
    job.status = GenerationJob.Status.COLLECTED
    job.collected_at = timezone.now()
    job.summary = {"stored": stored, "failures": failures}
    job.save(update_fields=["status", "collected_at", "summary"])
    return job.summary


def run_sync(client, targets: list[Target], language: Language, env: ContentEnvironment, model: str, log=print,
             replace_base_drafts: bool = False, effort: str | None = None) -> dict:
    """Genera de una en una, sin lote. Para muestras pequeñas."""
    stored, failures = 0, []
    for t in targets:
        meta = {"model": model, "effort": effort or "", "prompt_version": prompts.PROMPT_VERSION, "mode": "sync",
                "custom_id": custom_id(t)}
        try:
            message = client.messages.create(**build_request(t, language, env, model, effort))
            store_result(request_map([t], replace_base_drafts)[custom_id(t)], language, parse_message(message), env, meta)
            stored += 1
            log(f"  ✓ {t.word.hanzi} ({t.mode})")
        except GenerationError as e:
            failures.append({"custom_id": custom_id(t), "word_id": t.word.pk, "reason": str(e)})
            log(f"  ✗ {t.word.hanzi}: {e}")
    return {"stored": stored, "failures": failures}
