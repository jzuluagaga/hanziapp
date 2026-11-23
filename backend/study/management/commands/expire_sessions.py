from django.core.management.base import BaseCommand

from study.services import expire_sessions


class Command(BaseCommand):
    help = "Caduca las sesiones sin actividad en `session_ttl_days` (R-SES-08). Programar a diario."

    def handle(self, *args, **opts):
        self.stdout.write(f"Sesiones caducadas: {expire_sessions()}")
