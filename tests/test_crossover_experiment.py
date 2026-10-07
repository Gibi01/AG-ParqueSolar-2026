import unittest

import pandas as pd

from tasks.compare_crossover import paired_results, territorial_frequency
from tasks.analyze_crossover import difference_statistics, common_budget_scores


class CrossoverExperimentTests(unittest.TestCase):
    def test_decoding_budget_is_separate_from_cached_requests(self):
        history = pd.DataFrame([
            dict(seed=7, variant='con_cruce', evaluation_requests=50, decoded_individuals=3, best_historical_fitness=.5),
            dict(seed=7, variant='con_cruce', evaluation_requests=80, decoded_individuals=8, best_historical_fitness=.9),
            dict(seed=7, variant='sin_cruce', evaluation_requests=50, decoded_individuals=3, best_historical_fitness=.5),
            dict(seed=7, variant='sin_cruce', evaluation_requests=100, decoded_individuals=5, best_historical_fitness=.8),
        ])
        budget, scores = common_budget_scores(history, 'decoded_individuals')
        self.assertEqual(budget, 5)
        self.assertAlmostEqual(scores.set_index('variant').loc['con_cruce', 'best_fitness'], .5)
        request_budget, request_scores = common_budget_scores(history)
        self.assertEqual(request_budget, 80)
        self.assertAlmostEqual(request_scores.set_index('variant').loc['con_cruce', 'best_fitness'], .9)

    def test_sign_flip_and_bootstrap_for_constant_differences(self):
        stats = difference_statistics([.02, .02, .02])
        self.assertAlmostEqual(stats['mean_delta'], .02)
        self.assertEqual(stats['bootstrap_95_ci'], [.02, .02])
        self.assertAlmostEqual(stats['sign_flip_p_two_sided'], .25)

    def test_common_budget_uses_only_completed_checkpoints(self):
        history = pd.DataFrame([
            dict(seed=7, variant='con_cruce', evaluation_requests=50, best_historical_fitness=.5),
            dict(seed=7, variant='con_cruce', evaluation_requests=120, best_historical_fitness=.9),
            dict(seed=7, variant='sin_cruce', evaluation_requests=50, best_historical_fitness=.5),
            dict(seed=7, variant='sin_cruce', evaluation_requests=100, best_historical_fitness=.8),
        ])
        budget, scores = common_budget_scores(history)
        self.assertEqual(budget, 100)
        self.assertAlmostEqual(scores.set_index('variant').loc['con_cruce', 'best_fitness'], .5)
        self.assertAlmostEqual(scores.set_index('variant').loc['sin_cruce', 'best_fitness'], .8)

    def test_pairs_match_seeds_and_reject_missing_runs(self):
        rows = pd.DataFrame([
            dict(seed=7, variant='con_cruce', best_fitness=.8),
            dict(seed=42, variant='sin_cruce', best_fitness=.7),
            dict(seed=42, variant='con_cruce', best_fitness=.6),
            dict(seed=7, variant='sin_cruce', best_fitness=.5),
        ])
        pairs = paired_results(rows).set_index('seed')
        self.assertAlmostEqual(pairs.loc[7, 'delta'], .3)
        self.assertAlmostEqual(pairs.loc[42, 'delta'], -.1)
        with self.assertRaises(ValueError):
            paired_results(rows.iloc[:-1])

    def test_sector_presence_counts_runs_once_not_parks(self):
        rows = pd.DataFrame([
            dict(seed=7, variant='con_cruce', centroid_x_m=5, centroid_y_m=5),
            dict(seed=7, variant='con_cruce', centroid_x_m=10, centroid_y_m=10),
            dict(seed=42, variant='con_cruce', centroid_x_m=20, centroid_y_m=20),
            dict(seed=42, variant='con_cruce', centroid_x_m=1100, centroid_y_m=20),
        ])
        counts = territorial_frequency(rows, (0, 0), 1, 2)
        self.assertEqual(counts.iloc[0].runs, 2)
        self.assertEqual(counts.iloc[0].percent, 100)
        self.assertEqual(counts.iloc[1].runs, 1)


if __name__ == '__main__':
    unittest.main()
