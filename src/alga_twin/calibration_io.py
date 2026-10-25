"""Explicit JSON job + long-form CSV adapter, independent of the UI."""

from dataclasses import asdict, fields

import numpy as np
import pandas as pd

from .calibration import CalibrationRun, ErrorModel, FitParameter
from .demo import demo_model_parameters
from .model import Conditions
from .models import DroopModel, MonodModel, simulate_model
from .parameters import Parameter


def load_job(config: dict, observations: pd.DataFrame):
    expected = {"format_version", "kind", "light", "diurnal", "parameters", "runs", "search", "error_model"}
    if set(config) != expected or config["format_version"] != 1:
        raise ValueError("Unsupported job schema; use format_version=1 and the documented explicit keys")
    if config["kind"] not in {"monod", "droop"} or not isinstance(config["diurnal"], bool):
        raise ValueError("Unknown nutrient model or non-boolean diurnal flag")
    if set(observations.columns) != {"run_id", "time_day", "observable", "value", "unit", "replicate"}:
        raise ValueError("Long CSV needs run_id,time_day,observable,value,unit,replicate")
    params = {name: Parameter(**record) for name, record in config["parameters"].items()}
    search = {name: FitParameter(**spec) for name, spec in config["search"].items()}
    errors = ErrorModel(**config["error_model"])
    condition_keys = {f.name for f in fields(Conditions)}
    cls = MonodModel if config["kind"] == "monod" else DroopModel
    runs = []
    for run in config["runs"]:
        if set(run) != {"run_id", "origin", "conditions", "initial_state", "temperature_c"}:
            raise ValueError(
                "Each run needs explicit id, origin, conditions, initial_state and temperature_c"
            )
        if set(run["conditions"]) != condition_keys:
            raise ValueError("All four condition fields must be explicit; no example-condition fallback")
        model = cls(
            params,
            Conditions(**run["conditions"]),
            light=config["light"],
            diurnal=config["diurnal"],
            temperature_c=run["temperature_c"],
        )
        selected = observations[observations.run_id == run["run_id"]].drop(columns="run_id")
        runs.append(
            CalibrationRun(run["run_id"], model, tuple(run["initial_state"]), selected, run["origin"])
        )
    if set(observations.run_id) != {r.run_id for r in runs} or len({r.run_id for r in runs}) != len(runs):
        raise ValueError("Config/CSV run ids must match exactly without duplicates")
    return tuple(runs), search, errors


def synthetic_job():
    """Seeded, explicitly SYNTHETIC multi-run example; no species data imported."""
    params = demo_model_parameters()
    rng = np.random.default_rng(619)
    descriptions, frames = [], []
    for i, (light, nitrogen) in enumerate([(60, 9), (200, 35), (500, 90)]):
        conditions = Conditions(
            biomass_initial_g_L=0.06,
            nitrogen_initial_mg_L=nitrogen,
            incident_light_umol_m2_s=light,
            optical_path_m=0.05,
        )
        model = MonodModel(params, conditions)
        initial = (0.06, nitrogen)
        curve = simulate_model(model, np.linspace(0, 5, 8), initial)
        for observable, unit, sd in [("X", "g_DW/liter", 0.003), ("N", "mg_N/liter", 0.3)]:
            frames.append(
                pd.DataFrame(
                    {
                        "run_id": f"synthetic-{i}",
                        "time_day": curve.time_day,
                        "observable": observable,
                        "value": curve[observable] + rng.normal(0, sd, len(curve)),
                        "unit": unit,
                        "replicate": "technical-1",
                    }
                )
            )
        descriptions.append(
            {
                "run_id": f"synthetic-{i}",
                "origin": "SYNTHETIC",
                "conditions": asdict(conditions),
                "initial_state": initial,
                "temperature_c": None,
            }
        )
    config = {
        "format_version": 1,
        "kind": "monod",
        "light": "monod",
        "diurnal": False,
        "parameters": {name: asdict(p) for name, p in params.items()},
        "runs": descriptions,
        "search": {"mu_max_day": asdict(FitParameter(0.3, 1.8, 0.7))},
        "error_model": asdict(ErrorModel("additive", {"X": (0.003, "g_DW/liter"), "N": (0.3, "mg_N/liter")})),
    }
    return config, pd.concat(frames, ignore_index=True)
