from decimal import Decimal

from django.conf import settings
from django.db import models

from wallet.models import Transaction


class CasinoRound(models.Model):
    """Uma rodada de roleta, caça-níquel ou dado, já liquidada."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="casino_rounds")
    game = models.CharField("jogo", max_length=10, choices=Transaction.Game.choices)
    stake = models.DecimalField("valor", max_digits=10, decimal_places=2)
    payout = models.DecimalField("prêmio", max_digits=12, decimal_places=2, default=Decimal("0.00"))
    details = models.JSONField("detalhes", default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "rodada"
        verbose_name_plural = "rodadas"

    def __str__(self):
        return f"{self.get_game_display()} F$ {self.stake} → F$ {self.payout} ({self.user})"

    @property
    def won(self) -> bool:
        return self.payout > 0

    @property
    def net(self) -> Decimal:
        return self.payout - self.stake
