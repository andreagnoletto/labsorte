from django.urls import path

from . import views

app_name = "wallet"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("extrato/", views.statement, name="statement"),
    path("recarregar/", views.recharge, name="recharge"),
]
