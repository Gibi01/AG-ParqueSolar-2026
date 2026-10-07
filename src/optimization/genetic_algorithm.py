"""Variable-area spatial GA. Evaluations consume only the processed local dataset."""
import json
import logging
from dataclasses import dataclass
from time import perf_counter

import numpy as np
import pandas as pd
from pyproj import Transformer

from src.optimization.crossover import competitive_crossover_pair
from src.optimization.mutation import mutate_effectively
from src.optimization.initialization import TerritorialSampler
from src.optimization.selection import tournament_selection
from src.optimization.spatial import Individual

logger = logging.getLogger(__name__)


@dataclass
class GAResult:
    top5: pd.DataFrame
    history: pd.DataFrame
    generations_run: int
    population_size: int
    n_candidates_considered: int
    random_seed: int
    candidates: pd.DataFrame

    @property
    def top10(self):
        """Compatibility alias for callers of the previous spatial API."""
        return self.top5


class GeneticAlgorithm:
    def __init__(self, evaluator, ga_config):
        self.evaluator, self.config = evaluator, ga_config
        self.random_seed = ga_config.random_seed if ga_config.random_seed is not None else int(np.random.SeedSequence().entropy)
        self.rng = np.random.default_rng(self.random_seed)

    def run(self, top_n=5):
        evaluator, config, rng = self.evaluator, self.config, self.rng
        if top_n != 5:
            raise ValueError('Esta versión exporta rankings de hasta cinco candidatos.')
        start = perf_counter()
        cache_start = evaluator.evaluate.cache_info()
        sampler = TerritorialSampler(evaluator, rng, config.territory_size_km)
        population = [sampler.individual() for _ in range(config.population_size)]
        hall, history = {}, []
        seen = set()
        mutation_events = mutation_attempts = mutation_changes = duplicate_fallbacks = 0
        for generation in range(config.generations + 1):
            parks = [evaluator.evaluate(individual) for individual in population]
            fitness = np.array([park.metrics['fitness'] for park in parks])
            for individual, park in zip(population, parks):
                seen.add(park.cell_ids)
                previous = hall.get(park.cell_ids)
                if previous is None or (len(individual.growth_genes), individual.seed_cell_id, individual.growth_genes) < (
                        len(previous[0].growth_genes), previous[0].seed_cell_id, previous[0].growth_genes):
                    hall[park.cell_ids] = (individual, park)
            # Keep strong candidates in every visited territory, not just one cluster.
            counts, retained = {}, {}
            for identity, pair in sorted(hall.items(), key=lambda item: (-item[1][1].metrics['fitness'], item[0])):
                metrics = pair[1].metrics
                territory = sampler.territory(metrics['centroid_x_m'], metrics['centroid_y_m'])
                if counts.get(territory, 0) < config.archive_per_territory:
                    retained[identity] = pair
                    counts[territory] = counts.get(territory, 0) + 1
            hall = retained
            cache = evaluator.evaluate.cache_info()
            history.append(dict(generation=generation, best_fitness=float(fitness.max()),
                                best_historical_fitness=max(p.metrics['fitness'] for _, p in hall.values()),
                                mean_fitness=float(fitness.mean()), median_fitness=float(np.median(fitness)),
                                std_fitness=float(fitness.std(ddof=0)),
                                unique_parks=len({p.cell_ids for p in parks}), population_size=len(population),
                                unique_parks_seen=len(seen), archive_candidates=len(hall),
                                mean_cells=float(np.mean([len(p.cell_ids) for p in parks])),
                                mean_genes=float(np.mean([len(i.growth_genes) for i in population])),
                                mean_accepted_genes=float(np.mean([len(p.accepted_gene_indices) for p in parks])),
                                mean_skipped_genes=float(np.mean([len(p.skipped_gene_indices) for p in parks])),
                                mean_unprocessed_genes=float(np.mean([p.unprocessed_genes for p in parks])),
                                mutation_events=mutation_events, mutation_attempts=mutation_attempts,
                                effective_mutations=mutation_changes,
                                mutation_effective_percent=100 * mutation_changes / mutation_events if mutation_events else np.nan,
                                duplicate_fallbacks=duplicate_fallbacks,
                                evaluation_requests=cache.hits + cache.misses - cache_start.hits - cache_start.misses,
                                decoded_individuals=cache.misses - cache_start.misses,
                                elapsed_seconds=perf_counter() - start))
            if generation % 20 == 0:
                logger.info('Generación %d: fitness %.5f, parques únicos %d', generation, fitness.max(), history[-1]['unique_parks'])
            if generation == config.generations:
                break
            elite, identities = [], set()
            for i in np.argsort(-fitness, kind='stable'):
                if len(elite) >= config.elitism:
                    break
                if parks[i].cell_ids not in identities:
                    elite.append(population[i])
                    identities.add(parks[i].cell_ids)
            children = tournament_selection(population, fitness, config.tournament_size,
                                            config.population_size - len(elite), rng)
            for i in range(0, len(children) - 1, 2):
                if rng.random() < config.crossover_probability:
                    children[i], children[i + 1] = competitive_crossover_pair(children[i], children[i + 1], rng, evaluator)
            mutation_events = mutation_attempts = mutation_changes = duplicate_fallbacks = 0
            population = list(elite)
            for child in children:
                if rng.random() < config.mutation_probability:
                    child, attempts, changed = mutate_effectively(child, evaluator, rng, config.mutation_attempts)
                    mutation_events += 1
                    mutation_attempts += attempts
                    mutation_changes += int(changed)
                for attempt in range(config.duplicate_attempts + 1):
                    identity = evaluator.evaluate(child).cell_ids
                    if identity not in identities:
                        break
                    if attempt == config.duplicate_attempts:
                        duplicate_fallbacks += 1
                        break
                    child = sampler.individual()
                identities.add(identity)
                population.append(child)
        transform = Transformer.from_crs(evaluator.grid.crs, 4326, always_xy=True)
        ranking = []
        for rank, (individual, park) in enumerate(hall.values(), 1):
            longitude, latitude = transform.transform(park.metrics['centroid_x_m'], park.metrics['centroid_y_m'])
            ranking.append(dict(rank=rank, seed_cell_id=individual.seed_cell_id,
                                growth_genes=json.dumps(individual.growth_genes), cell_ids=json.dumps(park.cell_ids),
                                accepted_gene_indices=json.dumps(park.accepted_gene_indices),
                                skipped_gene_indices=json.dumps(park.skipped_gene_indices),
                                latitude=latitude, longitude=longitude, **park.metrics))
        candidates = pd.DataFrame(ranking)
        return GAResult(candidates.head(5).copy(), pd.DataFrame(history), config.generations,
                        config.population_size, len(evaluator.grid), self.random_seed, candidates)
