"""PEtab 2.0 native-model exchange using the exact existing AlgaTwin simulator.

The PEtab spec is model-language agnostic. libpetab's default model factory
cannot read this native JSON language: use load_petab(), which supplies a Model
adapter to its public Problem constructor and runs the official validators.
No SBML/AMICI portability or independent biological validity is implied.
"""

from __future__ import annotations

import json
from dataclasses import asdict, replace
from pathlib import Path

import pandas as pd
import petab.v2 as pt
import yaml
from petab.v2.core import ProblemConfig
from petab.v2.models import Model

from .. import __version__
from ..calibration import CalibrationRun, ErrorModel, FitParameter, _validate_problem
from ..model import Conditions
from ..models import DroopModel, MonodModel
from ..parameters import Parameter
from .data import BenchmarkDataset, local_file, sha256, validate_permission, validate_problem_metadata

LANGUAGE = "alga_twin_native_v1"


class NativeModel(Model):
    """Public libpetab model interface; JSON identifies package equations/units."""

    type_id = LANGUAGE

    def __init__(self, definition: dict, model_id="alga_model"):
        if definition["format"] != LANGUAGE or definition["implementation_version"] != __version__:
            raise ValueError(
                "Native model format/implementation version differs; reproduce with the recorded release"
            )
        self.definition, self._model_id = definition, model_id
        self.params = {name: Parameter(**record) for name, record in definition["parameters"].items()}
        cls = {"monod": MonodModel, "droop": DroopModel}[definition["kind"]]
        self.model = cls(
            self.params,
            Conditions(**definition["conditions"]),
            light=definition["light"],
            diurnal=definition["diurnal"],
            temperature_c=definition["temperature_c"],
        )
        self.model.validate_initial(definition["initial_state"])
        expected_units = dict(zip(self.model.states, self.model.state_units, strict=True))
        if definition["state_units"] != expected_units or definition["time_unit"] != "day":
            raise ValueError("Native state/time units differ from documented solver units")
        self.entities = {name: p.value for name, p in self.params.items()}
        self.entities.update(zip(self.model.states, definition["initial_state"], strict=True))
        self.entities.update(
            {k: definition["conditions"][k] for k in ("incident_light_umol_m2_s", "optical_path_m")}
        )
        if definition["temperature_c"] is not None:
            self.entities["temperature_c"] = definition["temperature_c"]

    @property
    def model_id(self):
        return self._model_id

    @staticmethod
    def from_file(filepath_or_buffer, model_id, base_path=None):
        root = Path(base_path or ".").resolve()
        return NativeModel(json.loads(local_file(root, str(filepath_or_buffer)).read_text()), model_id)

    def to_file(self, filename=None):
        if filename is None:
            raise ValueError("Supply a native model output path")
        Path(filename).write_text(json.dumps(self.definition, indent=2, allow_nan=False) + "\n")

    def get_parameter_value(self, id_):
        if id_ not in self.entities or id_ in self.model.states:
            raise ValueError(f"Unknown constant parameter: {id_}")
        return self.entities[id_]

    def get_free_parameter_ids_with_values(self):
        return ((key, value) for key, value in self.entities.items() if key not in self.model.states)

    def get_parameter_ids(self):
        return list(self.get_valid_parameters_for_parameter_table())

    def has_entity_with_id(self, entity_id):
        return entity_id in self.entities

    def get_valid_parameters_for_parameter_table(self):
        return [key for key in self.entities if key not in self.model.states]

    def get_valid_ids_for_condition_table(self):
        return list(self.entities)

    def symbol_allowed_in_observable_formula(self, id_):
        return id_ in self.entities

    def is_valid(self):
        return True  # Constructor validates actual parameter records/model/initial state.

    def is_state_variable(self, id_):
        return id_ in self.model.states


def _write_table(frame, root, name):
    frame.to_csv(root / name, sep="\t", index=False)


def export_petab(dataset: BenchmarkDataset, output: str | Path) -> Path:
    """Export every loaded problem to PEtab 2 tables + faithful native JSON model."""
    runs, search, errors = dataset.problem()
    _validate_problem(runs, search, errors)
    root = Path(output).resolve()
    if root.exists() and any(root.iterdir()):
        raise ValueError("PEtab export requires a new or empty directory; no silent overwrite")
    root.mkdir(parents=True, exist_ok=True)
    base = runs[0]
    definition = {
        "format": LANGUAGE,
        "implementation_version": __version__,
        "kind": base.model.kind,
        "light": base.model.light,
        "diurnal": base.model.diurnal,
        "parameters": {n: asdict(p) for n, p in base.model.params.items()},
        "conditions": asdict(base.model.conditions),
        "temperature_c": base.model.temperature_c,
        "initial_state": base.initial_state,
        "state_units": dict(zip(base.model.states, base.model.state_units, strict=True)),
        "time_unit": "day",
    }
    NativeModel(definition).to_file(root / "model.json")
    _write_table(
        pd.DataFrame(
            [
                {
                    "parameterId": name,
                    "lowerBound": p.low,
                    "upperBound": p.high,
                    "nominalValue": p.initial,
                    "estimate": "true",
                    "algaTwinSearchScale": p.scale,
                    "unit": base.model.params[name].unit,
                }
                for name, p in search.items()
            ]
        ),
        root,
        "parameters.tsv",
    )
    used = set(dataset.observations.observable)
    _write_table(
        pd.DataFrame(
            [
                {
                    "observableId": f"obs_{state}",
                    "observableFormula": state,
                    "noiseFormula": errors.scales[state][0],
                    "noiseDistribution": "normal" if errors.kind == "additive" else "log-normal",
                    "unit": base.model.state_units[base.model.states.index(state)],
                }
                for state in base.model.states
                if state in used
            ]
        ),
        root,
        "observables.tsv",
    )
    measurements, conditions, experiments = [], [], []
    for i, run in enumerate(runs):
        experiment, condition = f"experiment_{i}", f"condition_{i}"
        frame = run.observations.rename(
            columns={"time_day": "time", "observable": "observableId", "value": "measurement"}
        ).copy()
        frame["observableId"] = "obs_" + frame.observableId
        frame["experimentId"], frame["runId"], frame["dataOrigin"] = experiment, run.run_id, run.origin
        measurements.append(frame)
        values = dict(zip(run.model.states, run.initial_state, strict=True))
        values.update(
            {k: getattr(run.model.conditions, k) for k in ("incident_light_umol_m2_s", "optical_path_m")}
        )
        if run.model.temperature_c is not None:
            values["temperature_c"] = run.model.temperature_c
        if run.model.diurnal:
            values.update({k: run.model.value(k) for k in ("period_day", "daylight_day", "dawn_day")})
        conditions.extend(
            {"conditionId": condition, "targetId": key, "targetValue": value} for key, value in values.items()
        )
        experiments.append({"experimentId": experiment, "time": 0, "conditionId": condition})
    _write_table(pd.concat(measurements, ignore_index=True), root, "measurements.tsv")
    _write_table(pd.DataFrame(conditions), root, "conditions.tsv")
    _write_table(pd.DataFrame(experiments), root, "experiments.tsv")
    config = {
        "format_version": "2.0.0",
        "id": dataset.metadata["id"],
        "model_files": {"alga_model": {"location": "model.json", "language": LANGUAGE}},
        **{
            kind + "_files": [kind + "s.tsv"]
            for kind in ("parameter", "measurement", "observable", "condition", "experiment")
        },
    }
    # PEtab uses plural table-key stems but singular file names above are pluralized.
    (root / "problem.yaml").write_text(yaml.safe_dump(config, sort_keys=False))
    (root / "dataset_metadata.json").write_text(json.dumps(dataset.metadata, indent=2) + "\n")
    (root / "LICENCE.txt").write_bytes(
        local_file(dataset.directory, dataset.metadata["files"]["licence"]["path"]).read_bytes()
    )
    files = [p for p in root.iterdir() if p.is_file()]
    (root / "checksums.json").write_text(
        json.dumps({p.name: sha256(p) for p in sorted(files)}, indent=2) + "\n"
    )
    load_petab(
        root / "problem.yaml"
    )  # Official PEtab + native subset checks before reporting export success.
    return root / "problem.yaml"


def load_petab(path: str | Path):
    """Read exported PEtab tables, not a hidden original-job copy. Reject unsupported edits."""
    file = Path(path).resolve()
    root = file.parent
    checksums = json.loads(local_file(root, "checksums.json").read_text())
    required = {
        "problem.yaml",
        "model.json",
        "parameters.tsv",
        "observables.tsv",
        "conditions.tsv",
        "experiments.tsv",
        "measurements.tsv",
        "dataset_metadata.json",
        "LICENCE.txt",
    }
    if checksums.keys() != required or any(
        sha256(local_file(root, name)) != digest for name, digest in checksums.items()
    ):
        raise ValueError("PEtab export checksum mismatch; reproduce export from reviewed source files")
    metadata = json.loads(local_file(root, "dataset_metadata.json").read_text())
    validate_permission(metadata, local_file(root, "LICENCE.txt"))
    raw = yaml.safe_load(file.read_text())
    expected_root = {"format_version", "id", "model_files"} | {
        k + "_files" for k in ("parameter", "measurement", "observable", "condition", "experiment")
    }
    if set(raw) != expected_root:
        raise ValueError("Unsupported PEtab root features; regenerate with the native exporter")
    config = ProblemConfig(**raw, base_path=root, filepath=file)
    if raw.get("format_version") != "2.0.0" or raw.get("model_files") != {
        "alga_model": {"location": "model.json", "language": LANGUAGE}
    }:
        raise ValueError("This reader supports one AlgaTwin native PEtab 2 model")
    for kind in ("parameter", "observable", "measurement", "condition", "experiment"):
        if raw.get(kind + "_files") != [kind + "s.tsv"]:
            raise ValueError("Unsupported PEtab table layout")
    native = NativeModel.from_file("model.json", "alga_model", root)
    tables = {
        kind: pd.read_csv(
            root / (kind + "s.tsv"),
            sep="\t",
            float_precision="round_trip",
            dtype={"replicate": str, "runId": str, "dataOrigin": str},
        )
        for kind in ("parameter", "observable", "measurement", "condition", "experiment")
    }
    columns = {
        "parameter": {
            "parameterId",
            "lowerBound",
            "upperBound",
            "nominalValue",
            "estimate",
            "algaTwinSearchScale",
            "unit",
        },
        "observable": {"observableId", "observableFormula", "noiseFormula", "noiseDistribution", "unit"},
        "measurement": {
            "time",
            "observableId",
            "measurement",
            "unit",
            "replicate",
            "experimentId",
            "runId",
            "dataOrigin",
        },
        "condition": {"conditionId", "targetId", "targetValue"},
        "experiment": {"experimentId", "time", "conditionId"},
    }
    if any(set(tables[k].columns) != expected for k, expected in columns.items()):
        raise ValueError(
            "Unsupported PEtab table columns; priors/placeholders/general mappings are not silently ignored"
        )
    if (
        tables["observable"].observableFormula.duplicated().any()
        or tables["parameter"].parameterId.duplicated().any()
    ):
        raise ValueError("Native reader requires unique parameter ids and one observable per state")
    problem = pt.Problem(
        models=[native],
        config=config,
        parameter_tables=[pt.ParameterTable.from_df(tables["parameter"].copy(deep=True))],
        observable_tables=[pt.ObservableTable.from_df(tables["observable"].copy(deep=True))],
        measurement_tables=[pt.MeasurementTable.from_df(tables["measurement"].copy(deep=True))],
        condition_tables=[pt.ConditionTable.from_df(tables["condition"].copy(deep=True))],
        experiment_tables=[pt.ExperimentTable.from_df(tables["experiment"].copy(deep=True))],
    )
    issues = problem.validate()
    if issues.has_errors():
        raise ValueError("PEtab validation failed: " + "; ".join(issue.message for issue in issues))
    search = {}
    for row in tables["parameter"].itertuples(index=False):
        if str(row.estimate).lower() != "true" or row.unit != native.params[row.parameterId].unit:
            raise ValueError("Only explicitly estimated native parameters with matching units are supported")
        search[row.parameterId] = FitParameter(
            row.lowerBound, row.upperBound, row.nominalValue, row.algaTwinSearchScale
        )
    obs = tables["observable"].set_index("observableId")
    distributions = set(obs.noiseDistribution)
    if len(distributions) != 1 or not distributions <= {"normal", "log-normal"}:
        raise ValueError("Unsupported/mixed PEtab noise distributions")
    error_kind = "additive" if distributions == {"normal"} else "log-normal"
    scales = {}
    for _, row in obs.iterrows():
        state = row.observableFormula
        if state not in native.model.states or row.unit != native.definition["state_units"][state]:
            raise ValueError("Only native state observables with matching units are supported")
        scales[state] = (float(row.noiseFormula), row.unit if error_kind == "additive" else "dimensionless")
    errors = ErrorModel(error_kind, scales)
    runs = []
    for experiment in tables["experiment"].itertuples(index=False):
        if experiment.time != 0:
            raise ValueError("Native batch reader supports one initial period per experiment")
        selected = tables["condition"][tables["condition"].conditionId == experiment.conditionId]
        if selected.targetId.duplicated().any():
            raise ValueError("Duplicate condition target")
        values = dict(zip(selected.targetId, selected.targetValue, strict=True))
        expected = set(native.model.states) | {"incident_light_umol_m2_s", "optical_path_m"}
        if native.model.temperature_c is not None:
            expected.add("temperature_c")
        if native.model.diurnal:
            expected.update({"period_day", "daylight_day", "dawn_day"})
        if values.keys() != expected:
            raise ValueError("Native conditions must explicitly supply starting states and all controls")
        data = tables["measurement"][tables["measurement"].experimentId == experiment.experimentId].copy()
        if data.empty or data.runId.nunique() != 1 or data.dataOrigin.nunique() != 1:
            raise ValueError("Each experiment must identify one run and origin")
        data["observable"] = data.observableId.map(obs.observableFormula)
        data = data.rename(columns={"measurement": "value", "time": "time_day"})
        p = {
            k: replace(
                v,
                value=float(values[k]),
                status="UNVERIFIED",
                low=None,
                high=None,
                evidence="condition_override",
            )
            if k in values
            else v
            for k, v in native.params.items()
        }
        initial = tuple(float(values[state]) for state in native.model.states)
        conditions = Conditions(
            initial[0], initial[1], float(values["incident_light_umol_m2_s"]), float(values["optical_path_m"])
        )
        cls = MonodModel if native.model.kind == "monod" else DroopModel
        model = cls(
            p,
            conditions,
            light=native.model.light,
            diurnal=native.model.diurnal,
            temperature_c=float(values["temperature_c"]) if "temperature_c" in values else None,
        )
        runs.append(
            CalibrationRun(
                str(data.runId.iloc[0]),
                model,
                initial,
                data[["time_day", "observable", "value", "unit", "replicate"]],
                str(data.dataOrigin.iloc[0]),
            )
        )
    _validate_problem(runs, search, errors)
    validate_problem_metadata(metadata, runs)
    return tuple(runs), search, errors, problem
