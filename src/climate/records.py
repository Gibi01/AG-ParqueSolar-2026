"""Tipos compartidos para asociar celdas con radiación ERA5-Land."""

from dataclasses import dataclass
from datetime import datetime


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
    download_timestamp: datetime
