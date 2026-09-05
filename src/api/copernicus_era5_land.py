"""Cliente programático oficial para el Copernicus Climate Data Store (CDS),
específicamente el dataset "ERA5-Land hourly time-series data from 1950
to present" (ARCO) — id `reanalysis-era5-land-timeseries`.

Mecanismo de acceso, confirmado directamente contra el servicio CDS real
antes de escribir este cliente (nunca adivinado):

- Librería: el paquete oficial `cdsapi`, `cdsapi.Client().retrieve(...)`.
- Autenticación: `~/.cdsapirc` con `url: https://cds.climate.copernicus.eu/api`
  y `key: <PERSONAL-ACCESS-TOKEN>` — o los kwargs equivalentes del
  constructor, que es lo que usa este cliente para que la clave pueda venir
  de la variable de entorno `CDS_API_KEY` en vez de un archivo.
- Confirmado vía el JSON de form/constraints/proceso-OGC del propio dataset
  (`.../api/catalogue/v1/collections/reanalysis-era5-land-timeseries/{form,constraints}.json`
  y `.../api/retrieve/v1/processes/reanalysis-era5-land-timeseries`):
    * `variable`: lista de nombres de variable, incluye
      `surface_solar_radiation_downwards` — etiquetada por el propio CDS
      como "Surface solar radiation downwards (**de-accumulated**)". Este
      es el hecho semántico clave del que depende este MVP: a diferencia
      del archivo crudo de ERA5-Land (donde SSRD es acumulado desde el
      inicio del forecast y hay que de-acumularlo manualmente), cada valor
      horario devuelto por ESTE dataset ya representa la acumulación de
      esa hora puntual. Ver src/climate/radiation.py para cómo esto guía
      la agregación.
    * Selección geográfica: el schema formal de entrada expone un bounding
      box `area` `[N, W, S, E]` (no una clave suelta "location" de
      lat/lon, aunque el formulario interactivo tenga un selector
      ubicación-vs-área — ese selector es un atajo de UI sobre el mismo
      campo `area`). El texto de ayuda oficial dice: "Location selection
      returns a time series for the nearest grid point to the selected
      location" — es decir, el servidor aplica automáticamente el vecino
      más cercano. Este cliente pide un bounding box mínimo centrado en el
      punto objetivo (ver `point_bbox_epsilon_deg`) para reproducir ese
      comportamiento de "ubicación" a través del campo `area` documentado,
      sin inventar un parámetro no documentado.
    * `date`: un único string de rango `"YYYY-MM-DD/YYYY-MM-DD"`.
    * `data_format`: `"csv"` o `"netcdf"`.

IMPORTANTE: este mapeo se derivó del schema legible por máquina del propio
dataset, no de adivinar — pero NO fue ejercido contra una solicitud
autenticada real (no había una CDS_API_KEY disponible al construir esto).
Antes de cualquier descarga masiva, correr `python -m src.main --test-era5`
(una solicitud de una sola coordenada, un solo mes) e inspeccionar sus
diagnósticos impresos (coordenadas solicitadas vs. devueltas, unidades,
primeros valores) según el requisito de validación de la Fase 10/36 del
proyecto. Si CDS cambió el schema desde entonces, solo este archivo y
`src/climate/radiation.py` deberían necesitar actualizarse.
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

# Alias de nombres de columna tolerados al parsear el CSV devuelto — el
# encabezado exacto que usa el servicio real no se pudo observar sin
# credenciales. Si una respuesta real usa un nombre distinto, agregarlo
# acá (único punto de adaptación) en vez de en el código que llama.
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
        # El formato de área de CDS es [Norte, Oeste, Sur, Este]
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
    hourly: pd.DataFrame  # columnas: valid_time (datetime64), value (float, J/m^2)
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
    """Lee un archivo de resultado de CDS que puede ser un CSV crudo o un zip que contiene uno."""
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as zf:
            csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not csv_names:
                raise CdsResponseParsingError(f"No CSV file found inside zip result {path}.")
            with zf.open(csv_names[0]) as f:
                return pd.read_csv(io.BytesIO(f.read()))
    return pd.read_csv(path)


class CopernicusEra5LandClient:
    """Envuelve `cdsapi.Client` para el dataset ERA5-Land Time-Series."""

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
        self._cds_client = cds_client  # inyectable para tests; se construye de forma perezosa si no

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
