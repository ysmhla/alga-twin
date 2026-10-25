"""Selectable batch models. Numerical verification is not biological validation.

All active parameters are explicit evidence records. No species values live here.
See docs/MODEL.md for assumptions, mass bases and source discrepancies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import asdict
from itertools import pairwise
from types import MappingProxyType

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

from .model import Conditions, Parameters
from .parameters import UNITS, Parameter, coefficient_unit, provenance_rows

_LIGHT_UNIT = "micromole/meter**2/second"
_POINTS, _WEIGHTS = np.polynomial.legendre.leggauss(16)


def _positive(value: float, name: str, *, zero: bool = False) -> None:
    if not np.isfinite(value) or (value < 0 if zero else value <= 0):
        raise ValueError(f"{name} must be finite and {'nonnegative' if zero else 'positive'}")


def haldane(light, mu_max: float, i_opt: float, alpha: float):
    """Gross day^-1; light in umol/m2/s, alpha in day^-1 per light unit."""
    for name, value in (("mu_max", mu_max), ("i_opt", i_opt), ("alpha", alpha)):
        _positive(value, name)
    irradiance = np.asarray(light, dtype=float)
    if np.any(~np.isfinite(irradiance)) or np.any(irradiance < 0):
        raise ValueError("Light must be finite and nonnegative")
    return mu_max * irradiance / (irradiance + (mu_max / alpha) * (irradiance / i_opt - 1) ** 2)


def han_steady(light, sigma: float, tau: float, k_damage: float, k_repair: float, k: float):
    """Steady-state Han response only. All rates must use the same day time base.

    sigma: (day * light unit)^-1; tau: day; k_damage: dimensionless;
    k_repair: day^-1; k: dimensionless. No A/B/C transient states implied.
    """
    for name, value in locals().copy().items():
        if name != "light":
            _positive(value, name)
    irradiance = np.asarray(light, dtype=float)
    if np.any(~np.isfinite(irradiance)) or np.any(irradiance < 0):
        raise ValueError("Light must be finite and nonnegative")
    return (
        k
        * sigma
        * irradiance
        / ((k_damage / k_repair) * tau * (sigma * irradiance) ** 2 + tau * sigma * irradiance + 1)
    )


def han_to_haldane(sigma: float, tau: float, k_damage: float, k_repair: float, k: float):
    """Return (mu_max day^-1, I_opt, alpha) for the steady-state Han expression."""
    for name, value in locals().copy().items():
        _positive(value, name)
    quadratic = k_damage * tau * sigma**2 / k_repair
    return (k * sigma / (tau * sigma + 2 * np.sqrt(quadratic)), 1 / np.sqrt(quadratic), k * sigma)


def ctmi(temperature_c: float, t_min: float, t_opt: float, t_max: float) -> float:
    """Dimensionless cardinal factor, zero outside (Tmin,Tmax); Celsius input."""
    if not np.all(np.isfinite([temperature_c, t_min, t_opt, t_max])):
        raise ValueError("Temperatures must be finite")
    # This domain prevents a pole/negative factor within the cardinal interval.
    if not t_min < t_opt < t_max or 2 * t_opt <= t_min + t_max:
        raise ValueError("CTMI requires Tmin < Topt < Tmax and 2*Topt > Tmin+Tmax")
    t = temperature_c
    if t <= t_min or t >= t_max:
        return 0.0
    return float(
        (t - t_max)
        * (t - t_min) ** 2
        / ((t_opt - t_min) * ((t_opt - t_min) * (t - t_opt) - (t_opt - t_max) * (t_opt + t_min - 2 * t)))
    )


def parameter_schema(kind: str, light: str, temperature: bool, diurnal: bool, exponent: float):
    """Canonical solver units and mass bases for each explicit configuration."""
    if kind not in {"monod", "droop"} or light not in {"monod", "haldane", "han"}:
        raise ValueError("Unknown nutrient or light model")
    schema = {
        "k_n_mg_L": ("mg_N/liter", "elemental_nitrogen"),
        "extinction_a0": (coefficient_unit(exponent), "dry_weight"),
        "background_extinction_m_inv": ("1/meter", "medium"),
        "extinction_exponent": ("dimensionless", "dimensionless"),
        "loss_rate_day": ("1/day", "specific_growth"),
    }
    if kind == "monod":
        schema["biomass_yield_g_per_gN"] = ("g_DW/g_N", "dry_weight_per_nitrogen")
    else:
        schema.update(
            rho_max=("g_N/g_DW/day", "nitrogen_per_dry_weight_per_day"),
            q_min=("g_N/g_DW", "nitrogen_per_dry_weight"),
            q_max=("g_N/g_DW", "nitrogen_per_dry_weight"),
        )
    if light == "monod":
        schema.update(mu_max_day=("1/day", "specific_growth"), k_i_umol_m2_s=(_LIGHT_UNIT, "photons"))
    elif light == "haldane":
        schema.update(
            mu_max_day=("1/day", "specific_growth"),
            i_opt=(_LIGHT_UNIT, "photons"),
            alpha=("meter**2*second/micromole/day", "light_response_slope"),
        )
    else:
        schema.update(
            han_sigma=("meter**2*second/micromole/day", "photon_absorption"),
            han_tau=("day", "turnover_time"),
            han_damage=("dimensionless", "damage_coefficient"),
            han_repair=("1/day", "repair_rate"),
            han_k=("dimensionless", "growth_conversion"),
        )
    if temperature:
        schema.update({name: ("degree_Celsius", "temperature") for name in ("t_min", "t_opt", "t_max")})
    if diurnal:
        schema.update({name: ("day", "time") for name in ("period_day", "daylight_day", "dawn_day")})
    return schema


class ModelBase(ABC):
    """Shared rhs(t, state), params and ordered states; explicit conditions in SI/day units."""

    kind: str
    states: tuple[str, ...]
    state_units: tuple[str, ...]

    def __init__(
        self,
        params: Mapping[str, Parameter],
        conditions: Conditions,
        *,
        light: str = "monod",
        temperature_c: float | None = None,
        diurnal: bool = False,
    ):
        conditions.validate()
        records = dict(params)
        if "extinction_exponent" not in records or records["extinction_exponent"].value is None:
            raise ValueError("Supply an explicit extinction exponent")
        schema = parameter_schema(
            self.kind, light, temperature_c is not None, diurnal, records["extinction_exponent"].value
        )
        if records.keys() != schema.keys():
            raise ValueError(
                f"Parameter keys differ: missing={schema.keys() - records.keys()}, extra={records.keys() - schema.keys()}"
            )
        species = {p.species for p in records.values()}
        tiers = {p.tier for p in records.values()}
        if len(species) != 1 or ("DEMO" in tiers and tiers != {"DEMO"}):
            raise ValueError("Do not mix source species or DEMO and research tiers")
        nonnegative = {"extinction_a0", "background_extinction_m_inv", "loss_rate_day"}
        unrestricted = {"t_min", "t_opt", "t_max", "dawn_day"}
        for name, (unit, basis) in schema.items():
            record = records[name]
            if record.value is None:
                raise ValueError(f"{name} is unset; supply measured or explicitly UNVERIFIED evidence")
            if record.unit != unit or record.basis != basis:
                raise ValueError(f"{name}: explicitly convert to {unit} with basis {basis}")
            if name not in unrestricted:
                _positive(record.value, name, zero=name in nonnegative)
        self.params = MappingProxyType(records)
        self.conditions = conditions
        self.light = light
        self.temperature_c = temperature_c
        self.diurnal = diurnal
        if temperature_c is not None:
            ctmi(temperature_c, self.value("t_min"), self.value("t_opt"), self.value("t_max"))
        if diurnal and not 0 < self.value("daylight_day") <= self.value("period_day"):
            raise ValueError("Daylight must be positive and no longer than the period")
        if self.kind == "droop" and not self.value("q_min") < self.value("q_max"):
            raise ValueError("Droop requires q_min < q_max")

    def value(self, name: str) -> float:
        return self.params[name].value

    def provenance(self) -> pd.DataFrame:
        return pd.DataFrame([{"parameter": name, **asdict(record)} for name, record in self.params.items()])

    def incident_light(self, time: float) -> float:
        if not np.isfinite(time):
            raise ValueError("Time must be finite")
        peak = self.conditions.incident_light_umol_m2_s
        if not self.diurnal:
            return peak
        phase = (time - self.value("dawn_day")) % self.value("period_day")
        daylight = self.value("daylight_day")
        return float(peak * np.sin(np.pi * phase / daylight)) if phase < daylight else 0.0

    def light_growth(self, irradiance):
        if self.light == "monod":
            return self.value("mu_max_day") * irradiance / (self.value("k_i_umol_m2_s") + irradiance)
        if self.light == "haldane":
            return haldane(irradiance, self.value("mu_max_day"), self.value("i_opt"), self.value("alpha"))
        return han_steady(
            irradiance,
            *(self.value(n) for n in ("han_sigma", "han_tau", "han_damage", "han_repair", "han_k")),
        )

    def potential_growth(self, time: float, biomass: float) -> float:
        incident = self.incident_light(time)
        depth = self.conditions.optical_path_m * (
            self.value("background_extinction_m_inv")
            + self.value("extinction_a0") * max(biomass, 0) ** self.value("extinction_exponent")
        )
        if depth == 0 or incident == 0:
            average = float(self.light_growth(incident))
        else:
            # Composite Gaussian quadrature in optical coordinates avoids missing a
            # thin illuminated layer at large optical depths. Dark tails are negligible.
            limit = min(depth, 745.0)
            edges = np.linspace(0, limit, max(1, int(np.ceil(limit / 2))) + 1)
            half = np.diff(edges) / 2
            y = (edges[:-1] + half)[:, None] + half[:, None] * _POINTS
            average = float(
                np.sum(self.light_growth(incident * np.exp(-y)) * _WEIGHTS * half[:, None]) / depth
            )
        if self.temperature_c is not None:
            average *= ctmi(self.temperature_c, self.value("t_min"), self.value("t_opt"), self.value("t_max"))
        return average

    @abstractmethod
    def rhs(self, time: float, state: np.ndarray) -> np.ndarray:
        """State derivatives, ordered as states, per day."""

    @abstractmethod
    def retained_nitrogen(self, state: np.ndarray) -> float:
        """Dissolved plus biomass-associated N, in mg N/L."""

    @abstractmethod
    def nitrogen_loss(self, state: np.ndarray) -> float:
        """Export to untracked loss pool, mg N/L/day; no dissolved recycling."""

    def validate_initial(self, initial) -> np.ndarray:
        initial = np.asarray(initial, dtype=float)
        if initial.shape != (len(self.states),) or np.any(~np.isfinite(initial)):
            raise ValueError(f"Supply finite initial states in order {self.states}")
        if initial[0] <= 0 or initial[1] < 0:
            raise ValueError("Initial X must be positive and N nonnegative")
        if self.kind == "droop" and not self.value("q_min") <= initial[2] <= self.value("q_max"):
            raise ValueError("Initial quota must lie within [q_min, q_max]")
        return initial


class MonodModel(ModelBase):
    kind = "monod"
    states = ("X", "N")
    state_units = ("g_DW/liter", "mg_N/liter")

    @classmethod
    def from_baseline(cls, parameters: Parameters, conditions: Conditions):
        """Adapter preserving the current constant-light, no-temperature Monod baseline."""
        parameters.validate()
        records = {}
        for row in provenance_rows(parameters):
            records[row["parameter"]] = Parameter(**{key: row[key] for key in Parameter.__dataclass_fields__})
        return cls(records, conditions)

    def rhs(self, time, state):
        x, n = np.maximum(state, 0)
        mu = self.potential_growth(time, x) * n / (self.value("k_n_mg_L") + n)
        return np.array(
            [(mu - self.value("loss_rate_day")) * x, -1000 * mu * x / self.value("biomass_yield_g_per_gN")]
        )

    def retained_nitrogen(self, state):
        x, n = state
        return n + 1000 * x / self.value("biomass_yield_g_per_gN")

    def nitrogen_loss(self, state):
        return 1000 * self.value("loss_rate_day") * max(state[0], 0) / self.value("biomass_yield_g_per_gN")


class DroopModel(ModelBase):
    kind = "droop"
    states = ("X", "N", "q")
    state_units = ("g_DW/liter", "mg_N/liter", "g_N/g_DW")

    def uptake(self, nitrogen, quota):
        n = max(nitrogen, 0)
        return (
            self.value("rho_max") * n / (self.value("k_n_mg_L") + n) * max(0, 1 - quota / self.value("q_max"))
        )

    def rhs(self, time, state):
        x, n, quota = state
        x = max(x, 0)
        q = max(quota, self.value("q_min"))
        mu = self.potential_growth(time, x) * max(0, 1 - self.value("q_min") / q)
        rho = self.uptake(n, q)
        return np.array([(mu - self.value("loss_rate_day")) * x, -1000 * rho * x, rho - mu * q])

    def retained_nitrogen(self, state):
        x, n, q = state
        return n + 1000 * q * x

    def nitrogen_loss(self, state):
        return 1000 * self.value("loss_rate_day") * max(state[0], 0) * max(state[2], 0)

    def equilibrium_quota(self, nitrogen: float, potential_growth: float) -> float:
        """Fixed-light fast-quota limit only, not an algebraic transient replacement."""
        _positive(potential_growth, "potential_growth")
        _positive(nitrogen, "nitrogen", zero=True)
        u = self.value("rho_max") * nitrogen / (self.value("k_n_mg_L") + nitrogen)
        return (u + potential_growth * self.value("q_min")) / (potential_growth + u / self.value("q_max"))

    def monod_limit(self, potential_growth: float) -> tuple[float, float]:
        """Return effective (mu_max, K_N) under fixed potential growth and dq/dt=0."""
        _positive(potential_growth, "potential_growth")
        rho, q0, ql = (self.value(n) for n in ("rho_max", "q_min", "q_max"))
        denominator = rho + potential_growth * q0
        return (
            potential_growth * rho * (1 - q0 / ql) / denominator,
            self.value("k_n_mg_L") * potential_growth * q0 / denominator,
        )


def simulate_model(model: ModelBase, times_day, initial_state) -> pd.DataFrame:
    """Common solver with a separate removed-N ledger for conservation accounting."""
    times = np.asarray(times_day, dtype=float)
    if times.ndim != 1 or len(times) < 2 or np.any(~np.isfinite(times)):
        raise ValueError("Supply at least two finite times")
    if times[0] != 0 or np.any(np.diff(times) <= 0) or times[-1] > 365:
        raise ValueError("Times must start at zero, increase strictly and end within 365 days")
    initial = model.validate_initial(initial_state)

    def augmented(time, values):
        return np.r_[model.rhs(time, values[:-1]), model.nitrogen_loss(values[:-1])]

    step = min(0.05, model.value("period_day") / 96) if model.diurnal else 0.05
    # Split at dawn/dusk; interpolation across a light switch can otherwise
    # create tiny, unphysical increases of dissolved N in the dark interval.
    breaks = [0.0, float(times[-1])]
    if model.diurnal:
        period, dawn, daylight = (model.value(n) for n in ("period_day", "dawn_day", "daylight_day"))
        for offset in (dawn % period, (dawn + daylight) % period):
            breaks.extend(
                offset + k * period
                for k in range(int(times[-1] / period) + 2)
                if 0 < offset + k * period < times[-1]
            )
    breaks = sorted(set(breaks))
    output = np.empty((len(initial) + 1, len(times)))
    current = np.r_[initial, 0.0]
    output[:, 0] = current
    for start, end in pairwise(breaks):
        solution = solve_ivp(
            augmented, (start, end), current, dense_output=True, rtol=1e-10, atol=1e-12, max_step=step
        )
        if not solution.success or np.any(~np.isfinite(solution.y)):
            raise RuntimeError(f"Numerical solver failed: {solution.message}")
        selected = (times > start) & (times <= end)
        if np.any(selected):
            output[:, selected] = solution.sol(times[selected])
        current = solution.y[:, -1]
    values = output[:-1].T
    if np.any(values[:, :2] < -1e-7):
        raise RuntimeError("Solver returned materially negative concentrations")
    values[:, :2] = np.maximum(values[:, :2], 0)
    if model.kind == "droop" and (
        np.any(values[:, 2] < model.value("q_min") - 1e-8)
        or np.any(values[:, 2] > model.value("q_max") + 1e-8)
    ):
        raise RuntimeError("Solver violated quota bounds")
    result = pd.DataFrame(values, columns=model.states)
    result.insert(0, "time_day", times)
    result["removed_n_mg_L"] = output[-1]
    result["total_n_mg_L"] = [model.retained_nitrogen(state) for state in values] + result.removed_n_mg_L
    return result


def assert_state_units(model: ModelBase) -> None:
    """Check the documented nitrogen identity with distinct biomass and N dimensions."""
    x, n = (UNITS(unit) for unit in model.state_units[:2])
    stored = x * (UNITS(model.state_units[2]) if model.kind == "droop" else 1 / UNITS("g_DW/g_N"))
    stored.to(n.units)  # g N/L to mg N/L; a carbon quota will fail dimensionality.
