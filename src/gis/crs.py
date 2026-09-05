"""CRS selection helpers.

The project must never hardcode an EPSG code for a region — a province
boundary changes, and so does the "right" projected CRS for it. Instead
we ask a geospatial library to derive an appropriate projected CRS from
the actual geometry, via GeoPandas/pyproj's `estimate_utm_crs()`. This
picks the UTM zone (and hemisphere) that contains the geometry's
centroid — an appropriate, well-defined choice of projected CRS in
metres for any Argentine province without maintaining a lookup table.
"""

from __future__ import annotations

import geopandas as gpd
from pyproj import CRS

GEOGRAPHIC_CRS = "EPSG:4326"  # WGS84, used for source data exchange only


def estimate_projected_crs(geodataframe: gpd.GeoDataFrame) -> CRS:
    """Estimate a metric, projected CRS appropriate for `geodataframe`.

    The input must have its CRS set. Distances/areas must NEVER be
    computed on a geographic (lat/lon) CRS — always reproject into the
    CRS returned here first.
    """
    if geodataframe.crs is None:
        raise ValueError("geodataframe.crs is not set; cannot estimate a projected CRS from it.")
    utm_crs = geodataframe.estimate_utm_crs()
    return CRS.from_user_input(utm_crs)


def to_projected(geodataframe: gpd.GeoDataFrame, projected_crs: CRS) -> gpd.GeoDataFrame:
    """Reproject `geodataframe` into `projected_crs` (a no-op if already there)."""
    if geodataframe.crs is None:
        raise ValueError("geodataframe.crs is not set; cannot reproject.")
    if CRS.from_user_input(geodataframe.crs) == CRS.from_user_input(projected_crs):
        return geodataframe
    return geodataframe.to_crs(projected_crs)


def to_geographic(geodataframe: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Reproject `geodataframe` back to WGS84 (EPSG:4326) for storage/export
    of latitude/longitude columns and for web-map display."""
    return geodataframe.to_crs(GEOGRAPHIC_CRS)
