"""Primitivas de validación reutilizables.

Se usan tanto en el pipeline (chequeos previos antes de que se permita
correr el AG — Fase 32 de los requisitos) como en los tests unitarios.
Cada validador lanza `ValidationError` con un mensaje lo bastante
específico para diagnosticar el problema sin tener que releer el código fuente.
"""

from __future__ import annotations

from typing import Iterable

import geopandas as gpd
import pandas as pd


class ValidationError(ValueError):
    pass


def validate_crs_is_set(gdf: gpd.GeoDataFrame, label: str) -> None:
    if gdf.crs is None:
        raise ValidationError(f"{label}: GeoDataFrame has no CRS set.")


def validate_geometries_valid(gdf: gpd.GeoDataFrame, label: str) -> None:
    invalid = ~gdf.geometry.is_valid
    if invalid.any():
        raise ValidationError(
            f"{label}: {int(invalid.sum())} of {len(gdf)} geometries are invalid "
            "(self-intersections or similar). Fix upstream before proceeding."
        )


def validate_no_empty_geometries(gdf: gpd.GeoDataFrame, label: str) -> None:
    empty = gdf.geometry.is_empty | gdf.geometry.isna()
    if empty.any():
        raise ValidationError(f"{label}: {int(empty.sum())} of {len(gdf)} geometries are empty/null.")


def validate_no_nulls(df: pd.DataFrame, columns: Iterable[str], label: str) -> None:
    missing_cols = [c for c in columns if c not in df.columns]
    if missing_cols:
        raise ValidationError(f"{label}: missing expected column(s) {missing_cols}.")
    for col in columns:
        n_null = df[col].isna().sum()
        if n_null:
            raise ValidationError(f"{label}: column '{col}' has {n_null} null value(s) out of {len(df)}.")


def validate_not_empty(gdf_or_df, label: str) -> None:
    if len(gdf_or_df) == 0:
        raise ValidationError(f"{label}: dataset is empty.")


def validate_layer_present(gdf: gpd.GeoDataFrame | None, label: str) -> None:
    """Falla si falta una capa correspondiente a un criterio activo."""
    if gdf is None or len(gdf) == 0:
        raise ValidationError(
            f"{label}: la capa activa está vacía. Configurá una fuente válida "
            "o poné el peso del criterio en 0 para desactivarlo."
        )
