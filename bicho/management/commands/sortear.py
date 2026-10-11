from django.core.management.base import BaseCommand

from bicho.models import Bet
from bicho.services import run_draw


class Command(BaseCommand):
    help = "Encerra a extração aberta, liquida as apostas pendentes e abre a próxima."

    def handle(self, *args, **options):
        draw = run_draw()
        if options["verbosity"] < 1:
            return
        self.stdout.write(self.style.SUCCESS(f"Extração nº {draw.number} encerrada."))
        for order, (prize, animal) in enumerate(draw.prize_animals, start=1):
            self.stdout.write(f"  {order}º prêmio: {prize}  →  {animal.code} {animal.name}")
        total = draw.bets.count()
        won = draw.bets.filter(status=Bet.Status.WON).count()
        self.stdout.write(f"  {total} aposta(s) liquidada(s), {won} premiada(s).")
