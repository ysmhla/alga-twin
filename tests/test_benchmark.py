"""Actual PEtab/pyPESTO checks on declared synthetic fixtures, not lab validation."""

import json
import shutil
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("petab.v2", reason="Full benchmark toolchain requires Python 3.12 and .[benchmark]")
pytest.importorskip("pypesto")

from alga_twin.benchmark.data import load_dataset, sha256
from alga_twin.benchmark.petab import export_petab, load_petab
from alga_twin.benchmark.pypesto import objective_value
from alga_twin.benchmark.run import run_registry
from alga_twin.calibration import predict_run
from alga_twin.demo import demo_model_parameters

ROOT = Path(__file__).resolve().parents[1] / "benchmark"


def clone(tmp_path):
    destination = tmp_path / "data"
    shutil.copytree(ROOT / "datasets/synthetic_batch", destination)
    return destination


def read_meta(directory):
    return json.loads((directory / "metadata.json").read_text())


def write_meta(directory, meta):
    (directory / "metadata.json").write_text(json.dumps(meta))


def load(directory):
    return load_dataset(directory / "metadata.json", ROOT / "metadata.schema.json")


def test_licence_units_bases_species_checks_and_no_default_fallback(tmp_path):
    directory = clone(tmp_path)
    original = read_meta(directory)
    assert load(directory).metadata["licence"]["id"] == "MIT"
    for field, value in [
        ("licence", {**original["licence"], "status": "UNVERIFIED"}),
        ("licence", {**original["licence"], "redistribution_allowed": False}),
        ("units", {**original["units"], "N": "mg_nitrate/liter"}),
        ("basis", {"biomass": "carbon", "nitrogen": "elemental_nitrogen"}),
        ("species", "Chlorella minutissima"),
        ("light", {**original["light"], "unit": "watt/meter**2"}),
        ("DOI", "10.3390/pr9030496"),
    ]:
        write_meta(directory, {**original, field: value})
        with pytest.raises(ValueError):
            load(directory)
    missing = {**original}
    missing.pop("licence")
    write_meta(directory, missing)
    with pytest.raises(ValueError, match="schema"):
        load(directory)
    write_meta(directory, original)
    (directory / "observations.csv").write_text("modified")
    with pytest.raises(ValueError, match="Checksum"):
        load(directory)


def test_dataset_references_cannot_escape_directory(tmp_path):
    directory = clone(tmp_path)
    meta = read_meta(directory)
    meta["files"]["licence"]["path"] = "../../LICENSE"
    write_meta(directory, meta)
    with pytest.raises(ValueError, match="leaves"):
        load(directory)


@pytest.mark.parametrize(
    "kind,light,forcing,s",
    [
        ("monod", "monod", False, 1),
        ("monod", "haldane", False, 0.5),
        ("droop", "haldane", True, 0.5),
        ("droop", "han", False, 1),
    ],
)
def test_petab_roundtrip_nll_units_and_mass_balance(tmp_path, kind, light, forcing, s):
    directory = clone(tmp_path)
    job = json.loads((directory / "job.json").read_text())
    job.update(kind=kind, light=light, diurnal=forcing)
    job["parameters"] = {
        name: asdict(p)
        for name, p in demo_model_parameters(
            kind, light, temperature=forcing, diurnal=forcing, extinction_exponent=s
        ).items()
    }
    if light == "han":
        job["search"]["han_k"] = job["search"].pop("mu_max_day")
    for run in job["runs"]:
        run["temperature_c"] = 23.0 if forcing else None
        if kind == "droop":
            run["initial_state"].append(0.09)
    (directory / "job.json").write_text(json.dumps(job))
    meta = read_meta(directory)
    meta["files"]["job"]["sha256"] = sha256(directory / "job.json")
    meta["light"]["mode"] = "diurnal_half_sine" if forcing else "constant"
    if kind == "droop":
        meta["units"]["q"] = "g_N/g_DW"
    write_meta(directory, meta)
    dataset = load(directory)
    before, search, errors = dataset.problem()
    path = export_petab(dataset, tmp_path / "exchange")
    after, search2, errors2, problem = load_petab(path)
    assert not problem.validate().has_errors()
    assert search == search2 and errors.kind == errors2.kind
    assert {k: tuple(v) for k, v in errors.scales.items()} == errors2.scales
    for coordinate in [0.1, 0.5, 0.9]:
        assert objective_value(before, search, errors, [coordinate]) == pytest.approx(
            objective_value(after, search2, errors2, [coordinate]), rel=1e-10, abs=1e-8
        )
    for old, new in zip(before, after, strict=True):
        assert old.run_id == new.run_id and old.model.state_units == new.model.state_units
        fitted_name = next(iter(search))
        values = {fitted_name: old.model.value(fitted_name)}
        p1, t1 = predict_run(old, values)
        p2, t2 = predict_run(new, values)
        np.testing.assert_allclose(p1, p2, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(t1.total_n_mg_L, t2.total_n_mg_L, rtol=1e-12)
        np.testing.assert_allclose(t2.total_n_mg_L, new.model.retained_nitrogen(new.initial_state), atol=3e-6)
        assert np.max(np.diff(t2.N)) <= 1e-8
    assert "LICENCE.txt" in json.loads((path.parent / "checksums.json").read_text())
    with pytest.raises(ValueError, match="overwrite"):
        export_petab(dataset, path.parent)
    (path.parent / "measurements.tsv").write_text("modified")
    with pytest.raises(ValueError, match="checksum"):
        load_petab(path)


def test_dark_transparent_export_limit_and_units(tmp_path):
    directory = clone(tmp_path)
    job = json.loads((directory / "job.json").read_text())
    job["parameters"] = {
        name: asdict(p)
        for name, p in demo_model_parameters(extinction_a0=0, background_extinction_m_inv=0).items()
    }
    for run in job["runs"]:
        run["conditions"]["incident_light_umol_m2_s"] = 0.0
    (directory / "job.json").write_text(json.dumps(job))
    meta = read_meta(directory)
    meta["files"]["job"]["sha256"] = sha256(directory / "job.json")
    meta["light"]["values"] = {r["run_id"]: 0 for r in job["runs"]}
    write_meta(directory, meta)
    path = export_petab(load(directory), tmp_path / "exchange")
    runs, _, _, _ = load_petab(path)
    for run in runs:
        _, trajectory = predict_run(run, {"mu_max_day": 0.9})
        np.testing.assert_allclose(trajectory.X, run.initial_state[0])
        np.testing.assert_allclose(trajectory.N, run.initial_state[1])
        np.testing.assert_allclose(trajectory.total_n_mg_L, run.model.retained_nitrogen(run.initial_state))


def test_real_pypesto_profiles_cv_and_scoreboard_have_licence_and_splits(tmp_path):
    destination = tmp_path / "run"
    assert run_registry(ROOT / "registry.json", destination) == 0
    evidence = json.loads((destination / "synthetic_batch/evidence.json").read_text())
    assert evidence["supported"]
    assert evidence["profile_crosscheck"]["profile_rows"] >= 5
    assert evidence["profile_crosscheck"]["absolute_nll_difference"] < 1e-3
    assert evidence["metadata"]["origin"] == "SYNTHETIC"
    assert {row["split"] for row in evidence["cross_validation"]["metrics"]} == {"in-sample", "held-out"}
    scoreboard = (destination / "scoreboard.md").read_text()
    assert "Licence: MIT" in scoreboard and "SYNTHETIC" in scoreboard
    assert "In-sample RMSE" in scoreboard and "Held-out RMSE" in scoreboard
    assert "3/3" in scoreboard and "pyPESTO" in scoreboard
    curves = pd.read_csv(destination / "synthetic_batch/pypesto_profiles.csv")
    assert curves.coordinate.min() == 0 and curves.coordinate.max() == 1


def test_bad_licence_is_refused_and_still_has_explicit_scoreboard_line(tmp_path):
    directory = clone(tmp_path)
    meta = read_meta(directory)
    meta["licence"]["status"] = "UNVERIFIED"
    write_meta(directory, meta)
    shutil.copy(ROOT / "metadata.schema.json", tmp_path / "metadata.schema.json")
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"schema_version": 1, "datasets": ["data/metadata.json"]}))
    assert run_registry(registry, tmp_path / "run") == 1
    text = (tmp_path / "run/scoreboard.md").read_text()
    assert "Licence:" in text and "REFUSED / FAILED" in text and "NOT SCORED" in text
    assert not (tmp_path / "run/synthetic_batch/evidence.json").exists()


def test_flat_benchmark_cannot_bypass_identifiability_gate(tmp_path):
    directory = clone(tmp_path)
    job = json.loads((directory / "job.json").read_text())
    job["error_model"]["scales"] = {"X": [100, "g_DW/liter"], "N": [1000, "mg_N/liter"]}
    (directory / "job.json").write_text(json.dumps(job))
    meta = read_meta(directory)
    meta["files"]["job"]["sha256"] = sha256(directory / "job.json")
    write_meta(directory, meta)
    shutil.copy(ROOT / "metadata.schema.json", tmp_path / "metadata.schema.json")
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"schema_version": 1, "datasets": ["data/metadata.json"]}))
    assert run_registry(registry, tmp_path / "run") == 1
    evidence = json.loads((tmp_path / "run/synthetic_batch/evidence.json").read_text())
    assert not evidence["supported"]
    assert evidence["estimates"]["mu_max_day"]["value"] is None
    assert evidence["estimates"]["mu_max_day"]["interval"] is None
    assert {f["status"] for f in evidence["cross_validation"]["folds"]} == {"NOT IDENTIFIABLE"}
    assert evidence["cross_validation"]["metrics"] == []
    scoreboard = (tmp_path / "run/scoreboard.md").read_text()
    assert "0/3" in scoreboard and "NOT AGGREGATED" in scoreboard


def test_petab_entrypoint_rechecks_permission_and_metadata_units(tmp_path):
    directory = clone(tmp_path)
    path = export_petab(load(directory), tmp_path / "exchange")
    metadata_path = path.parent / "dataset_metadata.json"
    original = json.loads(metadata_path.read_text())
    checksums_path = path.parent / "checksums.json"
    for change in [
        {"licence": {**original["licence"], "status": "UNVERIFIED"}},
        {"units": {**original["units"], "N": "mg_nitrate/liter"}},
    ]:
        metadata_path.write_text(json.dumps({**original, **change}))
        checksums = json.loads(checksums_path.read_text())
        checksums[metadata_path.name] = sha256(metadata_path)
        checksums_path.write_text(json.dumps(checksums))
        with pytest.raises(ValueError):
            load_petab(path)
