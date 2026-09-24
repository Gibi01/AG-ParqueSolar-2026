"""Punto de entrada del CLI.

    python -m src.main --setup
    python -m src.main --download
    python -m src.main --process
    python -m src.main --optimize
    python -m src.main --run-all

Las capas vectoriales y los bloques climáticos ARCO se cachean en disco.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd

from src.climate.arco import ArcoSolarService
from src.config.settings import Settings, load_settings
from src.data.cache import layer_cache_for_settings
from src.data.validators import ValidationError
from src.database.repository import Repository
from src.gis.grid import build_grid
from src.optimization.genetic_algorithm import GeneticAlgorithm
from src.pipeline.ingest import (
    ingest_power_lines,
    ingest_region_boundary,
    ingest_transformers,
    ingest_urban_areas,
)
from src.pipeline.preprocess import run_preprocessing
from src.pipeline.reporting import write_run_outputs

logger = logging.getLogger(__name__)

REQUIRED_LAYER_NAMES = ["region_boundary", "urban_areas_points"]


def _empty_layer(columns: list[str]) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(columns=columns + ["geometry"], geometry="geometry", crs="EPSG:4326")


def setup_logging(settings: Settings) -> None:
    settings.paths.logs.mkdir(parents=True, exist_ok=True)
    log_file = settings.paths.logs / f"run_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
    )
    logger.info("Logging to %s", log_file)


def cmd_setup(settings: Settings) -> None:
    settings.ensure_directories()
    print(f"Región configurada: {settings.region.name} (code={settings.region.admin_source.code_value})")
    print(f"Grilla: {settings.grid.resolution_km} km | Parque: {settings.park.area_hectares} ha")
    print(
        "Pesos fitness: solar={:.2f} linea={:.2f} transformador={:.2f} (suma={:.2f})".format(
            settings.fitness.weight_solar,
            settings.fitness.weight_grid_distance,
            settings.fitness.weight_transformer_distance,
            settings.fitness.weight_solar
            + settings.fitness.weight_grid_distance
            + settings.fitness.weight_transformer_distance,
        )
    )
    print(f"Clima: {settings.climate.dataset} / {settings.climate.variable}")
    print(
        f"       período={settings.climate.year_months[0]} a {settings.climate.year_months[-1]} "
        f"meses representativos={settings.climate.months}"
    )
    if settings.fitness.use_solar and not settings.cds_api_key:
        print("CDS_API_KEY: no configurada; ARCO requiere esa credencial.")
    print("Directorios de datos/resultados verificados/creados.")


def cmd_download(settings: Settings, force: bool = False) -> None:
    region = ingest_region_boundary(settings, force=force)
    print(f"Límite provincial: {region.metadata['source']}")
    urban = ingest_urban_areas(settings, region.gdf, force=force)
    print(f"Zonas urbanas (BAHRA): {len(urban.gdf)} puntos en la región.")
    if settings.fitness.use_power_lines:
        lines = ingest_power_lines(settings, region.gdf, force=force)
        print(f"Líneas eléctricas: {len(lines.gdf)} segmentos en la región.")
    if settings.fitness.use_transformers:
        transformers = ingest_transformers(settings, region.gdf, force=force)
        print(f"Centros/subestaciones transformadoras: {len(transformers.gdf)} en la región.")


def _load_cached_layers(settings: Settings) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    cache = layer_cache_for_settings(settings)
    required = REQUIRED_LAYER_NAMES.copy()
    if settings.fitness.use_power_lines:
        required.append("power_lines")
    if settings.fitness.use_transformers:
        required.append("transformers")
    missing = [n for n in required if not cache.exists(n)]
    if missing:
        raise RuntimeError(
            f"Faltan capas en caché: {missing}. Ejecutá 'python -m src.main --download' primero."
        )
    region_gdf, _ = cache.load("region_boundary")
    urban_gdf, _ = cache.load("urban_areas_points")
    lines_gdf = cache.load("power_lines")[0] if settings.fitness.use_power_lines else _empty_layer(["line_id", "tension_v"])
    transformers_gdf = cache.load("transformers")[0] if settings.fitness.use_transformers else _empty_layer(["nombre"])
    return region_gdf, urban_gdf, lines_gdf, transformers_gdf


def cmd_process(settings: Settings, repo: Repository):
    region_gdf, urban_gdf, lines_gdf, transformers_gdf = _load_cached_layers(settings)
    if not settings.fitness.use_solar:
        era5_service = None
    else:
        era5_service = ArcoSolarService(settings)
    candidates = run_preprocessing(settings, repo, region_gdf, urban_gdf, lines_gdf, transformers_gdf, era5_service)
    print(f"Candidatos: {int(candidates['valid'].sum())} válidos de {len(candidates)} celdas de grilla.")
    return candidates


def cmd_optimize(settings: Settings, repo: Repository):
    region_gdf, urban_gdf, lines_gdf, transformers_gdf = _load_cached_layers(settings)
    grid = build_grid(region_gdf, settings.grid.resolution_km)

    stored_grid = repo.get_grid_cells_df()
    if stored_grid.empty or not stored_grid["region_name"].eq(settings.region.name).all() or not stored_grid["resolution_km"].eq(settings.grid.resolution_km).all():
        raise RuntimeError("La base procesada corresponde a otra región o grilla; ejecutá --process antes de --optimize.")

    candidates_valid = repo.get_candidate_locations_df(valid_only=True)
    candidates_all = repo.get_candidate_locations_df(valid_only=False)
    for active, columns in (
        (settings.fitness.use_solar, ["solar_score"]),
        (settings.fitness.use_power_lines, ["distance_to_power_line_km", "grid_proximity_score"]),
        (settings.fitness.use_transformers, ["distance_to_transformer_km", "transformer_proximity_score"]),
    ):
        if not active:
            candidates_valid.loc[:, columns] = float("nan")
            candidates_all.loc[:, columns] = float("nan")
    if len(candidates_valid) == 0:
        raise RuntimeError(
            "No hay candidatos válidos en la base de datos. Ejecutá "
            "'python -m src.main --process' primero."
        )

    ga = GeneticAlgorithm(candidates_valid, settings.fitness, settings.genetic_algorithm)
    result = ga.run(top_n=10)

    outputs = write_run_outputs(
        settings, repo, result, candidates_all, region_gdf, grid.gdf, urban_gdf, lines_gdf, transformers_gdf
    )
    print("\nTOP 10 UBICACIONES")
    print("=" * 60)
    for _, row in result.top10.iterrows():
        summary = (
            f"#{int(row['rank']):>2}  cell_id={int(row['grid_cell_id']):<6} "
            f"lat={row['latitude']:.5f} lon={row['longitude']:.5f}  "
            f"fitness={row['fitness']:.4f}"
        )
        if settings.fitness.use_solar:
            summary += f"  solar={row['solar_score']:.3f}"
        if settings.fitness.use_power_lines:
            summary += f"  linea={row['distance_to_power_line_km']:.1f}km ({row['grid_proximity_score']:.3f})"
        if settings.fitness.use_transformers:
            summary += f"  transf={row['distance_to_transformer_km']:.1f}km ({row['transformer_proximity_score']:.3f})"
        print(summary)
    print("=" * 60)
    print(
        "\nNota: estas son ubicaciones potencialmente favorables según las variables "
        "espaciales y climáticas consideradas — no una determinación de óptimo económico."
    )
    for label, path in outputs.items():
        print(f"  {label}: {path}")
    return result


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Optimización de ubicaciones de parques solares (MVP)")
    parser.add_argument("--config", default="config.yaml", help="Ruta al archivo de configuración YAML")
    parser.add_argument("--setup", action="store_true", help="Validar configuración y preparar directorios")
    parser.add_argument("--download", action="store_true", help="Descargar/cachear capas desde las APIs")
    parser.add_argument("--process", action="store_true", help="Construir grilla, distancias y clima -> candidatos")
    parser.add_argument("--optimize", action="store_true", help="Ejecutar el algoritmo genético y generar resultados")
    parser.add_argument("--run-all", action="store_true", help="Ejecutar setup+download+process+optimize en secuencia")
    parser.add_argument("--force", action="store_true", help="Forzar re-descarga, ignorando la caché en disco")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass  # no todos los streams de stdout soportan reconfigure (p. ej. cuando se capturan en tests)

    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if not any([args.setup, args.download, args.process, args.optimize, args.run_all]):
        parser.print_help()
        return 0

    settings = load_settings(args.config)
    settings.ensure_directories()
    setup_logging(settings)

    try:
        if args.setup or args.run_all:
            cmd_setup(settings)

        if args.download or args.run_all:
            cmd_download(settings, force=args.force)

        repo = Repository(settings.paths.database)

        if args.process or args.run_all:
            cmd_process(settings, repo)

        if args.optimize or args.run_all:
            cmd_optimize(settings, repo)

    except (ValidationError, RuntimeError) as exc:
        logger.error("%s", exc)
        print(f"\nERROR: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
