"""Serviços do cassino: debitam, rodam o motor, pagam e registram a rodada."""

from decimal import Decimal

from django.db import transaction

from wallet.models import Transaction
from wallet.services import credit, debit, get_wallet

from . import dice, roulette, slots
from .models import CasinoRound


@transaction.atomic
def _play(user, game, stake, bet_label, outcome):
    """Fluxo comum: debita → sorteia → credita prêmio (se houver) → registra."""
    wallet = get_wallet(user)
    debit(wallet, stake, game, f"Aposta: {bet_label}")
    payout, details = outcome()
    if payout > 0:
        credit(wallet, payout, Transaction.Kind.PAYOUT, game, f"Prêmio: {bet_label}")
    return CasinoRound.objects.create(user=user, game=game, stake=stake, payout=payout, details=details)


def play_roulette(user, bet_type, selection, stake, rng=None) -> CasinoRound:
    selection = roulette.validate_selection(bet_type, selection)
    label = roulette.describe(bet_type, selection)

    def outcome():
        number = roulette.spin(rng)
        payout = roulette.compute_payout(bet_type, selection, stake, number)
        details = {
            "bet_type": bet_type,
            "selection": selection,
            "label": label,
            "number": number,
            "color": roulette.color(number),
        }
        return payout, details

    return _play(user, Transaction.Game.ROULETTE, stake, f"Roleta, {label.lower()}", outcome)


def play_slots(user, stake, rng=None) -> CasinoRound:
    def outcome():
        reels = slots.spin(rng)
        details = {
            "reels": list(reels),
            "symbols": [slots.SYMBOLS[symbol] for symbol in reels],
            "multiplier": slots.multiplier(reels),
        }
        return slots.compute_payout(stake, reels), details

    return _play(user, Transaction.Game.SLOTS, stake, "Caça-níquel", outcome)


def play_dice(user, pick, stake, rng=None) -> CasinoRound:
    pick = int(pick)

    def outcome():
        result = dice.roll(rng)
        return dice.compute_payout(pick, Decimal(stake), result), {"pick": pick, "result": result}

    return _play(user, Transaction.Game.DICE, stake, f"Dado, face {pick}", outcome)
