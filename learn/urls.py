from django.urls import path

from . import views

app_name = "learn"

urlpatterns = [
    path("", views.index, name="index"),
    path("jogo-do-bicho/", views.bicho, name="bicho"),
    path("probabilidade/", views.probability, name="probability"),
    path("falacias/", views.fallacies, name="fallacies"),
    path("lei-e-jogo-responsavel/", views.legal, name="legal"),
    path("simulador/", views.simulator, name="simulator"),
]
