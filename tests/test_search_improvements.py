import unittest

import numpy as np

from test_spatial_growth import example_evaluator
from src.config.settings import GeneticAlgorithmConfig
from src.optimization.genetic_algorithm import GeneticAlgorithm
from src.optimization.spatial import Individual
from src.optimization.mutation import mutate_effectively
from src.optimization.initialization import TerritorialSampler


class SearchImprovementsTests(unittest.TestCase):
    def test_territories_are_visited_without_repetition_before_next_cycle(self):
        sampler = TerritorialSampler(example_evaluator(20), np.random.default_rng(42), .1)
        seeds = [sampler.next_seed() for _ in range(3)]
        self.assertEqual(set(seeds), {1, 2, 3})

    def test_stop_when_no_frontier_cell_fits_preserves_partial_growth(self):
        evaluator = example_evaluator(10)
        park = evaluator.evaluate(Individual(1, (0, 1) + (0,) * 1000))
        self.assertEqual(park.cell_ids, (1, 3))
        self.assertEqual(park.accepted_gene_indices, (1,))
        self.assertEqual(park.skipped_gene_indices, (0,))
        self.assertEqual(park.unprocessed_genes, 1000)

    def test_effective_mutation_changes_phenotype_with_bounded_attempts(self):
        evaluator = example_evaluator(10)
        original = Individual(1, (0, 1) + (0,) * 100)
        for seed in range(10):
            child, attempts, changed = mutate_effectively(original, evaluator, np.random.default_rng(seed), 4)
            self.assertLessEqual(attempts, 4)
            self.assertEqual(changed, evaluator.evaluate(child).cell_ids != evaluator.evaluate(original).cell_ids)
            self.assertTrue(changed)

    def test_small_search_space_terminates_and_exports_top5_metrics(self):
        config = GeneticAlgorithmConfig(population_size=12, generations=3, crossover_probability=.75,
                                        mutation_probability=.8, elitism=2, tournament_size=3, random_seed=42)
        first = GeneticAlgorithm(example_evaluator(20), config).run()
        second = GeneticAlgorithm(example_evaluator(20), config).run()
        self.assertEqual(first.top5.to_json(), second.top5.to_json())
        self.assertLessEqual(len(first.top5), 5)
        self.assertTrue(first.history.best_fitness.diff().dropna().ge(-1e-12).all())
        self.assertTrue(first.history.population_size.eq(12).all())
        self.assertGreater(first.history.duplicate_fallbacks.sum(), 0)
        self.assertTrue(first.history.evaluation_requests.is_monotonic_increasing)
        self.assertIn('mutation_effective_percent', first.history)


if __name__ == '__main__':
    unittest.main()
