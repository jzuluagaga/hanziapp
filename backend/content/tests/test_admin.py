from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from content.models import Example

from .helpers import make_base, make_language, setup_syllabus


class AdminSmokeTests(TestCase):
    def setUp(self):
        self.words = setup_syllabus()
        self.base = make_base(self.words["喝"])
        self.lang = make_language(self.base)
        admin = get_user_model().objects.create_superuser(email="admin@example.com", password="x", username="admin")
        self.client.force_login(admin)

    def test_pages_load(self):
        sense = self.base.senses.get()
        for url in [
            reverse("admin:content_word_changelist"),
            reverse("admin:content_wordbaseversion_changelist"),
            reverse("admin:content_wordbaseversion_change", args=[self.base.pk]),
            reverse("admin:content_sense_change", args=[sense.pk]),
            reverse("admin:content_languagecontentversion_change", args=[self.lang.pk]),
            reverse("admin:ops_parameter_changelist"),
            reverse("admin:languages_language_changelist"),
        ]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_editing_example_recomputes_pinyin_and_revalidates(self):
        sense = self.base.senses.get()
        examples = list(sense.examples.order_by("position"))
        data = {
            "position": sense.position, "pos": sense.pos, "reading": "", "source_gloss": "",
            "examples-TOTAL_FORMS": "3", "examples-INITIAL_FORMS": "3",
            "examples-MIN_NUM_FORMS": "0", "examples-MAX_NUM_FORMS": "1000",
        }
        for i, e in enumerate(examples):
            data.update({f"examples-{i}-id": e.pk, f"examples-{i}-sense": sense.pk,
                         f"examples-{i}-position": e.position, f"examples-{i}-text_zh": e.text_zh,
                         f"examples-{i}-pinyin": e.pinyin})
        data["examples-0-text_zh"] = "他喝水。"
        response = self.client.post(reverse("admin:content_sense_change", args=[sense.pk]), data)
        self.assertEqual(response.status_code, 302, getattr(response, "context", None) and response.context.get("errors"))
        self.assertEqual(Example.objects.get(pk=examples[0].pk).pinyin, "tā hē shuǐ.")
        # La traducción quedó desfasada y la validación de idioma lo marca.
        failed = {v.code for v in self.lang.validations.all() if not v.passed}
        self.assertIn("translation_complete", failed)
