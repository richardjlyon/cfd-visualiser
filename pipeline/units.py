"""Named unit constants for monetary and energy quantities (PIPE-07).

Importers must use these symbols rather than string/float literals so unit
drift is caught by grep and by the fixture tests in tests/test_units.py.
"""
from __future__ import annotations

# String labels (for column metadata, axis labels)
GBP: str = "GBP"
GBP_PER_MWH: str = "GBP/MWh"
MWH: str = "MWh"
GWH: str = "GWh"
TCO2E: str = "tCO2e"

# Scale factors (divide raw £/MWh figures by these to render larger units)
GBP_M: float = 1_000_000.0
GBP_BN: float = 1_000_000_000.0
MWH_PER_GWH: float = 1_000.0


def gbp_to_millions(value_gbp: float) -> float:
    """Convert raw GBP amount to millions of GBP."""
    return value_gbp / GBP_M


def gbp_to_billions(value_gbp: float) -> float:
    """Convert raw GBP amount to billions of GBP."""
    return value_gbp / GBP_BN


def mwh_to_gwh(value_mwh: float) -> float:
    """Convert MWh to GWh."""
    return value_mwh / MWH_PER_GWH


def millions_to_gbp(value_millions: float) -> float:
    """Convert millions of GBP back to raw GBP (inverse of gbp_to_millions)."""
    return value_millions * GBP_M
