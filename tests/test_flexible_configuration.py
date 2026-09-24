"""Pruebas locales de criterios opcionales y separación de caché."""

from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import geopandas as gpd
import numpy as np
import pandas as pd
from pydantic import ValidationError
from shapely.geometry import LineString, box
from sqlalchemy import create_engine

from src.config.settings import ClimateConfig, FitnessWeights, Settings, load_settings
from src.data.cache import layer_cache_for_settings
from src.data.validators import ValidationError as DataValidationError
from src.database.models import Base, OptimizationResult
from src.main import build_arg_parser, cmd_download
from src.optimization.fitness import compute_fitness
from src.pipeline.ingest import ingest_region_boundary
from src.pipeline.preprocess import run_preprocessing
from src.visualization.map import build_map


class FlexibleConfigurationTests(unittest.TestCase):
    def test_only_santa_fe_is_accepted_from_configuration(self) -> None:
        configured = load_settings().model_dump()
        self.assertEqual(configured["region"]["name"], "Santa Fe")
        self.assertEqual(configured["region"]["admin_source"]["code_value"], "82")
        for name, code in (("Córdoba", "14"), ("Santa Fe", "14"), ("Córdoba", "82")):
            with self.subTest(name=name, code=code), self.assertRaisesRegex(ValidationError, "solo admite Santa Fe"):
                candidate = {**configured, "region": {
                    **configured["region"], "name": name,
                    "admin_source": {**configured["region"]["admin_source"], "code_value": code},
                }}
                Settings.model_validate(candidate)

    def test_climate_only_accepts_arco_configuration(self) -> None:
        climate = load_settings().climate.model_dump()
        for obsolete_field, value in (
            ("access_mode", "cds"),
            ("area_tile_size_deg", 0.3),
            ("max_concurrent_requests", 4),
        ):
            with self.subTest(field=obsolete_field), self.assertRaises(ValidationError):
                ClimateConfig.model_validate({**climate, obsolete_field: value})
        self.assertNotIn("--test-era5", build_arg_parser().format_help())

    def test_zero_weight_excludes_missing_metric(self) -> None:
        weights = FitnessWeights(
            weight_solar=0.6,
            weight_grid_distance=0.4,
            weight_transformer_distance=0,
        )
        candidates = pd.DataFrame({
            "solar_score": [0.8],
            "grid_proximity_score": [0.5],
            "transformer_proximity_score": [np.nan],
        })
        self.assertAlmostEqual(compute_fitness(candidates, weights).iloc[0], 0.68)
        self.assertFalse(weights.use_transformers)
        for field, column in (
            ("weight_solar", "solar_score"),
            ("weight_grid_distance", "grid_proximity_score"),
            ("weight_transformer_distance", "transformer_proximity_score"),
        ):
            with self.subTest(criterion=field):
                single = FitnessWeights(**{
                    "weight_solar": 0,
                    "weight_grid_distance": 0,
                    "weight_transformer_distance": 0,
                    field: 1,
                })
                self.assertEqual(compute_fitness(pd.DataFrame({column: [0.7]}), single).iloc[0], 0.7)
        with self.assertRaises(ValidationError):
            FitnessWeights(weight_solar=0, weight_grid_distance=0, weight_transformer_distance=0)

    def test_cache_is_scoped_by_region_and_source(self) -> None:
        with patch("src.data.cache.RawLayerCache", side_effect=lambda path: SimpleNamespace(cache_dir=path)):
            settings = load_settings()
            first = layer_cache_for_settings(settings).cache_dir
            settings.region.admin_source.code_value = "14"
            second = layer_cache_for_settings(settings).cache_dir
            settings.infrastructure.power_lines.resource_id = "another-source"
            third = layer_cache_for_settings(settings).cache_dir
            self.assertEqual(len({first, second, third}), 3)

    def test_region_name_cannot_disagree_with_code(self) -> None:
        settings = load_settings()
        settings.region.name = "Cordoba"
        settings.region.admin_source.code_value = "82"
        provinces = gpd.GeoDataFrame(
            {"NAM": ["Santa Fe"], "IN1": ["82"]},
            geometry=[box(-62, -32, -60, -30)], crs="EPSG:4326",
        )
        cache = MagicMock()
        cache.exists.return_value = False
        cache.cache_dir = Path("unused")
        with patch("src.pipeline.ingest.download_and_extract_zip", return_value=Path("unused")), \
             patch("src.pipeline.ingest.gpd.read_file", return_value=provinces):
            with self.assertRaisesRegex(DataValidationError, "no coincide"):
                ingest_region_boundary(settings, cache=cache)
        cache.save.assert_not_called()

    def test_preprocess_without_solar_or_transformers(self) -> None:
        weights = FitnessWeights(
            weight_solar=0,
            weight_grid_distance=1,
            weight_transformer_distance=0,
        )
        settings = SimpleNamespace(
            fitness=weights,
            grid=SimpleNamespace(resolution_km=9),
            region=SimpleNamespace(name="Prueba"),
            urban_exclusion=SimpleNamespace(include_types=["LOCALIDAD"], buffer_km=3),
        )
        grid_gdf = gpd.GeoDataFrame(
            {"cell_id": [1, 2], "latitude": [-30.0, -30.1], "longitude": [-61.0, -61.1]},
            geometry=[box(0, 0, 9000, 9000), box(9000, 0, 18000, 9000)],
            crs="EPSG:32720",
        )
        region = gpd.GeoDataFrame(geometry=[box(0, 0, 18000, 9000)], crs="EPSG:32720")
        urban = gpd.GeoDataFrame({"tipo": []}, geometry=[], crs="EPSG:4326")
        lines = gpd.GeoDataFrame(geometry=[LineString([(0, 0), (0, 9000)])], crs="EPSG:32720")
        transformers = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
        repo = MagicMock()
        climate_service = MagicMock()

        with patch("src.pipeline.preprocess.build_grid", return_value=SimpleNamespace(gdf=grid_gdf, projected_crs=grid_gdf.crs)):
            candidates = run_preprocessing(
                settings, repo, region, urban, lines, transformers, climate_service
            )

        climate_service.get_monthly_radiation.assert_not_called()
        repo.clear_transformers.assert_called_once()
        repo.replace_solar_radiation.assert_called_once_with([])
        self.assertTrue(candidates["solar_score"].isna().all())
        self.assertTrue(candidates["transformer_proximity_score"].isna().all())
        self.assertTrue(candidates["grid_proximity_score"].notna().all())

    def test_download_skips_disabled_sources(self) -> None:
        settings = SimpleNamespace(fitness=FitnessWeights(
            weight_solar=1, weight_grid_distance=0, weight_transformer_distance=0
        ))
        region = SimpleNamespace(gdf=object(), metadata={"source": "IGN"})
        urban = SimpleNamespace(gdf=[1, 2])
        with patch("src.main.ingest_region_boundary", return_value=region), \
             patch("src.main.ingest_urban_areas", return_value=urban), \
             patch("src.main.ingest_power_lines") as lines, \
             patch("src.main.ingest_transformers") as transformers:
            cmd_download(settings)
        lines.assert_not_called()
        transformers.assert_not_called()

    def test_optimization_storage_accepts_unused_metrics(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        data = pd.DataFrame([{
            "run_id": "test", "rank": 1, "grid_cell_id": 1,
            "latitude": -30.0, "longitude": -61.0, "solar_score": 0.9,
            "distance_to_power_line_km": np.nan,
            "distance_to_transformer_km": np.nan,
            "grid_proximity_score": np.nan,
            "transformer_proximity_score": np.nan,
            "fitness": 0.9, "created_at": pd.Timestamp("2026-01-01"),
        }])
        data.to_sql(OptimizationResult.__tablename__, engine, if_exists="append", index=False)
        stored = pd.read_sql(OptimizationResult.__tablename__, engine)
        self.assertTrue(pd.isna(stored.iloc[0]["distance_to_transformer_km"]))

    def test_map_omits_disabled_layers_and_metrics(self) -> None:
        region = gpd.GeoDataFrame(geometry=[box(-62, -31, -61, -30)], crs="EPSG:4326")
        grid = gpd.GeoDataFrame(geometry=[box(0, 0, 9000, 9000)], crs="EPSG:32720")
        empty = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
        top = pd.DataFrame([{
            "rank": 1, "grid_cell_id": 1, "latitude": -30.5, "longitude": -61.5,
            "fitness": 1.0, "solar_score": np.nan, "solar_annual_kwh_m2": np.nan,
            "grid_proximity_score": np.nan, "distance_to_power_line_km": np.nan,
            "transformer_proximity_score": np.nan, "distance_to_transformer_km": np.nan,
        }])
        rendered = []
        def capture_save(fmap, _path):
            rendered.append(fmap.get_root().render())
        with patch("folium.Map.save", autospec=True, side_effect=capture_save):
            output = Path("map.html")
            build_map(region, grid, empty, empty, empty, top, output, grid_resolution_km=9)
        html = rendered[0]
        self.assertIn("Grilla de an\\u00e1lisis (9 km)", html)
        self.assertNotIn("Centros / subestaciones transformadoras", html)
        self.assertNotIn("Líneas eléctricas (por tensión)", html)
        self.assertNotIn("Radiación anual estimada:", html)


if __name__ == "__main__":
    unittest.main()
