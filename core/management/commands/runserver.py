"""runserver do projeto: mesma implementação do Django, porta padrão 8777.

Para ter precedência sobre o comando do ``django.contrib.staticfiles``, o app
``core`` precisa vir antes dele em ``INSTALLED_APPS``.
"""

from django.contrib.staticfiles.management.commands.runserver import Command as StaticfilesRunserver


class Command(StaticfilesRunserver):
    default_port = "8777"
