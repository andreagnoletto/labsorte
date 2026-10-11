"""Processadores de contexto do app core."""

from wallet.services import get_wallet


def wallet(request):
    """Disponibiliza ``wallet`` em todos os templates para usuários logados."""
    if request.user.is_authenticated:
        return {"wallet": get_wallet(request.user)}
    return {}
