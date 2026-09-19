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
      más cercano. Este cliente pide un bounding box centrado en el punto
      objetivo (ver `point_bbox_epsilon_deg`) para reproducir ese
      comportamiento de "ubicación" a través del campo `area` documentado,
      sin inventar un parámetro no documentado.
    * `date`: un único string de rango `"YYYY-MM-DD/YYYY-MM-DD"`.
    * `data_format`: `"csv"` o `"netcdf"`.

CONFIRMADO EMPÍRICAMENTE (Fase 10, con credenciales reales): un
`point_bbox_epsilon_deg` demasiado chico (se probó 0.001°) hace que el
backend falle con `MultiAdaptorNoDataError: No data found` — la fase real
de la grilla ARCO respecto a una coordenada arbitraria no está
documentada, así que una caja de 0.002° de lado puede no contener ningún
punto de grilla. Con epsilon=0.06° (caja de 0.12°, más ancha que el
espaciado nativo de 0.1°) la solicitud funciona correctamente. Cuando el
área devuelve más de un punto de grilla, este cliente se queda con el más
cercano a la coordenada pedida (ver más abajo en `fetch_point_hourly`).
Si CDS cambió el schema desde entonces, solo este archivo y
`src/climate/radiation.py` deberían necesitar actualizarse.

MODO ÁREA (`fetch_area_hourly` / `Era5AreaRequest`): pedir punto por
punto significa una solicitud HTTP por cada (punto ERA5, mes), y cada una
pasa por cola en el servidor (~20-35s observados) — para la grilla real
del proyecto (miles de puntos únicos) esto tarda decenas de horas. El
mismo campo `area` documentado soporta un bounding box y devuelve TODOS
los puntos de grilla ARCO adentro en una sola respuesta. Agrupando los
puntos necesarios en tiles geográficos (ver src/climate/era5_land.py) se
reduce la cantidad de solicitudes sin cambiar el mecanismo de caché ni la
semántica de nearest-neighbour.

LÍMITE DE COSTO (CONFIRMADO EMPÍRICAMENTE, no documentado por CDS): el
`maximum_extent: {lat: 1.0, lon: 1.0}` de `form.json` es solo el límite
GEOGRÁFICO del modo área. Al pedir un mes completo (744 horas) para un
tile, CDS además rechaza la solicitud con 403 "cost limits exceeded, Your
request is too large" bastante antes de llegar a 1°: un tile de 0.3°
(~16 puntos) funciona, uno de 0.4° (~25 puntos) ya falla. El costo real
parece escalar con (puntos × horas del rango de fechas), no solo con el
área. Ver `area_tile_size_deg` en config.yaml para la calibración
completa y el valor por defecto usado.
"""

from __future__ import annotations

import io
import logging
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
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


@dataclass
class Era5AreaRequest:
    """Solicitud en modo "área": trae TODOS los puntos de grilla ARCO
    dentro de un bounding box en una sola llamada, en vez de un punto por
    llamada. El schema oficial del dataset (`form.json`) documenta esta
    variante con `maximum_extent: {lat: 1.0, lon: 1.0}` — hasta 1° de
    lado. A 0.1° de espaciado nativo, un tile de 1° puede traer hasta
    ~100 puntos en una sola solicitud, lo que reduce drásticamente la
    cantidad de llamadas necesarias frente a pedir punto por punto.
    """

    variable: str
    north: float
    west: float
    south: float
    east: float
    start_date: date
    end_date: date
    data_format: str = "csv"

    def to_cds_request(self) -> dict:
        return {
            "variable": [self.variable],
            "area": [self.north, self.west, self.south, self.east],
            "date": [f"{self.start_date.isoformat()}/{self.end_date.isoformat()}"],
            "data_format": self.data_format,
        }


@dataclass
class Era5AreaResponse:
    requested: Era5AreaRequest
    # (era5_latitude, era5_longitude) -> serie horaria (columnas valid_time, value)
    points: dict[tuple[float, float], pd.DataFrame]
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

        # El bounding box `area` que se envía puede, según el desfase real
        # de la grilla ARCO respecto al punto pedido, devolver más de un
        # punto de grilla (ver point_bbox_epsilon_deg en config.yaml). Nos
        # quedamos con el punto más cercano a la coordenada solicitada — el
        # servidor ya hizo su propia selección de vecino más cercano al
        # resolver `area`, esto solo desempata entre los puntos devueltos.
        unique_points = df_raw[[lat_col, lon_col]].drop_duplicates().reset_index(drop=True)
        if len(unique_points) > 1:
            distances = np.hypot(
                unique_points[lat_col].astype(float) - request.latitude,
                unique_points[lon_col].astype(float) - request.longitude,
            )
            nearest = unique_points.loc[distances.idxmin()]
            era5_lat = float(nearest[lat_col])
            era5_lon = float(nearest[lon_col])
            logger.info(
                "Area request returned %d distinct ERA5-Land points; keeping "
                "the nearest one to the requested coordinate: (%.4f, %.4f).",
                len(unique_points),
                era5_lat,
                era5_lon,
            )
            df_raw = df_raw[
                (df_raw[lat_col].astype(float) == era5_lat) & (df_raw[lon_col].astype(float) == era5_lon)
            ]
        else:
            era5_lat = float(unique_points.loc[0, lat_col])
            era5_lon = float(unique_points.loc[0, lon_col])

        hourly = pd.DataFrame(
            {
                "valid_time": pd.to_datetime(df_raw[time_col]),
                "value": df_raw[value_col].astype(float),
            }
        ).sort_values("valid_time").reset_index(drop=True)

        return Era5PointResponse(
            requested=request,
            era5_latitude=era5_lat,
            era5_longitude=era5_lon,
            hourly=hourly,
            raw_file_path=target_path,
            retrieved_at=datetime.now(timezone.utc),
        )

    def fetch_area_hourly(self, request: Era5AreaRequest) -> Era5AreaResponse:
        """Pide todos los puntos ERA5-Land dentro de `request`'s bounding
        box en una sola llamada. Usar esto (agrupando puntos cercanos en
        tiles, ver src/climate/era5_land.py) en vez de `fetch_point_hourly`
        para descargas masivas — reduce la cantidad de solicitudes en
        órdenes de magnitud frente a pedir un punto a la vez.
        """
        client = self._get_cds_client()
        cds_request = request.to_cds_request()

        target_name = (
            f"{request.variable}_{request.start_date.isoformat()}_{request.end_date.isoformat()}"
            f"_area_{request.north:.4f}_{request.west:.4f}_{request.south:.4f}_{request.east:.4f}"
            f".{('zip' if request.data_format == 'netcdf' else 'csv')}"
        )
        target_path = self.raw_download_dir / target_name

        logger.info("Requesting CDS dataset=%s (area mode) request=%s", DATASET_ID, cds_request)
        client.retrieve(DATASET_ID, cds_request, str(target_path))

        df_raw = _read_result_file(target_path)
        columns = list(df_raw.columns)

        time_col = _find_column(columns, TIME_COLUMN_ALIASES, "time")
        lat_col = _find_column(columns, LATITUDE_COLUMN_ALIASES, "latitude")
        lon_col = _find_column(columns, LONGITUDE_COLUMN_ALIASES, "longitude")
        value_col = _find_column(
            columns, VARIABLE_COLUMN_ALIASES.get(request.variable, [request.variable]), request.variable
        )

        points: dict[tuple[float, float], pd.DataFrame] = {}
        for (lat, lon), group in df_raw.groupby([lat_col, lon_col]):
            hourly = pd.DataFrame(
                {
                    "valid_time": pd.to_datetime(group[time_col]),
                    "value": group[value_col].astype(float),
                }
            ).sort_values("valid_time").reset_index(drop=True)
            points[(float(lat), float(lon))] = hourly

        logger.info("Area request returned %d distinct ERA5-Land points.", len(points))

        return Era5AreaResponse(
            requested=request,
            points=points,
            raw_file_path=target_path,
            retrieved_at=datetime.now(timezone.utc),
        )
