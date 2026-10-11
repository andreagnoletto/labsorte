"""Caça-níquel de três rolos com retorno calculado por enumeração exata."""

import random
from decimal import Decimal
from fractions import Fraction
from itertools import product

SYMBOLS: dict[str, str] = {
    "cereja": "🍒",
    "limao": "🍋",
    "laranja": "🍊",
    "sino": "🔔",
    "estrela": "⭐",
    "sete": "7️⃣",
    "diamante": "💎",
}

NAMES: dict[str, str] = {
    "cereja": "Cereja",
    "limao": "Limão",
    "laranja": "Laranja",
    "sino": "Sino",
    "estrela": "Estrela",
    "sete": "Sete",
    "diamante": "Diamante",
}

# Cada rolo tem 20 posições; símbolos raros aparecem uma vez só.
REEL: list[str] = (
    ["cereja"] * 6 + ["limao"] * 5 + ["laranja"] * 4 + ["sino"] * 2 + ["estrela", "sete", "diamante"]
)
REELS = 3

PAYTABLE: dict[str, int] = {
    "cereja": 5,
    "limao": 8,
    "laranja": 15,
    "sino": 25,
    "estrela": 60,
    "sete": 150,
    "diamante": 1000,
}
TWO_CHERRIES = 2


def spin(rng: random.Random | None = None) -> tuple[str, str, str]:
    rng = rng or random.SystemRandom()
    return tuple(rng.choice(REEL) for _ in range(REELS))


def multiplier(reels) -> int:
    """Multiplicador da aposta para a combinação sorteada (0 se não paga)."""
    first, *rest = reels
    if all(symbol == first for symbol in rest):
        return PAYTABLE[first]
    if list(reels).count("cereja") == 2:
        return TWO_CHERRIES
    return 0


def compute_payout(stake: Decimal, reels) -> Decimal:
    return stake * multiplier(reels)


def rtp() -> Fraction:
    """Retorno ao jogador: média do multiplicador sobre as 8000 combinações."""
    total = sum(multiplier(combo) for combo in product(REEL, repeat=REELS))
    return Fraction(total, len(REEL) ** REELS)


def house_edge() -> Fraction:
    return 1 - rtp()


def paytable_rows() -> list[dict]:
    """Linhas da tabela de prêmios, do maior para o menor multiplicador."""
    combos = len(REEL) ** REELS
    rows = []
    for symbol, mult in sorted(PAYTABLE.items(), key=lambda item: -item[1]):
        count = REEL.count(symbol)
        probability = Fraction(count**REELS, combos)
        rows.append(
            {
                "symbols": SYMBOLS[symbol] * 3,
                "label": f"Três {NAMES[symbol].lower()}s" if symbol != "sete" else "Três setes",
                "multiplier": mult,
                "probability": probability,
                "contribution_pct": float(probability * mult * 100),
            }
        )
    cherries = REEL.count("cereja")
    two = Fraction(3 * cherries**2 * (len(REEL) - cherries), combos)
    rows.append(
        {
            "symbols": SYMBOLS["cereja"] * 2 + "·",
            "label": "Exatamente duas cerejas",
            "multiplier": TWO_CHERRIES,
            "probability": two,
            "contribution_pct": float(two * TWO_CHERRIES * 100),
        }
    )
    return rows
