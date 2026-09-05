"""Fitness function: reads only pre-computed local metrics, never an API.

    fitness = weight_solar * normalized_solar
            + weight_grid_distance * normalized_grid_proximity
            + weight_transformer_distance * normalized_transformer_proximity

All three inputs are already normalized to [0, 1] (closer/more-radiation
= 1, per src/optimization/fitness.py:normalize_min_max) before this
function combines them — this module does not itself compute distances
or radiation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config.settings import FitnessWeights


def normalize_min_max(values: np.ndarray, invert: bool = False) -> np.ndarray:
    """Min-max normalize `values` to [0, 1].

    invert=False: the largest raw value maps to 1 (use for "more is
    better" metrics, e.g. solar radiation).
    invert=True: the SMALLEST raw value maps to 1 (use for "closer is
    better" metrics, e.g. distance to infrastructure — so proximity, not
    distance, is what ends up close to 1).

    If every value is identical (no discriminating information), every
    output is 1.0 — documented choice: with no basis to prefer one cell
    over another on this metric, it should not penalize any of them.
    """
    values = np.asarray(values, dtype=float)
    vmin, vmax = np.nanmin(values), np.nanmax(values)
    if np.isclose(vmax, vmin):
        return np.ones_like(values)
    normalized = (values - vmin) / (vmax - vmin)
    return 1.0 - normalized if invert else normalized


def compute_fitness(candidates: pd.DataFrame, weights: FitnessWeights) -> pd.Series:
    """Compute the weighted fitness for each row of `candidates`.

    Expects columns: solar_score, grid_proximity_score,
    transformer_proximity_score — all already normalized to [0, 1].
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
