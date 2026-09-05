import numpy as np
import pandas as pd
import pytest

from src.config.settings import FitnessWeights, GeneticAlgorithmConfig
from src.optimization.crossover import crossover_population
from src.optimization.genetic_algorithm import GeneticAlgorithm
from src.optimization.mutation import mutate_population
from src.optimization.selection import tournament_selection


def _candidates_with_one_clear_winner(n=20) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    df = pd.DataFrame(
        {
            "grid_cell_id": np.arange(1, n + 1),
            "latitude": rng.uniform(-33, -32, n),
            "longitude": rng.uniform(-61, -60, n),
            "solar_score": rng.uniform(0, 0.5, n),
            "grid_proximity_score": rng.uniform(0, 0.5, n),
            "transformer_proximity_score": rng.uniform(0, 0.5, n),
        }
    )
    # la celda 0 domina claramente todas las métricas
    df.loc[0, ["solar_score", "grid_proximity_score", "transformer_proximity_score"]] = [1.0, 1.0, 1.0]
    return df


def test_ga_converges_to_the_dominant_candidate():
    weights = FitnessWeights(weight_solar=0.5, weight_grid_distance=0.2, weight_transformer_distance=0.3)
    config = GeneticAlgorithmConfig(
        population_size=20,
        generations=30,
        crossover_probability=0.75,
        mutation_probability=0.05,
        elitism=2,
        tournament_size=3,
        random_seed=42,
    )
    candidates = _candidates_with_one_clear_winner()
    ga = GeneticAlgorithm(candidates, weights, config)
    result = ga.run(top_n=10)

    assert result.top10.iloc[0]["grid_cell_id"] == 1  # cell_id del índice 0
    assert result.top10.iloc[0]["fitness"] == pytest.approx(1.0)
    assert result.history["best_fitness"].iloc[-1] == pytest.approx(1.0)


def test_ga_top10_is_sorted_descending_by_fitness():
    weights = FitnessWeights(weight_solar=0.5, weight_grid_distance=0.2, weight_transformer_distance=0.3)
    config = GeneticAlgorithmConfig(
        population_size=15,
        generations=10,
        crossover_probability=0.75,
        mutation_probability=0.1,
        elitism=1,
        tournament_size=3,
        random_seed=1,
    )
    candidates = _candidates_with_one_clear_winner(n=30)
    ga = GeneticAlgorithm(candidates, weights, config)
    result = ga.run(top_n=10)
    fitness_values = result.top10["fitness"].to_numpy()
    assert np.all(np.diff(fitness_values) <= 1e-12)  # no creciente


def test_ga_rejects_empty_candidates():
    weights = FitnessWeights(weight_solar=0.5, weight_grid_distance=0.2, weight_transformer_distance=0.3)
    config = GeneticAlgorithmConfig(
        population_size=10, generations=5, crossover_probability=0.7, mutation_probability=0.05, elitism=1, tournament_size=2
    )
    with pytest.raises(ValueError):
        GeneticAlgorithm(pd.DataFrame(columns=["solar_score", "grid_proximity_score", "transformer_proximity_score"]), weights, config)


def test_tournament_selection_always_picks_from_current_population():
    rng = np.random.default_rng(0)
    population = np.array([2, 5, 7, 9])
    fitness_lookup = np.array([0.1, 0.9, 0.2, 0.05, 0.3, 0.99, 0.4, 0.5, 0.6, 0.01])
    selected = tournament_selection(population, fitness_lookup, tournament_size=2, num_to_select=10, rng=rng)
    assert set(selected).issubset(set(population))


def test_mutate_population_respects_probability_zero():
    rng = np.random.default_rng(0)
    population = np.array([1, 2, 3, 4, 5])
    mutated = mutate_population(population, mutation_probability=0.0, n_candidates=100, rng=rng)
    assert np.array_equal(mutated, population)


def test_crossover_population_respects_probability_zero():
    rng = np.random.default_rng(0)
    population = np.array([1, 2, 3, 4])
    children = crossover_population(population, crossover_probability=0.0, n_candidates=100, rng=rng)
    assert np.array_equal(children, population)


def test_crossover_children_within_valid_range():
    rng = np.random.default_rng(0)
    population = np.array([0, 99, 50, 10])
    children = crossover_population(population, crossover_probability=1.0, n_candidates=100, rng=rng)
    assert np.all((children >= 0) & (children < 100))
