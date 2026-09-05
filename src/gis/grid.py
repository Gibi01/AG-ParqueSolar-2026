"""Construcción de la grilla de análisis.

Construye una grilla cuadrada configurable de resolution_km x
resolution_km sobre el límite de la región, siguiendo el procedimiento
exigido por los requisitos: proyectar a un CRS métrico, teselar en
metros, recortar al límite, asignar IDs y centroides. Esta grilla es una
unidad de discretización espacial para el problema de optimización — es
independiente de, y más gruesa/fina que, la resolución nativa de
cualquier fuente de datos climáticos en particular (ver
src/climate/era5_land.py para cómo los puntos de ~9km de ERA5-Land se
asocian a estas celdas de 5km).
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
    """Construye la grilla de análisis, recortada a `region_boundary`.

    Pasos (según los requisitos del proyecto, Fase 13):
    1. Determinar un CRS proyectado apropiado si no se da uno (vía
       `estimate_utm_crs`, nunca un EPSG hardcodeado).
    2. Reproyectar el límite a ese CRS.
    3. Tesselar el bounding box del límite en cuadrados de
       resolution_km x resolution_km.
    4. Intersectar cada cuadrado con el límite (las celdas parcialmente
       fuera de la región se recortan, no se descartan, pero las celdas
       con intersección totalmente vacía se eliminan).
    5. Asignar un cell_id único y calcular centroides (tanto en el CRS
       proyectado, en metros, como reproyectados de vuelta a lat/lon
       WGS84 para almacenamiento/trazabilidad).
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
