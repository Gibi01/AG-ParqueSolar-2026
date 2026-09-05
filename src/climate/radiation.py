"""Agregación de SSRD: valor original -> transformación -> unidad final.

    Valor original  : surface_solar_radiation_downwards (SSRD), en J/m^2,
                      del dataset "reanalysis-era5-land-timeseries" de CDS.
                      El propio CDS etiqueta la variable de este dataset
                      como "(de-accumulated)": cada registro horario ya
                      representa la radiación acumulada durante ESA hora
                      puntual — NO un total corriendo desde el inicio de
                      un forecast, que es como se guarda SSRD en el
                      archivo crudo/bulk de ERA5-Land y que de otro modo
                      requeriría diferenciar manualmente horas
                      consecutivas. Este supuesto es exactamente lo que
                      la prueba de un solo punto de la Fase 10
                      (`--test-era5`) existe para confirmar empíricamente
                      una vez que haya credenciales reales disponibles.
    Transformación  : sumar los valores horarios en J/m^2 dentro de un mes
                      calendario, luego convertir J/m^2 -> kWh/m^2
                      (1 kWh = 3.6e6 J).
    Unidad final    : kWh/m^2 por mes — elegida por interpretabilidad
                      (requisito del proyecto) sobre el J/m^2 crudo.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass

import pandas as pd

from src.data.transformers import joules_per_m2_to_kwh_per_m2

# Límites de plausibilidad generosos para radiación solar superficial
# mensual en latitudes medio-sur (~28-34S, Santa Fe). La climatología real
# de la Pampa argentina ronda 80-110 kWh/m^2/mes en invierno (julio) y
# 190-230 kWh/m^2/mes en verano (enero); los límites se dejan amplios a
# propósito ya que esto es una guarda de plausibilidad, no un modelo climatológico.
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
    """Agrega una serie horaria de SSRD ya de-acumulada (columnas
    `valid_time`, `value` en J/m^2) en una única cifra mensual de kWh/m^2.
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
    """Combina los meses muestreados (ene/abr/jul/oct) en una única cifra
    representativa mediante un promedio simple, según la metodología de
    MVP del proyecto (documentado como un placeholder — no una afirmación
    sobre la insolación de todo el año)."""
    if not monthly_values_kwh_m2:
        raise ValueError("monthly_values_kwh_m2 is empty.")
    return sum(monthly_values_kwh_m2) / len(monthly_values_kwh_m2)
