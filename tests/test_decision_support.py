"""SYNTHETIC / UNVERIFIED numerical decision checks, not species validation."""

import json
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from alga_twin.calibration import CalibrationRun, ErrorModel, FitParameter, fit_joint
from alga_twin.decision_io import load_experiments, load_selection, synthetic_decision_problem
from alga_twin.demo import demo_model_parameters
from alga_twin.experiment_design import ExperimentCandidate, candidate_prediction, rank_experiments
from alga_twin.model import Conditions
from alga_twin.model_selection import ModelCandidate, compare_models
from alga_twin.models import MonodModel, simulate_model


@pytest.fixture(scope="module")
def exponential_fit():
    # Transparent, nutrient-saturated limit; constant light factor is known.
    params = demo_model_parameters(extinction_a0=0, background_extinction_m_inv=0, k_n_mg_L=1e-9)
    conditions = Conditions(0.06, 1000.0, 100.0, 0.05)
    model = MonodModel(params, conditions)
    t = np.array([0.0, 0.5, 1.0, 1.5, 2.0])
    factor = 100 / (85 + 100)
    data = pd.DataFrame(
        {
            "time_day": t,
            "observable": "X",
            "value": 0.06 * np.exp(0.9 * factor * t),
            "unit": "g_DW/liter",
            "replicate": "one",
        }
    )
    run = CalibrationRun("limit", model, (0.06, 1000.0), data, "SYNTHETIC")
    errors = ErrorModel("log-normal", {"X": (0.02, "dimensionless")})
    result = fit_joint([run], {"mu_max_day": FitParameter(0.3, 1.8, 0.7)}, errors, profile_points=5)
    assert result.supported, result.table().to_string()
    return run, result


def proposals(run, errors):
    return [
        ExperimentCandidate(
            name,
            replace(run.model.conditions, incident_light_umol_m2_s=light),
            run.initial_state,
            2.0,
            (0.5, 1.0, 1.5, 2.0),
            ("X",),
            errors,
            None,
        )
        for name, light in [("dark", 0.0), ("low", 10.0), ("high", 1000.0)]
    ]


def test_known_best_experiment_matches_independent_exponential_information(exponential_fit):
    run, fit = exponential_fit
    candidates = proposals(run, fit.error_model)
    ranking = rank_experiments([run], fit, candidates)
    assert ranking.top3.candidate.tolist() == ["high", "low", "dark"]
    mu = fit.values()["mu_max_day"]
    dmu_dz = mu * np.log(1.8 / 0.3)
    times = np.array([0.5, 1.0, 1.5, 2.0])
    for c in candidates:
        light = c.conditions.incident_light_umol_m2_s
        analytic = np.sum((times * light / (85 + light) * dmu_dz / 0.02) ** 2)
        assert ranking.information_candidates[c.name][0, 0] == pytest.approx(analytic, rel=2e-5, abs=1e-10)
    assert ranking.ranking.iloc[-1].log_det_information_gain == pytest.approx(0, abs=1e-10)
    assert "not intervals" in ranking.report()["scope"]
    json.dumps(ranking.report(), allow_nan=False)


@pytest.mark.parametrize("kind", ["additive", "log-normal"])
def test_proposed_trajectory_units_conservation_and_replicate_information(exponential_fit, kind):
    run, original = exponential_fit
    errors = ErrorModel(kind, {"X": (0.003, "g_DW/liter")}) if kind == "additive" else original.error_model
    fit = original if kind == "log-normal" else fit_joint([run], original.search, errors, profile_points=5)
    c = proposals(run, errors)[1]
    once = rank_experiments([run], fit, [c])
    twice = rank_experiments([run], fit, [replace(c, technical_replicates=2)])
    np.testing.assert_allclose(
        twice.information_candidates[c.name], 2 * once.information_candidates[c.name], rtol=1e-10
    )
    _, curve = candidate_prediction(run.model, c, fit.values())
    assert curve.N.diff().dropna().max() <= 1e-8
    assert (curve[["X", "N"]] >= 0).all().all()
    np.testing.assert_allclose(curve.total_n_mg_L, run.model.retained_nitrogen(run.initial_state), atol=2e-6)
    assert twice.ranking.iloc[0].scalar_measurements == 8
    assert twice.ranking.iloc[0].log_det_information_gain > once.ranking.iloc[0].log_det_information_gain


def test_information_gain_invariant_to_parameter_coordinate(exponential_fit):
    run, logfit = exponential_fit
    linearfit = fit_joint(
        [run], {"mu_max_day": FitParameter(0.3, 1.8, 0.7, "linear")}, logfit.error_model, profile_points=5
    )
    candidates = proposals(run, logfit.error_model)
    a = rank_experiments([run], logfit, candidates)
    b = rank_experiments([run], linearfit, candidates)
    np.testing.assert_allclose(
        a.ranking.log_det_information_gain, b.ranking.log_det_information_gain, rtol=2e-5, atol=1e-8
    )


def test_unsupported_and_stale_fits_refused(exponential_fit):
    run, fit = exponential_fit
    candidates = proposals(run, fit.error_model)
    unsupported = replace(
        fit,
        estimates={
            n: replace(e, value=None, interval=None, status="NOT IDENTIFIABLE")
            for n, e in fit.estimates.items()
        },
    )
    with pytest.raises(ValueError, match="refusing"):
        rank_experiments([run], unsupported, candidates)
    changed = run.observations.copy()
    changed.loc[1, "value"] *= 1.1
    with pytest.raises(ValueError, match="Stale/mismatched"):
        rank_experiments([replace(run, observations=changed)], fit, candidates)
    wrong_noise = replace(fit, error_model=ErrorModel("log-normal", {"X": (0.1, "dimensionless")}))
    with pytest.raises(ValueError, match="Stale fit"):
        rank_experiments([run], wrong_noise, candidates)


def test_invalid_designs_units_and_log_zero_refused(exponential_fit):
    run, fit = exponential_fit
    candidate = proposals(run, fit.error_model)[0]
    for change in [
        {"sampling_times_day": (1.0, 1.0)},
        {"duration_day": 0},
        {"technical_replicates": 0},
        {"sampling_times_day": (3.0,)},
        {"observables": ("X", "X")},
    ]:
        with pytest.raises(ValueError):
            replace(candidate, **change)
    with pytest.raises(ValueError, match="units"):
        rank_experiments(
            [run], fit, [replace(candidate, errors=ErrorModel("additive", {"X": (1, "g_C/liter")}))]
        )
    with pytest.raises(ValueError, match="initial X/N"):
        rank_experiments([run], fit, [replace(candidate, initial_state=(0.06, 500.0))])
    zero_n = replace(
        candidate,
        conditions=replace(candidate.conditions, nitrogen_initial_mg_L=0),
        initial_state=(0.06, 0.0),
        observables=("N",),
        errors=ErrorModel("log-normal", {"N": (0.1, "dimensionless")}),
    )
    with pytest.raises(ValueError, match="positive predictions"):
        rank_experiments([run], fit, [zero_n])
    with pytest.raises(ValueError, match="numerical"):
        rank_experiments([run], fit, [candidate], step=0)


@pytest.fixture(scope="module")
def comparison():
    config, data, _ = synthetic_decision_problem()
    candidates, errors = load_selection(config, data)
    result = compare_models(candidates, errors, **config["decision"], profile_points=5)
    return config, data, candidates, errors, result


def test_same_data_comparison_recommends_supported_monod_and_counts_likelihood(comparison):
    _config, data, _candidates, _errors, result = comparison
    assert result.status == "RECOMMENDED", result.table.to_string()
    assert result.recommendation == "monod + monod light"
    row = result.table.set_index("model").loc[result.recommendation]
    fit = result.fits[result.recommendation]
    assert row.n == len(data) and row.k == 1
    assert row.aic == pytest.approx(2 * fit.nll + 2)
    assert row.bic == pytest.approx(2 * fit.nll + np.log(len(data)))
    assert not (result.table.status == "INCOMPLETE").any()
    assert "held-out error not computed" in result.report()["scope"]
    json.dumps(result.report(), allow_nan=False)


def test_true_photoinhibition_is_selected(comparison):
    config, _data, candidates, errors, _ = comparison
    haldane = candidates[1]
    generated = []
    for run in haldane.runs:
        curve = simulate_model(run.model, np.unique(run.observations.time_day), run.initial_state)
        obs = run.observations.copy()
        obs["value"] = [
            curve.set_index("time_day").loc[t, state]
            for t, state in zip(obs.time_day, obs.observable, strict=True)
        ]
        obs["run_id"] = run.run_id
        generated.append(obs)
    alternate, errors = load_selection(config, pd.concat(generated, ignore_index=True))
    result = compare_models(alternate[:2], errors, **config["decision"], profile_points=5)
    assert result.recommendation == "monod + haldane light", result.table.to_string()
    assert result.table.set_index("model").loc["monod + monod light", "status"] == "LACK OF FIT"


def test_no_support_with_dark_flat_data_and_too_few_points(exponential_fit):
    run, fit = exponential_fit
    dark_model = MonodModel(dict(run.model.params), replace(run.model.conditions, incident_light_umol_m2_s=0))
    data = run.observations.copy()
    data["value"] = 0.06
    dark = replace(run, model=dark_model, observations=data)
    candidates = [ModelCandidate(n, (dark,), fit.search) for n in ("a", "b")]
    result = compare_models(
        candidates, fit.error_model, delta_aic=0, delta_bic=0, adequacy_alpha=0.01, profile_points=5
    )
    assert result.status == "NO SUPPORTABLE MODEL" and result.recommendation is None
    assert set(result.table.status) == {"NOT IDENTIFIABLE"}
    assert result.table.aic.isna().all()
    sparse = replace(run, observations=run.observations.iloc[:2])
    result = compare_models(
        [ModelCandidate(n, (sparse,), fit.search) for n in ("a", "b")],
        fit.error_model,
        delta_aic=0,
        delta_bic=0,
        adequacy_alpha=0.01,
        profile_points=5,
    )
    assert result.status == "NO SUPPORTABLE MODEL"
    assert set(result.table.status) == {"INSUFFICIENT DATA"}


def test_incomparable_data_or_error_models_refused(comparison):
    config, data, candidates, errors, _ = comparison
    first, second = candidates[:2]
    changed = second.runs[0].observations.copy()
    changed.loc[0, "value"] += 0.001
    other = replace(second, runs=(replace(second.runs[0], observations=changed), *second.runs[1:]))
    with pytest.raises(ValueError, match="same observations"):
        compare_models([first, other], errors, delta_aic=0, delta_bic=0, adequacy_alpha=0.01)
    broken = json.loads(json.dumps(config))
    broken["candidates"][1]["job"]["error_model"]["scales"]["X"][0] *= 2
    with pytest.raises(ValueError, match="same fixed error"):
        load_selection(broken, data)
    with pytest.raises(ValueError, match="condition"):
        load_experiments([{"name": "incomplete"}])


def test_failed_fit_prevents_a_model_winner(exponential_fit):
    run, fit = exponential_fit
    result = compare_models(
        [ModelCandidate(n, (run,), fit.search) for n in ("a", "b")],
        fit.error_model,
        delta_aic=0,
        delta_bic=0,
        adequacy_alpha=0.01,
        max_nfev=1,
        profile_points=5,
    )
    assert result.status == "INCOMPLETE" and result.recommendation is None


def test_ui_upload_default_and_synthetic_top_three():
    AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
    from pathlib import Path

    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=120).run()

    def widget(kind, label):
        return next(w for w in getattr(app, kind) if w.label == label)

    widget("selectbox", "Workspace").set_value("Model support and next experiment").run()
    assert not app.exception
    assert widget("radio", "Decision input").value == "Upload explicit problems"
    widget("radio", "Decision input").set_value("SYNTHETIC worked example").run()
    widget("button", "Compare models and check support").click().run()
    assert not app.exception
    assert app.session_state["decision_comparison"][1].recommendation == "monod + monod light"
    widget("button", "Rank next experiments").click().run()
    assert not app.exception
    assert len(app.session_state["decision_ranking"][1].top3) == 3
    assert any("these are not confidence intervals" in c.value for c in app.caption)
    widget("text_area", "Proposed experiments JSON").set_value("[]").run()
    assert not any(w.label == "Download experiment ranking evidence" for w in app.get("download_button"))
