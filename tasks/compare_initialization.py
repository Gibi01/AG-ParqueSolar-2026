"""Factorial initialization/crossover experiment, isolated from production settings."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from src.optimization.initialization import TerritorialSampler
from tasks import compare_crossover


class UniformInitialSampler(TerritorialSampler):
    """Uniform valid seed cells initially; original territorial replacement thereafter."""
    def __init__(self, evaluator, rng, size_km, initial_count):
        super().__init__(evaluator, rng, size_km)
        self.remaining_initial = initial_count

    def next_seed(self):
        if self.remaining_initial > 0:
            self.remaining_initial -= 1
            return int(self.rng.choice(self.evaluator.seed_ids))
        return super().next_seed()


def fast_difference_statistics(delta):
    """Same exact sign-flip test as the prior helper; vectorized in bounded chunks."""
    delta = np.asarray(delta, dtype=float)
    if not len(delta) or len(delta) > 20 or not np.isfinite(delta).all():
        raise ValueError('Requires 1–20 finite paired differences.')
    rng = np.random.default_rng(90210)
    boot = rng.choice(delta, size=(20000, len(delta)), replace=True).mean(axis=1)
    observed = abs(delta.mean())
    exceedances = 0
    total = 1 << len(delta)
    for start in range(0, total, 65536):
        indices = np.arange(start, min(start + 65536, total), dtype=np.uint32)
        bits = (indices[:, None] >> np.arange(len(delta), dtype=np.uint32)) & 1
        signs = bits.astype(float) * 2 - 1
        null = abs((signs * delta).mean(axis=1))
        exceedances += int((null >= observed - 1e-14).sum())
    return dict(mean_delta=float(delta.mean()), median_delta=float(np.median(delta)),
        bootstrap_95_ci=np.quantile(boot, [.025, .975]).tolist(),
        sign_flip_p_two_sided=exceedances / total,
        crossover_wins=int((delta > 1e-12).sum()), no_crossover_wins=int((delta < -1e-12).sum()),
        ties=int((abs(delta) <= 1e-12).sum()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--generations', type=int, default=150)
    parser.add_argument('--seeds', type=int, nargs='+', default=list(range(501, 521)))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    reference_path = Path('results/spatial/run-20261006T231108-428e45c4/optimization_run.json')
    reference = json.loads(reference_path.read_text(encoding='utf-8'))
    population_size = reference['configuration']['genetic_algorithm']['population_size']
    manifest = dict(status='running', generations=args.generations, seeds=args.seeds,
        dataset_id=reference['dataset_id'], initialization_scope='Only the initial population; territorial replacement remains.',
        conditions=['territorial/con_cruce', 'territorial/sin_cruce', 'uniforme/con_cruce', 'uniforme/sin_cruce'],
        runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    manifest_path = args.output / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    initial_rows, diversity_rows = [], []
    for method in ('territorial', 'uniforme'):
        captured = []
        base = UniformInitialSampler if method == 'uniforme' else TerritorialSampler

        class RecordingSampler(base):
            def __init__(self, evaluator, rng, size_km):
                if method == 'uniforme':
                    super().__init__(evaluator, rng, size_km, initial_count=population_size)
                else:
                    super().__init__(evaluator, rng, size_km)
                self.initial = []
                captured.append(self)

            def individual(self):
                individual = super().individual()
                if len(self.initial) < population_size:
                    self.initial.append(individual)
                return individual

        mode_path = args.output / method
        argv = ['compare_crossover', '--operator', 'competitive', '--reference', str(reference_path),
            '--output', str(mode_path), '--generations', str(args.generations), '--seeds', *map(str, args.seeds)]
        with patch.object(sys, 'argv', argv), \
             patch.object(compare_crossover, 'TerritorialSampler', RecordingSampler), \
             patch('src.optimization.genetic_algorithm.TerritorialSampler', RecordingSampler):
            compare_crossover.main()
        assert len(captured) == 4 * len(args.seeds)
        for index, seed in enumerate(args.seeds):
            samplers = captured[index * 4:(index + 1) * 4]
            assert all(s.initial == samplers[0].initial for s in samplers)
            sampler = samplers[0]
            evaluator = sampler.evaluator
            individuals = sampler.initial
            evaluator.evaluate.cache_clear()
            parks = [evaluator.evaluate(ind) for ind in individuals]
            positions = [evaluator.positions[ind.seed_cell_id] for ind in individuals]
            coordinates = np.column_stack([evaluator.x[positions], evaluator.y[positions]]) / 1000
            distances = np.linalg.norm(coordinates[:, None] - coordinates[None, :], axis=2)
            pair_distances = distances[np.triu_indices(len(individuals), 1)]
            sectors = [sampler.territory(*(point * 1000)) for point in coordinates]
            diversity_rows.append(dict(initialization=method, seed=seed,
                occupied_sectors_50km=len(set(sectors)), distinct_seed_cells=len(set(positions)),
                distinct_initial_parks=len({park.cell_ids for park in parks}),
                mean_seed_distance_km=float(pair_distances.mean()),
                median_seed_distance_km=float(np.median(pair_distances)),
                best_initial_fitness=max(p.metrics['fitness'] for p in parks),
                mean_initial_fitness=float(np.mean([p.metrics['fitness'] for p in parks])),
                mean_initial_genes=float(np.mean([len(ind.growth_genes) for ind in individuals]))))
            for slot, (ind, park, sector) in enumerate(zip(individuals, parks, sectors)):
                initial_rows.append(dict(initialization=method, seed=seed, slot=slot,
                    seed_cell_id=ind.seed_cell_id, growth_genes=json.dumps(ind.growth_genes),
                    cell_ids=json.dumps(park.cell_ids), fitness=park.metrics['fitness'],
                    sector_x=sector[0], sector_y=sector[1]))
        mode_manifest = json.loads((mode_path / 'manifest.json').read_text(encoding='utf-8'))
        mode_manifest.update(initialization=method, initialization_scope=manifest['initialization_scope'],
            experiment_runner_sha256=manifest['runner_sha256'])
        (mode_path / 'manifest.json').write_text(json.dumps(mode_manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        pd.DataFrame(initial_rows).to_csv(args.output / 'initial_populations.csv', index=False)
        pd.DataFrame(diversity_rows).to_csv(args.output / 'initial_diversity.csv', index=False)
    manifest.update(status='complete', completed_runs=4 * len(args.seeds))
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print('FACTORIAL_OUTPUT=' + str(args.output.resolve()), flush=True)


if __name__ == '__main__':
    main()
