import tempfile
import unittest
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from src.visualization.map import build_map


class TopFiveMapTests(unittest.TestCase):
    def test_five_separate_visible_layers_and_bounds_cover_all_five(self):
        region = gpd.GeoDataFrame(geometry=[box(500000, 6600000, 560000, 6601000)], crs=32720)
        empty = gpd.GeoDataFrame(geometry=[], crs=32720)
        rows = []
        for rank in range(1, 7):
            rows.append(dict(rank=rank, geometry_wkt=box(500000 + rank * 5000, 6600000,
                             500500 + rank * 5000, 6600500).wkt,
                             fitness=.8, number_of_cells=1, park_area_km2=.25, park_area_ha=25,
                             installed_power_mw=7.825, max_connection_capacity_mw=80,
                             capacity_used_percent=9.78125, solar_annual_kwh_m2=float('nan'),
                             distance_to_transformer_km=float('nan'), distance_to_power_line_km=float('nan')))
        # Input order must not determine which parks are selected.
        ranking = pd.DataFrame(rows).iloc[::-1]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'map.html'
            build_map(region, region, empty, empty, empty, ranking, output)
            html = output.read_text(encoding='utf-8')
        for rank in range(1, 6):
            self.assertIn(f'TOP 5 - Parque #{rank}', html)
            self.assertIn(f'Candidato #{rank}', html)
        self.assertNotIn('Parque #6', html)
        bounds = gpd.GeoSeries.from_wkt([row['geometry_wkt'] for row in rows[:5]], crs=32720).to_crs(4326).total_bounds
        self.assertIn(str([[float(bounds[1]), float(bounds[0])], [float(bounds[3]), float(bounds[2])]]), html)
        self.assertIn('pueden superponerse', html)


if __name__ == '__main__':
    unittest.main()
