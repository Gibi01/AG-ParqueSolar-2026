import json,sqlite3
from pathlib import Path
import geopandas as gpd
import pandas as pd
ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).parent
d=json.loads((OUT/'evidence.json').read_text(encoding='utf-8'))
with sqlite3.connect(ROOT/'data/processed/parque_solar_spatial.sqlite') as c:
    rows=pd.read_sql_query('SELECT climate_pixel_id, AVG(latitude) latitude, AVG(longitude) longitude, MAX(solar_annual_kwh_m2) solar FROM spatial_cells WHERE dataset_id=? AND valid=1 GROUP BY climate_pixel_id',c,params=[d['metadata']['dataset_id']])
    layers={}
    for n in ['lines','transformers']:
        f=pd.read_sql_query('SELECT * FROM layer_'+n+' WHERE dataset_id=?',c,params=[d['metadata']['dataset_id']]).drop(columns='dataset_id')
        g=gpd.GeoDataFrame(f.drop(columns='geometry_wkt'),geometry=gpd.GeoSeries.from_wkt(f.geometry_wkt),crs=4326)
        layers[n]=json.loads(g.to_json())
    (OUT/'mapdata.json').write_text(json.dumps(dict(solar=rows.to_dict('records'),**layers),ensure_ascii=False),encoding='utf-8')
print('pixels',len(rows))
