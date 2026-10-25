"""Source records are evidence, not species-transfer or validation guarantees."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from math import isfinite

import pint

UNITS = pint.UnitRegistry()
for definition in (
    "g_DW = [dry_biomass]",
    "g_C = [biomass_carbon]",
    "g_N = [elemental_nitrogen]",
    "mg_N = 0.001 * g_N",
    "mg_O2 = [oxygen_mass]",
):
    UNITS.define(definition)

SPECIES = "Chlorella minutissima"
LM21 = "https://doi.org/10.3390/pr9030496"
M18 = "https://doi.org/10.1016/j.jtbi.2018.07.016"
BL21 = "https://arxiv.org/html/2108.10009v1"


@dataclass(frozen=True)
class Parameter:
    value: float | None
    low: float | None
    high: float | None
    unit: str
    source: str | None
    status: str
    species: str
    conditions: str
    basis: str
    tier: str
    evidence: str
    locator: str = ""

    def __post_init__(self) -> None:
        if self.status not in {"VERIFIED", "UNVERIFIED", "NO_SPECIES_DATA"}:
            raise ValueError("Unknown evidence status")
        if self.tier not in {"DEMO", "LITERATURE", "MEASURED"}:
            raise ValueError("Choose DEMO, LITERATURE or MEASURED tier")
        UNITS.parse_units(self.unit)
        if not self.basis or not self.conditions or not self.species:
            raise ValueError("Basis, species and conditions must be explicit")
        if any(v is not None and not isfinite(v) for v in (self.value, self.low, self.high)):
            raise ValueError("Parameter values and bounds must be finite")
        if (self.low is None) != (self.high is None):
            raise ValueError("Both range endpoints must be supplied, or neither")
        if self.low is not None and self.low > self.high:
            raise ValueError("Range endpoints are reversed")
        if self.status == "NO_SPECIES_DATA" and any(v is not None for v in (self.value, self.low, self.high)):
            raise ValueError("NO_SPECIES_DATA must stay unset")
        if self.status == "VERIFIED" and (
            self.value is None or not self.source or not self.source.startswith("https://")
        ):
            raise ValueError("VERIFIED needs a value and source URL")
        if self.tier == "DEMO" and self.status != "UNVERIFIED":
            raise ValueError("Synthetic demo values cannot be VERIFIED")
        if self.low is not None and self.evidence != "reported_range":
            raise ValueError("A point or assumption must not acquire invented range endpoints")

    def override_warning(self, value: float) -> str | None:
        if not isfinite(value):
            raise ValueError("Override must be finite")
        if self.status == "VERIFIED" and self.low is not None and (value < self.low or value > self.high):
            return (
                f"Your value {value:g} {self.unit} is outside the source-reported range "
                f"[{self.low:g}, {self.high:g}]. This range applies only to {self.conditions}."
            )
        return None


def coefficient_unit(exponent: float, basis: str = "dry_weight") -> str:
    if not 0 < exponent <= 1:
        raise ValueError("Extinction exponent must satisfy 0 < s <= 1")
    mass = {"dry_weight": "g_DW", "carbon": "g_C"}.get(basis)
    if mass is None:
        raise ValueError("Extinction basis must be dry_weight or carbon")
    return f"liter ** {float(exponent)!r} / {mass} ** {float(exponent)!r} / meter"


def convert_extinction(record: Parameter, exponent: float, *, carbon_fraction: float | None = None) -> float:
    """Convert a supplied coefficient to (g DW/L)-based optics; never assume f_C."""
    if record.value is None:
        raise ValueError("Extinction is unset: measure extinction directly")
    target = coefficient_unit(exponent, record.basis)
    converted = (record.value * UNITS(record.unit)).to(target).magnitude
    if record.basis == "carbon":
        if carbon_fraction is None or not isfinite(carbon_fraction) or not 0 < carbon_fraction <= 1:
            raise ValueError("Carbon to dry-weight conversion requires an explicit 0 < f_C <= 1")
        converted *= carbon_fraction**exponent
    return float(converted)


def parameter_units(exponent: float = 1.0) -> dict[str, tuple[str, str]]:
    return {
        "mu_max_day": ("1/day", "specific_growth"),
        "k_n_mg_L": ("mg_N/liter", "elemental_nitrogen"),
        "k_i_umol_m2_s": ("micromole/meter**2/second", "photons"),
        "biomass_yield_g_per_gN": ("g_DW/g_N", "dry_weight_per_nitrogen"),
        "extinction_a0": (coefficient_unit(exponent), "dry_weight"),
        "background_extinction_m_inv": ("1/meter", "medium"),
        "loss_rate_day": ("1/day", "specific_growth"),
        "extinction_exponent": ("dimensionless", "dimensionless"),
    }


def c_minutissima_preset() -> dict[str, Parameter]:
    """Read-only literature catalogue. NOT a complete executable Monod preset."""
    context = (
        "LM21 Table 1/Fig. 2; Aleya et al. data; light 30–550 umol/m2/s; "
        "light response at 10, 30, 35 degC; pH uncontrolled; oxygen assumed 135% saturation"
    )

    def entry(value, unit, basis, evidence="reported_point", locator="Table 2", status="VERIFIED"):
        return Parameter(
            value, None, None, unit, LM21, status, SPECIES, context, basis, "LITERATURE", evidence, locator
        )

    records = {
        name: Parameter(
            None,
            None,
            None,
            unit,
            None,
            "NO_SPECIES_DATA",
            SPECIES,
            "No applicable species/model value established in audited sources",
            basis,
            "LITERATURE",
            "missing",
        )
        for name, (unit, basis) in parameter_units().items()
    }
    records["extinction_a0"] = replace(records["extinction_a0"], source=M18, locator="Table 1")
    records.update(
        {
            "haldane_mu_opt_day": entry(0.64, "1/day", "specific_growth", locator="Table 2, footnote a"),
            "haldane_i_opt": entry(150.0, "micromole/meter**2/second", "photons"),
            "haldane_alpha": entry(0.006, "meter**2*second/micromole/day", "light_response_slope"),
            "lot_a_g": entry(22.4, "dimensionless", "dimensionless"),
            "lot_a_m": entry(17.6, "dimensionless", "dimensionless"),
            "lot_e_g": entry(1.14e5, "joule/mole", "activation_energy"),
            "lot_e_m": entry(1.21e5, "joule/mole", "activation_energy"),
            "lot_t0": entry(35.0, "degree_Celsius", "reference_temperature"),
            "reported_lot_optimum": entry(
                29.3, "degree_Celsius", "LOT_result_not_CTMI_parameter", locator="Section 3.1; low oxygen"
            ),
            "oxygen_k_m": entry(
                0.203,
                "(liter/mg_O2)**0.09",
                "oxygen_toxicity",
                evidence="adopted_unit_conflict",
                status="UNVERIFIED",
            ),
            "oxygen_n": entry(0.09, "dimensionless", "dimensionless", evidence="adopted_point"),
        }
    )
    for name in ("ctmi_t_min", "ctmi_t_opt", "ctmi_t_max"):
        records[name] = Parameter(
            None,
            None,
            None,
            "degree_Celsius",
            LM21,
            "NO_SPECIES_DATA",
            SPECIES,
            "Appendix A defines CTMI; complete species-specific cardinal triplet not reported",
            "temperature",
            "LITERATURE",
            "missing",
            "Appendix A",
        )
    records["carbon_fraction"] = Parameter(
        None,
        None,
        None,
        "g_C/g_DW",
        None,
        "NO_SPECIES_DATA",
        SPECIES,
        "Requires measurement or applicable source",
        "carbon_per_dry_weight",
        "LITERATURE",
        "missing",
    )
    return records


def provenance_rows(parameters) -> list[dict]:
    """Preserve source bounds, but revoke verified value status after a numeric override."""
    records = dict(parameters.provenance)
    rows = []
    for name, (unit, basis) in parameter_units(parameters.extinction_exponent).items():
        current = getattr(parameters, name)
        record = records.get(name)
        if record is None:
            record = Parameter(
                current,
                None,
                None,
                unit,
                None,
                "UNVERIFIED",
                parameters.species,
                "Explicit user input; no source established",
                basis,
                parameters.tier,
                "user_input",
            )
        else:
            if record.species != parameters.species:
                raise ValueError(f"{name}: source species differs from the active configuration")
            if parameters.tier == "DEMO" and record.status != "UNVERIFIED":
                raise ValueError("DEMO configurations cannot present VERIFIED literature evidence")
            # Also reject a stale coefficient record after an exponent change.
            incompatible = UNITS(record.unit).dimensionality != UNITS(unit).dimensionality
            if incompatible or record.basis != basis:
                raise ValueError(
                    f"{name}: provenance units/basis do not match the active model; convert explicitly"
                )
            if record.unit != unit:
                raise ValueError(f"{name}: convert provenance to the documented model unit before execution")
            if record.value != current:
                record = replace(
                    record,
                    value=current,
                    status="UNVERIFIED",
                    evidence="user_override",
                    unit=unit,
                    basis=basis,
                    low=None,
                    high=None,
                )
                # Range evidence is kept separately in the warning below, not fabricated for the override.
        row = {"parameter": name, **asdict(record)}
        original = records.get(name)
        row["source_value"] = original.value if original is not None else None
        row["source_low"] = original.low if original is not None else None
        row["source_high"] = original.high if original is not None else None
        row["override_warning"] = records[name].override_warning(current) if name in records else None
        rows.append(row)
    return rows
