from decimal import Decimal

from django import forms

from wallet.services import MAX_STAKE, MIN_STAKE

from .roulette import BetType, validate_selection


def _stake_field():
    return forms.IntegerField(
        label="Valor da aposta (F$)",
        min_value=int(MIN_STAKE),
        max_value=int(MAX_STAKE),
        initial=10,
        help_text=f"Fichas inteiras, de {MIN_STAKE:.0f} a {MAX_STAKE:.0f}.",
    )


class StakeForm(forms.Form):
    stake = _stake_field()

    def clean_stake(self):
        return Decimal(self.cleaned_data["stake"])


class RouletteForm(StakeForm):
    bet_type = forms.ChoiceField(
        label="Tipo de aposta", choices=BetType.choices, initial=BetType.RED, widget=forms.RadioSelect
    )
    selection = forms.CharField(
        label="Número (0 a 36), dúzia ou coluna (1 a 3)",
        required=False,
        max_length=2,
        help_text="Só é usado nas apostas de número, dúzia e coluna.",
    )
    field_order = ["bet_type", "selection", "stake"]

    def clean(self):
        data = super().clean()
        bet_type = data.get("bet_type")
        if bet_type:
            try:
                data["selection"] = validate_selection(bet_type, data.get("selection", ""))
            except ValueError as exc:
                self.add_error("selection", str(exc))
        return data


class SlotsForm(StakeForm):
    pass


class DiceForm(StakeForm):
    pick = forms.TypedChoiceField(
        label="Face do dado",
        choices=[(i, str(i)) for i in range(1, 7)],
        coerce=int,
        initial=6,
        widget=forms.RadioSelect,
    )
    field_order = ["pick", "stake"]
