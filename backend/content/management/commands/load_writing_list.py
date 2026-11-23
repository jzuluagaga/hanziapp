"""
Carga la lista de escritura del sílabo (书写字): qué caracteres se piden escribir y
desde qué nivel (R-ESC-10). Repetible: no duplica ni toca `has_stroke_data`.
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from content.models import Character, Word
from content.services.reading import characters_of

DEFAULT = Path(__file__).resolve().parents[2] / "pipeline" / "data" / "writing_list.json"


class Command(BaseCommand):
    help = "Carga la lista de escritura del sílabo en content.Character (R-ESC-10)."

    def add_arguments(self, parser):
        parser.add_argument("path", nargs="?", default=str(DEFAULT))

    @transaction.atomic
    def handle(self, path, **opts):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        levels = {int(k): v for k, v in data["levels"].items()}
        for lvl, expected in data.get("expected", {}).items():
            if len(levels.get(int(lvl), "")) != expected:
                raise CommandError(f"HSK {lvl}: se esperaban {expected} caracteres y hay {len(levels.get(int(lvl), ''))}")
        all_chars = [c for chars in levels.values() for c in chars]
        if len(all_chars) != len(set(all_chars)):
            raise CommandError("Hay caracteres repetidos entre niveles.")

        listed = {c for c in all_chars}
        Character.objects.exclude(char__in=listed).exclude(writing_level=None).update(writing_level=None, writing_order=None)
        changed = 0
        for lvl, chars in sorted(levels.items()):
            for order, ch in enumerate(chars, start=1):
                obj, created = Character.objects.get_or_create(char=ch, defaults={"writing_level": lvl, "writing_order": order})
                if not created and (obj.writing_level, obj.writing_order) != (lvl, order):
                    obj.writing_level, obj.writing_order = lvl, order
                    obj.save(update_fields=["writing_level", "writing_order"])
                    changed += 1
                changed += created

        # Cotejo con el sílabo cargado: cada carácter debe aparecer en una palabra de su nivel o inferior.
        first: dict[str, int] = {}
        for hanzi, level in Word.objects.filter(retired_at__isnull=True).values_list("hanzi", "hsk_level"):
            for ch in characters_of(hanzi):
                first[ch] = min(first.get(ch, 99), level)
        missing = [ch for ch in all_chars if ch not in first]
        later = [f"{ch}(HSK {first[ch]})" for lvl, chars in levels.items() for ch in chars if ch in first and first[ch] > lvl]
        self.stdout.write(f"Lista de escritura: {len(all_chars)} caracteres; {changed} filas creadas o cambiadas.")
        for lvl, chars in sorted(levels.items()):
            self.stdout.write(f"  HSK {lvl}: {len(chars)}")
        if Word.objects.exists():
            if missing:
                self.stdout.write(self.style.WARNING(f"Sin palabra en el sílabo cargado: {' '.join(missing)}"))
            if later:
                self.stdout.write(self.style.WARNING(f"Solo en palabras de un nivel superior: {' '.join(later)}"))
            if not missing and not later:
                self.stdout.write("Cotejo con el sílabo: sin diferencias.")
