"""Fixtures compartidas. Ningún test de esta suite toca la red — los
GeoDataFrames se construyen directamente a partir de geometrías en
memoria, nunca se descargan."""

from __future__ import annotations

import geopandas as gpd
import pytest
from shapely.geometry import box

# Una pequeña "región" cuadrada (~50km x 50km) alrededor de un punto en
# Santa Fe, ya en WGS84, usada por todo test que necesite un límite.
_REGION_BOUNDS = (-61.2, -32.2, -60.7, -31.7)  # minx, miny, maxx, maxy (cuadrado de ~50km aprox.)


@pytest.fixture
def region_boundary_gdf() -> gpd.GeoDataFrame:
    geom = box(*_REGION_BOUNDS)
    return gpd.GeoDataFrame({"region_name": ["Test Region"], "region_code": ["00"]}, geometry=[geom], crs="EPSG:4326")
