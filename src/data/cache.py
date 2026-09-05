"""On-disk caching.

Two independent caches live here:

- `RawLayerCache`: generic cache for whole vector layers ingested from an
  API (region boundary, urban areas, power lines, transformers). Keyed by
  a filename; stores the GeoDataFrame as GeoPackage plus a JSON sidecar
  with source traceability metadata. Re-running the ETL step is then a
  no-op unless `force=True`.

- `Era5LandCache`: the ERA5-Land point cache required by the project
  ("era5_land_cache/"). ERA5-Land's ~9 km grid is coarser than our 5 km
  analysis grid, so multiple grid cells legitimately map to the SAME
  ERA5-Land point. This cache is keyed by (variable, year, month,
  era5_latitude, era5_longitude) — i.e. by the ERA5-Land point actually
  used — so that when two cells share a point, the second one is served
  from disk instead of re-querying the CDS API.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import geopandas as gpd
import pandas as pd


class RawLayerCache:
    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _paths(self, name: str) -> tuple[Path, Path]:
        return self.cache_dir / f"{name}.gpkg", self.cache_dir / f"{name}.meta.json"

    def exists(self, name: str) -> bool:
        gpkg_path, meta_path = self._paths(name)
        return gpkg_path.exists() and meta_path.exists()

    def load(self, name: str) -> tuple[gpd.GeoDataFrame, dict[str, Any]]:
        gpkg_path, meta_path = self._paths(name)
        gdf = gpd.read_file(gpkg_path)
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        return gdf, metadata

    def save(self, name: str, gdf: gpd.GeoDataFrame, metadata: dict[str, Any]) -> None:
        gpkg_path, meta_path = self._paths(name)
        gdf.to_file(gpkg_path, driver="GPKG")
        meta_path.write_text(json.dumps(_json_safe(metadata), indent=2, default=str), encoding="utf-8")


@dataclass(frozen=True)
class Era5CacheKey:
    variable: str
    year: int
    month: int
    era5_latitude: float
    era5_longitude: float

    def filename(self) -> str:
        lat_s = f"{self.era5_latitude:.2f}".replace("-", "m").replace(".", "p")
        lon_s = f"{self.era5_longitude:.2f}".replace("-", "m").replace(".", "p")
        return f"{self.variable}_{self.year}_{self.month:02d}_{lat_s}_{lon_s}"


class Era5LandCache:
    """File-backed cache mapping an (variable, year, month, ERA5-Land point)
    key to its hourly time series, so that grid cells sharing an ERA5-Land
    point never trigger a second CDS download for the same period."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _paths(self, key: Era5CacheKey) -> tuple[Path, Path]:
        base = self.cache_dir / key.filename()
        return base.with_suffix(".csv"), base.with_suffix(".meta.json")

    def get(self, key: Era5CacheKey) -> Optional[tuple[pd.DataFrame, dict[str, Any]]]:
        data_path, meta_path = self._paths(key)
        if not (data_path.exists() and meta_path.exists()):
            return None
        df = pd.read_csv(data_path, parse_dates=["valid_time"])
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        return df, metadata

    def put(self, key: Era5CacheKey, hourly_df: pd.DataFrame, metadata: dict[str, Any]) -> None:
        data_path, meta_path = self._paths(key)
        hourly_df.to_csv(data_path, index=False)
        meta_path.write_text(json.dumps(_json_safe(metadata), indent=2, default=str), encoding="utf-8")


def _json_safe(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return _json_safe(asdict(obj))
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj
