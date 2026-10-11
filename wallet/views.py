from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from . import services
from .analysis import expected_return
from .charts import polyline


@login_required
def dashboard(request):
    wallet = services.get_wallet(request.user)
    summary = services.summary(wallet)
    latest = wallet.transactions.order_by("-created_at", "-id").values_list("balance_after", flat=True)[:200]
    chart = polyline(list(reversed(list(latest))), baseline=services.INITIAL_BONUS)
    context = {
        "wallet": wallet,
        "summary": summary,
        "chart": chart,
        "theory": expected_return(request.user),
        "initial_bonus": services.INITIAL_BONUS,
        "recharge_amount": services.RECHARGE_AMOUNT,
    }
    return render(request, "wallet/dashboard.html", context)


@login_required
def statement(request):
    wallet = services.get_wallet(request.user)
    paginator = Paginator(wallet.transactions.all(), 50)
    page = paginator.get_page(request.GET.get("pagina"))
    return render(request, "wallet/statement.html", {"wallet": wallet, "page": page})


@login_required
@require_POST
def recharge(request):
    wallet = services.get_wallet(request.user)
    services.recharge(wallet)
    messages.info(
        request,
        f"Recarga nº {wallet.recharges}: mais F$ {services.RECHARGE_AMOUNT:.0f} em fichas fictícias. "
        "Num jogo de verdade, esse seria dinheiro novo saindo do seu bolso.",
    )
    return redirect("wallet:dashboard")
