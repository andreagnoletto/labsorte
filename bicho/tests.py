import random
from decimal import Decimal
from fractions import Fraction

from django.test import SimpleTestCase

from bicho import rules
from bicho.rules import Modality, Position


class RulesTests(SimpleTestCase):
    def test_groups(self):
        self.assertEqual(rules.group_for_dezena(1), 1)
        self.assertEqual(rules.group_for_dezena(4), 1)
        self.assertEqual(rules.group_for_dezena(5), 2)
        self.assertEqual(rules.group_for_dezena(99), 25)
        self.assertEqual(rules.group_for_dezena(0), 25)
        self.assertEqual(rules.animal_for_prize("1200").name, "Vaca")
        self.assertEqual(rules.animal_for_prize("1234").name, "Cobra")
        self.assertEqual(rules.animal_for_group(1).name, "Avestruz")
        self.assertEqual(rules.ANIMALS[24].dezenas, ["97", "98", "99", "00"])
        self.assertEqual(rules.ANIMALS[0].dezenas, ["01", "02", "03", "04"])
        self.assertEqual(len(rules.ANIMALS), 25)
        self.assertEqual(len({a.name for a in rules.ANIMALS}), 25)

    def test_normalize(self):
        self.assertEqual(rules.normalize_pick(Modality.GRUPO, " 7 "), "07")
        self.assertEqual(rules.normalize_pick(Modality.GRUPO, "25"), "25")
        self.assertEqual(rules.normalize_pick(Modality.DEZENA, "7"), "07")
        self.assertEqual(rules.normalize_pick(Modality.MILHAR, "0"), "0000")
        self.assertEqual(rules.normalize_pick(Modality.DEZENA, "00"), "00")
        self.assertEqual(rules.normalize_pick(Modality.CENTENA, "123"), "123")
        for mod, bad in [
            (Modality.GRUPO, "26"),
            (Modality.GRUPO, "0"),
            (Modality.GRUPO, ""),
            (Modality.DEZENA, "100"),
            (Modality.CENTENA, "abc"),
            (Modality.MILHAR, "12345"),
            (Modality.MILHAR, "-1"),
            (Modality.DEZENA, "²"),  # sobrescrito: isdigit() aceita, int() não
            (Modality.MILHAR, "١٢٣٤"),  # algarismos arábico-índicos
            (Modality.GRUPO, "٣"),
        ]:
            with self.assertRaises(ValueError, msg=f"{mod} {bad!r}"):
                rules.normalize_pick(mod, bad)

    def test_payout_cabeca(self):
        prizes = ["1234", "5678", "0000", "4321", "9999"]
        self.assertEqual(
            rules.compute_payout(Modality.MILHAR, Position.CABECA, "1234", Decimal("2"), prizes),
            Decimal("8000"),
        )
        self.assertEqual(
            rules.compute_payout(Modality.CENTENA, Position.CABECA, "234", Decimal("1"), prizes),
            Decimal("600"),
        )
        self.assertEqual(
            rules.compute_payout(Modality.DEZENA, Position.CABECA, "34", Decimal("1"), prizes),
            Decimal("60"),
        )
        # 34 -> grupo 9 (Cobra)
        self.assertEqual(
            rules.compute_payout(Modality.GRUPO, Position.CABECA, "09", Decimal("1"), prizes),
            Decimal("18"),
        )
        self.assertEqual(
            rules.compute_payout(Modality.GRUPO, Position.CABECA, "25", Decimal("1"), prizes),
            Decimal("0"),
        )

    def test_payout_cercado_pays_per_hit(self):
        prizes = ["1234", "5634", "0000", "4321", "9934"]
        # 3 acertos * 5 * 12
        self.assertEqual(
            rules.compute_payout(Modality.DEZENA, Position.CERCADO, "34", Decimal("5"), prizes),
            Decimal("180"),
        )
        # 0000 -> grupo 25, 1 acerto * 10 * 3.6
        self.assertEqual(
            rules.compute_payout(Modality.GRUPO, Position.CERCADO, "25", Decimal("10"), prizes),
            Decimal("36"),
        )
        self.assertEqual(
            rules.compute_payout(Modality.MILHAR, Position.CERCADO, "7777", Decimal("10"), prizes),
            Decimal("0"),
        )

    def test_house_edge(self):
        self.assertEqual(rules.house_edge(Modality.GRUPO), Fraction(7, 25))
        self.assertEqual(rules.house_edge(Modality.DEZENA), Fraction(2, 5))
        self.assertEqual(rules.house_edge(Modality.CENTENA), Fraction(2, 5))
        self.assertEqual(rules.house_edge(Modality.MILHAR), Fraction(3, 5))

    def test_odds_table(self):
        table = rules.odds_table()
        self.assertEqual([row["modality"] for row in table], list(Modality))
        grupo = table[0]
        self.assertEqual(grupo["multiplier"], Decimal("18"))
        self.assertEqual(grupo["fair_multiplier"], 25)
        self.assertEqual(grupo["probability"], Fraction(1, 25))
        self.assertAlmostEqual(grupo["house_edge_pct"], 28.0)

    def test_random_prizes(self):
        prizes = rules.random_prizes(random.Random(1))
        self.assertEqual(len(prizes), 5)
        self.assertTrue(all(len(p) == 4 and p.isdigit() for p in prizes))
        self.assertEqual(prizes, rules.random_prizes(random.Random(1)))
        self.assertEqual(len(rules.random_prizes()), 5)


from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from bicho import services
from bicho.forms import BetForm
from bicho.models import Bet, Draw
from wallet import services as wallet_services


class ServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("ana", password="x")
        self.wallet = wallet_services.get_wallet(self.user)

    def test_current_draw_is_created_on_demand_and_reused(self):
        first = Draw.current()
        self.assertEqual(first.number, 1)
        self.assertEqual(first.status, Draw.Status.OPEN)
        self.assertEqual(Draw.current().pk, first.pk)

    def test_place_bet_debits_and_attaches_to_open_draw(self):
        bet = services.place_bet(self.user, Modality.MILHAR, Position.CABECA, "1234", Decimal("10"))
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("990"))
        self.assertEqual(bet.draw, Draw.current())
        self.assertEqual(bet.status, Bet.Status.PENDING)
        self.assertEqual(bet.multiplier, Decimal("4000"))
        self.assertEqual(bet.pick_label, "1234")
        grupo = services.place_bet(self.user, Modality.GRUPO, Position.CERCADO, "09", Decimal("1"))
        self.assertEqual(grupo.pick_label, "09 Cobra")

    def test_place_bet_insufficient_funds(self):
        with self.assertRaises(wallet_services.InsufficientFunds):
            services.place_bet(self.user, Modality.GRUPO, Position.CABECA, "01", Decimal("5000"))
        self.assertEqual(Bet.objects.count(), 0)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("1000"))

    def test_run_draw_settles_and_opens_next(self):
        win = services.place_bet(self.user, Modality.DEZENA, Position.CABECA, "34", Decimal("1"))
        lose = services.place_bet(self.user, Modality.MILHAR, Position.CABECA, "0001", Decimal("1"))
        draw = services.run_draw(["1234", "0000", "0000", "0000", "0000"])
        win.refresh_from_db()
        lose.refresh_from_db()
        self.wallet.refresh_from_db()
        self.assertEqual(draw.status, Draw.Status.CLOSED)
        self.assertIsNotNone(draw.drawn_at)
        self.assertEqual(win.status, Bet.Status.WON)
        self.assertEqual(win.payout, Decimal("60"))
        self.assertEqual(lose.status, Bet.Status.LOST)
        self.assertEqual(lose.payout, Decimal("0"))
        self.assertEqual(self.wallet.balance, Decimal("1000") - 2 + 60)
        self.assertEqual(Draw.current().number, draw.number + 1)
        self.assertEqual([a.name for _, a in draw.prize_animals], ["Cobra", "Vaca", "Vaca", "Vaca", "Vaca"])
        payout_tx = self.wallet.transactions.filter(kind="PAYOUT").get()
        self.assertEqual(payout_tx.amount, Decimal("60"))
        self.assertEqual(payout_tx.game, "BICHO")

    def test_run_draw_without_bets(self):
        draw = services.run_draw()
        self.assertEqual(len(draw.prizes), 5)
        self.assertEqual(Draw.current().number, draw.number + 1)

    def test_sortear_command(self):
        call_command("sortear", verbosity=0)
        self.assertEqual(Draw.objects.filter(status=Draw.Status.CLOSED).count(), 1)
        self.assertEqual(Draw.objects.filter(status=Draw.Status.OPEN).count(), 1)


class BetFormTests(SimpleTestCase):
    def test_normalizes_pick(self):
        form = BetForm({"modality": "DEZENA", "position": "CABECA", "pick": "7", "stake": "10"})
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["pick"], "07")
        self.assertEqual(form.cleaned_data["stake"], Decimal("10"))

    def test_rejects_bad_pick_and_stake(self):
        base = {"modality": "GRUPO", "position": "CABECA", "pick": "1", "stake": "10"}
        self.assertFalse(BetForm({**base, "pick": "30"}).is_valid())
        self.assertFalse(BetForm({**base, "stake": "501"}).is_valid())
        self.assertFalse(BetForm({**base, "stake": "0"}).is_valid())
        self.assertFalse(BetForm({**base, "stake": "0.5"}).is_valid())
        self.assertFalse(BetForm({**base, "modality": "TERNO"}).is_valid())
        self.assertTrue(BetForm(base).is_valid())


from django.urls import reverse


class ViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("ana", password="x")
        self.wallet = wallet_services.get_wallet(self.user)
        self.valid = {"modality": "GRUPO", "position": "CABECA", "pick": "9", "stake": "10"}

    def test_index_anonymous(self):
        r = self.client.get(reverse("bicho:index"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Avestruz")
        self.assertContains(r, "Extração nº 1")

    def test_post_requires_login(self):
        r = self.client.post(reverse("bicho:index"), self.valid)
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("login"), r["Location"])
        self.assertEqual(Bet.objects.count(), 0)

    def test_place_bet_via_post(self):
        self.client.force_login(self.user)
        r = self.client.post(reverse("bicho:index"), self.valid)
        self.assertRedirects(r, reverse("bicho:index"))
        bet = Bet.objects.get()
        self.assertEqual(bet.pick, "09")
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("990"))
        r = self.client.get(reverse("bicho:index"))
        self.assertContains(r, "Cobra")
        self.assertContains(r, "Aguardando sorteio")

    def test_insufficient_funds_shows_error_without_bet(self):
        self.client.force_login(self.user)
        wallet_services.debit(self.wallet, Decimal("995"), "DICE", "zera")
        r = self.client.post(reverse("bicho:index"), self.valid)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Saldo insuficiente")
        self.assertEqual(Bet.objects.count(), 0)

    def test_invalid_pick_rerenders_with_error(self):
        self.client.force_login(self.user)
        r = self.client.post(reverse("bicho:index"), {**self.valid, "pick": "30"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "O grupo vai de 01")
        self.assertEqual(Bet.objects.count(), 0)

    def test_draw_view_settles(self):
        self.client.force_login(self.user)
        self.client.post(reverse("bicho:index"), self.valid)
        r = self.client.post(reverse("bicho:draw"))
        self.assertRedirects(r, f"{reverse('bicho:index')}?sorteio=1")
        self.assertEqual(Draw.objects.filter(status=Draw.Status.CLOSED).count(), 1)
        self.assertEqual(Bet.objects.get().status in {Bet.Status.WON, Bet.Status.LOST}, True)
        r = self.client.get(reverse("bicho:index"))
        self.assertContains(r, "Deu no poste")
        self.assertNotContains(r, "data-animar-sorteio")
        r = self.client.get(f"{reverse('bicho:index')}?sorteio=1")
        self.assertContains(r, "data-animar-sorteio")
        head = Draw.objects.get(number=1).prizes[0]
        self.assertContains(r, f'<span class="digito" data-final="{head[0]}">{head[0]}</span>')
        r = self.client.get(f"{reverse('bicho:index')}?sorteio=99")
        self.assertNotContains(r, "data-animar-sorteio")

    def test_draw_view_rejects_get_and_anonymous(self):
        self.assertEqual(self.client.post(reverse("bicho:draw")).status_code, 302)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("bicho:draw")).status_code, 405)

    def test_history(self):
        services.run_draw(["1234", "5678", "0000", "4321", "9999"])
        r = self.client.get(reverse("bicho:history"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Extração nº 1")
        self.assertContains(r, "Cobra")
