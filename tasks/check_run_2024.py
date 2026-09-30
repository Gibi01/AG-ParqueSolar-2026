"""Read-only numerical audit of the saved run; regenerate only a separate map."""
import json
import sqlite3
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from src.visualization.map import build_map

run = Path('results/spatial/run-20260927T203525-c33c9918')
meta = json.loads((run / 'optimization_run.json').read_text(encoding='utf-8'))
ranking = pd.read_csv(run / 'ranking.csv')
db = Path(meta['configuration']['paths']['database'])
connection = sqlite3.connect(db.as_uri() + '?mode=ro', uri=True)
key = meta['dataset_id']
crs = meta['dataset']['projected_crs']

def read(table):
    return pd.read_sql_query(f'SELECT * FROM {table} WHERE dataset_id=?', connection, params=(key,)).drop(columns='dataset_id')

def geo(table, projection):
    frame = read(table)
    return gpd.GeoDataFrame(frame.drop(columns='geometry_wkt'), geometry=gpd.GeoSeries.from_wkt(frame.geometry_wkt), crs=projection)

grid = geo('spatial_cells', crs).set_index('cell_id', drop=False)
lines = geo('layer_lines', 4326).to_crs(crs)
stations = geo('layer_transformers', 4326).to_crs(crs)
region = geo('layer_region', 4326).to_crs(crs)
urban = geo('layer_urban', 4326).to_crs(crs)
buffers = urban.copy()
buffers.geometry = buffers.buffer(meta['configuration']['urban_exclusion']['buffer_km'] * 1000)
climate = read('pixel_months')
tree = shapely.STRtree(lines.geometry.values)
bounds = meta['normalization_bounds']
weights = meta['configuration']['fitness']
density = meta['configuration']['park']['pv_power_density_mw_per_km2']
capacity = meta['configuration']['park']['max_connection_capacity_mw']
region_shape = region.geometry.union_all()
urban_shape = buffers.geometry.union_all()
checks = []
for row in ranking.itertuples():
    cells = grid.loc[json.loads(row.cell_ids)]
    shape = cells.geometry.union_all()
    center = shape.centroid
    area = shape.area / 1e6
    solar = np.average(cells.solar_annual_kwh_m2, weights=cells.geometry.area)
    nearest = int(tree.nearest(center))
    dl = center.distance(lines.geometry.iloc[nearest]) / 1000
    dt = stations.distance(center) / 1000
    norm = lambda value, name: float(np.clip((value - bounds[name][0]) / (bounds[name][1] - bounds[name][0]), 0, 1))
    fitness = (weights['weight_solar'] * norm(solar, 'solar') + weights['weight_grid_distance'] * (1 - norm(dl, 'line'))
               + weights['weight_transformer_distance'] * (1 - norm(dt.min(), 'transformer'))
               + weights['weight_installed_power'] * area * density / capacity)
    assert cells.valid.astype(bool).all()
    assert shape.is_valid and shape.geom_type == 'Polygon'
    assert shape.difference(region_shape).area < .01
    assert shape.intersection(urban_shape).area < .01
    assert shape.equals(shapely.from_wkt(row.geometry_wkt))
    assert area * density <= capacity
    assert abs(area - row.park_area_km2) < 1e-8
    assert abs(area * density - row.installed_power_mw) < 1e-8
    assert abs(solar - row.solar_annual_kwh_m2) < 1e-8
    assert abs(dl - row.distance_to_power_line_km) < 1e-8
    assert abs(dt.min() - row.distance_to_transformer_km) < 1e-8
    assert abs(fitness - row.fitness) < 1e-8
    pixels = climate.loc[climate.climate_pixel_id.isin(cells.climate_pixel_id)]
    assert pixels.complete.astype(bool).all()
    checks.append(dict(rank=row.rank, fitness=fitness, nearest_line_voltage=int(lines.tension_v.iloc[nearest]),
                       climate_pixels=cells.climate_pixel_id.nunique(), monthly_records=len(pixels),
                       max_fitness_error=abs(fitness-row.fitness)))
print('AUDIT', json.dumps(checks))
print('VOLTAGES', lines.tension_v.value_counts().to_dict())
top = [set(json.loads(raw)) for raw in ranking.head(5).cell_ids]
print('TOP5_SHARED_CELLS', len(set.intersection(*top)), 'UNION', len(set.union(*top)))
print('COVERAGE', climate.groupby(['year','month']).complete.agg(['count','sum']).to_string())
print('HISTORY', pd.read_csv(run/'history.csv').iloc[[0,-1]].to_json(orient='records'))
selected = grid.loc[sorted(set.union(*top))].reset_index(drop=True)
build_map(region, selected, buffers, lines, stations, ranking, run/'map_top5.html',
          grid_resolution_km=.5, climate_period='2024-2026: 11 meses representativos; extrapolación estacional')
print('MAP', run/'map_top5.html')
connection.close()
