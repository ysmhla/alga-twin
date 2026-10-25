"""Dataset metadata, units and recorded licence evidence are mandatory."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from jsonschema import Draft202012Validator

from ..calibration import _validate_problem
from ..calibration_io import load_job


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local_file(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError("Dataset file references must be nonempty relative paths")
    result = (root / name).resolve()
    if not result.is_relative_to(root.resolve()) or not result.is_file():
        raise ValueError(f"Dataset reference is missing or leaves its directory: {name}")
    return result


@dataclass(frozen=True)
class BenchmarkDataset:
    metadata: dict
    config: dict
    observations: pd.DataFrame
    directory: Path
    licence_text: str

    def problem(self):
        return load_job(self.config, self.observations)


def load_dataset(metadata_path: str | Path, schema_path: str | Path) -> BenchmarkDataset:
    path = Path(metadata_path).resolve()
    root = path.parent
    metadata = json.loads(path.read_text())
    schema = json.loads(Path(schema_path).read_text())
    errors = sorted(Draft202012Validator(schema).iter_errors(metadata), key=lambda e: str(e.path))
    if errors:
        raise ValueError("Metadata schema: " + "; ".join(e.message for e in errors[:5]))
    validate_permission(metadata, local_file(root, metadata["files"]["licence"]["path"]))
    for field in ("job", "observations", "licence"):
        record = metadata["files"][field]
        file = local_file(root, record["path"])
        if sha256(file) != record["sha256"]:
            raise ValueError(f"Checksum mismatch for {field}; recheck data and licence evidence")
    licence_text = local_file(root, metadata["files"]["licence"]["path"]).read_text()
    if not licence_text.strip():
        raise ValueError("Licence evidence must contain the permission/licence text")
    config = json.loads(local_file(root, metadata["files"]["job"]["path"]).read_text())
    observations = pd.read_csv(
        local_file(root, metadata["files"]["observations"]["path"]),
        dtype={"run_id": str, "replicate": str},
        float_precision="round_trip",
    )
    runs, search, noise = load_job(config, observations)
    _validate_problem(runs, search, noise)
    validate_problem_metadata(metadata, runs)
    return BenchmarkDataset(metadata, config, observations, root, licence_text)


def validate_permission(metadata, evidence: Path):
    """Validate recorded permission, not ownership or legal compatibility."""
    licence = metadata["licence"]
    needed = {"id", "url", "attribution", "status", "redistribution_allowed", "reviewer", "reviewed_on"}
    if needed - licence.keys() or any(
        not isinstance(licence[k], str) or not licence[k].strip() for k in needed - {"redistribution_allowed"}
    ):
        raise ValueError("Incomplete licence evidence record")
    if licence["id"].strip().upper() in {"UNKNOWN", "UNVERIFIED", "NONE", "N/A"}:
        raise ValueError("A concrete licence identifier is required")
    if (
        licence["status"] not in {"REPOSITORY_LICENSE", "CHECKED_BY_DATA_PROVIDER"}
        or licence["redistribution_allowed"] is not True
    ):
        raise ValueError("UNVERIFIED or unapproved licence: loading/scoring refused")
    if not licence["url"].startswith("https://") or not urlparse(licence["url"]).netloc:
        raise ValueError("An explicit HTTPS licence evidence URL is required")
    date.fromisoformat(licence["reviewed_on"])
    if sha256(evidence) != metadata["files"]["licence"]["sha256"] or not evidence.read_text().strip():
        raise ValueError("Licence evidence is empty or its recorded checksum differs")


def validate_problem_metadata(metadata, runs):
    """Share unit/species/origin checks between raw-data and PEtab entry points."""
    licence = metadata["licence"]
    if metadata["origin"] not in {"SYNTHETIC", "MEASURED"} or any(
        r.origin != metadata["origin"] for r in runs
    ):
        raise ValueError(
            "Dataset origin must match all run origins; unspecified origin is not benchmark data"
        )
    if any(p.species != metadata["species"] for r in runs for p in r.model.params.values()):
        raise ValueError("Dataset species differs from model parameter species; no implicit species transfer")
    canonical = {
        "time": "day",
        "X": "g_DW/liter",
        "N": "mg_N/liter",
        "light": "micromole/meter**2/second",
        "path": "meter",
    }
    if runs[0].model.kind == "droop":
        canonical["q"] = "g_N/g_DW"
    if metadata["units"] != canonical or metadata["basis"] != {
        "biomass": "dry_weight",
        "nitrogen": "elemental_nitrogen",
    }:
        raise ValueError(
            "Canonical units and DW/elemental-N bases are required; convert source data explicitly"
        )
    for field, attr in (("light", "incident_light_umol_m2_s"), ("path", "optical_path_m")):
        if metadata[field]["values"].keys() != {r.run_id for r in runs}:
            raise ValueError(f"{field} metadata must cover exactly the run ids")
        expected_unit = canonical[field]
        if metadata[field]["unit"] != expected_unit:
            raise ValueError(f"{field} unit must be {expected_unit}")
        if any(metadata[field]["values"][r.run_id] != getattr(r.model.conditions, attr) for r in runs):
            raise ValueError(f"{field} metadata disagrees with controlled run conditions")
    mode = "diurnal_half_sine" if runs[0].model.diurnal else "constant"
    if metadata["light"]["mode"] != mode:
        raise ValueError("Light schedule metadata disagrees with model")
    if metadata["origin"] == "SYNTHETIC" and (
        metadata["species"] != "SYNTHETIC"
        or metadata["doi_status"] != "NOT_APPLICABLE_SYNTHETIC"
        or metadata["DOI"] is not None
    ):
        raise ValueError("Synthetic data must not claim a biological species or invented DOI")
    if metadata["origin"] == "MEASURED" and licence["status"] != "CHECKED_BY_DATA_PROVIDER":
        raise ValueError("Measured data require explicit provider-reviewed licence evidence")
    if (metadata["DOI"] is not None) != (metadata["doi_status"] == "PROVIDED_UNVERIFIED"):
        raise ValueError("DOI value/status disagree; no DOI is verified by syntax checking")
    if metadata["origin"] == "MEASURED" and metadata["doi_status"] == "NOT_APPLICABLE_SYNTHETIC":
        raise ValueError("Measured data cannot use the synthetic DOI status")
