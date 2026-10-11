"""Regras puras do jogo do bicho: tabela dos bichos, modalidades e pagamentos.

Nada aqui toca o banco de dados; tudo é determinístico e testável isoladamente.
"""

import random
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

from django.db import models

PRIZE_COUNT = 5


@dataclass(frozen=True)
class Animal:
    group: int
    name: str
    emoji: str

    @property
    def dezenas(self) -> list[str]:
        """As quatro dezenas do grupo; a dezena 00 pertence ao grupo 25."""
        return [f"{(self.group - 1) * 4 + i:02d}"[-2:] for i in range(1, 5)]

    @property
    def code(self) -> str:
        return f"{self.group:02d}"


_NAMES = [
    ("Avestruz", "🪶"), ("Águia", "🦅"), ("Burro", "🐴"), ("Borboleta", "🦋"),
    ("Cachorro", "🐕"), ("Cabra", "🐐"), ("Carneiro", "🐏"), ("Camelo", "🐪"),
    ("Cobra", "🐍"), ("Coelho", "🐇"), ("Cavalo", "🐎"), ("Elefante", "🐘"),
    ("Galo", "🐓"), ("Gato", "🐈"), ("Jacaré", "🐊"), ("Leão", "🦁"),
    ("Macaco", "🐒"), ("Porco", "🐖"), ("Pavão", "🦚"), ("Peru", "🦃"),
    ("Touro", "🐂"), ("Tigre", "🐅"), ("Urso", "🐻"), ("Veado", "🦌"),
    ("Vaca", "🐄"),
]

ANIMALS: list[Animal] = [Animal(i + 1, name, emoji) for i, (name, emoji) in enumerate(_NAMES)]


def group_for_dezena(dezena: int) -> int:
    """Grupo (1..25) de uma dezena (0..99). 00 conta como 100 → grupo 25."""
    n = dezena if dezena != 0 else 100
    return (n - 1) // 4 + 1


def animal_for_group(group: int) -> Animal:
    return ANIMALS[group - 1]


def animal_for_prize(prize: str) -> Animal:
    """Bicho sorteado por um prêmio de 4 dígitos (pela dezena final)."""
    return animal_for_group(group_for_dezena(int(prize[-2:])))


class Modality(models.TextChoices):
    GRUPO = "GRUPO", "Grupo"
    DEZENA = "DEZENA", "Dezena"
    CENTENA = "CENTENA", "Centena"
    MILHAR = "MILHAR", "Milhar"


class Position(models.TextChoices):
    CABECA = "CABECA", "Na cabeça (1º prêmio)"
    CERCADO = "CERCADO", "Do 1º ao 5º prêmio"


MULTIPLIERS: dict[str, Decimal] = {
    Modality.GRUPO: Decimal("18"),
    Modality.DEZENA: Decimal("60"),
    Modality.CENTENA: Decimal("600"),
    Modality.MILHAR: Decimal("4000"),
}

PROBABILITY: dict[str, Fraction] = {
    Modality.GRUPO: Fraction(1, 25),
    Modality.DEZENA: Fraction(1, 100),
    Modality.CENTENA: Fraction(1, 1000),
    Modality.MILHAR: Fraction(1, 10000),
}

PICK_LENGTH: dict[str, int] = {
    Modality.GRUPO: 2,
    Modality.DEZENA: 2,
    Modality.CENTENA: 3,
    Modality.MILHAR: 4,
}


def normalize_pick(modality: str, raw: str) -> str:
    """Limpa e completa com zeros o palpite; levanta ValueError se inválido."""
    text = (raw or "").strip()
    if not (text.isascii() and text.isdigit()):  # isdigit() sozinho aceita "²" e dígitos de outros alfabetos
        raise ValueError("Informe apenas números.")
    length = PICK_LENGTH[modality]
    if len(text) > length:
        raise ValueError(f"{Modality(modality).label} tem no máximo {length} dígitos.")
    pick = text.zfill(length)
    if modality == Modality.GRUPO and not 1 <= int(pick) <= 25:
        raise ValueError("O grupo vai de 01 (Avestruz) a 25 (Vaca).")
    return pick


def matches(modality: str, pick: str, prize: str) -> bool:
    """O palpite acerta este prêmio?"""
    if modality == Modality.GRUPO:
        return group_for_dezena(int(prize[-2:])) == int(pick)
    return prize.endswith(pick)


def compute_payout(modality: str, position: str, pick: str, stake: Decimal, prizes: list[str]) -> Decimal:
    """Prêmio total de uma aposta diante dos 5 prêmios sorteados.

    Na cabeça só vale o 1º prêmio, pagando o multiplicador cheio. Do 1º ao 5º,
    cada prêmio acertado paga ``multiplicador / 5`` — por isso a vantagem da
    banca é a mesma nas duas posições.
    """
    multiplier = MULTIPLIERS[modality]
    if position == Position.CABECA:
        return stake * multiplier if matches(modality, pick, prizes[0]) else Decimal("0")
    hits = sum(1 for prize in prizes[:PRIZE_COUNT] if matches(modality, pick, prize))
    return stake * multiplier / PRIZE_COUNT * hits


def house_edge(modality: str) -> Fraction:
    """Fração da aposta que, em média, fica com a banca."""
    return 1 - PROBABILITY[modality] * Fraction(MULTIPLIERS[modality])


def odds_table() -> list[dict]:
    """Linhas para a tabela educativa: probabilidade, pagamento, justo, vantagem."""
    rows = []
    for modality in Modality:
        probability = PROBABILITY[modality]
        rows.append(
            {
                "modality": modality,
                "label": modality.label,
                "probability": probability,
                "probability_pct": float(probability * 100),
                "one_in": probability.denominator,
                "multiplier": MULTIPLIERS[modality],
                "fair_multiplier": probability.denominator,
                "expected_return_pct": float((1 - house_edge(modality)) * 100),
                "house_edge_pct": float(house_edge(modality) * 100),
            }
        )
    return rows


def random_prizes(rng: random.Random | None = None) -> list[str]:
    """Cinco prêmios de 0000 a 9999 (gerador criptográfico por padrão)."""
    rng = rng or random.SystemRandom()
    return [f"{rng.randrange(10000):04d}" for _ in range(PRIZE_COUNT)]
