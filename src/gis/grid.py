"""Construcción de la grilla de análisis.

Construye una grilla cuadrada configurable de resolution_km x
resolution_km sobre el límite de la región, siguiendo el procedimiento
exigido por los requisitos: proyectar a un CRS métrico, teselar en
metros, recortar al límite, asignar IDs y centroides. Esta grilla es una
unidad de discretización espacial para el problema de optimización — es
independiente de, y más gruesa/fina que, la resolución nativa de
cualquier fuente de datos climáticos en particular (ver
src/climate/arco.py para cómo los puntos de ~9km de ERA5-Land se
asocian a estas celdas de optimización de 500 m).
"""

from __future__ import annotations

from dataclasses import dataclass

import geopandas as gpd
import numpy as np
from pyproj import CRS
from shapely.geometry import box
import shapely

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

    rows, columns = np.meshgrid(np.arange(len(ys) - 1), np.arange(len(xs) - 1), indexing="ij")
    rows, columns = rows.ravel(), columns.ravel()
    squares = shapely.box(xs[columns], ys[rows], xs[columns] + cell_size_m, ys[rows] + cell_size_m)
    candidate_grid = gpd.GeoDataFrame({"row": rows, "column": columns}, geometry=squares, crs=projected_crs)

    shapely.prepare(region_geom)
    intersects_mask = shapely.intersects(region_geom, squares)
    clipped = candidate_grid.loc[intersects_mask].copy()
    # Interior squares need no intersection with the complex provincial boundary.
    partial = ~shapely.contains_properly(region_geom, clipped.geometry.to_numpy())
    clipped.loc[partial, 'geometry'] = clipped.loc[partial].geometry.intersection(region_geom)
    clipped = clipped.explode(index_parts=False).reset_index(drop=True)
    clipped = clipped.loc[(clipped.geometry.geom_type == "Polygon") & (clipped.geometry.area > 0)].copy()
    # Only split squares require geometry-based component ordering.
    split = clipped.duplicated(['row', 'column'], keep=False)
    order = sorted(clipped.index[split], key=lambda i: (
        clipped.at[i, 'row'], clipped.at[i, 'column'], tuple(clipped.at[i, 'geometry'].bounds),
        clipped.at[i, 'geometry'].normalize().wkb_hex))
    clipped['_order'] = 0
    clipped.loc[order, '_order'] = np.arange(len(order))
    clipped = clipped.sort_values(["row", "column", "_order"]).drop(columns="_order").reset_index(drop=True)
    clipped["component"] = clipped.groupby(["row", "column"]).cumcount()

    clipped.insert(0, "cell_id", np.arange(1, len(clipped) + 1))
    clipped["cell_area_m2"] = clipped.geometry.area

    centroids_proj = clipped.geometry.centroid
    clipped["centroid_x_m"] = centroids_proj.x
    clipped["centroid_y_m"] = centroids_proj.y

    centroids_geo = gpd.GeoSeries(centroids_proj.values, crs=projected_crs).to_crs(GEOGRAPHIC_CRS)
    clipped["latitude"] = centroids_geo.y.values
    clipped["longitude"] = centroids_geo.x.values

    return Grid(gdf=clipped, projected_crs=projected_crs)


def build_neighbors(grid: gpd.GeoDataFrame) -> dict[int, tuple[int, ...]]:
    """Precompute symmetric edge adjacency. Corners and excluded cells never connect."""
    ids = grid.cell_id.to_numpy()
    geometries = grid.geometry.to_numpy()
    neighbors = {int(cell_id): [] for cell_id in ids}
    tree = shapely.STRtree(geometries)
    # Batches bound the spatial query's memory on the provincial 500 m grid.
    for start in range(0, len(grid), 10000):
        left, right = tree.query(geometries[start:start + 10000], predicate="touches")
        left = left + start
        mask = left < right
        left, right = left[mask], right[mask]
        lengths = shapely.length(shapely.intersection(
            shapely.boundary(geometries[left]), shapely.boundary(geometries[right])))
        for a, b in zip(left[lengths > 0], right[lengths > 0]):
            neighbors[int(ids[a])].append(int(ids[b]))
            neighbors[int(ids[b])].append(int(ids[a]))
    return {key: tuple(sorted(values)) for key, values in neighbors.items()}
