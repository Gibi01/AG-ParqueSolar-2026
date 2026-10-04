"""Regression cases for INDEC urban envelopes, independent of network data."""

import unittest

import geopandas as gpd
from pyproj import CRS
from shapely.geometry import LineString, Point, Polygon, box

from src.gis.spatial_operations import build_urban_mask, prepare_urban_mask, urban_exclusion_mask


METRIC_CRS = CRS.from_epsg(32720)


def layer(geometries, crs=METRIC_CRS):
    return gpd.GeoDataFrame(geometry=geometries, crs=crs)


class UrbanEnvelopeTests(unittest.TestCase):
    def test_irregular_outline_does_not_exclude_open_exterior_land(self):
        # The missing upper-right corner is open to the countryside.
        outline = Polygon([(0, 0), (300, 0), (300, 100), (100, 100),
                           (100, 300), (0, 300)])
        mask = build_urban_mask(layer([outline]), 0, METRIC_CRS)
        self.assertEqual(mask.crs, METRIC_CRS)
        self.assertTrue(mask.geometry.union_all().equals(outline))
        self.assertFalse(mask.geometry.union_all().intersects(box(150, 150, 200, 200)))

    def test_union_precedes_filling_hole_formed_by_multiple_components(self):
        pieces = [box(0, 0, 100, 300), box(200, 0, 300, 300),
                  box(100, 0, 200, 100), box(100, 200, 200, 300)]
        filled = build_urban_mask(layer(pieces), 0, METRIC_CRS)
        unfilled = build_urban_mask(layer(pieces), 0, METRIC_CRS, fill_holes=False)
        courtyard = box(120, 120, 180, 180)
        self.assertTrue(filled.geometry.union_all().covers(courtyard))
        self.assertFalse(unfilled.geometry.union_all().intersects(courtyard))

    def test_fill_holes_keeps_disconnected_components_separate(self):
        donut = Polygon(box(0, 0, 300, 300).exterior.coords,
                        holes=[box(100, 100, 200, 200).exterior.coords])
        mask = build_urban_mask(layer([donut, box(600, 0, 800, 300)]),
                                0, METRIC_CRS)
        union = mask.geometry.union_all()
        self.assertTrue(union.covers(box(120, 120, 180, 180)))
        self.assertFalse(union.intersects(box(400, 100, 500, 200)))

    def test_margin_is_measured_from_polygon_perimeter_in_metres(self):
        mask = build_urban_mask(layer([box(500000, 6600000, 501000, 6601000)]),
                                .1, METRIC_CRS)
        union = mask.geometry.union_all()
        self.assertEqual(union.bounds, (499900, 6599900, 501100, 6601100))
        self.assertTrue(union.covers(Point(501090, 6600500)))
        self.assertFalse(union.covers(Point(501110, 6600500)))

    def test_geographic_source_is_reprojected_before_buffer(self):
        metric = layer([box(500000, 6600000, 501000, 6601000)])
        mask = build_urban_mask(metric.to_crs(4326), .1, METRIC_CRS)
        self.assertEqual(mask.crs, METRIC_CRS)
        for actual, expected in zip(mask.total_bounds,
                                    (499900, 6599900, 501100, 6601100)):
            self.assertAlmostEqual(actual, expected, places=5)

    def test_self_crossing_polygon_is_repaired(self):
        bowtie = Polygon([(0, 0), (200, 200), (0, 200), (200, 0), (0, 0)])
        self.assertFalse(bowtie.is_valid)
        mask = build_urban_mask(layer([bowtie]), 0, METRIC_CRS)
        self.assertTrue(mask.geometry.is_valid.all())
        self.assertTrue(mask.geometry.geom_type.isin(['Polygon', 'MultiPolygon']).all())
        self.assertTrue(mask.geometry.union_all().covers(Point(100, 25)))
        self.assertTrue(mask.geometry.union_all().covers(Point(100, 175)))

    def test_empty_or_nonpolygonal_source_is_rejected(self):
        for geometries in ([], [Polygon()], [None], [Point(0, 0)],
                           [LineString([(0, 0), (10, 10)])],
                           [box(0, 0, 100, 100), Point(200, 200)]):
            with self.subTest(geometries=geometries):
                with self.assertRaises(ValueError):
                    build_urban_mask(layer(geometries), 0, METRIC_CRS)

    def test_exclusion_includes_partial_overlap_and_boundary_contact(self):
        mask = build_urban_mask(layer([box(0, 0, 100, 100)]), 0, METRIC_CRS)
        grid = layer([box(90, 90, 190, 190), box(100, 10, 200, 90),
                      box(100, 100, 200, 200), box(101, 101, 201, 201)])
        grid.index = [14, 27, 35, 49]
        excluded = urban_exclusion_mask(grid, mask)
        self.assertEqual(excluded.index.tolist(), [14, 27, 35, 49])
        self.assertEqual(excluded.tolist(), [True, True, True, False])

    def test_exclusion_rejects_inconsistent_crs(self):
        mask = layer([box(500000, 6600000, 501000, 6601000)])
        with self.assertRaises(ValueError):
            urban_exclusion_mask(mask.to_crs(4326), mask)

    def test_mask_requires_known_source_and_metric_target_crs(self):
        with self.assertRaises(ValueError):
            build_urban_mask(layer([box(0, 0, 100, 100)], crs=None), 0, METRIC_CRS)
        with self.assertRaises(ValueError):
            build_urban_mask(layer([box(0, 0, 100, 100)]), .1, CRS.from_epsg(4326))

    def test_negative_margin_is_rejected(self):
        with self.assertRaises(ValueError):
            build_urban_mask(layer([box(0, 0, 100, 100)]), -.1, METRIC_CRS)


class PrepareUrbanMaskTests(unittest.TestCase):
    def test_na_code_does_not_select_distant_simple_localities(self):
        urban = layer([box(0, 0, 100, 100), box(10000, 10000, 10100, 10100)])
        urban['codaglo'] = ['N/A', 'N/A']
        urban['fid'] = [1, 2]
        selected, mask = prepare_urban_mask(
            urban, layer([box(-50, -50, 500, 500)]), 0, METRIC_CRS)
        self.assertEqual(selected.fid.tolist(), [1])
        self.assertTrue(mask.geometry.union_all().equals(box(0, 0, 100, 100)))

    def test_outside_locality_margin_reaches_provincial_edge(self):
        region = layer([box(0, 0, 1000, 1000)])
        urban = layer([box(1050, 400, 1150, 600)])
        urban['codaglo'] = ['N/A']
        selected, mask = prepare_urban_mask(urban, region, .1, METRIC_CRS)
        self.assertEqual(len(selected), 1)
        self.assertTrue(mask.geometry.union_all().covers(Point(975, 500)))
        self.assertTrue(region.geometry.union_all().covers(mask.geometry.union_all()))
        excluded = urban_exclusion_mask(layer([box(900, 450, 1000, 550)]), mask)
        self.assertEqual(excluded.tolist(), [True])

    def test_fill_hole_before_crop_opens_it_at_provincial_boundary(self):
        donut = Polygon(box(0, 0, 300, 300).exterior.coords,
                        holes=[box(100, 100, 200, 200).exterior.coords])
        urban = layer([donut])
        urban['codaglo'] = ['N/A']
        region = layer([box(0, 0, 150, 300)])
        _, mask = prepare_urban_mask(urban, region, 0, METRIC_CRS)
        self.assertTrue(mask.geometry.union_all().covers(box(110, 110, 140, 190)))
        _, unfilled = prepare_urban_mask(urban, region, 0, METRIC_CRS, fill_holes=False)
        self.assertFalse(unfilled.geometry.union_all().intersects(box(110, 110, 140, 190)))

    def test_complete_agglomeration_selected_even_for_distant_component(self):
        urban = layer([box(0, 0, 100, 100), box(10000, 10000, 10100, 10100),
                       box(20000, 20000, 20100, 20100)])
        urban['codaglo'] = ['0003', '0003', '0004']
        urban['fid'] = [1, 2, 3]
        selected, mask = prepare_urban_mask(
            urban, layer([box(-50, -50, 500, 500)]), 0, METRIC_CRS)
        self.assertEqual(selected.fid.tolist(), [1, 2])
        self.assertTrue(mask.geometry.union_all().equals(box(0, 0, 100, 100)))

    def test_simple_localities_do_not_fill_joint_hole_but_agglomeration_does(self):
        urban = layer([box(0, 0, 100, 300), box(200, 0, 300, 300),
                       box(100, 0, 200, 100), box(100, 200, 200, 300)])
        region = layer([box(-10, -10, 310, 310)])
        courtyard = box(120, 120, 180, 180)
        urban['codaglo'] = ['N/A'] * 4
        _, simple_mask = prepare_urban_mask(urban, region, 0, METRIC_CRS)
        self.assertFalse(simple_mask.geometry.union_all().intersects(courtyard))
        urban['codaglo'] = ['0003'] * 4
        _, agglomeration_mask = prepare_urban_mask(urban, region, 0, METRIC_CRS)
        self.assertTrue(agglomeration_mask.geometry.union_all().covers(courtyard))

    def test_empty_source_is_rejected(self):
        with self.assertRaises(ValueError):
            prepare_urban_mask(layer([]), layer([box(0, 0, 100, 100)]), 0, METRIC_CRS)
