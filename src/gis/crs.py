"""Helpers de selección de CRS.

El proyecto nunca debe hardcodear un código EPSG para una región — el
límite de una provincia cambia, y también cambia el CRS proyectado
"correcto" para ella. En cambio, le pedimos a una librería geoespacial
que derive un CRS proyectado apropiado a partir de la geometría real, vía
`estimate_utm_crs()` de GeoPandas/pyproj. Esto elige la zona UTM (y el
hemisferio) que contiene el centroide de la geometría — una elección
apropiada y bien definida de CRS proyectado en metros para cualquier
provincia argentina sin mantener una tabla de referencia.
"""

from __future__ import annotations

import geopandas as gpd
from pyproj import CRS

GEOGRAPHIC_CRS = "EPSG:4326"  # WGS84, usado solo para intercambio de datos de origen


def estimate_projected_crs(geodataframe: gpd.GeoDataFrame) -> CRS:
    """Estima un CRS métrico y proyectado apropiado para `geodataframe`.

    La entrada debe tener su CRS seteado. Las distancias/áreas NUNCA deben
    calcularse sobre un CRS geográfico (lat/lon) — siempre reproyectar
    primero al CRS devuelto acá.
    """
    if geodataframe.crs is None:
        raise ValueError("geodataframe.crs is not set; cannot estimate a projected CRS from it.")
    utm_crs = geodataframe.estimate_utm_crs()
    return CRS.from_user_input(utm_crs)


def to_projected(geodataframe: gpd.GeoDataFrame, projected_crs: CRS) -> gpd.GeoDataFrame:
    """Reproyecta `geodataframe` a `projected_crs` (no hace nada si ya está en ese CRS)."""
    if geodataframe.crs is None:
        raise ValueError("geodataframe.crs is not set; cannot reproject.")
    if CRS.from_user_input(geodataframe.crs) == CRS.from_user_input(projected_crs):
        return geodataframe
    return geodataframe.to_crs(projected_crs)


def to_geographic(geodataframe: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Reproyecta `geodataframe` de vuelta a WGS84 (EPSG:4326) para
    guardar/exportar columnas de latitud/longitud y para mostrar en el mapa web."""
    return geodataframe.to_crs(GEOGRAPHIC_CRS)
