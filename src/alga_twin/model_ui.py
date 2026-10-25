"""Explicit synthetic sandbox for model selection; no research-preset fallback."""

import json
from dataclasses import asdict

import numpy as np
import plotly.graph_objects as go

from . import __version__
from .demo import demo_model_parameters
from .model import Conditions
from .models import DroopModel, MonodModel, simulate_model


def render_model_sandbox():
    import streamlit as st

    st.markdown("### Selectable model sandbox")
    st.warning("SYNTHETIC / UNVERIFIED: these assumptions are not C. minutissima values or reported ranges.")
    st.caption(
        "This page simulates models. Joint fitting/profiles are in the Joint calibration workspace. Supported model selection remains pending."
    )
    kind = st.selectbox("Nutrient model", ["Monod", "Droop"]).lower()
    light_choice = st.selectbox(
        "Light response", ["Monod saturation", "Haldane photoinhibition", "Han steady state"]
    )
    light = {"Monod saturation": "monod", "Haldane photoinhibition": "haldane", "Han steady state": "han"}[
        light_choice
    ]
    temperature = st.checkbox("Enable CTMI temperature factor", value=False)
    temperature_c = (
        st.number_input("Synthetic temperature (°C)", -20.0, 60.0, 25.0, 1.0) if temperature else None
    )
    diurnal = st.checkbox("Enable diurnal half-sine light", value=False)
    loss = st.number_input("Synthetic respiration/loss rate (day⁻¹)", 0.0, 5.0, 0.0, 0.01)
    incident = st.number_input("Synthetic incident/peak light (µmol/m²/s)", 0.0, 10000.0, 180.0, 10.0)
    nitrogen = st.number_input("Synthetic initial N (mg N/L)", 0.0, 1000.0, 70.0, 5.0)
    quota = (
        st.number_input("Synthetic initial quota (g N/g DW)", 0.03, 0.15, 0.09, 0.01)
        if kind == "droop"
        else None
    )
    params = demo_model_parameters(kind, light, temperature=temperature, diurnal=diurnal, loss_rate_day=loss)
    c = Conditions(nitrogen_initial_mg_L=nitrogen, incident_light_umol_m2_s=incident)
    model = (MonodModel if kind == "monod" else DroopModel)(
        params, c, light=light, temperature_c=temperature_c, diurnal=diurnal
    )
    initial = [c.biomass_initial_g_L, nitrogen] + ([quota] if kind == "droop" else [])
    result = simulate_model(model, np.linspace(0, 8, 161), initial)
    st.caption("X: g DW/L; N: mg elemental N/L; q: g N/g DW. Initial X=0.1 g DW/L is a synthetic fixture.")
    fig = go.Figure(go.Scatter(x=result.time_day, y=result.X, name="Dry biomass (g DW/L)"))
    fig.update_layout(xaxis_title="Time (day)", yaxis_title="Dry biomass (g DW/L)")
    st.plotly_chart(fig, width="stretch")
    st.dataframe(result, width="stretch", hide_index=True)
    error = np.max(np.abs(result.total_n_mg_L - result.total_n_mg_L.iloc[0]))
    st.metric("Maximum nitrogen ledger error (mg N/L)", f"{error:.3g}")
    st.caption(
        "Total N = dissolved + biomass-stored + removed N. Respiration/loss exports biomass-associated N; "
        "no dissolved recycling is assumed. Droop can grow on stored N after dissolved N is depleted. "
        "Han here is steady state, without dynamic photosystem states."
    )
    st.dataframe(model.provenance(), width="stretch", hide_index=True)
    st.download_button(
        "Download selected model trajectory", result.to_csv(index=False), "synthetic_model.csv", "text/csv"
    )
    report = {
        "software_version": __version__,
        "model_id": f"batch-{kind}-{light}-ctmi{temperature}-diurnal{diurnal}-v1",
        "status": "SYNTHETIC_UNVERIFIED",
        "species": "SYNTHETIC",
        "kind": kind,
        "light": light,
        "temperature_c": temperature_c,
        "diurnal": diurnal,
        "conditions": asdict(c),
        "states": model.states,
        "state_units": model.state_units,
        "initial_state": initial,
        "parameters": {name: asdict(p) for name, p in params.items()},
        "validation": "No independent biological validation",
    }
    st.download_button(
        "Download selected model provenance",
        json.dumps(report, indent=2),
        "synthetic_model_provenance.json",
        "application/json",
    )
