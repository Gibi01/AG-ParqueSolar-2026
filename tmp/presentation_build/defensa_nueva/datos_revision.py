import sqlite3,json,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).parent
d=json.loads((OUT/'evidence.json').read_text(encoding='utf-8'))
with sqlite3.connect(ROOT/'data/processed/parque_solar_spatial.sqlite') as c:
    pixels=pd.read_sql_query('SELECT climate_pixel_id, MAX(solar_annual_kwh_m2) solar, MIN(solar_annual_kwh_m2) solar_min FROM spatial_cells WHERE dataset_id=? AND valid=1 GROUP BY climate_pixel_id',c,params=[d['metadata']['dataset_id']])
    locations=pd.read_sql_query('SELECT climate_pixel_id, MAX(era5_latitude) latitude, MAX(era5_longitude) longitude FROM pixel_months WHERE dataset_id=? GROUP BY climate_pixel_id',c,params=[d['metadata']['dataset_id']])
    frame=pixels.merge(locations,on='climate_pixel_id',validate='one_to_one')
    assert len(frame)==1370 and abs(frame.solar-frame.solar_min).max()<1e-9
    (OUT/'solar_pixels_verificados.json').write_text(frame.to_json(orient='records'),encoding='utf-8')
ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
notes=[]
with zipfile.ZipFile(ROOT/'output/pptx/Defensa_AG_SantaFe_2026_v2.pptx') as z:
    for i in range(1,28):
        xml=ET.fromstring(z.read(f'ppt/notesSlides/notesSlide{i}.xml'))
        body=next(sp for sp in xml.findall('.//p:sp',ns) if sp.find('.//p:ph',ns) is not None and sp.find('.//p:ph',ns).get('type')=='body')
        note='\n'.join(''.join(p.itertext()) for p in body.findall('.//a:p',ns))
        assert 'DESARROLLO DEL CONTENIDO' in note
        notes.append(note)
(OUT/'notas_actuales.json').write_text(json.dumps(notes,ensure_ascii=False),encoding='utf-8')
print({'pixeles':len(frame),'min':float(frame.solar.min()),'max':float(frame.solar.max()),'notas':len(notes)})
