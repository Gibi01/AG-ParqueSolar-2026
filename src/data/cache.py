"""Caché en disco para capas vectoriales ingeridas desde fuentes externas."""

from __future__ import annotations

import json
import hashlib
import re
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import geopandas as gpd


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


def layer_cache_for_settings(settings: Any) -> RawLayerCache:
    """Aísla capas recortadas por provincia y fuentes, sin mezclar corridas."""
    scope = {
        "region": settings.region.model_dump(),
        "infrastructure": settings.infrastructure.model_dump(),
    }
    digest = hashlib.sha256(json.dumps(scope, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    code = re.sub(r"[^A-Za-z0-9_-]", "_", settings.region.admin_source.code_value)
    return RawLayerCache(settings.paths.data_raw / "layers" / f"{code}-{digest}")


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
