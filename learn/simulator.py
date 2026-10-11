"""Simulador Monte Carlo: milhares de apostas de F$ 1 sem tocar na carteira."""

import random
from decimal import Decimal
from fractions import Fraction

from bicho import rules
from casino import dice, roulette, slots

MIN_ROUNDS = 100
MAX_ROUNDS = 50_000
MAX_POINTS = 400
ONE = Decimal("1")


def _bicho(modality: str, pick: str):
    def play(rng: random.Random) -> Decimal:
        head = f"{rng.randrange(10000):04d}"
        return rules.compute_payout(modality, rules.Position.CABECA, pick, ONE, [head])

    return play


def _roulette(bet_type: str, selection: str):
    def play(rng: random.Random) -> Decimal:
        return roulette.compute_payout(bet_type, selection, ONE, roulette.spin(rng))

    return play


GAMES: dict[str, dict] = {
    "BICHO_GRUPO": {
        "label": "Jogo do bicho: grupo na cabeça",
        "play": _bicho(rules.Modality.GRUPO, "01"),
        "rate": 1 - rules.house_edge(rules.Modality.GRUPO),
    },
    "BICHO_DEZENA": {
        "label": "Jogo do bicho: dezena na cabeça",
        "play": _bicho(rules.Modality.DEZENA, "01"),
        "rate": 1 - rules.house_edge(rules.Modality.DEZENA),
    },
    "BICHO_CENTENA": {
        "label": "Jogo do bicho: centena na cabeça",
        "play": _bicho(rules.Modality.CENTENA, "001"),
        "rate": 1 - rules.house_edge(rules.Modality.CENTENA),
    },
    "BICHO_MILHAR": {
        "label": "Jogo do bicho: milhar na cabeça",
        "play": _bicho(rules.Modality.MILHAR, "0001"),
        "rate": 1 - rules.house_edge(rules.Modality.MILHAR),
    },
    "ROULETTE_NUMBER": {
        "label": "Roleta: um número",
        "play": _roulette(roulette.BetType.NUMBER, "17"),
        "rate": 1 - roulette.house_edge(roulette.BetType.NUMBER),
    },
    "ROULETTE_RED": {
        "label": "Roleta: vermelho",
        "play": _roulette(roulette.BetType.RED, ""),
        "rate": 1 - roulette.house_edge(roulette.BetType.RED),
    },
    "SLOTS": {
        "label": "Caça-níquel: um giro",
        "play": lambda rng: slots.compute_payout(ONE, slots.spin(rng)),
        "rate": slots.rtp(),
    },
    "DICE": {
        "label": "Dado: acertar a face",
        "play": lambda rng: dice.compute_payout(6, ONE, dice.roll(rng)),
        "rate": 1 - dice.house_edge(),
    },
}


def simulate(game: str, rounds: int, seed: int | None = None) -> dict:
    """Aposta F$ 1 por rodada e devolve totais, sequências e a série do saldo."""
    if game not in GAMES:
        raise ValueError("Jogo desconhecido.")
    if not MIN_ROUNDS <= rounds <= MAX_ROUNDS:
        raise ValueError(f"Escolha entre {MIN_ROUNDS} e {MAX_ROUNDS} apostas.")
    spec = GAMES[game]
    rng = random.Random(seed) if seed is not None else random.Random()
    play = spec["play"]
    step = -(-rounds // MAX_POINTS)  # teto da divisão: no máximo MAX_POINTS pontos

    net = returned = wins = streak = longest = peak = trough = 0
    series: list[int] = []
    for index in range(1, rounds + 1):
        payout = int(play(rng))
        returned += payout
        net += payout - 1
        if payout > 0:
            wins += 1
            streak = 0
        else:
            streak += 1
            longest = max(longest, streak)
        peak = max(peak, net)
        trough = min(trough, net)
        if index % step == 0 or index == rounds:
            series.append(net)

    return {
        "game": game,
        "label": spec["label"],
        "rounds": rounds,
        "staked": rounds,
        "returned": returned,
        "net": net,
        "wins": wins,
        "return_rate": Fraction(returned, rounds),
        "theoretical_rate": spec["rate"],
        "longest_losing_streak": longest,
        "peak": peak,
        "trough": trough,
        "series": series,
    }
