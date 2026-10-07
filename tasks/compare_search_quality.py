"""Independent search baselines on a frozen snapshot, including compactness."""
import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from pyproj import Transformer

from src.config.settings import Settings
from src.database.spatial import SpatialRepository
from src.optimization.genetic_algorithm import GeneticAlgorithm
from src.optimization.initialization import TerritorialSampler
from src.optimization.ranking import territorial_top5
from src.optimization.spatial import Individual, ParkEvaluator

SEEDS = [7, 21, 42, 63, 84, 105, 126, 147, 168, 2026]


def connected(cells, evaluator):
    if not cells:
        return False
    seen, pending = set(), [next(iter(cells))]
    while pending:
        cid = pending.pop()
        if cid not in seen:
            seen.add(cid)
            pending.extend(n for n in evaluator.neighbors.get(cid, ()) if n in cells and n not in seen)
    return seen == cells


def encode_cells(cells, evaluator):
    """Canonical genotype solely to call the unchanged objective evaluator."""
    cells = set(cells)
    seed = min(cells, key=evaluator.positions.__getitem__)
    selected, genes = {seed}, []
    frontier = set(evaluator.neighbors.get(seed, ())) & evaluator.positions.keys()
    while selected != cells:
        choices = frontier & (cells - selected)
        if not choices:
            raise ValueError('Disconnected cells cannot be encoded.')
        cid = min(choices, key=evaluator.positions.__getitem__)
        ordered = sorted(frontier, key=evaluator.positions.__getitem__)
        genes.append(ordered.index(cid))
        selected.add(cid)
        frontier.update(set(evaluator.neighbors.get(cid, ())) & evaluator.positions.keys())
        frontier.difference_update(selected)
    return Individual(seed, tuple(genes))


def random_cells(evaluator, sampler, rng):
    cells = {sampler.next_seed()}
    target = int(rng.integers(1, sampler.typical + 2))
    area = math.fsum(evaluator.area[evaluator.positions[c]] for c in cells)
    frontier = set(evaluator.neighbors.get(next(iter(cells)), ())) & evaluator.positions.keys()
    for _ in range(target - 1):
        fitting = sorted(c for c in frontier if
                         (area + evaluator.area[evaluator.positions[c]]) * evaluator.config.pv_power_density_mw_per_km2
                         <= evaluator.config.max_connection_capacity_mw)
        if not fitting:
            break
        cid = int(rng.choice(fitting))
        cells.add(cid)
        area = math.fsum(evaluator.area[evaluator.positions[c]] for c in cells)
        frontier.update(set(evaluator.neighbors.get(cid, ())) & evaluator.positions.keys())
        frontier.difference_update(cells)
    return frozenset(cells)


def local_neighbors(cells, evaluator):
    cells = set(cells)
    proposals = set()
    frontier = set().union(*(set(evaluator.neighbors.get(c, ())) for c in cells)) & evaluator.positions.keys()
    for cid in sorted(frontier - cells):
        proposals.add(frozenset(cells | {cid}))
    if len(cells) > 1:
        for removed in sorted(cells):
            rest = cells - {removed}
            proposals.add(frozenset(rest))
            border = set().union(*(set(evaluator.neighbors.get(c, ())) for c in rest)) & evaluator.positions.keys()
            for added in sorted(border - cells):
                proposals.add(frozenset(rest | {added}))
    for proposed in sorted(proposals, key=lambda p: tuple(sorted(p))):
        power = math.fsum(evaluator.area[evaluator.positions[c]] for c in proposed) * evaluator.config.pv_power_density_mw_per_km2
        if power <= evaluator.config.max_connection_capacity_mw and connected(set(proposed), evaluator):
            yield proposed


class BudgetFinished(Exception):
    pass


class Tracker:
    def __init__(self, evaluator, size_km=50, archive_size=10, budget=None):
        self.evaluator, self.original, self.budget = evaluator, evaluator.evaluate, budget
        self.origin = (float(evaluator.x.min()), float(evaluator.y.min()))
        self.size_m, self.archive_size = size_km*1000, archive_size
        self.requests = self.computations = 0
        self.seen, self.archive, self.curve, self.draw_fitness = set(), {}, [], []
        self.best = -math.inf

    def __call__(self, individual):
        if self.budget is not None and self.computations >= self.budget:
            raise BudgetFinished
        before = self.original.cache_info().misses
        park = self.original(individual)
        self.requests += 1
        self.computations += self.original.cache_info().misses - before
        self.seen.add(park.cell_ids)
        self.best = max(self.best, park.metrics['fitness'])
        m = park.metrics
        key = (int((m['centroid_x_m'] - self.origin[0]) // self.size_m),
               int((m['centroid_y_m'] - self.origin[1]) // self.size_m))
        archive = self.archive.setdefault(key, {})
        if park.cell_ids in archive or len(archive) < self.archive_size or m['fitness'] > min(p.metrics['fitness'] for p in archive.values()):
            archive[park.cell_ids] = park
            if len(archive) > self.archive_size:
                worst = min(archive, key=lambda p: (archive[p].metrics['fitness'], p))
                del archive[worst]
        if not self.curve or self.computations >= self.curve[-1]['evaluations'] + 100:
            self.curve.append(dict(evaluations=self.computations, best_fitness=self.best))
        return park

    def cache_info(self):
        return self.original.cache_info()

    def candidates(self):
        parks = [p for a in self.archive.values() for p in a.values()]
        return pd.DataFrame([dict(cell_ids=json.dumps(p.cell_ids), **p.metrics) for p in parks])


def random_search(evaluator, config, seed, budget, local=False):
    evaluator.evaluate.cache_clear()
    rng = np.random.default_rng(seed)
    sampler = TerritorialSampler(evaluator, rng, config.territory_size_km)
    tracker = Tracker(evaluator, config.territory_size_km, config.archive_per_territory, budget)
    initial_budget = int(budget*.4) if local else budget
    starts = steps = 0
    try:
        while tracker.computations < initial_budget:
            park = tracker(encode_cells(random_cells(evaluator, sampler, rng), evaluator))
            tracker.draw_fitness.append(park.metrics['fitness'])
        if local:
            pool = sorted((p for a in tracker.archive.values() for p in a.values()),
                          key=lambda p: (-p.metrics['fitness'], p.cell_ids))
            while tracker.computations < budget:
                if pool:
                    current = pool.pop(0)
                else:
                    current = tracker(encode_cells(random_cells(evaluator, sampler, rng), evaluator))
                starts += 1
                while True:
                    best = current
                    for cells in local_neighbors(current.cell_ids, evaluator):
                        trial = tracker(encode_cells(cells, evaluator))
                        if trial.metrics['fitness'] > best.metrics['fitness'] + 1e-12:
                            best = trial
                    if best is current:
                        break
                    current = best
                    steps += 1
    except BudgetFinished:
        pass
    assert tracker.computations == budget
    tracker.curve.append(dict(evaluations=tracker.computations, best_fitness=tracker.best))
    return tracker, dict(local_starts=starts, local_improving_steps=steps,
                         random_draws=len(tracker.draw_fitness), random_phase_budget=initial_budget)


def integral(values):
    return np.pad(values.cumsum(axis=0).cumsum(axis=1), ((1, 0), (1, 0)))


def enumerate_rectangles(evaluator, thresholds, progress=None, batch_size=20000):
    grid = evaluator.grid
    # Strict full-cell area; clipped components belong to other search families.
    full = grid.loc[(grid.cell_area_m2 == 250000.) & (grid.component == 0)]
    r0, c0 = int(grid.row.min()), int(grid.column.min())
    shape = (int(grid.row.max())-r0+1, int(grid.column.max())-c0+1)
    rr, cc = full.row.to_numpy()-r0, full.column.to_numpy()-c0
    occupied = np.zeros(shape, dtype=np.int32)
    occupied[rr, cc] = 1
    lookup = np.full(shape, -1, dtype=np.int64)
    lookup[rr, cc] = full.cell_id.to_numpy()
    prefixes = [integral(occupied)]
    for values in (full.cell_area_m2, full.solar_annual_kwh_m2*full.cell_area_m2,
                   full.centroid_x_m*full.cell_area_m2, full.centroid_y_m*full.cell_area_m2):
        matrix = np.zeros(shape)
        matrix[rr, cc] = values.to_numpy()
        prefixes.append(integral(matrix))
    max_cells = int(evaluator.config.max_connection_capacity_mw / (.25*evaluator.config.pv_power_density_mw_per_km2))
    dimensions = [(h, w) for h in range(1, max_cells+1) for w in range(1, max_cells//h+1)]
    # For separation=0, four retained parks can eliminate at most this many
    # rectangular placements by cell overlap. Enough for the exact family top5.
    keep = 4*max_cells*sum(h*w for h, w in dimensions)+5
    retained = pd.DataFrame()
    counts, summary = np.zeros(len(thresholds), dtype=np.int64), []
    total = 0
    bounds, weights = evaluator.bounds, evaluator.weights
    def normalized(value, name, invert=False):
        lo, hi = bounds[name]
        score = np.ones_like(value) if np.isclose(lo, hi) else np.clip((value-lo)/(hi-lo), 0, 1)
        return score if not invert or np.isclose(lo, hi) else 1-score
    started = perf_counter()
    for h, w in dimensions:
        count = prefixes[0][h:, w:] - prefixes[0][:-h, w:] - prefixes[0][h:, :-w] + prefixes[0][:-h, :-w]
        rows, columns = np.where(count == h*w)
        shape_best = -math.inf
        for offset in range(0, len(rows), batch_size):
            r, c = rows[offset:offset+batch_size], columns[offset:offset+batch_size]
            sums = [p[r+h, c+w]-p[r, c+w]-p[r+h, c]+p[r, c] for p in prefixes[1:]]
            area, radiation, cx, cy = sums[0], sums[1]/sums[0], sums[2]/sums[0], sums[3]/sums[0]
            centers = shapely.points(cx, cy)
            dl = shapely.distance(centers, evaluator.lines[evaluator.line_tree.nearest(centers)])/1000
            distances = np.stack([shapely.distance(centers, g) for g in evaluator.transformers.geometry]) / 1000
            station_index = distances.argmin(axis=0)
            dt = distances.min(axis=0)
            power = area/1e6*evaluator.config.pv_power_density_mw_per_km2
            perimeter = 2*500*(h+w)
            compactness = 4*math.pi*area/perimeter**2
            solar_score, line_score, et_score = normalized(radiation, 'solar'), normalized(dl, 'line', True), normalized(dt, 'transformer', True)
            fitness = (weights.weight_solar*solar_score + weights.weight_grid_distance*line_score
                       + weights.weight_transformer_distance*et_score + weights.weight_installed_power*power/evaluator.config.max_connection_capacity_mw
                       + weights.weight_compactness*compactness)
            # Prefix sums accumulate floating rounding; treat <1e-7 as a tie.
            counts += np.array([(fitness > threshold+1e-7).sum() for threshold in thresholds])
            total += len(fitness)
            shape_best = max(shape_best, float(fitness.max()))
            take = np.argpartition(fitness, max(0, len(fitness)-keep))[max(0, len(fitness)-keep):]
            block = pd.DataFrame(dict(row=r[take], column=c[take], height=h, width=w,
                                      number_of_cells=h*w, fitness=fitness[take], park_area_km2=area[take]/1e6,
                                      park_area_ha=area[take]/10000, installed_power_mw=power[take],
                                      park_perimeter_m=perimeter, compactness_score=compactness[take],
                                      solar_annual_kwh_m2=radiation[take], distance_to_power_line_km=dl[take],
                                      distance_to_transformer_km=dt[take], centroid_x_m=cx[take], centroid_y_m=cy[take],
                                      solar_score=solar_score[take], grid_proximity_score=line_score[take],
                                      transformer_proximity_score=et_score[take],
                                      installed_power_score=power[take]/evaluator.config.max_connection_capacity_mw,
                                      station_id=evaluator.transformers.station_id.to_numpy()[station_index[take]]))
            retained = pd.concat([retained, block], ignore_index=True).nlargest(keep, 'fitness')
        summary.append(dict(height=h, width=w, placements=len(rows), best_fitness=shape_best))
        if progress:
            progress(dict(rectangle=f'{h}x{w}', evaluated=total, best=float(retained.fitness.max()), seconds=round(perf_counter()-started, 1)))
    retained['cell_ids'] = [json.dumps(sorted(lookup[int(p.row):int(p.row)+int(p.height), int(p.column):int(p.column)+int(p.width)].ravel().tolist())) for p in retained.itertuples()]
    return retained, pd.DataFrame(summary), dict(evaluations=total, full_cells=len(full), keep=keep,
                                                counts_above_threshold=counts.tolist(), seconds=perf_counter()-started)


def export_candidates(frame, evaluator, directory):
    directory.mkdir(parents=True, exist_ok=True)
    frame = frame.sort_values('fitness', ascending=False).reset_index(drop=True).copy()
    frame['rank'] = np.arange(1, len(frame)+1)
    indexed = evaluator.grid.set_index('cell_id')
    frame['geometry_wkt'] = [shapely.union_all(indexed.loc[json.loads(raw)].geometry.to_numpy()).wkt for raw in frame.cell_ids]
    transform = Transformer.from_crs(evaluator.grid.crs, 4326, always_xy=True)
    frame['longitude'], frame['latitude'] = transform.transform(frame.centroid_x_m.to_numpy(), frame.centroid_y_m.to_numpy())
    territorial = territorial_top5(frame, 0)
    for data, name in ((frame, 'candidates'), (frame.head(5), 'ranking'), (territorial, 'ranking_territorial')):
        data.to_csv(directory/(name+'.csv'), index=False)
    for data, name in ((frame.head(5), 'parks'), (territorial, 'parks_territorial')):
        geo = gpd.GeoDataFrame(data.drop(columns='geometry_wkt'), geometry=gpd.GeoSeries.from_wkt(data.geometry_wkt), crs=evaluator.grid.crs).to_crs(4326)
        (directory/(name+'.geojson')).write_text(geo.to_json(), encoding='utf-8')
    for row in pd.concat([frame.head(5), territorial]).drop_duplicates('cell_ids').itertuples():
        ids = json.loads(row.cell_ids)
        assert connected(set(ids), evaluator)
        actual = evaluator.evaluate(encode_cells(ids, evaluator))
        assert actual.cell_ids == tuple(sorted(ids, key=evaluator.positions.__getitem__))
        for name in ('fitness', 'park_area_km2', 'park_perimeter_m', 'compactness_score', 'solar_annual_kwh_m2', 'distance_to_transformer_km'):
            assert np.isclose(getattr(row, name), actual.metrics[name], atol=1e-7, rtol=1e-9), (name, getattr(row, name), actual.metrics[name])
    return frame, territorial


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, default=Path('results/spatial/run-20261007T003424-8b60c1ab/optimization_run.json'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seeds', type=int, nargs='+', default=SEEDS)
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=False)
    reference = json.loads(args.reference.read_text(encoding='utf-8'))
    settings = Settings.model_validate(reference['configuration'])
    manifest = dict(status='running', started_utc=datetime.now(timezone.utc).isoformat(),
                    reference=str(args.reference), dataset_id=reference['dataset_id'], seeds=args.seeds,
                    configuration=reference['configuration'], plan='tasks/search_quality_plan.md',
                    budget='Per seed: same objective computations (cache misses) as AG; rectangle enumeration unrestricted',
                    code_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__), *Path('src/optimization').glob('*.py'), Path('src/config/settings.py')]})
    def save_manifest():
        (output/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    save_manifest()
    repo = SpatialRepository(settings.paths.database)
    try:
        data = repo.load_dataset(reference['dataset']['config_signature'])
        assert data['dataset_id'] == reference['dataset_id']
        ev = ParkEvaluator(data['grid'], data['neighbors'], data['lines'], data['transformers'], settings.park, settings.fitness)
        assert all(np.allclose(ev.bounds[k], v, atol=1e-12) for k, v in reference['normalization_bounds'].items())
        manifest['projected_crs'] = str(ev.grid.crs)
        save_manifest()
        references = []
        for ranking in ('ranking', 'ranking_territorial'):
            frame = pd.read_csv(args.reference.parent/(ranking+'.csv'))
            frame['ranking_type'] = ranking
            references.append(frame)
        refs = pd.concat(references, ignore_index=True)
        refs.to_csv(output/'reference_rankings.csv', index=False)
        rectangles, shape_summary, rectangle_stats = enumerate_rectangles(ev, refs.fitness.to_numpy(),
            progress=lambda x: print(json.dumps(x), flush=True))
        rectangles, rect_top5 = export_candidates(rectangles, ev, output/'rectangles')
        shape_summary.to_csv(output/'rectangles/dimensions.csv', index=False)
        refs['rectangles_better'] = rectangle_stats['counts_above_threshold']
        refs['rectangle_percentile'] = 100*(1-refs.rectangles_better/rectangle_stats['evaluations'])
        refs.to_csv(output/'reference_rectangles_comparison.csv', index=False)
        manifest['rectangles'] = rectangle_stats
        save_manifest()
        records, all_territorial = [], []
        for seed in args.seeds:
            config = settings.genetic_algorithm.model_copy(update={'random_seed':seed})
            ev.evaluate.cache_clear()
            tracker = Tracker(ev, config.territory_size_km, config.archive_per_territory)
            original = ev.evaluate
            ev.evaluate = tracker
            start = perf_counter()
            try:
                ga = GeneticAlgorithm(ev, config).run()
            finally:
                ev.evaluate = original
            elapsed = perf_counter()-start
            budget = int(ga.history.iloc[-1].decoded_individuals)
            assert budget == tracker.computations
            assert np.isclose(ga.candidates.fitness.max(), tracker.best)
            if seed == reference['random_seed']:
                assert np.isclose(ga.top5.fitness.max(), refs.iloc[0].fitness, atol=1e-12)
            methods = [('ag', tracker, ga.candidates, elapsed, {})]
            ga.history.to_csv(output/f'ga_history_seed_{seed}.csv', index=False)
            for method, local in (('random', False), ('random_local', True)):
                start = perf_counter()
                other, info = random_search(ev, config, seed, budget, local)
                methods.append((method, other, other.candidates(), perf_counter()-start, info))
                print(json.dumps(dict(seed=seed, method=method, best=other.best, budget=budget)), flush=True)
            for method, t, candidates, seconds, info in methods:
                directory = output/method/f'seed-{seed}'
                candidates, territorial = export_candidates(candidates, ev, directory)
                t.curve.append(dict(evaluations=t.computations, best_fitness=t.best))
                pd.DataFrame(t.curve).drop_duplicates('evaluations', keep='last').to_csv(directory/'curve.csv', index=False)
                if t.draw_fitness:
                    np.save(directory/'random_draw_fitness.npy', t.draw_fitness)
                winner = candidates.iloc[0]
                record = dict(seed=seed, method=method, best_fitness=float(winner.fitness),
                              objective_evaluations=t.computations, evaluation_requests=t.requests,
                              unique_parks_seen=len(t.seen), seconds=seconds,
                              territorial_count=len(territorial), territorial_mean=float(territorial.fitness.mean()),
                              **{k:float(winner[k]) for k in ('installed_power_mw','compactness_score','park_perimeter_m','distance_to_transformer_km','solar_annual_kwh_m2')}, **info)
                records.append(record)
                all_territorial.extend(territorial.assign(seed=seed, method=method).to_dict('records'))
                print(json.dumps(record), flush=True)
            pd.DataFrame(records).to_csv(output/'runs.csv', index=False)
        pd.DataFrame(all_territorial).to_csv(output/'territorial_all.csv', index=False)
        manifest.update(status='complete', completed_runs=len(records), finished_utc=datetime.now(timezone.utc).isoformat())
        save_manifest()
        print('OUTPUT='+str(output.resolve()), flush=True)
    finally:
        repo.engine.dispose()


if __name__ == '__main__':
    main()
