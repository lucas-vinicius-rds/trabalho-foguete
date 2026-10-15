"""Validação numérica dos requisitos; execute com py -m unittest -v."""
import math
import random
import unittest

from main import FUEL_CELL_AMOUNT, FUEL_CELL_COUNT, FUEL_CELL_RADIUS, MAX_ALTITUDE, Game
from physics import DT, DRY_MASS, FUEL_MASS, FUEL_PER_FRAME, G, MAX_ANGLE, THRUST
from rocket import Rocket


class PhysicsTests(unittest.TestCase):
    def test_altitude_limit_finishes_flight_and_restart_clears_victory(self):
        game = Game()
        game.rocket.y = MAX_ALTITUDE - 1
        game.rocket.vy = 120
        game.update(True)
        self.assertTrue(game.won)
        self.assertTrue(game.rocket.alive)
        self.assertEqual(game.rocket.y, MAX_ALTITUDE)
        self.assertEqual((game.rocket.vx, game.rocket.vy), (0, 0))
        self.assertFalse(game.rocket.thrusting)
        state = (game.elapsed, game.rocket.x, game.rocket.y, game.rocket.fuel)
        for _ in range(60):
            game.update(True, 1)
        self.assertEqual(state, (game.elapsed, game.rocket.x, game.rocket.y, game.rocket.fuel))
        game.restart()
        self.assertFalse(game.won)
        self.assertEqual(game.rocket.y, 1000)
        self.assertEqual(game.elapsed, 0)

    def test_fuel_stays_below_altitude_limit(self):
        game = Game(rng=random.Random(42))
        game.rocket.y = MAX_ALTITUDE - 100
        game.extend_fuel_field()
        self.assertTrue(all(y < MAX_ALTITUDE for x, y in game.fuel_cells))

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
        self.assertAlmostEqual(rocket.y, 1000 + expected_vy * DT)

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

    def test_collect_refuels_once_and_changes_mass(self):
        game = Game()
        game.fuel_cells = [(500, 1000)]
        game.rocket.x, game.rocket.y = game.fuel_cells[0]
        game.rocket.fuel = FUEL_MASS * 0.20
        game.update()
        self.assertEqual(game.collected, 1)
        self.assertNotIn((500, 1000), game.fuel_cells)
        self.assertEqual(game.rocket.fuel, FUEL_MASS * 0.20 + FUEL_CELL_AMOUNT)
        self.assertEqual(game.rocket.mass, DRY_MASS + game.rocket.fuel)
        game.update()
        self.assertEqual(game.collected, 1)
        self.assertEqual(game.rocket.fuel, FUEL_MASS * 0.20 + FUEL_CELL_AMOUNT)

    def test_collect_caps_tank_and_restart_restores_cells(self):
        game = Game()
        game.rocket.x, game.rocket.y = game.fuel_cells[0]
        game.rocket.fuel = FUEL_MASS - 1
        game.update()
        self.assertEqual(game.rocket.fuel, FUEL_MASS)
        game.restart()
        self.assertEqual(game.collected, 0)
        self.assertEqual(sum(abs(x) < 900 and 250 < y < 1800 for x, y in game.fuel_cells), FUEL_CELL_COUNT)
        self.assertEqual(game.rocket.y, 1000)

    def test_four_nearby_cells_and_random_map_on_restart(self):
        game = Game(rng=random.Random(42))
        original = game.fuel_cells[:]
        nearby = [(x, y) for x, y in original if abs(x) < 900 and 250 < y < 1800]
        self.assertEqual(len(nearby), 4)
        self.assertTrue(all(math.hypot(x, y - 1000) > FUEL_CELL_RADIUS for x, y in nearby))
        self.assertTrue(any(x < -2000 for x, y in original))
        self.assertTrue(any(x > 2000 for x, y in original))
        game.restart()
        self.assertNotEqual(original, game.fuel_cells)

    def test_diagonal_and_horizontal_flight_generate_new_regions(self):
        for destination in ((9000, 1000), (-9000, 1000), (9000, 8000)):
            game = Game(rng=random.Random(42))
            original = set(game.fuel_cells)
            game.rocket.x, game.rocket.y = destination
            game.extend_fuel_field()
            added = set(game.fuel_cells) - original
            self.assertGreater(len(added), 0)
            self.assertTrue(any(abs(x - destination[0]) < 2000 for x, y in added))
            self.assertTrue(any(abs(y - destination[1]) < 1500 for x, y in added))

    def test_visited_sectors_do_not_regenerate_collected_fuel(self):
        game = Game(rng=random.Random(42))
        collected_cell = game.fuel_cells[-1]
        game.fuel_cells.remove(collected_cell)
        game.extend_fuel_field()
        self.assertNotIn(collected_cell, game.fuel_cells)
        game.rocket.x = 9000
        game.extend_fuel_field()
        positions = set(game.fuel_cells)
        game.rocket.x = 0
        game.extend_fuel_field()
        self.assertEqual(set(game.fuel_cells), positions)
        self.assertNotIn(collected_cell, game.fuel_cells)

    def test_long_climb_discards_old_cells(self):
        game = Game(rng=random.Random(42))
        for altitude in range(2000, 50000, 1000):
            game.rocket.y = altitude
            game.extend_fuel_field()
        self.assertLess(len(game.fuel_cells), 100)
        self.assertTrue(all(y >= game.highest_y - 6000 for x, y in game.fuel_cells))

    def test_larger_hitbox_collects_nearby_but_not_distant_cells(self):
        game = Game()
        game.fuel_cells = [(FUEL_CELL_RADIUS - 1, 1000), (FUEL_CELL_RADIUS + 1, 1000)]
        game.update()
        self.assertEqual(game.collected, 1)
        self.assertEqual(game.fuel_cells, [(FUEL_CELL_RADIUS + 1, 1000)])

    def test_collection_uses_distance_and_entire_frame_path(self):
        game = Game()
        game.fuel_cells = [(300, 1000)]
        game.update()
        self.assertEqual(game.collected, 0)
        game.rocket.vx = 600 / DT
        game.update()
        self.assertEqual(game.collected, 1)
        self.assertNotIn((300, 1000), game.fuel_cells)

    def test_dead_rocket_cannot_collect(self):
        game = Game()
        game.fuel_cells = [(0, 0)]
        game.rocket = Rocket(y=0.001)
        game.update()
        self.assertFalse(game.rocket.alive)
        self.assertEqual(game.collected, 0)
        self.assertEqual(game.fuel_cells, [(0, 0)])


if __name__ == "__main__":
    unittest.main()
