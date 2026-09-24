"""Contratos del mapa OSM; no realizan solicitudes de red."""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

import folium

from src.visualization.map import OSM_APP_ID, OSM_TILE_URL, add_identified_osm_layer


class OsmTileTests(unittest.TestCase):
    def test_generated_map_identifies_osm_and_keeps_attribution(self) -> None:
        fmap = folium.Map(location=[-30.7, -60.9], tiles=None)
        add_identified_osm_layer(fmap)
        html = fmap.get_root().render()

        self.assertIn(OSM_TILE_URL, html)
        self.assertIn(OSM_APP_ID, html)
        self.assertIn("createIdentifiedOsmTileLayer(", html)
        self.assertIn("openstreetmap.org/copyright", html)
        self.assertNotIn("= L.tileLayer(", html)

    @unittest.skipUnless(shutil.which("node"), "Node.js no está disponible")
    def test_tile_loader_with_mocked_response(self) -> None:
        script = Path(__file__).with_name("osm_tiles.test.js")
        result = subprocess.run(
            ["node", str(script)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
