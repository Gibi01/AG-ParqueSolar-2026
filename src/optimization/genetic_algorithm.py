"""Algoritmo genético sobre ubicaciones candidatas de parque solar.

Representación del individuo: un único entero — la posición de una fila
en la tabla (fija, pre-filtrada a `valid == True`) de ubicaciones
candidatas. Esa fila ya lleva `grid_cell_id`, así que "individuo =
grid_cell_id" (según los requisitos del proyecto) se cumple vía este
mapeo uno a uno; el índice entero es solo una codificación contigua y
conveniente para las operaciones de arreglo en selección/cruce/mutación.

El fitness de cada candidato se precalcula una sola vez (depende solo de
columnas estáticas, ya normalizadas, de la base de datos local — no
sucede ninguna llamada a API en ningún lugar de este módulo, cumpliendo
el requisito de "el AG nunca consulta una API"). Un hall-of-fame acumula
los mejores individuos vistos a lo largo de todas las generaciones, así
que el ranking final TOP-10 no puede perder una solución fuerte por
deriva genética tarde en la corrida.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.config.settings import FitnessWeights, GeneticAlgorithmConfig
from src.optimization.crossover import crossover_population
from src.optimization.fitness import compute_fitness
from src.optimization.mutation import mutate_population
from src.optimization.selection import tournament_selection

logger = logging.getLogger(__name__)


@dataclass
class GAResult:
    top10: pd.DataFrame
    history: pd.DataFrame
    generations_run: int
    population_size: int
    n_candidates_considered: int


class GeneticAlgorithm:
    def __init__(
        self,
        candidates: pd.DataFrame,
        weights: FitnessWeights,
        ga_config: GeneticAlgorithmConfig,
    ):
        if len(candidates) == 0:
            raise ValueError("candidates is empty; cannot run the genetic algorithm.")
        self.candidates = candidates.reset_index(drop=True)
        self.weights = weights
        self.config = ga_config
        self.fitness_lookup = compute_fitness(self.candidates, weights).to_numpy()
        self.n_candidates = len(self.candidates)
        self.rng = np.random.default_rng(ga_config.random_seed)

    def run(self, top_n: int = 10) -> GAResult:
        if self.n_candidates < self.config.population_size:
            logger.warning(
                "Only %d valid candidates available (< population_size=%d); "
                "sampling with replacement to fill the population.",
                self.n_candidates,
                self.config.population_size,
            )

        population = self.rng.integers(0, self.n_candidates, size=self.config.population_size)
        hall_of_fame: dict[int, float] = {}

        def update_hall_of_fame(indices: np.ndarray) -> None:
            for idx in indices:
                idx = int(idx)
                hall_of_fame[idx] = float(self.fitness_lookup[idx])

        update_hall_of_fame(population)
        history_rows = []

        for generation in range(self.config.generations):
            fitness_values = self.fitness_lookup[population]
            history_rows.append(
                {
                    "generation": generation,
                    "best_fitness": float(fitness_values.max()),
                    "mean_fitness": float(fitness_values.mean()),
                }
            )

            order = np.argsort(-fitness_values)
            elite = population[order[: self.config.elitism]]

            num_offspring = self.config.population_size - self.config.elitism
            parents = tournament_selection(
                population, self.fitness_lookup, self.config.tournament_size, num_offspring, self.rng
            )
            children = crossover_population(parents, self.config.crossover_probability, self.n_candidates, self.rng)
            children = mutate_population(children, self.config.mutation_probability, self.n_candidates, self.rng)

            population = np.concatenate([elite, children])
            update_hall_of_fame(population)

        final_fitness = self.fitness_lookup[population]
        history_rows.append(
            {
                "generation": self.config.generations,
                "best_fitness": float(final_fitness.max()),
                "mean_fitness": float(final_fitness.mean()),
            }
        )

        ranked_indices = sorted(hall_of_fame, key=lambda i: hall_of_fame[i], reverse=True)[:top_n]
        top10 = self.candidates.iloc[ranked_indices].copy().reset_index(drop=True)
        top10["fitness"] = [hall_of_fame[i] for i in ranked_indices]
        top10 = top10.sort_values("fitness", ascending=False).reset_index(drop=True)
        top10.insert(0, "rank", np.arange(1, len(top10) + 1))

        return GAResult(
            top10=top10,
            history=pd.DataFrame(history_rows),
            generations_run=self.config.generations,
            population_size=self.config.population_size,
            n_candidates_considered=self.n_candidates,
        )
