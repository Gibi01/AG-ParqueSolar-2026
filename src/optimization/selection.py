"""Tournament selection over fitness of decoded parks."""
import numpy as np


def tournament_selection(population, fitness, tournament_size, count, rng):
    result = []
    for _ in range(count):
        indices = rng.integers(0, len(population), size=tournament_size)
        winner = indices[np.argmax(fitness[indices])]
        result.append(population[int(winner)])
    return result
