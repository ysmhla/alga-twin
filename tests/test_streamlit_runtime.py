"""Exercise real Streamlit widget state and the main research workflow."""
from pathlib import Path

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
APP = Path(__file__).resolve().parents[1] / "app.py"


def test_real_streamlit_calibration_scenarios_and_planner():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
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
    assert any("Constrained calibration converged" in s.value for s in app.success)

    app.button[1].click().run()
    saved = app.session_state["scenarios"]["Scenario A"]
    assert saved[2] == fit.parameters

    app.number_input[0].set_value(250.0).run()
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
