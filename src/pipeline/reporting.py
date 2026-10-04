"""Export spatial solutions without overwriting historical runs."""
import json
from datetime import datetime, timezone
from uuid import uuid4
from importlib.metadata import version

import geopandas as gpd
import shapely

from src.visualization.map import build_map
from src.visualization.search_charts import write_search_charts
from src.optimization.ranking import territorial_top5

RESULT_DISCLAIMER = (
    "Capacidad de conexión EXPERIMENTAL: no representa capacidad real de las ET. "
    "Energía anual ideal de referencia: sin pérdidas, inclinación ni modelado DC/AC. "
    "Irradiación anual estimada mediante cuatro meses representativos; no integración anual completa. "
    "Las distancias son geográficas, no trazados de conexión ni prueba de viabilidad eléctrica."
)


def write_run_outputs(settings, repo, ga_result, dataset, evaluator):
    if 'urban_mask' not in dataset or dataset['metadata'].get('processing_version') != 3:
        raise ValueError('Falta la máscara urbana INDEC persistida; ejecutá --process.')
    run_id = datetime.now(timezone.utc).strftime('run-%Y%m%dT%H%M%S') + '-' + uuid4().hex[:8]
    output = settings.paths.results / run_id
    output.mkdir(parents=True, exist_ok=False)
    candidates = ga_result.candidates.copy()
    indexed = dataset['grid'].set_index('cell_id')
    selected_ids = set()
    geometries = []
    for raw in candidates.cell_ids:
        ids = json.loads(raw)
        selected_ids.update(ids)
        geometries.append(shapely.union_all(indexed.loc[ids].geometry.to_numpy()))
    candidates['geometry_wkt'] = [geometry.wkt for geometry in geometries]
    ranking = candidates.head(5).copy()
    separation = settings.genetic_algorithm.territorial_separation_km
    territorial = territorial_top5(candidates, separation)
    candidates.to_csv(output / 'candidates.csv', index=False)
    ranking.to_csv(output / 'ranking.csv', index=False)
    territorial.to_csv(output / 'ranking_territorial.csv', index=False)
    ga_result.history.to_csv(output / 'history.csv', index=False)
    write_search_charts(ga_result.history, output / 'evolution.html')
    for frame, name in [(ranking, 'parks.geojson'), (territorial, 'parks_territorial.geojson')]:
        polygons = gpd.GeoDataFrame(frame.drop(columns='geometry_wkt'),
                                   geometry=gpd.GeoSeries.from_wkt(frame.geometry_wkt), crs=dataset['grid'].crs).to_crs(4326)
        (output / name).write_text(polygons.to_json(), encoding='utf-8')
    metadata = dict(run_id=run_id, dataset_id=dataset['dataset_id'],
                    random_seed=ga_result.random_seed,
                    software_versions={name: version(name) for name in ('numpy', 'pandas', 'shapely', 'geopandas', 'pyproj')},
                    configuration=settings.model_dump(mode='json', exclude={'cds_api_key'}),
                    dataset=dataset['metadata'], normalization_bounds=evaluator.bounds,
                    search_version=3,
                    territorial_ranking=dict(requested=5, obtained=len(territorial), candidates=len(candidates),
                                             separation_km=separation, overlap_allowed=False,
                                             incomplete_reason='No hay cinco alternativas compatibles en el archivo retenido.' if len(territorial)<5 else None),
                    energy_formula='P_MW * H_kWh_m2 / (1 kW/m2)', disclaimer=RESULT_DISCLAIMER)
    (output / 'optimization_run.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
    climate = dataset['climate']
    if len(climate):
        valid = climate.loc[climate.complete.astype(bool)]
        counts = valid.groupby(['climate_pixel_id', 'month']).year.nunique().rename('valid_years').reset_index()
        all_pairs = climate[['climate_pixel_id', 'month']].drop_duplicates()
        all_pairs.merge(counts, how='left').fillna({'valid_years': 0}).to_csv(output / 'climate_coverage.csv', index=False)
    selected_ids = {cid for raw in territorial.cell_ids for cid in json.loads(raw)}
    selected_grid = dataset['grid'].loc[dataset['grid'].cell_id.isin(selected_ids)]
    build_map(dataset['region'], selected_grid, dataset['urban_mask'], dataset['lines'], dataset['transformers'],
              territorial, output / 'map.html', grid_resolution_km=settings.grid.resolution_km,
              ranking_description=f'TOP 5 territorial: {len(territorial)}/5 alternativas sin superposición; separación mínima {separation:g} km. No acredita conexión eléctrica.',
              climate_period='enero, abril, julio y octubre; extrapolación estacional')
    repo.save_run(run_id, dataset['dataset_id'], metadata, ranking)
    return dict(ranking_csv=output / 'ranking.csv', history_csv=output / 'history.csv',
                ranking_territorial_csv=output / 'ranking_territorial.csv', evolution_html=output / 'evolution.html',
                parks_geojson=output / 'parks.geojson', map_html=output / 'map.html',
                optimization_run_json=output / 'optimization_run.json')
