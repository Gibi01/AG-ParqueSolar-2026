import json
import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import box, Point, LineString, Polygon
from sqlalchemy import text

from src.climate.records import PixelClimate
from src.config.settings import load_settings
from src.database.spatial import SpatialRepository, config_signature
from src.main import cmd_optimize
from src.pipeline.preprocess import run_preprocessing
from src.gis.spatial_operations import urban_exclusion_mask


class CompleteClimate:
    def get_monthly_radiation(self, cells):
        # One native pixel shared by every optimization cell, no interpolation.
        mapping = pd.DataFrame({'grid_cell_id': [c.grid_cell_id for c in cells], 'climate_pixel_id': '0:0'})
        records = pd.DataFrame([dict(climate_pixel_id='0:0', year=2024, month=m,
                                    radiation_kwh_m2=150., complete=True) for m in (1, 4, 7, 10)])
        return PixelClimate(mapping, records)


def spatial_fixture():
    region = gpd.GeoDataFrame(geometry=[box(500000, 6600000, 502000, 6602000)], crs=32720)
    urban = gpd.GeoDataFrame(geometry=[box(600000, 6700000, 601000, 6701000)], crs=32720)
    lines = gpd.GeoDataFrame({'tension_v': [132000]}, geometry=[LineString([(500000, 6600000), (500000, 6602000)])], crs=32720)
    stations = gpd.GeoDataFrame({'id': ['ST', 'CN', 'RO', 'RM'], 'nombre': ['A', 'B', 'C', 'D']},
                               geometry=[Point(500000 + i * 500, 6600000) for i in range(4)], crs=32720)
    return region, urban, lines, stations


class SpatialPipelineTests(unittest.TestCase):
    def test_nonempty_mask_survives_snapshot_and_no_park_intersects_it(self):
        settings = load_settings()
        settings.climate.end_year = 2024
        settings.genetic_algorithm.population_size = 12
        settings.genetic_algorithm.generations = 5
        region, _, lines, stations = spatial_fixture()
        outline = Polygon(box(500750, 6600750, 501250, 6601250).exterior.coords,
                          holes=[box(500900, 6600900, 501100, 6601100).exterior.coords])
        urban = gpd.GeoDataFrame({'codaglo': ['0003'], 'nam': ['Ciudad de prueba']},
                                 geometry=[outline], crs=32720)
        with tempfile.TemporaryDirectory() as directory:
            settings.paths.results = Path(directory) / 'results'
            repo = SpatialRepository(Path(directory) / 'spatial.sqlite')
            try:
                # Existing BAHRA snapshots have only this geometry schema.
                with repo.engine.begin() as connection:
                    connection.execute(text('CREATE TABLE layer_urban (dataset_id TEXT, geometry_wkt TEXT)'))
                grid = run_preprocessing(settings, repo, region, urban, lines, stations, CompleteClimate())
                self.assertEqual(int((~grid.valid).sum()), 4)
                dataset = repo.load_dataset(config_signature(settings))
                self.assertEqual(dataset['urban_envelopes'].nam.tolist(), ['Ciudad de prueba'])
                mask = dataset['urban_mask'].to_crs(grid.crs)
                self.assertAlmostEqual(mask.geometry.area.sum(), 250000, places=3)
                self.assertTrue(mask.geometry.union_all().covers(Point(501000, 6601000)))
                self.assertFalse(urban_exclusion_mask(grid.loc[grid.valid], mask).any())
                result = cmd_optimize(settings, repo)
                for raw in result.top10.cell_ids:
                    chosen = grid.loc[grid.cell_id.isin(json.loads(raw))]
                    self.assertFalse(urban_exclusion_mask(chosen, mask).any())
                run = next(settings.paths.results.iterdir())
                html = (run / 'map.html').read_text(encoding='utf-8')
                self.assertIn('INDEC', html)
                self.assertIn('Marco Geoestad', html)
                meta = json.loads((run / 'optimization_run.json').read_text(encoding='utf-8'))
                self.assertEqual(meta['dataset']['urban_exclusion']['interior_holes_count'], 1)
                self.assertEqual(meta['dataset']['urban_exclusion']['excluded_cells'], 4)
                self.assertEqual(meta['search_version'], 4)
                self.assertEqual(meta['fitness_version'], 2)
                self.assertEqual(meta['compactness']['weight'], .1)
                ranking = pd.read_csv(run / 'ranking.csv')
                self.assertTrue(ranking.compactness_score.between(0, 1).all())
                self.assertTrue(ranking.park_perimeter_m.gt(0).all())
                self.assertIn('Perímetro total:', html)
                self.assertEqual(meta['crossover_operator'], 'competitive_homologous')
            finally:
                repo.engine.dispose()

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
                self.assertEqual((run / 'evolution.html').read_text(encoding='utf-8').count('<svg '), 6)
                self.assertTrue(pd.read_csv(run / 'history.csv').std_fitness.ge(0).all())
                geojson = json.loads((run / 'parks.geojson').read_text())
                self.assertTrue(all(f['geometry']['type'] == 'Polygon' for f in geojson['features']))
                self.assertTrue(all(f['properties']['station_id'] in ('ST', 'CN', 'RO', 'RM') for f in geojson['features']))
            repo.engine.dispose()
