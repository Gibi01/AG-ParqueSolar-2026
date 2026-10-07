import unittest

import numpy as np

from test_spatial_growth import example_evaluator
from src.optimization.crossover import competitive_crossover_pair
from src.optimization.spatial import Individual


class CompetitiveCrossoverTests(unittest.TestCase):
    def test_rejects_a_recombination_that_degrades_the_parent(self):
        evaluator = example_evaluator(20)
        a, b = Individual(2, ()), Individual(1, (0,))
        children = competitive_crossover_pair(a, b, np.random.default_rng(3), evaluator)
        self.assertEqual(children[0], a)
        self.assertEqual(evaluator.evaluate(children[0]).metrics['fitness'], evaluator.evaluate(a).metrics['fitness'])

    def test_children_never_worse_than_corresponding_parents_and_replay(self):
        evaluator = example_evaluator(20)
        a, b = Individual(1, (0, 7, 99)), Individual(3, (0,))
        for seed in range(30):
            first = competitive_crossover_pair(a, b, np.random.default_rng(seed), evaluator)
            second = competitive_crossover_pair(a, b, np.random.default_rng(seed), evaluator)
            self.assertEqual(first, second)
            for child, parent in zip(first, (a, b)):
                self.assertEqual(child.seed_cell_id, parent.seed_cell_id)
                self.assertGreaterEqual(evaluator.evaluate(child).metrics['fitness'], evaluator.evaluate(parent).metrics['fitness'])
                self.assertLessEqual(evaluator.evaluate(child).metrics['installed_power_mw'], 20)
        self.assertEqual(a.growth_genes, (0, 7, 99))
        self.assertEqual(b.growth_genes, (0,))

    def test_recombination_can_improve_a_parent_without_mutation(self):
        evaluator = example_evaluator(20)
        a, b = Individual(1, ()), Individual(3, (0,))
        children = competitive_crossover_pair(a, b, np.random.default_rng(1), evaluator)
        self.assertGreater(evaluator.evaluate(children[0]).metrics['fitness'], evaluator.evaluate(a).metrics['fitness'])
        self.assertEqual(evaluator.evaluate(children[0]).cell_ids, (1, 2))

    def test_empty_parents_and_capacity_stop_are_valid(self):
        evaluator = example_evaluator(10)
        a, b = Individual(1, (0, 1, 7, 99)), Individual(3, ())
        children = competitive_crossover_pair(a, b, np.random.default_rng(4), evaluator)
        for child, parent in zip(children, (a, b)):
            self.assertEqual(evaluator.evaluate(child).cell_ids, evaluator.evaluate(parent).cell_ids)
            self.assertEqual(len(child.growth_genes), len(evaluator.evaluate(child).accepted_gene_indices))


if __name__ == '__main__':
    unittest.main()
