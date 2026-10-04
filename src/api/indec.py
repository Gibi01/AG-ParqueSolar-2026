"""Download complete INDEC locality envelopes through its public WFS 2.0 service."""
import hashlib
import json
from datetime import datetime, timezone

import geopandas as gpd
import requests

from src.gis.spatial_operations import repair_urban_envelopes


def fetch_urban_envelopes(source, session=None):
    """Keep national polygons so later margins never depend on a prior crop.

    Ordered pagination, advertised total and unique IDs are checked before
    exposing a source to the exclusion pipeline. A partial download must fail.
    """
    if (not source.wfs_url or not source.layer_name or source.reference_year != 2022
            or not isinstance(source.page_size, int) or source.page_size <= 0):
        raise ValueError('INDEC: configuración de referencia incompleta.')
    session = session or requests.Session()
    features, seen = [], set()
    total = None
    digest = hashlib.sha256()
    while total is None or len(features) < total:
        params = dict(service='WFS', version='2.0.0', request='GetFeature',
                      typeNames=source.layer_name, outputFormat='application/json',
                      srsName='EPSG:4326', count=source.page_size,
                      startIndex=len(features), sortBy='fid')
        response = session.get(source.wfs_url, params=params, timeout=120)
        response.raise_for_status()
        payload = response.json()
        if payload.get('type') != 'FeatureCollection':
            raise ValueError('INDEC: se esperaba un FeatureCollection GeoJSON.')
        matched = payload.get('numberMatched')
        if isinstance(matched, bool) or not isinstance(matched, int) or matched <= 0:
            raise ValueError('INDEC: falta un total nacional verificable (numberMatched).')
        if total is not None and total != matched:
            raise ValueError('INDEC: el total cambió durante la paginación; repetir la descarga.')
        total = matched
        page = payload.get('features', [])
        if not page or payload.get('numberReturned') != len(page):
            raise ValueError('INDEC: descarga incompleta o cantidad de registros inconsistente.')
        for feature in page:
            properties = feature.get('properties', {})
            required = ('fid', 'clc', 'cpr', 'nam', 'codaglo', 'aglomerado')
            if any(key not in properties for key in required):
                raise ValueError('INDEC: faltan identificadores de localidad o aglomerado.')
            if any(properties[key] in (None, '') for key in ('fid', 'clc', 'cpr', 'nam')):
                raise ValueError('INDEC: identificadores de localidad vacíos.')
            identity = feature.get('id')
            if not identity or identity in seen:
                raise ValueError('INDEC: IDs duplicados o ausentes; la paginación no es confiable.')
            seen.add(identity)
        features.extend(page)
        for feature in page:
            digest.update(json.dumps(feature, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode('utf-8'))
        if len(features) > total:
            raise ValueError('INDEC: la descarga excede el total anunciado.')
    frame = gpd.GeoDataFrame.from_features(features, crs='EPSG:4326')
    # Preserve the source geometry; processing records repairs separately.
    repair_urban_envelopes(frame)
    frame['source_feature_id'] = [feature['id'] for feature in features]
    if frame.fid.duplicated().any():
        raise ValueError('INDEC: identificadores nacionales duplicados.')
    metadata = dict(source='INDEC - Localidades censales (Censo 2022)',
                    url=source.wfs_url, layer_name=source.layer_name,
                    reference_year=source.reference_year, native_crs='EPSG:4326',
                    sha256=digest.hexdigest(), national_total_records=total,
                    geometry_type_confirmed='Polygon/MultiPolygon',
                    downloaded_at=datetime.now(timezone.utc).isoformat(),
                    attribution='Instituto Nacional de Estadística y Censos (2022). Marco Geoestadístico Nacional.',
                    metadata_url='https://portalgeoestadistico.indec.gob.ar/geoportal/documents/metadato_localidades_censales.pdf')
    frame.attrs['source_metadata'] = metadata
    return frame, metadata
