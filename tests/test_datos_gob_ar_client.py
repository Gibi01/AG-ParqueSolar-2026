"""Tests para el cliente de datos.gob.ar — la sesión HTTP se mockea, así
que ningún test de este módulo toca la red."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.api.datos_gob_ar import DatosGobArClient, DatosGobArError


def _mock_response(payload: dict):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = payload
    return resp


def _success_payload(records, total, fields=None):
    return {
        "success": True,
        "result": {"records": records, "total": total, "fields": fields or []},
    }


def test_inspect_schema_returns_fields():
    session = MagicMock()
    session.get.return_value = _mock_response(
        _success_payload([{"a": 1}], total=1, fields=[{"id": "a", "type": "int"}])
    )
    client = DatosGobArClient(session=session)
    fields = client.inspect_schema("some-resource-id")
    assert fields == [{"id": "a", "type": "int"}]


def test_fetch_all_records_paginates_until_total_reached():
    session = MagicMock()
    page1 = _mock_response(_success_payload([{"_id": 1}, {"_id": 2}], total=3))
    page2 = _mock_response(_success_payload([{"_id": 3}], total=3))
    session.get.side_effect = [page1, page2]

    client = DatosGobArClient(session=session)
    result = client.fetch_all_records("resource-id", page_size=2)

    assert result.total == 3
    assert [r["_id"] for r in result.records] == [1, 2, 3]
    assert session.get.call_count == 2


def test_fetch_all_records_raises_on_api_failure():
    session = MagicMock()
    session.get.return_value = _mock_response({"success": False, "error": "boom"})
    client = DatosGobArClient(session=session)
    with pytest.raises(DatosGobArError):
        client.fetch_all_records("resource-id")


def test_fetch_file_returns_bytes():
    session = MagicMock()
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.content = b"col1,col2\n1,2\n"
    session.get.return_value = resp

    client = DatosGobArClient(session=session)
    content, downloaded_at = client.fetch_file("http://example.com/data.csv")
    assert content == b"col1,col2\n1,2\n"
    assert downloaded_at is not None
