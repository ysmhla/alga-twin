"""Actual Streamlit state tests; these are not human usability observations."""

from io import BytesIO
from pathlib import Path

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
APP = Path(__file__).resolve().parents[1] / "app.py"


def widget(app, kind, label):
    return next(w for w in getattr(app, kind) if w.label == label)


def start():
    app = AppTest.from_file(str(APP), default_timeout=120).run()
    widget(app, "selectbox", "Workspace").set_value("Guided upload to report").run()
    assert not app.exception
    return app


def synthetic_to_model(app):
    widget(app, "radio", "Guided input").set_value("SYNTHETIC worked example").run()
    widget(app, "button", "Continue to column mapping").click().run()
    widget(app, "button", "Apply mapping and conversions").click().run()
    assert not app.exception
    widget(
        app, "checkbox", "I confirm the units, culture/technical replicate ids, and times from inoculation"
    ).check().run()
    widget(app, "button", "Continue to model").click().run()
    assert not app.exception


def test_guided_synthetic_fit_report_and_back_navigation_invalidation():
    app = start()
    assert widget(app, "radio", "Guided input").value == "Upload my measurements"
    synthetic_to_model(app)
    widget(app, "button", "Confirm model and all explicit assumptions").click().run()
    assert not app.exception
    assert app.session_state["guide_job"]["kind"] == "monod"
    assert widget(app, "button", "Read result and export report").disabled
    widget(app, "button", "Fit and check identifiability").click().run()
    assert not app.exception
    assert app.session_state["guide_fit"][1].supported
    assert not widget(app, "button", "Read result and export report").disabled
    widget(app, "button", "Read result and export report").click().run()
    assert not app.exception
    assert any("Download PDF report" == w.label for w in app.get("download_button"))
    assert any(
        "Interval method: Reoptimized profile likelihood" in w.value and "Confidence: 95%" in w.value
        for w in app.caption
    )
    assert any("Held-out error not computed" in w.value for w in app.warning)
    widget(app, "selectbox", "Current step").set_value("4 Choose model").run()
    widget(app, "selectbox", "Current step").set_value("6 Read result / report").run()
    assert not app.exception
    assert any("Complete Step 4" in w.value for w in app.info)
    assert not any(w.label == "Download PDF report" for w in app.get("download_button"))
    widget(app, "selectbox", "Current step").set_value("1 Upload").run()
    widget(app, "radio", "Guided input").set_value("Upload my measurements").run()
    widget(app, "selectbox", "Current step").set_value("6 Read result / report").run()
    assert any("Start with Step 1" in w.value for w in app.info)


def test_measured_wizard_never_inserts_synthetic_biological_values():
    app = start()
    synthetic_to_model(app)
    # Exercise the same measured form as an upload without pretending this fixture is real data.
    digest, _ = app.session_state["guide_source"]
    app.session_state["guide_source"] = (digest, False)
    app.run()
    widget(app, "radio", "Species / strain").set_value("I don't know my strain").run()
    frames = [w.value for w in app.dataframe if "parameter" in w.value.columns and "basis" in w.value.columns]
    assert frames and frames[0].loc[frames[0].parameter.ne("extinction_exponent"), "value"].isna().all()
    widget(app, "button", "Confirm model and all explicit assumptions").click().run()
    assert not app.exception
    assert any("incomplete or inconsistent" in w.value for w in app.error)
    assert any("No executable VERIFIED-range preset" in w.value for w in app.info)
    assert "guide_job" not in app.session_state


def test_proxy_workspace_fit_residuals_and_extrapolation_refusal():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    widget(app, "selectbox", "Workspace").set_value("OD / cell count calibration").run()
    assert widget(app, "radio", "Paired data").value == "Upload my paired measurements"
    widget(app, "radio", "Paired data").set_value("SYNTHETIC teaching example").run()
    widget(app, "button", "Fit dry-weight conversion").click().run()
    assert not app.exception
    assert app.session_state["active_dw_calibration"].origin == "SYNTHETIC"
    assert any(w.label == "R² (in-sample)" for w in app.metric)
    widget(app, "number_input", "Proxy value to convert").set_value(1.1).run()
    assert not app.exception
    assert any("Extrapolation refused" in w.value for w in app.error)
    assert not any(w.label.startswith("Converted dry weight") for w in app.metric)
    widget(app, "radio", "Conversion curve").set_value("Quadratic").run()
    assert "active_dw_calibration" not in app.session_state


def test_new_user_lands_on_empty_upload_without_demo_fallback():
    app = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not app.exception
    assert widget(app, "selectbox", "Workspace").value == "Guided upload to report"
    assert widget(app, "radio", "Guided input").value == "Upload my measurements"
    assert widget(app, "radio", "Uploaded data origin").value.startswith("MEASURED")
    assert "guide_source" not in app.session_state
    assert any(w.label == "Download blank CSV template" for w in app.get("download_button"))
    assert not any(w.label == "Download PDF report" for w in app.get("download_button"))


@pytest.mark.parametrize("reset", ["origin", "native_remove", "explicit_clear"])
def test_uploaded_synthetic_origin_and_file_removal_invalidate_results(monkeypatch, reset):
    from alga_twin.wizard_ui import _worked_wide

    _, raw = _worked_wide()
    current_upload = [BytesIO(raw)]
    monkeypatch.setattr(
        "streamlit.file_uploader",
        lambda *a, **kw: current_upload[0] if kw.get("key") == "guide_upload_0" else None,
    )
    app = AppTest.from_file(str(APP), default_timeout=120).run()
    assert app.session_state["guide_source"][1] is False
    widget(app, "radio", "Uploaded data origin").set_value("SYNTHETIC — simulated teaching data").run()
    assert app.session_state["guide_source"][1] is True
    widget(app, "button", "Continue to column mapping").click().run()
    widget(app, "button", "Apply mapping and conversions").click().run()
    widget(
        app, "checkbox", "I confirm the units, culture/technical replicate ids, and times from inoculation"
    ).check().run()
    widget(app, "button", "Continue to model").click().run()
    widget(app, "button", "Confirm model and all explicit assumptions").click().run()
    assert not app.exception
    config = app.session_state["guide_job"]
    assert {r["origin"] for r in config["runs"]} == {"SYNTHETIC"}
    assert {p["tier"] for p in config["parameters"].values()} == {"DEMO"}
    widget(app, "button", "Fit and check identifiability").click().run()
    assert not app.exception
    assert app.session_state["guide_fit"][1].supported
    widget(app, "selectbox", "Current step").set_value("1 Upload").run()
    assert widget(app, "radio", "Uploaded data origin").value.startswith("SYNTHETIC")
    assert any("Active CSV:" in w.value for w in app.caption)
    if reset == "origin":
        # The same bytes relabelled measured cannot reuse a synthetic fit/configuration.
        widget(app, "radio", "Uploaded data origin").set_value("MEASURED — laboratory observations").run()
        assert app.session_state["guide_source"][1] is False
        assert "guide_fit" not in app.session_state and "guide_job" not in app.session_state
        current_upload[0] = None
        app.run()
    elif reset == "native_remove":
        current_upload[0] = None
        app.run()
    else:
        widget(app, "button", "Remove current CSV and results").click().run()
        assert app.session_state["guide_upload_generation"] == 1
    assert "guide_source" not in app.session_state
    assert "guide_fit" not in app.session_state and "guide_job" not in app.session_state
    assert "guide_observations" not in app.session_state
    widget(app, "selectbox", "Current step").set_value("6 Read result / report").run()
    assert any("Start with Step 1" in w.value for w in app.info)
    assert not any(w.label == "Download PDF report" for w in app.get("download_button"))
