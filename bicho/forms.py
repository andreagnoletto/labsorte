from decimal import Decimal

from django import forms

from wallet.services import MAX_STAKE, MIN_STAKE

from .rules import Modality, Position, normalize_pick


class BetForm(forms.Form):
    modality = forms.ChoiceField(
        label="Modalidade", choices=Modality.choices, initial=Modality.GRUPO, widget=forms.RadioSelect
    )
    position = forms.ChoiceField(
        label="Posição", choices=Position.choices, initial=Position.CABECA, widget=forms.RadioSelect
    )
    pick = forms.CharField(
        label="Palpite",
        max_length=4,
        help_text="Grupo de 01 a 25, ou os últimos dígitos do prêmio (dezena, centena ou milhar).",
    )
    stake = forms.IntegerField(
        label="Valor da aposta (F$)",
        min_value=int(MIN_STAKE),
        max_value=int(MAX_STAKE),
        initial=10,
        help_text=f"Fichas inteiras, de {MIN_STAKE:.0f} a {MAX_STAKE:.0f}.",
    )

    def clean_stake(self):
        return Decimal(self.cleaned_data["stake"])

    def clean(self):
        data = super().clean()
        modality = data.get("modality")
        pick = data.get("pick")
        if modality and pick is not None:
            try:
                data["pick"] = normalize_pick(modality, pick)
            except ValueError as exc:
                self.add_error("pick", str(exc))
        return data
