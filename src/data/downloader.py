"""Descarga genérica de archivos, con soporte de caché.

Se usa tanto para descargas puntuales del límite administrativo (zip del
shapefile del IGN) como para cualquier otro archivo crudo "descargar una
vez, reusar para siempre". Esto NO es la caché de puntos de ERA5-Land
(ver src/data/cache.py) — esa se indexa por (variable, año, mes, lat, lon)
en vez de por una URL.
"""

from __future__ import annotations

import logging
import zipfile
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_S = 60


def download_file(
    url: str,
    dest_path: Path,
    session: Optional[requests.Session] = None,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    force: bool = False,
) -> Path:
    """Descarga `url` a `dest_path`, omitiendo la solicitud si el archivo
    ya existe en disco (salvo que force=True)."""
    dest_path = Path(dest_path)
    if dest_path.exists() and not force:
        logger.info("Using cached file, skipping download: %s", dest_path)
        return dest_path

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    session = session or requests.Session()
    response = session.get(url, timeout=timeout_s)
    response.raise_for_status()
    dest_path.write_bytes(response.content)
    logger.info("Downloaded %s -> %s (%d bytes)", url, dest_path, len(response.content))
    return dest_path


def download_and_extract_zip(
    url: str,
    zip_dest_path: Path,
    extract_dir: Path,
    session: Optional[requests.Session] = None,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    force: bool = False,
) -> Path:
    """Descarga un archivo zip (cacheado) y lo extrae (de forma idempotente)."""
    zip_path = download_file(url, zip_dest_path, session=session, timeout_s=timeout_s, force=force)
    extract_dir = Path(extract_dir)
    if not extract_dir.exists() or force:
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)
        logger.info("Extracted %s -> %s", zip_path, extract_dir)
    return extract_dir
