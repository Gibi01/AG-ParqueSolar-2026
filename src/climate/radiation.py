"""SSRD aggregation: raw value -> transformation -> final unit.

    Original value : surface_solar_radiation_downwards (SSRD), in J/m^2,
                      from the CDS "reanalysis-era5-land-timeseries"
                      dataset. CDS itself labels this dataset's variable
                      as "(de-accumulated)": each hourly record already
                      represents the radiation accumulated during THAT
                      single hour — NOT a running total since the start
                      of a forecast, which is how SSRD is stored in the
                      raw/bulk ERA5-Land archive and would otherwise
                      require manually differencing consecutive hours.
                      This assumption is exactly what Fase 10's single
                      point test (`--test-era5`) exists to confirm
                      empirically once real credentials are available.
    Transformation  : sum the hourly J/m^2 values within a calendar month,
                      then convert J/m^2 -> kWh/m^2 (1 kWh = 3.6e6 J).
    Final unit      : kWh/m^2 per month — chosen for interpretability
                      (project requirement) over the raw J/m^2.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass

import pandas as pd

from src.data.transformers import joules_per_m2_to_kwh_per_m2

# Generous plausibility bounds for monthly surface solar radiation at
# mid-southern latitudes (~28-34S, Santa Fe). Real Argentine Pampas
# climatology is roughly 80-110 kWh/m^2/month in winter (July) and
# 190-230 kWh/m^2/month in summer (January); bounds are kept wide on
# purpose since this is a plausibility guard, not a climatological model.
PLAUSIBLE_MONTHLY_KWH_M2_RANGE = (20.0, 320.0)

MIN_HOURLY_COVERAGE_FRACTION = 0.95


@dataclass
class MonthlyAggregationResult:
    year: int
    month: int
    radiation_kwh_m2: float
    n_hours_used: int
    n_hours_expected: int
    is_plausible: bool


class RadiationAggregationError(RuntimeError):
    pass


def aggregate_monthly_kwh_m2(hourly: pd.DataFrame, year: int, month: int) -> MonthlyAggregationResult:
    """Aggregate an hourly de-accumulated SSRD series (columns
    `valid_time`, `value` in J/m^2) into a single monthly kWh/m^2 figure.
    """
    mask = (hourly["valid_time"].dt.year == year) & (hourly["valid_time"].dt.month == month)
    month_hours = hourly.loc[mask]

    n_days = calendar.monthrange(year, month)[1]
    n_hours_expected = n_days * 24
    n_hours_used = len(month_hours)

    if n_hours_used < n_hours_expected * MIN_HOURLY_COVERAGE_FRACTION:
        raise RadiationAggregationError(
            f"Insufficient hourly coverage for {year}-{month:02d}: "
            f"{n_hours_used}/{n_hours_expected} hours present "
            f"(< {MIN_HOURLY_COVERAGE_FRACTION:.0%} required)."
        )

    total_j_m2 = float(month_hours["value"].sum())
    radiation_kwh_m2 = joules_per_m2_to_kwh_per_m2(total_j_m2)

    low, high = PLAUSIBLE_MONTHLY_KWH_M2_RANGE
    is_plausible = low <= radiation_kwh_m2 <= high

    return MonthlyAggregationResult(
        year=year,
        month=month,
        radiation_kwh_m2=radiation_kwh_m2,
        n_hours_used=n_hours_used,
        n_hours_expected=n_hours_expected,
        is_plausible=is_plausible,
    )


def representative_solar_score(monthly_values_kwh_m2: list[float]) -> float:
    """Combine the sampled months (Jan/Apr/Jul/Oct) into one representative
    figure via a simple mean, per the project's MVP methodology (documented
    as a placeholder — not a claim about full-year insolation)."""
    if not monthly_values_kwh_m2:
        raise ValueError("monthly_values_kwh_m2 is empty.")
    return sum(monthly_values_kwh_m2) / len(monthly_values_kwh_m2)
