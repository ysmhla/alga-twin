"""Synthetic recovery/failure cases; none are independent biological validation."""

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
from scipy.stats import lognorm, norm

from alga_twin.calibration import (
    CalibrationRun,
    ErrorModel,
    FitParameter,
    fit_joint,
    leave_one_run_out,
    predict_run,
    with_values,
)
from alga_twin.demo import demo_model_parameters
from alga_twin.model import Conditions
from alga_twin.models import DroopModel, MonodModel, simulate_model


def make_runs(kind="monod", light="monod", *, replicates=1, noise=None, days=5, count=3):
    rng = np.random.default_rng(98)
    runs = []
    for index, (incident, nitrogen) in enumerate([(60, 9), (200, 35), (500, 90)][:count]):
        params = demo_model_parameters(kind, light)
        c = Conditions(
            biomass_initial_g_L=0.06, nitrogen_initial_mg_L=nitrogen, incident_light_umol_m2_s=incident
        )
        model = (MonodModel if kind == "monod" else DroopModel)(params, c, light=light)
        initial = (0.06, nitrogen) + ((0.09,) if kind == "droop" else ())
        trajectory = simulate_model(model, np.linspace(0, days, 8), initial)
        rows = []
        for state, unit in zip(model.states, model.state_units, strict=True):
            for t, value in zip(trajectory.time_day, trajectory[state], strict=True):
                for rep in range(replicates):
                    if noise == "log-normal":
                        value_observed = value * np.exp(rng.normal(0, 0.015))
                    elif noise == "additive":
                        sd = {"X": 0.001, "N": 0.1, "q": 0.0002}[state]
                        value_observed = value + rng.normal(0, sd)
                    else:
                        value_observed = value
                    rows.append(
                        {
                            "time_day": t,
                            "observable": state,
                            "value": value_observed,
                            "unit": unit,
                            "replicate": f"technical-{rep}",
                        }
                    )
        runs.append(CalibrationRun(f"run-{index}", model, initial, pd.DataFrame(rows), "SYNTHETIC"))
    return runs


def error_model(kind="additive", *, droop=False):
    if kind == "log-normal":
        return ErrorModel(
            kind, {s: (0.015, "dimensionless") for s in (["X", "N", "q"] if droop else ["X", "N"])}
        )
    scales = {"X": (0.003, "g_DW/liter"), "N": (0.3, "mg_N/liter")}
    if droop:
        scales["q"] = (0.0006, "g_N/g_DW")
    return ErrorModel(kind, scales)


def search_mu():
    return {"mu_max_day": FitParameter(0.3, 1.8, 0.7)}


@pytest.mark.parametrize("kind", ["additive", "log-normal"])
def test_joint_noisy_recovery_and_named_profile_intervals(kind):
    runs = make_runs(noise=kind, replicates=2)
    result = fit_joint(
        runs,
        {**search_mu(), "biomass_yield_g_per_gN": FitParameter(3, 18, 9)},
        error_model(kind),
        profile_points=5,
    )
    assert result.supported, result.table().to_string()
    truth = {name: runs[0].model.value(name) for name in result.estimates}
    for name, estimate in result.estimates.items():
        assert estimate.value == pytest.approx(truth[name], rel=0.04)
        assert estimate.interval[0] < estimate.value < estimate.interval[1]
        assert "profile likelihood" in estimate.method and "chi-square" in estimate.method
    assert result.cutoff == pytest.approx(3.841458820694124)
    assert set(result.metrics.split) == {"in-sample"}
    assert len(result.predictions) == sum(len(r.observations) for r in runs)
    assert set(result.predictions.replicate) == {"technical-0", "technical-1"}
    assert all(p["origin"] == "SYNTHETIC" for p in result.provenance)
    assert "independent biological validation" in result.report()["scientific_status"]
    assert result.report()["search_bounds_not_literature_ranges"]


def test_log_likelihood_matches_independent_scipy_densities():
    y, pred = np.array([0.12, 0.3, 0.7]), np.array([0.1, 0.25, 0.8])
    obs = ["X"] * len(y)
    additive = ErrorModel("additive", {"X": (0.02, "g_DW/liter")})
    lognormal = ErrorModel("log-normal", {"X": (0.12, "dimensionless")})
    assert additive.nll(y, pred, obs) == pytest.approx(-norm.logpdf(y, loc=pred, scale=0.02).sum())
    assert lognormal.nll(y, pred, obs) == pytest.approx(-lognorm.logpdf(y, s=0.12, scale=pred).sum())
    for invalid in [np.array([0, 0.3, 0.7]), np.array([-1, 0.3, 0.7])]:
        with pytest.raises(ValueError, match="positive"):
            lognormal.nll(invalid, pred, obs)
    # Additive normal noise is allowed below a blank; do not clip raw measurements.
    assert np.isfinite(additive.nll(np.array([-0.01, 0.3, 0.7]), pred, obs))


def test_flat_profile_from_no_nitrogen_variation_withholds_estimate():
    runs = []
    for run in make_runs():
        c = replace(run.model.conditions, nitrogen_initial_mg_L=1e10)
        model = MonodModel(dict(run.model.params), c)
        t = np.linspace(0, 3, 7)
        frame = simulate_model(model, t, (0.06, 1e10))
        data = pd.DataFrame(
            {"time_day": t, "observable": "X", "value": frame.X, "unit": "g_DW/liter", "replicate": "one"}
        )
        runs.append(CalibrationRun(run.run_id, model, (0.06, 1e10), data, "SYNTHETIC"))
    result = fit_joint(
        runs,
        {"k_n_mg_L": FitParameter(0.2, 20, 5)},
        ErrorModel("additive", {"X": (0.003, "g_DW/liter")}),
        profile_points=5,
    )
    assert not result.supported
    estimate = result.estimates["k_n_mg_L"]
    assert estimate.status == "NOT IDENTIFIABLE" and "flat" in estimate.reason
    assert estimate.value is None and estimate.interval is None
    assert result.report()["estimates"]["k_n_mg_L"]["value"] is None
    with pytest.raises(ValueError, match="refusing"):
        result.values()


def test_too_few_points_duplicate_ids_and_wrong_units_rejected():
    run = make_runs(count=1)[0]
    sparse = replace(run, observations=run.observations[run.observations.time_day <= 1].copy())
    with pytest.raises(ValueError, match="Too few"):
        fit_joint([sparse], search_mu(), error_model())
    duplicate = pd.concat([run.observations, run.observations.iloc[[2]]])
    with pytest.raises(ValueError, match="Duplicate"):
        replace(run, observations=duplicate)
    wrong = run.observations.copy()
    wrong.loc[wrong.observable == "N", "unit"] = "mg_nitrate/liter"
    with pytest.raises(ValueError, match="units"):
        replace(run, observations=wrong)
    with pytest.raises(ValueError, match="Noise scale"):
        fit_joint([run], search_mu(), ErrorModel("additive", {"X": (3, "mg/liter"), "N": (1, "mg_N/liter")}))
    with pytest.raises(ValueError, match="unique"):
        fit_joint([run, run], search_mu(), error_model())
    with pytest.raises(ValueError, match="mix synthetic"):
        fit_joint([run, replace(run, run_id="real", origin="MEASURED")], search_mu(), error_model())


def test_open_profiles_and_optimizer_failure_cannot_report_points():
    runs = make_runs(count=1)
    result = fit_joint(runs, {"mu_max_day": FitParameter(0.899, 0.901, 0.9)}, error_model(), profile_points=5)
    assert not result.supported
    assert result.estimates["mu_max_day"].value is None
    assert result.estimates["mu_max_day"].interval is None
    failed = fit_joint(runs, search_mu(), error_model(), profile_points=5, max_nfev=1)
    assert not failed.optimizer_success and not failed.supported
    assert failed.estimates["mu_max_day"].status == "PROFILE FAILED"
    assert failed.estimates["mu_max_day"].value is None


def test_droop_recovery_uses_same_interface_and_preserves_nitrogen():
    runs = make_runs("droop", "haldane", count=2, days=3)
    result = fit_joint(runs, search_mu(), error_model(droop=True), profile_points=5)
    assert result.supported, result.table().to_string()
    assert result.values()["mu_max_day"] == pytest.approx(0.9, rel=2e-4)
    for run in runs:
        _, trajectory = predict_run(run, result.values())
        np.testing.assert_allclose(
            trajectory.total_n_mg_L, run.model.retained_nitrogen(run.initial_state), atol=2e-6
        )
        np.testing.assert_allclose(
            trajectory.q * trajectory.X + trajectory.N / 1000,
            run.initial_state[2] * run.initial_state[0] + run.initial_state[1] / 1000,
            atol=2e-9,
        )
        records = with_values(run.model, result.values()).provenance()
        assert set(records.status) == {"UNVERIFIED"}


def test_whole_run_holdouts_have_separate_metrics_and_no_later_data_leakage():
    runs = make_runs(count=2)
    result = leave_one_run_out(runs, search_mu(), error_model(), profile_points=5)
    assert set(result.folds.status) == {"SCORED"}, result.folds.to_string()
    assert set(result.metrics.split) == {"in-sample", "held-out"}
    assert set(result.predictions.split) == {"held-out"}
    assert result.metrics[result.metrics.split == "held-out"].rmse.max() < 1e-4
    modified = runs[0].observations.copy()
    modified.loc[(modified.observable == "X") & (modified.time_day > 0), "value"] *= 1.5
    changed = leave_one_run_out(
        [replace(runs[0], observations=modified), runs[1]], search_mu(), error_model(), profile_points=5
    )
    before = result.predictions[result.predictions.run_id == runs[0].run_id]
    after = changed.predictions[changed.predictions.run_id == runs[0].run_id]
    np.testing.assert_allclose(before.predicted, after.predicted, atol=0, rtol=0)
    assert after.value.sum() != before.value.sum()
    with pytest.raises(ValueError, match="at least two"):
        leave_one_run_out([runs[0]], search_mu(), error_model())


def test_growth_and_absorption_confounding_withholds_both_points():
    params = demo_model_parameters(extinction_a0=0, background_extinction_m_inv=0)
    conditions = Conditions(biomass_initial_g_L=0.06, nitrogen_initial_mg_L=35)
    model = MonodModel(params, conditions)
    curve = simulate_model(model, np.linspace(0, 3, 7), (0.06, 35))
    data = pd.concat(
        [
            pd.DataFrame(
                {
                    "time_day": curve.time_day,
                    "observable": state,
                    "value": curve[state],
                    "unit": unit,
                    "replicate": "one",
                }
            )
            for state, unit in zip(model.states, model.state_units, strict=True)
        ],
        ignore_index=True,
    )
    run = CalibrationRun("same-light", model, (0.06, 35), data, "SYNTHETIC")
    result = fit_joint(
        [run],
        {"mu_max_day": FitParameter(0.7, 1.1, 0.9), "k_i_umol_m2_s": FitParameter(10, 400, 85)},
        error_model(),
        profile_points=5,
    )
    for estimate in result.estimates.values():
        assert estimate.status == "NOT IDENTIFIABLE"
        assert estimate.value is None and estimate.interval is None
        assert "flat" in estimate.reason


@pytest.mark.parametrize("kind", ["monod", "droop"])
@pytest.mark.parametrize("loss", [0, 0.1])
def test_log_numerical_coordinates_match_states_and_conserve_n(kind, loss):
    model = (MonodModel if kind == "monod" else DroopModel)(
        demo_model_parameters(kind, loss_rate_day=loss), Conditions(nitrogen_initial_mg_L=20)
    )
    initial = (0.1, 20) + ((0.09,) if kind == "droop" else ())
    times = np.linspace(0, 8, 41)
    reference = simulate_model(model, times, initial)
    transformed = simulate_model(model, times, initial, log_nitrogen=True)
    np.testing.assert_allclose(
        transformed[list(model.states)], reference[list(model.states)], atol=1e-7, rtol=2e-6
    )
    np.testing.assert_allclose(transformed.total_n_mg_L, model.retained_nitrogen(initial), atol=1e-6)
    assert transformed.log_N.is_monotonic_decreasing
    np.testing.assert_allclose(np.exp(transformed.log_N), transformed.N)
    for n in [1, 1e-250, 0]:
        assert np.isfinite(
            model.log_nitrogen_rate(0, np.array([0.1, n] + ([0.09] if kind == "droop" else [])))
        )
    with pytest.raises(ValueError, match="strictly positive"):
        simulate_model(model, [0, 1], (0.1, 0) + ((0.09,) if kind == "droop" else ()), log_nitrogen=True)


def test_job_loader_roundtrip_and_no_condition_fallback():
    from alga_twin.calibration_io import load_job, synthetic_job

    config, data = synthetic_job()
    runs, search, errors = load_job(config, data)
    assert len(runs) == 3 and set(search) == {"mu_max_day"}
    assert all(r.origin == "SYNTHETIC" for r in runs)
    assert errors.kind == "additive"
    config["runs"][0]["conditions"].pop("optical_path_m")
    with pytest.raises(ValueError, match="explicit"):
        load_job(config, data)


def test_unsupported_training_folds_refuse_held_out_scores():
    result = leave_one_run_out(
        make_runs(count=2),
        search_mu(),
        ErrorModel("additive", {"X": (100, "g_DW/liter"), "N": (1000, "mg_N/liter")}),
        profile_points=5,
    )
    assert set(result.folds.status) == {"NOT IDENTIFIABLE"}
    assert result.metrics.empty and result.predictions.empty


def test_joint_cli_exports_named_intervals_and_split_metrics(tmp_path):
    import json

    from alga_twin.calibration_io import synthetic_job
    from alga_twin.cli import main

    config, data = synthetic_job()
    job, csv, report = tmp_path / "job.json", tmp_path / "observations.csv", tmp_path / "result.json"
    job.write_text(json.dumps(config))
    data.to_csv(csv, index=False)
    assert (
        main(
            [
                "fit-joint",
                "--config",
                str(job),
                "--observations",
                str(csv),
                "--output",
                str(report),
                "--cross-validate",
            ]
        )
        == 0
    )
    payload = json.loads(report.read_text())
    assert "profile likelihood" in payload["interval_method"]
    assert payload["estimates"]["mu_max_day"]["interval"]
    assert {r["split"] for r in payload["cross_validation"]["metrics"]} == {"in-sample", "held-out"}
    assert report.with_suffix(".held_out.csv").exists()
