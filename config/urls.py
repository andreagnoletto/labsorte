"""Rotas do projeto."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("contas/", include("django.contrib.auth.urls")),
    path("carteira/", include("wallet.urls")),
    path("bicho/", include("bicho.urls")),
    path("cassino/", include("casino.urls")),
    path("aprenda/", include("learn.urls")),
]
