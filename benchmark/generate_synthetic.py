"""Regenerate the labelled synthetic fixture; never downloads/digitises real data."""

import json
from pathlib import Path

from alga_twin.benchmark.data import sha256
from alga_twin.calibration_io import synthetic_job

ROOT = Path(__file__).resolve().parent


def main():
    destination = ROOT / "datasets" / "synthetic_batch"
    config, observations = synthetic_job()
    (destination / "job.json").write_text(json.dumps(config, indent=2) + "\n")
    observations.to_csv(destination / "observations.csv", index=False)
    (destination / "LICENCE.txt").write_bytes((ROOT.parent / "LICENSE").read_bytes())
    metadata = {
        "schema_version": 1,
        "id": "synthetic_batch",
        "origin": "SYNTHETIC",
        "species": "SYNTHETIC",
        "reactor": "SYNTHETIC well-mixed batch; effective one-dimensional optical path",
        "light": {
            "mode": "constant",
            "unit": "micromole/meter**2/second",
            "values": {r["run_id"]: r["conditions"]["incident_light_umol_m2_s"] for r in config["runs"]},
        },
        "path": {
            "unit": "meter",
            "values": {r["run_id"]: r["conditions"]["optical_path_m"] for r in config["runs"]},
        },
        "N_source": "SYNTHETIC available elemental-N pool; no real chemical feed compound claimed",
        "units": {
            "time": "day",
            "X": "g_DW/liter",
            "N": "mg_N/liter",
            "light": "micromole/meter**2/second",
            "path": "meter",
        },
        "basis": {"biomass": "dry_weight", "nitrogen": "elemental_nitrogen"},
        "licence": {
            "id": "MIT",
            "url": "https://github.com/ysmhla/alga-twin/blob/main/LICENSE",
            "attribution": "Copyright (c) 2026 AlgaTwin contributors; synthetic software test fixture",
            "status": "REPOSITORY_LICENSE",
            "redistribution_allowed": True,
            "reviewer": "AlgaTwin fixture generator; copied repository MIT licence",
            "reviewed_on": "2026-10-25",
        },
        "DOI": None,
        "doi_status": "NOT_APPLICABLE_SYNTHETIC",
        "source": "alga_twin.calibration_io.synthetic_job; seed 619; all physiological inputs UNVERIFIED; no biological species",
        "files": {
            kind: {"path": name, "sha256": sha256(destination / name)}
            for kind, name in [
                ("job", "job.json"),
                ("observations", "observations.csv"),
                ("licence", "LICENCE.txt"),
            ]
        },
    }
    (destination / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print("Generated SYNTHETIC fixture only:", destination)


if __name__ == "__main__":
    main()
