from django.apps import AppConfig


class OpsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ops"
    verbose_name = "Operación"

    def ready(self):
        from django.db.models.signals import post_delete, post_save

        from . import params
        from .models import Parameter

        def _forget(sender, instance, **kwargs):
            params.forget(instance.key)

        post_save.connect(_forget, sender=Parameter, dispatch_uid="ops_param_forget_save")
        post_delete.connect(_forget, sender=Parameter, dispatch_uid="ops_param_forget_delete")
