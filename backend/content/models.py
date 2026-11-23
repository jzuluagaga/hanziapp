"""
Módulo `content` (09-arquitectura.md §2): palabras, base, contenido por idioma,
versiones, validaciones y audio. Reglas R-CON.

Dos capas con estado editorial propio (R-CON-04, D-11):

    Word ─┬─ WordBaseVersion (acepciones + ejemplos en chino, común a todos los idiomas)
          │      └─ Sense ─ Example
          └─ LanguageContentVersion (por idioma: significados y traducciones)
                 ├─ SenseTranslation  → Sense
                 └─ ExampleTranslation → Example

De cada capa hay como máximo un borrador y una versión publicada (R-CON-05),
garantizado por restricciones en la base. Las lecturas de estudiantes solo
deben consultar versiones publicadas (09-arquitectura.md §5).
"""
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from .pos import POS_CHOICES


class VersionStatus(models.TextChoices):
    DRAFT = "draft", "draft"
    PUBLISHED = "published", "published"
    ARCHIVED = "archived", "archived"  # antes publicada, reemplazada por otra


class Origin(models.TextChoices):
    GENERATED = "generated", "generated"
    IMPORTED = "imported", "imported"
    MANUAL = "manual", "manual"


class Word(models.Model):
    """Entrada del sílabo. Su id es el identificador estable (R-CON-03)."""

    hanzi = models.CharField(max_length=20)
    pinyin = models.CharField(max_length=100, help_text="Pinyin del sílabo. No se recalcula (08-contenido.md §2).")
    hsk_level = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(6)])
    syllabus_order = models.PositiveIntegerField(help_text="Número de orden en el sílabo.")
    retired_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["hsk_level", "syllabus_order"]
        constraints = [
            models.UniqueConstraint(fields=["hsk_level", "syllabus_order"], name="word_unique_syllabus_position"),
        ]
        permissions = [("manage_content", "Editor: cargar, revisar y publicar contenido")]

    def __str__(self):
        return f"{self.hanzi} ({self.pinyin}) · HSK {self.hsk_level} #{self.syllabus_order}"


class ThirdPartyGloss(models.Model):
    """Glosa de terceros (R-CON-02): solo ancla interna de generación. Nunca se muestra."""

    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="third_party_glosses")
    source = models.CharField(max_length=60)
    position = models.PositiveSmallIntegerField()
    pos_raw = models.CharField(max_length=60, blank=True)
    gloss = models.TextField()
    is_primary = models.BooleanField(default=True)

    class Meta:
        ordering = ["word", "source", "position"]
        constraints = [
            models.UniqueConstraint(fields=["word", "source", "position"], name="gloss_unique_position"),
        ]

    def __str__(self):
        return f"[{self.source}] {self.word.hanzi}: {self.gloss}"


class _Version(models.Model):
    status = models.CharField(max_length=10, choices=VersionStatus.choices, default=VersionStatus.DRAFT)
    origin = models.CharField(max_length=10, choices=Origin.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+",
    )
    generation_meta = models.JSONField(default=dict, blank=True, help_text="Modelo, versión de prompt y lote de origen.")

    class Meta:
        abstract = True


class WordBaseVersion(_Version):
    """Base de la palabra: acepciones y ejemplos en chino (R-CON-04)."""

    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="base_versions")

    class Meta:
        ordering = ["word", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["word"], condition=Q(status="draft"), name="base_one_draft"),
            models.UniqueConstraint(fields=["word"], condition=Q(status="published"), name="base_one_published"),
        ]

    def __str__(self):
        return f"Base {self.word.hanzi} · {self.status} · {self.origin}"


class Sense(models.Model):
    """Acepción: un significado de la palabra con su categoría gramatical (común a todos los idiomas)."""

    base_version = models.ForeignKey(WordBaseVersion, on_delete=models.CASCADE, related_name="senses")
    position = models.PositiveSmallIntegerField()
    pos = models.CharField("categoría gramatical", max_length=30, choices=POS_CHOICES, blank=True)
    reading = models.CharField(
        max_length=60, blank=True,
        help_text="Pinyin de la palabra en esta acepción si difiere del sílabo (好 hào). Vacío = el del sílabo.",
    )
    source_gloss = models.ForeignKey(ThirdPartyGloss, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["base_version", "position"]
        constraints = [models.UniqueConstraint(fields=["base_version", "position"], name="sense_unique_position")]

    def __str__(self):
        return f"{self.base_version.word.hanzi} #{self.position} ({self.pos or '?'})"


class Example(models.Model):
    """Oración en chino, con pinyin, que ilustra una acepción."""

    sense = models.ForeignKey(Sense, on_delete=models.CASCADE, related_name="examples")
    position = models.PositiveSmallIntegerField()
    text_zh = models.CharField(max_length=200)
    pinyin = models.CharField(max_length=400, blank=True)

    class Meta:
        ordering = ["sense", "position"]
        constraints = [models.UniqueConstraint(fields=["sense", "position"], name="example_unique_position")]

    def __str__(self):
        return self.text_zh


class LanguageContentVersion(_Version):
    """Contenido por idioma: significados y traducciones de una base concreta (R-IDI-05)."""

    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="language_versions")
    language = models.ForeignKey("languages.Language", on_delete=models.PROTECT, related_name="+")
    base_version = models.ForeignKey(
        WordBaseVersion, on_delete=models.PROTECT, related_name="language_versions",
        help_text="Base cuyas acepciones y ejemplos traduce.",
    )

    class Meta:
        ordering = ["word", "language", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["word", "language"], condition=Q(status="draft"), name="lang_one_draft"),
            models.UniqueConstraint(fields=["word", "language"], condition=Q(status="published"), name="lang_one_published"),
        ]

    def __str__(self):
        return f"{self.language_id} {self.word.hanzi} · {self.status} · {self.origin}"


class SenseTranslation(models.Model):
    """Significado: texto en el idioma de estudio que traduce una acepción."""

    language_version = models.ForeignKey(LanguageContentVersion, on_delete=models.CASCADE, related_name="sense_translations")
    sense = models.ForeignKey(Sense, on_delete=models.CASCADE, related_name="translations")
    text = models.CharField(max_length=255)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["language_version", "sense"], name="sense_translation_unique")]

    def __str__(self):
        return self.text


class ExampleTranslation(models.Model):
    """Traducción de un ejemplo. `source_text` guarda el chino traducido, para detectar
    traducciones que quedaron desfasadas si el ejemplo se edita."""

    language_version = models.ForeignKey(LanguageContentVersion, on_delete=models.CASCADE, related_name="example_translations")
    example = models.ForeignKey(Example, on_delete=models.CASCADE, related_name="translations")
    text = models.CharField(max_length=400)
    source_text = models.CharField(max_length=200)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["language_version", "example"], name="example_translation_unique")]

    def __str__(self):
        return self.text


class ValidationResult(models.Model):
    """Resultado de una validación automática sobre un borrador (08-contenido.md §3)."""

    base_version = models.ForeignKey(WordBaseVersion, null=True, blank=True, on_delete=models.CASCADE, related_name="validations")
    language_version = models.ForeignKey(LanguageContentVersion, null=True, blank=True, on_delete=models.CASCADE, related_name="validations")
    code = models.CharField(max_length=40)
    passed = models.BooleanField()
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]
        constraints = [
            models.CheckConstraint(
                condition=(Q(base_version__isnull=False) & Q(language_version__isnull=True))
                | (Q(base_version__isnull=True) & Q(language_version__isnull=False)),
                name="validation_one_layer",
            ),
        ]

    def __str__(self):
        return f"{'✓' if self.passed else '✗'} {self.code}"


class AudioAsset(models.Model):
    """Audio sintetizado, identificado por texto, idioma hablado y voz (R-IDI-08, R-CON-13)."""

    text = models.CharField(max_length=400)
    text_hash = models.CharField(max_length=64, help_text="SHA-256 del texto.")
    spoken_language = models.CharField(max_length=10, help_text="Idioma hablado, p. ej. 'zh'.")
    voice = models.CharField(max_length=100)
    file = models.CharField(max_length=500, help_text="Ruta en el almacenamiento (R2).")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["text_hash", "spoken_language", "voice"], name="audio_unique_text_language_voice"),
        ]

    def __str__(self):
        return f"{self.spoken_language}/{self.voice}: {self.text}"


class GenerationJob(models.Model):
    """Lote de generación enviado a la API, para retomarlo y no duplicar (HU-E13-02)."""

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "submitted"
        COLLECTED = "collected", "collected"

    batch_id = models.CharField(max_length=100, unique=True)
    language = models.ForeignKey("languages.Language", on_delete=models.PROTECT, related_name="+")
    model = models.CharField(max_length=60)
    effort = models.CharField(max_length=10, blank=True)
    prompt_version = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SUBMITTED)
    request_map = models.JSONField(help_text="custom_id → {word_id, mode, base_version_id}.")
    summary = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    collected_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.batch_id} ({self.language_id}, {self.status})"


class Character(models.Model):
    """Carácter con o sin datos de trazos (R-CON-12). Lo llena `load_characters` (08-contenido.md §2, paso 3).
    Mientras un carácter no tenga fila, se ofrece en escritura: Hanzi Writer cubre todo HSK 1–6."""

    char = models.CharField(max_length=1, primary_key=True)
    has_stroke_data = models.BooleanField(default=True)

    def __str__(self):
        return self.char


class ContentReport(models.Model):
    """Reporte de error de un estudiante sobre una palabra (R-CON-14)."""

    class Element(models.TextChoices):
        HANZI = "hanzi", "hanzi"
        PINYIN = "pinyin", "pinyin"
        MEANING = "meaning", "significado"
        EXAMPLE = "example", "ejemplo"
        AUDIO = "audio", "audio"
        STROKES = "strokes", "trazos"
        OTHER = "other", "otro"

    class Status(models.TextChoices):
        OPEN = "open", "abierto"
        RESOLVED = "resolved", "resuelto"
        DISMISSED = "dismissed", "descartado"

    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="reports")
    account = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="content_reports",
        help_text="Se desvincula al eliminar la cuenta (R-DAT-06).",
    )
    element = models.CharField(max_length=10, choices=Element.choices)
    comment = models.TextField(blank=True, max_length=1000)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    resolution = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["status", "-created_at"]

    def __str__(self):
        return f"{self.word.hanzi} · {self.element} · {self.status}"
