"""Parámetros de contenido para HSK 6 (Docs/08-contenido.md §3: se fijan al preparar el nivel). PROPUESTA."""
from django.db import migrations

VALUES = {"content.example_max_chars": 22, "content.example_level_tolerance": 1}


def add(apps, schema_editor):
    Parameter = apps.get_model("ops", "Parameter")
    for key, value in VALUES.items():
        p = Parameter.objects.filter(key=key).first()
        if p is not None and isinstance(p.value, dict):
            p.value = {**p.value, "6": p.value.get("6", value)}
            p.save(update_fields=["value"])


def remove(apps, schema_editor):
    Parameter = apps.get_model("ops", "Parameter")
    for key in VALUES:
        p = Parameter.objects.filter(key=key).first()
        if p is not None and isinstance(p.value, dict):
            p.value.pop("6", None)
            p.save(update_fields=["value"])


class Migration(migrations.Migration):
    dependencies = [("ops", "0005_hsk5_content_parameters")]
    operations = [migrations.RunPython(add, remove)]
