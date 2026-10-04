"""Offline regression coverage for complete, reproducible INDEC WFS reads."""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import geopandas as gpd
import requests
from shapely.geometry import mapping, box, Point

from src.api.indec import fetch_urban_envelopes
from src.config.settings import Settings, load_settings
from src.main import cmd_optimize
from src.pipeline.ingest import ingest_urban_areas


def source(**overrides):
    values = dict(wfs_url='https://example.test/geoserver/wfs',
                  layer_name='geonode:localidades_censales',
                  reference_year=2022, page_size=1)
    values.update(overrides)
    return SimpleNamespace(**values)


def feature(identifier):
    return dict(type='Feature', id=f'localidades.{identifier}',
                properties=dict(fid=identifier, id=f'lc-{identifier}',
                                clc=f'820{identifier:05d}', cpr='82',
                                nam=f'Localidad {identifier}', codaglo='004',
                                aglomerado='Gran Rosario'),
                geometry=mapping(box(-60.8 + identifier * .01, -33,
                                     -60.795 + identifier * .01, -32.995)))


def page(features, total=2):
    return dict(type='FeatureCollection', numberMatched=total,
                numberReturned=len(features), features=features)


class FakeResponse:
    def __init__(self, payload, http_error=False):
        self.payload = payload
        self.http_error = http_error

    def raise_for_status(self):
        if self.http_error:
            raise requests.HTTPError('503 Service Unavailable')

    def json(self):
        return copy.deepcopy(self.payload)


class FakeSession:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def get(self, url, params=None, **kwargs):
        self.calls.append((url, dict(params or {})))
        return next(self.responses)


def session(*pages):
    return FakeSession([FakeResponse(payload) for payload in pages])


class IndecIngestionTests(unittest.TestCase):
    def test_old_bahra_configuration_is_rejected(self):
        configuration = load_settings().model_dump()
        for field in ('include_types', 'resource_id'):
            candidate = copy.deepcopy(configuration)
            if field == 'include_types':
                candidate['urban_exclusion'][field] = ['LOCALIDAD']
            else:
                candidate['infrastructure']['urban_areas'] = {field: 'old-bahra-resource'}
            with self.subTest(field=field), self.assertRaises(ValueError):
                Settings.model_validate(candidate)

    def test_incomplete_cached_source_is_rejected(self):
        configured = load_settings()
        frame = gpd.GeoDataFrame.from_features([feature(1)], crs=4326)
        metadata = dict(url=configured.infrastructure.urban_areas.wfs_url,
                        layer_name=configured.infrastructure.urban_areas.layer_name,
                        reference_year=2022, national_total_records=2, sha256='abc')
        cache = MagicMock()
        cache.exists.return_value = True
        cache.load.return_value = frame, metadata
        with self.assertRaisesRegex(ValueError, 'caché INDEC'):
            ingest_urban_areas(configured, frame, cache=cache)

    def test_updated_source_requires_processing_before_optimization(self):
        configured = load_settings()
        repo = MagicMock()
        repo.load_dataset.return_value = {'metadata': {'urban_source': {'sha256': 'old'}}}
        with tempfile.TemporaryDirectory() as directory:
            cache = SimpleNamespace(cache_dir=Path(directory))
            path = cache.cache_dir / 'urban_areas_envelopes.meta.json'
            path.write_text(json.dumps({'sha256': 'new'}), encoding='utf-8')
            with patch('src.main.layer_cache_for_settings', return_value=cache):
                with self.assertRaisesRegex(RuntimeError, 'INDEC cambió'):
                    cmd_optimize(configured, repo)

    def test_pagination_preserves_properties_and_source_provenance(self):
        client = session(page([feature(1)]), page([feature(2)]))
        data, metadata = fetch_urban_envelopes(source(), session=client)
        self.assertIsInstance(data, gpd.GeoDataFrame)
        self.assertEqual(data.crs.to_epsg(), 4326)
        self.assertEqual(len(data), 2)
        for key in ('fid', 'id', 'clc', 'cpr', 'nam', 'codaglo', 'aglomerado'):
            self.assertEqual(data[key].tolist(),
                             [feature(i)['properties'][key] for i in (1, 2)])
        self.assertTrue(data.geometry.geom_type.eq('Polygon').all())
        self.assertEqual([call[1]['startIndex'] for call in client.calls], [0, 1])
        self.assertTrue(all(call[1]['count'] == 1 for call in client.calls))
        self.assertTrue(all(call[1]['sortBy'].lower() == 'fid' for call in client.calls))
        self.assertTrue(all(call[0] == source().wfs_url for call in client.calls))
        self.assertEqual(data.source_feature_id.tolist(), ['localidades.1', 'localidades.2'])
        self.assertEqual(metadata['national_total_records'], 2)
        self.assertEqual(metadata['reference_year'], 2022)
        self.assertEqual(metadata['url'], source().wfs_url)
        self.assertEqual(metadata['layer_name'], source().layer_name)
        self.assertRegex(metadata['sha256'], r'^[0-9a-f]{64}$')

    def test_source_digest_is_reproducible_and_changes_with_geometry(self):
        _, first = fetch_urban_envelopes(source(), session=session(
            page([feature(1)]), page([feature(2)])))
        _, repeated = fetch_urban_envelopes(source(), session=session(
            page([feature(1)]), page([feature(2)])))
        changed = feature(2)
        changed['geometry'] = mapping(box(-60.8, -33, -60.7, -32.9))
        _, different = fetch_urban_envelopes(source(), session=session(
            page([feature(1)]), page([changed])))
        self.assertEqual(first['sha256'], repeated['sha256'])
        self.assertNotEqual(first['sha256'], different['sha256'])

    def test_truncated_collection_is_rejected(self):
        with self.assertRaises(ValueError):
            fetch_urban_envelopes(source(), session=session(
                page([feature(1)]), page([])))

    def test_changed_total_and_inconsistent_returned_count_are_rejected(self):
        with self.assertRaises(ValueError):
            fetch_urban_envelopes(source(), session=session(
                page([feature(1)]), page([feature(2)], total=3)))
        inconsistent = page([feature(1)], total=1)
        inconsistent['numberReturned'] = 2
        with self.assertRaises(ValueError):
            fetch_urban_envelopes(source(), session=session(inconsistent))

    def test_ignored_pagination_and_duplicate_feature_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            fetch_urban_envelopes(source(), session=session(
                page([feature(1)]), page([feature(1)])))
        duplicate = feature(2)
        duplicate['id'] = feature(1)['id']
        with self.assertRaises(ValueError):
            fetch_urban_envelopes(source(), session=session(
                page([feature(1)]), page([duplicate])))

    def test_http_failure_is_propagated(self):
        client = FakeSession([FakeResponse({}, http_error=True)])
        with self.assertRaises(requests.HTTPError):
            fetch_urban_envelopes(source(), session=client)

    def test_duplicate_fid_with_distinct_geojson_ids_is_rejected(self):
        duplicate = feature(2)
        duplicate['properties']['fid'] = 1
        with self.assertRaises(ValueError):
            fetch_urban_envelopes(source(), session=session(
                page([feature(1)]), page([duplicate])))

    def test_shared_locality_code_across_provinces_is_preserved(self):
        second_province = feature(2)
        second_province['properties']['clc'] = feature(1)['properties']['clc']
        second_province['properties']['cpr'] = '66'
        data, _ = fetch_urban_envelopes(source(), session=session(
            page([feature(1)]), page([second_province])))
        self.assertEqual(len(data), 2)
        self.assertEqual(data.cpr.tolist(), ['82', '66'])

    def test_locality_without_agglomeration_can_have_null_agglomeration_fields(self):
        standalone = feature(1)
        standalone['properties'].update(codaglo=None, aglomerado=None)
        data, _ = fetch_urban_envelopes(source(), session=session(page([standalone], total=1)))
        self.assertEqual(len(data), 1)

    def test_empty_source_and_nonpolygonal_geometry_are_rejected(self):
        with self.assertRaises(ValueError):
            fetch_urban_envelopes(source(), session=session(page([], total=0)))
        for geometry in (None, mapping(Point(-60.7, -32.9)),
                         dict(type='Polygon', coordinates=[])):
            bad = feature(1)
            bad['geometry'] = geometry
            with self.subTest(geometry=geometry):
                with self.assertRaises(ValueError):
                    fetch_urban_envelopes(source(), session=session(page([bad], total=1)))

    def test_missing_critical_properties_are_rejected(self):
        for field in ('fid', 'clc', 'cpr', 'nam', 'codaglo', 'aglomerado'):
            bad = feature(1)
            del bad['properties'][field]
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    fetch_urban_envelopes(source(), session=session(page([bad], total=1)))

    def test_incomplete_source_reference_is_rejected_before_http(self):
        for overrides in ({'wfs_url': ''}, {'layer_name': ''},
                          {'reference_year': None}, {'page_size': 0}):
            client = session()
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    fetch_urban_envelopes(source(**overrides), session=client)
                self.assertEqual(client.calls, [])
