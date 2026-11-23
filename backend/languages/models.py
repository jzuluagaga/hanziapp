from django.db import models


class Language(models.Model):
    """
    Idioma de estudio y/o de interfaz (R-IDI-02). Los idiomas son datos: añadir
    uno es insertar una fila y encender sus interruptores (R-IDI-10), sin
    migraciones ni cambios de código.
    """

    code = models.CharField(max_length=10, primary_key=True, help_text="Código BCP 47, p. ej. 'es', 'en'.")
    name = models.CharField(max_length=60, help_text="Nombre del idioma en ese idioma (endónimo).")
    is_study_active = models.BooleanField(default=False)
    is_ui_active = models.BooleanField(default=False)

    # Datos que usa la tubería de contenido (08-contenido.md §8). Viven aquí para
    # que un idioma nuevo no exija tocar código.
    generation_name = models.CharField(
        max_length=120, blank=True,
        help_text="Cómo se nombra el idioma al pedir el contenido, p. ej. 'Spanish'.",
    )
    generation_style = models.TextField(
        blank=True,
        help_text="Indicaciones de variedad y estilo para significados y traducciones.",
    )
    function_words = models.JSONField(
        default=list, blank=True,
        help_text=(
            "Palabras funcionales frecuentes del idioma, en minúsculas. La validación "
            "translation_language las usa para detectar restos de otro idioma."
        ),
    )

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.name} ({self.code})"
