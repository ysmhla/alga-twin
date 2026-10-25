"""Reproducible scoreboard: native gates/CV plus real pyPESTO profile cross-check."""

from __future__ import annotations

import argparse
import json
import platform
from importlib.metadata import version
from pathlib import Path

import numpy as np

from .. import __version__
from ..calibration import fit_joint, leave_one_run_out
from .data import load_dataset, local_file, sha256
from .petab import export_petab, load_petab
from .pypesto import run_profiles


def _cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def _summary(metrics, split):
    if metrics.empty:
        return "NOT SCORED"
    selected = metrics[metrics.split == split]
    if selected.empty:
        return "NOT SCORED"
    rows = []
    for observable, frame in selected.groupby("observable", sort=True):
        score = np.sqrt(np.sum(frame.n * frame.rmse**2) / np.sum(frame.n))
        rows.append(f"{observable}: {score:.6g} {frame.unit.iloc[0]}")
    return "; ".join(rows)


def run_registry(registry_path: str | Path, output: str | Path, *, scoreboard_path=None):
    registry_file = Path(registry_path).resolve()
    base = registry_file.parent
    registry = json.loads(registry_file.read_text())
    if (
        set(registry) != {"schema_version", "datasets"}
        or registry["schema_version"] != 1
        or not registry["datasets"]
    ):
        raise ValueError("Use registry schema_version=1 with a nonempty dataset-path list")
    root = Path(output).resolve()
    if root.exists() and any(root.iterdir()):
        raise ValueError("Benchmark output must be new/empty; no silent overwrite of previous results")
    if root == base or base.is_relative_to(root):
        raise ValueError("Benchmark output must not replace its source directory")
    root.mkdir(parents=True, exist_ok=True)
    rows, sections, ids = [], [], set()
    environment = {
        "alga_twin": __version__,
        "python": platform.python_version(),
        **{name: version(name) for name in ("petab", "pypesto", "numpy", "pandas", "scipy")},
        "registry_sha256": sha256(registry_file),
        "estimates_and_cv_engine": "AlgaTwin SciPy reoptimized profile gates / leave-one-whole-run-out",
        "external_crosscheck": "pyPESTO Powell optimization and parameter_profile, same exported PEtab objective",
    }
    (root / "environment.json").write_text(json.dumps(environment, indent=2) + "\n")
    failures = 0
    for reference in registry["datasets"]:
        metadata = None
        dataset_id = Path(reference).parent.name
        try:
            source = local_file(base, reference)
            metadata = json.loads(source.read_text())
            dataset_id = metadata.get("id", dataset_id)
            dataset = load_dataset(source, local_file(base, "metadata.schema.json"))
            if dataset_id in ids:
                raise ValueError("Duplicate dataset id in registry")
            ids.add(dataset_id)
            destination = root / dataset_id
            if not destination.resolve().is_relative_to(root):
                raise ValueError("Invalid dataset output id")
            destination.mkdir()
            petab_file = export_petab(dataset, destination / "petab")
            runs, search, errors, problem = load_petab(petab_file)
            validation = problem.validate()
            gate = fit_joint(runs, search, errors)
            crosscheck = run_profiles(runs, search, errors)
            tolerance = 1e-3 + 1e-6 * abs(gate.nll)
            if (
                abs(crosscheck.best_nll - gate.nll) > tolerance
                or crosscheck.profiles.nll.min() < gate.nll - tolerance
            ):
                raise RuntimeError(
                    "pyPESTO/native optimum mismatch; no parameter result or benchmark score accepted"
                )
            cv = leave_one_run_out(runs, search, errors)
            payload = gate.report()
            payload["profile_crosscheck"] = {
                "engine": f"pyPESTO {crosscheck.version}",
                "nll": crosscheck.best_nll,
                "absolute_nll_difference": abs(crosscheck.best_nll - gate.nll),
                "tolerance": tolerance,
                "profile_rows": len(crosscheck.profiles),
            }
            payload["metadata"] = metadata
            payload["cross_validation"] = {
                "method": cv.method,
                "engine": environment["estimates_and_cv_engine"],
                "folds": cv.folds.to_dict("records"),
                "metrics": cv.metrics.to_dict("records"),
            }
            (destination / "evidence.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
            gate.profiles.to_csv(destination / "native_profiles.csv", index=False)
            crosscheck.profiles.to_csv(destination / "pypesto_profiles.csv", index=False)
            gate.metrics.to_csv(destination / "in_sample_metrics.csv", index=False)
            cv.metrics.to_csv(destination / "cv_metrics.csv", index=False)
            cv.folds.to_csv(destination / "cv_folds.csv", index=False)
            cv.predictions.to_csv(destination / "held_out_predictions.csv", index=False)
            scored = int((cv.folds.status == "SCORED").sum())
            status = "SUPPORTED" if gate.supported and scored == len(runs) else "NOT FULLY SUPPORTED"
            if status != "SUPPORTED":
                failures += 1
            rows.append(
                {
                    "dataset": dataset_id,
                    "origin": metadata["origin"],
                    "species": metadata["species"],
                    "model": f"{runs[0].model.kind}/{runs[0].model.light}",
                    "in_sample": _summary(gate.metrics, "in-sample"),
                    "held_out": _summary(cv.metrics, "held-out")
                    if scored == len(runs)
                    else "NOT AGGREGATED: incomplete fold coverage",
                    "folds": f"{scored}/{len(runs)}",
                    "status": status,
                    "licence": metadata["licence"]["id"],
                }
            )
            sections.append(
                f"### {_cell(dataset_id)}\n\n"
                f"Licence: {_cell(metadata['licence']['id'])}; {_cell(metadata['licence']['url'])}; "
                f"review status: {_cell(metadata['licence']['status'])}.\n\n"
                f"Attribution: {_cell(metadata['licence']['attribution'])}.\n\n"
                f"DOI: {_cell(metadata['DOI'] or 'None')}; status: {_cell(metadata['doi_status'])}.\n\n"
                f"PEtab validation: {len(validation)} issue(s); native model reader required. "
                f"pyPESTO {crosscheck.version}: {len(crosscheck.profiles)} profile points; "
                f"NLL difference {abs(crosscheck.best_nll - gate.nll):.6g}.\n"
            )
        except (ValueError, TypeError, KeyError, RuntimeError, OSError) as exc:
            failures += 1
            licence = (
                metadata.get("licence", {}).get("id", "UNVERIFIED")
                if isinstance(metadata, dict)
                else "UNVERIFIED"
            )
            rows.append(
                {
                    "dataset": dataset_id,
                    "origin": "UNVERIFIED",
                    "species": "UNVERIFIED",
                    "model": "NOT RUN",
                    "in_sample": "NOT SCORED",
                    "held_out": "NOT SCORED",
                    "folds": "0",
                    "status": "REFUSED / FAILED",
                    "licence": licence,
                }
            )
            sections.append(
                f"### {_cell(dataset_id)}\n\nLicence: {_cell(licence)}; permission/data checks not accepted.\n\n"
                f"REFUSED / FAILED: {_cell(exc)}. No score or point estimate reported.\n"
            )
    measured = any(row["origin"] == "MEASURED" for row in rows)
    data_statement = (
        "Measured origins are provider-declared; no independent biological validation is claimed. "
        if measured
        else "No accepted measured cultivation dataset is present in this registry. "
    )
    header = (
        "# AlgaTwin benchmark scoreboard\n\n"
        "Only registered, checked-input problems are attempted. "
        + data_statement
        + "SYNTHETIC results verify software behavior, not independent biological prediction accuracy.\n\n"
        "Estimates and whole-run CV: AlgaTwin profile-gated SciPy engine. External full-data profile cross-check: pyPESTO. "
        "Search bounds/SDs are explicit assumptions; intervals are conditional marginal asymptotic profiles. "
        "Incomplete held-out folds are not pooled into an optimistic score.\n\n"
        "| Dataset | Origin | Model | In-sample RMSE | Held-out RMSE | Scored folds | Conditional parameter gate | Licence |\n"
        "|---|---|---|---|---|---|---|---|\n"
    )
    lines = [
        "| "
        + " | ".join(
            _cell(row[key])
            for key in ("dataset", "origin", "model", "in_sample", "held_out", "folds", "status", "licence")
        )
        + " |"
        for row in rows
    ]
    report = (
        header
        + "\n".join(lines)
        + "\n\n"
        + "\n".join(sections)
        + f"\nSoftware: AlgaTwin {__version__}; PEtab {environment['petab']}; pyPESTO {environment['pypesto']}; Python {environment['python']}.\n"
    )
    (root / "scoreboard.md").write_text(report)
    (root / "scoreboard.json").write_text(
        json.dumps({"rows": rows, "failed_or_unsupported": failures}, indent=2) + "\n"
    )
    if scoreboard_path is not None:
        Path(scoreboard_path).write_text(report)
    return failures


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Licensed-input AlgaTwin benchmark; synthetic checks are not biological validation"
    )
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scoreboard", type=Path, help="Explicit additional scoreboard destination")
    args = parser.parse_args(argv)
    return 1 if run_registry(args.registry, args.output, scoreboard_path=args.scoreboard) else 0
