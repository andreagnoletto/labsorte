"""Serviços do jogo do bicho: apostar e realizar a extração."""

from django.db import transaction
from django.utils import timezone

from wallet.models import Transaction
from wallet.services import credit, debit, get_wallet

from .models import Bet, Draw
from .rules import MULTIPLIERS, Modality, Position, compute_payout, random_prizes


@transaction.atomic
def place_bet(user, modality, position, pick, stake) -> Bet:
    """Debita a aposta e a registra na extração aberta.

    Levanta ``wallet.services.InsufficientFunds`` sem criar nada.
    """
    wallet = get_wallet(user)
    draw = Draw.current()
    position_label = "cabeça" if position == Position.CABECA else "1º ao 5º"
    debit(
        wallet,
        stake,
        Transaction.Game.BICHO,
        f"Aposta: {Modality(modality).label} {pick} ({position_label}), extração nº {draw.number}",
    )
    return Bet.objects.create(
        user=user,
        draw=draw,
        modality=modality,
        position=position,
        pick=pick,
        stake=stake,
        multiplier=MULTIPLIERS[modality],
    )


@transaction.atomic
def run_draw(prizes: list[str] | None = None) -> Draw:
    """Encerra a extração aberta, liquida as apostas pendentes e abre a próxima."""
    draw = Draw.current()
    draw.prizes = list(prizes) if prizes else random_prizes()
    draw.status = Draw.Status.CLOSED
    draw.drawn_at = timezone.now()
    draw.save(update_fields=["prizes", "status", "drawn_at"])

    for bet in draw.bets.filter(status=Bet.Status.PENDING).select_related("user"):
        amount = compute_payout(bet.modality, bet.position, bet.pick, bet.stake, draw.prizes)
        if amount > 0:
            credit(
                get_wallet(bet.user),
                amount,
                Transaction.Kind.PAYOUT,
                Transaction.Game.BICHO,
                f"Prêmio: {Modality(bet.modality).label} {bet.pick_label} na extração nº {draw.number}",
            )
            bet.status = Bet.Status.WON
            bet.payout = amount
        else:
            bet.status = Bet.Status.LOST
        bet.save(update_fields=["status", "payout"])

    Draw.objects.create(number=draw.number + 1)
    return draw
