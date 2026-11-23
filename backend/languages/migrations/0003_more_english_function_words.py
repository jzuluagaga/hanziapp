"""Más palabras funcionales del inglés para `translation_language` (se coló "after a verb:" en un significado)."""
from django.db import migrations

EXTRA = ["after", "before", "used", "into", "about", "only", "also", "something", "someone", "would", "should", "can't", "don't"]


def add(apps, schema_editor):
    Language = apps.get_model("languages", "Language")
    en = Language.objects.filter(code="en").first()
    if en:
        en.function_words = sorted(set(en.function_words) | set(EXTRA))
        en.save(update_fields=["function_words"])


def remove(apps, schema_editor):
    Language = apps.get_model("languages", "Language")
    en = Language.objects.filter(code="en").first()
    if en:
        en.function_words = [w for w in en.function_words if w not in EXTRA]
        en.save(update_fields=["function_words"])


class Migration(migrations.Migration):
    dependencies = [("languages", "0002_seed_languages")]
    operations = [migrations.RunPython(add, remove)]
