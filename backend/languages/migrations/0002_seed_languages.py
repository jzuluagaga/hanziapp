"""
R-IDI-02: al lanzar, español activo para estudio e interfaz; inglés cargado e
inactivo en ambos. Los textos de estilo y las palabras funcionales son datos
editables en el panel.
"""
from django.db import migrations

# Palabras funcionales frecuentes. Se excluyen las que también existen en el
# otro idioma ("a", "no", "me", "he", "has", "son"...) para no dar falsos positivos.
ES_FUNCTION_WORDS = [
    "el", "los", "las", "del", "que", "y", "un", "una", "es", "está", "están", "por",
    "para", "con", "se", "sus", "yo", "él", "ella", "nosotros", "ellos", "ellas",
    "este", "esta", "esto", "eso", "muy", "pero", "como", "qué", "al", "lo", "le",
    "hay", "tiene", "tengo", "también", "porque", "cuando", "dónde",
]
EN_FUNCTION_WORDS = [
    "the", "of", "and", "to", "is", "are", "was", "were", "you", "it", "this", "that",
    "with", "for", "she", "they", "we", "have", "what", "my", "your", "his", "their",
    "be", "will", "does", "not", "at", "on", "an", "or", "but", "from", "by", "there",
    "which", "who", "how", "why", "when", "where", "i", "very", "because",
]


def seed(apps, schema_editor):
    Language = apps.get_model("languages", "Language")
    Language.objects.update_or_create(code="es", defaults={
        "name": "Español",
        "is_study_active": True,
        "is_ui_active": True,
        "generation_name": "Spanish",
        "generation_style": (
            "Neutral Latin American Spanish, easy to understand for learners in Colombia. "
            "Use \"tú\" (never \"vos\" or \"vosotros\") and avoid regional words."
        ),
        "function_words": ES_FUNCTION_WORDS,
    })
    Language.objects.update_or_create(code="en", defaults={
        "name": "English",
        "is_study_active": False,
        "is_ui_active": False,
        "generation_name": "English",
        "generation_style": "Plain, neutral international English.",
        "function_words": EN_FUNCTION_WORDS,
    })


def unseed(apps, schema_editor):
    apps.get_model("languages", "Language").objects.filter(code__in=["es", "en"]).delete()


class Migration(migrations.Migration):
    dependencies = [("languages", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
