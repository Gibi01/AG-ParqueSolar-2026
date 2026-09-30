import unittest

import geopandas as gpd
import numpy as np
from shapely.geometry import box

from src.config.settings import ParkConfig, FitnessWeights
from src.optimization.spatial import Individual, ParkEvaluator


def example_evaluator(capacity=10):
    grid = gpd.GeoDataFrame({
        'cell_id': [1, 2, 3], 'row': [0, 0, 1], 'column': [0, 1, 0], 'component': [0, 0, 0],
        'cell_area_m2': [250000., 250000., 50000.],
        'solar_annual_kwh_m2': [1000., 2000., 1600.],
        'valid': [True, True, True],
    }, geometry=[box(0, 0, 500, 500), box(500, 0, 1000, 500), box(0, 500, 100, 1000)], crs=32720)
    grid['centroid_x_m'] = grid.geometry.centroid.x
    grid['centroid_y_m'] = grid.geometry.centroid.y
    empty = gpd.GeoDataFrame(geometry=[], crs=32720)
    weights = FitnessWeights(weight_solar=.75, weight_grid_distance=0, weight_transformer_distance=0,
                             weight_installed_power=.25)
    return ParkEvaluator(grid, {1: (2, 3), 2: (1,), 3: (1,)}, empty, empty,
                         ParkConfig(max_connection_capacity_mw=capacity), weights)


class GrowthTests(unittest.TestCase):
    def test_skip_excess_then_accept_partial(self):
        evaluator = example_evaluator()
        genome = Individual(1, (0, 1))
        park = evaluator.evaluate(genome)
        self.assertEqual(park.cell_ids, (1, 3))
        self.assertEqual(park.accepted_gene_indices, (1,))
        self.assertEqual(park.skipped_gene_indices, (0,))
        self.assertEqual(genome.growth_genes, (0, 1))
        self.assertAlmostEqual(park.metrics['park_area_km2'], .3)
        self.assertAlmostEqual(park.metrics['installed_power_mw'], 9.39)
        self.assertAlmostEqual(park.metrics['solar_annual_kwh_m2'], 1100.)
        self.assertAlmostEqual(park.metrics['estimated_annual_energy_mwh'], 10329.)
        self.assertEqual(evaluator.evaluate(genome), park)

    def test_seed_must_fit_and_be_valid(self):
        evaluator = example_evaluator(2)
        self.assertEqual(evaluator.seed_ids.tolist(), [3])
        with self.assertRaises(ValueError):
            evaluator.evaluate(Individual(1, ()))
        with self.assertRaises(ValueError):
            example_evaluator(.1)

    def test_exact_capacity_and_effective_reduction(self):
        evaluator = example_evaluator(15.65)
        bigger = evaluator.evaluate(Individual(1, (0,)))
        smaller = evaluator.evaluate(Individual(1, ()))
        self.assertAlmostEqual(bigger.metrics['installed_power_mw'], 15.65)
        self.assertEqual(bigger.metrics['installed_power_score'], 1)
        self.assertLess(smaller.metrics['park_area_km2'], bigger.metrics['park_area_km2'])

    def test_station_tie_is_resolved_by_source_id(self):
        from shapely.geometry import Point
        evaluator = example_evaluator(20)
        stations = gpd.GeoDataFrame({'station_id': ['Z', 'A'], 'nombre': ['Z', 'A']},
                                   geometry=[Point(0, 250), Point(500, 250)], crs=32720)
        weights = FitnessWeights(weight_solar=0, weight_grid_distance=0, weight_transformer_distance=1)
        tied = ParkEvaluator(evaluator.grid, evaluator.neighbors, gpd.GeoDataFrame(geometry=[], crs=32720),
                             stations, evaluator.config, weights)
        self.assertEqual(tied.evaluate(Individual(1)).metrics['station_id'], 'A')

    def test_long_genomes_never_exceed_capacity_or_duplicate_cells(self):
        evaluator = example_evaluator()
        rng = np.random.default_rng(42)
        for _ in range(100):
            genome = Individual(int(rng.choice(evaluator.seed_ids)), tuple(rng.integers(0, 100, size=50)))
            park = evaluator.evaluate(genome)
            self.assertLessEqual(park.metrics['installed_power_mw'], 10)
            self.assertEqual(len(set(park.cell_ids)), len(park.cell_ids))
            self.assertGreaterEqual(park.metrics['fitness'], 0)
            self.assertLessEqual(park.metrics['fitness'], 1)
