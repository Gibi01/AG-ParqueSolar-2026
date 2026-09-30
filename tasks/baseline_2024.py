"""Independent rectangular-park baseline against the immutable saved dataset."""
import json
import sqlite3
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

run = Path('results/spatial/run-20260927T203525-c33c9918')
meta = json.loads((run/'optimization_run.json').read_text())
c = sqlite3.connect(Path(meta['configuration']['paths']['database']).as_uri()+'?mode=ro', uri=True)
key = meta['dataset_id']
grid = pd.read_sql_query('SELECT cell_id,row,column,centroid_x_m,centroid_y_m,solar_annual_kwh_m2 FROM spatial_cells WHERE dataset_id=? AND valid=1 AND component=0 AND abs(cell_area_m2-250000)<0.001', c, params=(key,))
index = pd.MultiIndex.from_frame(grid[['row','column']])
lookup = pd.Series(np.arange(len(grid)), index=index)
positions = np.column_stack([lookup.reindex(pd.MultiIndex.from_arrays([grid.row+dr,grid.column+dc])).to_numpy()
                            for dr in range(2) for dc in range(5)])
positions = positions[np.isfinite(positions).all(axis=1)].astype(int)
coords = grid[['centroid_x_m','centroid_y_m']].to_numpy()[positions].mean(axis=1)
centers = shapely.points(coords)
solar = grid.solar_annual_kwh_m2.to_numpy()[positions].mean(axis=1)
def layer(table):
    f=pd.read_sql_query(f'SELECT * FROM {table} WHERE dataset_id=?',c,params=(key,))
    return gpd.GeoDataFrame(f,geometry=gpd.GeoSeries.from_wkt(f.geometry_wkt),crs=4326).to_crs(meta['dataset']['projected_crs'])
lines=layer('layer_lines'); stations=layer('layer_transformers')
tree=shapely.STRtree(lines.geometry.values)
dl=shapely.distance(centers,lines.geometry.values[tree.nearest(centers)])/1000
dt=np.min(np.stack([shapely.distance(centers,g) for g in stations.geometry]),axis=0)/1000
b=meta['normalization_bounds']; w=meta['configuration']['fitness']
norm=lambda x,k: np.clip((x-b[k][0])/(b[k][1]-b[k][0]),0,1)
fitness=w['weight_solar']*norm(solar,'solar')+w['weight_grid_distance']*(1-norm(dl,'line'))+w['weight_transformer_distance']*(1-norm(dt,'transformer'))+w['weight_installed_power']*78.25/80
i=int(np.argmax(fitness)); ids=grid.cell_id.to_numpy()[positions[i]].tolist()
print(json.dumps(dict(rectangles=len(fitness),better_than_ga=int((fitness>pd.read_csv(run/'ranking.csv').fitness.max()).sum()),fitness=float(fitness[i]),solar=float(solar[i]),line_km=float(dl[i]),station_km=float(dt[i]),cell_ids=ids)))
c.close()
