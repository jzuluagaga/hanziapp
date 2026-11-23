from django.core.management.base import BaseCommand

from decks.services import build_system_decks


class Command(BaseCommand):
    help = "Arma (o rehace) los mazos del sistema de cada nivel (R-MAZ-02, D-43). Repetible."

    def add_arguments(self, parser):
        parser.add_argument("--level", type=int, action="append", help="Solo estos niveles.")

    def handle(self, *args, level=None, **opts):
        for lvl, n in build_system_decks(level).items():
            self.stdout.write(f"HSK {lvl}: {n} mazos")
