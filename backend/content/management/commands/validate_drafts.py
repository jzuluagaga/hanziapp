"""
Paso 5 de 08-contenido.md §2: ejecuta las validaciones de §3 sobre los borradores.
"""
from collections import Counter

from django.core.management.base import BaseCommand

from content.models import LanguageContentVersion, VersionStatus, WordBaseVersion
from content.services.environment import build_environment
from content.services.validation import validate_base, validate_language


class Command(BaseCommand):
    help = "Valida los borradores de base y de idioma."

    def add_arguments(self, parser):
        parser.add_argument("--level", type=int)
        parser.add_argument("--language", help="Validar solo este idioma (además de las bases).")
        parser.add_argument("--show", type=int, default=5, help="Ejemplos de fallo a mostrar por código.")

    def handle(self, *args, level, language, show, **opts):
        env = build_environment()
        bases = WordBaseVersion.objects.filter(status=VersionStatus.DRAFT).select_related("word")
        langs = LanguageContentVersion.objects.filter(status=VersionStatus.DRAFT).select_related("word", "base_version")
        if level:
            bases, langs = bases.filter(word__hsk_level=level), langs.filter(word__hsk_level=level)
        if language:
            langs = langs.filter(language_id=language)

        for title, qs, fn in (("Base", bases, validate_base), ("Idioma", langs, validate_language)):
            failed, samples, ok_versions, total = Counter(), {}, 0, 0
            for v in qs:
                total += 1
                results = fn(v, env)
                bad = [r for r in results if not r.passed]
                ok_versions += not bad
                for r in bad:
                    failed[r.code] += 1
                    samples.setdefault(r.code, []).append(f"{v.word.hanzi}: {r.detail}")
            self.stdout.write(self.style.MIGRATE_HEADING(f"{title}: {ok_versions}/{total} borradores sin fallos"))
            for code, n in failed.most_common():
                self.stdout.write(f"  ✗ {code}: {n}")
                for s in samples[code][:show]:
                    self.stdout.write(f"      {s[:220]}")
