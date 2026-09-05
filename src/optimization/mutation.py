"""Random-resetting mutation over candidate-index encoded individuals."""

from __future__ import annotations

import numpy as np


def mutate_population(
    population: np.ndarray,
    mutation_probability: float,
    n_candidates: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """With probability `mutation_probability`, replace an individual's
    candidate index with a fresh uniformly-random one (keeps the search
    from converging prematurely on a local optimum)."""
    mutated = population.copy()
    mutate_mask = rng.random(len(population)) < mutation_probability
    n_mutations = int(mutate_mask.sum())
    if n_mutations:
        mutated[mutate_mask] = rng.integers(0, n_candidates, size=n_mutations)
    return mutated
