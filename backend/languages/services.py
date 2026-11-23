from .models import Language


def get_language(code: str) -> Language:
    """Devuelve un idioma cargado (activo o no). Lanza Language.DoesNotExist si no existe."""
    return Language.objects.get(code=code)


def loaded_languages() -> list[Language]:
    return list(Language.objects.all())
