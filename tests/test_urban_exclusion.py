import math

import geopandas as gpd
import pytest
from shapely.geometry import Point, box

from src.gis.spatial_operations import buffer_points_km, urban_exclusion_mask

PROJECTED_CRS = "EPSG:5346"


def test_buffer_points_km_produces_polygons_of_expected_radius():
    points = gpd.GeoDataFrame({"id": [1]}, geometry=[Point(0, 0)], crs=PROJECTED_CRS)
    buffered = buffer_points_km(points, buffer_km=2.0, projected_crs=PROJECTED_CRS)
    # A circle of radius 2000m has area pi*r^2; allow generous tolerance
    # for polygon approximation of the circle.
    expected_area = math.pi * (2000**2)
    assert buffered.geometry.iloc[0].area == pytest.approx(expected_area, rel=0.02)


def test_urban_exclusion_mask_flags_intersecting_cells():
    cell_far = box(-1000, -1000, -500, -500)
    cell_near = box(0, 0, 1000, 1000)
    grid = gpd.GeoDataFrame({"cell_id": [1, 2]}, geometry=[cell_far, cell_near], crs=PROJECTED_CRS)

    urban_point = gpd.GeoDataFrame({"id": [1]}, geometry=[Point(500, 500)], crs=PROJECTED_CRS)
    buffered = buffer_points_km(urban_point, buffer_km=0.1, projected_crs=PROJECTED_CRS)

    mask = urban_exclusion_mask(grid, buffered)
    assert list(mask) == [False, True]


def test_urban_exclusion_mask_empty_urban_layer_excludes_nothing():
    grid = gpd.GeoDataFrame({"cell_id": [1]}, geometry=[box(0, 0, 1000, 1000)], crs=PROJECTED_CRS)
    empty_urban = gpd.GeoDataFrame({"id": []}, geometry=[], crs=PROJECTED_CRS)
    mask = urban_exclusion_mask(grid, empty_urban)
    assert list(mask) == [False]
