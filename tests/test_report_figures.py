import sys
import unittest
from pathlib import Path

import pandas as pd
from PIL import Image
from shapely.geometry import box


REPORTING = Path(__file__).resolve().parents[1] / "tools" / "reporting"
TMP = Path(__file__).resolve().parents[1] / "tmp"
sys.path.insert(0, str(REPORTING))
import build_figures  # noqa: E402


class ReportFigureTests(unittest.TestCase):
    def test_territorial_map_draws_the_province_behind_the_candidates(self):
        ranking = pd.DataFrame([
            {"rank": 1, "longitude": -61.0, "latitude": -31.0, "station_id": "ST"},
        ])
        province = box(-62.5, -34.0, -59.0, -28.5)

        output = TMP / "test_report_map.png"
        self.addCleanup(output.unlink, missing_ok=True)
        build_figures.territorial_map(ranking=ranking, province=province, output=output)
        with Image.open(output) as image:
            province_pixels = dict((color, count) for count, color in image.getcolors(2_000_000)).get(
                (232, 236, 232), 0
            )

        self.assertGreater(province_pixels, 10_000)


if __name__ == "__main__":
    unittest.main()
