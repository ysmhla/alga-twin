"""Empirical proxy-to-DW observation model; never a species/growth preset.

Equal-weight OLS on paired measurements. No extrapolation or uncertainty claim.
Calibration applies only to the supplied strain, instrument and conditions.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

SIGNAL_UNITS = {"OD": ("dimensionless",), "cell_count": ("cells/mL", "cells/L")}
DW_FACTORS = {"g_DW/liter": 1.0, "g_DW/meter**3": 0.001}


def _signal(values, kind, unit):
    if kind not in SIGNAL_UNITS or unit not in SIGNAL_UNITS[kind]:
        raise ValueError("Choose OD (dimensionless) or cell_count (cells/mL or cells/L)")
    x = np.asarray(values, dtype=float)
    if np.any(~np.isfinite(x)) or np.any(x < 0):
        raise ValueError("Proxy measurements must be finite and nonnegative")
    with np.errstate(over="ignore"):
        converted = x * (1000.0 if unit == "cells/mL" else 1.0)
    if np.any(~np.isfinite(converted)):
        raise ValueError("Canonical proxy values must be finite")
    return converted


@dataclass(frozen=True)
class BiomassCalibration:
    kind: str
    signal_unit: str
    degree: int
    coefficients: tuple[float, ...]  # Ascending powers, in canonical signal units.
    center: float
    scale: float
    scaled_coefficients: tuple[float, ...]
    domain: tuple[float, float]
    r_squared: float
    residuals: pd.DataFrame
    species: str
    conditions: str
    origin: str
    method: str = "Equal-weight ordinary least squares; descriptive in-sample R-squared; no interval"
    status: str = "UNVERIFIED"

    @property
    def canonical_signal_unit(self):
        return "dimensionless" if self.kind == "OD" else "cells/L"

    def predict(self, signal, *, unit: str) -> np.ndarray:
        x = _signal(signal, self.kind, unit)
        if np.any(x < self.domain[0]) or np.any(x > self.domain[1]):
            raise ValueError(
                f"Extrapolation refused: use proxy values within {self.domain} {self.canonical_signal_unit}; "
                "measure new paired dry weights to extend the calibration."
            )
        return np.polynomial.polynomial.polyval((x - self.center) / self.scale, self.scaled_coefficients)

    def report(self):
        return {
            "kind": self.kind,
            "canonical_signal_unit": self.canonical_signal_unit,
            "output_unit": "g_DW/liter",
            "basis": "dry_weight",
            "degree": self.degree,
            "coefficients_ascending_powers": list(self.coefficients),
            "domain": list(self.domain),
            "r_squared_in_sample": self.r_squared,
            "method": self.method,
            "interval": None,
            "status": self.status,
            "species": self.species,
            "conditions": self.conditions,
            "origin": self.origin,
            "scope": "Paired proxy/DW calibration only; instrument and strain transfer not established",
        }


def fit_biomass_calibration(
    data: pd.DataFrame,
    *,
    kind: str,
    signal_unit: str,
    dry_weight_unit: str,
    degree: int,
    species: str,
    conditions: str,
    origin: str,
) -> BiomassCalibration:
    if set(data.columns) != {"signal", "dry_weight"} or data.empty or len(data) > 5000:
        raise ValueError("Supply 1-5000 paired rows with exactly signal,dry_weight columns")
    if degree not in {1, 2}:
        raise ValueError("Choose a linear (1) or quadratic (2) fit")
    if not species.strip() or not conditions.strip() or origin not in {"SYNTHETIC", "MEASURED"}:
        raise ValueError("Supply strain/species, instrument/conditions and explicit data origin")
    if dry_weight_unit not in DW_FACTORS:
        raise ValueError("Use g_DW/liter or g_DW/meter**3; carbon/OD are not dry weight")
    x = _signal(data.signal.to_numpy(), kind, signal_unit)
    y = np.asarray(data.dry_weight, dtype=float) * DW_FACTORS[dry_weight_unit]
    if np.any(~np.isfinite(y)) or np.any(y < 0):
        raise ValueError("Paired dry weights must be finite and nonnegative")
    if len(x) <= degree + 1 or len(np.unique(x)) < degree + 1 or np.ptp(y) == 0:
        raise ValueError("Need residual degrees of freedom, distinct proxy levels and varying dry weights")
    center, scale = float((x.min() + x.max()) / 2), float(np.ptp(x) / 2)
    z = (x - center) / scale
    scaled = np.polynomial.polynomial.polyfit(z, y, degree)
    fitted = np.polynomial.polynomial.polyval(z, scaled)
    derivative = np.polynomial.polynomial.polyder(scaled)
    slopes = np.polynomial.polynomial.polyval([-1.0, 1.0], derivative)
    ends = np.polynomial.polynomial.polyval([-1.0, 1.0], scaled)
    # For degrees 1/2, endpoint derivatives establish monotonicity everywhere.
    if min(slopes) < 0 or max(slopes) <= 0 or min(ends) < -1e-12:
        raise ValueError(
            "Fit is not nonnegative and increasing across the measured domain; inspect residuals"
        )
    physical = np.polynomial.Polynomial(scaled)(np.polynomial.Polynomial([-center / scale, 1 / scale]))
    residuals = pd.DataFrame(
        {"signal_canonical": x, "observed_g_DW_L": y, "fitted_g_DW_L": fitted, "residual_g_DW_L": y - fitted}
    )
    return BiomassCalibration(
        kind,
        signal_unit,
        degree,
        tuple(physical.coef),
        center,
        scale,
        tuple(scaled),
        (float(x.min()), float(x.max())),
        float(1 - np.sum((y - fitted) ** 2) / np.sum((y - y.mean()) ** 2)),
        residuals,
        species.strip(),
        conditions.strip(),
        origin,
    )
