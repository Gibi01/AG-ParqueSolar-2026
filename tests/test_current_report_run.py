import copy
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/reporting'))
import current_run


class CurrentReportRunTests(unittest.TestCase):
    def test_accepts_complete_current_metadata(self):
        with patch.object(Path, 'read_text', return_value=json.dumps(current_run.RUN['metadata'])):
            self.assertTrue(current_run.is_current_run(Path('run')))

    def test_rejects_incompatible_region_source_and_model(self):
        changes = [
            (('configuration', 'region', 'name'), 'Región inválida'),
            (('configuration', 'region', 'admin_source', 'code_value'), '00'),
            (('configuration', 'infrastructure', 'urban_areas', 'provider'), 'unsupported'),
            (('dataset', 'processing_version'), 0),
            (('search_version',), 0),
            (('fitness_version',), 0),
        ]
        for keys, value in changes:
            with self.subTest(field=keys):
                metadata = copy.deepcopy(current_run.RUN['metadata'])
                target = metadata
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = value
                with patch.object(Path, 'read_text', return_value=json.dumps(metadata)):
                    self.assertFalse(current_run.is_current_run(Path('run')))
