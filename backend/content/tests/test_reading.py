"""Pruebas de E07 (diccionario) y de las partes nuevas de E13."""
from django.contrib.auth.models import Permission
from django.test import TestCase

from analytics.models import Event
from content.models import ContentReport, Word
from content.services.editorial import publish_word, start_correction
from content.services.reports import close_report
from hanzi_backend.testing import client_for, make_word, publish_word as publish_fixture, student
from ops.models import AuditLog
from scheduling.models import ReviewState

from .helpers import editor, make_base, make_language, setup_syllabus


class E07Dictionary(TestCase):
    def setUp(self):
        self.ai = make_word(1, 1, "爱", meaning="amar; querer")
        self.ai.pinyin = "ài"
        self.ai.save()
        self.ba = make_word(1, 2, "爸爸", meaning="papá")
        self.ba.pinyin = "bàba"
        self.ba.save()
        self.draft = make_word(1, 3, "杯子", publish=None, gloss="cup")
        self.c = client_for(student())

    def search(self, q):
        return self.c.get("/api/v1/words/search", {"q": q}).json()

    def test_e07_01_search_by_hanzi(self):
        self.assertEqual([w["id"] for w in self.search("爸")], [str(self.ba.pk)])
        self.assertEqual(self.search("杯")[0]["editorial"], "in_review")

    def test_e07_01_search_by_pinyin_with_or_without_tones(self):
        self.assertEqual(self.search("bàba")[0]["id"], str(self.ba.pk))
        self.assertEqual(self.search("baba")[0]["id"], str(self.ba.pk))
        self.assertEqual(self.search("ai")[0]["id"], str(self.ai.pk))

    def test_search_scoped_to_study_language(self):
        publish_fixture(self.draft, "en", meaning="cup; glass")
        self.assertEqual(self.search("QUERER")[0]["id"], str(self.ai.pk))  # sin distinguir mayúsculas
        self.assertEqual(self.search("papa")[0]["id"], str(self.ba.pk))  # sin tildes
        self.assertEqual(self.search("cup"), [])  # el inglés no se busca con estudio en español

    def test_e07_01_search_event_has_no_query_text(self):
        self.search("querer")
        e = Event.objects.get(name="search_performed")
        self.assertEqual(e.props, {"query_kind": "meaning", "result_count": 1})

    def test_e07_02_published_word_detail(self):
        w = self.c.get(f"/api/v1/words/{self.ai.pk}?from=search").json()
        self.assertEqual(w["editorial"], "published")
        self.assertEqual(w["senses"][0]["meaning"], "amar; querer")
        self.assertTrue(w["examples"][0]["translation"])
        self.assertTrue(w["audio"])
        self.assertEqual(Event.objects.get(name="word_viewed").props["from"], "search")

    def test_e07_02_unpublished_shows_syllabus_only(self):
        w = self.c.get(f"/api/v1/words/{self.draft.pk}").json()
        self.assertEqual((w["editorial"], w["hanzi"], w["level"], w["senses"], w["examples"], w["audio"]),
                         ("in_review", "杯子", 1, [], [], None))

    def test_e07_02_never_exposes_third_party_gloss(self):
        for path in (f"/api/v1/words/{self.draft.pk}", "/api/v1/words/search?q=杯", "/api/v1/words/search?q=cup"):
            self.assertNotIn("cup", self.c.get(path).content.decode())

    def test_e07_02_dictionary_free_for_all_levels(self):
        hsk5 = make_word(5, 1, "政治", meaning="política")
        w = self.c.get(f"/api/v1/words/{hsk5.pk}").json()
        self.assertEqual((w["editorial"], w["senses"][0]["meaning"]), ("published", "política"))

    def test_e07_04_report_created_open(self):
        r = self.c.post(f"/api/v1/words/{self.ai.pk}/reports", {"element": "example", "comment": "tono raro"}, format="json")
        self.assertEqual(r.status_code, 201)
        rep = ContentReport.objects.get()
        self.assertEqual((rep.status, rep.element, rep.comment), ("open", "example", "tono raro"))

    def test_e07_04_invalid_element_rejected(self):
        r = self.c.post(f"/api/v1/words/{self.ai.pk}/reports", {"element": "color"}, format="json")
        self.assertEqual(r.json()["error"], "invalid_input")
        self.assertFalse(ContentReport.objects.exists())

    def test_e07_04_report_event_has_no_comment(self):
        self.c.post(f"/api/v1/words/{self.ai.pk}/reports", {"element": "audio", "comment": "no suena"}, format="json")
        self.assertEqual(Event.objects.get(name="content_report_submitted").props, {"element": "audio", "hsk_level": 1})

    def test_e13_01_loaded_words_visible_in_review(self):
        fresh = Word.objects.create(hanzi="龙", pinyin="lóng", hsk_level=2, syllabus_order=1)
        w = self.c.get(f"/api/v1/words/{fresh.pk}").json()
        self.assertEqual((w["editorial"], w["pinyin"]), ("in_review", "lóng"))


class E13Operations(TestCase):
    def setUp(self):
        self.words = setup_syllabus()
        self.editor = editor()

    def publish_he(self):
        word = self.words["喝"]
        make_language(make_base(word))
        publish_word(word, "es", self.editor)
        return word

    def test_e13_03_publish_emits_event(self):
        self.publish_he()
        events = list(Event.objects.filter(name="content_published").order_by("occurred_at"))
        self.assertEqual([e.props["layer"] for e in events], ["base", "language"])
        self.assertTrue(all(e.account_key is None for e in events))  # sin datos del editor

    def test_e13_04_correction_keeps_review_states(self):
        from datetime import datetime, timezone as tz

        word = self.publish_he()
        user = student()
        now = datetime(2026, 12, 1, tzinfo=tz.utc)
        ReviewState.objects.create(account=user, skill="recognition", unit_key=str(word.pk), word=word, stability=12,
                                   difficulty=5, fsrs_state=2, due_at=now, due_day=now.date(), last_review_at=now,
                                   last_review_day=now.date())
        new_base = start_correction(word, self.editor, "errata")
        from content.models import SenseTranslation

        SenseTranslation.objects.filter(language_version__base_version=new_base).update(text="tomar")
        publish_word(word, "es", self.editor)
        st = ReviewState.objects.get(account=user, unit_key=str(word.pk))
        self.assertEqual(st.stability, 12)
        detail = client_for(user).get(f"/api/v1/words/{word.pk}").json()
        self.assertEqual(detail["senses"][0]["meaning"], "tomar")

    def _report(self):
        word = self.publish_he()
        return ContentReport.objects.create(word=word, account=student(), element="meaning", comment="mal")

    def test_e13_05_open_reports_listed_in_admin(self):
        self._report()
        self.editor.is_staff = True
        self.editor.save()
        self.client.force_login(self.editor)
        page = self.client.get("/admin/content/contentreport/")
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "mal")
        self.assertNotContains(page, "ana@example.com")

    def test_e13_05_resolution_audited(self):
        report = self._report()
        close_report(report, self.editor, "dismissed", "No es un error")
        self.assertEqual(report.status, "dismissed")
        self.assertTrue(AuditLog.objects.filter(action="content_report_closed", reason="No es un error").exists())
        with self.assertRaises(ValueError):
            close_report(report, self.editor, "fixed", "  ")

    def test_e13_05_resolution_emits_event(self):
        close_report(self._report(), self.editor, "fixed", "Corregido")
        self.assertEqual(Event.objects.get(name="content_report_resolved").props, {"outcome": "fixed", "days_open": 0})
