"""
Estado editorial, publicación y corrección (R-CON-04 a R-CON-07, R-IDI-05).

Publicar = cambiar la versión publicada en una sola transacción
(09-arquitectura.md §5). Nadie publica sin el permiso de editor, y ningún
borrador con validaciones fallidas se publica.
"""
from __future__ import annotations

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from analytics.services import emit
from ops.services import audit

from ..models import (
    Example, ExampleTranslation, LanguageContentVersion, Origin, Sense, SenseTranslation,
    VersionStatus, Word, WordBaseVersion,
)
from .environment import build_environment
from .validation import failed_codes, validate_base, validate_language

EDITOR_PERMISSION = "content.manage_content"


class PublishError(Exception):
    pass


def require_editor(user) -> None:
    if user is None or not user.has_perm(EDITOR_PERMISSION):
        raise PermissionDenied("Se necesita el permiso de editor de contenido.")


def published_base(word: Word) -> WordBaseVersion | None:
    return word.base_versions.filter(status=VersionStatus.PUBLISHED).first()


def draft_base(word: Word) -> WordBaseVersion | None:
    return word.base_versions.filter(status=VersionStatus.DRAFT).first()


def published_language(word: Word, language_code: str) -> LanguageContentVersion | None:
    return word.language_versions.filter(language_id=language_code, status=VersionStatus.PUBLISHED).first()


def draft_language(word: Word, language_code: str) -> LanguageContentVersion | None:
    return word.language_versions.filter(language_id=language_code, status=VersionStatus.DRAFT).first()


def editorial_status(word: Word, language_code: str | None = None) -> str:
    """`none`, `draft` o `published` (glosario: estado editorial) de la base o de un idioma."""
    qs = word.base_versions if language_code is None else word.language_versions.filter(language_id=language_code)
    statuses = set(qs.values_list("status", flat=True))
    if VersionStatus.PUBLISHED in statuses:
        return "published"
    if VersionStatus.DRAFT in statuses:
        return "draft"
    return "none"


def _mark_published(version, user) -> None:
    version.status = VersionStatus.PUBLISHED
    version.published_at = timezone.now()
    version.published_by = user
    version.save(update_fields=["status", "published_at", "published_by", "updated_at"])


def _archive(version) -> None:
    version.status = VersionStatus.ARCHIVED
    version.save(update_fields=["status", "updated_at"])


@transaction.atomic
def publish_base(version: WordBaseVersion, user, reason: str = "") -> WordBaseVersion:
    """
    Publica una base. Si la palabra ya tenía contenido publicado en algún idioma
    sobre la base anterior, ese idioma debe tener un borrador válido sobre esta
    base y se publica en la misma transacción: el estudiante nunca ve acepciones
    nuevas con traducciones viejas (R-CON-05).
    """
    require_editor(user)
    version = WordBaseVersion.objects.select_for_update().get(pk=version.pk)
    if version.status != VersionStatus.DRAFT:
        raise PublishError("Solo se publica un borrador.")
    env = build_environment()
    validate_base(version, env)
    failed = failed_codes(version)
    if failed:
        raise PublishError(f"Validaciones fallidas: {', '.join(failed)}")

    word = version.word
    old = published_base(word)
    companions = []
    for lang_pub in word.language_versions.filter(status=VersionStatus.PUBLISHED).exclude(base_version=version):
        draft = word.language_versions.filter(
            language_id=lang_pub.language_id, status=VersionStatus.DRAFT, base_version=version,
        ).first()
        if draft is None:
            raise PublishError(
                f"'{lang_pub.language_id}' está publicado sobre la base anterior: falta su borrador sobre esta base."
            )
        validate_language(draft, env)
        if failed_codes(draft):
            raise PublishError(f"El borrador '{draft.language_id}' tiene validaciones fallidas: {', '.join(failed_codes(draft))}")
        companions.append((lang_pub, draft))

    if old:
        _archive(old)
    _mark_published(version, user)
    audit(user, "content_published", version, reason, layer="base", origin=version.origin,
          hsk_level=word.hsk_level, replaces_published=bool(old))
    emit("content_published", layer="base", language="", origin=version.origin,
         hsk_level=word.hsk_level, replaces_published=bool(old))
    for lang_pub, draft in companions:
        _archive(lang_pub)
        _mark_published(draft, user)
        audit(user, "content_published", draft, reason, layer="language", language=draft.language_id,
              origin=draft.origin, hsk_level=word.hsk_level, replaces_published=True)
        emit("content_published", layer="language", language=draft.language_id, origin=draft.origin,
             hsk_level=word.hsk_level, replaces_published=True)
    return version


@transaction.atomic
def publish_language(version: LanguageContentVersion, user, reason: str = "") -> LanguageContentVersion:
    """Publica el contenido de un idioma. Exige su base publicada (R-CON-04)."""
    require_editor(user)
    version = LanguageContentVersion.objects.select_for_update().get(pk=version.pk)
    if version.status != VersionStatus.DRAFT:
        raise PublishError("Solo se publica un borrador.")
    word = version.word
    base = published_base(word)
    if base is None or base.pk != version.base_version_id:
        raise PublishError("La base de la palabra debe estar publicada antes que su contenido por idioma (R-CON-04).")
    validate_language(version)
    failed = failed_codes(version)
    if failed:
        raise PublishError(f"Validaciones fallidas: {', '.join(failed)}")
    old = published_language(word, version.language_id)
    if old:
        _archive(old)
    _mark_published(version, user)
    audit(user, "content_published", version, reason, layer="language", language=version.language_id,
          origin=version.origin, hsk_level=word.hsk_level, replaces_published=bool(old))
    emit("content_published", layer="language", language=version.language_id, origin=version.origin,
         hsk_level=word.hsk_level, replaces_published=bool(old))
    return version


@transaction.atomic
def publish_word(word: Word, language_code: str, user, reason: str = "") -> None:
    """Publica de una vez el borrador de base (si hay) y el del idioma indicado (si hay)."""
    base = draft_base(word)
    if base:
        publish_base(base, user, reason)
    lang = draft_language(word, language_code)
    if lang and lang.status == VersionStatus.DRAFT:
        lang.refresh_from_db()
        if lang.status == VersionStatus.DRAFT:
            publish_language(lang, user, reason)


@transaction.atomic
def start_correction(word: Word, user, reason: str = "") -> WordBaseVersion:
    """
    Crea un borrador de base copiado de la versión publicada, y un borrador de
    cada idioma publicado copiado sobre esa nueva base (HU-E13-04). Lo publicado
    sigue visible hasta que se publique la corrección.
    """
    require_editor(user)
    pub = published_base(word)
    if pub is None:
        raise PublishError("La palabra no tiene una base publicada que corregir.")
    if draft_base(word):
        raise PublishError("Ya hay un borrador de base para esta palabra.")
    new = WordBaseVersion.objects.create(word=word, origin=Origin.MANUAL, generation_meta={"copied_from": pub.pk})
    sense_map, example_map = {}, {}
    for s in pub.senses.order_by("position"):
        ns = Sense.objects.create(base_version=new, position=s.position, pos=s.pos, reading=s.reading,
                                  source_gloss=s.source_gloss)
        sense_map[s.pk] = ns
        for e in s.examples.order_by("position"):
            example_map[e.pk] = Example.objects.create(sense=ns, position=e.position, text_zh=e.text_zh, pinyin=e.pinyin)
    for lang_pub in word.language_versions.filter(status=VersionStatus.PUBLISHED):
        if draft_language(word, lang_pub.language_id):
            continue
        nl = LanguageContentVersion.objects.create(
            word=word, language_id=lang_pub.language_id, base_version=new, origin=Origin.MANUAL,
            generation_meta={"copied_from": lang_pub.pk},
        )
        SenseTranslation.objects.bulk_create([
            SenseTranslation(language_version=nl, sense=sense_map[t.sense_id], text=t.text)
            for t in lang_pub.sense_translations.all() if t.sense_id in sense_map
        ])
        ExampleTranslation.objects.bulk_create([
            ExampleTranslation(language_version=nl, example=example_map[t.example_id], text=t.text, source_text=t.source_text)
            for t in lang_pub.example_translations.all() if t.example_id in example_map
        ])
    audit(user, "content_correction_started", new, reason)
    env = build_environment()
    validate_base(new, env)
    for nl in new.language_versions.all():
        validate_language(nl, env)
    return new
