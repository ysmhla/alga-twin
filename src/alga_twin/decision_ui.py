"""User-facing conditional model comparison and experiment recommendation."""

import hashlib
import json
from io import BytesIO

import pandas as pd

from .decision_io import load_experiments, load_selection, synthetic_decision_problem
from .experiment_design import rank_experiments
from .model_selection import compare_models


def render_decisions():
    import streamlit as st

    st.subheader("Choose a supported model and plan the next experiment")
    st.warning(
        "No independent biological validation. Missing C. minutissima parameters still require measurements; no species values are filled in here."
    )
    example, example_data, example_experiments = synthetic_decision_problem()
    with st.expander("Explicit JSON schemas — SYNTHETIC teaching templates"):
        st.download_button(
            "Download model comparison template",
            json.dumps(example, indent=2),
            "SYNTHETIC_model_comparison.json",
            "application/json",
        )
        st.download_button(
            "Download comparison observations",
            example_data.to_csv(index=False),
            "SYNTHETIC_comparison.csv",
            "text/csv",
        )
        st.download_button(
            "Download experiment template",
            json.dumps(example_experiments, indent=2),
            "SYNTHETIC_experiments.json",
            "application/json",
        )
    mode = st.radio("Decision input", ["Upload explicit problems", "SYNTHETIC worked example"])
    if mode.startswith("Upload"):
        job = st.file_uploader("Model comparison JSON", type="json", key="decision_job")
        csv = st.file_uploader("Common observations CSV", type="csv", key="decision_csv")
        if job is None or csv is None:
            st.info(
                "Supply complete model problems and one common observation table. Partial uploads have no fallback."
            )
            return
        if max(job.size, csv.size) > 2_000_000:
            st.error("Maximum 2 MB per input")
            return
        try:
            config = json.loads(job.getvalue())
            data = pd.read_csv(BytesIO(csv.getvalue()), dtype={"run_id": str, "replicate": str})
        except (ValueError, UnicodeError) as exc:
            st.error(str(exc))
            return
    else:
        st.warning(
            "SYNTHETIC / UNVERIFIED / DEMO. All biological values, fixed SDs and decision thresholds are teaching assumptions."
        )
        config, data = example, example_data
    try:
        candidates, errors = load_selection(config, data)
        if len(data) > 500 or not 2 <= len(candidates) <= 6 or any(len(c.search) > 3 for c in candidates):
            raise ValueError(
                "Interactive limit: 500 rows, 2–6 models and at most 3 fitted parameters per model; use the Python API for larger jobs"
            )
    except (ValueError, TypeError, KeyError) as exc:
        st.error(str(exc))
        return
    st.caption(
        "AIC/BIC use the same observations and fixed noise. Profile gates withhold unsupported estimates. The residual screen is an approximate chi-square test, not validation. Fixed initial quota, noise and other parameters remain conditional assumptions."
    )
    with st.expander("Review data, provenance and decision assumptions"):
        st.dataframe(data, hide_index=True, width="stretch")
        st.json(config)
    signature = hashlib.sha256(
        json.dumps(config, sort_keys=True).encode() + data.to_csv(index=False).encode()
    ).hexdigest()
    if st.button("Compare models and check support"):
        with st.spinner("Fitting every candidate and reoptimizing parameter profiles..."):
            try:
                result = compare_models(candidates, errors, **config["decision"])
                st.session_state.decision_comparison = (signature, result)
            except (ValueError, RuntimeError) as exc:
                st.error(str(exc))
    bundle = st.session_state.get("decision_comparison")
    if not bundle or bundle[0] != signature:
        return
    result = bundle[1]
    st.dataframe(result.table, hide_index=True, width="stretch")
    if result.recommendation:
        st.success(f"Conditional recommendation: {result.recommendation}. {result.reason}")
    else:
        st.warning(f"{result.status}: {result.reason}")
    st.info(
        "Held-out error has not been computed by this comparison. Use whole-run cross-validation to test out-of-sample predictions."
    )
    st.download_button(
        "Download model support evidence",
        json.dumps(result.report(), indent=2, allow_nan=False),
        "model_support.json",
        "application/json",
    )
    eligible = result.table[result.table.status == "ELIGIBLE"].model.tolist()
    if result.status == "INCOMPLETE" or not eligible:
        return
    selected = st.selectbox(
        "Model for local experiment planning",
        eligible,
        index=eligible.index(result.recommendation) if result.recommendation in eligible else 0,
    )
    chosen = next(c for c in candidates if c.name == selected)
    fit = result.fits[selected]
    with st.expander("Selected fit and named profile intervals"):
        st.caption(f"Interval method: {fit.report()['interval_method']}. Confidence: {fit.confidence:.0%}.")
        st.dataframe(fit.table(), hide_index=True, width="stretch")
    st.subheader("Rank feasible next experiments")
    st.caption(
        "Specify light, initial N, duration, sampling days, observables and assay SDs. Confirm these choices are practical in your reactor. Rankings use absolute information gain; unequal budgets are not cost-normalized. A flat/unresolved current profile cannot be used for this local calculation."
    )
    raw = st.text_area(
        "Proposed experiments JSON",
        value=json.dumps(example_experiments, indent=2)
        if mode.startswith("SYNTHETIC") and chosen.runs[0].model.kind == "monod"
        else "[]",
        height=250,
        key=f"decision_experiments_{signature}_{selected}",
    )
    design_signature = hashlib.sha256((signature + selected + raw).encode()).hexdigest()
    if st.button("Rank next experiments"):
        with st.spinner("Checking sensitivities and expected information..."):
            try:
                proposals = load_experiments(json.loads(raw))
                if not 1 <= len(proposals) <= 12 or any(
                    len(c.sampling_times_day) * c.technical_replicates > 100 for c in proposals
                ):
                    raise ValueError(
                        "Interactive limit: 1–12 experiments, at most 100 time/replicate pairs each"
                    )
                design = rank_experiments(chosen.runs, fit, proposals)
                st.session_state.decision_ranking = (design_signature, design)
            except (ValueError, RuntimeError, TypeError, KeyError) as exc:
                st.error(str(exc))
    design_bundle = st.session_state.get("decision_ranking")
    if design_bundle and design_bundle[0] == design_signature:
        design = design_bundle[1]
        st.caption(
            f"Method: {design.method}. Expected local reductions only; these are not confidence intervals."
        )
        for row in design.top3.to_dict("records"):
            st.markdown(f"**{row['rank']}. {row['candidate']}**")
            st.write(row["reason"])
        st.dataframe(design.ranking, hide_index=True, width="stretch")
        st.download_button(
            "Download experiment ranking evidence",
            json.dumps(design.report(), indent=2, allow_nan=False),
            "experiment_ranking.json",
            "application/json",
        )
