import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd
import xarray as xr

from src.climate.arco import ArcoSolarService
from src.climate.records import CellPoint


class PixelClimateTests(unittest.TestCase):
    def test_shared_pixel_and_incomplete_month_exclusion(self):
        times = pd.date_range('2020-01-01', '2020-01-31 23:00', freq='h')
        values = np.full((len(times), 1, 2), 3.6e6)
        values[0, 0, 1] = np.nan
        ds = xr.Dataset({'ssrd': (('time', 'latitude', 'longitude'), values)},
                        coords={'time': times, 'latitude': [-30.], 'longitude': [-61., -60.]}).chunk({'latitude': 1, 'longitude': 2})
        with tempfile.TemporaryDirectory() as directory:
            settings = SimpleNamespace(paths=SimpleNamespace(arco_cache=Path(directory)),
                                       climate=SimpleNamespace(year_months=[(2020, 1)]))
            service = ArcoSolarService(settings)
            with patch.object(service, '_open', return_value=ds):
                result = service.get_monthly_radiation([
                    CellPoint(1, -30., -61.), CellPoint(2, -30.001, -61.), CellPoint(3, -30., -60.)])
            self.assertEqual(len(result.cell_pixels), 3)
            self.assertEqual(len(result.records), 2)
            self.assertEqual(result.cell_pixels.climate_pixel_id.nunique(), 2)
            valid = result.records[result.records.complete]
            self.assertEqual(len(valid), 1)
            self.assertAlmostEqual(valid.iloc[0].radiation_kwh_m2, 744.)
            self.assertTrue(result.records.loc[~result.records.complete, 'radiation_kwh_m2'].isna().all())

    def test_duplicate_timestamp_is_not_complete(self):
        from src.climate.arco import summarize_month
        times = pd.date_range('2020-04-01', periods=720, freq='h')
        times = times[:-1].append(times[:1])
        monthly, counts = summarize_month(np.ones((720, 1, 1)), times, 2020, 4)
        self.assertEqual(counts[0, 0], 0)

    def test_annual_extrapolation_and_missing_month(self):
        from src.climate.climatology import annual_solar_kwh_m2
        frame = pd.DataFrame([{'climate_pixel_id': 'p', 'year': 2020, 'month': m,
                               'radiation_kwh_m2': days * 5} for m, days in [(1, 31), (4, 30), (7, 31), (10, 31)]])
        self.assertAlmostEqual(annual_solar_kwh_m2(frame, [1, 4, 7, 10])['p'], 365.25 * 5)
        frame.loc[frame.month == 4, 'radiation_kwh_m2'] = np.nan
        self.assertTrue(np.isnan(annual_solar_kwh_m2(frame, [1, 4, 7, 10])['p']))
