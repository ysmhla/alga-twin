"""Reproducible, JSON-serializable run records and straightforward metrics."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime

import numpy as np
import pandas as pd

from . import __version__
from .model import Conditions, Parameters
from .parameters import provenance_rows


def error_metrics(observed: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    valid = np.isfinite(observed) & np.isfinite(predicted)
    if not valid.any():
        raise ValueError("No matched finite observations to score")
    residual = observed[valid] - predicted[valid]
    return {"mae": float(np.mean(np.abs(residual))), "rmse": float(np.sqrt(np.mean(residual**2)))}


def manifest(
    parameters: Parameters,
    conditions: Conditions,
    *,
    data_csv: bytes | None,
    mode: str,
    notes: list[str] | None = None,
) -> str:
    payload = {
        "tool": "AlgaTwin",
        "version": __version__,
        "model": "batch-monod-power-extinction-v0.3",
        "calibration_status": mode,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "parameters": asdict(parameters),
        "conditions": asdict(conditions),
        "parameter_provenance": provenance_rows(parameters),
        "parameter_tier": parameters.tier,
        "input_sha256": hashlib.sha256(data_csv).hexdigest() if data_csv is not None else None,
        "numerical_solver": "scipy.solve_ivp(RK45); rtol=1e-8; atol=1e-10; max_step=0.12 day",
        "warnings": notes or [],
        "scientific_status": "Illustrative model; not independently validated for field/lab decisions",
    }
    return json.dumps(payload, indent=2)


def model_dataframe_to_csv(frame: pd.DataFrame) -> bytes:
    return frame.to_csv(index=False, float_format="%.8g").encode("utf-8")
