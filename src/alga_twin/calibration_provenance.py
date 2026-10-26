"""Stable job identity shared by calibration and downstream decision modules.

Kept independent of calibration imports so incremental app updates can load
new decision features beside an already-imported compatible fitter.
"""

import hashlib
from dataclasses import asdict


def run_provenance(run) -> dict:
    """Exact input identity used to bind downstream decisions to a fitted job."""
    return {
        "run_id": run.run_id,
        "origin": run.origin,
        "input_sha256": hashlib.sha256(run.observations.to_csv(index=False).encode()).hexdigest(),
        "kind": run.model.kind,
        "light": run.model.light,
        "temperature_c": run.model.temperature_c,
        "diurnal": run.model.diurnal,
        "conditions": asdict(run.model.conditions),
        "states": run.model.states,
        "state_units": run.model.state_units,
        "initial_state": run.initial_state,
        "parameters_before_fitting": [
            {"parameter": name, **asdict(record)} for name, record in run.model.params.items()
        ],
    }
