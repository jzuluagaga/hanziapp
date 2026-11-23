"""
Recalcula el pinyin de los ejemplos en borrador con la tubería actual
(08-contenido.md §2). Útil al cargar un nivel nuevo del sílabo: sus palabras
pasan a leerse con su pinyin oficial también en ejemplos de otros niveles
(R-CON-01), o al mejorar las reglas.

Solo toca borradores; lo publicado se corrige con una corrección (HU-E13-04).
Sobrescribe el pinyin editado a mano en esos borradores: usa --dry-run antes.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from content.models import Example, VersionStatus
from content.services.environment import build_environment
from content.services.validation import example_pinyin, validate_base


class Command(BaseCommand):
    help = "Recalcula el pinyin de los ejemplos en borrador."

    def add_arguments(self, parser):
        parser.add_argument("--level", type=int)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--show", type=int, default=15)

    def handle(self, *args, level, dry_run, show, **opts):
        env = build_environment()
        qs = Example.objects.filter(sense__base_version__status=VersionStatus.DRAFT).select_related(
            "sense__base_version__word")
        if level:
            qs = qs.filter(sense__base_version__word__hsk_level=level)
        changed, bases = [], set()
        with transaction.atomic():
            for ex in qs:
                sense = ex.sense
                new = example_pinyin(ex.text_zh, sense.base_version.word, sense.reading, env)
                if new != ex.pinyin:
                    changed.append((ex.text_zh, ex.pinyin, new))
                    bases.add(sense.base_version)
                    if not dry_run:
                        ex.pinyin = new
                        ex.save(update_fields=["pinyin"])
            if not dry_run:
                for b in bases:
                    validate_base(b, env)
        for zh, old, new in changed[:show]:
            self.stdout.write(f"  {zh}\n     antes:  {old}\n     ahora:  {new}")
        self.stdout.write(self.style.SUCCESS(
            f"{'[dry-run] ' if dry_run else ''}{len(changed)} ejemplos con pinyin nuevo en {len(bases)} palabras "
            f"(de {qs.count()} ejemplos en borrador)."
        ))
