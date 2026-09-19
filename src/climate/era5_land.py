"""Asocia celdas de grilla con puntos de ERA5-Land y orquesta la obtención de datos.

La grilla nativa de ERA5-Land (~9 km / 0.1°) es más gruesa que la grilla
de análisis del proyecto (5 km por defecto), así que muchas celdas de
grilla legítimamente comparten el mismo punto de ERA5-Land. Este módulo:

1. Predice, para cada centroide de celda, el punto más cercano en la
   grilla regular de 0.1° x 0.1° de ERA5-Land
   (`predict_nearest_era5_grid_point`) — usado puramente para AGRUPAR
   celdas antes de consultar, de modo que la API de CDS y la
   `Era5LandCache` local se golpeen una vez por cada punto x año x mes
   único, nunca una vez por celda. El servicio de CDS hace su propia
   selección autoritativa de vecino más cercano en el servidor; esta
   predicción local es solo una heurística de deduplicación.
2. Agrupa esos puntos únicos en tiles geográficos de
   `climate.area_tile_size_deg` grados de lado (`tile_for_point`), y
   pide cada tile completo en UNA sola solicitud de área a
   `CopernicusEra5LandClient.fetch_area_hourly` — en vez de una
   solicitud HTTP por punto. Esto es lo que hace viable descargar miles
   de puntos: pedir uno por uno significa decenas de horas de espera en
   cola en el servidor de CDS; agrupados en tiles (0.3° por defecto,
   acotado por un límite de costo de CDS no documentado — ver
   src/api/copernicus_era5_land.py), la misma cantidad de puntos se
   cubre en varios cientos de solicitudes en vez de miles.
3. Para cada (punto, año, mes) único, sirve el dato desde
   `Era5LandCache` si ya está cacheado — de modo que un tile solo se
   vuelve a pedir si le falta al menos un punto — y agrega la serie
   horaria a una cifra mensual de kWh/m^2 (`src/climate/radiation.py`).
4. Devuelve una fila por (grid_cell_id, year, month) con trazabilidad
   completa (era5_latitude/era5_longitude realmente confirmados por CDS,
   fuente, timestamp de descarga) — lista para guardarse en la tabla
   `solar_radiation`.

La clave de caché sigue siendo (variable, year, month, era5_latitude,
era5_longitude) usando el punto PREDICHO localmente — igual que antes de
introducir el modo área — así que una caché ya poblada con el modo
punto-por-punto sigue siendo válida sin cambios.

No se realiza interpolación, siguiendo la metodología de vecino más
cercano documentada por el propio dataset; la interpolación podría
agregarse a futuro como una estrategia separada sin tocar la lógica de
asociación/caché de arriba.
"""

from __future__ import annotations

import logging
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from datetime import datetime as dt
from typing import Optional

from src.api.copernicus_era5_land import CopernicusEra5LandClient, Era5AreaRequest
from src.climate.radiation import aggregate_monthly_kwh_m2
from src.config.settings import Settings
from src.data.cache import Era5CacheKey, Era5LandCache

logger = logging.getLogger(__name__)

ERA5_LAND_GRID_SPACING_DEG = 0.1
SOURCE_LABEL = "CDS reanalysis-era5-land-timeseries"

# Margen de seguridad agregado a cada lado de un tile antes de pedirlo,
# para no dejar afuera por error de redondeo un punto que cae justo en el
# borde. Con el valor por defecto (area_tile_size_deg=0.3) el tile
# efectivo pedido es 0.38° de lado — bien por debajo tanto del máximo
# geográfico documentado por CDS (1.0°) como del límite de costo real
# calibrado empíricamente (ver src/api/copernicus_era5_land.py).
AREA_TILE_MARGIN_DEG = 0.04


@dataclass(frozen=True)
class CellPoint:
    grid_cell_id: int
    latitude: float
    longitude: float


@dataclass
class SolarRadiationRecord:
    grid_cell_id: int
    year: int
    month: int
    era5_latitude: float
    era5_longitude: float
    radiation_kwh_m2: float
    source: str
    download_timestamp: dt


def predict_nearest_era5_grid_point(lat: float, lon: float) -> tuple[float, float]:
    """Redondea (lat, lon) al punto más cercano de la grilla regular de
    0.1° de ERA5-Land. Esta es una predicción local usada solo para
    deduplicar solicitudes entre celdas — el valor realmente guardado
    para cada celda siempre viene de la respuesta de CDS (ver
    `SolarRadiationRecord.era5_latitude/longitude`).
    """
    lat_r = round(round(lat / ERA5_LAND_GRID_SPACING_DEG) * ERA5_LAND_GRID_SPACING_DEG, 1)
    lon_r = round(round(lon / ERA5_LAND_GRID_SPACING_DEG) * ERA5_LAND_GRID_SPACING_DEG, 1)
    return lat_r, lon_r


def tile_for_point(lat: float, lon: float, tile_size_deg: float) -> tuple[float, float]:
    """Devuelve la esquina suroeste del tile de `tile_size_deg` grados de
    lado que contiene a (lat, lon), alineado a una grilla que arranca en
    0.0° (piso de lat/tile_size, piso de lon/tile_size). Todos los
    puntos que caen en el mismo tile se piden juntos en una sola
    solicitud de área.
    """
    tile_lat = math.floor(lat / tile_size_deg) * tile_size_deg
    tile_lon = math.floor(lon / tile_size_deg) * tile_size_deg
    return round(tile_lat, 6), round(tile_lon, 6)


class Era5LandRadiationService:
    def __init__(
        self,
        settings: Settings,
        client: Optional[CopernicusEra5LandClient] = None,
        cache: Optional[Era5LandCache] = None,
    ):
        self.settings = settings
        self.client = client or CopernicusEra5LandClient(
            api_key=settings.cds_api_key,
            api_url=settings.cds_api_url,
            raw_download_dir=settings.paths.data_raw / "era5_downloads",
        )
        self.cache = cache or Era5LandCache(settings.paths.era5_cache)

    def get_monthly_radiation(self, cells: list[CellPoint]) -> list[SolarRadiationRecord]:
        variable = self.settings.climate.variable
        year_months = self.settings.climate.year_months
        tile_size = self.settings.climate.area_tile_size_deg

        point_to_cells: dict[tuple[float, float], list[int]] = defaultdict(list)
        for cell in cells:
            point = predict_nearest_era5_grid_point(cell.latitude, cell.longitude)
            point_to_cells[point].append(cell.grid_cell_id)

        unique_points = list(point_to_cells.keys())
        logger.info(
            "ERA5-Land association: %d grid cells -> %d unique ERA5-Land points "
            "(%.1fx dedup factor)",
            len(cells),
            len(unique_points),
            len(cells) / max(len(unique_points), 1),
        )

        tile_to_points: dict[tuple[float, float], list[tuple[float, float]]] = defaultdict(list)
        for point in unique_points:
            tile = tile_for_point(point[0], point[1], tile_size)
            tile_to_points[tile].append(point)

        logger.info(
            "%d puntos ERA5 únicos agrupados en %d tiles de %.2f° (%.1f puntos/tile en promedio)",
            len(unique_points),
            len(tile_to_points),
            tile_size,
            len(unique_points) / max(len(tile_to_points), 1),
        )
        logger.info(
            "Estimación máxima de solicitudes CDS sin caché: %d tiles x %d meses = %d",
            len(tile_to_points),
            len(year_months),
            len(tile_to_points) * len(year_months),
        )

        records: list[SolarRadiationRecord] = []
        for year, month in year_months:
            point_results = self._get_or_fetch_month_for_all_tiles(
                variable, tile_to_points, tile_size, year, month
            )
            for point, cell_ids in point_to_cells.items():
                era5_lat, era5_lon, radiation_kwh_m2, downloaded_at = point_results[point]
                for cell_id in cell_ids:
                    records.append(
                        SolarRadiationRecord(
                            grid_cell_id=cell_id,
                            year=year,
                            month=month,
                            era5_latitude=era5_lat,
                            era5_longitude=era5_lon,
                            radiation_kwh_m2=radiation_kwh_m2,
                            source=SOURCE_LABEL,
                            download_timestamp=downloaded_at,
                        )
                    )
        return records

    def _get_or_fetch_month_for_all_tiles(
        self,
        variable: str,
        tile_to_points: dict[tuple[float, float], list[tuple[float, float]]],
        tile_size: float,
        year: int,
        month: int,
    ) -> dict[tuple[float, float], tuple[float, float, float, dt]]:
        """Resuelve, para un (variable, year, month) dado, el resultado de
        cada punto único de todos los tiles — sirviendo desde caché lo que
        ya esté, y pidiendo UN área por tile para lo que falte."""
        results: dict[tuple[float, float], tuple[float, float, float, dt]] = {}

        for tile, points_in_tile in tile_to_points.items():
            missing_points: list[tuple[float, float]] = []
            for point in points_in_tile:
                cache_key = Era5CacheKey(
                    variable=variable, year=year, month=month, era5_latitude=point[0], era5_longitude=point[1]
                )
                cached = self.cache.get(cache_key)
                if cached is not None:
                    hourly_df, metadata = cached
                    agg = aggregate_monthly_kwh_m2(hourly_df, year, month)
                    results[point] = (
                        metadata["era5_latitude"],
                        metadata["era5_longitude"],
                        agg.radiation_kwh_m2,
                        dt.fromisoformat(metadata["download_timestamp"]),
                    )
                else:
                    missing_points.append(point)

            if not missing_points:
                continue

            self._fetch_tile_and_fill(variable, tile, tile_size, missing_points, year, month, results)

        return results

    def _fetch_tile_and_fill(
        self,
        variable: str,
        tile: tuple[float, float],
        tile_size: float,
        missing_points: list[tuple[float, float]],
        year: int,
        month: int,
        results: dict[tuple[float, float], tuple[float, float, float, dt]],
    ) -> None:
        tile_lat, tile_lon = tile
        first_day = date(year, month, 1)
        last_day = date(year, month, _days_in_month(year, month))
        area_request = Era5AreaRequest(
            variable=variable,
            north=tile_lat + tile_size + AREA_TILE_MARGIN_DEG,
            west=tile_lon - AREA_TILE_MARGIN_DEG,
            south=tile_lat - AREA_TILE_MARGIN_DEG,
            east=tile_lon + tile_size + AREA_TILE_MARGIN_DEG,
            start_date=first_day,
            end_date=last_day,
        )
        area_response = self.client.fetch_area_hourly(area_request)

        if not area_response.points:
            raise RuntimeError(
                f"CDS no devolvió ningún punto ERA5-Land para el tile "
                f"({tile_lat}, {tile_lon}) en {year}-{month:02d} — se esperaban "
                f"{len(missing_points)} punto(s): {missing_points}. Puede que el "
                f"tile caiga fuera de tierra firme (ERA5-Land solo cubre "
                f"continente) o que el tile_size configurado sea demasiado chico."
            )

        for point in missing_points:
            nearest = min(
                area_response.points.keys(),
                key=lambda rp: (rp[0] - point[0]) ** 2 + (rp[1] - point[1]) ** 2,
            )
            hourly_df = area_response.points[nearest]
            agg = aggregate_monthly_kwh_m2(hourly_df, year, month)

            if not agg.is_plausible:
                logger.warning(
                    "Radiación mensual %.2f kWh/m^2 para %s-%02d en (%.4f, %.4f) "
                    "está fuera del rango de plausibilidad configurado en "
                    "src/climate/radiation.py — verificar el supuesto de "
                    "de-acumulación contra la respuesta cruda en %s.",
                    agg.radiation_kwh_m2,
                    year,
                    month,
                    nearest[0],
                    nearest[1],
                    area_response.raw_file_path,
                )

            metadata = {
                "variable": variable,
                "requested_latitude": point[0],
                "requested_longitude": point[1],
                "era5_latitude": nearest[0],
                "era5_longitude": nearest[1],
                "year": year,
                "month": month,
                "source": SOURCE_LABEL,
                "raw_file_path": str(area_response.raw_file_path),
                "download_timestamp": area_response.retrieved_at.isoformat(),
                "spatial_selection_method": "nearest_neighbour (server-side area query, CDS-documented)",
                "n_hours_used": agg.n_hours_used,
                "n_hours_expected": agg.n_hours_expected,
                "is_plausible": agg.is_plausible,
            }
            cache_key = Era5CacheKey(
                variable=variable, year=year, month=month, era5_latitude=point[0], era5_longitude=point[1]
            )
            self.cache.put(cache_key, hourly_df, metadata)

            results[point] = (nearest[0], nearest[1], agg.radiation_kwh_m2, area_response.retrieved_at)


def _days_in_month(year: int, month: int) -> int:
    import calendar

    return calendar.monthrange(year, month)[1]
