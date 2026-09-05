"""Ingesta: APIs -> GeoDataFrames crudos, cacheados en disco.

Cada función acá es agnóstica de la región: lee `settings.region` para
decidir *qué* obtener y *cómo recortarlo*, nunca un nombre de provincia
hardcodeado. Cambiar `region` en config.yaml (name + admin_source) alcanza
para apuntar todo el paso de ingesta a otra provincia, siempre que los
mismos datasets nacionales (BAHRA, líneas eléctricas, estaciones
transformadoras) la cubran — ver README "Cambiar de provincia" para las
partes que TODAVÍA no están generalizadas (p. ej. estaciones
transformadoras es una fuente de la Secretaría de Energía a nivel país,
lo cual está bien; un país distinto necesitaría un
`infrastructure.transformers.source_url` diferente).

Los datasets nacionales de puntos/líneas (localidades BAHRA, líneas
eléctricas, estaciones transformadoras) se obtienen completos y luego se
recortan espacialmente al límite de la región, en vez de filtrarse por un
campo de texto con el nombre de provincia. Esto evita el matching de
texto frágil (acentos, mayúsculas) contra las variantes de escritura del
nombre de provincia específicas de cada fuente, y generaliza limpiamente
a cualquier provincia.
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
    """Obtiene el límite provincial oficial del IGN y aísla la región configurada.

    Fuente: dataset "Unidades Territoriales" del Instituto Geográfico
    Nacional (IGN), capa provincia (WGS84 / EPSG:4326 según su archivo .prj).
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
    # La fuente del IGN trae geometrías 3D (Z=0); se aplanan a 2D ya que
    # toda operación espacial posterior acá es puramente planar.
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
    """Obtiene las localidades BAHRA (puntos) y las recorta al límite de la región.

    Confirmado al inspeccionar el schema: este recurso es geometría de
    PUNTO (campo `geojson` con tipo "Point"), nunca polígonos — ver README
    para saber por qué las zonas urbanas se aproximan entonces con un buffer.
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
    """Obtiene las geometrías de líneas eléctricas y las recorta al límite de la región.

    Confirmado al inspeccionar el schema: geometría MultiLineString con un
    único atributo `tension` (voltaje) — sin entidades de
    subestación/transformador en este recurso (ver ingest_transformers
    para esa capa).

    NOTA DE ALCANCE IMPORTANTE (hallada empíricamente, no documentada en
    la página del dataset): pese a su nombre genérico "Consejo Federal",
    los ~46 mil registros de este recurso ya están TODOS ubicados dentro
    del bounding box de Santa Fe — en realidad no cubre el resto del país.
    Es una buena fuente para la región de este MVP, pero cambiar `region`
    a otra provincia muy probablemente devuelva cero features de línea
    eléctrica recortadas para este mismo resource_id, y habrá que
    configurar una fuente distinta. Esto es exactamente el tipo de
    limitación específica de la fuente que el diseño agnóstico de región
    intenta hacer visible en vez de esconder en silencio (un resultado
    recortado vacío igual falla explícitamente vía validate_not_empty más abajo).
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
        # La fuente usa MultiPoint con un único miembro por estación; se normaliza a Point.
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
    """Obtiene las estaciones transformadoras/subestaciones y las recorta al límite de la región.

    Esta es una capa obligatoria e independiente (ver README/requisitos
    Fase 16): el recurso de líneas eléctricas de arriba no tiene datos de
    subestaciones, así que esto usa una fuente oficial separada — el
    dataset "Transporte Eléctrico AT - Estaciones Transformadoras" de la
    Secretaría de Energía. Si esta fuente alguna vez desaparece, el
    pipeline debe fallar explícitamente en vez de seguir en silencio sin
    el criterio de proximidad a transformadores.
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
