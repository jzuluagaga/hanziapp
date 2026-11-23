"""
Convierte una lista "New HSK Vocabulary – Level N" (PDF de Mandarin Bean) al
formato JSON de `load_syllabus`. Requiere `pdftotext` (poppler).

    python manage.py syllabus_from_pdf ~/Downloads/New-HSK-Vocabulary-Level-2.pdf --level 2 \
        --out content_pipeline/hsk2_final.json

Ojo: esa lista no es el documento oficial del sílabo. Antes de publicar un
nivel hay que cotejarlo con el oficial (R-CON-01, `check_syllabus`). Sus
traducciones en inglés son glosas de terceros: solo uso interno (R-CON-02).
"""
import json
import re
import shutil
import subprocess

from django.core.management.base import BaseCommand, CommandError

from ._mandarinbean_pdf import parse_layout_text


class Command(BaseCommand):
    help = "Extrae el vocabulario de un PDF de Mandarin Bean a JSON para load_syllabus."

    def add_arguments(self, parser):
        parser.add_argument("pdf")
        parser.add_argument("--level", type=int, required=True)
        parser.add_argument("--out", required=True)

    def handle(self, *args, pdf, level, out, **opts):
        if not shutil.which("pdftotext"):
            raise CommandError("Falta pdftotext (brew install poppler).")
        text = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True, check=True).stdout
        # "ENTRIES" va a la derecha de la cabecera; el número, al final de la línea siguiente.
        declared = re.search(r"ENTRIES\s*\n[^\n]*?(\d+)\s*$", text, re.MULTILINE)
        entries = parse_layout_text(text, level)
        numbers = [e["no"] for e in entries]
        problems = []
        if numbers != list(range(1, len(entries) + 1)):
            problems.append("la numeración no es consecutiva")
        if declared and int(declared.group(1)) != len(entries):
            problems.append(f"el PDF declara {declared.group(1)} entradas y se leyeron {len(entries)}")
        if problems:
            raise CommandError("; ".join(problems))
        with open(out, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        glosses = sum(len(e["senses"]) for e in entries)
        self.stdout.write(self.style.SUCCESS(f"{len(entries)} palabras y {glosses} glosas → {out}"))
