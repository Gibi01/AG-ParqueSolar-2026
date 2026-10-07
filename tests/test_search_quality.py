import unittest
import geopandas as gpd
import numpy as np
from shapely.geometry import box, LineString, Point
from src.config.settings import FitnessWeights, ParkConfig, GeneticAlgorithmConfig
from src.gis.grid import build_neighbors
from src.optimization.spatial import ParkEvaluator
from tasks.compare_search_quality import encode_cells, enumerate_rectangles, local_neighbors, random_search, connected


def fixture():
    cells = [(r,c) for r in range(3) for c in range(4)]
    grid = gpd.GeoDataFrame(dict(cell_id=range(1,13), row=[p[0] for p in cells],
                                column=[p[1] for p in cells], component=0, valid=True,
                                cell_area_m2=250000., solar_annual_kwh_m2=np.arange(1800.,1812.)),
                            geometry=[box(c*500,r*500,(c+1)*500,(r+1)*500) for r,c in cells], crs=32720)
    grid['centroid_x_m'], grid['centroid_y_m'] = grid.geometry.centroid.x, grid.geometry.centroid.y
    lines = gpd.GeoDataFrame(geometry=[LineString([(0,0),(0,1500)])],crs=32720)
    et = gpd.GeoDataFrame(dict(station_id=['A'],nombre=['A']),geometry=[Point(0,0)],crs=32720)
    weights = FitnessWeights(weight_solar=.35,weight_grid_distance=.1,
                             weight_transformer_distance=.35,weight_installed_power=.1,weight_compactness=.1)
    return ParkEvaluator(grid,build_neighbors(grid),lines,et,ParkConfig(),weights)


class SearchQualityTests(unittest.TestCase):
    def test_rectangle_enumeration_matches_direct_objective_and_count(self):
        ev = fixture()
        rectangles, _, stats = enumerate_rectangles(ev, [.5],batch_size=7)
        self.assertEqual(stats['evaluations'],59)
        exact = []
        import json
        for row in rectangles.itertuples():
            park = ev.evaluate(encode_cells(json.loads(row.cell_ids),ev))
            self.assertAlmostEqual(row.fitness,park.metrics['fitness'],places=10)
            exact.append(park.metrics['fitness'])
        self.assertEqual(stats['counts_above_threshold'][0],sum(x>.5000001 for x in exact))

    def test_local_moves_preserve_connection_capacity_and_can_translate(self):
        ev = fixture()
        moves = list(local_neighbors([1,2,5,6],ev))
        self.assertTrue(any(len(p)==3 for p in moves))
        self.assertTrue(any(len(p)==4 and 1 not in p for p in moves))
        self.assertTrue(any(len(p)==5 for p in moves))
        for cells in moves:
            self.assertTrue(connected(set(cells),ev))
            park = ev.evaluate(encode_cells(cells,ev))
            self.assertEqual(set(park.cell_ids),set(cells))
            self.assertLessEqual(park.metrics['installed_power_mw'],80)

    def test_random_and_local_respect_budget_and_replay(self):
        ev = fixture()
        config = GeneticAlgorithmConfig(population_size=8,generations=2,crossover_probability=.75,
                                        mutation_probability=.2,elitism=2,tournament_size=3)
        for local in (False,True):
            a,_ = random_search(ev,config,42,100,local)
            b,_ = random_search(ev,config,42,100,local)
            self.assertEqual(a.computations,100)
            self.assertEqual(a.best,b.best)
            self.assertEqual(a.requests,b.requests)
            self.assertEqual(a.candidates().to_json(),b.candidates().to_json())
            values = [p['best_fitness'] for p in a.curve]
            self.assertEqual(values,sorted(values))
