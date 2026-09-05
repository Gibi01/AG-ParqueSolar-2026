"""Mutación por reinicio aleatorio sobre individuos codificados como índice de candidato."""

from __future__ import annotations

import numpy as np


def mutate_population(
    population: np.ndarray,
    mutation_probability: float,
    n_candidates: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Con probabilidad `mutation_probability`, reemplaza el índice de
    candidato de un individuo por uno nuevo uniformemente aleatorio
    (evita que la búsqueda converja prematuramente a un óptimo local)."""
    mutated = population.copy()
    mutate_mask = rng.random(len(population)) < mutation_probability
    n_mutations = int(mutate_mask.sum())
    if n_mutations:
        mutated[mutate_mask] = rng.integers(0, n_candidates, size=n_mutations)
    return mutated
