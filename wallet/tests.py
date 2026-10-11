from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from wallet import services
from wallet.models import Transaction


class DatabaseLockingTests(SimpleTestCase):
    def test_sqlite_transactions_start_immediate(self):
        """select_for_update() é ignorado no SQLite; o modo IMMEDIATE serializa as escritas."""
        from django.db import connection

        if connection.vendor == "sqlite":
            self.assertEqual(connection.settings_dict["OPTIONS"].get("transaction_mode"), "IMMEDIATE")


class WalletServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("ana", password="x")

    def test_get_wallet_creates_with_initial_bonus(self):
        wallet = services.get_wallet(self.user)
        self.assertEqual(wallet.balance, services.INITIAL_BONUS)
        self.assertEqual(wallet.transactions.count(), 1)
        self.assertEqual(wallet.recharges, 0)
        services.get_wallet(self.user)  # segunda chamada não duplica bônus
        self.assertEqual(wallet.transactions.count(), 1)

    def test_debit_and_credit_update_balance_and_ledger(self):
        wallet = services.get_wallet(self.user)
        tx = services.debit(wallet, Decimal("10"), Transaction.Game.DICE, "aposta")
        self.assertEqual(tx.amount, Decimal("-10"))
        self.assertEqual(tx.balance_after, Decimal("990"))
        services.credit(
            wallet, Decimal("50"), Transaction.Kind.PAYOUT, Transaction.Game.DICE, "prêmio"
        )
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, Decimal("1040"))

    def test_debit_insufficient_funds_changes_nothing(self):
        wallet = services.get_wallet(self.user)
        with self.assertRaises(services.InsufficientFunds):
            services.debit(wallet, Decimal("5000"), Transaction.Game.DICE, "x")
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, services.INITIAL_BONUS)
        self.assertEqual(wallet.transactions.count(), 1)

    def test_debit_rejects_non_positive_amount(self):
        wallet = services.get_wallet(self.user)
        with self.assertRaises(ValueError):
            services.debit(wallet, Decimal("0"), Transaction.Game.DICE, "x")

    def test_recharge_counts(self):
        wallet = services.get_wallet(self.user)
        services.recharge(wallet)
        wallet.refresh_from_db()
        self.assertEqual(wallet.recharges, 1)
        self.assertEqual(wallet.balance, services.INITIAL_BONUS + services.RECHARGE_AMOUNT)

    def test_summary(self):
        wallet = services.get_wallet(self.user)
        services.debit(wallet, Decimal("10"), Transaction.Game.DICE, "a")
        services.debit(wallet, Decimal("20"), Transaction.Game.SLOTS, "b")
        services.credit(
            wallet, Decimal("15"), Transaction.Kind.PAYOUT, Transaction.Game.DICE, "p"
        )
        s = services.summary(wallet)
        self.assertEqual(s["staked"], Decimal("30"))
        self.assertEqual(s["won"], Decimal("15"))
        self.assertEqual(s["net"], Decimal("-15"))
        self.assertEqual(s["bets"], 2)
        self.assertEqual(s["return_rate"], Decimal("0.5"))
        self.assertEqual(s["per_game"]["DICE"]["net"], Decimal("5"))
        self.assertEqual(s["per_game"]["SLOTS"]["staked"], Decimal("20"))

    def test_summary_without_bets(self):
        wallet = services.get_wallet(self.user)
        s = services.summary(wallet)
        self.assertEqual(s["staked"], Decimal("0"))
        self.assertEqual(s["bets"], 0)
        self.assertIsNone(s["return_rate"])
        self.assertEqual(s["per_game"], {})


from django.test import SimpleTestCase
from django.urls import reverse

from wallet import analysis, charts


class ChartTests(SimpleTestCase):
    def test_polyline_three_points(self):
        data = charts.polyline([Decimal("1000"), Decimal("500"), Decimal("1500")], width=600, height=200)
        self.assertEqual(data["points"], "0,100 300,200 600,0")
        self.assertEqual(data["min"], Decimal("500"))
        self.assertEqual(data["max"], Decimal("1500"))
        self.assertIsNone(data["baseline_y"])

    def test_polyline_baseline(self):
        data = charts.polyline([Decimal("500"), Decimal("1500")], width=600, height=200, baseline=Decimal("1000"))
        self.assertEqual(data["baseline_y"], "100")
        # baseline fora do intervalo entra na escala
        data = charts.polyline([Decimal("1200"), Decimal("1400")], width=600, height=200, baseline=Decimal("1000"))
        self.assertEqual(data["min"], Decimal("1000"))
        self.assertEqual(data["baseline_y"], "200")

    def test_polyline_extra_series_share_scale(self):
        data = charts.polyline([Decimal("0"), Decimal("10")], width=100, height=100, extra=[[Decimal("0"), Decimal("-10")]])
        self.assertEqual(data["min"], Decimal("-10"))
        self.assertEqual(data["max"], Decimal("10"))
        self.assertEqual(data["points"], "0,50 100,0")
        self.assertEqual(data["extra_points"], ["0,50 100,100"])
        self.assertEqual(charts.polyline([Decimal("1")])["extra_points"], [])

    def test_polyline_empty_single_and_flat(self):
        self.assertEqual(charts.polyline([])["points"], "")
        single = charts.polyline([Decimal("5")], width=600, height=200)
        self.assertEqual(single["points"], "0,100")
        flat = charts.polyline([Decimal("5"), Decimal("5")], width=600, height=200)
        self.assertEqual(flat["points"], "0,100 600,100")


class AnalysisTests(TestCase):
    def test_expected_return_counts_only_settled_bets(self):
        from bicho import services as bicho_services
        from casino import services as casino_services

        user = get_user_model().objects.create_user("ana", password="x")
        services.get_wallet(user)
        bicho_services.place_bet(user, "GRUPO", "CABECA", "01", Decimal("10"))
        import random

        from casino import dice

        losing_pick = 1 if dice.roll(random.Random(1)) != 1 else 2
        casino_services.play_dice(user, pick=losing_pick, stake=Decimal("12"), rng=random.Random(1))
        before = analysis.expected_return(user)
        self.assertEqual(before["settled_staked"], Decimal("12"))
        self.assertEqual(before["expected_return"], Decimal("10"))
        bicho_services.run_draw(["9999", "9999", "9999", "9999", "9999"])
        after = analysis.expected_return(user)
        self.assertEqual(after["settled_staked"], Decimal("22"))
        self.assertEqual(after["expected_return"], Decimal("17.2"))
        self.assertEqual(after["actual_return"], Decimal("0"))


class WalletViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("ana", password="x")
        self.wallet = services.get_wallet(self.user)

    def test_requires_login(self):
        for name in ["wallet:dashboard", "wallet:statement"]:
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 302, name)
            self.assertIn(reverse("login"), r["Location"])
        r = self.client.post(reverse("wallet:recharge"))
        self.assertEqual(r.status_code, 302)
        self.assertEqual(self.wallet.recharges, 0)

    def test_dashboard_renders_summary_and_chart(self):
        self.client.force_login(self.user)
        services.debit(self.wallet, Decimal("100"), Transaction.Game.DICE, "aposta")
        services.credit(self.wallet, Decimal("40"), Transaction.Kind.PAYOUT, Transaction.Game.DICE, "prêmio")
        r = self.client.get(reverse("wallet:dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Apostado")
        self.assertContains(r, "<polyline")
        self.assertContains(r, "Dado")
        self.assertContains(r, "940,00")
        # atributos SVG não podem ser localizados ("0,0" quebra o gráfico)
        self.assertContains(r, 'y1="0"')
        self.assertNotContains(r, 'y1="0,0"')

    def test_dashboard_without_bets(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse("wallet:dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Você ainda não apostou")

    def test_statement_lists_transactions(self):
        self.client.force_login(self.user)
        r = self.client.get(reverse("wallet:statement"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Fichas iniciais")

    def test_recharge(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("wallet:recharge")).status_code, 405)
        r = self.client.post(reverse("wallet:recharge"))
        self.assertRedirects(r, reverse("wallet:dashboard"))
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.recharges, 1)
        self.assertEqual(self.wallet.balance, Decimal("2000"))
