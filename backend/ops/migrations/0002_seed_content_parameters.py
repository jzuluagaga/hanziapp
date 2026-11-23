"""
Parámetros de contenido (Docs/03-reglas-de-negocio.md §11). Las tolerancias de
example_length y example_level se fijan al preparar cada nivel
(Docs/08-contenido.md §3); los valores de HSK 1 y 2 son una propuesta medida
sobre el contenido HSK 1 ya revisado, pendiente de confirmar.
"""
from django.db import migrations

PARAMS = [
    ("content.example_max_chars", {"1": 12, "2": 14}, "08-contenido §3",
     "Máximo de caracteres chinos (sin puntuación) por ejemplo, por nivel. PROPUESTA."),
    ("content.example_level_tolerance", {"1": 1, "2": 1}, "08-contenido §3",
     "Palabras por encima del nivel admitidas en un ejemplo, por nivel. PROPUESTA."),
    ("content.examples_max_similarity", 0.75, "08-contenido §3",
     "Similitud máxima entre dos ejemplos de una palabra (examples_distinct)."),
    ("content.examples_per_sense", 3, "08-contenido §2", "Ejemplos por acepción."),
    ("content.audio_voice", None, "R-CON-13",
     "Voz vigente para el audio en chino. Vacía hasta elegir proveedor de síntesis (08-contenido §1)."),
]


def seed(apps, schema_editor):
    Parameter = apps.get_model("ops", "Parameter")
    for key, value, rule, description in PARAMS:
        Parameter.objects.get_or_create(key=key, defaults={"value": value, "rule": rule, "description": description})


def unseed(apps, schema_editor):
    apps.get_model("ops", "Parameter").objects.filter(key__in=[p[0] for p in PARAMS]).delete()


class Migration(migrations.Migration):
    dependencies = [("ops", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
