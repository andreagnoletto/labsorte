from django.contrib import admin

from .models import Bet, Draw


@admin.register(Draw)
class DrawAdmin(admin.ModelAdmin):
    list_display = ("number", "status", "prizes", "opened_at", "drawn_at")
    list_filter = ("status",)
    readonly_fields = ("opened_at",)


@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = ("created_at", "user", "draw", "modality", "position", "pick", "stake", "status", "payout")
    list_filter = ("status", "modality", "position")
    search_fields = ("user__username", "pick")
