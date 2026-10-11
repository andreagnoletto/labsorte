"""Roleta europeia: 37 casas (0 a 36), uma só verde."""

import random
from decimal import Decimal
from fractions import Fraction

from django.db import models

RED = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
POCKETS = 37

# Sequência física das casas na roda europeia, no sentido horário a partir do zero.
WHEEL_ORDER = [
    0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10,
    5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7, 28, 12, 35, 3, 26,
]


class BetType(models.TextChoices):
    NUMBER = "NUMBER", "Número"
    RED = "RED", "Vermelho"
    BLACK = "BLACK", "Preto"
    EVEN = "EVEN", "Par"
    ODD = "ODD", "Ímpar"
    LOW = "LOW", "Baixo (1 a 18)"
    HIGH = "HIGH", "Alto (19 a 36)"
    DOZEN = "DOZEN", "Dúzia"
    COLUMN = "COLUMN", "Coluna"


SIMPLE = {BetType.RED, BetType.BLACK, BetType.EVEN, BetType.ODD, BetType.LOW, BetType.HIGH}
GROUPED = {BetType.DOZEN, BetType.COLUMN}

MULTIPLIER: dict[str, Decimal] = {
    **{BetType.NUMBER: Decimal("36")},
    **{bet_type: Decimal("2") for bet_type in SIMPLE},
    **{bet_type: Decimal("3") for bet_type in GROUPED},
}

PROBABILITY: dict[str, Fraction] = {
    **{BetType.NUMBER: Fraction(1, POCKETS)},
    **{bet_type: Fraction(18, POCKETS) for bet_type in SIMPLE},
    **{bet_type: Fraction(12, POCKETS) for bet_type in GROUPED},
}


def color(number: int) -> str:
    if number == 0:
        return "verde"
    return "vermelho" if number in RED else "preto"


def wins(bet_type: str, selection: str, number: int) -> bool:
    """A aposta ``bet_type``/``selection`` ganha com o número sorteado?"""
    if bet_type == BetType.NUMBER:
        return number == int(selection)
    if number == 0:
        return False  # o zero derruba todas as apostas externas
    if bet_type == BetType.RED:
        return number in RED
    if bet_type == BetType.BLACK:
        return number not in RED
    if bet_type == BetType.EVEN:
        return number % 2 == 0
    if bet_type == BetType.ODD:
        return number % 2 == 1
    if bet_type == BetType.LOW:
        return number <= 18
    if bet_type == BetType.HIGH:
        return number >= 19
    if bet_type == BetType.DOZEN:
        return (number - 1) // 12 + 1 == int(selection)
    if bet_type == BetType.COLUMN:
        return (number - 1) % 3 + 1 == int(selection)
    raise ValueError(f"Tipo de aposta desconhecido: {bet_type}")


def validate_selection(bet_type: str, selection: str) -> str:
    """Normaliza a seleção para o tipo de aposta; levanta ValueError se inválida."""
    text = (selection or "").strip()
    if bet_type == BetType.NUMBER:
        if not (text.isascii() and text.isdigit()) or not 0 <= int(text) <= 36:
            raise ValueError("Escolha um número de 0 a 36.")
        return str(int(text))
    if bet_type in GROUPED:
        if text not in {"1", "2", "3"}:
            raise ValueError("Escolha 1, 2 ou 3.")
        return text
    return ""


def describe(bet_type: str, selection: str) -> str:
    if bet_type == BetType.NUMBER:
        return f"Número {selection}"
    if bet_type == BetType.DOZEN:
        low = (int(selection) - 1) * 12 + 1
        return f"{selection}ª dúzia ({low} a {low + 11})"
    if bet_type == BetType.COLUMN:
        return f"{selection}ª coluna"
    return BetType(bet_type).label


def spin(rng: random.Random | None = None) -> int:
    rng = rng or random.SystemRandom()
    return rng.randrange(POCKETS)


def compute_payout(bet_type: str, selection: str, stake: Decimal, number: int) -> Decimal:
    if wins(bet_type, selection, number):
        return stake * MULTIPLIER[bet_type]
    return Decimal("0")


def house_edge(bet_type: str) -> Fraction:
    return 1 - PROBABILITY[bet_type] * Fraction(MULTIPLIER[bet_type])


def odds_table() -> list[dict]:
    rows = []
    for bet_type in BetType:
        probability = PROBABILITY[bet_type]
        rows.append(
            {
                "bet_type": bet_type,
                "label": bet_type.label,
                "probability": probability,
                "probability_pct": float(probability * 100),
                "multiplier": MULTIPLIER[bet_type],
                "fair_multiplier": float(1 / probability),
                "house_edge_pct": float(house_edge(bet_type) * 100),
            }
        )
    return rows
