"""Generic, cache-aware file downloading.

Used both for one-off administrative-boundary downloads (IGN shapefile
zip) and for any other "download once, reuse forever" raw file. This is
NOT the ERA5-Land point cache (see src/data/cache.py) — that one keys on
(variable, year, month, lat, lon) rather than a URL.
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
    """Download `url` to `dest_path`, skipping the request if the file
    already exists on disk (unless force=True)."""
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
    """Download a zip file (cached) and extract it (idempotently)."""
    zip_path = download_file(url, zip_dest_path, session=session, timeout_s=timeout_s, force=force)
    extract_dir = Path(extract_dir)
    if not extract_dir.exists() or force:
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)
        logger.info("Extracted %s -> %s", zip_path, extract_dir)
    return extract_dir
