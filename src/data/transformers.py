"""Generic unit-conversion primitives.

Domain-specific aggregation logic (e.g. "how to turn an hourly SSRD
series into a monthly kWh/m^2 figure") lives in src/climate/radiation.py.
This module only holds the small, dimensionally-obvious conversions that
logic depends on, so they can be unit-tested in isolation.
"""

from __future__ import annotations

JOULES_PER_KWH = 3_600_000.0


def joules_per_m2_to_kwh_per_m2(value_j_per_m2: float) -> float:
    """Convert an energy areal density from J/m^2 to kWh/m^2.

    1 kWh = 3.6e6 J, so kWh/m^2 = (J/m^2) / 3.6e6. This is a pure unit
    conversion — it says nothing about *what* the J/m^2 figure represents
    (instantaneous, hourly-accumulated, or otherwise); that semantic
    determination is made in src/climate/radiation.py based on the
    official CDS documentation for the specific dataset in use.
    """
    return value_j_per_m2 / JOULES_PER_KWH
