import pytest

from src.climate.era5_land import predict_nearest_era5_grid_point


@pytest.mark.parametrize(
    "lat,lon,expected",
    [
        (-31.73, -60.71, (-31.7, -60.7)),
        (-31.75, -60.75, (-31.8, -60.8)),  # caso límite de redondeo (round-half-to-even)
        (-31.0, -60.0, (-31.0, -60.0)),
        (-31.849, -60.849, (-31.8, -60.8)),
    ],
)
def test_predict_nearest_era5_grid_point_rounds_to_0_1_degree(lat, lon, expected):
    result = predict_nearest_era5_grid_point(lat, lon)
    assert result[0] == pytest.approx(expected[0], abs=1e-9)
    assert result[1] == pytest.approx(expected[1], abs=1e-9)


def test_predict_nearest_era5_grid_point_groups_nearby_cells_together():
    # Dos centroides de celda lo bastante cerca como para plausiblemente
    # compartir el mismo punto de ERA5-Land de ~9km deberían predecir el MISMO punto.
    a = predict_nearest_era5_grid_point(-31.731, -60.712)
    b = predict_nearest_era5_grid_point(-31.734, -60.708)
    assert a == b
