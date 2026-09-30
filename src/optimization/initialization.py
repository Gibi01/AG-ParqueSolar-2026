"""Balanced random sampling of occupied projected-coordinate territories."""
import numpy as np

from src.optimization.spatial import Individual
from src.optimization.mutation import random_gene


class TerritorialSampler:
    def __init__(self, evaluator, rng, size_km):
        self.evaluator, self.rng = evaluator, rng
        self.size_m = size_km * 1000
        self.origin = (float(evaluator.x.min()), float(evaluator.y.min()))
        self.groups = {}
        for cid in evaluator.seed_ids:
            i = evaluator.positions[int(cid)]
            key = self.territory(evaluator.x[i], evaluator.y[i])
            self.groups.setdefault(key, []).append(int(cid))
        self.keys = sorted(self.groups)
        self.pending = []
        self.typical = max(1, int(evaluator.config.max_connection_capacity_mw /
                                 (np.median(evaluator.area) * evaluator.config.pv_power_density_mw_per_km2)))

    def territory(self, x, y):
        return (int((x - self.origin[0]) // self.size_m), int((y - self.origin[1]) // self.size_m))

    def next_seed(self):
        if not self.pending:
            self.pending = self.rng.permutation(len(self.keys)).tolist()
        return int(self.rng.choice(self.groups[self.keys[self.pending.pop()]]))

    def individual(self):
        seed = self.next_seed()
        return Individual(seed, tuple(random_gene(self.rng) for _ in range(int(self.rng.integers(self.typical + 1)))))
