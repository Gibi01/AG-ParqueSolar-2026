"""Client for datos.gob.ar (CKAN DataStore API + direct file downloads).

Two access patterns are used by this project, matching what schema
inspection (Fase 3) revealed about the actual resources:

- DataStore-backed resources (BAHRA localities, power lines) are queried
  through the CKAN `datastore_search` action, paginated.
- The transformer-station resource is a plain CSV file hosted by the
  Secretaría de Energía (not DataStore-backed: `datastore_active` is
  False for it), so it is fetched as a direct file download instead.

Every fetch returns a `FetchResult` carrying source traceability
(url/resource id, parameters, download timestamp) alongside the data,
per the project's traceability requirements.
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
    """Raised when the datos.gob.ar API returns an error or unexpected shape."""


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
    """Thin, testable wrapper around the datos.gob.ar CKAN API."""

    def __init__(self, session: Optional[requests.Session] = None, timeout_s: int = DEFAULT_TIMEOUT_S):
        self._session = session or requests.Session()
        self._timeout_s = timeout_s

    def inspect_schema(self, resource_id: str) -> list[dict[str, str]]:
        """Return the DataStore field list for a resource (id + type).

        Use this BEFORE assuming a resource's shape (e.g. whether geometries
        are points or polygons) — see Fase 3 of the project requirements.
        """
        result = self._datastore_search(resource_id, limit=1)
        return result.fields

    def fetch_all_records(
        self,
        resource_id: str,
        filters: Optional[dict[str, Any]] = None,
        page_size: int = DEFAULT_PAGE_SIZE,
    ) -> FetchResult:
        """Fetch every record of a DataStore resource, paginating as needed."""
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
        """Download a plain file resource (not DataStore-backed), e.g. the
        transformer-stations CSV published directly by Secretaría de Energía.
        """
        response = self._session.get(url, timeout=self._timeout_s)
        response.raise_for_status()
        return response.content, datetime.now(timezone.utc)
