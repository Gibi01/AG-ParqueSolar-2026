import json
import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import box, Point, LineString

from src.climate.records import PixelClimate
from src.config.settings import load_settings
from src.database.spatial import SpatialRepository, config_signature
from src.main import cmd_optimize
from src.pipeline.preprocess import run_preprocessing


class CompleteClimate:
    def get_monthly_radiation(self, cells):
        # One native pixel shared by every optimization cell, no interpolation.
        mapping = pd.DataFrame({'grid_cell_id': [c.grid_cell_id for c in cells], 'climate_pixel_id': '0:0'})
        records = pd.DataFrame([dict(climate_pixel_id='0:0', year=2024, month=m,
                                    radiation_kwh_m2=150., complete=True) for m in (1, 4, 7, 10)])
        return PixelClimate(mapping, records)


def spatial_fixture():
    region = gpd.GeoDataFrame(geometry=[box(500000, 6600000, 502000, 6602000)], crs=32720)
    urban = gpd.GeoDataFrame({'tipo': []}, geometry=[], crs=4326)
    lines = gpd.GeoDataFrame({'tension_v': [132000]}, geometry=[LineString([(500000, 6600000), (500000, 6602000)])], crs=32720)
    stations = gpd.GeoDataFrame({'id': ['ST', 'CN', 'RO', 'RM'], 'nombre': ['A', 'B', 'C', 'D']},
                               geometry=[Point(500000 + i * 500, 6600000) for i in range(4)], crs=32720)
    return region, urban, lines, stations


class SpatialPipelineTests(unittest.TestCase):
    def test_process_optimize_and_map_without_network(self):
        settings = load_settings()
        settings.climate.end_year = 2024
        settings.genetic_algorithm.population_size = 12
        settings.genetic_algorithm.generations = 5
        with tempfile.TemporaryDirectory() as directory:
            settings.paths.results = Path(directory) / 'results'
            repo = SpatialRepository(Path(directory) / 'spatial.sqlite')
            grid = run_preprocessing(settings, repo, *spatial_fixture(), CompleteClimate())
            self.assertEqual(len(grid), 16)
            self.assertEqual(grid.climate_pixel_id.nunique(), 1)
            self.assertTrue(grid.climate_valid_years_1.eq(1).all())
            loaded = repo.load_dataset(config_signature(settings))
            self.assertEqual(len(loaded['climate']), 4)
            for capacity in (40, 80, 120, 160):
                settings.park.max_connection_capacity_mw = capacity
                result = cmd_optimize(settings, repo)
                self.assertTrue(result.top10.installed_power_mw.le(capacity).all())
            runs = list(settings.paths.results.iterdir())
            self.assertEqual(len(runs), 4)
            for run in runs:
                html = (run / 'map.html').read_text(encoding='utf-8')
                self.assertIn('Capacidad EXPERIMENTAL', html)
                self.assertIn('Energía anual ideal', html)
                self.assertIn('TOP 5 territorial', html)
                self.assertLessEqual(len(pd.read_csv(run / 'ranking.csv')), 5)
                self.assertLessEqual(len(pd.read_csv(run / 'ranking_territorial.csv')), 5)
                self.assertEqual((run / 'evolution.html').read_text(encoding='utf-8').count('<svg '), 4)
                geojson = json.loads((run / 'parks.geojson').read_text())
                self.assertTrue(all(f['geometry']['type'] == 'Polygon' for f in geojson['features']))
                self.assertTrue(all(f['properties']['station_id'] in ('ST', 'CN', 'RO', 'RM') for f in geojson['features']))
            repo.engine.dispose()
