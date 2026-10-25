"""Optical-depth productivity for Haldane growth, not a cultivation recommendation.

Bernard & Lu arXiv:2108.10009v1 Eq. 9 has a high-light branch discrepancy.
The general solver evaluates both stationary points and Y=0 explicitly.
"""

from dataclasses import dataclass

import numpy as np
from scipy.integrate import quad

from .models import _positive, haldane


def compensation_roots(mu_max: float, i_opt: float, alpha: float, respiration: float):
    """Positive light roots of mu(I)=R for 0<R<mu_max; stable quadratic evaluation."""
    for name, value in locals().copy().items():
        _positive(value, name)
    if respiration >= mu_max:
        raise ValueError("Two compensation roots require 0 < R < mu_max")
    a = respiration * mu_max / (alpha * i_opt**2)
    b = mu_max - respiration + 2 * respiration * mu_max / (alpha * i_opt)
    c = respiration * mu_max / alpha
    discriminant = (mu_max - respiration) * (
        mu_max - respiration + 4 * respiration * mu_max / (alpha * i_opt)
    )
    return 2 * c / (b + np.sqrt(discriminant)), (b + np.sqrt(discriminant)) / (2 * a)


def optical_productivity(
    depth: float, incident: float, mu_max: float, i_opt: float, alpha: float, respiration: float
) -> float:
    """P(Y)=integral_0^Y [mu(Is exp(-y))-R]dy, day^-1, Y dimensionless."""
    _positive(depth, "depth", zero=True)
    _positive(incident, "incident", zero=True)
    _positive(respiration, "respiration", zero=True)
    haldane(0, mu_max, i_opt, alpha)  # Validate the response even at Y=0.
    if depth == 0:
        return 0.0
    return float(
        quad(
            lambda y: float(haldane(incident * np.exp(-y), mu_max, i_opt, alpha)) - respiration,
            0,
            depth,
            epsabs=1e-10,
            epsrel=1e-10,
        )[0]
    )


def printed_eq9_depth(
    incident: float, mu_max: float, i_opt: float, alpha: float, respiration: float
) -> float:
    """Diagnostic transcription of BOTH printed branches; may be a minimum/negative.

    Never use as the general optimum. Defined only for incident>0 and 0<R<mu_max.
    """
    _positive(incident, "incident")
    low, high = compensation_roots(mu_max, i_opt, alpha, respiration)
    root = low if haldane(incident, mu_max, i_opt, alpha) > respiration else high
    return float(np.log(incident / root))


@dataclass(frozen=True)
class OpticalOptimum:
    optical_depth: float
    productivity_day_inv: float
    finite: bool
    reason: str
    method: str = "Compare both compensation roots and Y=0 by integrated optical productivity"


def optimal_optical_depth(
    incident: float, mu_max: float, i_opt: float, alpha: float, respiration: float
) -> OpticalOptimum:
    """Global maximum over Y>=0; zero respiration can have only an asymptotic supremum."""
    _positive(incident, "incident", zero=True)
    _positive(respiration, "respiration", zero=True)
    haldane(0, mu_max, i_opt, alpha)
    if incident == 0 or respiration >= mu_max:
        return OpticalOptimum(0, 0, True, "No positive net growth is attainable")
    if respiration == 0:
        supremum = quad(
            lambda y: float(haldane(incident * np.exp(-y), mu_max, i_opt, alpha)), 0, np.inf, epsabs=1e-10
        )[0]
        return OpticalOptimum(
            np.inf, float(supremum), False, "Zero respiration: supremum at infinite optical depth"
        )
    roots = compensation_roots(mu_max, i_opt, alpha, respiration)
    candidates = [0.0] + [float(np.log(incident / root)) for root in roots if root <= incident]
    scores = [optical_productivity(y, incident, mu_max, i_opt, alpha, respiration) for y in candidates]
    best = int(np.argmax(scores))
    return OpticalOptimum(
        candidates[best],
        scores[best],
        True,
        "Zero-depth boundary" if best == 0 else "Positive compensation-point maximum",
    )
