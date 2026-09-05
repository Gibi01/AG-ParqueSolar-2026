"""Assembles and writes results/: ranking.csv, candidate_locations.csv,
optimization_run.json and map.html — plus persisting the run into
`optimization_results`.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.config.settings import Settings
from src.database.repository import Repository
from src.gis.spatial_operations import buffer_points_km
from src.optimization.genetic_algorithm import GAResult
from src.visualization.map import build_map

logger = logging.getLogger(__name__)

MONTH_COLUMN_NAMES = {
    1: "solar_january",
    2: "solar_february",
    3: "solar_march",
    4: "solar_april",
    5: "solar_may",
    6: "solar_june",
    7: "solar_july",
    8: "solar_august",
    9: "solar_september",
    10: "solar_october",
    11: "solar_november",
    12: "solar_december",
}

RESULT_DISCLAIMER = (
    "Estos resultados representan ubicaciones potencialmente favorables segun "
    "las variables espaciales y climaticas consideradas en este MVP. No "
    "constituyen una determinacion de la ubicacion economicamente optima: "
    "no incorporan costo de terreno, costo de conexion, capacidad disponible "
    "de subestacion o linea, permisos, cobertura de suelo completa, pendiente, "
    "areas protegidas, hidrografia ni un analisis financiero. Los pesos de la "
    "funcion de fitness son valores iniciales del MVP, no pesos cientificamente "
    "validados."
)


def enrich_with_monthly_solar(top10: pd.DataFrame, solar_radiation_df: pd.DataFrame, year: int) -> pd.DataFrame:
    subset = solar_radiation_df[solar_radiation_df["year"] == year]
    pivot = subset.pivot_table(index="grid_cell_id", columns="month", values="radiation_kwh_m2")
    pivot = pivot.rename(columns=MONTH_COLUMN_NAMES)
    month_cols = [c for c in pivot.columns if c in MONTH_COLUMN_NAMES.values()]
    enriched = top10.merge(pivot[month_cols], left_on="grid_cell_id", right_index=True, how="left")
    return enriched


def write_run_outputs(
    settings: Settings,
    repo: Repository,
    ga_result: GAResult,
    candidates_df: pd.DataFrame,
    region_gdf: gpd.GeoDataFrame,
    grid_gdf: gpd.GeoDataFrame,
    urban_gdf: gpd.GeoDataFrame,
    power_lines_gdf: gpd.GeoDataFrame,
    transformers_gdf: gpd.GeoDataFrame,
    run_id: str | None = None,
) -> dict[str, Path]:
    run_id = run_id or datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")
    results_dir = settings.paths.results
    results_dir.mkdir(parents=True, exist_ok=True)

    solar_radiation_df = repo.get_solar_radiation_df()
    ranking = enrich_with_monthly_solar(ga_result.top10, solar_radiation_df, settings.climate.years[0])

    ranking_path = results_dir / "ranking.csv"
    ranking.to_csv(ranking_path, index=False)

    candidates_path = results_dir / "candidate_locations.csv"
    candidates_df.to_csv(candidates_path, index=False)

    run_metadata = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "region": settings.region.name,
        "grid_resolution_km": settings.grid.resolution_km,
        "park_area_hectares": settings.park.area_hectares,
        "park_area_note": (
            "Stored for traceability only; this MVP does not yet verify that "
            "20,000 contiguous m^2 of usable, obstruction-free land actually "
            "exist inside a candidate cell (no land-cover layer yet)."
        ),
        "climate": {
            "dataset": settings.climate.dataset,
            "variable": settings.climate.variable,
            "years": settings.climate.years,
            "months": settings.climate.months,
            "spatial_selection_method": "nearest_neighbour",
        },
        "fitness_weights": settings.fitness.model_dump(),
        "genetic_algorithm_config": settings.genetic_algorithm.model_dump(),
        "n_candidates_considered": ga_result.n_candidates_considered,
        "generations_run": ga_result.generations_run,
        "population_size": ga_result.population_size,
        "top10_grid_cell_ids": ranking["grid_cell_id"].tolist(),
        "disclaimer": RESULT_DISCLAIMER,
    }
    run_path = results_dir / "optimization_run.json"
    run_path.write_text(json.dumps(run_metadata, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    result_cols = [
        "rank",
        "grid_cell_id",
        "latitude",
        "longitude",
        "solar_score",
        "distance_to_power_line_km",
        "distance_to_transformer_km",
        "grid_proximity_score",
        "transformer_proximity_score",
        "fitness",
    ]
    repo.save_optimization_results(run_id, ga_result.top10[result_cols])

    excluded_types = set(settings.urban_exclusion.include_types)
    urban_for_map = urban_gdf[urban_gdf["tipo"].isin(excluded_types)]
    urban_buffered = buffer_points_km(urban_for_map, settings.urban_exclusion.buffer_km, grid_gdf.crs)

    map_path = build_map(
        region_gdf=region_gdf,
        grid_gdf=grid_gdf,
        urban_buffered_gdf=urban_buffered,
        power_lines_gdf=power_lines_gdf,
        transformers_gdf=transformers_gdf,
        top10_df=ranking,
        output_path=results_dir / "map.html",
    )

    logger.info("Wrote run outputs: %s", results_dir)
    return {
        "ranking_csv": ranking_path,
        "candidate_locations_csv": candidates_path,
        "optimization_run_json": run_path,
        "map_html": map_path,
    }
