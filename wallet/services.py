"""Serviços da carteira: única porta de entrada para mover fichas.

Todas as funções que alteram saldo rodam em ``transaction.atomic()`` e
recarregam a carteira dentro da transação, de modo que saldo e livro-razão
sejam gravados juntos. Em bancos com ``SELECT ... FOR UPDATE`` (PostgreSQL,
MySQL) a linha é bloqueada; no SQLite esse bloqueio não existe e a exclusão
vem do modo de transação IMMEDIATE configurado em ``settings.DATABASES``.
"""

from decimal import Decimal

from django.db import transaction
from django.db.models import Count, F, Q, Sum

from .models import Transaction, Wallet

INITIAL_BONUS = Decimal("1000.00")
RECHARGE_AMOUNT = Decimal("1000.00")
MIN_STAKE = Decimal("1.00")
MAX_STAKE = Decimal("500.00")


class InsufficientFunds(Exception):
    """Saldo insuficiente para cobrir a aposta."""


def _apply(wallet, delta, kind, game, description):
    locked = Wallet.objects.select_for_update().get(pk=wallet.pk)
    new_balance = locked.balance + delta
    if new_balance < 0:
        raise InsufficientFunds(
            f"Saldo insuficiente: você tem F$ {locked.balance} e precisa de F$ {-delta}."
        )
    locked.balance = new_balance
    locked.save(update_fields=["balance"])
    wallet.balance = new_balance
    return Transaction.objects.create(
        wallet=locked,
        kind=kind,
        game=game,
        amount=delta,
        balance_after=new_balance,
        description=description,
    )


@transaction.atomic
def credit(wallet, amount, kind, game, description):
    """Credita ``amount`` (positivo) na carteira e registra no livro-razão."""
    amount = Decimal(amount)
    if amount <= 0:
        raise ValueError("O valor a creditar deve ser positivo.")
    return _apply(wallet, amount, kind, game, description)


@transaction.atomic
def debit(wallet, amount, game, description):
    """Debita uma aposta. Levanta ``InsufficientFunds`` sem alterar nada."""
    amount = Decimal(amount)
    if amount <= 0:
        raise ValueError("O valor da aposta deve ser positivo.")
    return _apply(wallet, -amount, Transaction.Kind.BET, game, description)


@transaction.atomic
def get_wallet(user):
    """Retorna a carteira do usuário, criando-a com o bônus inicial se preciso."""
    wallet, created = Wallet.objects.get_or_create(user=user)
    if created:
        credit(wallet, INITIAL_BONUS, Transaction.Kind.BONUS, "", "Fichas iniciais do simulador")
    return wallet


@transaction.atomic
def recharge(wallet):
    """Recarga educativa: credita fichas e conta quantas vezes foi preciso."""
    tx = credit(wallet, RECHARGE_AMOUNT, Transaction.Kind.BONUS, "", "Recarga educativa")
    Wallet.objects.filter(pk=wallet.pk).update(recharges=F("recharges") + 1)
    wallet.recharges += 1
    return tx


def _totals(queryset):
    agg = queryset.aggregate(
        staked=Sum("amount", filter=Q(kind=Transaction.Kind.BET)),
        won=Sum("amount", filter=Q(kind=Transaction.Kind.PAYOUT)),
        bets=Count("id", filter=Q(kind=Transaction.Kind.BET)),
    )
    staked = -(agg["staked"] or Decimal("0"))
    won = agg["won"] or Decimal("0")
    return {
        "staked": staked,
        "won": won,
        "net": won - staked,
        "bets": agg["bets"],
        "return_rate": (won / staked) if staked else None,
    }


def summary(wallet):
    """Totais do usuário (apostado, ganho, líquido, retorno) no geral e por jogo."""
    queryset = wallet.transactions.all()
    result = _totals(queryset)
    per_game = {}
    games = (
        queryset.exclude(game="").values_list("game", flat=True).distinct().order_by("game")
    )
    for game in games:
        per_game[game] = _totals(queryset.filter(game=game))
        per_game[game]["label"] = Transaction.Game(game).label
    result["per_game"] = per_game
    return result
