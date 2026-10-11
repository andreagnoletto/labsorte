import random
from decimal import Decimal
from fractions import Fraction

from django.test import SimpleTestCase

from casino import dice, roulette, slots


class RouletteTests(SimpleTestCase):
    def test_colors(self):
        self.assertEqual(roulette.color(0), "verde")
        self.assertEqual(roulette.color(1), "vermelho")
        self.assertEqual(roulette.color(2), "preto")
        self.assertEqual(len(roulette.RED), 18)
        self.assertEqual(sum(1 for n in range(1, 37) if roulette.color(n) == "preto"), 18)

    def test_wins(self):
        B = roulette.BetType
        self.assertTrue(roulette.wins(B.NUMBER, "17", 17))
        self.assertFalse(roulette.wins(B.NUMBER, "17", 18))
        self.assertTrue(roulette.wins(B.NUMBER, "0", 0))
        self.assertTrue(roulette.wins(B.RED, "", 1))
        self.assertFalse(roulette.wins(B.RED, "", 0))
        self.assertFalse(roulette.wins(B.BLACK, "", 0))
        self.assertTrue(roulette.wins(B.BLACK, "", 2))
        self.assertTrue(roulette.wins(B.EVEN, "", 2))
        self.assertFalse(roulette.wins(B.EVEN, "", 0))
        self.assertTrue(roulette.wins(B.ODD, "", 3))
        self.assertTrue(roulette.wins(B.LOW, "", 18))
        self.assertFalse(roulette.wins(B.LOW, "", 19))
        self.assertTrue(roulette.wins(B.HIGH, "", 19))
        self.assertFalse(roulette.wins(B.HIGH, "", 0))
        self.assertTrue(roulette.wins(B.DOZEN, "2", 13))
        self.assertFalse(roulette.wins(B.DOZEN, "2", 25))
        self.assertTrue(roulette.wins(B.DOZEN, "3", 36))
        self.assertTrue(roulette.wins(B.COLUMN, "1", 34))
        self.assertTrue(roulette.wins(B.COLUMN, "2", 35))
        self.assertTrue(roulette.wins(B.COLUMN, "3", 36))
        self.assertFalse(roulette.wins(B.COLUMN, "3", 0))

    def test_payout_and_edge(self):
        B = roulette.BetType
        self.assertEqual(roulette.compute_payout(B.NUMBER, "5", Decimal("1"), 5), Decimal("36"))
        self.assertEqual(roulette.compute_payout(B.NUMBER, "5", Decimal("1"), 6), Decimal("0"))
        self.assertEqual(roulette.compute_payout(B.RED, "", Decimal("2"), 3), Decimal("4"))
        self.assertEqual(roulette.compute_payout(B.DOZEN, "1", Decimal("2"), 3), Decimal("6"))
        for bet_type in B:
            self.assertEqual(roulette.house_edge(bet_type), Fraction(1, 37), bet_type)
        self.assertEqual(roulette.PROBABILITY[B.NUMBER], Fraction(1, 37))
        self.assertEqual(roulette.PROBABILITY[B.RED], Fraction(18, 37))
        self.assertEqual(roulette.PROBABILITY[B.DOZEN], Fraction(12, 37))

    def test_validate_selection(self):
        B = roulette.BetType
        self.assertEqual(roulette.validate_selection(B.NUMBER, " 7"), "7")
        self.assertEqual(roulette.validate_selection(B.NUMBER, "0"), "0")
        with self.assertRaises(ValueError):
            roulette.validate_selection(B.NUMBER, "37")
        with self.assertRaises(ValueError):
            roulette.validate_selection(B.NUMBER, "")
        with self.assertRaises(ValueError):
            roulette.validate_selection(B.DOZEN, "4")
        self.assertEqual(roulette.validate_selection(B.COLUMN, "3"), "3")
        for unicode_digit in ["²", "٣٦"]:
            with self.assertRaises(ValueError):
                roulette.validate_selection(B.NUMBER, unicode_digit)
        self.assertEqual(roulette.validate_selection(B.RED, "qualquer"), "")

    def test_describe(self):
        B = roulette.BetType
        self.assertEqual(roulette.describe(B.NUMBER, "7"), "Número 7")
        self.assertEqual(roulette.describe(B.DOZEN, "2"), "2ª dúzia (13 a 24)")
        self.assertEqual(roulette.describe(B.RED, ""), "Vermelho")

    def test_wheel_order_is_the_real_european_wheel(self):
        wheel = roulette.WHEEL_ORDER
        self.assertEqual(len(wheel), 37)
        self.assertEqual(set(wheel), set(range(37)))
        self.assertEqual(wheel[0], 0)
        self.assertEqual(wheel[1], 32)
        self.assertEqual(wheel[-1], 26)
        # na roda real, vermelho e preto se alternam (o zero é o único verde)
        for i in range(1, 37):
            nxt = wheel[(i + 1) % 37]
            if nxt != 0:
                self.assertNotEqual(roulette.color(wheel[i]), roulette.color(nxt), (wheel[i], nxt))

    def test_spin_range_and_determinism(self):
        self.assertTrue(all(0 <= roulette.spin(random.Random(i)) <= 36 for i in range(50)))
        self.assertEqual(roulette.spin(random.Random(3)), roulette.spin(random.Random(3)))
        self.assertTrue(0 <= roulette.spin() <= 36)


class SlotsTests(SimpleTestCase):
    def test_reel_composition(self):
        self.assertEqual(len(slots.REEL), 20)
        self.assertEqual(slots.REEL.count("cereja"), 6)
        self.assertEqual(slots.REEL.count("diamante"), 1)
        self.assertEqual(set(slots.REEL), set(slots.SYMBOLS))

    def test_multipliers(self):
        self.assertEqual(slots.multiplier(("diamante",) * 3), 1000)
        self.assertEqual(slots.multiplier(("cereja", "cereja", "limao")), 2)
        self.assertEqual(slots.multiplier(("cereja", "limao", "cereja")), 2)
        self.assertEqual(slots.multiplier(("limao", "cereja", "cereja")), 2)
        self.assertEqual(slots.multiplier(("cereja",) * 3), 5)
        self.assertEqual(slots.multiplier(("cereja", "limao", "sete")), 0)
        self.assertEqual(slots.multiplier(("sino", "sino", "sino")), 25)

    def test_rtp(self):
        self.assertEqual(slots.rtp(), Fraction(7474, 8000))
        self.assertEqual(slots.house_edge(), Fraction(526, 8000))

    def test_payout(self):
        self.assertEqual(slots.compute_payout(Decimal("3"), ("sete",) * 3), Decimal("450"))
        self.assertEqual(slots.compute_payout(Decimal("3"), ("sete", "sino", "cereja")), Decimal("0"))

    def test_spin(self):
        reels = slots.spin(random.Random(5))
        self.assertEqual(len(reels), 3)
        self.assertTrue(all(symbol in slots.SYMBOLS for symbol in reels))
        self.assertEqual(reels, slots.spin(random.Random(5)))

    def test_paytable_rows(self):
        rows = slots.paytable_rows()
        self.assertEqual(rows[0]["symbols"], "💎💎💎")
        self.assertEqual(rows[0]["multiplier"], 1000)
        self.assertEqual(rows[0]["probability"], Fraction(1, 8000))
        self.assertEqual(rows[-1]["multiplier"], 2)
        self.assertEqual(rows[-1]["probability"], Fraction(1512, 8000))


class DiceTests(SimpleTestCase):
    def test_payout(self):
        self.assertEqual(dice.compute_payout(3, Decimal("2"), 3), Decimal("10"))
        self.assertEqual(dice.compute_payout(3, Decimal("2"), 4), Decimal("0"))

    def test_edge(self):
        self.assertEqual(dice.house_edge(), Fraction(1, 6))
        self.assertEqual(dice.PROBABILITY, Fraction(1, 6))

    def test_roll(self):
        self.assertTrue(all(1 <= dice.roll(random.Random(i)) <= 6 for i in range(50)))
        self.assertTrue(1 <= dice.roll() <= 6)


from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from casino import services
from casino.models import CasinoRound
from wallet import services as wallet_services


class ServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("ana", password="x")
        self.wallet = wallet_services.get_wallet(self.user)

    def test_play_dice_win(self):
        result = dice.roll(random.Random(1))
        rnd = services.play_dice(self.user, pick=result, stake=Decimal("10"), rng=random.Random(1))
        self.assertEqual(rnd.game, "DICE")
        self.assertEqual(rnd.payout, Decimal("50"))
        self.assertEqual(rnd.details, {"pick": result, "result": result})
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("1040"))
        self.assertEqual(self.wallet.transactions.filter(kind="PAYOUT", game="DICE").count(), 1)

    def test_play_dice_loss(self):
        result = dice.roll(random.Random(1))
        pick = 1 if result != 1 else 2
        rnd = services.play_dice(self.user, pick=pick, stake=Decimal("10"), rng=random.Random(1))
        self.assertEqual(rnd.payout, Decimal("0"))
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("990"))
        self.assertEqual(self.wallet.transactions.filter(kind="PAYOUT").count(), 0)

    def test_play_roulette(self):
        number = roulette.spin(random.Random(2))
        rnd = services.play_roulette(self.user, "NUMBER", str(number), Decimal("1"), rng=random.Random(2))
        self.assertEqual(rnd.payout, Decimal("36"))
        self.assertEqual(rnd.details["number"], number)
        self.assertEqual(rnd.details["color"], roulette.color(number))
        self.assertEqual(rnd.details["label"], f"Número {number}")
        self.assertEqual(rnd.details["bet_type"], "NUMBER")

    def test_play_slots(self):
        reels = slots.spin(random.Random(3))
        rnd = services.play_slots(self.user, Decimal("2"), rng=random.Random(3))
        self.assertEqual(rnd.details["reels"], list(reels))
        self.assertEqual(rnd.details["multiplier"], slots.multiplier(reels))
        self.assertEqual(rnd.payout, slots.compute_payout(Decimal("2"), reels))

    def test_insufficient_funds_creates_nothing(self):
        wallet_services.debit(self.wallet, Decimal("995"), "DICE", "zera")
        with self.assertRaises(wallet_services.InsufficientFunds):
            services.play_dice(self.user, pick=1, stake=Decimal("10"))
        self.assertEqual(CasinoRound.objects.count(), 0)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("5"))


class ViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("ana", password="x")
        self.wallet = wallet_services.get_wallet(self.user)

    def test_pages_render_anonymous(self):
        for name, needle in [("casino:roulette", "2,7"), ("casino:slots", "93,4"), ("casino:dice", "16,7")]:
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 200, name)
            self.assertContains(r, needle)

    def test_post_requires_login(self):
        r = self.client.post(reverse("casino:dice"), {"pick": "3", "stake": "10"})
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("login"), r["Location"])
        self.assertEqual(CasinoRound.objects.count(), 0)

    def test_dice_post_redirects_to_result(self):
        self.client.force_login(self.user)
        r = self.client.post(reverse("casino:dice"), {"pick": "3", "stake": "10"})
        rnd = CasinoRound.objects.get()
        self.assertRedirects(r, f"{reverse('casino:dice')}?r={rnd.pk}")
        r = self.client.get(r["Location"])
        self.assertContains(r, "Saiu")
        self.wallet.refresh_from_db()
        self.assertIn(self.wallet.balance, {Decimal("990"), Decimal("1040")})

    def test_roulette_invalid_selection_rerenders(self):
        self.client.force_login(self.user)
        r = self.client.post(reverse("casino:roulette"), {"bet_type": "NUMBER", "selection": "40", "stake": "10"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "de 0 a 36")
        self.assertEqual(CasinoRound.objects.count(), 0)

    def test_result_pages_carry_animation_data(self):
        self.client.force_login(self.user)
        rnd = services.play_roulette(self.user, "RED", "", Decimal("5"), rng=random.Random(2))
        r = self.client.get(f"{reverse('casino:roulette')}?r={rnd.pk}")
        self.assertContains(r, f'data-roleta="{rnd.details["number"]}"')
        self.assertContains(r, 'id="roleta-ordem"')
        self.assertContains(r, '[0, "verde"], [32, "vermelho"]')
        rnd = services.play_slots(self.user, Decimal("5"), rng=random.Random(3))
        r = self.client.get(f"{reverse('casino:slots')}?r={rnd.pk}")
        self.assertContains(r, "data-caca-niquel")
        self.assertContains(r, f'data-final="{rnd.details["symbols"][0]}"')
        self.assertContains(r, 'id="simbolos-rolo"')
        rnd = services.play_dice(self.user, pick=2, stake=Decimal("5"), rng=random.Random(4))
        r = self.client.get(f"{reverse('casino:dice')}?r={rnd.pk}")
        self.assertContains(r, f'data-dado="{rnd.details["result"]}"')
        self.assertContains(r, 'class="pip"', count=9)

    def test_roulette_and_slots_post(self):
        self.client.force_login(self.user)
        r = self.client.post(reverse("casino:roulette"), {"bet_type": "RED", "selection": "", "stake": "5"})
        self.assertEqual(r.status_code, 302)
        r = self.client.post(reverse("casino:slots"), {"stake": "5"})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(CasinoRound.objects.count(), 2)
        r = self.client.get(r["Location"])
        self.assertEqual(r.status_code, 200)

    def test_insufficient_funds_rerenders_with_error(self):
        self.client.force_login(self.user)
        wallet_services.debit(self.wallet, Decimal("995"), "DICE", "zera")
        r = self.client.post(reverse("casino:slots"), {"stake": "10"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Saldo insuficiente")

    def test_round_of_other_user_is_404(self):
        other = get_user_model().objects.create_user("beto", password="x")
        rnd = services.play_dice(other, pick=1, stake=Decimal("1"))
        self.client.force_login(self.user)
        r = self.client.get(f"{reverse('casino:dice')}?r={rnd.pk}")
        self.assertEqual(r.status_code, 404)
        r = self.client.get(f"{reverse('casino:roulette')}?r=abc")
        self.assertEqual(r.status_code, 404)
        r = self.client.get(f"{reverse('casino:dice')}?r=²")
        self.assertEqual(r.status_code, 404)
