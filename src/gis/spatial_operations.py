"""Spatial operations on layers: buffering and exclusion masks.

`urban_exclusion_mask` implements the hard requirement that any grid
cell intersecting an urban area is EXCLUDED outright — never merely
penalised in fitness.
"""

from __future__ import annotations

from pyproj import CRS

import geopandas as gpd
import pandas as pd

from src.gis.crs import to_projected


def buffer_points_km(points_gdf: gpd.GeoDataFrame, buffer_km: float, projected_crs: CRS) -> gpd.GeoDataFrame:
    """Buffer point geometries by `buffer_km` in a metric CRS.

    Used to approximate an urban footprint from BAHRA's point-only
    localities (see README for why this is an approximation, and how to
    replace it once a real urban-polygon layer is available).
    """
    proj = to_projected(points_gdf, projected_crs).copy()
    proj["geometry"] = proj.geometry.buffer(buffer_km * 1000.0)
    return proj


def urban_exclusion_mask(grid_gdf: gpd.GeoDataFrame, urban_polygons_proj: gpd.GeoDataFrame) -> pd.Series:
    """Return a boolean Series (aligned with grid_gdf's index) that is True
    for cells intersecting ANY urban (buffered) polygon — to be excluded.

    Both inputs must already share the same projected CRS.
    """
    if len(urban_polygons_proj) == 0:
        return pd.Series(False, index=grid_gdf.index)
    urban_union = urban_polygons_proj.geometry.union_all()
    return grid_gdf.geometry.intersects(urban_union)
