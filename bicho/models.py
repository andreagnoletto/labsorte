from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Max

from .rules import Modality, Position, animal_for_group, animal_for_prize


class Draw(models.Model):
    """Uma extração: recebe apostas enquanto aberta e sorteia cinco prêmios."""

    class Status(models.TextChoices):
        OPEN = "OPEN", "Aberta"
        CLOSED = "CLOSED", "Encerrada"

    number = models.PositiveIntegerField("número", unique=True)
    status = models.CharField(max_length=6, choices=Status.choices, default=Status.OPEN)
    prizes = models.JSONField("prêmios", default=list, blank=True)
    opened_at = models.DateTimeField("aberta em", auto_now_add=True)
    drawn_at = models.DateTimeField("sorteada em", null=True, blank=True)

    class Meta:
        ordering = ["-number"]
        verbose_name = "extração"
        verbose_name_plural = "extrações"

    def __str__(self):
        return f"Extração nº {self.number} ({self.get_status_display()})"

    @classmethod
    def current(cls):
        """A extração aberta, criada sob demanda com o próximo número."""
        draw = cls.objects.filter(status=cls.Status.OPEN).order_by("number").first()
        if draw is not None:
            return draw
        last = cls.objects.aggregate(last=Max("number"))["last"] or 0
        return cls.objects.create(number=last + 1)

    @property
    def prize_animals(self):
        """Lista de (prêmio, bicho) na ordem do 1º ao 5º."""
        return [(prize, animal_for_prize(prize)) for prize in self.prizes]


class Bet(models.Model):
    """Aposta de um usuário em uma extração."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Aguardando sorteio"
        WON = "WON", "Premiada"
        LOST = "LOST", "Não premiada"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bicho_bets")
    draw = models.ForeignKey(Draw, on_delete=models.PROTECT, related_name="bets")
    modality = models.CharField("modalidade", max_length=8, choices=Modality.choices)
    position = models.CharField("posição", max_length=8, choices=Position.choices)
    pick = models.CharField("palpite", max_length=4)
    stake = models.DecimalField("valor", max_digits=10, decimal_places=2)
    multiplier = models.DecimalField("multiplicador", max_digits=8, decimal_places=2)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.PENDING)
    payout = models.DecimalField("prêmio", max_digits=12, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "aposta"
        verbose_name_plural = "apostas"

    def __str__(self):
        return f"{self.get_modality_display()} {self.pick_label} F$ {self.stake} ({self.user})"

    @property
    def pick_label(self) -> str:
        """Palpite legível: grupos ganham o nome do bicho."""
        if self.modality == Modality.GRUPO:
            return f"{self.pick} {animal_for_group(int(self.pick)).name}"
        return self.pick

    @property
    def position_short(self) -> str:
        return "cabeça" if self.position == Position.CABECA else "1º ao 5º"
