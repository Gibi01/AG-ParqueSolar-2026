import unittest
from unittest.mock import patch
import numpy as np

from test_spatial_growth import example_evaluator
from src.config.settings import GeneticAlgorithmConfig
from src.optimization.genetic_algorithm import GeneticAlgorithm
from src.optimization.spatial import Individual
from src.optimization.crossover import crossover_pair
from src.optimization.mutation import mutate_individual


class SpatialGATests(unittest.TestCase):
    def test_history_records_population_fitness_standard_deviation(self):
        evaluator = example_evaluator(20)
        population = [Individual(1, ()), Individual(2, ()), Individual(3, ())]
        fitness = [evaluator.evaluate(i).metrics['fitness'] for i in population]
        config = GeneticAlgorithmConfig(population_size=3, generations=1, elitism=1,
                                        tournament_size=2, random_seed=42,
                                        crossover_probability=0, mutation_probability=0)
        with patch('src.optimization.genetic_algorithm.TerritorialSampler.individual',
                   side_effect=population + [population[0]] * 100):
            result = GeneticAlgorithm(evaluator, config).run()
        self.assertAlmostEqual(result.history.iloc[0].std_fitness, np.std(fitness, ddof=0))
        self.assertTrue(result.history.std_fitness.ge(0).all())

    def test_generated_seed_is_recorded_and_replayable(self):
        config = GeneticAlgorithmConfig(population_size=8, generations=3, crossover_probability=.75,
                                        mutation_probability=.2, elitism=2, tournament_size=3, random_seed=None)
        first = GeneticAlgorithm(example_evaluator(20), config).run()
        config.random_seed = first.random_seed
        second = GeneticAlgorithm(example_evaluator(20), config).run()
        self.assertEqual(first.top10.to_json(), second.top10.to_json())

    def test_repeatable_ga_and_unique_phenotypes(self):
        config = GeneticAlgorithmConfig(population_size=12, generations=8, crossover_probability=.75,
                                        mutation_probability=.8, elitism=2, tournament_size=3, random_seed=42)
        first = GeneticAlgorithm(example_evaluator(20), config).run()
        second = GeneticAlgorithm(example_evaluator(20), config).run()
        self.assertEqual(first.top10.to_json(), second.top10.to_json())
        self.assertEqual(first.top10.cell_ids.nunique(), len(first.top10))
        self.assertTrue((first.top10.installed_power_mw <= 20).all())

    def test_crossover_keeps_prefix_seed_and_parents(self):
        a, b = Individual(1, (1, 2, 3)), Individual(3, (4,))
        children = crossover_pair(a, b, np.random.default_rng(3))
        self.assertEqual([c.seed_cell_id for c in children], [1, 3])
        self.assertEqual(a.growth_genes, (1, 2, 3))

    def test_mutations_can_grow_shrink_move_and_change_shape(self):
        individual = Individual(1, (1, 2, 3))
        rng = np.random.default_rng(12)
        results = [mutate_individual(individual, np.array([1, 2, 3]), rng) for _ in range(100)]
        self.assertTrue(any(len(c.growth_genes) == 2 for c in results))
        self.assertTrue(any(len(c.growth_genes) == 4 for c in results))
        self.assertTrue(any(c.seed_cell_id != 1 for c in results))
        self.assertTrue(any(len(c.growth_genes) == 3 and c.growth_genes != individual.growth_genes for c in results))
