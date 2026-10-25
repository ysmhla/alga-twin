"""Paired OD/cell count to dry-weight calibration workspace."""

import hashlib
import json
from io import BytesIO

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .biomass_calibration import DW_FACTORS, SIGNAL_UNITS, fit_biomass_calibration
from .parameters import SPECIES


def synthetic_pairs():
    """Teaching relationship only; not a biological OD conversion factor."""
    x = np.linspace(0.1, 1.0, 8)
    return pd.DataFrame(
        {
            "signal": x,
            "dry_weight": 0.02 + 0.4 * x + np.array([0, 0.003, -0.002, 0.001, -0.001, 0.002, -0.003, 0]),
        }
    )


def render_biomass_calibration():
    import streamlit as st

    st.markdown("### OD / cell count to dry weight")
    st.write("Pair each proxy reading with an independently measured dry weight from the same sample.")
    st.info("This empirical conversion is separate from light extinction. It is not a species preset.")
    mode = st.radio(
        "Paired data", ["Upload my paired measurements", "SYNTHETIC teaching example"], key="dw_mode"
    )
    synthetic = mode.startswith("SYNTHETIC")
    if st.session_state.get("dw_mode_seen") != mode:
        st.session_state.pop("active_dw_calibration", None)
    st.session_state.dw_mode_seen = mode
    if synthetic:
        st.warning("SYNTHETIC / UNVERIFIED relationship; do not apply its coefficients to your culture.")
        raw = synthetic_pairs().to_csv(index=False).encode()
    else:
        uploaded = st.file_uploader("Paired measurements CSV", type=["csv"], key="dw_csv")
        st.caption("Include a proxy column and a dry-weight column. Missing pairs are refused, not imputed.")
        if uploaded is None:
            st.session_state.pop("active_dw_calibration", None)
            return
        raw = uploaded.getvalue()
    try:
        if len(raw) > 2_000_000:
            raise ValueError("Input exceeds 2 MB")
        data = pd.read_csv(BytesIO(raw))
        if not 1 <= len(data) <= 5000:
            raise ValueError("Use 1-5000 paired rows")
    except (ValueError, UnicodeError, pd.errors.ParserError) as exc:
        st.session_state.pop("active_dw_calibration", None)
        st.error(str(exc))
        return
    st.dataframe(data, width="stretch", hide_index=True)
    kind = st.selectbox("Proxy type", list(SIGNAL_UNITS), key="dw_kind")
    signal_column = st.selectbox("Proxy column", list(data.columns), key="dw_signal_col")
    dw_column = st.selectbox(
        "Dry-weight column", list(data.columns), index=min(1, len(data.columns) - 1), key="dw_value_col"
    )
    signal_unit = st.selectbox("Proxy unit", SIGNAL_UNITS[kind], key="dw_signal_unit")
    dw_unit = st.selectbox("Paired dry-weight unit", list(DW_FACTORS), key="dw_mass_unit")
    degree = st.radio("Conversion curve", ["Linear", "Quadratic"], horizontal=True, key="dw_degree")
    species = st.text_input(
        "Strain / species for this conversion",
        value="SYNTHETIC" if synthetic else SPECIES,
        key=f"dw_species_{synthetic}",
    )
    conditions = st.text_area(
        "Instrument and measurement conditions",
        value="SYNTHETIC teaching pairs; no instrument" if synthetic else "",
        help="For OD: wavelength, cuvette path, blank and dilution. For cell count: counting method/dilution. Include dry-weight method and culture conditions.",
        key=f"dw_conditions_{synthetic}",
    )
    signature = hashlib.sha256(
        raw
        + json.dumps(
            [signal_column, dw_column, kind, signal_unit, dw_unit, degree, species, conditions, synthetic]
        ).encode()
    ).hexdigest()
    stored = st.session_state.get("dw_fit")
    if not stored or stored[0] != signature:
        st.session_state.pop("active_dw_calibration", None)
    if st.button("Fit dry-weight conversion", key="dw_fit_button"):
        try:
            if signal_column == dw_column:
                raise ValueError("Proxy and dry weight must be different columns")
            fit = fit_biomass_calibration(
                pd.DataFrame({"signal": data[signal_column], "dry_weight": data[dw_column]}),
                kind=kind,
                signal_unit=signal_unit,
                dry_weight_unit=dw_unit,
                degree=1 if degree == "Linear" else 2,
                species=species,
                conditions=conditions,
                origin="SYNTHETIC" if synthetic else "MEASURED",
            )
            st.session_state.dw_fit = (signature, fit)
            st.session_state.active_dw_calibration = fit
        except (ValueError, TypeError, np.linalg.LinAlgError) as exc:
            st.error(str(exc))
    stored = st.session_state.get("dw_fit")
    if stored and stored[0] == signature:
        fit = stored[1]
        st.success(
            "Conversion fitted within the measured domain. It is available in the guided workflow for this session."
        )
        st.metric("R² (in-sample)", f"{fit.r_squared:.5f}")
        st.caption(
            f"{fit.method}. Domain: {fit.domain} {fit.canonical_signal_unit}. No extrapolation. Coefficient uncertainty is not propagated into growth fits."
        )
        fig = go.Figure()
        points = fit.residuals
        fig.add_scatter(
            x=points.signal_canonical, y=points.observed_g_DW_L, mode="markers", name="Paired measurements"
        )
        grid = np.linspace(*fit.domain, 100)
        fig.add_scatter(x=grid, y=fit.predict(grid, unit=fit.canonical_signal_unit), name="Fitted conversion")
        fig.update_layout(xaxis_title=fit.canonical_signal_unit, yaxis_title="Dry weight (g DW/L)")
        st.plotly_chart(fig, width="stretch")
        st.dataframe(points, width="stretch", hide_index=True)
        residual_fig = go.Figure(
            go.Scatter(x=points.signal_canonical, y=points.residual_g_DW_L, mode="markers")
        )
        residual_fig.add_hline(y=0)
        residual_fig.update_layout(
            xaxis_title=fit.canonical_signal_unit, yaxis_title="Observed - fitted (g DW/L)"
        )
        st.plotly_chart(residual_fig, width="stretch")
        value = st.number_input("Proxy value to convert", value=None, key="dw_predict")
        if value is not None:
            try:
                st.metric(
                    "Converted dry weight (g DW/L)", f"{float(fit.predict([value], unit=signal_unit)[0]):.6g}"
                )
            except ValueError as exc:
                st.error(str(exc))
        st.download_button(
            "Download conversion evidence",
            json.dumps(fit.report(), indent=2, allow_nan=False),
            "dry_weight_conversion.json",
            "application/json",
        )
        st.download_button(
            "Download conversion residuals",
            points.to_csv(index=False),
            "dry_weight_residuals.csv",
            "text/csv",
        )
