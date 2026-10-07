"""Spatial dataset snapshots and reproducible run records."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, inspect, text


def config_signature(settings):
    # Capacity, density, weights and GA settings do not alter the processed spatial data.
    value = {name: getattr(settings, name).model_dump(mode='json')
             for name in ('region', 'grid', 'urban_exclusion', 'climate', 'infrastructure')}
    value['periods'] = settings.climate.year_months
    value['active_sources'] = [settings.fitness.use_solar, settings.fitness.use_power_lines, settings.fitness.use_transformers]
    value['processing_version'] = 3
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def geometry_frame(frame):
    result = pd.DataFrame(frame.drop(columns='geometry'))
    result['geometry_wkt'] = frame.geometry.to_wkt(rounding_precision=-1)
    return result


class SpatialRepository:
    def __init__(self, path):
        self.db_path = Path(path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        if 'grid_cells' in inspect(self.engine).get_table_names():
            self.engine.dispose()
            raise RuntimeError('Esquema incompatible: usar una base espacial válida; no se sobrescribirá esta base.')
        with self.engine.begin() as conn:
            conn.execute(text('CREATE TABLE IF NOT EXISTS datasets (dataset_id TEXT PRIMARY KEY, metadata TEXT NOT NULL, created_at TEXT NOT NULL)'))
            conn.execute(text('CREATE TABLE IF NOT EXISTS spatial_runs (run_id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL, metadata TEXT NOT NULL, ranking TEXT NOT NULL)'))

    def save_dataset(self, grid, neighbors, climate, layers, metadata):
        frames = {'spatial_cells': geometry_frame(grid),
                  'spatial_neighbors': pd.DataFrame({'cell_id': list(neighbors), 'neighbors': [json.dumps(v) for v in neighbors.values()]})}
        if len(climate):
            frames['pixel_months'] = climate.copy()
        for name, layer in layers.items():
            frames['layer_' + name] = geometry_frame(layer)
        digest = hashlib.sha256(json.dumps(metadata, sort_keys=True, default=str).encode())
        for name, frame in sorted(frames.items()):
            digest.update(name.encode())
            digest.update(pd.util.hash_pandas_object(frame, index=False).values.tobytes())
        dataset_id = digest.hexdigest()
        with self.engine.begin() as conn:
            if conn.execute(text('SELECT 1 FROM datasets WHERE dataset_id=:id'), {'id': dataset_id}).first():
                return dataset_id
            for name, frame in frames.items():
                frame = frame.copy()
                frame.insert(0, 'dataset_id', dataset_id)
                frame.to_sql(name, conn, if_exists='append', index=False, chunksize=5000)
                conn.execute(text(f'CREATE INDEX IF NOT EXISTS idx_{name}_dataset ON {name}(dataset_id)'))
            conn.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS idx_cells_identity ON spatial_cells(dataset_id, cell_id)'))
            if len(climate):
                conn.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS idx_pixel_month_identity ON pixel_months(dataset_id, climate_pixel_id, year, month)'))
            conn.execute(text('INSERT INTO datasets VALUES (:id, :metadata, :created)'),
                         {'id': dataset_id, 'metadata': json.dumps(metadata, default=str), 'created': datetime.now(timezone.utc).isoformat()})
        return dataset_id

    def load_dataset(self, signature):
        with self.engine.connect() as conn:
            available = conn.execute(text('SELECT dataset_id, metadata FROM datasets ORDER BY created_at DESC')).all()
            found = next(((key, json.loads(meta)) for key, meta in available
                          if json.loads(meta)['config_signature'] == signature), None)
            if found is None:
                raise RuntimeError('No hay dataset compatible; ejecutá --process con esta configuración.')
            key, metadata = found
            tables = set(inspect(conn).get_table_names())

            def read(name):
                if name not in tables:
                    return pd.DataFrame()
                return pd.read_sql(text(f'SELECT * FROM {name} WHERE dataset_id=:id'), conn,
                                   params={'id': key}).drop(columns='dataset_id')

            def geo(name, crs):
                frame = read(name)
                if 'geometry_wkt' not in frame:
                    return gpd.GeoDataFrame(geometry=[], crs=crs)
                return gpd.GeoDataFrame(frame.drop(columns='geometry_wkt'),
                                        geometry=gpd.GeoSeries.from_wkt(frame.geometry_wkt), crs=crs)

            grid = geo('spatial_cells', metadata['projected_crs'])
            graph = read('spatial_neighbors')
            neighbors = {int(row.cell_id): tuple(json.loads(row.neighbors)) for row in graph.itertuples()}
            layers = {name: geo('layer_' + name, 'EPSG:4326') for name in ('region', 'urban', 'lines', 'transformers')}
            layers['urban_mask'] = geo('layer_urban_mask', metadata['projected_crs'])
            layers['urban_envelopes'] = geo('layer_urban_envelopes', 'EPSG:4326')
            return dict(dataset_id=key, metadata=metadata, grid=grid, neighbors=neighbors,
                        climate=read('pixel_months'), **layers)

    def save_run(self, run_id, dataset_id, metadata, ranking):
        with self.engine.begin() as conn:
            conn.execute(text('INSERT INTO spatial_runs VALUES (:run, :dataset, :meta, :ranking)'),
                         {'run': run_id, 'dataset': dataset_id, 'meta': json.dumps(metadata, default=str),
                          'ranking': ranking.to_json(orient='records', double_precision=15)})
