"""Explicit same-data model problems and proposed-experiment JSON adapters."""

from copy import deepcopy
from dataclasses import asdict

from .calibration import ErrorModel
from .calibration_io import load_job, synthetic_job
from .demo import demo_model_parameters
from .experiment_design import ExperimentCandidate
from .model import Conditions
from .model_selection import ModelCandidate


def load_selection(config, observations):
    if set(config) != {"format_version", "candidates", "decision"} or config["format_version"] != 1:
        raise ValueError("Selection schema requires format_version=1, candidates and decision")
    if set(config["decision"]) != {"delta_aic", "delta_bic", "adequacy_alpha"}:
        raise ValueError("Specify both IC windows and approximate lack-of-fit alpha")
    candidates, errors = [], None
    for description in config["candidates"]:
        if set(description) != {"name", "job"}:
            raise ValueError("Each model candidate requires name and complete calibration job")
        runs, search, candidate_errors = load_job(description["job"], observations)
        if errors is not None and candidate_errors != errors:
            raise ValueError("Model comparisons require exactly the same fixed error model")
        errors = candidate_errors
        candidates.append(ModelCandidate(description["name"], runs, search))
    return tuple(candidates), errors


def load_experiments(descriptions):
    required = {
        "name",
        "conditions",
        "initial_state",
        "duration_day",
        "sampling_times_day",
        "observables",
        "errors",
        "temperature_c",
        "technical_replicates",
    }
    candidates = []
    for record in descriptions:
        if set(record) != required or set(record["conditions"]) != set(Conditions.__dataclass_fields__):
            raise ValueError("Every proposed experiment field and all four conditions must be explicit")
        values = dict(record)
        values["conditions"] = Conditions(**values["conditions"])
        values["errors"] = ErrorModel(**values["errors"])
        for name in ("initial_state", "sampling_times_day", "observables"):
            values[name] = tuple(values[name])
        candidates.append(ExperimentCandidate(**values))
    return tuple(candidates)


def synthetic_decision_problem():
    """SYNTHETIC / UNVERIFIED / DEMO only; NOT C. minutissima candidate ranges."""
    base, data = synthetic_job()
    models = []
    for kind in ("monod", "droop"):
        for light in ("monod", "haldane"):
            job = deepcopy(base)
            job["kind"], job["light"] = kind, light
            job["parameters"] = {n: asdict(p) for n, p in demo_model_parameters(kind, light).items()}
            if kind == "droop":
                for run in job["runs"]:
                    run["initial_state"] = (*run["initial_state"], 0.09)
            models.append({"name": f"{kind} + {light} light", "job": job})
    config = {
        "format_version": 1,
        "candidates": models,
        "decision": {"delta_aic": 2.0, "delta_bic": 2.0, "adequacy_alpha": 0.01},
    }
    experiments = []
    for name, light, nitrogen, duration, times in [
        ("moderate light, lower N", 100.0, 12.0, 4.0, [0.5, 1.0, 2.0, 3.0, 4.0]),
        ("higher light, higher N", 400.0, 80.0, 4.0, [0.5, 1.0, 2.0, 3.0, 4.0]),
        ("short frequent sampling", 200.0, 35.0, 2.0, [0.2, 0.5, 1.0, 1.5, 2.0]),
        ("dark control", 0.0, 35.0, 4.0, [0.5, 1.0, 2.0, 3.0, 4.0]),
    ]:
        experiments.append(
            asdict(
                ExperimentCandidate(
                    name,
                    Conditions(0.06, nitrogen, light, 0.05),
                    (0.06, nitrogen),
                    duration,
                    tuple(times),
                    ("X", "N"),
                    ErrorModel(**base["error_model"]),
                    None,
                    1,
                )
            )
        )
    return config, data, experiments
