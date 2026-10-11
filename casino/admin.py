from django.contrib import admin

from .models import CasinoRound


@admin.register(CasinoRound)
class CasinoRoundAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "game", "stake", "payout", "details")
    list_filter = ("game",)
    search_fields = ("user__username",)
    date_hierarchy = "created_at"
