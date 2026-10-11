from django.contrib.auth.views import redirect_to_login
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from wallet.models import Transaction
from wallet.services import InsufficientFunds

from . import dice, roulette, slots
from .forms import DiceForm, RouletteForm, SlotsForm
from .models import CasinoRound
from .services import play_dice, play_roulette, play_slots

def _play_or_form(request, form_class, play):
    """Processa o POST; retorna (form, resposta_de_redirecionamento_ou_None)."""
    form = form_class(request.POST or None)
    if request.method == "POST":
        if not request.user.is_authenticated:
            return form, redirect_to_login(request.path)
        if form.is_valid():
            try:
                rnd = play(form.cleaned_data)
            except (InsufficientFunds, ValueError) as exc:
                form.add_error(None, str(exc))
            else:
                return form, redirect(f"{request.path}?r={rnd.pk}")
    return form, None


def _result_round(request, game):
    """Rodada indicada por ?r=, só do próprio usuário e do jogo certo."""
    key = request.GET.get("r")
    if not key:
        return None
    if not request.user.is_authenticated or not (key.isascii() and key.isdigit()):
        raise Http404
    return get_object_or_404(CasinoRound, pk=int(key), user=request.user, game=game)


def _recent(request, game):
    if not request.user.is_authenticated:
        return []
    return CasinoRound.objects.filter(user=request.user, game=game)[:10]


def roulette_view(request):
    game = Transaction.Game.ROULETTE
    form, response = _play_or_form(
        request,
        RouletteForm,
        lambda d: play_roulette(request.user, d["bet_type"], d["selection"], d["stake"]),
    )
    if response:
        return response
    context = {
        "form": form,
        "result": _result_round(request, game),
        "recent": _recent(request, game),
        "table": roulette.odds_table(),
        "board": [(n, roulette.color(n)) for n in range(37)],
        "wheel": [[n, roulette.color(n)] for n in roulette.WHEEL_ORDER],
        "house_edge_pct": float(roulette.house_edge(roulette.BetType.RED) * 100),
    }
    return render(request, "casino/roulette.html", context)


def slots_view(request):
    game = Transaction.Game.SLOTS
    form, response = _play_or_form(request, SlotsForm, lambda d: play_slots(request.user, d["stake"]))
    if response:
        return response
    context = {
        "form": form,
        "result": _result_round(request, game),
        "recent": _recent(request, game),
        "paytable": slots.paytable_rows(),
        "symbol_list": list(slots.SYMBOLS.values()),
        "reel": [(symbol, slots.SYMBOLS[symbol], slots.NAMES[symbol], slots.REEL.count(symbol)) for symbol in slots.SYMBOLS],
        "reel_size": len(slots.REEL),
        "rtp_pct": float(slots.rtp() * 100),
        "house_edge_pct": float(slots.house_edge() * 100),
    }
    return render(request, "casino/slots.html", context)


def dice_view(request):
    game = Transaction.Game.DICE
    form, response = _play_or_form(request, DiceForm, lambda d: play_dice(request.user, d["pick"], d["stake"]))
    if response:
        return response
    context = {
        "form": form,
        "result": _result_round(request, game),
        "recent": _recent(request, game),
        "multiplier": dice.MULTIPLIER,
        "fair_multiplier": dice.FACES,
        "probability_pct": float(dice.PROBABILITY * 100),
        "house_edge_pct": float(dice.house_edge() * 100),
    }
    return render(request, "casino/dice.html", context)
