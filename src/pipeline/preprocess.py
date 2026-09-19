"""Preprocesamiento: capas ingeridas -> grilla -> métricas -> candidate_locations.

Este es el paso de ETL que convierte los GeoDataFrames crudos ingeridos
en la tabla local `candidate_locations`, lista para el AG (Fase 20 de los
requisitos). Nada acá llama a una API externa — la obtención de clima
(que sí llama a la API de CDS, cacheada) es la única excepción, invocada
a través de `Era5LandRadiationService`, que a su vez nunca vuelve a
obtener un punto/mes ya cacheado.
"""

from __future__ import annotations

import logging

import geopandas as gpd
import pandas as pd

from src.climate.era5_land import CellPoint, Era5LandRadiationService
from src.climate.climatology import annual_solar_kwh_m2
from src.config.settings import Settings
from src.data.validators import validate_layer_present, validate_not_empty
from src.database.repository import Repository
from src.gis.distance import nearest_distance_km
from src.gis.grid import Grid, build_grid
from src.gis.spatial_operations import buffer_points_km, urban_exclusion_mask
from src.optimization.fitness import normalize_min_max

logger = logging.getLogger(__name__)


def run_preprocessing(
    settings: Settings,
    repo: Repository,
    region_gdf: gpd.GeoDataFrame,
    urban_gdf: gpd.GeoDataFrame,
    power_lines_gdf: gpd.GeoDataFrame,
    transformers_gdf: gpd.GeoDataFrame,
    era5_service: Era5LandRadiationService | None = None,
) -> pd.DataFrame:
    # Chequeos previos de la Fase 32: fallar explícitamente, nunca seguir
    # en silencio sin una capa requerida (transformadores en particular — Fase 16).
    validate_layer_present(power_lines_gdf, "power_lines")
    validate_layer_present(transformers_gdf, "transformers")

    grid: Grid = build_grid(region_gdf, settings.grid.resolution_km)
    logger.info("Built grid: %d cells (%s)", len(grid.gdf), grid.projected_crs)
    repo.replace_grid_cells(grid.gdf, settings.region.name, settings.grid.resolution_km, str(grid.projected_crs))

    excluded_types = set(settings.urban_exclusion.include_types)
    urban_for_exclusion = urban_gdf[urban_gdf["tipo"].isin(excluded_types)]
    urban_buffered = buffer_points_km(urban_for_exclusion, settings.urban_exclusion.buffer_km, grid.projected_crs)
    urban_mask = urban_exclusion_mask(grid.gdf, urban_buffered).reset_index(drop=True)
    repo.replace_urban_areas(urban_gdf, excluded_types)
    logger.info(
        "Urban exclusion: %d/%d cells excluded (buffer=%.1fkm, types=%s)",
        int(urban_mask.sum()),
        len(grid.gdf),
        settings.urban_exclusion.buffer_km,
        sorted(excluded_types),
    )

    repo.replace_power_lines(power_lines_gdf)
    repo.replace_transformers(transformers_gdf)

    d_lines_km = nearest_distance_km(grid.gdf, power_lines_gdf, grid.projected_crs)
    d_trafo_km = nearest_distance_km(grid.gdf, transformers_gdf, grid.projected_crs)

    era5_service = era5_service or Era5LandRadiationService(settings)
    cell_points = [
        CellPoint(grid_cell_id=int(row.cell_id), latitude=float(row.latitude), longitude=float(row.longitude))
        for row in grid.gdf.itertuples()
    ]
    solar_records = era5_service.get_monthly_radiation(cell_points)
    repo.replace_solar_radiation(solar_records)

    solar_df = pd.DataFrame(
        {
            "grid_cell_id": [r.grid_cell_id for r in solar_records],
            "year": [r.year for r in solar_records],
            "month": [r.month for r in solar_records],
            "radiation_kwh_m2": [r.radiation_kwh_m2 for r in solar_records],
        }
    )
    representative_solar = annual_solar_kwh_m2(solar_df, settings.climate.months).reindex(grid.gdf["cell_id"])

    missing_climate = representative_solar.isna().reset_index(drop=True)

    solar_norm = normalize_min_max(representative_solar.fillna(representative_solar.mean()).to_numpy(), invert=False)
    grid_prox_norm = normalize_min_max(d_lines_km, invert=True)
    trafo_prox_norm = normalize_min_max(d_trafo_km, invert=True)

    candidates = pd.DataFrame(
        {
            "grid_cell_id": grid.gdf["cell_id"].to_numpy(),
            "latitude": grid.gdf["latitude"].to_numpy(),
            "longitude": grid.gdf["longitude"].to_numpy(),
            "solar_score": solar_norm,
            "distance_to_power_line_km": d_lines_km,
            "grid_proximity_score": grid_prox_norm,
            "distance_to_transformer_km": d_trafo_km,
            "transformer_proximity_score": trafo_prox_norm,
        }
    )

    invalid_reason = pd.Series([None] * len(candidates), dtype=object)
    invalid_reason[urban_mask.to_numpy()] = "intersects_urban_area"
    invalid_reason[missing_climate.to_numpy() & invalid_reason.isna()] = "missing_climate_data"

    candidates["valid"] = invalid_reason.isna()
    candidates["invalid_reason"] = invalid_reason

    validate_not_empty(candidates[candidates["valid"]], "candidate_locations (valid)")
    repo.replace_candidate_locations(candidates)

    logger.info(
        "Candidate locations: %d valid / %d total (%d excluded: urban, %d excluded: missing climate)",
        int(candidates["valid"].sum()),
        len(candidates),
        int((invalid_reason == "intersects_urban_area").sum()),
        int((invalid_reason == "missing_climate_data").sum()),
    )
    return candidates
