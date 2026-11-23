from django.core.management.base import BaseCommand

from privacy.services import purge_voice_recordings


class Command(BaseCommand):
    help = "Borra las grabaciones de voz vencidas o revocadas (R-DAT-08). Programar a diario."

    def handle(self, *args, **opts):
        self.stdout.write(f"Grabaciones borradas: {purge_voice_recordings()}")
