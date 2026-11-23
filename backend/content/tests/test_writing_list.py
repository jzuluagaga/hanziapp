"""Lista de escritura del sílabo (R-ESC-10)."""
import json
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from content.models import Character

DATA = Path(__file__).resolve().parents[1] / "pipeline" / "data" / "writing_list.json"


class WritingList(TestCase):
    def test_load_writing_list_is_idempotent(self):
        Character.objects.create(char="妈", has_stroke_data=False)
        Character.objects.create(char="鑫", writing_level=2)  # no está en la lista: se quita
        call_command("load_writing_list", stdout=StringIO())
        call_command("load_writing_list", stdout=StringIO())
        counts = {lvl: Character.objects.filter(writing_level=lvl).count() for lvl in (1, 2, 3, 4, 5, 6)}
        self.assertEqual(counts, {1: 50, 2: 50, 3: 150, 4: 150, 5: 150, 6: 150})
        ai = Character.objects.get(char="妈")
        self.assertEqual((ai.writing_level, ai.has_stroke_data), (1, False))  # no toca los trazos
        self.assertIsNone(Character.objects.get(char="鑫").writing_level)

    def test_writing_list_data_is_consistent(self):
        data = json.loads(DATA.read_text(encoding="utf-8"))
        chars = "".join(data["levels"].values())
        self.assertEqual(len(chars), 700)
        self.assertEqual(len(set(chars)), 700)
