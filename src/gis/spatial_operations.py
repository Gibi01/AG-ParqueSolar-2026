"""Operaciones espaciales sobre capas: buffers y máscaras de exclusión.

`urban_exclusion_mask` implementa el requisito estricto de que cualquier
celda de grilla que intersecte una zona urbana quede EXCLUIDA por
completo — nunca simplemente penalizada en el fitness.
"""

from __future__ import annotations

from pyproj import CRS

import geopandas as gpd
import pandas as pd

from src.gis.crs import to_projected


def buffer_points_km(points_gdf: gpd.GeoDataFrame, buffer_km: float, projected_crs: CRS) -> gpd.GeoDataFrame:
    """Bufferiza geometrías de punto por `buffer_km` en un CRS métrico.

    Se usa para aproximar una huella urbana a partir de las localidades
    de solo-puntos de BAHRA (ver README para por qué esto es una
    aproximación, y cómo reemplazarla una vez que haya disponible una
    capa real de polígonos urbanos).
    """
    proj = to_projected(points_gdf, projected_crs).copy()
    proj["geometry"] = proj.geometry.buffer(buffer_km * 1000.0)
    return proj


def urban_exclusion_mask(grid_gdf: gpd.GeoDataFrame, urban_polygons_proj: gpd.GeoDataFrame) -> pd.Series:
    """Devuelve una Serie booleana (alineada con el índice de grid_gdf) que
    es True para las celdas que intersectan CUALQUIER polígono urbano
    (bufferizado) — a excluir.

    Ambas entradas ya deben compartir el mismo CRS proyectado.
    """
    if len(urban_polygons_proj) == 0:
        return pd.Series(False, index=grid_gdf.index)
    urban_union = urban_polygons_proj.geometry.union_all()
    return grid_gdf.geometry.intersects(urban_union)
