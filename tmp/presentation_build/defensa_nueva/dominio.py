import sqlite3,json,math
from pathlib import Path
r=Path(__file__).resolve().parents[3]
d=json.loads((Path(__file__).parent/'evidence.json').read_text())
with sqlite3.connect(r/'data/processed/parque_solar_spatial.sqlite') as c:
    row=c.execute('SELECT count(*),sum(abs(cell_area_m2-250000)<0.01),min(cell_area_m2),max(cell_area_m2) FROM spatial_cells WHERE dataset_id=? AND valid=1',(d['metadata']['dataset_id'],)).fetchone()
counts=[1,2,6,19,63,216,760,2725,9910,36446]
print(json.dumps({'valid':row[0],'full':row[1],'partial':row[0]-row[1],'min_area_m2':row[2],'max_area_m2':row[3],'forms_1to10':sum(counts),'ideal_placements':sum(counts)*row[0],'ideal_full_placements_bound':sum(counts)*row[1],'ten_cell_forms':36446,'max_area_km2':80/31.3,'sample_fraction_ideal_percent':6309/(sum(counts)*row[0])*100}))
