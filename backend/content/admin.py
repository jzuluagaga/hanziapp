"""
Panel del editor (D-13, HU-E13-03): revisar, editar (revalida) y publicar,
palabra por palabra o por lote. Lo publicado no se edita: se abre una
corrección (HU-E13-04).
"""
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.utils.html import format_html, format_html_join

from .models import (
    AudioAsset, ContentReport, Example, WordTheme, ExampleTranslation, GenerationJob, LanguageContentVersion, Sense,
    SenseTranslation, ThirdPartyGloss, ValidationResult, VersionStatus, Word, WordBaseVersion,
)
from .services.editorial import (
    PublishError, editorial_status, publish_base, publish_language, start_correction,
)
from .services.environment import build_environment
from .services.validation import example_pinyin, validate_base, validate_language


def _validation_summary(version):
    results = list(version.validations.all())
    if not results:
        return "sin validar"
    failed = [r for r in results if not r.passed]
    if not failed:
        return format_html('<span style="color:#16794a">✓ todas</span>')
    return format_html_join(
        format_html("<br>"), '<span style="color:#b42318" title="{}">✗ {}</span>',
        ((r.detail, r.code) for r in failed),
    )


def _revalidate_base(base, env=None):
    env = env or build_environment()
    validate_base(base, env)
    for lang in base.language_versions.filter(status=VersionStatus.DRAFT):
        validate_language(lang, env)


class _ReadOnlyUnlessDraft:
    """Las versiones publicadas o archivadas no se editan (R-CON-05)."""

    def _version_of(self, obj):
        return obj

    def has_change_permission(self, request, obj=None):
        v = self._version_of(obj) if obj is not None else None
        if v is not None and v.status != VersionStatus.DRAFT:
            return False
        return super().has_change_permission(request, obj)


class ValidationInline(admin.TabularInline):
    model = ValidationResult
    extra = 0
    can_delete = False
    fields = ("code", "passed", "detail")
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


class BaseValidationInline(ValidationInline):
    fk_name = "base_version"


class LanguageValidationInline(ValidationInline):
    fk_name = "language_version"


class ThirdPartyGlossInline(admin.TabularInline):
    model = ThirdPartyGloss
    extra = 0
    fields = ("source", "position", "pos_raw", "gloss", "is_primary")
    readonly_fields = fields
    verbose_name_plural = "Glosas de terceros (uso interno, nunca se muestran)"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ("syllabus_order", "hanzi", "pinyin", "hsk_level", "base_status", "es_status")
    list_display_links = ("hanzi",)
    list_filter = ("hsk_level",)
    search_fields = ("hanzi", "pinyin")
    readonly_fields = ("created_at", "updated_at")
    inlines = [ThirdPartyGlossInline]
    actions = ["action_start_correction"]

    @admin.display(description="base")
    def base_status(self, obj):
        return editorial_status(obj)

    @admin.display(description="es")
    def es_status(self, obj):
        return editorial_status(obj, "es")

    @admin.action(description="Abrir corrección de lo publicado")
    def action_start_correction(self, request, queryset):
        for word in queryset:
            try:
                start_correction(word, request.user)
                self.message_user(request, f"{word.hanzi}: borrador de corrección creado.")
            except (PublishError, PermissionDenied) as e:
                self.message_user(request, f"{word.hanzi}: {e}", messages.ERROR)


class SenseInline(admin.TabularInline):
    model = Sense
    extra = 0
    fields = ("position", "pos", "reading", "source_gloss", "examples_preview")
    readonly_fields = ("examples_preview",)
    show_change_link = True

    @admin.display(description="ejemplos (editar en el enlace)")
    def examples_preview(self, obj):
        return format_html_join(format_html("<br>"), "{} <small>{}</small>",
                                ((e.text_zh, e.pinyin) for e in obj.examples.all()))

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "source_gloss":
            kwargs["queryset"] = ThirdPartyGloss.objects.select_related("word")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class _PublishActions:
    @admin.action(description="Volver a validar")
    def action_validate(self, request, queryset):
        env = build_environment()
        for v in queryset.filter(status=VersionStatus.DRAFT):
            (validate_base if isinstance(v, WordBaseVersion) else validate_language)(v, env)
        self.message_user(request, "Validaciones actualizadas.")

    @admin.action(description="Publicar los seleccionados")
    def action_publish(self, request, queryset):
        ok = 0
        for v in queryset.filter(status=VersionStatus.DRAFT):
            try:
                (publish_base if isinstance(v, WordBaseVersion) else publish_language)(v, request.user)
                ok += 1
            except (PublishError, PermissionDenied) as e:
                self.message_user(request, f"{v.word.hanzi}: {e}", messages.ERROR)
        if ok:
            self.message_user(request, f"Publicados: {ok}.")


@admin.register(WordBaseVersion)
class WordBaseVersionAdmin(_PublishActions, _ReadOnlyUnlessDraft, admin.ModelAdmin):
    list_display = ("word", "status", "origin", "validations_col", "published_at", "published_by")
    list_filter = ("status", "origin", "word__hsk_level")
    search_fields = ("word__hanzi",)
    readonly_fields = ("word", "status", "origin", "published_at", "published_by", "generation_meta")
    inlines = [SenseInline, BaseValidationInline]
    actions = ["action_publish", "action_validate"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("word", "published_by").prefetch_related("validations")

    @admin.display(description="validaciones")
    def validations_col(self, obj):
        return _validation_summary(obj)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        _revalidate_base(form.instance)


class ExampleInline(admin.TabularInline):
    model = Example
    extra = 0
    fields = ("position", "text_zh", "pinyin")


@admin.register(Sense)
class SenseAdmin(_ReadOnlyUnlessDraft, admin.ModelAdmin):
    list_display = ("__str__", "pos", "reading")
    fields = ("base_version", "position", "pos", "reading", "source_gloss")
    readonly_fields = ("base_version",)
    inlines = [ExampleInline]
    search_fields = ("base_version__word__hanzi",)

    def _version_of(self, obj):
        return obj.base_version

    def has_module_permission(self, request):
        return False  # se llega desde la base

    def save_formset(self, request, form, formset, change):
        """Si cambia el chino o la lectura y no se tocó el pinyin, se recalcula."""
        env = build_environment()
        sense = form.instance
        instances = formset.save(commit=False)
        for ex in instances:
            old =Example.objects.filter(pk=ex.pk).first() if ex.pk else None
            text_changed = old is None or old.text_zh != ex.text_zh
            pinyin_untouched = old is None or old.pinyin == ex.pinyin
            if (text_changed or "reading" in form.changed_data) and pinyin_untouched:
                ex.pinyin = example_pinyin(ex.text_zh, sense.base_version.word, sense.reading, env)
            ex.save()
        for obj in formset.deleted_objects:
            obj.delete()
        if "reading" in form.changed_data:
            for ex in sense.examples.exclude(pk__in=[i.pk for i in instances]):
                ex.pinyin = example_pinyin(ex.text_zh, sense.base_version.word, sense.reading, env)
                ex.save(update_fields=["pinyin"])

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        _revalidate_base(form.instance.base_version)


class SenseTranslationInline(admin.TabularInline):
    model = SenseTranslation
    extra = 0
    fields = ("sense", "sense_pos", "text")
    readonly_fields = ("sense", "sense_pos")
    verbose_name_plural = "Significados"

    @admin.display(description="categoría")
    def sense_pos(self, obj):
        return obj.sense.pos


class ExampleTranslationInline(admin.TabularInline):
    model = ExampleTranslation
    extra = 0
    fields = ("example_zh", "example_pinyin", "text", "stale")
    readonly_fields = ("example_zh", "example_pinyin", "stale")
    verbose_name_plural = "Traducciones de los ejemplos"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("example__sense").order_by("example__sense__position", "example__position")

    @admin.display(description="ejemplo")
    def example_zh(self, obj):
        return obj.example.text_zh

    @admin.display(description="pinyin")
    def example_pinyin(self, obj):
        return obj.example.pinyin

    @admin.display(description="¿desfasada?")
    def stale(self, obj):
        return "⚠ el chino cambió" if obj.source_text != obj.example.text_zh else ""


@admin.register(LanguageContentVersion)
class LanguageContentVersionAdmin(_PublishActions, _ReadOnlyUnlessDraft, admin.ModelAdmin):
    list_display = ("word", "language", "status", "origin", "validations_col", "published_at", "published_by")
    list_filter = ("language", "status", "origin", "word__hsk_level")
    search_fields = ("word__hanzi",)
    readonly_fields = ("word", "language", "base_version", "status", "origin", "published_at", "published_by",
                       "generation_meta")
    inlines = [SenseTranslationInline, ExampleTranslationInline, LanguageValidationInline]
    actions = ["action_publish", "action_validate"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("word", "published_by").prefetch_related("validations")

    @admin.display(description="validaciones")
    def validations_col(self, obj):
        return _validation_summary(obj)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for t in instances:
            if isinstance(t, ExampleTranslation):
                t.source_text = t.example.text_zh  # el editor confirma la traducción del chino actual
            t.save()
        for obj in formset.deleted_objects:
            obj.delete()

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        validate_language(form.instance)


@admin.register(AudioAsset)
class AudioAssetAdmin(admin.ModelAdmin):
    list_display = ("text", "spoken_language", "voice", "file", "created_at")
    list_filter = ("spoken_language", "voice")
    search_fields = ("text",)


@admin.register(GenerationJob)
class GenerationJobAdmin(admin.ModelAdmin):
    list_display = ("batch_id", "language", "model", "prompt_version", "status", "created_at", "collected_at")
    readonly_fields = [f.name for f in GenerationJob._meta.fields]

    def has_add_permission(self, request):
        return False


@admin.register(ContentReport)
class ContentReportAdmin(admin.ModelAdmin):
    """Reportes de estudiantes (HU-E13-05). El panel no muestra quién reportó."""

    list_display = ("created_at", "word", "element", "comment", "status")
    list_filter = ("status", "element")
    search_fields = ("word__hanzi", "comment")
    readonly_fields = ("word", "element", "comment", "created_at", "resolved_at", "status")
    exclude = ("account",)
    actions = ["mark_fixed", "mark_dismissed"]

    def has_module_permission(self, request):
        return request.user.has_perm("content.manage_content")

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm("content.manage_content")

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm("content.manage_content")

    def has_add_permission(self, request):
        return False

    def _close(self, request, queryset, outcome):
        from .services.reports import close_report

        reason = request.POST.get("reason") or ("Corregido en una versión nueva" if outcome == "fixed" else "Sin error")
        for report in queryset.filter(status=ContentReport.Status.OPEN):
            close_report(report, request.user, outcome, reason)

    @admin.action(description="Marcar como resuelto (corregido)")
    def mark_fixed(self, request, queryset):
        self._close(request, queryset, "fixed")

    @admin.action(description="Descartar (no era un error)")
    def mark_dismissed(self, request, queryset):
        self._close(request, queryset, "dismissed")


class _SubthemeFilter(admin.SimpleListFilter):
    title = "subtema"
    parameter_name = "subtheme"

    def lookups(self, request, model_admin):
        from .services.themes import taxonomy

        return [(s["key"], f"{t['es']} · {s['es']}") for t in taxonomy()["themes"] for s in t["subthemes"]]

    def queryset(self, request, queryset):
        return queryset.filter(subtheme=self.value()) if self.value() else queryset


@admin.register(WordTheme)
class WordThemeAdmin(admin.ModelAdmin):
    """Revisión de temas (D-49): las dudosas primero; se cambia el subtema en la lista y se aprueba por lote."""

    list_display = ("hanzi", "pinyin", "level", "meaning", "subtheme", "doubtful", "status")
    list_editable = ("subtheme",)
    list_filter = ("status", "doubtful", _SubthemeFilter, "word__hsk_level")
    search_fields = ("word__hanzi", "word__pinyin")
    actions = ["approve_selected"]
    list_per_page = 100

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("word").order_by("-doubtful", "word__hsk_level", "word__syllabus_order")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "subtheme":
            from django import forms

            from .services.themes import taxonomy

            choices = [(s["key"], f"{t['es']} · {s['es']}") for t in taxonomy()["themes"] for s in t["subthemes"]]
            return forms.ChoiceField(choices=choices)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def has_module_permission(self, request):
        return request.user.has_perm("content.manage_content")

    def has_view_permission(self, request, obj=None):
        return request.user.has_perm("content.manage_content")

    def has_change_permission(self, request, obj=None):
        return request.user.has_perm("content.manage_content")

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        if change and "subtheme" in form.changed_data:
            obj.origin, obj.doubtful = "manual", False
        super().save_model(request, obj, form, change)

    @admin.display(description="hanzi")
    def hanzi(self, obj):
        return obj.word.hanzi

    @admin.display(description="pinyin")
    def pinyin(self, obj):
        return obj.word.pinyin

    @admin.display(description="nivel")
    def level(self, obj):
        return obj.word.hsk_level

    @admin.display(description="significado")
    def meaning(self, obj):
        from .services.themes import _meanings

        return _meanings([obj.word]).get(obj.word_id, ("", ""))[1][:60]

    @admin.action(description="Aprobar los seleccionados")
    def approve_selected(self, request, queryset):
        from .services.themes import approve

        self.message_user(request, f"Aprobados: {approve(queryset, request.user)}")
