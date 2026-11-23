from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from progress.services import close_days


class Command(BaseCommand):
    help = "Cierra los días pasados de todas las cuentas (R-PRO-09). Programar cada hora."

    def handle(self, *args, **opts):
        n = sum(close_days(a) for a in get_user_model().objects.filter(is_active=True, suspended_at__isnull=True))
        self.stdout.write(f"Días cerrados: {n}")
