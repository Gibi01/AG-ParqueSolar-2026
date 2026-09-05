"""Primitivas genéricas de conversión de unidades.

La lógica de agregación específica del dominio (p. ej. "cómo convertir
una serie horaria de SSRD en una cifra mensual de kWh/m^2") vive en
src/climate/radiation.py. Este módulo solo contiene las conversiones
chicas y dimensionalmente obvias de las que depende esa lógica, para que
puedan testearse unitariamente de forma aislada.
"""

from __future__ import annotations

JOULES_PER_KWH = 3_600_000.0


def joules_per_m2_to_kwh_per_m2(value_j_per_m2: float) -> float:
    """Convierte una densidad areal de energía de J/m^2 a kWh/m^2.

    1 kWh = 3.6e6 J, entonces kWh/m^2 = (J/m^2) / 3.6e6. Esto es una
    conversión de unidad pura — no dice nada sobre *qué* representa la
    cifra en J/m^2 (instantánea, acumulada por hora, u otra cosa); esa
    determinación semántica se hace en src/climate/radiation.py en base
    a la documentación oficial de CDS para el dataset específico en uso.
    """
    return value_j_per_m2 / JOULES_PER_KWH
