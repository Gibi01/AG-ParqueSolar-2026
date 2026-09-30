"""Sequence crossover: each child keeps the seed associated with its prefix."""
from src.optimization.spatial import Individual


def crossover_pair(a, b, rng):
    cut_a = int(rng.integers(len(a.growth_genes) + 1))
    cut_b = int(rng.integers(len(b.growth_genes) + 1))
    return (Individual(a.seed_cell_id, a.growth_genes[:cut_a] + b.growth_genes[cut_b:]),
            Individual(b.seed_cell_id, b.growth_genes[:cut_b] + a.growth_genes[cut_a:]))
