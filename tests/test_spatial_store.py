import tempfile
import unittest
from pathlib import Path

import pandas as pd
from test_spatial_growth import example_evaluator
from src.database.spatial import SpatialRepository


class SpatialStoreTests(unittest.TestCase):
    def test_snapshot_round_trip_and_compatible_selection(self):
        evaluator = example_evaluator()
        with tempfile.TemporaryDirectory() as directory:
            repo = SpatialRepository(Path(directory) / 'spatial.sqlite')
            grid = evaluator.grid.copy()
            metadata = {'config_signature': 'test', 'projected_crs': str(grid.crs)}
            key = repo.save_dataset(grid, evaluator.neighbors, pd.DataFrame(), {}, metadata)
            loaded = repo.load_dataset('test')
            self.assertEqual(loaded['dataset_id'], key)
            self.assertEqual(loaded['grid'].cell_id.tolist(), grid.cell_id.tolist())
            self.assertEqual(loaded['neighbors'], evaluator.neighbors)
            self.assertTrue(loaded['grid'].geometry.geom_equals(grid.geometry).all())
            self.assertEqual(repo.save_dataset(grid, evaluator.neighbors, pd.DataFrame(), {}, metadata), key)
            with self.assertRaisesRegex(RuntimeError, 'process'):
                repo.load_dataset('other')
            repo.engine.dispose()

    def test_old_snapshot_survives_new_processing(self):
        evaluator = example_evaluator()
        with tempfile.TemporaryDirectory() as directory:
            repo = SpatialRepository(Path(directory) / 'spatial.sqlite')
            metadata = {'config_signature': 'first', 'projected_crs': str(evaluator.grid.crs)}
            first = repo.save_dataset(evaluator.grid, evaluator.neighbors, pd.DataFrame(), {}, metadata)
            metadata['config_signature'] = 'second'
            second = repo.save_dataset(evaluator.grid, evaluator.neighbors, pd.DataFrame(), {}, metadata)
            self.assertNotEqual(first, second)
            self.assertEqual(repo.load_dataset('first')['dataset_id'], first)
            self.assertEqual(repo.load_dataset('second')['dataset_id'], second)
            repo.engine.dispose()

    def test_historical_database_is_rejected_without_changes(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'legacy.sqlite'
            with sqlite3.connect(path) as conn:
                conn.execute('CREATE TABLE grid_cells (cell_id INTEGER)')
                conn.execute('INSERT INTO grid_cells VALUES (42)')
            conn.close()  # sqlite3's transaction context does not close the Windows file handle.
            before = path.read_bytes()
            with self.assertRaisesRegex(RuntimeError, 'histórica'):
                SpatialRepository(path)
            self.assertEqual(path.read_bytes(), before)
