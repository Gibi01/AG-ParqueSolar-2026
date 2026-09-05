import geopandas as gpd
import pytest
from shapely.geometry import LineString, Point

from src.gis.distance import nearest_distance_km


def test_nearest_distance_km_matches_known_offset():
    # Dos puntos separados ~0.01 grados de latitud en el ecuador dan ~1.1km,
    # pero usamos un CRS proyectado con offsets EXACTOS en metros para que
    # la expectativa sea inequívoca, en vez de depender de aproximaciones geodésicas.
    projected_crs = "EPSG:5346"  # POSGAR 2007 / Argentina Faja 4 (métrico)
    source = gpd.GeoDataFrame({"id": [1]}, geometry=[Point(0, 0)], crs=projected_crs)
    target = gpd.GeoDataFrame({"id": [1]}, geometry=[Point(0, 3000)], crs=projected_crs)  # 3000 m al norte

    distances = nearest_distance_km(source, target, projected_crs)
    assert distances[0] == pytest.approx(3.0, abs=1e-6)


def test_nearest_distance_km_picks_the_closer_of_several_targets():
    projected_crs = "EPSG:5346"
    source = gpd.GeoDataFrame({"id": [1]}, geometry=[Point(0, 0)], crs=projected_crs)
    target = gpd.GeoDataFrame(
        {"id": [1, 2, 3]},
        geometry=[Point(0, 5000), Point(0, 500), Point(0, 10000)],
        crs=projected_crs,
    )
    distances = nearest_distance_km(source, target, projected_crs)
    assert distances[0] == pytest.approx(0.5, abs=1e-6)


def test_nearest_distance_km_to_line_uses_perpendicular_distance():
    projected_crs = "EPSG:5346"
    source = gpd.GeoDataFrame({"id": [1]}, geometry=[Point(0, 0)], crs=projected_crs)
    # Una línea vertical a 1000m al este; la distancia perpendicular es exactamente 1000m
    target = gpd.GeoDataFrame(
        {"id": [1]}, geometry=[LineString([(1000, -5000), (1000, 5000)])], crs=projected_crs
    )
    distances = nearest_distance_km(source, target, projected_crs)
    assert distances[0] == pytest.approx(1.0, abs=1e-6)


def test_nearest_distance_km_raises_on_empty_target():
    projected_crs = "EPSG:5346"
    source = gpd.GeoDataFrame({"id": [1]}, geometry=[Point(0, 0)], crs=projected_crs)
    target = gpd.GeoDataFrame({"id": []}, geometry=[], crs=projected_crs)
    with pytest.raises(ValueError):
        nearest_distance_km(source, target, projected_crs)
