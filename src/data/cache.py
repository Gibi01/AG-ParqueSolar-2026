"""Caché en disco.

Acá viven dos cachés independientes:

- `RawLayerCache`: caché genérica para capas vectoriales completas
  ingeridas desde una API (límite de región, zonas urbanas, líneas
  eléctricas, transformadores). Indexada por un nombre de archivo; guarda
  el GeoDataFrame como GeoPackage más un sidecar JSON con metadata de
  trazabilidad de la fuente. Volver a correr el paso de ETL es entonces
  un no-op salvo que se pase `force=True`.

- `Era5LandCache`: la caché de puntos de ERA5-Land requerida por el
  proyecto ("era5_land_cache/"). La grilla de ~9 km de ERA5-Land es más
  gruesa que nuestra grilla de análisis de 5 km, así que varias celdas
  de grilla legítimamente mapean al MISMO punto de ERA5-Land. Esta caché
  se indexa por (variable, year, month, era5_latitude, era5_longitude)
  — es decir, por el punto de ERA5-Land realmente usado — de modo que
  cuando dos celdas comparten un punto, la segunda se sirve desde disco
  en vez de volver a consultar la API de CDS.
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
    """Caché respaldada por archivos que mapea una clave
    (variable, year, month, punto ERA5-Land) a su serie horaria, de modo
    que las celdas de grilla que comparten un punto de ERA5-Land nunca
    disparen una segunda descarga de CDS para el mismo período."""

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
