import numpy as np
import pandas as pd
import pytest

from src.config.settings import FitnessWeights
from src.optimization.fitness import compute_fitness, normalize_min_max


def test_normalize_min_max_basic():
    values = np.array([0.0, 5.0, 10.0])
    result = normalize_min_max(values)
    assert result[0] == pytest.approx(0.0)
    assert result[1] == pytest.approx(0.5)
    assert result[2] == pytest.approx(1.0)


def test_normalize_min_max_invert_makes_smallest_value_best():
    distances_km = np.array([0.0, 5.0, 10.0])
    proximity = normalize_min_max(distances_km, invert=True)
    assert proximity[0] == pytest.approx(1.0)  # más cerca -> mejor puntaje
    assert proximity[2] == pytest.approx(0.0)  # más lejos -> peor puntaje


def test_normalize_min_max_constant_values_returns_ones():
    values = np.array([7.0, 7.0, 7.0])
    result = normalize_min_max(values)
    assert np.all(result == 1.0)


def test_compute_fitness_weighted_sum():
    weights = FitnessWeights(weight_solar=0.5, weight_grid_distance=0.2, weight_transformer_distance=0.3)
    candidates = pd.DataFrame(
        {
            "solar_score": [1.0, 0.0],
            "grid_proximity_score": [1.0, 0.0],
            "transformer_proximity_score": [1.0, 0.0],
        }
    )
    fitness = compute_fitness(candidates, weights)
    assert fitness.iloc[0] == pytest.approx(1.0)
    assert fitness.iloc[1] == pytest.approx(0.0)


def test_compute_fitness_transformer_dominates_grid_when_scores_differ():
    weights = FitnessWeights(weight_solar=0.5, weight_grid_distance=0.2, weight_transformer_distance=0.3)
    candidates = pd.DataFrame(
        {"solar_score": [0.0], "grid_proximity_score": [1.0], "transformer_proximity_score": [1.0]}
    )
    fitness = compute_fitness(candidates, weights)
    assert fitness.iloc[0] == pytest.approx(0.5)


def test_compute_fitness_missing_column_raises():
    weights = FitnessWeights(weight_solar=0.5, weight_grid_distance=0.2, weight_transformer_distance=0.3)
    candidates = pd.DataFrame({"solar_score": [1.0]})
    with pytest.raises(ValueError):
        compute_fitness(candidates, weights)
