"""Dado de seis faces: o exemplo mais simples de vantagem da casa."""

import random
from decimal import Decimal
from fractions import Fraction

FACES = 6
MULTIPLIER = Decimal("5")
PROBABILITY = Fraction(1, FACES)


def roll(rng: random.Random | None = None) -> int:
    rng = rng or random.SystemRandom()
    return rng.randint(1, FACES)


def compute_payout(pick: int, stake: Decimal, result: int) -> Decimal:
    return stake * MULTIPLIER if pick == result else Decimal("0")


def house_edge() -> Fraction:
    return 1 - PROBABILITY * Fraction(MULTIPLIER)
