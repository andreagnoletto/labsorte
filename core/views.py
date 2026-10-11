from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from bicho.rules import ANIMALS, Modality
from bicho.rules import house_edge as bicho_edge
from casino import dice, roulette, slots
from wallet.services import INITIAL_BONUS, get_wallet


def house_edges() -> dict[str, float]:
    """Vantagem da banca (em %) de cada jogo, calculada pelos próprios motores."""
    return {
        "bicho_min": float(bicho_edge(Modality.GRUPO) * 100),
        "bicho_max": float(bicho_edge(Modality.MILHAR) * 100),
        "roulette": float(roulette.house_edge(roulette.BetType.RED) * 100),
        "slots": float(slots.house_edge() * 100),
        "dice": float(dice.house_edge() * 100),
    }


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["animals"] = ANIMALS
        context["initial_bonus"] = INITIAL_BONUS
        context["edges"] = house_edges()
        return context


class SignupView(FormView):
    template_name = "core/signup.html"
    form_class = UserCreationForm
    success_url = reverse_lazy("core:home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("core:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        get_wallet(user)
        login(self.request, user)
        messages.success(
            self.request,
            f"Conta criada. Você recebeu F$ {INITIAL_BONUS:.0f} em fichas fictícias para estudar.",
        )
        return super().form_valid(form)
