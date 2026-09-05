"""Shared fixtures. No test in this suite touches the network — GeoDataFrames
are built directly from in-memory geometries, never fetched."""

from __future__ import annotations

import geopandas as gpd
import pytest
from shapely.geometry import box

# A small square "region" (~50km x 50km) around a point in Santa Fe,
# already in WGS84, used by every test that needs a boundary.
_REGION_BOUNDS = (-61.2, -32.2, -60.7, -31.7)  # minx, miny, maxx, maxy (approx 50km square)


@pytest.fixture
def region_boundary_gdf() -> gpd.GeoDataFrame:
    geom = box(*_REGION_BOUNDS)
    return gpd.GeoDataFrame({"region_name": ["Test Region"], "region_code": ["00"]}, geometry=[geom], crs="EPSG:4326")
