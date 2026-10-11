from fractions import Fraction

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from learn import simulator


class SimulatorTests(SimpleTestCase):
    def test_dice(self):
        result = simulator.simulate("DICE", 1000, seed=1)
        self.assertEqual(result["staked"], 1000)
        self.assertEqual(result["rounds"], 1000)
        self.assertLessEqual(len(result["series"]), 400)
        self.assertEqual(result["theoretical_rate"], Fraction(5, 6))
        self.assertEqual(result["returned"], result["wins"] * 5)
        self.assertEqual(result["net"], result["returned"] - result["staked"])
        self.assertEqual(result["return_rate"], Fraction(result["returned"], 1000))
        self.assertEqual(result["series"][-1], result["net"])
        self.assertTrue(0 <= result["longest_losing_streak"] <= 1000)
        self.assertGreaterEqual(result["peak"], result["trough"])
        self.assertEqual(result["label"], "Dado: acertar a face")

    def test_other_games(self):
        self.assertGreaterEqual(simulator.simulate("SLOTS", 100, seed=2)["returned"], 0)
        self.assertEqual(simulator.simulate("BICHO_MILHAR", 100, seed=3)["theoretical_rate"], Fraction(2, 5))
        self.assertEqual(simulator.simulate("BICHO_GRUPO", 100, seed=3)["theoretical_rate"], Fraction(18, 25))
        self.assertEqual(simulator.simulate("ROULETTE_NUMBER", 100, seed=3)["theoretical_rate"], Fraction(36, 37))
        self.assertEqual(simulator.simulate("ROULETTE_RED", 100, seed=3)["theoretical_rate"], Fraction(36, 37))
        self.assertEqual(len(simulator.GAMES), 8)

    def test_determinism(self):
        self.assertEqual(simulator.simulate("ROULETTE_RED", 500, seed=7), simulator.simulate("ROULETTE_RED", 500, seed=7))

    def test_bounds(self):
        with self.assertRaises(ValueError):
            simulator.simulate("DICE", 99)
        with self.assertRaises(ValueError):
            simulator.simulate("DICE", 50001)
        with self.assertRaises(ValueError):
            simulator.simulate("POKER", 100)


class ViewTests(TestCase):
    def test_pages_render(self):
        for name, needle in [
            ("learn:index", "Fica com a banca"),
            ("learn:bicho", "Avestruz"),
            ("learn:probability", "valor esperado"),
            ("learn:fallacies", "número atrasado"),
            ("learn:legal", "188"),
            ("learn:simulator", "Simular"),
        ]:
            r = self.client.get(reverse(name))
            self.assertEqual(r.status_code, 200, name)
            self.assertContains(r, needle)

    def test_simulator_post(self):
        r = self.client.post(reverse("learn:simulator"), {"game": "DICE", "rounds": "500", "seed": "1"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Retorno real")
        self.assertContains(r, "<polyline")
        self.assertNotRegex(r.content.decode(), r'y[12]="[0-9]+,[0-9]+"')
        self.assertNotRegex(r.content.decode(), r'points="[^"]*[0-9],[0-9]+,')

    def test_simulator_invalid(self):
        r = self.client.post(reverse("learn:simulator"), {"game": "DICE", "rounds": "10"})
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "Retorno real")
