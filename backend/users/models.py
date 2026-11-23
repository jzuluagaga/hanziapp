"""
Módulo `accounts` (app `users`, nombre heredado; 09-arquitectura.md §2).
Cuentas, acceso, perfil y cohorte. Reglas R-CTA.
"""
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

from vocab.models import Word


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email).lower()
        extra_fields.setdefault('username', email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    hsk_target_level = models.IntegerField(default=1)  # heredado; lo sustituye la meta de examen (V2)
    cohort = models.CharField(max_length=60, blank=True, help_text="Cohorte del enlace de registro (R-CTA-10).")
    email_verified_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True, help_text="R-CTA-09: la suspensión no borra nada.")
    suspension_reason = models.TextField(blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        permissions = [("owner", "Dueño: métricas, soporte, concesiones y suspensiones")]


class Profile(models.Model):
    """Datos y preferencias editables de la cuenta (glosario §1)."""

    THEMES = [("system", "system"), ("light", "light"), ("dark", "dark")]

    account = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    name = models.CharField(max_length=80, blank=True)
    ui_language = models.ForeignKey("languages.Language", on_delete=models.PROTECT, related_name="+")
    study_language = models.ForeignKey("languages.Language", on_delete=models.PROTECT, related_name="+")
    timezone = models.CharField(max_length=64, default="America/Bogota")
    # R-PRO-02: la zona nueva rige desde el día siguiente. Hasta `timezone_changed_at` vale la anterior.
    previous_timezone = models.CharField(max_length=64, blank=True)
    timezone_changed_at = models.DateTimeField(null=True, blank=True)
    new_limit_recognition = models.PositiveSmallIntegerField(default=10)
    new_limit_writing = models.PositiveSmallIntegerField(default=5)
    theme = models.CharField(max_length=10, choices=THEMES, default="system")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Perfil de {self.account_id}"


class LoginFailure(models.Model):
    """Intento de acceso fallido, por correo (R-CTA-08). Se guarda exista o no la cuenta."""

    email = models.CharField(max_length=254, db_index=True)
    at = models.DateTimeField(auto_now_add=True)


class UserProgress(models.Model):
    """Heredado del MVP anterior; sin uso. Lo sustituye `scheduling.ReviewState`."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress')
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name='progress')
    ease_factor = models.FloatField(default=2.5)
    interval_days = models.IntegerField(default=1)
    next_review = models.DateTimeField()
    last_reviewed = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.word}"
