"""Ingestion: APIs -> raw GeoDataFrames, cached to disk.

Every function here is region-agnostic: it reads `settings.region` to
decide *what* to fetch and *how to clip it*, never a hardcoded province
name. Changing `region` in config.yaml (name + admin_source) is enough
to point the whole ingestion step at a different province, as long as
the same national datasets (BAHRA, power lines, transformer stations)
cover it — see README "Cambiar de provincia" for the parts that are
NOT yet generalized (e.g. transformer stations is an Argentina-wide
Secretaría de Energía source, which is fine; a different country would
need a different `infrastructure.transformers.source_url`).

National point/line datasets (BAHRA localities, power lines, transformer
stations) are fetched in full and then spatially clipped to the region
boundary, rather than filtered by a province-name text field. This
avoids brittle text matching (accents, casing) against source-specific
province-name spellings and generalizes cleanly to any province.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import geopandas as gpd
import pandas as pd
import requests
import shapely
from shapely.geometry import shape

from src.api.datos_gob_ar import DatosGobArClient
from src.config.settings import Settings
from src.data.cache import RawLayerCache
from src.data.downloader import download_and_extract_zip
from src.data.validators import (
    validate_crs_is_set,
    validate_geometries_valid,
    validate_no_empty_geometries,
    validate_not_empty,
)
from src.gis.crs import GEOGRAPHIC_CRS

logger = logging.getLogger(__name__)


@dataclass
class LayerBundle:
    gdf: gpd.GeoDataFrame
    metadata: dict[str, Any]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ingest_region_boundary(
    settings: Settings,
    cache: Optional[RawLayerCache] = None,
    session: Optional[requests.Session] = None,
    force: bool = False,
) -> LayerBundle:
    """Fetch the official IGN provincial boundary and isolate the configured region.

    Source: Instituto Geográfico Nacional (IGN) "Unidades Territoriales"
    dataset, provincia layer (WGS84 / EPSG:4326 per its .prj file).
    """
    cache = cache or RawLayerCache(settings.paths.data_raw / "layers")
    name = "region_boundary"
    if cache.exists(name) and not force:
        gdf, metadata = cache.load(name)
        return LayerBundle(gdf, metadata)

    admin = settings.region.admin_source
    zip_path = settings.paths.data_raw / "downloads" / "ign_provincia.zip"
    extract_dir = settings.paths.data_raw / "downloads" / "ign_provincia"
    extract_dir = download_and_extract_zip(
        admin.shapefile_zip_url, zip_path, extract_dir, session=session, force=force
    )

    shp_path = extract_dir / admin.shapefile_member
    all_provinces = gpd.read_file(shp_path)
    if all_provinces.crs is None:
        all_provinces = all_provinces.set_crs(admin.native_crs)

    match = all_provinces[all_provinces[admin.code_field].astype(str) == str(admin.code_value)]
    if len(match) == 0:
        match = all_provinces[
            all_provinces[admin.name_field].str.strip().str.upper() == settings.region.name.strip().upper()
        ]
    if len(match) != 1:
        raise ValueError(
            f"Expected exactly one boundary feature for region "
            f"'{settings.region.name}' (code {admin.code_value}) in {shp_path}, "
            f"found {len(match)}."
        )

    boundary = match[[admin.name_field, admin.code_field, "geometry"]].rename(
        columns={admin.name_field: "region_name", admin.code_field: "region_code"}
    )
    boundary = boundary.reset_index(drop=True)
    # The IGN source ships 3D (Z=0) geometries; flatten to 2D since every
    # downstream spatial operation here is purely planar.
    boundary["geometry"] = shapely.force_2d(boundary["geometry"])
    validate_crs_is_set(boundary, "region_boundary")
    validate_geometries_valid(boundary, "region_boundary")
    validate_no_empty_geometries(boundary, "region_boundary")

    metadata = {
        "source": "IGN - Instituto Geográfico Nacional (Unidades Territoriales, capa Provincia)",
        "url": admin.shapefile_zip_url,
        "downloaded_at": _now(),
        "native_crs": str(boundary.crs),
        "region_name": settings.region.name,
        "region_code": admin.code_value,
    }
    cache.save(name, boundary, metadata)
    return LayerBundle(boundary, metadata)


def _bahra_records_to_geodataframe(records: list[dict[str, Any]]) -> gpd.GeoDataFrame:
    geometries = []
    rows = []
    for rec in records:
        geojson_raw = rec.get("geojson")
        if not geojson_raw:
            continue
        geometries.append(shape(json.loads(geojson_raw)))
        rows.append(
            {
                "bahra_id": rec.get("_id"),
                "nom_prov": rec.get("nom_prov"),
                "nom_depto": rec.get("nom_depto"),
                "nombre": rec.get("nombre"),
                "tipo": rec.get("tipo"),
                "fuente": rec.get("fuente"),
            }
        )
    return gpd.GeoDataFrame(rows, geometry=geometries, crs=GEOGRAPHIC_CRS)


def ingest_urban_areas(
    settings: Settings,
    region_boundary: gpd.GeoDataFrame,
    cache: Optional[RawLayerCache] = None,
    client: Optional[DatosGobArClient] = None,
    force: bool = False,
) -> LayerBundle:
    """Fetch BAHRA localities (points) and clip them to the region boundary.

    Confirmed by schema inspection: this resource is POINT geometry
    (`geojson` field with type "Point"), never polygons — see README for
    why urban areas are therefore approximated via a buffer.
    """
    cache = cache or RawLayerCache(settings.paths.data_raw / "layers")
    name = "urban_areas_points"
    if cache.exists(name) and not force:
        gdf, metadata = cache.load(name)
        return LayerBundle(gdf, metadata)

    client = client or DatosGobArClient()
    resource_id = settings.infrastructure.urban_areas.resource_id
    result = client.fetch_all_records(resource_id)
    gdf = _bahra_records_to_geodataframe(result.records)

    region_geom = region_boundary.union_all()
    clipped = gdf[gdf.intersects(region_geom)].reset_index(drop=True)
    validate_not_empty(clipped, "urban_areas (clipped to region)")

    metadata = {
        "source": "BAHRA - Base de Asentamientos Humanos de la República Argentina (datos.gob.ar DataStore)",
        "resource_id": resource_id,
        "url": result.source_url,
        "downloaded_at": _now(),
        "geometry_type_confirmed": "Point",
        "national_total_records": result.total,
        "clipped_to_region_count": len(clipped),
        "native_crs": GEOGRAPHIC_CRS,
    }
    cache.save(name, clipped, metadata)
    return LayerBundle(clipped, metadata)


def _linestring_records_to_geodataframe(records: list[dict[str, Any]]) -> gpd.GeoDataFrame:
    geometries = []
    rows = []
    for rec in records:
        geojson_raw = rec.get("geojson")
        if not geojson_raw:
            continue
        geometries.append(shape(json.loads(geojson_raw)))
        rows.append({"line_id": rec.get("_id"), "tension_v": rec.get("tension")})
    return gpd.GeoDataFrame(rows, geometry=geometries, crs=GEOGRAPHIC_CRS)


def ingest_power_lines(
    settings: Settings,
    region_boundary: gpd.GeoDataFrame,
    cache: Optional[RawLayerCache] = None,
    client: Optional[DatosGobArClient] = None,
    force: bool = False,
) -> LayerBundle:
    """Fetch power-line geometries and clip them to the region boundary.

    Confirmed by schema inspection: MultiLineString geometry with a
    `tension` (voltage) attribute only — no substation/transformer
    entities in this resource (see ingest_transformers for that layer).

    IMPORTANT scope note (found empirically, not documented on the
    dataset page): despite its generic "Consejo Federal" name, this
    resource's ~46k records are ALL located within Santa Fe's bounding
    box already — it does not actually cover the rest of the country.
    It is a good fit for this MVP's region, but switching `region` to
    another province will very likely yield zero clipped power-line
    features from this same resource_id, and a different source will
    need to be configured. This is exactly the kind of source-specific
    limitation the region-agnostic design tries to make visible rather
    than silently hide (an empty clipped result still fails loudly via
    validate_not_empty below).
    """
    cache = cache or RawLayerCache(settings.paths.data_raw / "layers")
    name = "power_lines"
    if cache.exists(name) and not force:
        gdf, metadata = cache.load(name)
        return LayerBundle(gdf, metadata)

    client = client or DatosGobArClient()
    resource_id = settings.infrastructure.power_lines.resource_id
    result = client.fetch_all_records(resource_id)
    gdf = _linestring_records_to_geodataframe(result.records)

    region_geom = region_boundary.union_all()
    clipped = gdf[gdf.intersects(region_geom)].reset_index(drop=True)
    validate_not_empty(clipped, "power_lines (clipped to region)")

    metadata = {
        "source": "Redes de distribución eléctrica del Consejo Federal (datos.gob.ar DataStore)",
        "resource_id": resource_id,
        "url": result.source_url,
        "downloaded_at": _now(),
        "geometry_type_confirmed": "MultiLineString",
        "national_total_records": result.total,
        "clipped_to_region_count": len(clipped),
        "native_crs": GEOGRAPHIC_CRS,
        "note": "No transformer/substation entities present in this resource.",
    }
    cache.save(name, clipped, metadata)
    return LayerBundle(clipped, metadata)


def _transformers_csv_to_geodataframe(csv_bytes: bytes) -> gpd.GeoDataFrame:
    import io

    text = csv_bytes.decode("utf-8-sig")
    df = pd.read_csv(io.StringIO(text))
    geometries = []
    for raw in df["geojson"]:
        geom = shape(json.loads(raw))
        # Source uses MultiPoint with a single member per station; normalize to Point.
        if geom.geom_type == "MultiPoint":
            geom = geom.geoms[0]
        geometries.append(geom)
    keep_cols = [
        "nombre",
        "id",
        "propiedad",
        "concesion",
        "potencia_instalada_mv",
        "fecha_puesta_servicio",
        "tension_entrada",
        "tension_salida",
    ]
    rows = df[[c for c in keep_cols if c in df.columns]].to_dict("records")
    return gpd.GeoDataFrame(rows, geometry=geometries, crs=GEOGRAPHIC_CRS)


def ingest_transformers(
    settings: Settings,
    region_boundary: gpd.GeoDataFrame,
    cache: Optional[RawLayerCache] = None,
    client: Optional[DatosGobArClient] = None,
    force: bool = False,
) -> LayerBundle:
    """Fetch transformer/substation stations and clip them to the region.

    This is a mandatory, independent layer (see README/requirements
    Fase 16): the power-lines resource above has no substation data, so
    this uses a separate official source — Secretaría de Energía's
    "Transporte Eléctrico AT - Estaciones Transformadoras" dataset.
    If this source ever disappears, the pipeline must fail loudly rather
    than silently proceed without the transformer-proximity criterion.
    """
    cache = cache or RawLayerCache(settings.paths.data_raw / "layers")
    name = "transformers"
    if cache.exists(name) and not force:
        gdf, metadata = cache.load(name)
        return LayerBundle(gdf, metadata)

    client = client or DatosGobArClient()
    url = settings.infrastructure.transformers.source_url
    csv_bytes, downloaded_at = client.fetch_file(url)
    gdf = _transformers_csv_to_geodataframe(csv_bytes)

    region_geom = region_boundary.union_all()
    clipped = gdf[gdf.intersects(region_geom)].reset_index(drop=True)
    validate_not_empty(clipped, "transformers (clipped to region)")

    metadata = {
        "source": "Secretaría de Energía - Transporte Eléctrico AT Estaciones Transformadoras (datos.gob.ar)",
        "url": url,
        "downloaded_at": downloaded_at.isoformat(),
        "geometry_type_confirmed": "Point (normalized from MultiPoint)",
        "national_total_records": len(gdf),
        "clipped_to_region_count": len(clipped),
        "native_crs": settings.infrastructure.transformers.native_crs,
    }
    cache.save(name, clipped, metadata)
    return LayerBundle(clipped, metadata)
