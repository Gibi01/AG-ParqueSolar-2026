"""Punto de entrada del CLI.

    python -m src.main --setup
    python -m src.main --download
    python -m src.main --process
    python -m src.main --optimize
    python -m src.main --run-all
    python -m src.main --test-era5      # diagnóstico de un solo punto, Fase 10/36

Las salidas de cada paso se cachean en disco (data/raw/layers/*.gpkg para
las capas vectoriales ingeridas, data/cache/era5_land_cache/ para los
puntos de clima, data/processed/parque_solar.sqlite para todo lo que
sigue). Volver a correr un paso es un no-op rápido salvo que se pase --force.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import geopandas as gpd

from src.api.copernicus_era5_land import CdsCredentialsError, CopernicusEra5LandClient, Era5PointRequest
from src.climate.era5_land import Era5LandRadiationService
from src.climate.radiation import aggregate_monthly_kwh_m2
from src.config.settings import Settings, load_settings
from src.data.cache import RawLayerCache
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

REQUIRED_LAYER_NAMES = ["region_boundary", "urban_areas_points", "power_lines", "transformers"]


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
    print(f"       años={settings.climate.years} meses={settings.climate.months}")
    if settings.cds_api_key:
        print("CDS_API_KEY: configurada (no se muestra el valor).")
    else:
        print(
            "CDS_API_KEY: NO configurada. Copiá .env.example a .env y completá tu "
            "token de https://cds.climate.copernicus.eu/how-to-api antes de --download/--process."
        )
    print("Directorios de datos/resultados verificados/creados.")


def cmd_download(settings: Settings, force: bool = False) -> None:
    region = ingest_region_boundary(settings, force=force)
    print(f"Límite provincial: {region.metadata['source']}")
    urban = ingest_urban_areas(settings, region.gdf, force=force)
    print(f"Zonas urbanas (BAHRA): {len(urban.gdf)} puntos en la región.")
    lines = ingest_power_lines(settings, region.gdf, force=force)
    print(f"Líneas eléctricas: {len(lines.gdf)} segmentos en la región.")
    transformers = ingest_transformers(settings, region.gdf, force=force)
    print(f"Centros/subestaciones transformadoras: {len(transformers.gdf)} en la región.")


def _load_cached_layers(settings: Settings) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    cache = RawLayerCache(settings.paths.data_raw / "layers")
    missing = [n for n in REQUIRED_LAYER_NAMES if not cache.exists(n)]
    if missing:
        raise RuntimeError(
            f"Faltan capas en caché: {missing}. Ejecutá 'python -m src.main --download' primero."
        )
    region_gdf, _ = cache.load("region_boundary")
    urban_gdf, _ = cache.load("urban_areas_points")
    lines_gdf, _ = cache.load("power_lines")
    transformers_gdf, _ = cache.load("transformers")
    return region_gdf, urban_gdf, lines_gdf, transformers_gdf


def cmd_process(settings: Settings, repo: Repository):
    region_gdf, urban_gdf, lines_gdf, transformers_gdf = _load_cached_layers(settings)
    era5_service = Era5LandRadiationService(settings)
    candidates = run_preprocessing(settings, repo, region_gdf, urban_gdf, lines_gdf, transformers_gdf, era5_service)
    print(f"Candidatos: {int(candidates['valid'].sum())} válidos de {len(candidates)} celdas de grilla.")
    return candidates


def cmd_optimize(settings: Settings, repo: Repository):
    region_gdf, urban_gdf, lines_gdf, transformers_gdf = _load_cached_layers(settings)
    grid = build_grid(region_gdf, settings.grid.resolution_km)

    candidates_valid = repo.get_candidate_locations_df(valid_only=True)
    candidates_all = repo.get_candidate_locations_df(valid_only=False)
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
        print(
            f"#{int(row['rank']):>2}  cell_id={int(row['grid_cell_id']):<6} "
            f"lat={row['latitude']:.5f} lon={row['longitude']:.5f}  "
            f"fitness={row['fitness']:.4f}  "
            f"solar={row['solar_score']:.3f}  linea={row['distance_to_power_line_km']:.1f}km "
            f"({row['grid_proximity_score']:.3f})  "
            f"transf={row['distance_to_transformer_km']:.1f}km ({row['transformer_proximity_score']:.3f})"
        )
    print("=" * 60)
    print(
        "\nNota: estas son ubicaciones potencialmente favorables según las variables "
        "espaciales y climáticas consideradas — no una determinación de óptimo económico."
    )
    for label, path in outputs.items():
        print(f"  {label}: {path}")
    return result


def cmd_test_era5(settings: Settings) -> None:
    """Fase 10/36: diagnóstico de una sola coordenada y un solo mes contra
    la API real de CDS, se corre ANTES de intentar cualquier descarga masiva."""
    cache = RawLayerCache(settings.paths.data_raw / "layers")
    if cache.exists("region_boundary"):
        region_gdf, _ = cache.load("region_boundary")
    else:
        region_gdf = ingest_region_boundary(settings).gdf

    centroid = region_gdf.geometry.union_all().centroid
    lat, lon = float(centroid.y), float(centroid.x)
    year, month = settings.climate.years[0], settings.climate.months[0]

    print(f"Coordenada solicitada: lat={lat:.5f}, lon={lon:.5f} (centroide de {settings.region.name})")
    print(f"Dataset: {settings.climate.dataset}")
    print(f"Variable: {settings.climate.variable}")
    print(f"Período: {year}-{month:02d}")

    client = CopernicusEra5LandClient(
        api_key=settings.cds_api_key,
        api_url=settings.cds_api_url,
        raw_download_dir=settings.paths.data_raw / "era5_downloads",
    )
    request = Era5PointRequest(
        variable=settings.climate.variable,
        latitude=lat,
        longitude=lon,
        start_date=date(year, month, 1),
        end_date=date(year, month, 28),
        bbox_epsilon_deg=settings.climate.point_bbox_epsilon_deg,
    )
    try:
        response = client.fetch_point_hourly(request)
    except CdsCredentialsError as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)

    print(f"\nCoordenada ERA5-Land utilizada (nearest-neighbour, servidor): lat={response.era5_latitude:.4f}, lon={response.era5_longitude:.4f}")
    print(f"Cantidad de registros horarios recuperados: {len(response.hourly)}")
    print("Unidad original: J/m^2 (surface_solar_radiation_downwards, de-accumulated por hora, según CDS)")
    print("Primeros valores (valid_time, J/m^2):")
    print(response.hourly.head(5).to_string(index=False))

    agg = aggregate_monthly_kwh_m2(response.hourly, year, month)
    print(f"\nMétodo de agregación: suma de J/m^2 horarios del mes -> división por 3.6e6 -> kWh/m^2")
    print(f"Radiación mensual agregada: {agg.radiation_kwh_m2:.2f} kWh/m^2 ({agg.n_hours_used}/{agg.n_hours_expected} horas)")
    print(f"¿Físicamente plausible?: {'sí' if agg.is_plausible else 'NO -- revisar supuesto de de-acumulación'}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Optimización de ubicaciones de parques solares (MVP)")
    parser.add_argument("--config", default="config.yaml", help="Ruta al archivo de configuración YAML")
    parser.add_argument("--setup", action="store_true", help="Validar configuración y preparar directorios")
    parser.add_argument("--download", action="store_true", help="Descargar/cachear capas desde las APIs")
    parser.add_argument("--process", action="store_true", help="Construir grilla, distancias y clima -> candidatos")
    parser.add_argument("--optimize", action="store_true", help="Ejecutar el algoritmo genético y generar resultados")
    parser.add_argument("--run-all", action="store_true", help="Ejecutar setup+download+process+optimize en secuencia")
    parser.add_argument("--test-era5", action="store_true", help="Diagnóstico de un solo punto ERA5-Land (Fase 10)")
    parser.add_argument("--force", action="store_true", help="Forzar re-descarga, ignorando la caché en disco")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass  # no todos los streams de stdout soportan reconfigure (p. ej. cuando se capturan en tests)

    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if not any([args.setup, args.download, args.process, args.optimize, args.run_all, args.test_era5]):
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

        if args.test_era5:
            cmd_test_era5(settings)

    except (ValidationError, RuntimeError, CdsCredentialsError) as exc:
        logger.error("%s", exc)
        print(f"\nERROR: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
