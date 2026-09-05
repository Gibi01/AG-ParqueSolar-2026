"""Cálculos de distancia mínima, siempre en un CRS proyectado (métrico).

Nunca calcular distancias físicas sobre grados crudos de lat/lon (un
sqrt((lat1-lat2)^2 + (lon1-lon2)^2) ingenuo no es una distancia real —
los grados de longitud se achican hacia los polos y los dos ejes ni
siquiera tienen la misma longitud). Todo acá opera en metros después de
reproyectar, y devuelve kilómetros.
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
    """Para cada geometría en `source_gdf`, devuelve la distancia (km) a la
    geometría más cercana en `target_gdf`, ambas reproyectadas a `projected_crs`.

    Usa el `sjoin_nearest` de GeoPandas (respaldado por índice espacial)
    en vez de un loop O(n*m), ya que las grillas pueden tener miles de celdas.
    """
    if len(target_gdf) == 0:
        raise ValueError("target_gdf is empty; cannot compute nearest distances.")

    source_proj = to_projected(source_gdf, projected_crs)[["geometry"]].reset_index(drop=True)
    target_proj = to_projected(target_gdf, projected_crs)[["geometry"]].reset_index(drop=True)

    joined = gpd.sjoin_nearest(source_proj, target_proj, distance_col="distance_m", how="left")
    # sjoin_nearest puede emitir >1 fila por feature de origen cuando varias
    # features de destino están exactamente equidistantes; nos quedamos con
    # el mínimo por fila de origen.
    nearest_m = joined.groupby(level=0)["distance_m"].min()
    nearest_m = nearest_m.reindex(range(len(source_proj)))
    return (nearest_m.to_numpy() / 1000.0)
