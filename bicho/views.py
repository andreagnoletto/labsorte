from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from wallet.services import InsufficientFunds

from .forms import BetForm
from .models import Bet, Draw
from .rules import ANIMALS, odds_table
from .services import place_bet, run_draw


def index(request):
    form = BetForm(request.POST or None)
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if form.is_valid():
            data = form.cleaned_data
            try:
                bet = place_bet(request.user, data["modality"], data["position"], data["pick"], data["stake"])
            except InsufficientFunds as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(
                    request,
                    f"Aposta registrada: {bet.get_modality_display()} {bet.pick_label} "
                    f"({bet.position_short}), F$ {bet.stake:.0f} na extração nº {bet.draw.number}.",
                )
                return redirect("bicho:index")

    draw = Draw.current()
    last_draw = Draw.objects.filter(status=Draw.Status.CLOSED).order_by("-number").first()
    animate_draw = last_draw is not None and request.GET.get("sorteio") == str(last_draw.number)
    my_bets = []
    if request.user.is_authenticated:
        my_bets = Bet.objects.filter(user=request.user).select_related("draw")[:15]
    context = {
        "animals": ANIMALS,
        "draw": draw,
        "pending_count": draw.bets.filter(status=Bet.Status.PENDING).count(),
        "last_draw": last_draw,
        "animate_draw": animate_draw,
        "form": form,
        "my_bets": my_bets,
        "table": odds_table(),
    }
    return render(request, "bicho/index.html", context)


@login_required
@require_POST
def draw(request):
    closed = run_draw()
    total = closed.bets.count()
    messages.success(
        request,
        f"Extração nº {closed.number} sorteada, {total} aposta(s) liquidada(s). Veja o resultado no poste.",
    )
    return redirect(f"{reverse('bicho:index')}?sorteio={closed.number}")


def history(request):
    draws = Draw.objects.filter(status=Draw.Status.CLOSED).order_by("-number")[:50]
    return render(request, "bicho/history.html", {"draws": draws})
