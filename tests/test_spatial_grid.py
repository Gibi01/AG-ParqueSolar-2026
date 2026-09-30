import unittest

import geopandas as gpd
from shapely.geometry import MultiPolygon, box

from src.gis.grid import build_grid, build_neighbors


class SpatialGridTests(unittest.TestCase):
    def test_partial_components_and_ids_are_reproducible(self):
        region = gpd.GeoDataFrame(geometry=[MultiPolygon([
            box(0, 0, 200, 200), box(300, 300, 400, 400),
        ])], crs=32720)
        first = build_grid(region, .5, region.crs).gdf
        second = build_grid(region, .5, region.crs).gdf
        self.assertEqual(len(first), 2)
        self.assertAlmostEqual(first.cell_area_m2.sum(), 50000)
        self.assertEqual(first[['row', 'column', 'component']].values.tolist(),
                         [[0, 0, 0], [0, 0, 1]])
        self.assertEqual(first.cell_id.tolist(), second.cell_id.tolist())
        self.assertTrue(first.geometry.geom_equals(second.geometry).all())

    def test_neighbors_share_edge_not_corner(self):
        region = gpd.GeoDataFrame(geometry=[box(0, 0, 1000, 1000)], crs=32720)
        grid = build_grid(region, .5, region.crs).gdf
        graph = build_neighbors(grid)
        self.assertEqual(graph[1], (2, 3))
        self.assertNotIn(4, graph[1])
        self.assertTrue((grid.cell_area_m2 == 250000).all())
        valid = grid[grid.cell_id != 2]
        self.assertNotIn(2, build_neighbors(valid)[1])
