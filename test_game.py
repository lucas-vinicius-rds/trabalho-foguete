"""Validação numérica dos requisitos; execute com py -m unittest -v."""
import math
import unittest

from main import Game
from physics import DT, DRY_MASS, FUEL_MASS, FUEL_PER_FRAME, G, MAX_ANGLE, THRUST
from rocket import Rocket


class PhysicsTests(unittest.TestCase):
    def test_free_fall_and_collision(self):
        rocket = Rocket(y=100)
        frames = 0
        while rocket.alive and frames < 1000:
            rocket.update(DT)
            frames += 1
        self.assertFalse(rocket.alive)
        self.assertLessEqual(abs(frames * DT - math.sqrt(200 / G)), DT)
        self.assertEqual((rocket.y, rocket.vx, rocket.vy), (0, 0, 0))
        self.assertEqual(rocket.fuel, FUEL_MASS)
        rocket.update(DT, True, 1)
        self.assertEqual((rocket.y, rocket.fuel), (0, FUEL_MASS))

    def test_first_thrust_frame(self):
        rocket = Rocket()
        rocket.update(DT, True)
        self.assertEqual(rocket.fuel, FUEL_MASS - FUEL_PER_FRAME)
        expected_vy = (THRUST / (DRY_MASS + FUEL_MASS) - G) * DT
        self.assertAlmostEqual(rocket.vy, expected_vy)
        self.assertAlmostEqual(rocket.y, 2500 + expected_vy * DT)

    def test_fuel_exhaustion(self):
        rocket = Rocket(y=100_000)
        for _ in range(1000):
            rocket.update(DT, True)
        self.assertEqual(rocket.fuel, 0)
        self.assertEqual(rocket.mass, DRY_MASS)
        vy = rocket.vy
        rocket.update(DT, True)
        self.assertFalse(rocket.thrusting)
        self.assertAlmostEqual(rocket.vy, vy - G * DT)

    def test_angle_limits_and_horizontal_thrust(self):
        for turn in (-1, 1):
            rocket = Rocket()
            for _ in range(120):
                rocket.update(DT, True, turn)
                self.assertLessEqual(abs(rocket.angle), MAX_ANGLE)
            self.assertAlmostEqual(rocket.angle, turn * MAX_ANGLE)
            self.assertGreater(rocket.vx * turn, 0)
            for _ in range(60):
                rocket.update(DT, False, 0)
            self.assertEqual(rocket.angle, 0)

    def test_score_stops_and_record_survives_restart(self):
        game = Game()
        game.rocket = Rocket(y=1)
        for _ in range(100):
            game.update()
        self.assertFalse(game.rocket.alive)
        score = game.elapsed
        game.update(True, 1)
        self.assertEqual(game.elapsed, score)
        game.restart()
        self.assertEqual(game.elapsed, 0)
        self.assertEqual(game.best, score)
        self.assertTrue(game.rocket.alive)
        self.assertEqual(game.rocket.fuel, FUEL_MASS)


if __name__ == "__main__":
    unittest.main()
