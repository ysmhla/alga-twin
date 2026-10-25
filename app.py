"""AlgaTwin Streamlit showcase; run with `streamlit run app.py`."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, replace
from io import BytesIO

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from alga_twin import __version__
from alga_twin.calibration import ErrorModel, FitParameter
from alga_twin.data import read_experiment_csv
from alga_twin.demo import demo_parameters, synthetic_experiment
from alga_twin.fitting import fit_experiment
from alga_twin.model import Conditions, conditions_for_observations, local_irradiance, simulate
from alga_twin.parameter_ui import render_parameter_gate
from alga_twin.parameters import provenance_rows
from alga_twin.planner import scenario_grid
from alga_twin.reporting import manifest, model_dataframe_to_csv
from alga_twin.trust import local_sensitivity, scenario_warnings

st.set_page_config(
    page_title="AlgaTwin | Microalgal Digital Twin",
    page_icon="🧫",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    """
<style>
    .block-container {max-width: 1320px; padding-top: 2rem; padding-bottom: 4rem;}
    h1, h2, h3 {letter-spacing: -.035em;}
    .hero {border: 1px solid rgba(100,160,160,.25); border-radius: 16px;
           padding: 25px 29px; background: linear-gradient(120deg,rgba(24,93,93,.16),rgba(40,88,135,.05));}
    .eyebrow {font-size: .72rem; letter-spacing: .16em; color: #43B59E; font-weight: 700;}
    .subtitle {color: #8fa2ab; font-size: 1.02rem; margin-top: .4rem;}
    div[data-testid="stMetric"] {border: 1px solid rgba(120,150,150,.23);border-radius: 12px;padding: 13px;}
    .tag {background: rgba(43,145,125,.15); border:1px solid rgba(43,145,125,.3);
          padding: 5px 9px; border-radius: 100px; font-size: .78rem;}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div class="hero">
 <span class="eyebrow">OPEN-SOURCE SCIENTIFIC SOFTWARE · v{__version__}</span>
 <h1 style="margin: 9px 0 4px 0;">AlgaTwin <span style="color:#42bba4">/</span> Virtual Photobioreactor</h1>
 <div class="subtitle">Data-calibrated microalgal growth simulations, light fields and virtual experiments.</div>
 <div style="margin-top: 17px;"><span class="tag">Batch · Single species</span>&nbsp;&nbsp;
 <span class="tag">Monod + Light</span>&nbsp;&nbsp;<span class="tag">Experimental demo</span></div>
</div>""",
    unsafe_allow_html=True,
)

workspace = st.selectbox(
    "Workspace",
    [
        "Baseline workflow",
        "Guided upload to report",
        "OD / cell count calibration",
        "Selectable models (SYNTHETIC)",
        "Joint calibration",
        "Model support and next experiment",
    ],
)
if workspace == "Guided upload to report":
    from alga_twin.wizard_ui import render_wizard

    render_wizard()
    st.stop()
if workspace == "OD / cell count calibration":
    from alga_twin.biomass_ui import render_biomass_calibration

    render_biomass_calibration()
    st.stop()

if workspace == "Model support and next experiment":
    from alga_twin.decision_ui import render_decisions

    render_decisions()
    st.stop()

render_parameter_gate()

if workspace == "Joint calibration":
    from alga_twin.calibration_ui import render_joint_calibration

    render_joint_calibration()
    st.stop()
if workspace == "Selectable models (SYNTHETIC)":
    from alga_twin.model_ui import render_model_sandbox

    render_model_sandbox()
    st.stop()

with st.sidebar:
    st.markdown("### 🧫 AlgaTwin")
    st.caption(f"v{__version__} · Research prototype · NOT independently validated")
    st.markdown("#### 01 / Experiment data")
    uploaded = st.file_uploader(
        "Upload experimental CSV",
        type=["csv"],
        help="One cultivation run; columns time_day, biomass_g_L and optional nitrate_n_mg_L. Maximum 2 MB.",
    )
    if uploaded is None:
        data = synthetic_experiment()
        source_tag = "SYNTHETIC demo data (seed 42)"
        raw_data = model_dataframe_to_csv(data)
    else:
        raw_data = uploaded.getvalue()
        if len(raw_data) > 2_000_000:
            st.error("CSV exceeds the 2 MB input limit")
            st.stop()
        try:
            headers = pd.read_csv(BytesIO(raw_data), nrows=0, encoding="utf-8-sig").columns.tolist()
        except (UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
            st.error(f"Cannot read CSV header: {exc}")
            st.stop()
        if not headers:
            st.error("Empty CSV header")
            st.stop()

        def guess(names, keywords, default=0):
            for idx, name in enumerate(names):
                if any(term in name.lower().replace(" ", "_") for term in keywords):
                    return idx
            return default

        with st.expander("Map your CSV columns", expanded=True):
            time_column = st.selectbox("Time / day", headers, index=guess(headers, ["time", "day"], 0))
            biomass_column = st.selectbox(
                "Dry biomass / g L⁻¹",
                headers,
                index=guess(headers, ["biomass", "dry", "dw_"], min(1, len(headers) - 1)),
            )
            n_columns = ["(not available)"] + headers
            nitrogen_column = st.selectbox(
                "Nitrate-N / mg N L⁻¹ (optional)",
                n_columns,
                index=guess(n_columns, ["nitrate", "nitrogen", "no3"], 0),
            )
        mapping = {"time_day": time_column, "biomass_g_L": biomass_column}
        if nitrogen_column != "(not available)":
            mapping["nitrate_n_mg_L"] = nitrogen_column
        try:
            data = read_experiment_csv(raw_data, column_map=mapping)
        except ValueError as exc:
            st.error(str(exc))
            st.stop()
        source_tag = f"Uploaded: {uploaded.name}"
    st.caption(source_tag)
    st.markdown("#### 02 / Calibration conditions")
    st.caption("Specify conditions used in your *measured* experiment, not desired future settings.")
    fit_light = st.number_input("Measured incident light (µmol/m²/s)", 0.0, 1200.0, 180.0, 10.0)
    fit_path_cm = st.number_input("Measured optical path (cm)", 0.5, 60.0, 5.0, 0.5)
    fit_n0 = st.number_input("Initial nitrate-N if not measured (mg N/L)", 0.0, 10000.0, 70.0, 5.0)
    with st.expander("Fixed biological assumptions"):
        st.caption(
            "UNVERIFIED synthetic assumptions; widget limits are numerical controls, not literature ranges."
        )
        k_n = st.number_input("Monod Kₙ (mg N/L)", 0.1, 100.0, 5.0, 0.5)
        k_i = st.number_input("Light Kᵢ (µmol/m²/s)", 1.0, 1000.0, 85.0, 5.0)
        optics = st.selectbox("Extinction law", ["Linear (s=1)", "Sublinear"], key="extinction_law")
        exponent = (
            1.0
            if optics.startswith("Linear")
            else st.number_input("Synthetic extinction exponent s", 0.01, 1.0, 0.5, 0.01)
        )
        st.caption(
            "a0 units: L^s / (g DW)^s / m. Changing s requires a new measured a0; "
            "DEMO reuses only a labelled hypothetical coefficient."
        )
        extinction = st.number_input("Extinction a0 (exponent-dependent units)", 0.0, 10000.0, 12.0, 1.0)
        background = st.number_input("Background attenuation (m⁻¹)", 0.0, 10000.0, 0.3, 0.1)
        fixed_yield = st.number_input("Initial/fixed biomass yield (g/g N)", 1.0, 25.0, 8.0, 0.5)
    with st.expander("Calibration likelihood assumptions"):
        st.caption("DEMO settings: noise SDs and search bounds are user assumptions, not literature ranges.")
        noise_kind = st.selectbox("Observation error model", ["additive", "log-normal"])
        sigma_x = st.number_input(
            "Fixed biomass SD (g DW/L; dimensionless for log-normal)", 0.00001, 10.0, 0.005, 0.001
        )
        sigma_n = st.number_input(
            "Fixed N SD (mg N/L; dimensionless for log-normal)", 0.00001, 1000.0, 1.0, 0.1
        )
        mu_low = st.number_input("µ search lower bound (day⁻¹)", 0.00001, 10.0, 0.01, 0.01)
        mu_high = st.number_input("µ search upper bound (day⁻¹)", 0.00001, 10.0, 3.0, 0.1)
        yield_low = st.number_input("Yield search lower bound (g DW/g N)", 0.00001, 1000.0, 1.0, 0.5)
        yield_high = st.number_input("Yield search upper bound (g DW/g N)", 0.00001, 1000.0, 25.0, 0.5)
    st.markdown("---")
    st.caption(
        "All calculations are local to this app session. Uploaded data are not intentionally stored on disk by the application."
    )

base_conditions = Conditions(
    biomass_initial_g_L=float(data.iloc[0]["biomass_g_L"]),
    nitrogen_initial_mg_L=float(fit_n0),
    incident_light_umol_m2_s=float(fit_light),
    optical_path_m=float(fit_path_cm / 100),
)
fixed_parameters = demo_parameters(
    k_n_mg_L=float(k_n),
    k_i_umol_m2_s=float(k_i),
    extinction_a0=float(extinction),
    biomass_yield_g_per_gN=float(fixed_yield),
    background_extinction_m_inv=float(background),
    extinction_exponent=float(exponent),
)
fit_signature = hashlib.sha256(
    raw_data
    + json.dumps(
        [
            asdict(base_conditions),
            asdict(fixed_parameters),
            noise_kind,
            sigma_x,
            sigma_n,
            mu_low,
            mu_high,
            yield_low,
            yield_high,
        ],
        sort_keys=True,
    ).encode()
).hexdigest()
existing_bundle = st.session_state.get("calibration")
active_fit = existing_bundle[1] if existing_bundle and existing_bundle[0] == fit_signature else None
active_p = active_fit.parameters if active_fit is not None and active_fit.success else fixed_parameters


def biomass_figure(curve: pd.DataFrame, observations: pd.DataFrame | None = None) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=curve.time_day,
            y=curve.biomass_g_L,
            mode="lines",
            name="Modelled biomass",
            line={"color": "#35b99b", "width": 3},
        )
    )
    if observations is not None:
        fig.add_trace(
            go.Scatter(
                x=observations.time_day,
                y=observations.biomass_g_L,
                mode="markers",
                name="Observations",
                marker={"color": "#efb864", "size": 8, "symbol": "circle-open", "line": {"width": 2}},
            )
        )
    fig.update_layout(
        xaxis_title="Time (days)",
        yaxis_title="Biomass (g dry weight/L)",
        margin={"l": 10, "r": 10, "t": 25, "b": 10},
        height=375,
        legend={"orientation": "h", "y": 1.13},
    )
    return fig


def nutrient_figure(curve: pd.DataFrame, observations: pd.DataFrame | None = None) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=curve.time_day,
            y=curve.nitrate_n_mg_L,
            mode="lines",
            name="Modelled nitrate-N",
            line={"color": "#6fa8e0", "width": 3},
        )
    )
    if observations is not None:
        masked = observations.dropna(subset=["nitrate_n_mg_L"])
        fig.add_trace(
            go.Scatter(
                x=masked.time_day,
                y=masked.nitrate_n_mg_L,
                mode="markers",
                name="N observations",
                marker={"color": "#efb864", "size": 8, "symbol": "circle-open", "line": {"width": 2}},
            )
        )
    fig.update_layout(
        xaxis_title="Time (days)",
        yaxis_title="Nitrate as N (mg N/L)",
        margin={"l": 10, "r": 10, "t": 25, "b": 10},
        height=360,
        legend={"orientation": "h", "y": 1.13},
    )
    return fig


calib_tab, twin_tab, light_tab, scenario_tab, trust_tab, planner_tab, methods_tab = st.tabs(
    [
        "📂 Data & SmartFit",
        "📈 Virtual Reactor",
        "☀️ LightScope",
        "🧪 ScenarioLab",
        "🛡️ TrustLens",
        "🎯 Planner",
        "📖 Methods & Export",
    ]
)

with calib_tab:
    st.markdown("### Calibration studio")
    if uploaded is None:
        st.info("**Synthetic data** are used. No fit result is independently validated.")
    else:
        st.info(
            "**User-uploaded data:** DEMO parameter assumptions remain UNVERIFIED. "
            "Check units and cultivation metadata before interpreting this fit."
        )
    c1, c2, c3 = st.columns(3)
    c1.metric("Biomass observations", len(data))
    c2.metric("Nitrate observations", int(data.nitrate_n_mg_L.notna().sum()))
    c3.metric("Experimental duration", f"{data.time_day.iloc[-1]:.1f} days")
    with st.expander("Review observations and CSV format", expanded=False):
        st.dataframe(data, width="stretch", hide_index=True)
        st.download_button(
            "Download sample experimental CSV" if uploaded is None else "Download normalized observations",
            model_dataframe_to_csv(data),
            "alga_twin_observations.csv",
            "text/csv",
        )
    st.caption(
        "Measured biomass (dry weight, g/L) and **nitrate as nitrogen** (mg N/L); optical path and irradiance are supplied in sidebar."
    )
    do_fit = st.button("⚙️ Fit supported parameters", type="primary", width="stretch")
    if do_fit:
        with st.spinner("Solving calibration trajectories..."):
            try:
                search = {
                    "mu_max_day": FitParameter(
                        mu_low, mu_high, float(np.clip(fixed_parameters.mu_max_day, mu_low, mu_high))
                    )
                }
                scales = {"X": (sigma_x, "g_DW/liter" if noise_kind == "additive" else "dimensionless")}
                if np.isfinite(data.nitrate_n_mg_L).sum() >= 3:
                    search["biomass_yield_g_per_gN"] = FitParameter(
                        yield_low, yield_high, float(np.clip(fixed_yield, yield_low, yield_high))
                    )
                    scales["N"] = (sigma_n, "mg_N/liter" if noise_kind == "additive" else "dimensionless")
                fit_result = fit_experiment(
                    data,
                    base_conditions,
                    fixed_parameters,
                    search=search,
                    errors=ErrorModel(noise_kind, scales),
                )
                st.session_state.calibration = (fit_signature, fit_result)
                active_fit = fit_result
                active_p = fit_result.parameters if fit_result.success else fixed_parameters
            except (ValueError, RuntimeError, FloatingPointError) as exc:
                st.error(f"Calibration failed: {exc}")
    if active_fit is not None:
        if active_fit.success:
            st.success(
                "Constrained calibration converged and selected profiles passed the conditional gate. "
                "These are **in-sample fit statistics**, not prediction validation."
            )
        else:
            st.warning(active_fit.message)
        if active_fit.success:
            p1, p2 = st.columns(2)
            p1.metric("Fitted µmax", f"{active_fit.parameters.mu_max_day:.3f} day⁻¹")
            p2.metric(
                "Fitted yield" if "biomass_yield_g_per_gN" in active_fit.fitted_names else "Fixed yield",
                f"{active_fit.parameters.biomass_yield_g_per_gN:.2f} g/g N",
            )
        st.metric("In-sample biomass RMSE", f"{active_fit.rmse_biomass_g_L:.4f} g/L")
        st.caption(
            f"Interval method: {active_fit.inference.report()['interval_method']}. "
            f"Confidence: {active_fit.inference.confidence:.0%}. "
            "Marginal intervals conditional on fixed inputs; empirical coverage is not established. "
            "NOT IDENTIFIABLE values are withheld."
        )
        st.dataframe(active_fit.inference.table(), width="stretch", hide_index=True)
        st.download_button(
            "Download calibration evidence",
            json.dumps(active_fit.inference.report(), indent=2, allow_nan=False),
            "calibration_evidence.json",
            "application/json",
        )
        p4, p5 = st.columns(2)
        with p4:
            st.plotly_chart(biomass_figure(active_fit.prediction, data), width="stretch")
        with p5:
            st.plotly_chart(nutrient_figure(active_fit.prediction, data), width="stretch")
        st.caption(
            "Only "
            + ", ".join(active_fit.fitted_names)
            + " fitted. Fixed constants, assumed measurement error scales and initial observations affect the estimates."
        )
        with st.expander("TrustLens: assumptions and limitations", expanded=True):
            for warning in active_fit.warnings:
                st.warning(warning, icon="⚠️")
    else:
        st.caption(
            "No active fit yet. Click the button to estimate permitted parameters; changing calibration inputs invalidates the existing fit."
        )
        st.plotly_chart(
            biomass_figure(
                simulate(
                    np.linspace(0, max(1, float(data.time_day.iloc[-1])), 121),
                    conditions_for_observations(data, base_conditions),
                    fixed_parameters,
                ),
                data,
            ),
            width="stretch",
        )

with twin_tab:
    st.markdown("### Virtual photobioreactor")
    st.caption("Explore scenarios using the active fitted parameters, or explicitly illustrative defaults.")
    st.info(
        "Using calibrated parameters from the current dataset"
        if active_fit is not None and active_fit.success
        else "Using illustrative default model parameters (NOT calibrated)"
    )
    a, b, c, d = st.columns(4)
    with a:
        light = st.slider("Light (µmol/m²/s)", 0, 700, int(np.clip(fit_light, 0, 700)), 10)
    with b:
        nitrogen = st.slider("Initial nitrate-N (mg/L)", 0, 300, int(min(300, fit_n0)), 5)
    with c:
        path_cm = st.slider("Optical path (cm)", 1, 25, int(np.clip(fit_path_cm, 1, 25)), 1)
    with d:
        days = st.slider("Cultivation length (days)", 2, 30, 12, 1)
    init_x = st.slider(
        "Inoculum biomass (g dry weight/L)",
        0.02,
        1.0,
        float(np.clip(data.iloc[0].biomass_g_L, 0.02, 1.0)),
        0.01,
    )
    current_conditions = Conditions(float(init_x), float(nitrogen), float(light), float(path_cm / 100))
    curve = simulate(np.linspace(0, days, days * 12 + 1), current_conditions, active_p)
    k1, k2, k3 = st.columns(3)
    k1.metric("Final predicted biomass", f"{curve.biomass_g_L.iloc[-1]:.3f} g/L")
    k2.metric(
        "Average volumetric productivity", f"{(curve.biomass_g_L.iloc[-1] - init_x) / days:.3f} g/L/day"
    )
    k3.metric("Final predicted nitrate-N", f"{curve.nitrate_n_mg_L.iloc[-1]:.1f} mg N/L")
    p1, p2 = st.columns(2)
    with p1:
        st.plotly_chart(biomass_figure(curve), width="stretch")
    with p2:
        st.plotly_chart(nutrient_figure(curve), width="stretch")
    st.download_button(
        "⬇️ Export simulated time series",
        model_dataframe_to_csv(curve),
        "alga_twin_simulation.csv",
        "text/csv",
    )

with light_tab:
    st.markdown("### LightScope / self-shading field")
    st.caption("Beer–Lambert attenuation across a 1-D effective optical path; not a spatial CFD model.")
    depth = np.linspace(0, current_conditions.optical_path_m, 60)
    subsampled = curve.iloc[:: max(1, len(curve) // 80)]
    field = np.vstack(
        [local_irradiance(depth, float(x), current_conditions, active_p) for x in subsampled.biomass_g_L]
    )
    fig = go.Figure(
        data=go.Heatmap(
            x=subsampled.time_day,
            y=depth * 100,
            z=field.T,
            colorscale="Viridis",
            colorbar={"title": "µmol/m²/s"},
        )
    )
    fig.update_layout(
        xaxis_title="Time (days)",
        yaxis_title="Depth from illuminated surface (cm)",
        height=475,
        margin={"l": 10, "r": 20, "t": 20, "b": 10},
    )
    st.plotly_chart(fig, width="stretch")
    col1, col2 = st.columns(2)
    col1.metric("Incident irradiance", f"{current_conditions.incident_light_umol_m2_s:.0f} µmol/m²/s")
    bottom = float(
        local_irradiance(
            np.array([current_conditions.optical_path_m]),
            float(curve.biomass_g_L.iloc[-1]),
            current_conditions,
            active_p,
        )[0]
    )
    col2.metric("Modelled terminal back-wall irradiance", f"{bottom:.1f} µmol/m²/s")
    st.caption(
        "Attenuation constants and well-mixed assumption may not transfer between reactor geometries or strains."
    )

with scenario_tab:
    st.markdown("### ScenarioLab / experiment comparisons")
    st.caption(
        "Store up to six virtual scenarios for comparison; stored only in your current browser session."
    )
    if "scenarios" not in st.session_state:
        st.session_state.scenarios = {}
    scenario_name = st.text_input("Scenario name", value="Scenario A", max_chars=40)
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("＋ Save current reactor settings", width="stretch"):
            if len(st.session_state.scenarios) >= 6 and scenario_name not in st.session_state.scenarios:
                st.warning("Maximum six scenarios")
            elif not scenario_name.strip():
                st.warning("Please name the scenario")
            else:
                st.session_state.scenarios[scenario_name.strip()] = (current_conditions, days, active_p)
                st.success(f"Saved {scenario_name.strip()}")
    with c2:
        if st.button("Clear saved scenarios", width="stretch"):
            st.session_state.scenarios = {}
            st.rerun()
    comparison = st.session_state.scenarios or {
        "Current conditions": (current_conditions, days, active_p),
        "Increased light (illustrative)": (
            replace(current_conditions, incident_light_umol_m2_s=min(light * 1.5, 900)),
            days,
            active_p,
        ),
    }
    compare_fig = go.Figure()
    rows = []
    exported = []
    for name, (c, duration, p_snapshot) in comparison.items():
        predicted = simulate(np.linspace(0, duration, duration * 12 + 1), c, p_snapshot)
        compare_fig.add_trace(
            go.Scatter(x=predicted.time_day, y=predicted.biomass_g_L, mode="lines", name=name)
        )
        rows.append(
            {
                "scenario": name,
                "incident_light": c.incident_light_umol_m2_s,
                "nitrogen_mg_L": c.nitrogen_initial_mg_L,
                "optical_path_cm": c.optical_path_m * 100,
                "final_biomass_g_L": round(float(predicted.biomass_g_L.iloc[-1]), 4),
                "model_mu_max_day": round(p_snapshot.mu_max_day, 4),
                "avg_productivity_g_L_day": round(
                    float((predicted.biomass_g_L.iloc[-1] - c.biomass_initial_g_L) / duration), 4
                ),
            }
        )
        exported.append(predicted.assign(scenario=name, model_mu_max_day=p_snapshot.mu_max_day))
    compare_fig.update_layout(
        xaxis_title="Days",
        yaxis_title="Biomass (g/L)",
        height=420,
        margin={"l": 10, "r": 10, "t": 25, "b": 10},
    )
    st.plotly_chart(compare_fig, width="stretch")
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.download_button(
        "Download comparison data",
        model_dataframe_to_csv(pd.concat(exported, ignore_index=True)),
        "alga_twin_comparison.csv",
        "text/csv",
    )
    st.warning(
        "Scenario ranking reflects stored modelling assumptions, not experimentally confirmed optimum conditions. Scenarios snapshot both conditions and parameters."
    )

with trust_tab:
    st.markdown("### TrustLens / model scrutiny")
    st.caption(
        "Local sensitivities and calibration-domain warnings, NOT formal prediction intervals or parameter confidence intervals."
    )
    observed_conditions = conditions_for_observations(data, base_conditions)
    for note in scenario_warnings(
        observed_conditions,
        current_conditions,
        calibrated=active_fit is not None and active_fit.success,
        scenario_days=float(days),
        observed_days=float(data.time_day.iloc[-1]),
    ):
        st.warning(note)
    sensitivities = local_sensitivity(current_conditions, active_p, days=float(days))
    sensitive_fig = go.Figure(
        go.Bar(
            x=sensitivities["parameter"],
            y=sensitivities["elasticity"],
            marker_color="#42bba4",
        )
    )
    sensitive_fig.update_layout(
        xaxis_title="Model parameter (one-at-a-time perturbation)",
        yaxis_title="Approximate final-biomass elasticity",
        height=375,
        margin={"l": 10, "r": 10, "t": 15, "b": 80},
    )
    st.plotly_chart(sensitive_fig, width="stretch")
    st.dataframe(sensitivities, width="stretch", hide_index=True)
    st.caption(
        "Computed by changing each positive parameter ±5% around the currently selected case, keeping others fixed. High sensitivity does not establish identifiability, reliability, or measurement precision."
    )
    if active_fit is not None:
        st.markdown("**In-sample calibration diagnostics**")
        st.metric("Biomass RMSE (training data)", f"{active_fit.rmse_biomass_g_L:.5f} g/L")
        if active_fit.rmse_nitrogen_mg_L is not None:
            st.metric("Nitrogen RMSE (training data)", f"{active_fit.rmse_nitrogen_mg_L:.3f} mg N/L")
        for w in active_fit.warnings:
            st.caption(f"⚠️ {w}")
    else:
        st.info("No active model fit. These diagnostics refer only to assumed default parameters.")

with planner_tab:
    st.markdown("### Exploratory experiment planner")
    st.caption(
        "Samples bounded light × nitrate scenarios, then highlights non-dominated candidates among those sampled. Not experimentally validated recommendations."
    )
    cp1, cp2, cp3 = st.columns(3)
    with cp1:
        max_light = st.slider("Light search upper bound (µmol/m²/s)", 50, 700, 350, 25)
    with cp2:
        max_nitrogen = st.slider("Nitrate-N upper bound (mg N/L)", 10, 300, 120, 10)
    with cp3:
        steps = st.slider("Grid resolution (points per axis)", 3, 10, 7, 1)
    design_signature = json.dumps(
        [asdict(current_conditions), asdict(active_p), days, max_light, max_nitrogen, steps], sort_keys=True
    )
    if st.button("🔎 Explore experimental conditions", width="stretch"):
        with st.spinner("Evaluating mechanistic scenarios..."):
            st.session_state.design = (
                design_signature,
                scenario_grid(
                    current_conditions,
                    active_p,
                    days=float(days),
                    max_light=float(max_light),
                    max_nitrogen=float(max_nitrogen),
                    steps=int(steps),
                ),
            )
    previous_design = st.session_state.get("design")
    if previous_design is not None and previous_design[0] == design_signature:
        grid = previous_design[1]
        front = grid[grid.sampled_pareto_candidate]
        st.metric("Scenarios simulated", len(grid))
        st.metric("Sampled non-dominated candidates", len(front))
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=grid.light_umol_m2_s,
                y=grid.final_biomass_g_L,
                mode="markers",
                name="Evaluated scenarios",
                marker={
                    "color": grid.initial_nitrogen_mg_L,
                    "colorscale": "Viridis",
                    "size": 8,
                    "colorbar": {"title": "Nitrate-N (mg/L)"},
                },
                text=[f"Nitrate-N {n:.1f} mg/L" for n in grid.initial_nitrogen_mg_L],
            )
        )
        fig.add_trace(
            go.Scatter(
                x=front.light_umol_m2_s,
                y=front.final_biomass_g_L,
                mode="markers",
                name="Non-dominated sample",
                marker={"symbol": "circle-open", "color": "#f0a65c", "size": 15, "line": {"width": 2}},
            )
        )
        fig.update_layout(
            xaxis_title="Incident light (µmol/m²/s)",
            yaxis_title="Predicted final dry biomass (g/L)",
            height=415,
        )
        st.plotly_chart(fig, width="stretch")
        st.dataframe(
            front.sort_values("final_biomass_g_L", ascending=False), width="stretch", hide_index=True
        )
        st.download_button(
            "Export sampled scenario grid",
            model_dataframe_to_csv(grid),
            "alga_twin_exploration.csv",
            "text/csv",
        )
        st.warning(
            "These are numerically non-dominated only within the selected discrete grid and assumed model; no cost, electricity, energy conversion, CO₂ or laboratory feasibility analysis is included."
        )
    else:
        st.info(
            "Select bounds and click Explore. Changing the reactor or assumptions invalidates previous exploration results."
        )

with methods_tab:
    st.markdown("### Scientific model and reproducibility")
    st.latex(r"\frac{dX}{dt}=(\mu_{max}\frac{N}{K_N+N}\overline{f_I}-k_d)X")
    st.latex(r"\frac{dN}{dt}=-\frac{1000\,\mu_g X}{Y_{X/N}}")
    st.latex(r"I(z)=I_0 \exp[-(a_1+a_0X^s)z],\quad\overline{f_I}=\frac{1}{L}\int_0^L\frac{I(z)}{K_I+I(z)}dz")
    st.markdown("""
**Current assumptions:** single-strain batch culture, time-constant surface irradiance, well-mixed biomass and external nitrogen, one-dimensional optical attenuation, no explicit CO₂ / temperature / pH / photoinhibition / feed control. Nitrogen is expressed as **mg elemental nitrogen per litre**. Yield is g biomass per g consumed nitrogen.

**Calibration:** only `mu_max_day` and, with at least three nitrogen observations, `biomass_yield_g_per_gN` are estimated. Other parameters remain fixed. Selected parameters receive reoptimized profiles;
only supported two-sided marginal asymptotic intervals/point estimates are shown.
These intervals condition on fixed parameters, initial states and specified noise SDs.
No independent validation is claimed.

**Scientific use:** educational and research prototyping; do not operate production reactors based solely on model outputs.
""")
    notes = (
        list(active_fit.warnings)
        if active_fit is not None
        else ["No calibration performed; all model parameter values are illustrative defaults."]
    )
    st.markdown("### Active parameter provenance")
    active_provenance = provenance_rows(active_p)
    st.dataframe(pd.DataFrame(active_provenance), width="stretch", hide_index=True)
    for row in active_provenance:
        if row["override_warning"]:
            st.warning(row["override_warning"])
    st.caption("No verified species ranges are available in this DEMO. No interval or range is invented.")
    report = manifest(
        active_p,
        current_conditions,
        data_csv=raw_data,
        mode="in-sample constrained fit"
        if active_fit is not None and active_fit.success
        else "unfitted illustrative model",
        notes=notes,
    )
    st.download_button(
        "📦 Download run manifest (JSON)", report, "alga_twin_run_manifest.json", "application/json"
    )
    with st.expander("Run manifest preview"):
        st.code(report, language="json")
    st.markdown(
        "**Next planned scientific milestones:** independent biological evaluation, interval coverage assessment, supported model selection and an information-based experiment recommender. Selectable models are available in the synthetic workspace."
    )
    st.caption(
        "Project documentation and full model specification are in the GitHub repository and docs/ directory."
    )
