from django.apps import AppConfig


class EntitlementsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "entitlements"
    verbose_name = "Derechos de acceso"

    def ready(self):
        from users.signals import account_created

        from . import services

        def _default_grant(sender, account, **kwargs):
            services.grant_default(account)

        account_created.connect(_default_grant, dispatch_uid="entitlements_default_grant")
