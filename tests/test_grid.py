import numpy as np

from src.gis.grid import build_grid


def test_build_grid_cells_are_within_region(region_boundary_gdf):
    grid = build_grid(region_boundary_gdf, resolution_km=5)
    assert len(grid.gdf) > 0
    region_geom_proj = region_boundary_gdf.to_crs(grid.projected_crs).geometry.union_all()
    # every cell must be (at least almost) contained in the region, since
    # cells are clipped by intersection with the boundary
    outside_area = grid.gdf.geometry.difference(region_geom_proj).area.sum()
    assert outside_area < 1.0  # negligible floating point slop, in m^2


def test_build_grid_assigns_unique_sequential_ids(region_boundary_gdf):
    grid = build_grid(region_boundary_gdf, resolution_km=5)
    ids = grid.gdf["cell_id"].to_numpy()
    assert len(np.unique(ids)) == len(ids)
    assert ids.min() == 1


def test_build_grid_finer_resolution_yields_more_cells(region_boundary_gdf):
    coarse = build_grid(region_boundary_gdf, resolution_km=10)
    fine = build_grid(region_boundary_gdf, resolution_km=5)
    assert len(fine.gdf) > len(coarse.gdf)


def test_build_grid_projected_crs_is_metric(region_boundary_gdf):
    grid = build_grid(region_boundary_gdf, resolution_km=5)
    assert grid.projected_crs.is_projected
    assert not grid.projected_crs.is_geographic


def test_build_grid_centroids_have_plausible_lat_lon(region_boundary_gdf):
    grid = build_grid(region_boundary_gdf, resolution_km=5)
    assert grid.gdf["latitude"].between(-90, 90).all()
    assert grid.gdf["longitude"].between(-180, 180).all()
    # centroids should fall inside (or very near) the original geographic bounds
    assert grid.gdf["latitude"].min() >= -32.3
    assert grid.gdf["latitude"].max() <= -31.6
