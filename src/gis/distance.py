"""Minimum-distance calculations, always in a projected (metric) CRS.

Never compute physical distances on raw lat/lon degrees (a naive
sqrt((lat1-lat2)^2 + (lon1-lon2)^2) is not a real distance — degrees of
longitude shrink towards the poles and the two axes aren't even the same
length). Everything here operates in metres after reprojection, and
returns kilometres.
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
from pyproj import CRS

from src.gis.crs import to_projected


def nearest_distance_km(
    source_gdf: gpd.GeoDataFrame,
    target_gdf: gpd.GeoDataFrame,
    projected_crs: CRS,
) -> np.ndarray:
    """For each geometry in `source_gdf`, return the distance (km) to the
    nearest geometry in `target_gdf`, both reprojected into `projected_crs`.

    Uses GeoPandas' spatial-index-backed `sjoin_nearest` rather than an
    O(n*m) loop, since grids can have thousands of cells.
    """
    if len(target_gdf) == 0:
        raise ValueError("target_gdf is empty; cannot compute nearest distances.")

    source_proj = to_projected(source_gdf, projected_crs)[["geometry"]].reset_index(drop=True)
    target_proj = to_projected(target_gdf, projected_crs)[["geometry"]].reset_index(drop=True)

    joined = gpd.sjoin_nearest(source_proj, target_proj, distance_col="distance_m", how="left")
    # sjoin_nearest can emit >1 row per source feature when several target
    # features are exactly equidistant; keep the minimum per source row.
    nearest_m = joined.groupby(level=0)["distance_m"].min()
    nearest_m = nearest_m.reindex(range(len(source_proj)))
    return (nearest_m.to_numpy() / 1000.0)
