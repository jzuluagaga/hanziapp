"""
Clasificación de palabras en subtemas (D-49, 08-contenido.md §7).

Cada palabra recibe un solo subtema de la lista cerrada de `themes.json`. La API
propone y el editor aprueba: nada de esto llega a los mazos sin revisión.
Repetirlo no duplica nada y nunca toca una asignación aprobada.
"""
from __future__ import annotations

import json
import random
from functools import lru_cache
from pathlib import Path

from django.db import transaction
from django.utils import timezone

from languages.models import Language

from ..models import GenerationJob, LanguageContentVersion, Origin, SenseTranslation, VersionStatus, Word, WordTheme
from .generation import GenerationError, parse_message

DATA = Path(__file__).resolve().parents[1] / "pipeline" / "data" / "themes.json"
PROMPT_VERSION = "themes-2"
CHUNK = 50
MAX_TOKENS = 16000


@lru_cache(maxsize=1)
def taxonomy() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def subtheme_keys() -> list[str]:
    return [s["key"] for t in taxonomy()["themes"] for s in t["subthemes"]]


def parent_of() -> dict[str, str]:
    return {s["key"]: t["key"] for t in taxonomy()["themes"] for s in t["subthemes"]}


def system_prompt() -> str:
    t = taxonomy()
    lines = [
        "Clasificas palabras del examen HSK (chino mandarín) en un subtema temático, para armar mazos de estudio",
        "para hispanohablantes. Usa SOLO las claves de subtema de esta lista, en este orden pedagógico:",
        "",
    ]
    for theme in t["themes"]:
        lines.append(f"{theme['es']}:")
        lines += [f"  - {s['key']}: {s['es']}" for s in theme["subthemes"]]
    lines += ["", "Reglas, en orden de prioridad:"]
    lines += [f"{i}. {r}" for i, r in enumerate(t["rules"], start=1)]
    lines += [
        "",
        "Para cada palabra devuelve su id y la clave del subtema. " + t.get("doubtful", ""),
        "No omitas ninguna palabra ni repitas ids.",
    ]
    return "\n".join(lines)


def schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "subtheme": {"type": "string", "enum": subtheme_keys()},
                        "doubtful": {"type": "boolean"},
                    },
                    "required": ["id", "subtheme", "doubtful"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["items"],
        "additionalProperties": False,
    }


def _meanings(words: list[Word], lang: str = "es") -> dict[int, tuple[str, str]]:
    """Categoría y significados de la versión vigente (publicada o, si no, borrador) en el idioma."""
    out: dict[int, tuple[str, str]] = {}
    versions = {}
    for v in LanguageContentVersion.objects.filter(word__in=words, language_id=lang).exclude(status=VersionStatus.ARCHIVED).order_by("status"):
        if v.word_id not in versions or v.status == VersionStatus.PUBLISHED:
            versions[v.word_id] = v
    trans = {}
    for t in SenseTranslation.objects.filter(language_version__in=versions.values()).select_related("sense").order_by("sense__position"):
        trans.setdefault(t.language_version_id, []).append((t.sense.pos, t.text))
    for wid, v in versions.items():
        senses = trans.get(v.pk, [])[:3]
        out[wid] = (senses[0][0] if senses else "", " / ".join(text for _, text in senses))
    return out


def user_message(words: list[Word]) -> str:
    info = _meanings(words)
    rows = ["id | hanzi | pinyin | nivel | categoría | significados en español"]
    for w in words:
        pos, meaning = info.get(w.pk, ("", ""))
        rows.append(f"{w.pk} | {w.hanzi} | {w.pinyin} | HSK {w.hsk_level} | {pos} | {meaning}")
    return "\n".join(rows)


def build_request(words: list[Word], model: str, effort: str | None = "low") -> dict:
    return {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "system": [{"type": "text", "text": system_prompt(), "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user_message(words)}],
        "output_config": {"format": {"type": "json_schema", "schema": schema()}, **({"effort": effort} if effort else {})},
    }


def select_words(levels=None, hanzi=None, regenerate=False, sample=None, seed=22) -> list[Word]:
    qs = Word.objects.filter(retired_at__isnull=True).order_by("hsk_level", "syllabus_order")
    if levels:
        qs = qs.filter(hsk_level__in=levels)
    if hanzi:
        qs = qs.filter(hanzi__in=hanzi)
    qs = qs.exclude(theme__status=WordTheme.Status.APPROVED)
    if not regenerate:
        qs = qs.filter(theme__isnull=True)
    words = list(qs)
    if sample:
        rng = random.Random(seed)
        by_level: dict[int, list[Word]] = {}
        for w in words:
            by_level.setdefault(w.hsk_level, []).append(w)
        per = max(1, sample // max(1, len(by_level)))
        words = [w for lvl in sorted(by_level) for w in sorted(rng.sample(by_level[lvl], min(per, len(by_level[lvl]))),
                                                                 key=lambda x: x.syllabus_order)]
    return words


def chunks(words: list[Word]) -> list[list[Word]]:
    """Grupos de hasta CHUNK palabras del mismo nivel."""
    out, by_level = [], {}
    for w in words:
        by_level.setdefault(w.hsk_level, []).append(w)
    for lvl in sorted(by_level):
        ws = by_level[lvl]
        out += [ws[i:i + CHUNK] for i in range(0, len(ws), CHUNK)]
    return out


@transaction.atomic
def store(ids: list[int], data: dict, meta: dict) -> tuple[int, list[str]]:
    """Guarda las propuestas como borrador. Rechaza ids ajenos o repetidos y claves fuera de la lista."""
    keys, expected = set(subtheme_keys()), set(ids)
    seen, problems, stored = set(), [], 0
    for item in data.get("items", []):
        wid, key = item.get("id"), item.get("subtheme")
        if wid not in expected or wid in seen:
            problems.append(f"id inesperado o repetido: {wid}")
            continue
        seen.add(wid)
        if key not in keys:
            problems.append(f"{wid}: subtema desconocido {key}")
            continue
        theme = WordTheme.objects.filter(word_id=wid).first()
        if theme and theme.status == WordTheme.Status.APPROVED:
            continue  # lo aprobado nunca se toca
        WordTheme.objects.update_or_create(word_id=wid, defaults={
            "subtheme": key, "doubtful": bool(item.get("doubtful")), "status": WordTheme.Status.DRAFT,
            "origin": Origin.GENERATED, "generation_meta": meta,
        })
        stored += 1
    missing = expected - seen
    if missing:
        problems.append(f"sin respuesta: {sorted(missing)}")
    return stored, problems


def _usage(message) -> dict:
    u = getattr(message, "usage", None)
    return {k: getattr(u, k, 0) or 0 for k in ("input_tokens", "output_tokens", "cache_read_input_tokens",
                                                "cache_creation_input_tokens")} if u else {}


def run_sync(client, words: list[Word], model: str, effort: str | None = "low", log=print) -> dict:
    stored, problems, usage = 0, [], {}
    for group in chunks(words):
        meta = {"model": model, "effort": effort or "", "prompt_version": PROMPT_VERSION, "mode": "sync"}
        try:
            message = client.messages.create(**build_request(group, model, effort))
            n, p = store([w.pk for w in group], parse_message(message), meta)
            stored += n
            problems += p
            for k, v in _usage(message).items():
                usage[k] = usage.get(k, 0) + v
            log(f"  HSK {group[0].hsk_level}: {n}/{len(group)} clasificadas")
        except GenerationError as e:
            problems.append(f"HSK {group[0].hsk_level} ({len(group)} palabras): {e}")
            log(f"  ✗ HSK {group[0].hsk_level}: {e}")
    return {"stored": stored, "problems": problems, "usage": usage}


def submit_batch(client, words: list[Word], model: str, effort: str | None = "low") -> GenerationJob:
    groups = chunks(words)
    requests = [{"custom_id": f"themes-{i}", "params": build_request(g, model, effort)} for i, g in enumerate(groups)]
    batch = client.messages.batches.create(requests=requests)
    return GenerationJob.objects.create(
        batch_id=batch.id, kind="themes", language=Language.objects.get(code="es"), model=model, effort=effort or "",
        prompt_version=PROMPT_VERSION, request_map={f"themes-{i}": [w.pk for w in g] for i, g in enumerate(groups)},
    )


def collect_batch(client, job: GenerationJob) -> dict:
    stored, problems, usage = 0, [], {}
    for result in client.messages.batches.results(job.batch_id):
        ids = job.request_map.get(result.custom_id)
        if ids is None:
            continue
        meta = {"model": job.model, "effort": job.effort, "prompt_version": job.prompt_version, "batch_id": job.batch_id}
        try:
            if result.result.type != "succeeded":
                raise GenerationError(f"resultado {result.result.type}")
            n, p = store(ids, parse_message(result.result.message), meta)
            stored += n
            problems += p
            for k, v in _usage(result.result.message).items():
                usage[k] = usage.get(k, 0) + v
        except GenerationError as e:
            problems.append(f"{result.custom_id}: {e}")
    job.status = GenerationJob.Status.COLLECTED
    job.collected_at = timezone.now()
    job.summary = {"stored": stored, "problems": problems, "usage": usage}
    job.save(update_fields=["status", "collected_at", "summary"])
    return job.summary


def approve(themes, user) -> int:
    from ops.services import audit

    n = 0
    for t in themes.exclude(status=WordTheme.Status.APPROVED):
        t.status, t.reviewed_by, t.reviewed_at = WordTheme.Status.APPROVED, user, timezone.now()
        t.save(update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"])
        audit(user, "word_theme_approved", t, subtheme=t.subtheme)
        n += 1
    return n
