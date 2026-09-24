"""Acceso tipado y validado a config.yaml + variables de entorno.

Esta es la única fuente de verdad para los parámetros configurables del
pipeline. La implementación espacial conserva la estructura de región,
pero esta versión solo admite Santa Fe y valida esa restricción al cargar.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_ERA5_DATASET = "reanalysis-era5-land-timeseries"
REQUIRED_ERA5_VARIABLE = "surface_solar_radiation_downwards"


class RegionAdminSource(BaseModel):
    provider: str
    shapefile_zip_url: str
    shapefile_member: str
    name_field: str
    code_field: str
    code_value: str
    native_crs: str


class RegionConfig(BaseModel):
    name: str
    admin_source: RegionAdminSource

    @model_validator(mode="after")
    def _only_santa_fe(self) -> "RegionConfig":
        if self.name != "Santa Fe" or self.admin_source.code_value != "82":
            raise ValueError(
                "Esta versión solo admite Santa Fe: usá "
                "region.name='Santa Fe' y region.admin_source.code_value='82'."
            )
        return self


class GridConfig(BaseModel):
    resolution_km: float = Field(gt=0)


class ParkConfig(BaseModel):
    area_hectares: float = Field(gt=0)

    @property
    def area_m2(self) -> float:
        return self.area_hectares * 10_000.0

    @property
    def area_km2(self) -> float:
        return self.area_hectares / 100.0


class UrbanExclusionConfig(BaseModel):
    buffer_km: float = Field(ge=0)
    include_types: list[str] = Field(min_length=1)


class ClimateConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset: str
    variable: str
    start_year: int = Field(ge=1950)
    end_year: int | str = "latest"
    months: list[int]

    @field_validator("dataset")
    @classmethod
    def _dataset_must_be_timeseries(cls, v: str) -> str:
        if v != REQUIRED_ERA5_DATASET:
            raise ValueError(
                f"climate.dataset must be '{REQUIRED_ERA5_DATASET}' "
                f"(ERA5-Land hourly time-series / ARCO dataset). Got '{v}'. "
                "The project requirements explicitly forbid substituting "
                "plain ERA5, ERA5-Land monthly averages, or the bulk "
                "ERA5-Land hourly archive unless technically justified "
                "and this check is deliberately updated."
            )
        return v

    @field_validator("variable")
    @classmethod
    def _variable_must_be_ssrd(cls, v: str) -> str:
        if v != REQUIRED_ERA5_VARIABLE:
            raise ValueError(
                f"climate.variable must be '{REQUIRED_ERA5_VARIABLE}' for this MVP. Got '{v}'."
            )
        return v

    @field_validator("months")
    @classmethod
    def _months_in_range(cls, v: list[int]) -> list[int]:
        for m in v:
            if not (1 <= m <= 12):
                raise ValueError(f"Invalid month {m}; must be 1-12.")
        return v

    @model_validator(mode="after")
    def _validate_period(self) -> "ClimateConfig":
        if self.end_year != "latest" and (not isinstance(self.end_year, int) or self.end_year < self.start_year):
            raise ValueError("climate.end_year must be 'latest' or an integer >= start_year")
        if len(set(self.months)) != len(self.months) or not self.months:
            raise ValueError("climate.months must contain distinct representative months")
        if set(self.months) != {1, 4, 7, 10}:
            raise ValueError("climate.months must contain January, April, July and October for the annual estimate")
        return self

    @property
    def year_months(self) -> list[tuple[int, int]]:
        """Meses completos, con un mes de margen para la publicación de datos."""
        now = datetime.now(timezone.utc)
        cutoff_year, cutoff_month = now.year, now.month - 2
        if cutoff_month <= 0:
            cutoff_year -= 1
            cutoff_month += 12
        last_year = cutoff_year if self.end_year == "latest" else min(self.end_year, cutoff_year)
        return [
            (year, month)
            for year in range(self.start_year, last_year + 1)
            for month in self.months
            if (year, month) <= (cutoff_year, cutoff_month)
        ]

    @property
    def years(self) -> list[int]:
        return sorted({year for year, _ in self.year_months})


class UrbanAreasSource(BaseModel):
    resource_id: str


class PowerLinesSource(BaseModel):
    resource_id: str


class TransformersSource(BaseModel):
    source_url: str
    native_crs: str


class InfrastructureConfig(BaseModel):
    urban_areas: UrbanAreasSource
    power_lines: PowerLinesSource
    transformers: TransformersSource


class FitnessWeights(BaseModel):
    weight_solar: float = Field(ge=0, le=1)
    weight_grid_distance: float = Field(ge=0, le=1)
    weight_transformer_distance: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def _weights_sum_to_one(self) -> "FitnessWeights":
        total = self.weight_solar + self.weight_grid_distance + self.weight_transformer_distance
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                "fitness weights must sum to 1.0 "
                f"(got weight_solar={self.weight_solar} + "
                f"weight_grid_distance={self.weight_grid_distance} + "
                f"weight_transformer_distance={self.weight_transformer_distance} = {total})"
            )
        return self


    @property
    def use_solar(self) -> bool:
        return self.weight_solar > 0

    @property
    def use_power_lines(self) -> bool:
        return self.weight_grid_distance > 0

    @property
    def use_transformers(self) -> bool:
        return self.weight_transformer_distance > 0


class GeneticAlgorithmConfig(BaseModel):
    population_size: int = Field(gt=0)
    generations: int = Field(gt=0)
    crossover_probability: float = Field(ge=0, le=1)
    mutation_probability: float = Field(ge=0, le=1)
    elitism: int = Field(ge=0)
    tournament_size: int = Field(ge=2)
    random_seed: Optional[int] = None

    @model_validator(mode="after")
    def _elitism_smaller_than_population(self) -> "GeneticAlgorithmConfig":
        if self.elitism >= self.population_size:
            raise ValueError(
                f"genetic_algorithm.elitism ({self.elitism}) must be smaller than "
                f"population_size ({self.population_size})."
            )
        if self.tournament_size > self.population_size:
            raise ValueError(
                f"genetic_algorithm.tournament_size ({self.tournament_size}) cannot "
                f"exceed population_size ({self.population_size})."
            )
        return self


class PathsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data_raw: Path
    data_processed: Path
    arco_cache: Path
    database: Path
    results: Path
    logs: Path

    @field_validator(
        "data_raw", "data_processed", "arco_cache", "database", "results", "logs", mode="before"
    )
    @classmethod
    def _resolve_relative_to_root(cls, v: str) -> Path:
        p = Path(v)
        return p if p.is_absolute() else (PROJECT_ROOT / p)


class Settings(BaseModel):
    region: RegionConfig
    grid: GridConfig
    park: ParkConfig
    urban_exclusion: UrbanExclusionConfig
    climate: ClimateConfig
    infrastructure: InfrastructureConfig
    fitness: FitnessWeights
    genetic_algorithm: GeneticAlgorithmConfig
    paths: PathsConfig

    # Token usado por ARCO; se conserva el nombre de variable CDS_API_KEY
    # para compatibilidad con los archivos .env existentes.
    cds_api_key: Optional[str] = None

    def ensure_directories(self) -> None:
        for p in (
            self.paths.data_raw,
            self.paths.data_processed,
            self.paths.arco_cache,
            self.paths.database.parent,
            self.paths.results,
            self.paths.logs,
        ):
            p.mkdir(parents=True, exist_ok=True)


def load_settings(config_path: str | Path = "config.yaml") -> Settings:
    """Carga y valida la configuración desde YAML + variables de entorno.

    La credencial de ARCO deliberadamente nunca se lee de config.yaml:
    se lee del entorno del proceso (poblado desde `.env` vía python-dotenv,
    o desde una variable de entorno real / secreto de CI).
    """
    config_path = Path(config_path)
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path

    load_dotenv(PROJECT_ROOT / ".env", override=False)

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    settings = Settings.model_validate(raw)
    settings.cds_api_key = os.environ.get("CDS_API_KEY") or None
    return settings
