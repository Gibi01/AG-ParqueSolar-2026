"""Tests for the CDS/ERA5-Land client. The underlying `cdsapi.Client` is
replaced with a fake object (`FakeCdsClient`) that writes a synthetic CSV
instead of calling the real Copernicus service — no test here touches
the network or requires a CDS_API_KEY."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from src.api.copernicus_era5_land import (
    CdsCredentialsError,
    CdsResponseParsingError,
    CopernicusEra5LandClient,
    Era5PointRequest,
)


class FakeCdsClient:
    def __init__(self, era5_lat: float, era5_lon: float, hourly_value_j_m2: float = 1_000_000.0):
        self.era5_lat = era5_lat
        self.era5_lon = era5_lon
        self.hourly_value_j_m2 = hourly_value_j_m2
        self.last_request = None
        self.last_dataset = None

    def retrieve(self, dataset: str, request: dict, target: str) -> None:
        self.last_dataset = dataset
        self.last_request = request
        times = pd.date_range("2024-01-01", periods=24, freq="h")
        df = pd.DataFrame(
            {
                "valid_time": times,
                "latitude": self.era5_lat,
                "longitude": self.era5_lon,
                "surface_solar_radiation_downwards": self.hourly_value_j_m2,
            }
        )
        df.to_csv(target, index=False)


def _make_request(lat=-31.73, lon=-60.71) -> Era5PointRequest:
    return Era5PointRequest(
        variable="surface_solar_radiation_downwards",
        latitude=lat,
        longitude=lon,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
        bbox_epsilon_deg=0.001,
    )


def test_area_bbox_is_tiny_box_centered_on_point():
    req = _make_request(lat=-31.73, lon=-60.71)
    north, west, south, east = req.area_bbox()
    assert north == pytest.approx(-31.729)
    assert south == pytest.approx(-31.731)
    assert west == pytest.approx(-60.711)
    assert east == pytest.approx(-60.709)


def test_to_cds_request_uses_documented_field_names():
    req = _make_request()
    payload = req.to_cds_request()
    assert payload["variable"] == ["surface_solar_radiation_downwards"]
    assert payload["date"] == ["2024-01-01/2024-01-31"]
    assert payload["data_format"] == "csv"
    assert len(payload["area"]) == 4


def test_fetch_point_hourly_parses_response_and_records_actual_era5_point(tmp_path: Path):
    fake_client = FakeCdsClient(era5_lat=-31.7, era5_lon=-60.7)
    client = CopernicusEra5LandClient(
        api_key="fake-key", raw_download_dir=tmp_path, cds_client=fake_client
    )
    response = client.fetch_point_hourly(_make_request())

    assert fake_client.last_dataset == "reanalysis-era5-land-timeseries"
    assert response.era5_latitude == pytest.approx(-31.7)
    assert response.era5_longitude == pytest.approx(-60.7)
    assert len(response.hourly) == 24
    assert set(response.hourly.columns) == {"valid_time", "value"}
    assert response.hourly["value"].iloc[0] == pytest.approx(1_000_000.0)


def test_missing_api_key_raises_credentials_error(tmp_path: Path):
    client = CopernicusEra5LandClient(api_key=None, raw_download_dir=tmp_path)
    with pytest.raises(CdsCredentialsError):
        client.fetch_point_hourly(_make_request())


def test_unrecognized_column_raises_clear_parsing_error(tmp_path: Path):
    class BrokenCdsClient:
        def retrieve(self, dataset, request, target):
            pd.DataFrame({"time": ["2024-01-01T00:00:00"], "lat": [-31.7], "lon": [-60.7]}).to_csv(
                target, index=False
            )

    client = CopernicusEra5LandClient(api_key="fake-key", raw_download_dir=tmp_path, cds_client=BrokenCdsClient())
    with pytest.raises(CdsResponseParsingError):
        client.fetch_point_hourly(_make_request())
