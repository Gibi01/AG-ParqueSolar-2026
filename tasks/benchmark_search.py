"""Compare search operators on the saved 2024-2026 dataset, without network calls."""
import json
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

from src.config.settings import Settings
from src.database.spatial import SpatialRepository
from src.optimization.spatial import Individual, ParkEvaluator
from src.optimization.genetic_algorithm import GeneticAlgorithm
from src.optimization.mutation import random_gene, mutate_individual
from src.optimization.crossover import crossover_pair
from src.optimization.selection import tournament_selection


def legacy(evaluator, config, generations):
    """Original random initialization/operators; same phenotype evaluator for both."""
    rng = np.random.default_rng(config.random_seed)
    typical = max(1, int(evaluator.config.max_connection_capacity_mw /
                         (np.median(evaluator.area) * evaluator.config.pv_power_density_mw_per_km2)))
    population = [Individual(int(rng.choice(evaluator.seed_ids)),
                             tuple(random_gene(rng) for _ in range(int(rng.integers(typical + 1)))))
                  for _ in range(config.population_size)]
    best = -np.inf
    for generation in range(generations + 1):
        parks = [evaluator.evaluate(i) for i in population]
        fitness = np.array([p.metrics['fitness'] for p in parks])
        best = max(best, fitness.max())
        if generation == generations:
            break
        elite = [population[i] for i in np.argsort(-fitness, kind='stable')[:config.elitism]]
        children = tournament_selection(population, fitness, config.tournament_size, config.population_size-len(elite), rng)
        for i in range(0, len(children)-1, 2):
            if rng.random() < config.crossover_probability:
                children[i], children[i+1] = crossover_pair(children[i], children[i+1], rng)
        population = elite + [mutate_individual(child, evaluator.seed_ids, rng)
                              if rng.random() < config.mutation_probability else child for child in children]
    return float(best), len({p.cell_ids for p in parks})


if __name__ == '__main__':
    meta = json.loads(Path('results/spatial/run-20260927T203525-c33c9918/optimization_run.json').read_text())
    settings = Settings.model_validate(meta['configuration'])
    repo = SpatialRepository(settings.paths.database)
    data = repo.load_dataset(meta['dataset']['config_signature'])
    assert data['dataset_id'] == meta['dataset_id']
    ev = ParkEvaluator(data['grid'], data['neighbors'], data['lines'], data['transformers'], settings.park, settings.fitness)
    results = []
    for seed in (42, 7, 2026):
        settings.genetic_algorithm.random_seed = seed
        ev.evaluate.cache_clear()
        t = perf_counter()
        new = GeneticAlgorithm(ev, settings.genetic_algorithm).run()
        elapsed = perf_counter()-t
        requests = int(new.history.iloc[-1].evaluation_requests)
        # Give the old search at least the same number of evaluation requests.
        old_generations = max(200, int(np.ceil(requests / settings.genetic_algorithm.population_size)) - 1)
        ev.evaluate.cache_clear()
        t = perf_counter()
        old, diversity = legacy(ev, settings.genetic_algorithm, old_generations)
        row = dict(seed=seed, new_best=float(new.top5.fitness.max()), old_best=old,
                   new_diversity=int(new.history.iloc[-1].unique_parks), old_diversity=diversity,
                   new_requests=requests, old_requests=(old_generations+1)*50,
                   new_seconds=elapsed, old_seconds=perf_counter()-t)
        print(json.dumps(row), flush=True)
        results.append(row)
    output = Path('results/search-validation')
    output.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(results).to_csv(output/'comparison.csv', index=False)
    repo.engine.dispose()
