"""Analysis grid construction.

Builds a configurable resolution_km x resolution_km square grid over the
region boundary, following the procedure mandated by the requirements:
project to a metric CRS, tile in metres, clip to the boundary, assign
IDs and centroids. This grid is a spatial discretisation unit for the
optimization problem — it is independent of, and coarser/finer than,
any single climate data source's native resolution (see
src/climate/era5_land.py for how ERA5-Land's ~9km points get associated
to these 5km cells).
"""

from __future__ import annotations

from dataclasses import dataclass

import geopandas as gpd
import numpy as np
from pyproj import CRS
from shapely.geometry import box

from src.gis.crs import GEOGRAPHIC_CRS, estimate_projected_crs, to_projected


@dataclass
class Grid:
    gdf: gpd.GeoDataFrame
    projected_crs: CRS


def build_grid(
    region_boundary: gpd.GeoDataFrame,
    resolution_km: float,
    projected_crs: CRS | None = None,
) -> Grid:
    """Build the analysis grid, clipped to `region_boundary`.

    Steps (per project requirements, Fase 13):
    1. Determine an appropriate projected CRS if not given (via
       `estimate_utm_crs`, never a hardcoded EPSG).
    2. Reproject the boundary into that CRS.
    3. Tile the boundary's bounding box into resolution_km x resolution_km
       squares.
    4. Intersect each square with the boundary (cells partially outside
       the region are clipped, not discarded, but cells with fully empty
       intersection are dropped).
    5. Assign a unique cell_id and compute centroids (both in the
       projected CRS, in metres, and reprojected back to WGS84 lat/lon
       for storage/traceability).
    """
    if projected_crs is None:
        projected_crs = estimate_projected_crs(region_boundary)

    boundary_proj = to_projected(region_boundary, projected_crs)
    region_geom = boundary_proj.geometry.union_all()

    minx, miny, maxx, maxy = region_geom.bounds
    cell_size_m = resolution_km * 1000.0

    xs = np.arange(minx, maxx + cell_size_m, cell_size_m)
    ys = np.arange(miny, maxy + cell_size_m, cell_size_m)

    squares = [
        box(x0, y0, x0 + cell_size_m, y0 + cell_size_m)
        for x0 in xs[:-1]
        for y0 in ys[:-1]
    ]
    candidate_grid = gpd.GeoDataFrame({"geometry": squares}, crs=projected_crs)

    intersects_mask = candidate_grid.intersects(region_geom)
    clipped = candidate_grid.loc[intersects_mask].copy()
    clipped["geometry"] = clipped.geometry.intersection(region_geom)
    clipped = clipped.loc[~clipped.geometry.is_empty].reset_index(drop=True)

    clipped.insert(0, "cell_id", np.arange(1, len(clipped) + 1))
    clipped["cell_area_m2"] = clipped.geometry.area

    centroids_proj = clipped.geometry.centroid
    clipped["centroid_x_m"] = centroids_proj.x
    clipped["centroid_y_m"] = centroids_proj.y

    centroids_geo = gpd.GeoSeries(centroids_proj.values, crs=projected_crs).to_crs(GEOGRAPHIC_CRS)
    clipped["latitude"] = centroids_geo.y.values
    clipped["longitude"] = centroids_geo.x.values

    return Grid(gdf=clipped, projected_crs=projected_crs)
