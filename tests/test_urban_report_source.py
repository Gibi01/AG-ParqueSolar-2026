"""Reports must describe the source in each run, including historical BAHRA runs."""
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch


class UrbanReportSourceTests(unittest.TestCase):
    def module(self, indec):
        source = {'provider': 'INDEC'} if indec else {'resource_id': 'bahra'}
        configuration = dict(infrastructure={'urban_areas': source},
                             urban_exclusion={'buffer_km': 0 if indec else 3, 'fill_holes': True},
                             genetic_algorithm={}, fitness={})
        current = SimpleNamespace(RUN=dict(configuration=configuration, metadata={}, first=None))
        path = Path(__file__).resolve().parents[1] / 'tools/reporting/report_content.py'
        with patch.dict(sys.modules, {'current_run': current}):
            return runpy.run_path(str(path))

    def test_new_report_describes_indec_margin_and_hole_policy(self):
        module = self.module(True)
        description = module['urban_method_description']()
        self.assertIn('INDEC del Censo 2022', description)
        self.assertIn('margen de 0 km', description)
        self.assertIn('huecos interiores', description)
        self.assertIn('Instituto Nacional de Estadística y Censos', module['REFERENCES'][9])

    def test_old_report_keeps_its_actual_bahra_source(self):
        module = self.module(False)
        self.assertIn('BAHRA', module['urban_method_description']())
        self.assertIn('3 km', module['urban_method_description']())
        self.assertIn('Localidades BAHRA', module['REFERENCES'][9])
