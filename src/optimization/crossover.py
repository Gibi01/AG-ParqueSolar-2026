"""Cruce (crossover) por mezcla aritmética sobre individuos codificados como índice de candidato.

Cada individuo es un único gen entero (su posición en el arreglo de
ubicaciones candidatas), así que el cruce clásico multi-gen no aplica. En
cambio, esto usa cruce de mezcla real/aritmético — estándar para AGs de
una sola variable — produciendo dos hijos cuyo índice cae sobre la línea
entre los índices de los dos padres, y luego redondea y recorta de vuelta
al rango válido.
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
    """Empareja padres consecutivos y aplica cruce de mezcla con
    probabilidad `crossover_probability`; los individuos no emparejados/
    saltados pasan sin cambios."""
    children = parents.copy()
    for i in range(0, len(parents) - 1, 2):
        if rng.random() < crossover_probability:
            c1, c2 = blend_crossover_pair(int(parents[i]), int(parents[i + 1]), n_candidates, rng)
            children[i], children[i + 1] = c1, c2
    return children
