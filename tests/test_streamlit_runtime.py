"""Exercise real Streamlit widget state and the main research workflow."""

from pathlib import Path

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
APP = Path(__file__).resolve().parents[1] / "app.py"


def test_real_streamlit_calibration_scenarios_and_planner():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not app.exception
    app.radio[0].set_value("DEMO — synthetic assumptions").run()
    assert not app.exception
    assert len(app.tabs) == 7
    initial_biomass = next(m.value for m in app.metric if m.label == "Final predicted biomass")

    app.slider[0].set_value(0).run()
    assert not app.exception
    dark_biomass = next(m.value for m in app.metric if m.label == "Final predicted biomass")
    assert float(dark_biomass.split()[0]) < float(initial_biomass.split()[0])
    assert dark_biomass == "0.100 g/L"

    app.slider[0].set_value(180).run()
    app.button[0].click().run()
    assert not app.exception
    fit = app.session_state["calibration"][1]
    assert fit.success and fit.rmse_biomass_g_L < 0.02
    provenance = next(frame.value for frame in app.dataframe if "basis" in frame.value.columns)
    row = provenance[provenance.parameter == "mu_max_day"].iloc[0]
    assert row.value == pytest.approx(fit.parameters.mu_max_day)
    assert row.status == "UNVERIFIED"
    assert any("Constrained calibration converged" in s.value for s in app.success)

    app.button[1].click().run()
    saved = app.session_state["scenarios"]["Scenario A"]
    assert saved[2] == fit.parameters

    next(w for w in app.number_input if w.label.startswith("Measured incident light")).set_value(250.0).run()
    assert not app.exception
    assert not any(m.label == "Fitted µmax" for m in app.metric)
    assert app.session_state["scenarios"]["Scenario A"] == saved

    app.slider[7].set_value(3).run()
    app.button[3].click().run()
    assert not app.exception
    assert len(app.session_state["design"][1]) == 9
    assert any(m.label == "Scenarios simulated" and m.value == "9" for m in app.metric)

    app.slider[0].set_value(200).run()
    assert not any(m.label == "Scenarios simulated" for m in app.metric)
    app.button[2].click().run()
    assert not app.exception
    assert app.session_state["scenarios"] == {}


def test_literature_landing_cannot_silently_run_demo():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not app.exception
    assert app.radio[0].value == "LITERATURE — C. minutissima"
    assert len(app.tabs) == 0
    assert not any(m.label == "Final predicted biomass" for m in app.metric)
    assert any("NO_SPECIES_DATA" in m.value for m in app.info)
    assert any("Measure extinction directly" in m.value for m in app.markdown)
    assert not any("converged" in m.value.lower() for m in app.success)


def test_sublinear_demo_renders_with_provenance():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.radio[0].set_value("DEMO — synthetic assumptions").run()
    next(w for w in app.selectbox if w.label == "Extinction law").set_value("Sublinear").run()
    assert not app.exception
    assert any(w.label == "Synthetic extinction exponent s" for w in app.number_input)
    assert any("UNVERIFIED" in w.value for w in app.warning)
    provenance = next(
        frame.value
        for frame in app.dataframe
        if "parameter" in frame.value.columns and "basis" in frame.value.columns
    )
    assert set(provenance.status) == {"UNVERIFIED"}
    assert set(provenance.tier) == {"DEMO"}


def test_selectable_model_sandbox_with_droop_han_ctmi_and_diurnal():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    app.radio[0].set_value("DEMO — synthetic assumptions").run()
    next(w for w in app.selectbox if w.label == "Workspace").set_value("Selectable models (SYNTHETIC)").run()
    assert not app.exception
    next(w for w in app.selectbox if w.label == "Nutrient model").set_value("Droop").run()
    next(w for w in app.selectbox if w.label == "Light response").set_value("Haldane photoinhibition").run()
    assert not app.exception
    next(w for w in app.checkbox if w.label == "Enable CTMI temperature factor").check().run()
    next(w for w in app.checkbox if w.label == "Enable diurnal half-sine light").check().run()
    next(w for w in app.number_input if w.label.startswith("Synthetic respiration")).set_value(0.1).run()
    assert not app.exception
    trajectory = next(frame.value for frame in app.dataframe if "total_n_mg_L" in frame.value.columns)
    assert "q" in trajectory and trajectory.removed_n_mg_L.iloc[-1] > 0
    assert trajectory.total_n_mg_L.max() - trajectory.total_n_mg_L.min() < 1e-6
    provenance = next(frame.value for frame in app.dataframe if "basis" in frame.value.columns)
    assert set(provenance.status) == {"UNVERIFIED"}
    assert set(provenance.species) == {"SYNTHETIC"}
    next(w for w in app.selectbox if w.label == "Light response").set_value("Han steady state").run()
    assert not app.exception
    provenance = next(frame.value for frame in app.dataframe if "basis" in frame.value.columns)
    assert "han_sigma" in set(provenance.parameter)
    assert any("selection" in m.value for m in app.caption)


def test_weak_data_ui_hides_fitted_point_estimates():
    app = AppTest.from_file(str(APP), default_timeout=120).run()
    app.radio[0].set_value("DEMO — synthetic assumptions").run()
    next(w for w in app.number_input if w.label.startswith("Fixed biomass SD")).set_value(10.0).run()
    next(w for w in app.number_input if w.label.startswith("Fixed N SD")).set_value(1000.0).run()
    next(w for w in app.button if "Fit supported parameters" in w.label).click().run()
    assert not app.exception
    fit = app.session_state["calibration"][1]
    assert not fit.success and fit.parameters is None
    assert not any(w.label in {"Fitted µmax", "Fitted yield"} for w in app.metric)
    assert any("withheld" in w.value for w in app.warning)


def test_joint_workspace_profiles_and_whole_run_cv():
    app = AppTest.from_file(str(APP), default_timeout=120).run()
    app.radio[0].set_value("DEMO — synthetic assumptions").run()
    next(w for w in app.selectbox if w.label == "Workspace").set_value("Joint calibration").run()
    assert not app.exception
    next(w for w in app.button if w.label == "Fit shared parameters").click().run()
    assert not app.exception
    result = app.session_state["joint_fit"][1]
    assert result.supported
    assert set(result.metrics.origin) == {"SYNTHETIC"}
    next(w for w in app.button if w.label == "Run leave-one-run-out").click().run()
    assert not app.exception
    cv = app.session_state["joint_cv"][1]
    assert set(cv.folds.status) == {"SCORED"}
    assert set(cv.metrics.split) == {"in-sample", "held-out"}
    next(w for w in app.radio if w.label == "Joint input").set_value("Upload configuration and CSV").run()
    assert not app.exception
    assert any("Both files are required" in w.value for w in app.info)
    assert not any("passed the conditional" in w.value for w in app.success)
