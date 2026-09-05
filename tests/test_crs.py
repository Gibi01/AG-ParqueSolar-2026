import pytest

from src.gis.crs import estimate_projected_crs, to_geographic, to_projected


def test_estimate_projected_crs_returns_metric_crs(region_boundary_gdf):
    crs = estimate_projected_crs(region_boundary_gdf)
    assert crs.is_projected
    assert not crs.is_geographic


def test_estimate_projected_crs_requires_crs_set(region_boundary_gdf):
    unset = region_boundary_gdf.copy()
    unset = unset.set_crs(None, allow_override=True)
    with pytest.raises(ValueError):
        estimate_projected_crs(unset)


def test_to_projected_then_to_geographic_roundtrip(region_boundary_gdf):
    crs = estimate_projected_crs(region_boundary_gdf)
    projected = to_projected(region_boundary_gdf, crs)
    assert projected.crs.is_projected

    back = to_geographic(projected)
    assert str(back.crs).endswith("4326")
    # el roundtrip debe preservar área/forma de cerca (se permite un pequeño error de reproyección)
    orig_bounds = region_boundary_gdf.total_bounds
    back_bounds = back.total_bounds
    assert orig_bounds == pytest.approx(back_bounds, abs=1e-6)
