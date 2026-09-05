import pandas as pd
import pytest

from src.climate.radiation import (
    PLAUSIBLE_MONTHLY_KWH_M2_RANGE,
    RadiationAggregationError,
    aggregate_monthly_kwh_m2,
    representative_solar_score,
)
from src.data.transformers import JOULES_PER_KWH, joules_per_m2_to_kwh_per_m2


def test_joules_per_m2_to_kwh_per_m2_conversion():
    assert joules_per_m2_to_kwh_per_m2(JOULES_PER_KWH) == pytest.approx(1.0)
    assert joules_per_m2_to_kwh_per_m2(0.0) == 0.0


def _make_hourly_series(year: int, month: int, hourly_value_j_m2: float) -> pd.DataFrame:
    import calendar

    n_hours = calendar.monthrange(year, month)[1] * 24
    times = pd.date_range(f"{year}-{month:02d}-01", periods=n_hours, freq="h")
    return pd.DataFrame({"valid_time": times, "value": [hourly_value_j_m2] * n_hours})


def test_aggregate_monthly_kwh_m2_sums_correctly():
    # 1.000.000 J/m^2 cada hora de enero de 2024 (744 horas)
    hourly = _make_hourly_series(2024, 1, 1_000_000.0)
    result = aggregate_monthly_kwh_m2(hourly, 2024, 1)
    expected_kwh = (744 * 1_000_000.0) / JOULES_PER_KWH
    assert result.radiation_kwh_m2 == pytest.approx(expected_kwh)
    assert result.n_hours_used == 744
    assert result.n_hours_expected == 744


def test_aggregate_monthly_kwh_m2_raises_on_insufficient_coverage():
    hourly = _make_hourly_series(2024, 1, 1_000_000.0).iloc[:100]  # muchísimo menos que un mes completo
    with pytest.raises(RadiationAggregationError):
        aggregate_monthly_kwh_m2(hourly, 2024, 1)


def test_aggregate_monthly_kwh_m2_flags_implausible_values():
    # Un valor horario irrealmente enorme debería fallar el chequeo de plausibilidad
    hourly = _make_hourly_series(2024, 7, 50_000_000.0)
    result = aggregate_monthly_kwh_m2(hourly, 2024, 7)
    assert not result.is_plausible
    assert result.radiation_kwh_m2 > PLAUSIBLE_MONTHLY_KWH_M2_RANGE[1]


def test_representative_solar_score_is_mean_of_months():
    assert representative_solar_score([220.0, 140.0, 90.0, 170.0]) == pytest.approx(155.0)


def test_representative_solar_score_empty_raises():
    with pytest.raises(ValueError):
        representative_solar_score([])
