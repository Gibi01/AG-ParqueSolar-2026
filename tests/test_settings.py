import pytest
from pydantic import ValidationError as PydanticValidationError

from src.config.settings import ClimateConfig, FitnessWeights, GeneticAlgorithmConfig


def test_climate_config_rejects_wrong_dataset():
    with pytest.raises(PydanticValidationError):
        ClimateConfig(
            dataset="reanalysis-era5-single-levels",  # forbidden substitute
            variable="surface_solar_radiation_downwards",
            years=[2024],
            months=[1, 4, 7, 10],
            point_bbox_epsilon_deg=0.001,
        )


def test_climate_config_accepts_required_dataset():
    cfg = ClimateConfig(
        dataset="reanalysis-era5-land-timeseries",
        variable="surface_solar_radiation_downwards",
        years=[2024],
        months=[1, 4, 7, 10],
        point_bbox_epsilon_deg=0.001,
    )
    assert cfg.dataset == "reanalysis-era5-land-timeseries"


def test_climate_config_rejects_invalid_month():
    with pytest.raises(PydanticValidationError):
        ClimateConfig(
            dataset="reanalysis-era5-land-timeseries",
            variable="surface_solar_radiation_downwards",
            years=[2024],
            months=[13],
            point_bbox_epsilon_deg=0.001,
        )


def test_fitness_weights_must_sum_to_one():
    with pytest.raises(PydanticValidationError):
        FitnessWeights(weight_solar=0.5, weight_grid_distance=0.2, weight_transformer_distance=0.2)


def test_fitness_weights_valid_combination():
    w = FitnessWeights(weight_solar=0.5, weight_grid_distance=0.2, weight_transformer_distance=0.3)
    assert w.weight_transformer_distance >= w.weight_grid_distance


def test_transformer_weight_must_not_be_below_grid_weight():
    with pytest.raises(PydanticValidationError):
        FitnessWeights(weight_solar=0.5, weight_grid_distance=0.3, weight_transformer_distance=0.2)


def test_ga_elitism_must_be_smaller_than_population():
    with pytest.raises(PydanticValidationError):
        GeneticAlgorithmConfig(
            population_size=10,
            generations=5,
            crossover_probability=0.7,
            mutation_probability=0.05,
            elitism=10,
            tournament_size=3,
        )


def test_ga_valid_config():
    cfg = GeneticAlgorithmConfig(
        population_size=50,
        generations=100,
        crossover_probability=0.75,
        mutation_probability=0.05,
        elitism=2,
        tournament_size=3,
        random_seed=42,
    )
    assert cfg.population_size == 50
