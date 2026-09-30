"""Prepare a versioned 500 m grid, edge graph and shared native climate pixels."""
import logging

import geopandas as gpd
import numpy as np
import pandas as pd

from src.climate.arco import ArcoSolarService, ARCO_SSRD_URL
from src.climate.records import CellPoint
from src.climate.climatology import annual_solar_kwh_m2
from src.database.spatial import config_signature
from src.gis.grid import build_grid, build_neighbors
from src.gis.spatial_operations import buffer_points_km, urban_exclusion_mask

logger = logging.getLogger(__name__)
STATION_IDS = frozenset({'ST', 'CN', 'RO', 'RM'})


def reference_stations(frame):
    """Freeze the existing four source identities, never use capacity attributes."""
    if 'id' not in frame:
        raise ValueError('Las ET requieren el identificador original de la fuente.')
    selected = frame.loc[frame['id'].astype(str).isin(STATION_IDS), ['id', 'nombre', 'geometry']].copy()
    if len(selected) != 4 or set(selected['id'].astype(str)) != STATION_IDS:
        raise ValueError('Falta alguna de las cuatro ET de referencia o hay IDs duplicados.')
    return selected.rename(columns={'id': 'station_id'}).sort_values('station_id').reset_index(drop=True)


def run_preprocessing(settings, repo, region_gdf, urban_gdf, power_lines_gdf, transformers_gdf, era5_service=None):
    grid = build_grid(region_gdf, settings.grid.resolution_km)
    cells = grid.gdf
    urban = urban_gdf.loc[urban_gdf.tipo.isin(settings.urban_exclusion.include_types)]
    buffers = buffer_points_km(urban, settings.urban_exclusion.buffer_km, grid.projected_crs)
    excluded = urban_exclusion_mask(cells, buffers).to_numpy()
    cells['valid'] = ~excluded
    cells['invalid_reason'] = np.where(excluded, 'intersects_urban_area', None)
    cells['climate_pixel_id'] = None
    cells['solar_annual_kwh_m2'] = np.nan
    for month in settings.climate.months:
        cells[f'climate_valid_years_{month}'] = 0
    climate = pd.DataFrame()
    if settings.fitness.use_solar:
        service = era5_service or ArcoSolarService(settings)
        points = [CellPoint(int(r.cell_id), float(r.latitude), float(r.longitude))
                  for r in cells.loc[cells.valid].itertuples()]
        if not points:
            raise ValueError('No hay celdas fuera de las exclusiones urbanas.')
        data = service.get_monthly_radiation(points)
        climate = data.records
        mapping = data.cell_pixels.set_index('grid_cell_id').climate_pixel_id
        cells['climate_pixel_id'] = cells.cell_id.map(mapping)
        annual = annual_solar_kwh_m2(climate, settings.climate.months)
        cells['solar_annual_kwh_m2'] = cells.climate_pixel_id.map(annual)
        valid_records = climate.loc[climate.complete.astype(bool)]
        counts = valid_records.groupby(['climate_pixel_id', 'month']).year.nunique().unstack('month')
        for month in settings.climate.months:
            values = counts[month] if month in counts else pd.Series(dtype=float)
            cells[f'climate_valid_years_{month}'] = cells.climate_pixel_id.map(values).fillna(0).astype(int)
        missing = cells.solar_annual_kwh_m2.isna() & cells.valid
        cells.loc[missing, 'invalid_reason'] = 'missing_climate_data'
        cells.loc[missing, 'valid'] = False
    if not cells.valid.any():
        raise ValueError('No hay celdas válidas después de aplicar exclusiones y cobertura climática.')
    empty = gpd.GeoDataFrame(geometry=[], crs=4326)
    lines = power_lines_gdf[['tension_v', 'geometry']].to_crs(4326) if settings.fitness.use_power_lines else empty.assign(tension_v=pd.Series(dtype=float))
    if settings.fitness.use_power_lines and lines.empty:
        raise ValueError('Falta la capa de líneas eléctricas.')
    stations = reference_stations(transformers_gdf).to_crs(4326) if settings.fitness.use_transformers else empty.assign(station_id=pd.Series(dtype=str), nombre=pd.Series(dtype=str))
    neighbors = build_neighbors(cells.loc[cells.valid])
    layers = dict(region=region_gdf[['geometry']].to_crs(4326),
                  urban=urban[['geometry']].to_crs(4326), lines=lines, transformers=stations)
    metadata = dict(config_signature=config_signature(settings), projected_crs=str(grid.projected_crs),
                    grid_origin=list(region_gdf.to_crs(grid.projected_crs).total_bounds[:2]),
                    resolution_km=settings.grid.resolution_km, climate_url=ARCO_SSRD_URL,
                    climate_periods=settings.climate.year_months, coverage='100% unique finite hourly values',
                    station_ids=stations.station_id.tolist(), processing_version=2)
    dataset_id = repo.save_dataset(cells, neighbors, climate, layers, metadata)
    cells.attrs['dataset_id'] = dataset_id
    logger.info('Dataset %s: %d/%d celdas válidas, %d registros mensuales por píxel',
                dataset_id[:12], int(cells.valid.sum()), len(cells), len(climate))
    return cells
