from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.test import TestCase

from content.models import AudioAsset, Example, VersionStatus, WordBaseVersion
from content.services.editorial import (
    PublishError, editorial_status, publish_base, publish_language, start_correction,
)
from content.services.validation import failed_codes, validate_base
from languages.models import Language
from ops.models import AuditLog

from .helpers import add_audio, editor, make_base, make_language, setup_syllabus


class PublishTests(TestCase):
    def setUp(self):
        self.words = setup_syllabus()
        self.word = self.words["喝"]
        self.editor = editor()

    def test_good_draft_passes_all_validations(self):
        base = make_base(self.word)
        validate_base(base)
        self.assertEqual(failed_codes(base), [])

    def test_cannot_publish_with_failed_validation(self):
        # Q-23 / R-CON-06
        base = make_base(self.word, examples=["我喝水。", "我吃饭。", "你喝吗？"])  # 2.º sin la palabra
        with self.assertRaisesMessage(PublishError, "word_in_example"):
            publish_base(base, self.editor)
        base.refresh_from_db()
        self.assertEqual(base.status, VersionStatus.DRAFT)

    def test_cannot_publish_without_audio(self):
        base = make_base(self.word, audio=False)
        with self.assertRaisesMessage(PublishError, "audio_present"):
            publish_base(base, self.editor)

    def test_requires_editor_permission(self):
        base = make_base(self.word)
        nobody = get_user_model().objects.create_user(email="x@example.com", password="x", username="x")
        with self.assertRaises(PermissionDenied):
            publish_base(base, nobody)

    def test_language_requires_published_base(self):
        # R-CON-04
        base = make_base(self.word)
        lang = make_language(base)
        with self.assertRaisesMessage(PublishError, "R-CON-04"):
            publish_language(lang, self.editor)
        publish_base(base, self.editor)
        publish_language(lang, self.editor)
        self.assertEqual(editorial_status(self.word, "es"), "published")

    def test_publication_records_who_when_origin(self):
        # R-CON-07, R-DAT-10
        base = make_base(self.word)
        publish_base(base, self.editor)
        base.refresh_from_db()
        self.assertEqual(base.published_by, self.editor)
        self.assertIsNotNone(base.published_at)
        entry = AuditLog.objects.get(action="content_published")
        self.assertEqual(entry.data["origin"], "generated")
        self.assertEqual(entry.data["layer"], "base")

    def test_content_status_independent_per_language(self):
        # R-IDI-05, prueba citada en R-IDI-10
        base = make_base(self.word)
        es, en = make_language(base, "es"), make_language(base, "en", meaning="to have a drink",
                                                          translations=["I drink water.", "Mum drinks tea.", "Do you drink?"])
        publish_base(base, self.editor)
        publish_language(es, self.editor)
        self.assertEqual(editorial_status(self.word, "es"), "published")
        self.assertEqual(editorial_status(self.word, "en"), "draft")
        en.refresh_from_db()
        self.assertEqual(en.status, VersionStatus.DRAFT)

    def test_at_most_one_draft_and_one_published(self):
        # R-CON-05, garantizado por la base de datos
        make_base(self.word)
        with self.assertRaises(IntegrityError), transaction.atomic():
            WordBaseVersion.objects.create(word=self.word, origin="manual")

    def test_correction_keeps_published_visible_and_republishes_languages_together(self):
        # R-CON-05, R-CON-11 (a): el id de la palabra no cambia
        base = make_base(self.word)
        es = make_language(base)
        publish_base(base, self.editor)
        publish_language(es, self.editor)

        new = start_correction(self.word, self.editor)
        self.assertEqual(editorial_status(self.word, "es"), "published")
        ex = Example.objects.filter(sense__base_version=new).order_by("position").first()
        ex.text_zh = "他喝水。"
        ex.pinyin = "tā hē shuǐ."
        ex.save()
        add_audio("他喝水。")
        es_draft = new.language_versions.get(language_id="es")

        # La traducción quedó desfasada: no se puede publicar la base sin su idioma válido.
        with self.assertRaisesMessage(PublishError, "es"):
            publish_base(new, self.editor)
        t = es_draft.example_translations.get(example=ex)
        t.text, t.source_text = "Él bebe agua.", ex.text_zh
        t.save()

        publish_base(new, self.editor)
        es_draft.refresh_from_db()
        base.refresh_from_db()
        self.assertEqual(es_draft.status, VersionStatus.PUBLISHED)
        self.assertEqual(base.status, VersionStatus.ARCHIVED)
        self.assertEqual(self.word.language_versions.filter(status="published").count(), 1)


class AudioTests(TestCase):
    def test_audio_keyed_by_language_and_voice(self):
        # R-IDI-08, prueba citada en R-IDI-10
        AudioAsset.objects.create(text="你好", text_hash="h", spoken_language="zh", voice="a", file="1")
        AudioAsset.objects.create(text="你好", text_hash="h", spoken_language="zh", voice="b", file="2")
        AudioAsset.objects.create(text="你好", text_hash="h", spoken_language="yue", voice="a", file="3")
        with self.assertRaises(IntegrityError), transaction.atomic():
            AudioAsset.objects.create(text="你好", text_hash="h", spoken_language="zh", voice="a", file="4")


class LanguagesSeedTests(TestCase):
    def test_spanish_active_english_loaded_inactive(self):
        # R-IDI-02
        es, en = Language.objects.get(code="es"), Language.objects.get(code="en")
        self.assertTrue(es.is_study_active and es.is_ui_active)
        self.assertFalse(en.is_study_active or en.is_ui_active)
