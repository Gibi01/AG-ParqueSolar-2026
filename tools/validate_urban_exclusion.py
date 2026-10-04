"""Audit INDEC margins on an existing grid without changing historical snapshots.

Run from the repository: python -m tools.validate_urban_exclusion --run <directory>
Outputs sensitivity tables and a Rosario map; this does not calibrate a margin.
"""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3

import folium
import geopandas as gpd
import pandas as pd
import shapely

from src.config.settings import load_settings, PROJECT_ROOT
from src.gis.spatial_operations import build_urban_mask, prepare_urban_mask, urban_exclusion_mask
from src.pipeline.ingest import ingest_urban_areas


def audit(run_dir, output, settings):
    metadata = json.loads((run_dir / 'optimization_run.json').read_text(encoding='utf-8'))
    crs = metadata['dataset']['projected_crs']
    database = Path(metadata['configuration']['paths']['database'])
    if not database.is_absolute():
        database = PROJECT_ROOT / database
    dataset_id = metadata['dataset_id']
    output.mkdir(parents=True, exist_ok=False)
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as connection:
        frame = pd.read_sql('SELECT geometry_wkt FROM layer_region WHERE dataset_id = ?',
                            connection, params=(dataset_id,))
        region = gpd.GeoDataFrame(geometry=gpd.GeoSeries.from_wkt(frame.geometry_wkt), crs=4326)
        source = ingest_urban_areas(settings, region)
        envelopes = source.gdf
        rosario = envelopes.loc[envelopes.nam.eq('Rosario') & envelopes.cpr.eq('82')]
        if len(rosario) != 1 or rosario.iloc[0].codaglo in ('N/A', '', None):
            raise ValueError('No se identificó un componente único de Rosario con código de aglomerado.')
        code = rosario.iloc[0].codaglo
        gran_rosario = envelopes.loc[envelopes.codaglo.eq(code)]
        masks, summaries = {}, []
        for margin_m in (0, 100, 250, 500):
            _, mask = prepare_urban_mask(envelopes, region, margin_m / 1000, crs, True)
            masks[margin_m] = mask
            summaries.append(dict(margin_m=margin_m, **mask.attrs,
                                  excluded_cells=0, newly_excluded_cells=0,
                                  formerly_excluded_now_available_cells=0))
        total, old_urban_excluded = 0, 0
        chunks = pd.read_sql(
            'SELECT cell_id, geometry_wkt, invalid_reason FROM spatial_cells WHERE dataset_id = ?',
            connection, params=(dataset_id,), chunksize=20000)
        for chunk in chunks:
            grid = gpd.GeoDataFrame(chunk.drop(columns='geometry_wkt'),
                geometry=gpd.GeoSeries.from_wkt(chunk.geometry_wkt, index=chunk.index), crs=crs)
            old = grid.invalid_reason.eq('intersects_urban_area')
            total += len(grid)
            old_urban_excluded += int(old.sum())
            for summary in summaries:
                excluded = urban_exclusion_mask(grid, masks[summary['margin_m']])
                summary['excluded_cells'] += int(excluded.sum())
                summary['newly_excluded_cells'] += int((excluded & ~old).sum())
                summary['formerly_excluded_now_available_cells'] += int((~excluded & old).sum())
        for summary in summaries:
            summary.update(total_cells=total, old_urban_excluded_cells=old_urban_excluded)
        ranking = pd.read_csv(run_dir / 'ranking_territorial.csv')
        row = ranking.loc[ranking.station_id.eq('RO')].iloc[0]
        park = shapely.from_wkt(row.geometry_wkt)
        ids = json.loads(row.cell_ids)
        placeholders = ','.join('?' for _ in ids)
        selected = pd.read_sql(
            f'SELECT cell_id, geometry_wkt FROM spatial_cells WHERE dataset_id = ? AND cell_id IN ({placeholders})',
            connection, params=(dataset_id, *ids))
        selected = gpd.GeoDataFrame(selected.drop(columns='geometry_wkt'),
            geometry=gpd.GeoSeries.from_wkt(selected.geometry_wkt), crs=crs)
        raw = gran_rosario.to_crs(crs).geometry.union_all()
        rosario_rows = []
        for margin_m in (0, 100, 250, 500):
            mask = build_urban_mask(gran_rosario, margin_m / 1000, crs, True)
            excluded = urban_exclusion_mask(selected, mask)
            rosario_rows.append(dict(margin_m=margin_m,
                park_area_ha=park.area / 1e4,
                raw_overlap_ha=park.intersection(raw).area / 1e4,
                mask_overlap_ha=park.intersection(mask.geometry.union_all()).area / 1e4,
                excluded_cells=int(excluded.sum()),
                excluded_cell_ids=json.dumps(selected.loc[excluded, 'cell_id'].tolist()),
                **mask.attrs))
        historical_rows = []
        for historical in sorted(run_dir.parent.glob('run-*')):
            meta_path = historical / 'optimization_run.json'
            if not meta_path.exists():
                continue
            info = json.loads(meta_path.read_text(encoding='utf-8'))
            for name in ('ranking.csv', 'ranking_territorial.csv'):
                if not (historical / name).exists():
                    continue
                data = pd.read_csv(historical / name)
                geometry = gpd.GeoSeries.from_wkt(data.geometry_wkt,
                    crs=info['dataset']['projected_crs']).to_crs(crs)
                for margin_m, mask in masks.items():
                    union = mask.geometry.union_all()
                    for index, candidate in data.iterrows():
                        polygon = geometry.iloc[index]
                        historical_rows.append(dict(run_id=historical.name, ranking=name,
                            rank=int(candidate['rank']), margin_m=margin_m,
                            intersects_urban=bool(polygon.intersects(union)),
                            overlap_ha=polygon.intersection(union).area / 1e4))
    pd.DataFrame(summaries).to_csv(output / 'provincial_sensitivity.csv', index=False)
    pd.DataFrame(rosario_rows).to_csv(output / 'rosario_sensitivity.csv', index=False)
    pd.DataFrame(historical_rows).to_csv(output / 'historical_parks.csv', index=False)
    gran_rosario.drop(columns='source_feature_id', errors='ignore').to_file(output / 'gran_rosario.geojson', driver='GeoJSON')
    masks[0].to_crs(4326).to_file(output / 'urban_mask.geojson', driver='GeoJSON')
    source.metadata.update(audited_run=run_dir.name, agglomeration_code=code,
                           agglomeration_components=len(gran_rosario),
                           margins_m=[0, 100, 250, 500],
                           calibration_status='Sensitivity only; requires independent recent reference.')
    (output / 'provenance.json').write_text(json.dumps(source.metadata, indent=2, ensure_ascii=False), encoding='utf-8')
    fmap = folium.Map(location=[row.latitude, row.longitude], zoom_start=12)
    folium.GeoJson(gran_rosario.to_json(), name='Envolventes originales INDEC 2022',
        tooltip=folium.GeoJsonTooltip(fields=['nam', 'codaglo']),
        style_function=lambda _: dict(color='#d62728', fillOpacity=.15, weight=1)).add_to(fmap)
    folium.GeoJson(gpd.GeoSeries([park], crs=crs).to_crs(4326).to_json(),
        name='Parque histórico: 250 ha',
        style_function=lambda _: dict(color='#0033cc', fillOpacity=.45, weight=3)).add_to(fmap)
    folium.LayerControl().add_to(fmap)
    fmap.get_root().html.add_child(folium.Element(
        '<div style="position:fixed;bottom:25px;left:10px;background:white;padding:10px;z-index:9999">'
        'Fuente: Instituto Nacional de Estadística y Censos (2022). Marco Geoestadístico Nacional.<br>'
        'Contornos censales; margen 0 m. Validación del parque histórico, no propuesta de emplazamiento.</div>'))
    fmap.save(output / 'rosario_map.html')
    print(pd.DataFrame(rosario_rows)[['margin_m', 'raw_overlap_ha', 'mask_overlap_ha', 'excluded_cells']].to_string(index=False))
    print(pd.DataFrame(summaries)[['margin_m', 'excluded_cells', 'newly_excluded_cells',
                                  'formerly_excluded_now_available_cells']].to_string(index=False))
    print(f'Resultados: {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='Directorio nuevo, no se sobrescribe.')
    parser.add_argument('--config', default='config.yaml')
    args = parser.parse_args()
    audit(args.run.resolve(), args.output.resolve(), load_settings(args.config))
