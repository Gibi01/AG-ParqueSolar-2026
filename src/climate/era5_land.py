"""Associates grid cells with ERA5-Land points and orchestrates retrieval.

ERA5-Land's native grid (~9 km / 0.1°) is coarser than the project's
analysis grid (5 km by default), so many grid cells legitimately share
the same ERA5-Land point. This module:

1. Predicts, for each cell centroid, the nearest point on ERA5-Land's
   regular 0.1° x 0.1° grid (`predict_nearest_era5_grid_point`) — used
   purely to GROUP cells before querying, so the CDS API and the local
   `Era5LandCache` are hit once per unique point x year x month, never
   once per cell. The CDS service performs its own authoritative
   nearest-neighbour selection server-side; this local prediction is
   only a deduplication heuristic.
2. For each unique (point, year, month), serves the request from
   `Era5LandCache` if present, otherwise calls
   `CopernicusEra5LandClient.fetch_point_hourly` and aggregates the
   returned hourly series to a monthly kWh/m^2 figure
   (`src/climate/radiation.py`).
3. Returns one row per (grid_cell_id, year, month) with full traceability
   (era5_latitude/era5_longitude actually confirmed by CDS, source,
   download timestamp) — ready for `solar_radiation` table storage.

No interpolation is performed, matching the dataset's own documented
nearest-neighbour methodology; interpolation could be added later as a
separate strategy without touching the association/caching logic above.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from datetime import datetime as dt
from typing import Optional

from src.api.copernicus_era5_land import CopernicusEra5LandClient, Era5PointRequest
from src.climate.radiation import aggregate_monthly_kwh_m2
from src.config.settings import Settings
from src.data.cache import Era5CacheKey, Era5LandCache

logger = logging.getLogger(__name__)

ERA5_LAND_GRID_SPACING_DEG = 0.1
SOURCE_LABEL = "CDS reanalysis-era5-land-timeseries"


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
    """Round (lat, lon) to the nearest point of ERA5-Land's regular 0.1°
    grid. This is a local prediction used only to deduplicate requests
    across cells — the value actually stored for each cell always comes
    from the CDS response (see `SolarRadiationRecord.era5_latitude/longitude`).
    """
    lat_r = round(round(lat / ERA5_LAND_GRID_SPACING_DEG) * ERA5_LAND_GRID_SPACING_DEG, 1)
    lon_r = round(round(lon / ERA5_LAND_GRID_SPACING_DEG) * ERA5_LAND_GRID_SPACING_DEG, 1)
    return lat_r, lon_r


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
        years = self.settings.climate.years
        months = self.settings.climate.months
        epsilon = self.settings.climate.point_bbox_epsilon_deg

        groups: dict[tuple[float, float], list[int]] = defaultdict(list)
        for cell in cells:
            key = predict_nearest_era5_grid_point(cell.latitude, cell.longitude)
            groups[key].append(cell.grid_cell_id)

        logger.info(
            "ERA5-Land association: %d grid cells -> %d unique ERA5-Land points "
            "(%.1fx dedup factor)",
            len(cells),
            len(groups),
            len(cells) / max(len(groups), 1),
        )

        records: list[SolarRadiationRecord] = []
        for (point_lat, point_lon), cell_ids in groups.items():
            for year in years:
                for month in months:
                    era5_lat, era5_lon, radiation_kwh_m2, downloaded_at = self._get_or_fetch_month(
                        variable, point_lat, point_lon, year, month, epsilon
                    )
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

    def _get_or_fetch_month(
        self,
        variable: str,
        point_lat: float,
        point_lon: float,
        year: int,
        month: int,
        epsilon: float,
    ) -> tuple[float, float, float, dt]:
        cache_key = Era5CacheKey(
            variable=variable, year=year, month=month, era5_latitude=point_lat, era5_longitude=point_lon
        )
        cached = self.cache.get(cache_key)
        if cached is not None:
            hourly_df, metadata = cached
            agg = aggregate_monthly_kwh_m2(hourly_df.rename(columns={"value": "value"}), year, month)
            return (
                metadata["era5_latitude"],
                metadata["era5_longitude"],
                agg.radiation_kwh_m2,
                dt.fromisoformat(metadata["download_timestamp"]),
            )

        first_day = date(year, month, 1)
        last_day = date(year, month, _days_in_month(year, month))
        request = Era5PointRequest(
            variable=variable,
            latitude=point_lat,
            longitude=point_lon,
            start_date=first_day,
            end_date=last_day,
            bbox_epsilon_deg=epsilon,
        )
        response = self.client.fetch_point_hourly(request)
        agg = aggregate_monthly_kwh_m2(response.hourly, year, month)

        if not agg.is_plausible:
            logger.warning(
                "Monthly radiation %.2f kWh/m^2 for %s-%02d at (%.4f, %.4f) "
                "is outside the plausibility range configured in "
                "src/climate/radiation.py — verify the de-accumulation "
                "assumption against the raw response at %s.",
                agg.radiation_kwh_m2,
                year,
                month,
                response.era5_latitude,
                response.era5_longitude,
                response.raw_file_path,
            )

        metadata = {
            "variable": variable,
            "requested_latitude": point_lat,
            "requested_longitude": point_lon,
            "era5_latitude": response.era5_latitude,
            "era5_longitude": response.era5_longitude,
            "year": year,
            "month": month,
            "source": SOURCE_LABEL,
            "raw_file_path": str(response.raw_file_path),
            "download_timestamp": response.retrieved_at.isoformat(),
            "spatial_selection_method": "nearest_neighbour (server-side, CDS-documented)",
            "n_hours_used": agg.n_hours_used,
            "n_hours_expected": agg.n_hours_expected,
            "is_plausible": agg.is_plausible,
        }
        self.cache.put(cache_key, response.hourly, metadata)

        return response.era5_latitude, response.era5_longitude, agg.radiation_kwh_m2, response.retrieved_at


def _days_in_month(year: int, month: int) -> int:
    import calendar

    return calendar.monthrange(year, month)[1]
