import json

import numpy as np

from alga_twin.demo import demo_parameters
from alga_twin.model import Conditions
from alga_twin.reporting import error_metrics, manifest


def test_manifest_provenance():
    result = json.loads(manifest(demo_parameters(), Conditions(), data_csv=b"abc", mode="test"))
    assert result["input_sha256"] == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert result["scientific_status"].startswith("Illustrative")


def test_rmse_mae():
    result = error_metrics(np.array([1.0, 2.0, 3.0]), np.array([1.0, 3.0, 3.0]))
    assert abs(result["rmse"] - (1 / 3) ** 0.5) < 1e-8
