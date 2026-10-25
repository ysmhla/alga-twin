import json
from dataclasses import replace

import numpy as np
import pytest

from alga_twin.cli import main
from alga_twin.model import Conditions, Parameters
from alga_twin.planner import scenario_grid
from alga_twin.trust import local_sensitivity, scenario_warnings


def test_sensitivity_is_finite_and_nonempty():
    result = local_sensitivity(Conditions(), Parameters(), days=6)
    assert len(result) >= 4
    assert np.isfinite(result.elasticity.to_numpy()).all()
    assert result.iloc[0].absolute_elasticity >= result.iloc[-1].absolute_elasticity


def test_sensitivity_needs_valid_horizon():
    with pytest.raises(ValueError):
        local_sensitivity(Conditions(), Parameters(), days=0)


def test_scenario_extrapolation_warnings():
    c = Conditions()
    changed = replace(c, incident_light_umol_m2_s=c.incident_light_umol_m2_s * 2)
    warnings = scenario_warnings(c, changed, calibrated=True, scenario_days=12, observed_days=6)
    assert any("Incident light" in w for w in warnings)
    assert any("duration" in w for w in warnings)


def test_planner_grid_and_pareto_candidates():
    frame = scenario_grid(Conditions(), Parameters(), days=4, steps=3)
    assert len(frame) == 9
    assert frame.sampled_pareto_candidate.any()
    assert frame.biomass_gain_g_L.min() >= -1e-8
    assert frame.biomass_gain_g_L.max() > frame.biomass_gain_g_L.min()


def test_zero_resources_do_not_produce_growth():
    frame = scenario_grid(Conditions(), Parameters(), days=3, steps=3)
    subset = frame[(frame.light_umol_m2_s == 0) | (frame.initial_nitrogen_mg_L == 0)]
    assert abs(subset.biomass_gain_g_L).max() < 1e-8


def test_cli_simulate_and_fit(tmp_path):
    csv = tmp_path / "predicted.csv"
    result = tmp_path / "fit.json"
    assert main(["simulate", "--days", "5", "--output", str(csv)]) == 0
    assert csv.exists()
    assert main(["fit", "--input", str(csv), "--light", "180", "--path-cm", "5", "--output", str(result)]) == 0
    payload = json.loads(result.read_text())
    assert payload["success"]
    assert "mu_max_day" in payload["fitted_names"]
    assert payload["scientific_status"].startswith("In-sample")
