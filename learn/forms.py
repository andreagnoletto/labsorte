from django import forms

from .simulator import GAMES, MAX_ROUNDS, MIN_ROUNDS


class SimulationForm(forms.Form):
    game = forms.ChoiceField(
        label="Jogo e aposta",
        choices=[(key, spec["label"]) for key, spec in GAMES.items()],
        initial="BICHO_GRUPO",
    )
    rounds = forms.IntegerField(
        label="Quantas apostas de F$ 1",
        min_value=MIN_ROUNDS,
        max_value=MAX_ROUNDS,
        initial=1000,
        help_text=f"De {MIN_ROUNDS} a {MAX_ROUNDS}. Experimente 100 e depois 50000.",
    )
    seed = forms.IntegerField(
        label="Semente (opcional)",
        required=False,
        help_text="Com a mesma semente o sorteio se repete. Em branco, cada simulação é nova.",
    )
