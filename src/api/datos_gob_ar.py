"""Cliente para datos.gob.ar (API CKAN DataStore + descargas directas de archivos).

Este proyecto usa dos patrones de acceso, según lo que reveló la
inspección de schemas (Fase 3) sobre los recursos reales:

- Los recursos respaldados por DataStore (localidades BAHRA, líneas
  eléctricas) se consultan mediante la acción CKAN `datastore_search`, paginada.
- El recurso de estaciones transformadoras es un archivo CSV plano alojado
  por la Secretaría de Energía (no respaldado por DataStore:
  `datastore_active` es False para él), así que se obtiene como una
  descarga directa de archivo en su lugar.

Cada fetch devuelve un `FetchResult` que lleva trazabilidad de la fuente
(url/id de recurso, parámetros, timestamp de descarga) junto con los
datos, según los requisitos de trazabilidad del proyecto.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

import requests

DATASTORE_SEARCH_URL = "https://datos.gob.ar/api/3/action/datastore_search"
DEFAULT_TIMEOUT_S = 30
DEFAULT_PAGE_SIZE = 1000


class DatosGobArError(RuntimeError):
    """Se lanza cuando la API de datos.gob.ar devuelve un error o una forma inesperada."""


@dataclass
class FetchResult:
    records: list[dict[str, Any]]
    fields: list[dict[str, str]]
    total: int
    source_url: str
    resource_id: Optional[str]
    params: dict[str, Any]
    downloaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DatosGobArClient:
    """Envoltorio delgado y testeable sobre la API CKAN de datos.gob.ar."""

    def __init__(self, session: Optional[requests.Session] = None, timeout_s: int = DEFAULT_TIMEOUT_S):
        self._session = session or requests.Session()
        self._timeout_s = timeout_s

    def inspect_schema(self, resource_id: str) -> list[dict[str, str]]:
        """Devuelve la lista de campos del DataStore para un recurso (id + tipo).

        Usar esto ANTES de asumir la forma de un recurso (p. ej. si las
        geometrías son puntos o polígonos) — ver Fase 3 de los requisitos del proyecto.
        """
        result = self._datastore_search(resource_id, limit=1)
        return result.fields

    def fetch_all_records(
        self,
        resource_id: str,
        filters: Optional[dict[str, Any]] = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> FetchResult:
        """Obtiene todos los registros de un recurso DataStore, paginando según sea necesario."""
        offset = 0
        all_records: list[dict[str, Any]] = []
        fields: list[dict[str, str]] = []
        total = None
        downloaded_at = datetime.now(timezone.utc)

        while True:
            page = self._datastore_search(
                resource_id, limit=page_size, offset=offset, filters=filters
            )
            if total is None:
                total = page.total
                fields = page.fields
            all_records.extend(page.records)
            offset += page_size
            if len(page.records) < page_size or offset >= total:
                break

        return FetchResult(
            records=all_records,
            fields=fields,
            total=total or 0,
            source_url=DATASTORE_SEARCH_URL,
            resource_id=resource_id,
            params={"filters": filters, "page_size": page_size},
            downloaded_at=downloaded_at,
        )

    def _datastore_search(
        self,
        resource_id: str,
        limit: int,
        offset: int = 0,
        filters: Optional[dict[str, Any]] = None,
    ) -> FetchResult:
        params: dict[str, Any] = {"resource_id": resource_id, "limit": limit, "offset": offset}
        if filters:
            import json

            params["filters"] = json.dumps(filters)

        response = self._session.get(DATASTORE_SEARCH_URL, params=params, timeout=self._timeout_s)
        response.raise_for_status()
        payload = response.json()

        if not payload.get("success"):
            raise DatosGobArError(f"datastore_search failed for resource {resource_id}: {payload}")

        result = payload["result"]
        return FetchResult(
            records=result.get("records", []),
            fields=result.get("fields", []),
            total=result.get("total", 0),
            source_url=DATASTORE_SEARCH_URL,
            resource_id=resource_id,
            params=params,
        )

    def fetch_file(self, url: str) -> tuple[bytes, datetime]:
        """Descarga un recurso de archivo plano (no respaldado por DataStore),
        p. ej. el CSV de estaciones transformadoras publicado directamente
        por la Secretaría de Energía.
        """
        response = self._session.get(url, timeout=self._timeout_s)
        response.raise_for_status()
        return response.content, datetime.now(timezone.utc)
