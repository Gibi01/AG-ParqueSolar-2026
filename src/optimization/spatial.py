"""Deterministic connected growth; no network access or polygon unions in fitness."""
from dataclasses import dataclass
from functools import lru_cache
import math

import numpy as np
import shapely


@dataclass(frozen=True)
class Individual:
    seed_cell_id: int
    growth_genes: tuple[int, ...] = ()


@dataclass
class Park:
    cell_ids: tuple[int, ...]
    accepted_gene_indices: tuple[int, ...]
    skipped_gene_indices: tuple[int, ...]
    metrics: dict
    unprocessed_genes: int = 0


def score(value, bounds, invert=False):
    low, high = bounds
    result = 1.0 if np.isclose(low, high) else float(np.clip((value - low) / (high - low), 0, 1))
    return result if not invert or np.isclose(low, high) else 1 - result


class ParkEvaluator:
    def __init__(self, grid, neighbors, lines, transformers, park_config, weights):
        self.grid = grid.loc[grid.valid.astype(bool)].sort_values(['row', 'column', 'component']).reset_index(drop=True)
        self.positions = {int(cid): i for i, cid in enumerate(self.grid.cell_id)}
        self.neighbors = neighbors
        self.config, self.weights = park_config, weights
        self.area = self.grid.cell_area_m2.to_numpy(dtype=float) / 1e6
        self.x = self.grid.centroid_x_m.to_numpy(dtype=float)
        self.y = self.grid.centroid_y_m.to_numpy(dtype=float)
        self.solar = self.grid.solar_annual_kwh_m2.to_numpy(dtype=float)
        self.seed_ids = self.grid.cell_id.to_numpy()[self.area * park_config.pv_power_density_mw_per_km2 <= park_config.max_connection_capacity_mw]
        if not len(self.seed_ids):
            raise ValueError('No hay semillas válidas compatibles con la capacidad experimental.')
        if weights.use_solar and not np.isfinite(self.solar).all():
            raise ValueError('Las celdas válidas requieren irradiación finita.')
        self.lines = lines.to_crs(grid.crs).geometry.to_numpy()
        self.line_tree = shapely.STRtree(self.lines) if len(self.lines) else None
        self.transformers = transformers.to_crs(grid.crs).copy()
        if len(transformers):
            self.transformers['station_id'] = self.transformers['station_id'].astype(str)
            self.transformers = self.transformers.sort_values('station_id').reset_index(drop=True)
        if weights.use_power_lines and self.line_tree is None:
            raise ValueError('Falta la capa de líneas.')
        if weights.use_transformers and not len(transformers):
            raise ValueError('Faltan las estaciones.')
        centers = shapely.points(self.x, self.y)
        self.bounds = {}
        if weights.use_solar:
            self.bounds['solar'] = (float(self.solar.min()), float(self.solar.max()))
        if self.line_tree is not None:
            distances = shapely.distance(centers, self.lines[self.line_tree.nearest(centers)]) / 1000
            self.bounds['line'] = (float(distances.min()), float(distances.max()))
        if len(transformers):
            distances = np.min(np.stack([shapely.distance(centers, g) for g in self.transformers.geometry]), axis=0) / 1000
            self.bounds['transformer'] = (float(distances.min()), float(distances.max()))
        # Cache is scoped to this immutable dataset/configuration, never shared across scenarios.
        self.evaluate = lru_cache(maxsize=10000)(self._evaluate)

    def _evaluate(self, individual):
        seed = individual.seed_cell_id
        if seed not in self.positions or self.area[self.positions[seed]] * self.config.pv_power_density_mw_per_km2 > self.config.max_connection_capacity_mw:
            raise ValueError('Semilla inválida o demasiado grande.')
        selected = {seed}
        frontier = set(self.neighbors.get(seed, ())) & self.positions.keys()
        area = float(self.area[self.positions[seed]])
        accepted, skipped = [], []
        processed = 0
        for index, gene in enumerate(individual.growth_genes):
            if not frontier:
                break
            ordered = sorted(frontier, key=self.positions.__getitem__)
            # If even the smallest frontier cell cannot fit, later genes cannot grow.
            smallest = min(frontier, key=lambda cid: self.area[self.positions[cid]])
            if math.fsum(self.area[self.positions[cid]] for cid in selected | {smallest}) * self.config.pv_power_density_mw_per_km2 > self.config.max_connection_capacity_mw:
                break
            processed += 1
            candidate = ordered[int(gene) % len(ordered)]
            new_area = math.fsum(self.area[self.positions[cid]] for cid in selected | {candidate})
            if new_area * self.config.pv_power_density_mw_per_km2 > self.config.max_connection_capacity_mw:
                skipped.append(index)
                continue
            selected.add(candidate)
            area = new_area
            accepted.append(index)
            frontier.update(set(self.neighbors.get(candidate, ())) & self.positions.keys())
            frontier.difference_update(selected)
        ids = tuple(sorted(selected, key=self.positions.__getitem__))
        positions = [self.positions[cid] for cid in ids]
        areas = self.area[positions]
        # fsum makes area independent of the path used to reach the same set of cells.
        cx = float(np.dot(areas, self.x[positions]) / area)
        cy = float(np.dot(areas, self.y[positions]) / area)
        center = shapely.Point(cx, cy)
        irradiation = float(np.dot(areas, self.solar[positions]) / area) if self.weights.use_solar else np.nan
        power = float(area * self.config.pv_power_density_mw_per_km2)
        metrics = dict(park_area_km2=float(area), park_area_ha=float(area * 100),
                       number_of_cells=len(ids), installed_power_mw=power,
                       max_connection_capacity_mw=self.config.max_connection_capacity_mw,
                       installed_power_score=float(np.clip(power / self.config.max_connection_capacity_mw, 0, 1)),
                       capacity_used_percent=100 * power / self.config.max_connection_capacity_mw,
                       solar_annual_kwh_m2=irradiation, estimated_annual_energy_mwh=power * irradiation,
                       centroid_x_m=cx, centroid_y_m=cy,
                       solar_score=score(irradiation, self.bounds['solar']) if self.weights.use_solar else np.nan,
                       grid_proximity_score=np.nan, distance_to_power_line_km=np.nan,
                       transformer_proximity_score=np.nan, distance_to_transformer_km=np.nan,
                       station_id=None, station_name=None)
        if self.line_tree is not None:
            distance = float(center.distance(self.lines[self.line_tree.nearest(center)]) / 1000)
            metrics.update(distance_to_power_line_km=distance, grid_proximity_score=score(distance, self.bounds['line'], True))
        if len(self.transformers):
            distances = shapely.distance(center, self.transformers.geometry.to_numpy()) / 1000
            nearest = int(np.argmin(distances))
            station = self.transformers.iloc[nearest]
            distance = float(distances[nearest])
            metrics.update(distance_to_transformer_km=distance, station_id=station.station_id,
                           station_name=station.get('nombre', station.station_id),
                           transformer_proximity_score=score(distance, self.bounds['transformer'], True))
        metrics['fitness'] = sum(weight * metrics[key] for weight, key in [
            (self.weights.weight_solar, 'solar_score'),
            (self.weights.weight_grid_distance, 'grid_proximity_score'),
            (self.weights.weight_transformer_distance, 'transformer_proximity_score'),
            (self.weights.weight_installed_power, 'installed_power_score')] if weight > 0)
        return Park(ids, tuple(accepted), tuple(skipped), metrics, len(individual.growth_genes) - processed)
