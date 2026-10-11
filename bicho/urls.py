from django.urls import path

from . import views

app_name = "bicho"

urlpatterns = [
    path("", views.index, name="index"),
    path("sortear/", views.draw, name="draw"),
    path("extracoes/", views.history, name="history"),
]
