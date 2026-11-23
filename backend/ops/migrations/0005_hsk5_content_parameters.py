"""Parámetros de contenido para HSK 5 (Docs/08-contenido.md §3: se fijan al preparar el nivel). PROPUESTA."""
from django.db import migrations

VALUES = {"content.example_max_chars": 20, "content.example_level_tolerance": 1}


def add(apps, schema_editor):
    Parameter = apps.get_model("ops", "Parameter")
    for key, value in VALUES.items():
        p = Parameter.objects.filter(key=key).first()
        if p is not None and isinstance(p.value, dict):
            p.value = {**p.value, "5": p.value.get("5", value)}
            p.save(update_fields=["value"])


def remove(apps, schema_editor):
    Parameter = apps.get_model("ops", "Parameter")
    for key in VALUES:
        p = Parameter.objects.filter(key=key).first()
        if p is not None and isinstance(p.value, dict):
            p.value.pop("5", None)
            p.save(update_fields=["value"])


class Migration(migrations.Migration):
    dependencies = [("ops", "0004_hsk4_content_parameters")]
    operations = [migrations.RunPython(add, remove)]
