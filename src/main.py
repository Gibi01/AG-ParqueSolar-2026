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
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd

from src.climate.arco import ArcoSolarService
from src.config.settings import Settings, load_settings
from src.data.cache import layer_cache_for_settings
from src.data.validators import ValidationError
from src.database.spatial import SpatialRepository as Repository, config_signature
from src.optimization.spatial import ParkEvaluator
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

REQUIRED_LAYER_NAMES = ["region_boundary", "urban_areas_envelopes"]


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
    print(f"Grilla: {settings.grid.resolution_km} km | Capacidad EXPERIMENTAL: {settings.park.max_connection_capacity_mw} MW")
    print(
        "Pesos fitness: solar={:.2f} linea={:.2f} transformador={:.2f} potencia={:.2f} (suma={:.2f})".format(
            settings.fitness.weight_solar,
            settings.fitness.weight_grid_distance,
            settings.fitness.weight_transformer_distance,
            settings.fitness.weight_installed_power,
            settings.fitness.weight_solar
            + settings.fitness.weight_grid_distance
            + settings.fitness.weight_transformer_distance
            + settings.fitness.weight_installed_power,
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
    print(f"Envolventes INDEC: {len(urban.gdf)} geometrías nacionales (recorte al procesar).")
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
    urban_gdf, urban_metadata = cache.load("urban_areas_envelopes")
    urban_gdf.attrs['source_metadata'] = urban_metadata
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
    dataset = repo.load_dataset(config_signature(settings))
    source_hash = dataset['metadata'].get('urban_source', {}).get('sha256')
    if source_hash:
        cache = layer_cache_for_settings(settings)
        metadata_path = cache.cache_dir / 'urban_areas_envelopes.meta.json'
        if not metadata_path.exists():
            raise RuntimeError('Falta la referencia urbana actual; ejecutá --download y --process.')
        current_hash = json.loads(metadata_path.read_text(encoding='utf-8')).get('sha256')
        if current_hash != source_hash:
            raise RuntimeError('La fuente INDEC cambió desde el procesamiento; ejecutá --process.')
    evaluator = ParkEvaluator(dataset['grid'], dataset['neighbors'], dataset['lines'],
                              dataset['transformers'], settings.park, settings.fitness)
    result = GeneticAlgorithm(evaluator, settings.genetic_algorithm).run()
    outputs = write_run_outputs(settings, repo, result, dataset, evaluator)
    print("\nTOP 5 PARQUES — capacidad experimental, no capacidad real de ET")
    print(result.top5[['rank', 'number_of_cells', 'park_area_km2', 'installed_power_mw', 'fitness']].to_string(index=False))
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

    except (ValidationError, RuntimeError, ValueError) as exc:
        logger.error("%s", exc)
        print(f"\nERROR: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
