"""Blend (arithmetic) crossover over candidate-index encoded individuals.

Each individual is a single integer gene (its position in the candidate
locations array), so classic multi-gene crossover doesn't apply. Instead
this uses real-coded/arithmetic blend crossover — standard for
single-variable GAs — producing two offspring whose index lies on the
line between the two parents' indices, then rounds and clips back into
the valid range.
"""

from __future__ import annotations

import numpy as np


def blend_crossover_pair(
    parent_a: int, parent_b: int, n_candidates: int, rng: np.random.Generator
) -> tuple[int, int]:
    alpha = rng.random()
    child1 = int(round(alpha * parent_a + (1 - alpha) * parent_b))
    child2 = int(round(alpha * parent_b + (1 - alpha) * parent_a))
    child1 = min(max(child1, 0), n_candidates - 1)
    child2 = min(max(child2, 0), n_candidates - 1)
    return child1, child2


def crossover_population(
    parents: np.ndarray,
    crossover_probability: float,
    n_candidates: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Pair up consecutive parents and apply blend crossover with
    probability `crossover_probability`; unpaired/skipped individuals
    pass through unchanged."""
    children = parents.copy()
    for i in range(0, len(parents) - 1, 2):
        if rng.random() < crossover_probability:
            c1, c2 = blend_crossover_pair(int(parents[i]), int(parents[i + 1]), n_candidates, rng)
            children[i], children[i + 1] = c1, c2
    return children
