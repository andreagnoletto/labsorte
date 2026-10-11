from decimal import Decimal
from fractions import Fraction

from django.shortcuts import render

from bicho import rules
from casino import dice, roulette, slots
from wallet.charts import polyline

from .forms import SimulationForm
from .simulator import simulate


def comparative_rows() -> list[dict]:
    """Vantagem da banca por jogo e aposta, da menor para a maior."""
    rows = []
    for row in rules.odds_table():
        rows.append(
            {
                "game": "Jogo do bicho",
                "bet": f"{row['label']} na cabeça",
                "probability": row["probability"],
                "multiplier": row["multiplier"],
                "fair": row["fair_multiplier"],
                "edge_pct": row["house_edge_pct"],
            }
        )
    for bet_type in [roulette.BetType.NUMBER, roulette.BetType.RED, roulette.BetType.DOZEN]:
        probability = roulette.PROBABILITY[bet_type]
        rows.append(
            {
                "game": "Roleta",
                "bet": bet_type.label,
                "probability": probability,
                "multiplier": roulette.MULTIPLIER[bet_type],
                "fair": float(1 / probability),
                "edge_pct": float(roulette.house_edge(bet_type) * 100),
            }
        )
    rows.append(
        {
            "game": "Caça-níquel",
            "bet": "Um giro (todas as combinações)",
            "probability": None,
            "multiplier": None,
            "fair": None,
            "edge_pct": float(slots.house_edge() * 100),
        }
    )
    rows.append(
        {
            "game": "Dado",
            "bet": "Acertar a face",
            "probability": dice.PROBABILITY,
            "multiplier": dice.MULTIPLIER,
            "fair": dice.FACES,
            "edge_pct": float(dice.house_edge() * 100),
        }
    )
    return sorted(rows, key=lambda row: row["edge_pct"])


def index(request):
    return render(request, "learn/index.html", {"rows": comparative_rows()})


def bicho(request):
    return render(request, "learn/bicho.html", {"animals": rules.ANIMALS, "table": rules.odds_table()})


def probability(request):
    return render(request, "learn/probability.html", {"table": rules.odds_table()})


def fallacies(request):
    return render(request, "learn/fallacies.html")


def legal(request):
    return render(request, "learn/legal.html")


def simulator(request):
    form = SimulationForm(request.POST or None)
    result = chart = None
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        result = simulate(data["game"], data["rounds"], data["seed"])
        expected = -(1 - result["theoretical_rate"]) * result["rounds"]
        expected_end = (Decimal(expected.numerator) / Decimal(expected.denominator)).quantize(Decimal("0.01"))
        chart = polyline(result["series"], baseline=0, extra=[[0, expected_end]])
        result["expected_net"] = float(expected_end)
        result["return_pct"] = float(result["return_rate"] * 100)
        result["theoretical_pct"] = float(result["theoretical_rate"] * 100)
        result["win_pct"] = float(Fraction(result["wins"], result["rounds"]) * 100)
    return render(request, "learn/simulator.html", {"form": form, "result": result, "chart": chart})
