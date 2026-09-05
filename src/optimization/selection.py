"""Selección por torneo.

Los individuos se representan como índices enteros dentro del arreglo
(fijo) de ubicaciones candidatas válidas — ver genetic_algorithm.py para saber por qué.
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
    """Selecciona `num_to_select` individuos de `population` mediante torneos.

    Cada torneo muestrea `tournament_size` miembros (con reposición) de la
    población actual y se queda con el más apto.
    """
    pop_size = len(population)
    selected = np.empty(num_to_select, dtype=population.dtype)
    for i in range(num_to_select):
        contender_positions = rng.integers(0, pop_size, size=tournament_size)
        contenders = population[contender_positions]
        contender_fitness = fitness_lookup[contenders]
        selected[i] = contenders[np.argmax(contender_fitness)]
    return selected
