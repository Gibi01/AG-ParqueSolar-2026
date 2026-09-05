"""Función de fitness: solo lee métricas locales precalculadas, nunca una API.

    fitness = weight_solar * normalized_solar
            + weight_grid_distance * normalized_grid_proximity
            + weight_transformer_distance * normalized_transformer_proximity

Las tres entradas ya están normalizadas a [0, 1] (más cerca/más radiación
= 1, según src/optimization/fitness.py:normalize_min_max) antes de que
esta función las combine — este módulo no calcula distancias ni radiación
por sí mismo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config.settings import FitnessWeights


def normalize_min_max(values: np.ndarray, invert: bool = False) -> np.ndarray:
    """Normaliza `values` a [0, 1] usando min-max.

    invert=False: el valor crudo más grande mapea a 1 (usar para métricas
    "más es mejor", p. ej. radiación solar).
    invert=True: el valor crudo MÁS CHICO mapea a 1 (usar para métricas
    "más cerca es mejor", p. ej. distancia a infraestructura — así que lo
    que termina cerca de 1 es la proximidad, no la distancia).

    Si todos los valores son idénticos (no hay información discriminante),
    toda salida es 1.0 — decisión documentada: sin ninguna base para
    preferir una celda sobre otra en esta métrica, no debería penalizar a ninguna.
    """
    values = np.asarray(values, dtype=float)
    vmin, vmax = np.nanmin(values), np.nanmax(values)
    if np.isclose(vmax, vmin):
        return np.ones_like(values)
    normalized = (values - vmin) / (vmax - vmin)
    return 1.0 - normalized if invert else normalized


def compute_fitness(candidates: pd.DataFrame, weights: FitnessWeights) -> pd.Series:
    """Calcula el fitness ponderado para cada fila de `candidates`.

    Espera las columnas: solar_score, grid_proximity_score,
    transformer_proximity_score — todas ya normalizadas a [0, 1].
    """
    required = ["solar_score", "grid_proximity_score", "transformer_proximity_score"]
    missing = [c for c in required if c not in candidates.columns]
    if missing:
        raise ValueError(f"candidates is missing required column(s): {missing}")

    return (
        weights.weight_solar * candidates["solar_score"]
        + weights.weight_grid_distance * candidates["grid_proximity_score"]
        + weights.weight_transformer_distance * candidates["transformer_proximity_score"]
    )
