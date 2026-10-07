"""Paired crossover experiment on one saved dataset; never changes the production GA."""
import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from src.config.settings import Settings
from src.database.spatial import SpatialRepository
from src.optimization.genetic_algorithm import GeneticAlgorithm
from src.optimization.crossover import crossover_pair, competitive_crossover_pair
from src.optimization.initialization import TerritorialSampler
from src.optimization.ranking import territorial_top5
from src.optimization.spatial import ParkEvaluator


DEFAULT_SEEDS = [7, 21, 42, 63, 84, 105, 126, 147, 168, 2026]


def paired_results(rows):
    pairs = rows.pivot(index='seed', columns='variant', values='best_fitness')
    if not {'con_cruce', 'sin_cruce'} <= set(pairs.columns) or pairs.isna().any().any():
        raise ValueError('Each seed needs exactly one result from each variant.')
    pairs['delta'] = pairs.con_cruce - pairs.sin_cruce
    return pairs.reset_index()


def territorial_frequency(rows, origin, size_km, number_of_runs):
    frame = rows.copy()
    frame['sector_x'] = np.floor((frame.centroid_x_m - origin[0]) / (size_km * 1000)).astype(int)
    frame['sector_y'] = np.floor((frame.centroid_y_m - origin[1]) / (size_km * 1000)).astype(int)
    counts = (frame.drop_duplicates(['variant', 'seed', 'sector_x', 'sector_y'])
              .groupby(['variant', 'sector_x', 'sector_y']).size().rename('runs').reset_index())
    counts['percent'] = 100 * counts.runs / number_of_runs
    return counts.sort_values(['variant', 'runs', 'sector_x', 'sector_y'], ascending=[True, False, True, True])


def initial_digest(evaluator, config):
    sampler = TerritorialSampler(evaluator, np.random.default_rng(config.random_seed), config.territory_size_km)
    individuals = [sampler.individual() for _ in range(config.population_size)]
    payload = [(i.seed_cell_id, i.growth_genes) for i in individuals]
    return hashlib.sha256(json.dumps(payload).encode()).hexdigest()


def validate_candidates(candidates, evaluator):
    for row in candidates.itertuples():
        cells = set(json.loads(row.cell_ids))
        if not cells or row.installed_power_mw > evaluator.config.max_connection_capacity_mw + 1e-9:
            raise ValueError('Empty park or capacity violation.')
        visited, pending = set(), [next(iter(cells))]
        while pending:
            cell = pending.pop()
            if cell in visited:
                continue
            visited.add(cell)
            pending.extend(n for n in evaluator.neighbors.get(cell, ()) if n in cells and n not in visited)
        if visited != cells:
            raise ValueError('Disconnected park.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, default=Path('results/spatial/run-20261006T231108-428e45c4/optimization_run.json'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--seeds', type=int, nargs='+', default=DEFAULT_SEEDS)
    parser.add_argument('--generations', type=int, default=200)
    parser.add_argument('--operator', choices=['sequence', 'competitive'], default='competitive',
                        help='sequence reproduces the previous independent-cut operator')
    args = parser.parse_args()
    if len(args.seeds) != len(set(args.seeds)):
        raise ValueError('Seeds must be unique.')
    reference = json.loads(args.reference.read_text(encoding='utf-8'))
    settings = Settings.model_validate(reference['configuration'])
    output = args.output or Path('results/experiments') / datetime.now(timezone.utc).strftime('crossover-%Y%m%dT%H%M%SZ')
    output.mkdir(parents=True, exist_ok=False)
    modules = list(Path('src/optimization').glob('*.py')) + [Path('src/config/settings.py'), Path(__file__)]
    manifest = dict(started_utc=datetime.now(timezone.utc).isoformat(), reference=str(args.reference),
                    dataset_id=reference['dataset_id'], seeds=args.seeds,
                    variants={'con_cruce': .75, 'sin_cruce': 0.0}, generations=args.generations,
                    crossover_operator=args.operator,
                    budget='Same generations and population; measured evaluation requests may differ.',
                    code_sha256={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in modules},
                    git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                    software_versions=reference['software_versions'],
                    configuration=settings.model_dump(mode='json', exclude={'cds_api_key'}), status='running')
    manifest_path = output / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    repo = SpatialRepository(settings.paths.database)
    try:
        data = repo.load_dataset(reference['dataset']['config_signature'])
        if data['dataset_id'] != reference['dataset_id']:
            raise ValueError('The selected dataset differs from the saved reference.')
        evaluator = ParkEvaluator(data['grid'], data['neighbors'], data['lines'], data['transformers'], settings.park, settings.fitness)
        origin = (float(evaluator.x.min()), float(evaluator.y.min()))
        manifest['sector_origin_projected_m'] = origin
        manifest['projected_crs'] = str(data['grid'].crs)
        indexed = data['grid'].set_index('cell_id')
        rows, winners, alternatives, histories = [], [], [], []
        for layer in ('region', 'lines', 'transformers'):
            data[layer].to_crs(4326).to_file(output / (layer + '.geojson'), driver='GeoJSON')
        for seed in args.seeds:
            initial_hash = None
            initial_stats = None
            for variant, probability in manifest['variants'].items():
                config = settings.genetic_algorithm.model_copy(update=dict(random_seed=seed, crossover_probability=probability, generations=args.generations))
                digest = initial_digest(evaluator, config)
                if initial_hash is not None and digest != initial_hash:
                    raise ValueError('Paired initial populations differ.')
                initial_hash = digest
                evaluator.evaluate.cache_clear()
                start = perf_counter()
                operator = (competitive_crossover_pair if args.operator == 'competitive' else
                            lambda a, b, rng, ev: crossover_pair(a, b, rng))
                with patch('src.optimization.genetic_algorithm.competitive_crossover_pair', operator):
                    result = GeneticAlgorithm(evaluator, config).run()
                seconds = perf_counter() - start
                history = result.history.copy()
                if len(history) != args.generations + 1 or not history.population_size.eq(config.population_size).all():
                    raise ValueError('Incomplete run.')
                current_stats = history.iloc[0][['best_fitness', 'mean_fitness', 'mean_genes']].to_numpy(dtype=float)
                if initial_stats is not None and not np.allclose(current_stats, initial_stats, rtol=0, atol=1e-14):
                    raise ValueError('Different paired generation zero.')
                initial_stats = current_stats
                candidates = result.candidates.copy()
                validate_candidates(candidates, evaluator)
                candidates['geometry_wkt'] = [shapely.union_all(indexed.loc[json.loads(raw)].geometry.to_numpy()).wkt for raw in candidates.cell_ids]
                territorial = territorial_top5(candidates, config.territorial_separation_km)
                directory = output / variant / ('seed-' + str(seed))
                directory.mkdir(parents=True)
                for frame, name in ((history, 'history'), (candidates, 'candidates'), (territorial, 'ranking_territorial'), (candidates.head(5), 'ranking')):
                    frame.to_csv(directory / (name + '.csv'), index=False)
                (directory / 'configuration.json').write_text(json.dumps(config.model_dump(mode='json'), indent=2), encoding='utf-8')
                best = candidates.sort_values('fitness', ascending=False).iloc[0]
                final = history.iloc[-1]
                if not np.isclose(best.fitness, final.best_fitness):
                    raise ValueError('Ranking best differs from population best.')
                row = dict(seed=seed, variant=variant, crossover_probability=probability,
                           initial_population_sha256=digest, initial_best=float(history.iloc[0].best_fitness),
                           best_fitness=float(best.fitness), gain=float(best.fitness - history.iloc[0].best_fitness),
                           seconds=seconds, evaluation_requests=int(final.evaluation_requests),
                           decoded_individuals=int(final.decoded_individuals), unique_parks_seen=int(final.unique_parks_seen),
                           final_unique_parks=int(final.unique_parks), archive_candidates=len(candidates),
                           seed_cell_id=int(best.seed_cell_id), cell_ids=best.cell_ids,
                           latitude=float(best.latitude), longitude=float(best.longitude),
                           centroid_x_m=float(best.centroid_x_m), centroid_y_m=float(best.centroid_y_m),
                           number_of_cells=int(best.number_of_cells), installed_power_mw=float(best.installed_power_mw),
                           station_id=best.station_id, station_name=best.station_name,
                           solar_annual_kwh_m2=float(best.solar_annual_kwh_m2),
                           distance_to_power_line_km=float(best.distance_to_power_line_km),
                           distance_to_transformer_km=float(best.distance_to_transformer_km))
                rows.append(row)
                winners.append(dict(row, geometry_wkt=best.geometry_wkt))
                for _, park in territorial.iterrows():
                    alternatives.append(dict(park, seed=seed, variant=variant))
                histories.append(history.assign(seed=seed, variant=variant))
                pd.DataFrame(rows).to_csv(output / 'runs.csv', index=False)
                print(json.dumps(dict(seed=seed, variant=variant, fitness=row['best_fitness'], seconds=round(seconds, 2), completed=len(rows), total=2*len(args.seeds))), flush=True)
        summary = pd.DataFrame(rows)
        paired_results(summary).to_csv(output / 'paired.csv', index=False)
        pd.concat(histories, ignore_index=True).to_csv(output / 'histories.csv', index=False)
        for frame, name in ((pd.DataFrame(winners), 'winners'), (pd.DataFrame(alternatives), 'alternatives')):
            frame.to_csv(output / (name + '.csv'), index=False)
            polygons = gpd.GeoDataFrame(frame.drop(columns='geometry_wkt'), geometry=gpd.GeoSeries.from_wkt(frame.geometry_wkt), crs=data['grid'].crs).to_crs(4326)
            polygons.to_file(output / (name + '.geojson'), driver='GeoJSON')
            for size in (10, 25, 50):
                territorial_frequency(frame, origin, size, len(args.seeds)).to_csv(output / f'{name}_frequency_{size}km.csv', index=False)
        manifest.update(status='complete', completed_runs=len(rows), finished_utc=datetime.now(timezone.utc).isoformat())
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        print('OUTPUT=' + str(output.resolve()), flush=True)
    finally:
        repo.engine.dispose()


if __name__ == '__main__':
    main()
