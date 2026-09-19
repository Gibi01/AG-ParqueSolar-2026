"""Promedios históricos de los meses representativos por celda."""

from __future__ import annotations

import pandas as pd

# Verano (DJF), otoño (MAM), invierno (JJA), primavera (SON).
# 90.25 días incorpora el 29 de febrero en promedio cada cuatro años.
SEASON_DAYS = {1: 90.25, 4: 92.0, 7: 92.0, 10: 91.0}
MONTH_DAYS = {1: 31, 4: 30, 7: 31, 10: 31}


def monthly_climatology(records: pd.DataFrame, months: list[int]) -> pd.DataFrame:
    """Media interanual por mes; conserva NaN cuando falta un mes entero."""
    monthly = records.groupby(["grid_cell_id", "month"])["radiation_kwh_m2"].mean()
    return monthly.unstack("month").reindex(columns=months)


def annual_solar_kwh_m2(records: pd.DataFrame, months: list[int]) -> pd.Series:
    """Estimación anual: irradiación diaria media de cada mes × días de su estación."""
    monthly = monthly_climatology(records, months)
    annual = sum(monthly[month] / MONTH_DAYS[month] * SEASON_DAYS[month] for month in months)
    return annual.where(monthly.notna().all(axis=1))
