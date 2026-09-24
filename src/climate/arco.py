"""Radiación ERA5-Land desde el Zarr ARCO usado por el dataset Time-Series.

Lee bloques espaciales completos a través del tiempo. Cada bloque se resume
en memoria a totales mensuales y se guarda en una caché pequeña para reanudar.
"""

from __future__ import annotations

import calendar
import logging
import os
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from src.climate.records import CellPoint, SolarRadiationRecord
from src.config.settings import Settings

logger = logging.getLogger(__name__)

# URL oficial ARCO para radiación/calor ERA5-Land, versión geo-chunked.
ARCO_SSRD_URL = (
    "https://arco.datastores.ecmwf.int/cadl-arco-geo-010/arco/"
    "reanalysis_era5_land/sfc-radiation-heat/geoChunked.zarr"
)
SOURCE_LABEL = "Copernicus ERA5-Land ARCO Zarr"


class ArcoSolarService:
    def __init__(self, settings: Settings, url: str = ARCO_SSRD_URL):
        self.settings = settings
        self.url = url
        self.cache_dir = settings.paths.arco_cache
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _open(self) -> xr.Dataset:
        if not self.settings.cds_api_key:
            raise RuntimeError("Falta CDS_API_KEY en .env para acceder a ARCO.")
        return xr.open_zarr(
            self.url,
            consolidated=True,
            storage_options={"headers": {"Authorization": f"Bearer {self.settings.cds_api_key}"}},
        )

    def get_monthly_radiation(self, cells: list[CellPoint]) -> list[SolarRadiationRecord]:
        if not cells:
            return []
        periods = self.settings.climate.year_months
        if not periods:
            raise RuntimeError("No hay meses climáticos configurados para consultar.")
        ds = self._open()
        try:
            lat_index = ds.indexes["latitude"]
            lon_index = ds.indexes["longitude"]
            lat_chunk = ds.ssrd.chunks[1][0]
            lon_chunk = ds.ssrd.chunks[2][0]
            blocks: dict[tuple[int, int], list[tuple[CellPoint, int, int]]] = defaultdict(list)
            for cell in cells:
                i = int(lat_index.get_indexer([cell.latitude], method="nearest")[0])
                j = int(lon_index.get_indexer([cell.longitude], method="nearest")[0])
                blocks[(i // lat_chunk, j // lon_chunk)].append((cell, i, j))

            logger.info(
                "ARCO: %d celdas, %d bloques espaciales, %d meses seleccionados",
                len(cells), len(blocks), len(periods),
            )
            records: list[SolarRadiationRecord] = []
            for number, (block, members) in enumerate(blocks.items(), 1):
                try:
                    monthly, counts, retrieved_at = self._load_or_fetch_block(
                        ds, block, lat_chunk, lon_chunk, periods
                    )
                except Exception as exc:
                    raise RuntimeError(f"No se pudo leer el bloque ARCO {block}: {exc}") from exc
                for cell, i, j in members:
                    lat = float(lat_index[i])
                    lon = float(lon_index[j])
                    for year, month in periods:
                        code = year * 100 + month
                        hours = calendar.monthrange(year, month)[1] * 24
                        used = int(counts[code][i % lat_chunk, j % lon_chunk])
                        if used < hours * 0.95:
                            raise RuntimeError(
                                f"Cobertura ARCO insuficiente para {year}-{month:02d} "
                                f"en ({lat}, {lon}): {used}/{hours} horas."
                            )
                        records.append(SolarRadiationRecord(
                            grid_cell_id=cell.grid_cell_id,
                            year=year,
                            month=month,
                            era5_latitude=lat,
                            era5_longitude=lon,
                            radiation_kwh_m2=float(monthly[code][i % lat_chunk, j % lon_chunk]),
                            source=SOURCE_LABEL,
                            download_timestamp=retrieved_at,
                        ))
                logger.info("ARCO: bloque %d/%d completado", number, len(blocks))
            return records
        finally:
            ds.close()

    def _load_or_fetch_block(
        self,
        ds: xr.Dataset,
        block: tuple[int, int],
        lat_chunk: int,
        lon_chunk: int,
        periods: list[tuple[int, int]],
    ) -> tuple[dict[int, np.ndarray], dict[int, np.ndarray], datetime]:
        path = self.cache_dir / f"ssrd_lat{block[0]}_lon{block[1]}.npz"
        monthly: dict[int, np.ndarray] = {}
        counts: dict[int, np.ndarray] = {}
        retrieved_at = datetime.now(timezone.utc)
        if path.exists():
            with np.load(path, allow_pickle=False) as saved:
                codes = saved["periods"].astype(int).tolist()
                monthly = dict(zip(codes, saved["monthly"]))
                counts = dict(zip(codes, saved["counts"]))
                retrieved_at = datetime.fromisoformat(str(saved["retrieved_at"].item()))

        missing = [(year, month) for year, month in periods if year * 100 + month not in monthly]
        if missing:
            first_year, first_month = missing[0]
            last_year, last_month = missing[-1]
            last_day = calendar.monthrange(last_year, last_month)[1]
            lat_start = block[0] * lat_chunk
            lon_start = block[1] * lon_chunk
            selected = ds.ssrd.isel(
                latitude=slice(lat_start, lat_start + lat_chunk),
                longitude=slice(lon_start, lon_start + lon_chunk),
            ).sel(time=slice(
                f"{first_year}-{first_month:02d}-01",
                f"{last_year}-{last_month:02d}-{last_day:02d}T23:00:00",
            ))
            logger.info("ARCO: leyendo bloque %s, %s a %s", block, missing[0], missing[-1])
            data = selected.to_numpy()
            times = pd.DatetimeIndex(selected.time.values)
            time_codes = times.year.to_numpy() * 100 + times.month.to_numpy()
            for year, month in missing:
                code = year * 100 + month
                values = data[time_codes == code]
                counts[code] = np.isfinite(values).sum(axis=0).astype(np.int16)
                monthly[code] = (np.nansum(values, axis=0, dtype=np.float64) / 3.6e6).astype(np.float32)
            retrieved_at = datetime.now(timezone.utc)
            self._save_block(path, monthly, counts, retrieved_at)
        return monthly, counts, retrieved_at

    @staticmethod
    def _save_block(
        path: Path,
        monthly: dict[int, np.ndarray],
        counts: dict[int, np.ndarray],
        retrieved_at: datetime,
    ) -> None:
        periods = sorted(monthly)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".npz", delete=False) as temp:
                temp_path = Path(temp.name)
                np.savez_compressed(
                    temp,
                    periods=np.array(periods, dtype=np.int32),
                    monthly=np.stack([monthly[code] for code in periods]),
                    counts=np.stack([counts[code] for code in periods]),
                    retrieved_at=retrieved_at.isoformat(),
                )
            os.replace(temp_path, path)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
