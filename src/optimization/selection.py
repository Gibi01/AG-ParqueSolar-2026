"""Tournament selection.

Individuals are represented as integer indices into the (fixed) array of
valid candidate locations — see genetic_algorithm.py for why.
"""

from __future__ import annotations

import numpy as np


def tournament_selection(
    population: np.ndarray,
    fitness_lookup: np.ndarray,
    tournament_size: int,
    num_to_select: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Select `num_to_select` individuals from `population` via tournaments.

    Each tournament samples `tournament_size` members (with replacement)
    from the current population and keeps the fittest.
    """
    pop_size = len(population)
    selected = np.empty(num_to_select, dtype=population.dtype)
    for i in range(num_to_select):
        contender_positions = rng.integers(0, pop_size, size=tournament_size)
        contenders = population[contender_positions]
        contender_fitness = fitness_lookup[contenders]
        selected[i] = contenders[np.argmax(contender_fitness)]
    return selected
