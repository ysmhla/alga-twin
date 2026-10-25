"""Same-data information criteria, conditional profile and lack-of-fit gates.

No structural-identifiability proof, held-out score, or biological validation.
Fixed parameters, initial states and fixed noise are explicit conditioning inputs.
"""

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
from scipy.stats import chi2

from .calibration import CalibrationRun, ErrorModel, FitParameter, JointFitResult, fit_joint, run_provenance


@dataclass(frozen=True)
class ModelCandidate:
    name: str
    runs: tuple[CalibrationRun, ...]
    search: dict[str, FitParameter]


@dataclass(frozen=True)
class SelectionResult:
    table: pd.DataFrame
    fits: dict[str, JointFitResult]
    recommendation: str | None
    status: str
    reason: str
    settings: dict

    def report(self):
        # pandas uses NaN for withheld numerical cells; JSON must contain null.
        rows = self.table.astype(object).where(pd.notna(self.table), None).to_dict("records")
        return {
            "status": self.status,
            "recommendation": self.recommendation,
            "reason": self.reason,
            "comparison": rows,
            "settings": self.settings,
            "fits": {name: fit.report() for name, fit in self.fits.items()},
            "scope": "In-sample conditional model support; held-out error not computed here; no biological validation",
        }


def _same_data(candidates):
    if len(candidates) < 2 or len({c.name for c in candidates}) != len(candidates):
        raise ValueError("At least two uniquely named model candidates are required")
    reference = {r.run_id: r for r in candidates[0].runs}
    if not reference:
        raise ValueError("Candidates require observations")
    for candidate in candidates:
        if not candidate.name.strip() or len({r.run_id for r in candidate.runs}) != len(candidate.runs):
            raise ValueError("Names and run ids must be nonempty and unique")
        if {r.run_id for r in candidate.runs} != set(reference):
            raise ValueError("Compare exactly the same run ids")
        for run in candidate.runs:
            other = reference[run.run_id]
            columns = ["time_day", "observable", "replicate", "unit", "value"]
            a = run.observations[columns].sort_values(columns[:3]).reset_index(drop=True)
            b = other.observations[columns].sort_values(columns[:3]).reset_index(drop=True)
            if not a.equals(b) or run.origin != other.origin:
                raise ValueError("Compare exactly the same observations, units, replicates and origins")
            if (
                run.model.conditions != other.model.conditions
                or run.model.temperature_c != other.model.temperature_c
                or run.model.diurnal != other.model.diurnal
                or run.initial_state[:2] != other.initial_state[:2]
            ):
                raise ValueError("Candidate forcing and initial X/N must match for each run")
            if {p.species for p in run.model.params.values()} != {
                p.species for p in other.model.params.values()
            }:
                raise ValueError("Candidate species must match")


def compare_models(candidates, errors: ErrorModel, *, delta_aic, delta_bic, adequacy_alpha, **fit_options):
    """Recommend the simplest eligible model within BOTH supplied IC windows.

    Windows and lack-of-fit alpha are user decision assumptions, not biological
    parameter ranges. Adequacy uses an approximate chi-square residual screen
    (n-k degrees of freedom), conditional on independent fixed Gaussian/log SDs.
    Numerical failures make the comparison incomplete, never a silent winner.
    """
    candidates = tuple(candidates)
    _same_data(candidates)
    if not np.all(np.isfinite([delta_aic, delta_bic, adequacy_alpha])) or min(delta_aic, delta_bic) < 0:
        raise ValueError("IC windows must be finite and nonnegative")
    if not 0 < adequacy_alpha < 1:
        raise ValueError("Supply a lack-of-fit significance level between zero and one")
    settings = {
        "delta_aic": delta_aic,
        "delta_bic": delta_bic,
        "adequacy_alpha": adequacy_alpha,
        "error_model_shared_by_all_candidates": asdict(errors),
        "criteria": "AIC=2*NLL+2*k; BIC=2*NLL+k*log(n); same original-scale likelihood and observations",
        "k": "Fitted shared parameters only; fixed SDs, initial states and other parameters conditional/known",
        "n": "Scalar measurements; independent technical errors assumed; not number of independent cultures",
        "adequacy": "Approximate fixed-noise residual chi-square(n-k) upper-tail screen; not validation",
        "parsimony": "Fewer fitted parameters, then fewer active parameters, then fewer states, then name",
        "fit_options": fit_options,
        "candidate_inputs": {
            c.name: {
                "runs": [run_provenance(r) for r in c.runs],
                "search": {n: asdict(p) for n, p in c.search.items()},
            }
            for c in candidates
        },
    }
    fits, rows = {}, []
    for candidate in candidates:
        n = sum(len(r.observations) for r in candidate.runs)
        k = len(candidate.search)
        row = {
            "model": candidate.name,
            "n": n,
            "k": k,
            "active_parameters": len(candidate.runs[0].model.params),
            "states": len(candidate.runs[0].model.states),
            "status": "INCOMPLETE",
            "reason": "",
            "aic": None,
            "bic": None,
            "residual_chi_square_p_approx": None,
        }
        try:
            fit = fit_joint(candidate.runs, candidate.search, errors, **fit_options)
        except (ValueError, RuntimeError) as exc:
            row["reason"] = str(exc)
            if isinstance(exc, ValueError) and str(exc).startswith("Too few informative points"):
                row["status"] = "INSUFFICIENT DATA"
        else:
            fits[candidate.name] = fit
            if not fit.optimizer_success or any(e.status == "PROFILE FAILED" for e in fit.estimates.values()):
                row["reason"] = "Optimization/profile unresolved; criteria withheld"
            elif not fit.supported:
                row.update(
                    status="NOT IDENTIFIABLE", reason="; ".join(e.reason for e in fit.estimates.values())
                )
            else:
                frame = fit.predictions
                residual = errors.residuals(
                    frame.value.to_numpy(),
                    frame.predicted.to_numpy(),
                    frame.observable,
                    frame.get("log_predicted"),
                )
                p = float(chi2.sf(float(residual @ residual), n - k))
                row.update(
                    aic=2 * fit.nll + 2 * k, bic=2 * fit.nll + k * np.log(n), residual_chi_square_p_approx=p
                )
                if p < adequacy_alpha:
                    row.update(
                        status="LACK OF FIT", reason="Residuals exceed the supplied fixed-noise approximation"
                    )
                else:
                    row.update(
                        status="ELIGIBLE",
                        reason="Conditional profile and approximate residual screens passed",
                    )
        rows.append(row)
    table = pd.DataFrame(rows)
    eligible = table[table.status == "ELIGIBLE"].copy()
    winner = None
    if (table.status == "INCOMPLETE").any():
        status, reason = "INCOMPLETE", "Resolve failed candidate fits before a model recommendation"
    elif eligible.empty:
        status, reason = (
            "NO SUPPORTABLE MODEL",
            "None passed both the conditional profile and residual screens",
        )
    else:
        table["delta_aic"] = table.aic - eligible.aic.min()
        table["delta_bic"] = table.bic - eligible.bic.min()
        acceptable = table[
            (table.status == "ELIGIBLE")
            & (table.delta_aic <= delta_aic + 1e-9)
            & (table.delta_bic <= delta_bic + 1e-9)
        ]
        if acceptable.empty:
            status, reason = "CRITERIA DISAGREE", "No eligible model is within both supplied AIC/BIC windows"
        else:
            winner = acceptable.sort_values(["k", "active_parameters", "states", "model"]).iloc[0].model
            status, reason = (
                "RECOMMENDED",
                "Simplest eligible candidate within both supplied IC windows; conditional evidence only",
            )
    return SelectionResult(table, fits, winner, status, reason, settings)
