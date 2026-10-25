"""Monod growth, nitrogen mass balance and spatially integrated light limitation.

This illustrative, single-species batch model assumes a well-mixed culture,
constant incident irradiance, constant temperature, nitrogen-limited growth,
and an effective one-dimensional optical path. It is not a validated plant twin.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

from .parameters import Parameter, parameter_units, provenance_rows

# Gauss-Legendre quadrature over normalized optical depth [0,1].
_GAUSS_POINTS, _GAUSS_WEIGHTS = np.polynomial.legendre.leggauss(16)
_DEPTH_FRACTIONS = (_GAUSS_POINTS + 1) / 2
_DEPTH_WEIGHTS = _GAUSS_WEIGHTS / 2


@dataclass(frozen=True)
class Parameters:
    """Explicit numerical configuration; no implicit biological parameter defaults."""

    mu_max_day: float
    k_n_mg_L: float
    k_i_umol_m2_s: float
    biomass_yield_g_per_gN: float
    extinction_a0: float
    background_extinction_m_inv: float
    loss_rate_day: float
    extinction_exponent: float
    provenance: tuple[tuple[str, Parameter], ...] = ()
    tier: str = "LITERATURE"
    species: str = "unspecified"

    def validate(self) -> None:
        names = parameter_units(self.extinction_exponent)
        vals = {name: getattr(self, name) for name in names}
        if any(not np.isfinite(v) for v in vals.values()):
            raise ValueError("Parameters must be finite")
        positive = ("mu_max_day", "k_n_mg_L", "k_i_umol_m2_s", "biomass_yield_g_per_gN")
        if any(vals[k] <= 0 for k in positive):
            raise ValueError("Growth, half-saturation and yield parameters must be positive")
        nonnegative = ("extinction_a0", "background_extinction_m_inv", "loss_rate_day")
        if any(vals[k] < 0 for k in nonnegative):
            raise ValueError("Extinction and biomass loss cannot be negative")
        if self.tier not in {"DEMO", "LITERATURE", "MEASURED"}:
            raise ValueError("Unknown parameter tier")
        # Every active value has explicit source/status metadata, including user overrides.
        provenance_rows(self)


@dataclass(frozen=True)
class Conditions:
    """Batch cultivation starting conditions."""

    biomass_initial_g_L: float = 0.1
    nitrogen_initial_mg_L: float = 60.0
    incident_light_umol_m2_s: float = 180.0
    optical_path_m: float = 0.05

    def validate(self) -> None:
        vals = asdict(self)
        if any(not np.isfinite(v) for v in vals.values()):
            raise ValueError("Conditions must be finite")
        if self.biomass_initial_g_L <= 0 or self.nitrogen_initial_mg_L < 0:
            raise ValueError("Initial biomass must be positive and nitrogen nonnegative")
        if self.incident_light_umol_m2_s < 0 or self.optical_path_m <= 0:
            raise ValueError("Incident light must be nonnegative and optical path positive")


def local_irradiance(
    depth_m: np.ndarray | float, biomass_g_L: float, condition: Conditions, p: Parameters
) -> np.ndarray:
    """Effective Beer-Lambert profile, units umol photons m^-2 s^-1."""
    depth = np.asarray(depth_m, dtype=float)
    return condition.incident_light_umol_m2_s * np.exp(
        -(p.background_extinction_m_inv + p.extinction_a0 * max(0, biomass_g_L) ** p.extinction_exponent)
        * depth
    )


def light_limitation(biomass_g_L: float, condition: Conditions, p: Parameters) -> float:
    """Integral over depth of local saturating light response, not f(mean(I))."""
    irradiance = local_irradiance(condition.optical_path_m * _DEPTH_FRACTIONS, biomass_g_L, condition, p)
    local_f = irradiance / (p.k_i_umol_m2_s + irradiance)
    return float(np.dot(local_f, _DEPTH_WEIGHTS))


def growth_rate(biomass_g_L: float, nitrogen_mg_L: float, c: Conditions, p: Parameters) -> float:
    """Gross specific growth (before optional biomass loss), day^-1."""
    n = max(0.0, nitrogen_mg_L)
    return p.mu_max_day * n / (p.k_n_mg_L + n) * light_limitation(biomass_g_L, c, p)


def simulate(
    times_day: np.ndarray | list[float],
    conditions: Conditions | None = None,
    parameters: Parameters | None = None,
) -> pd.DataFrame:
    """Solve a two-state batch system at user-specified days (first day must be zero).

    N is reported in mg elemental nitrogen / L (NOT mg nitrate ion/L).
    A positive loss_rate_day removes biomass without recycling N in this MVP.
    """
    c = conditions or Conditions()
    if parameters is None:
        raise ValueError("Supply explicit parameters; synthetic values require demo_parameters()")
    p = parameters
    c.validate()
    p.validate()
    t = np.asarray(times_day, dtype=float)
    if t.ndim != 1 or len(t) < 2 or np.any(~np.isfinite(t)):
        raise ValueError("Provide at least two finite time points")
    if abs(t[0]) > 1e-10 or np.any(np.diff(t) <= 0) or t[-1] > 365:
        raise ValueError("Time must start at zero, increase strictly, and end within 365 days")

    def rhs(_time: float, state: np.ndarray) -> tuple[float, float]:
        x, n = state
        x = max(0.0, x)
        mu = growth_rate(x, n, c, p)
        # Dissolved nitrogen uptake tracks biomass *gross growth*, not decay.
        return ((mu - p.loss_rate_day) * x, -1000 * (mu * x) / p.biomass_yield_g_per_gN)

    result = solve_ivp(
        rhs,
        (0, float(t[-1])),
        [c.biomass_initial_g_L, c.nitrogen_initial_mg_L],
        t_eval=t,
        method="RK45",
        max_step=0.12,
        rtol=1e-8,
        atol=1e-10,
    )
    if not result.success or np.any(~np.isfinite(result.y)):
        raise RuntimeError(f"Numerical solver failed: {result.message}")
    x, n = result.y
    # Small negative concentrations may arise from numerical tolerances; avoid
    # presenting them as physical concentrations.
    return pd.DataFrame(
        {
            "time_day": t,
            "biomass_g_L": np.maximum(x, 0),
            "nitrate_n_mg_L": np.maximum(n, 0),
        }
    )


def conditions_for_observations(data: pd.DataFrame, base: Conditions) -> Conditions:
    """Use first biomass and first measured nitrogen at t0 as initial observations."""
    first = data.iloc[0]
    nitrogen = (
        float(first["nitrate_n_mg_L"]) if np.isfinite(first["nitrate_n_mg_L"]) else base.nitrogen_initial_mg_L
    )
    return replace(base, biomass_initial_g_L=float(first["biomass_g_L"]), nitrogen_initial_mg_L=nitrogen)
