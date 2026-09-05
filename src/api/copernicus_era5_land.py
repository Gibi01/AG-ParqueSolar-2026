"""Official programmatic client for the Copernicus Climate Data Store (CDS),
specifically the "ERA5-Land hourly time-series data from 1950 to present"
(ARCO) dataset — id `reanalysis-era5-land-timeseries`.

Access mechanism, confirmed directly against the live CDS service before
writing this client (never guessed):

- Library: the official `cdsapi` package, `cdsapi.Client().retrieve(...)`.
- Auth: `~/.cdsapirc` with `url: https://cds.climate.copernicus.eu/api`
  and `key: <PERSONAL-ACCESS-TOKEN>` — or the equivalent constructor
  kwargs, which is what this client uses so the key can come from the
  `CDS_API_KEY` environment variable instead of a file.
- Confirmed via the dataset's own form/constraints/OGC-process JSON
  (`.../api/catalogue/v1/collections/reanalysis-era5-land-timeseries/{form,constraints}.json`
  and `.../api/retrieve/v1/processes/reanalysis-era5-land-timeseries`):
    * `variable`: list of variable names, includes
      `surface_solar_radiation_downwards` — labelled by CDS itself as
      "Surface solar radiation downwards (**de-accumulated**)". This is
      the key semantic fact this MVP relies on: unlike the raw ERA5-Land
      archive (where SSRD is accumulated since the start of the forecast
      and must be manually de-accumulated), each hourly value returned by
      THIS dataset already represents the accumulation for that single
      hour. See src/climate/radiation.py for how this drives aggregation.
    * Geographic selection: the formal input schema exposes an `area`
      bounding box `[N, W, S, E]` (no separate bare lat/lon "location"
      key, even though the interactive form has a location-vs-area
      toggle — the toggle is a UI convenience over the same `area`
      field). The official help text states: "Location selection
      returns a time series for the nearest grid point to the selected
      location" — i.e. nearest-neighbour is applied automatically by the
      server. This client requests a tiny bounding box centred on the
      target point (see `point_bbox_epsilon_deg`) to reproduce that
      "location" behaviour through the documented `area` field, without
      inventing an undocumented parameter.
    * `date`: a single `"YYYY-MM-DD/YYYY-MM-DD"` range string.
    * `data_format`: `"csv"` or `"netcdf"`.

IMPORTANT: this mapping was derived from the dataset's own machine-readable
schema, not from guesswork — but it has NOT been exercised against a real
authenticated request (no CDS_API_KEY was available while building this).
Before any bulk download, run `python -m src.main --test-era5` (a single
coordinate, single month request) and inspect its printed diagnostics
(requested vs. returned coordinates, units, first values) per the
project's Fase 10/36 validation requirement. If CDS has since changed the
schema, only this file and `src/climate/radiation.py` should need updates.
"""

from __future__ import annotations

import io
import logging
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

DATASET_ID = "reanalysis-era5-land-timeseries"

# Column-name aliases tolerated when parsing the returned CSV — the exact
# header used by the live service was not observable without credentials.
# If a real response uses a different name, add it here (single point of
# adaptation) rather than in calling code.
VARIABLE_COLUMN_ALIASES: dict[str, list[str]] = {
    "surface_solar_radiation_downwards": [
        "surface_solar_radiation_downwards",
        "ssrd",
    ],
}
TIME_COLUMN_ALIASES = ["valid_time", "time", "date"]
LATITUDE_COLUMN_ALIASES = ["latitude", "lat"]
LONGITUDE_COLUMN_ALIASES = ["longitude", "lon"]


class CdsCredentialsError(RuntimeError):
    pass


class CdsResponseParsingError(RuntimeError):
    pass


@dataclass
class Era5PointRequest:
    variable: str
    latitude: float
    longitude: float
    start_date: date
    end_date: date
    bbox_epsilon_deg: float
    data_format: str = "csv"

    def area_bbox(self) -> list[float]:
        eps = self.bbox_epsilon_deg
        # CDS area format is [North, West, South, East]
        return [self.latitude + eps, self.longitude - eps, self.latitude - eps, self.longitude + eps]

    def to_cds_request(self) -> dict:
        return {
            "variable": [self.variable],
            "area": self.area_bbox(),
            "date": [f"{self.start_date.isoformat()}/{self.end_date.isoformat()}"],
            "data_format": self.data_format,
        }


@dataclass
class Era5PointResponse:
    requested: Era5PointRequest
    era5_latitude: float
    era5_longitude: float
    hourly: pd.DataFrame  # columns: valid_time (datetime64), value (float, J/m^2)
    raw_file_path: Path
    retrieved_at: datetime


def _find_column(columns: list[str], aliases: list[str], role: str) -> str:
    lower_map = {c.lower(): c for c in columns}
    for alias in aliases:
        if alias.lower() in lower_map:
            return lower_map[alias.lower()]
    raise CdsResponseParsingError(
        f"Could not find a '{role}' column among {columns}. "
        f"Tried aliases: {aliases}. Update VARIABLE_COLUMN_ALIASES / "
        f"*_COLUMN_ALIASES in src/api/copernicus_era5_land.py after "
        f"inspecting a real response (see the --test-era5 diagnostic)."
    )


def _read_result_file(path: Path) -> pd.DataFrame:
    """Read a CDS result file that may be a raw CSV or a zip containing one."""
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not csv_names:
                raise CdsResponseParsingError(f"No CSV file found inside zip result {path}.")
            with zf.open(csv_names[0]) as f:
                return pd.read_csv(io.BytesIO(f.read()))
    return pd.read_csv(path)


class CopernicusEra5LandClient:
    """Wraps `cdsapi.Client` for the ERA5-Land Time-Series dataset."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        raw_download_dir: Optional[Path] = None,
        cds_client=None,
    ):
        self._api_key = api_key
        self._api_url = api_url or "https://cds.climate.copernicus.eu/api"
        self.raw_download_dir = Path(raw_download_dir) if raw_download_dir else Path("data/raw/era5_downloads")
        self.raw_download_dir.mkdir(parents=True, exist_ok=True)
        self._cds_client = cds_client  # injectable for tests; built lazily otherwise

    def _get_cds_client(self):
        if self._cds_client is not None:
            return self._cds_client
        if not self._api_key:
            raise CdsCredentialsError(
                "CDS_API_KEY is not set. Copy .env.example to .env, obtain a "
                "personal access token at https://cds.climate.copernicus.eu/how-to-api "
                "and set CDS_API_KEY there. Credentials are never hardcoded in source."
            )
        import cdsapi

        self._cds_client = cdsapi.Client(url=self._api_url, key=self._api_key)
        return self._cds_client

    def fetch_point_hourly(self, request: Era5PointRequest) -> Era5PointResponse:
        client = self._get_cds_client()
        cds_request = request.to_cds_request()

        target_name = (
            f"{request.variable}_{request.start_date.isoformat()}_{request.end_date.isoformat()}"
            f"_{request.latitude:.4f}_{request.longitude:.4f}.{('zip' if request.data_format == 'netcdf' else 'csv')}"
        )
        target_path = self.raw_download_dir / target_name

        logger.info("Requesting CDS dataset=%s request=%s", DATASET_ID, cds_request)
        client.retrieve(DATASET_ID, cds_request, str(target_path))

        df_raw = _read_result_file(target_path)
        columns = list(df_raw.columns)

        time_col = _find_column(columns, TIME_COLUMN_ALIASES, "time")
        lat_col = _find_column(columns, LATITUDE_COLUMN_ALIASES, "latitude")
        lon_col = _find_column(columns, LONGITUDE_COLUMN_ALIASES, "longitude")
        value_col = _find_column(
            columns, VARIABLE_COLUMN_ALIASES.get(request.variable, [request.variable]), request.variable
        )

        hourly = pd.DataFrame(
            {
                "valid_time": pd.to_datetime(df_raw[time_col]),
                "value": df_raw[value_col].astype(float),
            }
        ).sort_values("valid_time").reset_index(drop=True)

        era5_lat = float(df_raw[lat_col].iloc[0])
        era5_lon = float(df_raw[lon_col].iloc[0])
        if df_raw[lat_col].nunique() > 1 or df_raw[lon_col].nunique() > 1:
            logger.warning(
                "Expected a single ERA5-Land point in the response but found "
                "multiple distinct (%s, %s) values; using the first one.",
                lat_col,
                lon_col,
            )

        return Era5PointResponse(
            requested=request,
            era5_latitude=era5_lat,
            era5_longitude=era5_lon,
            hourly=hourly,
            raw_file_path=target_path,
            retrieved_at=datetime.now(timezone.utc),
        )
