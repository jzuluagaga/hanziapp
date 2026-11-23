from django.apps import AppConfig


class ProgressConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "progress"
    verbose_name = "Progreso y hábito"

    def ready(self):
        from study.signals import answer_recorded

        from .services import on_answer_recorded

        answer_recorded.connect(on_answer_recorded, dispatch_uid="progress_answer_recorded")
