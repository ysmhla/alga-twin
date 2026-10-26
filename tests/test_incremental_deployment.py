"""Regression for new decision modules beside a compatible cached fitter."""

import subprocess
import sys


def test_decision_imports_do_not_require_new_exports_from_cached_calibration():
    # Match the observed hosting failure: old calibration API has no provenance
    # export. A facade retains existing callable semantics but omits that name.
    script = """
import sys
import types
import alga_twin.calibration as original
cached = types.ModuleType("alga_twin.calibration")
for name, value in vars(original).items():
    if name != "run_provenance":
        setattr(cached, name, value)
sys.modules["alga_twin.calibration"] = cached
from alga_twin.decision_io import synthetic_decision_problem, load_selection
from alga_twin.model_selection import compare_models
config, data, _ = synthetic_decision_problem()
candidates, errors = load_selection(config, data)
result = compare_models(candidates[:2], errors, **config["decision"], profile_points=5)
assert result.recommendation == "monod + monod light", result.table.to_string()
"""
    subprocess.run([sys.executable, "-c", script], check=True, capture_output=True, text=True, timeout=120)
