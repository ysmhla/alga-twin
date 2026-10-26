"""Inspect built distributions and exercise a real wheel install outside checkout."""

import hashlib
import importlib.metadata
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import numpy as np

import alga_twin
from alga_twin.demo import demo_model_parameters
from alga_twin.model import Conditions
from alga_twin.models import DroopModel, MonodModel, simulate_model


def main():
    project = Path(__file__).resolve().parents[1]
    installed = Path(alga_twin.__file__).resolve()
    if installed.is_relative_to(project):
        raise RuntimeError("This check must use an actual installed wheel, not the source checkout")
    if alga_twin.__version__ != importlib.metadata.version("alga-twin"):
        raise RuntimeError("Installed module/distribution versions differ")
    distributions = project / "dist"
    wheel, source = list(distributions.glob("*.whl")), list(distributions.glob("*.tar.gz"))
    if len(wheel) != 1 or len(source) != 1:
        raise RuntimeError("Check one clean wheel/source archive pair")
    required = {
        "app.py",
        "CITATION.cff",
        "LICENSE",
        "README_PYPI.md",
        "docs/MODEL.md",
        "docs/VERIFICATION.md",
        "paper.md",
        "benchmark/registry.json",
        "benchmark/datasets/synthetic_batch/LICENCE.txt",
    }
    with tarfile.open(source[0], "r:gz") as archive:
        files = {"/".join(Path(m.name).parts[1:]) for m in archive.getmembers() if m.isfile()}
    if not required <= files:
        raise RuntimeError(f"Source archive omits reproducibility files: {required - files}")
    if any(Path(name).name in {"secrets.toml", ".env"} for name in files):
        raise RuntimeError("Refusing distribution containing secret configuration names")
    for kind, cls, initial in [
        ("monod", MonodModel, (0.06, 35.0)),
        ("droop", DroopModel, (0.06, 35.0, 0.09)),
    ]:
        c = Conditions(0.06, 35.0, 180.0, 0.05)
        p = demo_model_parameters(kind, "haldane")
        model = cls(p, c, light="haldane")
        curve = simulate_model(model, np.linspace(0, 2, 9), initial)
        np.testing.assert_allclose(curve.total_n_mg_L, model.retained_nitrogen(initial), atol=2e-6)
        if np.any(np.diff(curve.N) > 1e-8) or np.any(curve[list(model.states)].to_numpy() < 0):
            raise RuntimeError("Installed wheel violated state/nitrogen conditions")
    command = Path(sys.executable).parent / "alga-twin"
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / "SYNTHETIC.csv"
        subprocess.run(
            [
                str(command),
                "simulate",
                "--demo",
                "--days",
                "1",
                "--light",
                "180",
                "--nitrogen",
                "70",
                "--output",
                str(target),
            ],
            cwd=directory,
            check=True,
            timeout=60,
        )
        if not target.is_file():
            raise RuntimeError("Installed CLI produced no output")
        refused = subprocess.run(
            [str(command), "simulate", "--output", str(target)],
            cwd=directory,
            capture_output=True,
            check=False,
            text=True,
            timeout=60,
        )
        if refused.returncode == 0 or "No complete literature Monod preset" not in refused.stderr:
            raise RuntimeError("Installed CLI bypassed the explicit DEMO gate")
    evidence = {
        "version": alga_twin.__version__,
        "installed_module": str(installed),
        "origin": "SYNTHETIC",
        "scientific_status": "Installed-wheel engineering smoke only; no biological validation",
        "checks": [
            "sdist reproducibility files",
            "installed Monod/Droop nitrogen ledger",
            "installed CLI execution outside checkout",
            "missing DEMO flag refusal",
        ],
        "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [*wheel, *source]},
    }
    (distributions / "installed-smoke.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
