from django.contrib import admin

from .models import Transaction, Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "recharges", "created_at")
    search_fields = ("user__username",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "wallet", "kind", "game", "amount", "balance_after", "description")
    list_filter = ("kind", "game")
    search_fields = ("wallet__user__username", "description")
    date_hierarchy = "created_at"
