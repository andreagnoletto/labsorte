from decimal import Decimal

from django.conf import settings
from django.db import models


class Wallet(models.Model):
    """Carteira de fichas fictícias de um usuário."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet"
    )
    balance = models.DecimalField("saldo", max_digits=12, decimal_places=2, default=Decimal("0.00"))
    recharges = models.PositiveIntegerField("recargas", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "carteira"
        verbose_name_plural = "carteiras"

    def __str__(self):
        return f"Carteira de {self.user} (F$ {self.balance})"


class Transaction(models.Model):
    """Livro-razão: toda movimentação de fichas gera uma linha."""

    class Kind(models.TextChoices):
        BONUS = "BONUS", "Bônus / recarga"
        BET = "BET", "Aposta"
        PAYOUT = "PAYOUT", "Prêmio"

    class Game(models.TextChoices):
        BICHO = "BICHO", "Jogo do bicho"
        ROULETTE = "ROULETTE", "Roleta"
        SLOTS = "SLOTS", "Caça-níquel"
        DICE = "DICE", "Dado"

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    kind = models.CharField("tipo", max_length=10, choices=Kind.choices)
    game = models.CharField("jogo", max_length=10, choices=Game.choices, blank=True, default="")
    amount = models.DecimalField("valor", max_digits=12, decimal_places=2)
    balance_after = models.DecimalField("saldo após", max_digits=12, decimal_places=2)
    description = models.CharField("descrição", max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "transação"
        verbose_name_plural = "transações"

    def __str__(self):
        return f"{self.get_kind_display()} {self.amount} ({self.wallet.user})"
