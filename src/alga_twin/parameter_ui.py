"""Research gate: missing species data must not silently fall back to demo values."""

from dataclasses import asdict
from io import BytesIO

import pandas as pd
import pint

from .extinction import fit_extinction
from .parameters import SPECIES, c_minutissima_preset


def render_parameter_gate() -> None:
    import streamlit as st

    mode = st.radio(
        "Parameter tier",
        ["LITERATURE — C. minutissima", "DEMO — synthetic assumptions"],
        key="parameter_tier",
    )
    if mode.startswith("DEMO"):
        st.warning(
            "DEMO: all biological/optical values are UNVERIFIED synthetic assumptions, not strain presets."
        )
        return
    st.markdown(f"### Species provenance: {SPECIES}")
    st.caption(
        "VERIFIED means transcribed from the identified source, not validated for your strain. "
        "Point values have no inferred range; different model parameters are not interchangeable."
    )
    rows = [{"parameter": name, **asdict(record)} for name, record in c_minutissima_preset().items()]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.info(
        "NO_SPECIES_DATA: Martínez Table 1 does not list C. minutissima. "
        "Extinction and carbon fraction remain unset. Measure extinction directly below."
    )
    st.warning(
        "A complete literature Monod parameter set is unavailable. Simulation and growth fitting "
        "are disabled in this tier; Haldane points cannot fill Monod parameter gaps. "
        "No verified ranges are established in the audited sources."
    )
    st.markdown("### Measure extinction directly")
    st.caption(
        "Upload your own measurements only. CSV columns: biomass, incident, transmitted, path. "
        "Include a medium blank (biomass=0), matched spectral/geometry conditions, and multiple "
        "dry biomass concentrations. OD and carbon mass are not dry biomass."
    )
    biomass_unit = st.selectbox("Measured dry-biomass unit", ["g_DW/liter", "g_DW/meter**3"])
    path_unit = st.selectbox("Measured optical-path unit", ["meter", "centimeter"])
    st.caption(
        "Both light readings must be photon flux density in micromole/m²/second, "
        "from the same calibrated spectral response. No automatic radiometric conversion."
    )
    kind = st.selectbox("Measured extinction model", ["Linear (s=1)", "Sublinear (fit s)"])
    uploaded = st.file_uploader("Upload extinction measurements CSV", type=["csv"], key="optical_csv")
    if uploaded is not None and st.button("Fit measured extinction", key="fit_optical"):
        try:
            raw = uploaded.getvalue()
            if len(raw) > 2_000_000:
                raise ValueError("CSV exceeds 2 MB")
            data = pd.read_csv(BytesIO(raw))
            if len(data) > 5000:
                raise ValueError("CSV exceeds 5000 rows")
            fit = fit_extinction(
                data,
                biomass_unit=biomass_unit,
                path_unit=path_unit,
                light_unit="micromole/meter**2/second",
                sublinear=kind.startswith("Sublinear"),
            )
            st.session_state.optical_result = fit
            st.session_state.optical_signature = (raw, biomass_unit, path_unit, kind)
        except (ValueError, RuntimeError, pint.errors.PintError) as exc:
            st.error(str(exc))
    signature = (uploaded.getvalue(), biomass_unit, path_unit, kind) if uploaded is not None else None
    if st.session_state.get("optical_signature") == signature and signature is not None:
        fit = st.session_state.optical_result
        st.dataframe(
            pd.DataFrame(
                [
                    {"parameter": name, **asdict(record)}
                    for name, record in (("a0", fit.a0), ("a1", fit.a1), ("s", fit.exponent))
                ]
            ),
            width="stretch",
            hide_index=True,
        )
        st.caption(
            f"Method: {fit.method}. R² (in-sample optical fit): {fit.r_squared:.5g}. "
            f"Measured biomass domain: {fit.biomass_domain_g_dw_L} g DW/L. "
            "No confidence interval estimated. No extrapolation or automatic literature promotion."
        )
        st.dataframe(fit.residuals, width="stretch", hide_index=True)
        st.download_button(
            "Download optical fit residuals",
            fit.residuals.to_csv(index=False),
            "measured_extinction_fit.csv",
            "text/csv",
        )
    st.stop()
