"""
SOLO DESARROLLO. Publica los borradores de unos niveles sin revisión humana y con
audio de marcador (`tts:`), para probar el frontend de punta a punta mientras no
hay proveedor de síntesis de voz (08-contenido.md §1).

Viola a propósito R-CON-06 y R-CON-07, así que se niega a correr salvo con
DEBUG=True y una base cuyo nombre termine en `dev.sqlite3`.
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from content.models import AudioAsset, LanguageContentVersion, VersionStatus, WordBaseVersion
from content.services.environment import text_hash
from decks.services import build_system_decks

DEV_VOICE = "dev-browser-tts"


class Command(BaseCommand):
    help = "SOLO DESARROLLO: publica borradores sin revisión y con audio de marcador."

    def add_arguments(self, parser):
        parser.add_argument("--level", type=int, action="append", required=True)
        parser.add_argument("--language", default="es")

    @transaction.atomic
    def handle(self, *args, level, language, **opts):
        name = str(settings.DATABASES["default"].get("NAME", ""))
        if not settings.DEBUG or not name.endswith("dev.sqlite3"):
            raise CommandError("Solo con DEBUG=True y DATABASE_URL apuntando a un archivo *dev.sqlite3.")
        now = timezone.now()
        n = 0
        for base in WordBaseVersion.objects.filter(word__hsk_level__in=level, status=VersionStatus.DRAFT,
                                                   word__retired_at__isnull=True).select_related("word"):
            word = base.word
            if word.base_versions.filter(status=VersionStatus.PUBLISHED).exists():
                continue
            lang = LanguageContentVersion.objects.filter(word=word, language_id=language, base_version=base,
                                                         status=VersionStatus.DRAFT).first()
            if lang is None:
                continue
            base.status, base.published_at = VersionStatus.PUBLISHED, now
            base.save(update_fields=["status", "published_at"])
            lang.status, lang.published_at = VersionStatus.PUBLISHED, now
            lang.save(update_fields=["status", "published_at"])
            texts = [word.hanzi] + [e.text_zh for s in base.senses.all() for e in s.examples.all()]
            for t in texts:
                AudioAsset.objects.get_or_create(text_hash=text_hash(t), spoken_language="zh", voice=DEV_VOICE,
                                                 defaults={"text": t, "file": f"tts:{t}"})
            n += 1
        build_system_decks()
        self.stdout.write(self.style.WARNING(f"[DEV] Publicadas {n} palabras sin revisión en {name}"))
