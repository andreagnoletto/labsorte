"""Teoria × prática: quanto o usuário deveria ter recebido, pela matemática.

Lê os modelos dos jogos apenas para somar apostas já liquidadas; nunca os altera.
"""

from decimal import Decimal
from fractions import Fraction

from django.db.models import Sum

from bicho.models import Bet
from bicho.rules import house_edge as bicho_house_edge
from casino import dice, roulette, slots
from casino.models import CasinoRound

from .models import Transaction

CASINO_RETURN: dict[str, Fraction] = {
    Transaction.Game.ROULETTE: 1 - roulette.house_edge(roulette.BetType.RED),
    Transaction.Game.SLOTS: slots.rtp(),
    Transaction.Game.DICE: 1 - dice.house_edge(),
}


def _decimal(fraction: Fraction) -> Decimal:
    return Decimal(fraction.numerator) / Decimal(fraction.denominator)


def expected_return(user) -> dict:
    """Soma, só das apostas já liquidadas, o retorno esperado e o recebido."""
    settled_staked = Decimal("0")
    expected = Decimal("0")

    bicho_rows = (
        Bet.objects.filter(user=user)
        .exclude(status=Bet.Status.PENDING)
        .values("modality")
        .annotate(total=Sum("stake"))
    )
    for row in bicho_rows:
        settled_staked += row["total"]
        expected += row["total"] * _decimal(1 - bicho_house_edge(row["modality"]))

    casino_rows = CasinoRound.objects.filter(user=user).values("game").annotate(total=Sum("stake"))
    for row in casino_rows:
        settled_staked += row["total"]
        expected += row["total"] * _decimal(CASINO_RETURN[row["game"]])

    bicho_paid = Bet.objects.filter(user=user).aggregate(total=Sum("payout"))["total"] or Decimal("0")
    casino_paid = CasinoRound.objects.filter(user=user).aggregate(total=Sum("payout"))["total"] or Decimal("0")
    actual = bicho_paid + casino_paid

    return {
        "settled_staked": settled_staked,
        "expected_return": expected.quantize(Decimal("0.01")),
        "actual_return": actual,
        "expected_rate": (expected / settled_staked) if settled_staked else None,
        "actual_rate": (actual / settled_staked) if settled_staked else None,
    }
