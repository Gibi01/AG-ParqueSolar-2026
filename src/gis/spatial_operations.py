"""Operaciones espaciales sobre capas: envolventes urbanas y máscaras de exclusión.

`urban_exclusion_mask` implementa el requisito estricto de que cualquier
celda de grilla que intersecte una zona urbana quede EXCLUIDA por
completo — nunca simplemente penalizada en el fitness.
"""

from __future__ import annotations

from pyproj import CRS

import geopandas as gpd
import pandas as pd
import numpy as np
import shapely
from shapely.geometry import Polygon, MultiPolygon

from src.gis.crs import to_projected


def _metric_crs(crs):
    if crs is None:
        raise ValueError('La geometría requiere un CRS conocido.')
    value = CRS.from_user_input(crs)
    if not value.is_projected or any(axis.unit_conversion_factor != 1 for axis in value.axis_info[:2]):
        raise ValueError('El CRS de análisis debe ser proyectado y estar en metros.')
    return value


def repair_urban_envelopes(envelopes):
    """Repair polygons without silently dropping nulls, collapsed parts or points."""
    if envelopes.crs is None:
        raise ValueError('Las envolventes requieren un CRS conocido.')
    if envelopes.empty or envelopes.geometry.isna().any() or envelopes.geometry.is_empty.any():
        raise ValueError('La fuente urbana contiene geometrías vacías o nulas.')
    if not envelopes.geom_type.isin(['Polygon', 'MultiPolygon']).all():
        raise ValueError('La fuente urbana debe contener exclusivamente polígonos.')
    result = envelopes.copy()
    invalid = ~result.geometry.is_valid
    result.loc[invalid, 'geometry'] = result.loc[invalid].geometry.make_valid()
    if not result.geom_type.isin(['Polygon', 'MultiPolygon']).all() or result.geometry.is_empty.any():
        raise ValueError('La reparación urbana produjo partes no poligonales; revisar la fuente.')
    result.attrs['repaired_geometries'] = int(invalid.sum())
    return result


def build_urban_mask(envelopes_gdf, buffer_km, projected_crs, fill_holes=True):
    """Union real outlines, optionally fill enclosed holes, then add a metric margin.

    Disconnected components and concave exterior edges are preserved. Filling
    holes is an explicit conservative exclusion policy, not a source correction.
    """
    target = _metric_crs(projected_crs)
    if not np.isfinite(buffer_km) or buffer_km < 0:
        raise ValueError('El margen urbano debe ser finito y no negativo.')
    repaired = repair_urban_envelopes(envelopes_gdf)
    projected = to_projected(repaired, target)
    original = projected.geometry.union_all()
    # INDEC uses N/A for simple localities. Never merge those into one group.
    if 'codaglo' in projected:
        codes = projected.codaglo.fillna('').astype(str)
        has_agglomeration = codes.str.fullmatch(r'\d+').fillna(False) & codes.ne('0000') & codes.ne('0')
        groups = codes.where(has_agglomeration, pd.Series(
            [f'locality:{i}' for i in range(len(projected))], index=projected.index))
        unions = [group.geometry.union_all() for _, group in projected.groupby(groups)]
    else:
        unions = [original]
    parts = [part for union in unions for part in
             (list(union.geoms) if isinstance(union, MultiPolygon) else [union])]
    holes = [Polygon(ring) for part in parts for ring in part.interiors]
    filled = shapely.union_all([Polygon(part.exterior) for part in parts]) if fill_holes else original
    mask = filled.buffer(buffer_km * 1000) if buffer_km else filled
    geometries = list(mask.geoms) if isinstance(mask, MultiPolygon) else [mask]
    result = gpd.GeoDataFrame(geometry=geometries, crs=target)
    result.attrs.update(
        repaired_geometries=repaired.attrs['repaired_geometries'],
        interior_holes_count=len(holes),
        interior_holes_area_km2=sum(h.area for h in holes) / 1e6,
        largest_interior_hole_km2=max((h.area for h in holes), default=0) / 1e6,
        envelope_area_km2=original.area / 1e6,
        filled_area_km2=filled.area / 1e6,
        margin_area_km2=(mask.area - filled.area) / 1e6,
        mask_area_km2=mask.area / 1e6,
    )
    return result


def prepare_urban_mask(envelopes, region_gdf, buffer_km, projected_crs, fill_holes=True):
    """Select complete nearby agglomerations; fill/buffer before provincial crop."""
    target = _metric_crs(projected_crs)
    if not np.isfinite(buffer_km) or buffer_km < 0:
        raise ValueError('El margen urbano debe ser finito y no negativo.')
    urban = repair_urban_envelopes(envelopes).to_crs(target)
    repaired_count = urban.attrs.get('repaired_geometries', 0)
    region = to_projected(region_gdf, target).union_all()
    nearby = urban.geometry.intersects(region.buffer(buffer_km * 1000))
    if 'codaglo' in urban:
        codes = urban.loc[nearby, 'codaglo'].dropna().astype(str)
        codes = codes.loc[codes.str.fullmatch(r'\d+') & ~codes.isin(['0', '0000'])]
        nearby |= urban.codaglo.astype(str).isin(codes)
    urban = urban.loc[nearby].copy()
    if urban.empty:
        mask = gpd.GeoDataFrame(geometry=[], crs=target)
        audit = dict(mask_area_km2=0, clipped_mask_area_km2=0)
    else:
        mask = build_urban_mask(urban, buffer_km, target, fill_holes)
        audit = mask.attrs.copy()
        mask['geometry'] = mask.geometry.intersection(region)
        mask = mask.loc[~mask.geometry.is_empty].copy()
        audit['clipped_mask_area_km2'] = mask.geometry.area.sum() / 1e6
    audit['repaired_source_geometries'] = repaired_count
    audit['selected_source_features'] = len(urban)
    mask.attrs = audit
    return urban, mask


def urban_exclusion_mask(grid_gdf: gpd.GeoDataFrame, urban_polygons_proj: gpd.GeoDataFrame) -> pd.Series:
    """Devuelve una Serie booleana (alineada con el índice de grid_gdf) que
    es True para las celdas que intersectan CUALQUIER polígono urbano
    de la máscara — a excluir.

    Ambas entradas ya deben compartir el mismo CRS proyectado.
    """
    target = _metric_crs(grid_gdf.crs)
    if urban_polygons_proj.crs is None or target != CRS.from_user_input(urban_polygons_proj.crs):
        raise ValueError('La grilla y la máscara urbana deben compartir el mismo CRS métrico.')
    if len(urban_polygons_proj) == 0:
        return pd.Series(False, index=grid_gdf.index)
    urban_union = urban_polygons_proj.geometry.union_all()
    shapely.prepare(urban_union)
    return pd.Series(shapely.intersects(urban_union, grid_gdf.geometry.array), index=grid_gdf.index)
