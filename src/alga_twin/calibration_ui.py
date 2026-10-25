"""Profile-gated joint calibration workspace; full guided upload wizard is separate."""

import hashlib
import json
from io import BytesIO

import pandas as pd
import plotly.graph_objects as go

from .calibration import fit_joint, leave_one_run_out
from .calibration_io import load_job, synthetic_job


def render_joint_calibration():
    import streamlit as st

    st.markdown("### Joint calibration and whole-run holdouts")
    st.caption(
        "Every run shares the fitted parameters; each retains its supplied light, N and initial state."
    )
    st.warning(
        "This Streamlit workspace uses UNVERIFIED / DEMO model assumptions. No independent biological validation."
    )
    mode = st.radio("Joint input", ["SYNTHETIC worked example", "Upload configuration and CSV"])
    if mode.startswith("SYNTHETIC"):
        config, data = synthetic_job()
        raw_config = json.dumps(config, sort_keys=True).encode()
        raw_data = data.to_csv(index=False).encode()
    else:
        job = st.file_uploader("Explicit calibration job JSON", type=["json"], key="joint_config")
        csv = st.file_uploader("Long-form run observations CSV", type=["csv"], key="joint_data")
        st.caption(
            "CSV: run_id,time_day,observable,value,unit,replicate. Download the synthetic example for the JSON schema. "
            "Biological culture replicates require separate run ids; technical repeats retain distinct replicate ids."
        )
        if job is None or csv is None:
            st.info("Both files are required; no synthetic fallback is applied to a partial upload.")
            return
        raw_config, raw_data = job.getvalue(), csv.getvalue()
        if max(len(raw_config), len(raw_data)) > 2_000_000:
            st.error("Input exceeds 2 MB per file")
            return
        try:
            config = json.loads(raw_config)
            data = pd.read_csv(BytesIO(raw_data), dtype={"run_id": str, "replicate": str})
        except (ValueError, UnicodeError, pd.errors.ParserError) as exc:
            st.error(str(exc))
            return
    try:
        if len(data) > 5000:
            raise ValueError("Joint CSV exceeds 5000 measurement rows")
        runs, search, errors = load_job(config, data)
        if any(p.tier != "DEMO" or p.status != "UNVERIFIED" for r in runs for p in r.model.params.values()):
            raise ValueError(
                "This DEMO workspace requires UNVERIFIED/DEMO records. Explicit research configs use the Python/CLI API."
            )
    except (ValueError, TypeError, KeyError) as exc:
        st.error(str(exc))
        return
    signature = hashlib.sha256(raw_config + raw_data).hexdigest()
    st.dataframe(data, width="stretch", hide_index=True)
    st.dataframe(runs[0].model.provenance(), width="stretch", hide_index=True)
    st.caption(
        f"Error model: {errors.kind}; fixed SDs: {errors.scales}. Search bounds: {config['search']}. "
        "These are explicit assumptions, not literature ranges. Intervals are marginal 95% asymptotic profile intervals."
    )
    st.download_button(
        "Download job configuration", json.dumps(config, indent=2), "joint_job.json", "application/json"
    )
    st.download_button("Download observations", raw_data, "joint_observations.csv", "text/csv")
    if st.button("Fit shared parameters", key="joint_fit_button"):
        with st.spinner("Joint fit and nuisance-parameter profiles..."):
            try:
                st.session_state.joint_fit = (signature, fit_joint(runs, search, errors))
            except (ValueError, RuntimeError) as exc:
                st.error(str(exc))
    bundle = st.session_state.get("joint_fit")
    if bundle and bundle[0] == signature:
        result = bundle[1]
        st.dataframe(result.table(), width="stretch", hide_index=True)
        if result.supported:
            st.success("Selected parameters passed the conditional profile gate; this is in-sample evidence.")
        else:
            st.warning(
                "NOT IDENTIFIABLE or unresolved: unsupported point estimates/intervals are withheld. "
                "Your data may not separate growth rate from light absorption when both are fitted."
            )
        st.dataframe(result.metrics, width="stretch", hide_index=True)
        fig = go.Figure()
        for name, profile in result.profiles.groupby("parameter"):
            fig.add_trace(go.Scatter(x=profile.value, y=profile.delta_deviance, name=name))
        fig.add_hline(y=result.cutoff)
        fig.update_layout(
            xaxis_title="Parameter value (see units in table)", yaxis_title="Profile Δ(-2 log likelihood)"
        )
        st.plotly_chart(fig, width="stretch")
        st.download_button(
            "Download joint calibration evidence",
            json.dumps(result.report(), indent=2, allow_nan=False),
            "joint_calibration.json",
            "application/json",
        )
        st.download_button(
            "Download reoptimized profiles",
            result.profiles.to_csv(index=False),
            "joint_profiles.csv",
            "text/csv",
        )
    if st.button("Run leave-one-run-out", key="joint_cv_button"):
        with st.spinner("Refitting and profiling each training fold; held-out measurements are excluded..."):
            try:
                st.session_state.joint_cv = (signature, leave_one_run_out(runs, search, errors))
            except (ValueError, RuntimeError) as exc:
                st.error(str(exc))
    bundle = st.session_state.get("joint_cv")
    if bundle and bundle[0] == signature:
        cv = bundle[1]
        st.dataframe(cv.folds, width="stretch", hide_index=True)
        st.dataframe(cv.metrics, width="stretch", hide_index=True)
        st.caption(
            f"Method: {cv.method}. In-sample and held-out errors are labelled separately. "
            "Synthetic holdouts verify code behavior, not biological prediction accuracy."
        )
        st.download_button("Download fold status", cv.folds.to_csv(index=False), "cv_folds.csv", "text/csv")
        st.download_button(
            "Download separate training/held-out metrics",
            cv.metrics.to_csv(index=False),
            "cv_metrics.csv",
            "text/csv",
        )
