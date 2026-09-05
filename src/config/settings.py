"""Typed, validated access to config.yaml + environment variables.

This is the single source of truth for every tunable parameter in the
pipeline. Nothing here hardcodes a region: `region.name` and
`region.admin_source` fully describe how to obtain the boundary of
whatever province is configured (see README "Cambiar de provincia").
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, model_validator

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
    dataset: str
    variable: str
    years: list[int]
    months: list[int]
    point_bbox_epsilon_deg: float = Field(gt=0, lt=0.05)

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

    @field_validator("years")
    @classmethod
    def _years_plausible(cls, v: list[int]) -> list[int]:
        for y in v:
            if y < 1950 or y > 2100:
                raise ValueError(f"Invalid year {y}; ERA5-Land time-series starts in 1950.")
        return v


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

    @model_validator(mode="after")
    def _transformer_weight_dominates_line_weight(self) -> "FitnessWeights":
        if self.weight_transformer_distance < self.weight_grid_distance:
            raise ValueError(
                "weight_transformer_distance must be >= weight_grid_distance "
                "(proximity to transformers/substations must be weighted at "
                "least as much as proximity to plain power lines, per project "
                f"requirements). Got transformer={self.weight_transformer_distance} "
                f"< grid={self.weight_grid_distance}."
            )
        return self


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
    data_raw: Path
    data_processed: Path
    era5_cache: Path
    database: Path
    results: Path
    logs: Path

    @field_validator(
        "data_raw", "data_processed", "era5_cache", "database", "results", "logs", mode="before"
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

    # Not part of config.yaml — loaded from the environment, never from the
    # repository, and never given a literal default value here.
    cds_api_key: Optional[str] = None
    cds_api_url: Optional[str] = None

    def ensure_directories(self) -> None:
        for p in (
            self.paths.data_raw,
            self.paths.data_processed,
            self.paths.era5_cache,
            self.paths.database.parent,
            self.paths.results,
            self.paths.logs,
        ):
            p.mkdir(parents=True, exist_ok=True)


def load_settings(config_path: str | Path = "config.yaml") -> Settings:
    """Load and validate configuration from YAML + environment variables.

    The CDS API key is deliberately never read from config.yaml: it is
    read from the process environment (populated from `.env` via
    python-dotenv, or from a real environment variable / CI secret).
    """
    config_path = Path(config_path)
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path

    load_dotenv(PROJECT_ROOT / ".env", override=False)

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    settings = Settings.model_validate(raw)
    settings.cds_api_key = os.environ.get("CDS_API_KEY") or None
    settings.cds_api_url = os.environ.get("CDS_API_URL") or "https://cds.climate.copernicus.eu/api"
    return settings
