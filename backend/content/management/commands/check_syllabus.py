"""
Paso 2 de 08-contenido.md §2: compara lo cargado con el documento oficial
(conteo por nivel, hanzi y pinyin). El informe debe quedar en cero antes de
publicar un nivel (R-CON-01). Sale con código 1 si hay diferencias.
"""
import sys
from collections import Counter

from django.core.management.base import BaseCommand

from content.models import Word

from ._syllabus_file import read_syllabus_file


class Command(BaseCommand):
    help = "Coteja las palabras cargadas contra un archivo del sílabo oficial."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Archivo con el sílabo oficial transcrito (mismo formato que load_syllabus).")
        parser.add_argument("--level", type=int, help="Limitar a un nivel.")

    def handle(self, *args, path, level, **opts):
        official = read_syllabus_file(path)
        if level:
            official = [e for e in official if e["hsk_level"] == level]
        levels = {e["hsk_level"] for e in official}
        loaded = {(w.hsk_level, w.syllabus_order): w for w in Word.objects.filter(hsk_level__in=levels, retired_at__isnull=True)}
        diffs = []

        off_count = Counter(e["hsk_level"] for e in official)
        db_count = Counter(lvl for lvl, _ in loaded)
        for lvl in sorted(levels):
            if off_count[lvl] != db_count[lvl]:
                diffs.append(f"HSK {lvl}: oficial {off_count[lvl]} palabras, cargadas {db_count[lvl]}")

        seen = set()
        for e in official:
            key = (e["hsk_level"], e["order"])
            seen.add(key)
            w = loaded.get(key)
            if w is None:
                diffs.append(f"HSK {key[0]} #{key[1]} {e['hanzi']}: falta")
                continue
            if w.hanzi != e["hanzi"]:
                diffs.append(f"HSK {key[0]} #{key[1]}: hanzi {w.hanzi} ≠ oficial {e['hanzi']}")
            if w.pinyin != e["pinyin"]:
                diffs.append(f"HSK {key[0]} #{key[1]} {w.hanzi}: pinyin {w.pinyin} ≠ oficial {e['pinyin']}")
        for key, w in loaded.items():
            if key not in seen:
                diffs.append(f"HSK {key[0]} #{key[1]} {w.hanzi}: cargada pero no está en el oficial")

        for d in diffs:
            self.stdout.write(f"  {d}")
        if diffs:
            self.stdout.write(self.style.ERROR(f"{len(diffs)} diferencias."))
            sys.exit(1)
        self.stdout.write(self.style.SUCCESS(f"Sin diferencias ({len(official)} palabras)."))
