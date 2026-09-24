"""results/map.html — visualización con GeoPandas + Folium.

Muestra el límite provincial, la grilla de análisis, los buffers de
exclusión urbana, las líneas eléctricas, las estaciones transformadoras,
y las ubicaciones del TOP-10, cada una como una capa que se puede activar/desactivar.
"""

from __future__ import annotations

from pathlib import Path

import folium
import geopandas as gpd
import pandas as pd
import shapely
from branca.element import Element, Template
from folium.utilities import camelize

from src.gis.crs import GEOGRAPHIC_CRS

# ~1m de precisión en estas latitudes — de sobra para una visualización a
# escala provincial, pero recorta la precisión de punto flotante (y por
# ende el tamaño de archivo) que folium/GeoJson heredaría de la
# reproyección de pyproj.
MAP_COORDINATE_PRECISION_DEG = 0.00001
OSM_TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
OSM_APP_ID = "AG-ParqueSolar-2026"
OSM_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'


class IdentifiedOsmTileLayer(folium.TileLayer):
    """Capa OSM identificada para HTML abierto directamente desde file://."""

    _template = Template(
        """
        {% macro script(this, kwargs) %}
        var {{ this.get_name() }} = createIdentifiedOsmTileLayer(
            L, {{ this.tiles|tojson }}, {{ this.js_options|tojson }}, {{ this.app_id|tojson }}
        );
        {% if this.show %}{{ this.get_name() }}.addTo({{ this._parent.get_name() }});{% endif %}
        {% endmacro %}
        """
    )

    def __init__(self) -> None:
        super().__init__(tiles=OSM_TILE_URL, attr=OSM_ATTRIBUTION, name="OpenStreetMap")
        self.app_id = OSM_APP_ID
        self.js_options = {camelize(key): value for key, value in self.options.items()}


def add_identified_osm_layer(fmap: folium.Map) -> None:
    source = Path(__file__).with_name("osm_tiles.js").read_text(encoding="utf-8")
    fmap.get_root().header.add_child(Element(f"<script>\n{source}\n</script>"))
    IdentifiedOsmTileLayer().add_to(fmap)


def _to_geographic(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        gdf = gdf.set_crs(GEOGRAPHIC_CRS)
    else:
        gdf = gdf.to_crs(GEOGRAPHIC_CRS)
    gdf = gdf.copy()
    gdf["geometry"] = shapely.set_precision(gdf.geometry.values, MAP_COORDINATE_PRECISION_DEG)
    return gdf


def build_map(
    region_gdf: gpd.GeoDataFrame,
    grid_gdf: gpd.GeoDataFrame,
    urban_buffered_gdf: gpd.GeoDataFrame,
    power_lines_gdf: gpd.GeoDataFrame,
    transformers_gdf: gpd.GeoDataFrame,
    top10_df: pd.DataFrame,
    output_path: Path,
    grid_resolution_km: float = 5,
    climate_period: str = "",
) -> Path:
    region_geo = _to_geographic(region_gdf)
    center = region_geo.geometry.union_all().centroid

    fmap = folium.Map(location=[center.y, center.x], zoom_start=7, tiles=None)
    add_identified_osm_layer(fmap)
    if climate_period:
        folium.Element(
            f'<div style="position:fixed;top:12px;left:50px;z-index:9999;background:white;'
            f'padding:8px;border:1px solid #777">Grilla {grid_resolution_km:g} km · '
            f'Radiación media: {climate_period}</div>'
        ).add_to(fmap.get_root().html)

    folium.GeoJson(
        region_geo[["geometry"]],
        name="Límite provincial",
        style_function=lambda _: {"color": "#222222", "weight": 2, "fillOpacity": 0},
    ).add_to(fmap)

    # Las capas de grilla y de líneas eléctricas pueden llevar decenas de
    # miles de vértices (5 mil+ celdas de grilla, 46 mil+ segmentos de
    # línea a resolución completa) — se simplifican acá puramente por
    # tamaño de archivo del mapa / renderizado en el navegador, nunca para
    # las geometrías analíticas subyacentes usadas en el resto del pipeline.
    simplify_tolerance_m = 25.0

    grid_layer = folium.FeatureGroup(name=f"Grilla de análisis ({grid_resolution_km:g} km)", show=False)
    grid_simplified = grid_gdf.copy()
    grid_simplified["geometry"] = grid_simplified.geometry.simplify(simplify_tolerance_m)
    folium.GeoJson(
        _to_geographic(grid_simplified)[["geometry"]],
        style_function=lambda _: {"color": "#999999", "weight": 0.4, "fillOpacity": 0},
    ).add_to(grid_layer)
    grid_layer.add_to(fmap)

    if len(urban_buffered_gdf) > 0:
        urban_layer = folium.FeatureGroup(name="Zonas urbanas excluidas (buffer)", show=True)
        folium.GeoJson(
            _to_geographic(urban_buffered_gdf)[["geometry"]],
            style_function=lambda _: {"color": "#d62728", "weight": 1, "fillColor": "#d62728", "fillOpacity": 0.25},
        ).add_to(urban_layer)
        urban_layer.add_to(fmap)

    if len(power_lines_gdf) > 0:
        lines_layer = folium.FeatureGroup(name="Líneas eléctricas (por tensión)", show=True)
        # Disolver segmentos por tensión reduce las features del mapa; la
        # simplificación solo afecta la visualización, no el análisis.
        lines_proj = power_lines_gdf.to_crs(grid_gdf.crs)
        dissolved = lines_proj.dissolve(by="tension_v").reset_index()
        dissolved["geometry"] = dissolved.geometry.simplify(simplify_tolerance_m)
        dissolved_geo = _to_geographic(dissolved)
        voltage_styles = {
            7620: {"color": "#fdd0a2", "weight": 1},
            13200: {"color": "#fdae6b", "weight": 1.5},
            33000: {"color": "#e6550d", "weight": 2.5},
            132000: {"color": "#a63603", "weight": 4},
        }
        default_style = {"color": "#ff7f0e", "weight": 1.5}
        for _, row in dissolved_geo.iterrows():
            style = voltage_styles.get(row["tension_v"], default_style)
            folium.GeoJson(
                gpd.GeoSeries([row.geometry], crs=GEOGRAPHIC_CRS).__geo_interface__,
                style_function=(lambda s: (lambda _: s))(style),
                tooltip=f"{row['tension_v']:.0f} V",
            ).add_to(lines_layer)
        lines_layer.add_to(fmap)

    if len(transformers_gdf) > 0:
        transformers_layer = folium.FeatureGroup(name="Centros / subestaciones transformadoras", show=True)
        for _, row in _to_geographic(transformers_gdf).iterrows():
            popup = row.get("nombre", "Estación transformadora")
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=6,
                color="#6a3d9a",
                fill=True,
                fill_color="#6a3d9a",
                fill_opacity=0.9,
                popup=str(popup),
            ).add_to(transformers_layer)
        transformers_layer.add_to(fmap)

    top_layer = folium.FeatureGroup(name="TOP 10 ubicaciones", show=True)
    for _, row in top10_df.iterrows():
        popup_html = (
            f"<b>Rank {int(row['rank'])}</b> — Cell ID {int(row['grid_cell_id'])}<br>"
            f"Lat/Lon: {row['latitude']:.5f}, {row['longitude']:.5f}<br>"
            f"Fitness: {row['fitness']:.4f}<br>"
        )
        if pd.notna(row["solar_score"]):
            popup_html += f"Radiación anual estimada: {row['solar_annual_kwh_m2']:.1f} kWh/m²/año<br>Solar score: {row['solar_score']:.3f}<br>"
        if pd.notna(row["grid_proximity_score"]):
            popup_html += f"Línea: {row['distance_to_power_line_km']:.2f} km (score {row['grid_proximity_score']:.3f})<br>"
        if pd.notna(row["transformer_proximity_score"]):
            popup_html += f"Transformador: {row['distance_to_transformer_km']:.2f} km (score {row['transformer_proximity_score']:.3f})"
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=folium.Popup(popup_html, max_width=320),
            icon=folium.Icon(color="green", icon="bolt", prefix="fa"),
            tooltip=f"#{int(row['rank'])}",
        ).add_to(top_layer)
    top_layer.add_to(fmap)

    folium.LayerControl(collapsed=False).add_to(fmap)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fmap.save(str(output_path))
    return output_path
