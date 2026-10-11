from django.urls import path

from . import views

app_name = "casino"

urlpatterns = [
    path("roleta/", views.roulette_view, name="roulette"),
    path("caca-niquel/", views.slots_view, name="slots"),
    path("dado/", views.dice_view, name="dice"),
]
