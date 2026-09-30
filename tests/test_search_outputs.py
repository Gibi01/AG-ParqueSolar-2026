import tempfile
import unittest
from pathlib import Path

import pandas as pd
from shapely.geometry import box

from src.optimization.ranking import territorial_top5
from src.visualization.search_charts import write_search_charts


class SearchOutputTests(unittest.TestCase):
    def test_territorial_ranking_uses_edges_and_keeps_source_rank(self):
        candidates = pd.DataFrame([dict(rank=i+1, fitness=1-i*.01, geometry_wkt=g.wkt)
                                  for i, g in enumerate([box(0,0,10,10), box(5,0,15,10),
                                                         box(20,0,30,10), box(50,0,60,10)])])
        result = territorial_top5(candidates, separation_km=.015)
        self.assertEqual(result.general_rank.tolist(), [1,4])
        self.assertEqual(result['rank'].tolist(), [1,2])
        # Touching is not overlapping; zero additional separation allows it.
        touching = pd.DataFrame([dict(rank=i+1, fitness=1, geometry_wkt=box(i*10,0,(i+1)*10,10).wkt) for i in range(6)])
        self.assertEqual(len(territorial_top5(touching)), 5)

    def test_charts_handle_missing_mutations_and_constant_series(self):
        history = pd.DataFrame(dict(generation=[0,1], best_historical_fitness=[.5,.5],
                                    mean_fitness=[.5,.5], median_fitness=[.5,.5],
                                    unique_parks=[2,2], population_size=[2,2],
                                    mutation_effective_percent=[float('nan'),100],
                                    mean_accepted_genes=[1,1], mean_skipped_genes=[0,0],
                                    mean_unprocessed_genes=[0,0]))
        with tempfile.TemporaryDirectory() as directory:
            path = write_search_charts(history, Path(directory)/'evolution.html')
            html = path.read_text(encoding='utf-8')
        self.assertEqual(html.count('<svg '), 4)
        self.assertNotIn('nan', html.lower())
        self.assertIn('Sin reinicios', html)
