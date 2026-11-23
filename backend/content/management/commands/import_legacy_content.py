"""
Trae el contenido HSK 1 ya generado y revisado (tablas de la app `vocab`) al
modelo de 08-contenido.md como borradores con origen "imported" (R-CON-07:
todo contenido, sea cual sea su origen, pasa por borrador y revisión humana).

- Requiere el sílabo cargado (load_syllabus): cada palabra se empareja por
  nivel y número de orden, y se comprueba que el hanzi coincida.
- El pinyin de los ejemplos se recalcula con la tubería (08-contenido.md §2).
  Si el pinyin revisado a mano leía la palabra objetivo distinto del sílabo de
  forma consistente (好 hào), esa lectura se guarda en la acepción.
- Escribe un informe JSON con las diferencias de pinyin, para revisarlas.
- Repetirlo no duplica: omite palabras que ya tienen alguna base.
"""
import json
import re
from collections import Counter

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from content.models import (
    Example, ExampleTranslation, LanguageContentVersion, Origin, Sense, SenseTranslation,
    ThirdPartyGloss, Word, WordBaseVersion,
)
from content.pipeline.pinyin import is_chinese_char, split_syllables, split_word_pinyin, to_marks
from content.pos import normalize_pos
from content.services.environment import build_environment
from content.services.validation import example_pinyin, validate_base, validate_language
from languages.models import Language
from vocab import models as legacy


def _target_reading(hanzi: str, syllabus_pinyin: str, examples) -> str:
    """Lectura de la palabra objetivo según el pinyin revisado, si difiere del sílabo."""
    base = split_word_pinyin(hanzi, syllabus_pinyin) or []
    votes = Counter()
    for ex in examples:
        chars = [c for c in ex.sentence_zh if is_chinese_char(c)]
        syls = split_syllables(ex.pinyin or "")
        if len(chars) != len(syls):
            continue
        text = "".join(chars)
        start = text.find(hanzi)
        if start < 0:
            continue
        votes[tuple(syls[start:start + len(hanzi)])] += 1
    if not votes or len(votes) > 1:
        return ""
    reading = list(votes.most_common(1)[0][0])
    if len(reading) != len(base):
        return ""

    def tone(s):
        return s[-1] if s[-1].isdigit() else "5"

    def letters(s):
        return re.sub(r"\d", "", s)

    differs = False
    for c, r, b in zip(hanzi, reading, base):
        if letters(r) != letters(b):
            differs = True  # otra sílaba
        elif c not in "一不" and "5" not in (tone(r), tone(b)) and tone(r) != tone(b):
            differs = True  # otro tono pleno (好 hǎo → hào); el neutro y el sandhi no cuentan
    return "".join(to_marks(r) for r in reading) if differs else ""


class Command(BaseCommand):
    help = "Importa el contenido de la app vocab como borradores (origen imported)."

    def add_arguments(self, parser):
        parser.add_argument("--language", default="es")
        parser.add_argument("--report", default="import_legacy_report.json", help="Informe de diferencias de pinyin.")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, language, report, dry_run, **opts):
        try:
            lang = Language.objects.get(code=language)
        except Language.DoesNotExist:
            raise CommandError(f"Idioma '{language}' no cargado.")
        if not Word.objects.exists():
            raise CommandError("Carga primero el sílabo: python manage.py load_syllabus …")
        env = build_environment()
        stats = Counter()
        diffs, problems = [], []

        with transaction.atomic():
            for lw in legacy.Word.objects.order_by("hsk_level", "source_no").prefetch_related("meanings__examples"):
                word = Word.objects.filter(hsk_level=lw.hsk_level, syllabus_order=lw.source_no).first()
                if word is None or word.hanzi != lw.hanzi:
                    problems.append(f"{lw.hanzi} (#{lw.source_no}): no coincide con el sílabo cargado")
                    continue
                if word.base_versions.exists():
                    stats["omitidas (ya tienen base)"] += 1
                    continue
                glosses = {g.gloss.strip(): g for g in ThirdPartyGloss.objects.filter(word=word)}
                base = WordBaseVersion.objects.create(word=word, origin=Origin.IMPORTED,
                                                      generation_meta={"imported_from": "vocab", "legacy_word_id": lw.pk})
                lcv = LanguageContentVersion.objects.create(word=word, language=lang, base_version=base,
                                                            origin=Origin.IMPORTED,
                                                            generation_meta={"imported_from": "vocab"})
                for si, m in enumerate(m for m in lw.meanings.order_by("sense_index")):
                    exs = list(m.examples.order_by("order"))
                    reading = _target_reading(word.hanzi, word.pinyin, exs)
                    sense = Sense.objects.create(
                        base_version=base, position=si, pos=normalize_pos(m.pos_raw), reading=reading,
                        source_gloss=glosses.get(m.translation_en.strip()),
                    )
                    if reading:
                        stats["acepciones con lectura propia"] += 1
                    SenseTranslation.objects.create(language_version=lcv, sense=sense, text=m.meaning_es.strip())
                    for ei, ex in enumerate(exs):
                        new_py = example_pinyin(ex.sentence_zh, word, reading, env)
                        if split_syllables(new_py) != split_syllables(ex.pinyin or ""):
                            diffs.append({"word": word.hanzi, "zh": ex.sentence_zh, "revisado": ex.pinyin, "tuberia": new_py})
                        e = Example.objects.create(sense=sense, position=ei, text_zh=ex.sentence_zh, pinyin=new_py)
                        ExampleTranslation.objects.create(language_version=lcv, example=e,
                                                          text=ex.sentence_es.strip(), source_text=ex.sentence_zh)
                        stats["ejemplos"] += 1
                    stats["acepciones"] += 1
                stats["palabras"] += 1
                for r in validate_base(base, env):
                    if not r.passed:
                        stats[f"base ✗ {r.code}"] += 1
                for r in validate_language(lcv, env):
                    if not r.passed:
                        stats[f"{lang.code} ✗ {r.code}"] += 1
            if dry_run:
                transaction.set_rollback(True)

        if not dry_run:
            with open(report, "w", encoding="utf-8") as f:
                json.dump({"pinyin_diferente": diffs, "problemas": problems}, f, ensure_ascii=False, indent=2)
        for k, v in sorted(stats.items()):
            self.stdout.write(f"  {k}: {v}")
        for p in problems:
            self.stdout.write(self.style.WARNING(f"  ! {p}"))
        self.stdout.write(self.style.SUCCESS(
            f"{'[dry-run] ' if dry_run else ''}Importadas {stats['palabras']} palabras como borrador. "
            f"Pinyin distinto del revisado: {len(diffs)}" + ("" if dry_run else f" (ver {report}).")
        ))
