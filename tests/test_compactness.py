"""Geometric and fitness checks independent of the GA search trajectory."""
import math
import unittest

import geopandas as gpd
import pandas as pd
import shapely
from pydantic import ValidationError
from shapely.geometry import box

from src.config.settings import FitnessWeights, ParkConfig, load_settings
from src.database.spatial import config_signature
from src.gis.grid import build_neighbors
from src.optimization.fitness import compute_fitness
from src.optimization.spatial import Individual, ParkEvaluator


def evaluator_for(geometries, weights=None):
    grid = gpd.GeoDataFrame({
        'cell_id': range(1, len(geometries) + 1), 'row': range(len(geometries)),
        'column': 0, 'component': 0, 'valid': True,
        'solar_annual_kwh_m2': 1800.,
    }, geometry=geometries, crs=32720)
    grid['cell_area_m2'] = grid.geometry.area
    grid['centroid_x_m'] = grid.geometry.centroid.x
    grid['centroid_y_m'] = grid.geometry.centroid.y
    empty = gpd.GeoDataFrame(geometry=[], crs=32720)
    weights = weights or FitnessWeights(weight_solar=0, weight_grid_distance=0,
                                       weight_transformer_distance=0, weight_compactness=1)
    return ParkEvaluator(grid, build_neighbors(grid), empty, empty,
                         ParkConfig(max_connection_capacity_mw=80), weights)


class CompactnessTests(unittest.TestCase):
    def test_compact_block_beats_chain_with_same_area_and_power(self):
        block = evaluator_for([box(0, 0, 500, 500), box(500, 0, 1000, 500),
                               box(0, 500, 500, 1000), box(500, 500, 1000, 1000)])
        chain = evaluator_for([box(i*500, 0, (i+1)*500, 500) for i in range(4)])
        a = block.evaluate(Individual(1, (0, 0, 0))).metrics
        b = chain.evaluate(Individual(1, (0, 0, 0))).metrics
        self.assertEqual(a['park_area_km2'], b['park_area_km2'])
        self.assertEqual(a['installed_power_mw'], b['installed_power_mw'])
        self.assertEqual(a['park_perimeter_m'], 4000)
        self.assertEqual(b['park_perimeter_m'], 5000)
        self.assertAlmostEqual(a['compactness_score'], math.pi/4)
        self.assertGreater(a['fitness'], b['fitness'])

    def test_partial_cells_and_holes_match_union_boundary(self):
        ring = [box(x*500, y*500, (x+1)*500, (y+1)*500)
                for y in range(3) for x in range(3) if (x, y) != (1, 1)]
        for cells in ([box(0, 0, 500, 500), box(500, 100, 650, 400)], ring):
            with self.subTest(cells=len(cells)):
                ev = evaluator_for(cells)
                park = ev.evaluate(Individual(1, (0,)*20))
                union = shapely.union_all(cells)
                self.assertEqual(len(park.cell_ids), len(cells))
                self.assertAlmostEqual(park.metrics['park_perimeter_m'], union.length)
                self.assertAlmostEqual(park.metrics['compactness_score'],
                                       4*math.pi*union.area/union.length**2)

    def test_same_park_has_same_score_for_different_growth_orders(self):
        ev = evaluator_for([box(0, 0, 500, 500), box(500, 0, 1000, 500),
                            box(0, 500, 500, 1000), box(500, 500, 1000, 1000)])
        a = ev.evaluate(Individual(1, (0, 0, 0)))
        b = ev.evaluate(Individual(4, (1, 0, 0)))
        self.assertEqual(a.cell_ids, b.cell_ids)
        self.assertEqual(a.metrics['compactness_score'], b.metrics['compactness_score'])

    def test_zero_weight_preserves_previous_fitness_and_geometry(self):
        weights = FitnessWeights(weight_solar=1, weight_grid_distance=0,
                                 weight_transformer_distance=0, weight_compactness=0)
        ev = evaluator_for([box(0, 0, 500, 500)], weights)
        park = ev.evaluate(Individual(1))
        self.assertEqual(park.cell_ids, (1,))
        self.assertEqual(park.metrics['fitness'], 1)
        self.assertAlmostEqual(park.metrics['compactness_score'], math.pi/4)
        self.assertEqual(compute_fitness(pd.DataFrame({'solar_score': [.7]}), weights).iloc[0], .7)

    def test_weight_is_validated_combined_and_does_not_invalidate_dataset(self):
        weights = FitnessWeights(weight_solar=.9, weight_grid_distance=0,
                                 weight_transformer_distance=0, weight_compactness=.1)
        result = compute_fitness(pd.DataFrame({'solar_score': [.5], 'compactness_score': [.8]}), weights)
        self.assertAlmostEqual(result.iloc[0], .53)
        for value in (-.1, 1.1, float('nan')):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                FitnessWeights(weight_solar=1, weight_grid_distance=0,
                               weight_transformer_distance=0, weight_compactness=value)
        with self.assertRaises(ValidationError):
            FitnessWeights(weight_solar=1, weight_grid_distance=0,
                           weight_transformer_distance=0, weight_compactness=.1)
        settings = load_settings()
        before = config_signature(settings)
        settings.fitness = FitnessWeights(weight_solar=.4, weight_grid_distance=.1,
                                          weight_transformer_distance=.4, weight_installed_power=.1,
                                          weight_compactness=0)
        self.assertEqual(config_signature(settings), before)
