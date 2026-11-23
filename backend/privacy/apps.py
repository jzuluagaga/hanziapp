from django.apps import AppConfig


class PrivacyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "privacy"
    verbose_name = "Datos personales"

    def ready(self):
        from users.signals import account_created

        from .services import on_account_created

        account_created.connect(on_account_created, dispatch_uid="privacy_account_created")
