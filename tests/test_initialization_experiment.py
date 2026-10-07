import unittest
from types import SimpleNamespace

import numpy as np
import pandas as pd

from src.optimization.initialization import TerritorialSampler
from tasks.compare_initialization import UniformInitialSampler, fast_difference_statistics
from tasks.analyze_crossover import difference_statistics
from tasks.analyze_initialization import factorial_differences


class InitializationExperimentTests(unittest.TestCase):
    def evaluator(self):
        return SimpleNamespace(seed_ids=np.arange(12), positions={i: i for i in range(12)},
            x=np.arange(12) * 1000., y=np.zeros(12), area=np.ones(12),
            config=SimpleNamespace(max_connection_capacity_mw=5, pv_power_density_mw_per_km2=1))

    def test_uniform_initial_can_repeat_sectors_then_uses_territorial_cycles(self):
        ev = self.evaluator()
        sampler = UniformInitialSampler(ev, np.random.default_rng(42), 1, initial_count=50)
        initial = [sampler.individual() for _ in range(50)]
        self.assertLess(len({p.seed_cell_id for p in initial[:12]}), 12)
        self.assertTrue(all(p.seed_cell_id in ev.seed_ids for p in initial))
        self.assertEqual(len({sampler.next_seed() for _ in range(12)}), 12)
        self.assertEqual(len({sampler.next_seed() for _ in range(12)}), 12)

    def test_zero_initial_count_matches_territorial_and_uniform_is_reproducible(self):
        ev = self.evaluator()
        standard = TerritorialSampler(ev, np.random.default_rng(17), 1)
        zero = UniformInitialSampler(ev, np.random.default_rng(17), 1, initial_count=0)
        self.assertEqual([standard.individual() for _ in range(30)], [zero.individual() for _ in range(30)])
        a = UniformInitialSampler(ev, np.random.default_rng(17), 1, initial_count=10)
        b = UniformInitialSampler(ev, np.random.default_rng(17), 1, initial_count=10)
        self.assertEqual([a.individual() for _ in range(30)], [b.individual() for _ in range(30)])

    def test_vectorized_statistics_match_reference_including_zero_and_ties(self):
        for delta in ([.01, .02, -.02, 0], [.02] * 3, [0.] * 5):
            actual = fast_difference_statistics(delta)
            expected = difference_statistics(delta)
            self.assertEqual(actual, expected)

    def test_interaction_compares_crossover_effect_not_just_final_scores(self):
        rows = pd.DataFrame([
            dict(seed=1, initialization='territorial', variant='con_cruce', best_fitness=.8),
            dict(seed=1, initialization='territorial', variant='sin_cruce', best_fitness=.7),
            dict(seed=1, initialization='uniforme', variant='con_cruce', best_fitness=.9),
            dict(seed=1, initialization='uniforme', variant='sin_cruce', best_fitness=.85),
        ])
        result = factorial_differences(rows)
        self.assertAlmostEqual(result.loc[1, 'interaction'], -.05)
        with self.assertRaises(ValueError):
            factorial_differences(rows.iloc[:-1])
        mismatched = rows.copy()
        mismatched.loc[mismatched.initialization == 'uniforme', 'seed'] = 2
        with self.assertRaises(ValueError):
            factorial_differences(mismatched)


if __name__ == '__main__':
    unittest.main()
