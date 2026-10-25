"""Guided, signature-keyed upload -> report. No research parameter fallback."""

import hashlib
import json
from dataclasses import asdict

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .calibration import fit_joint, leave_one_run_out
from .calibration_io import load_job, synthetic_job
from .demo import demo_model_parameters
from .fit_report import plain_language, report_html, report_payload, report_pdf
from .models import parameter_schema
from .parameters import SPECIES, Parameter, c_minutissima_preset
from .wizard_data import DW_FACTORS, N_FACTORS, TIME_FACTORS, map_observations, read_wide_csv

STAGES = ["1 Upload", "2 Map columns", "3 Check units", "4 Choose model", "5 Fit", "6 Read result / report"]


def _clear(st, *names):
    for name in names:
        st.session_state.pop("guide_" + name, None)


def _next(st, stage):
    st.session_state.guide_pending_stage = STAGES[stage]
    st.rerun()


def _worked_wide():
    config, long = synthetic_job()
    wide = long.pivot(
        index=["run_id", "time_day", "replicate"], columns="observable", values="value"
    ).reset_index()
    return config, wide.to_csv(index=False).encode()


def render_wizard():
    import streamlit as st

    st.markdown("### Guided upload to report")
    st.caption("Six steps. Biological cultures need separate run ids; technical repeats share a culture id.")
    if "guide_pending_stage" in st.session_state:
        st.session_state.guide_stage = st.session_state.pop("guide_pending_stage")
    stage = st.selectbox("Current step", STAGES, key="guide_stage")
    index = STAGES.index(stage)
    st.progress(index / 5, text=f"Step {index + 1} of 6")
    if index == 0:
        mode = st.radio(
            "Guided input", ["Upload my measurements", "SYNTHETIC worked example"], key="guide_input_mode"
        )
        synthetic = mode.startswith("SYNTHETIC")
        if st.session_state.get("guide_mode_seen") != mode:
            _clear(st, "source", "raw", "observations", "confirmed", "job", "fit", "cv", "proxy")
        st.session_state.guide_mode_seen = mode
        if synthetic:
            _, raw = _worked_wide()
            st.warning("SYNTHETIC / DEMO teaching data. All model values are UNVERIFIED assumptions.")
        else:
            upload = st.file_uploader("Cultivation measurements CSV", type=["csv"], key="guide_upload")
            st.write(
                "Use a wide table: one time column, dry-weight (or calibrated proxy) column, optional elemental N/quota, run id and technical replicate id."
            )
            if upload is None:
                return
            raw = upload.getvalue()
        digest = hashlib.sha256(raw).hexdigest()
        source = (digest, synthetic)
        if st.session_state.get("guide_source") != source:
            _clear(st, "source", "raw", "observations", "confirmed", "job", "fit", "cv", "proxy")
        try:
            frame = read_wide_csv(raw)
        except (ValueError, UnicodeError, pd.errors.ParserError) as exc:
            st.error(str(exc))
            return
        st.session_state.guide_source = source
        st.session_state.guide_raw = raw
        st.dataframe(frame, width="stretch", hide_index=True)
        if st.button("Continue to column mapping", key="guide_to_mapping"):
            _next(st, 1)
        return
    if "guide_source" not in st.session_state:
        st.info("Start with Step 1: upload a CSV or explicitly select the synthetic example.")
        return
    digest, synthetic = st.session_state.guide_source
    raw = st.session_state.guide_raw
    if index == 1:
        _clear(st, "confirmed", "job", "fit", "cv")
        frame = read_wide_csv(raw)
        columns = list(frame.columns)

        def choose(label, expected, optional=False):
            options = ["(absent)"] + columns if optional else columns
            return st.selectbox(
                label,
                options,
                index=options.index(expected) if expected in options else 0,
                key="guide_map_" + label,
            )

        mapping = {"time": choose("Time", "time_day"), "X": choose("Biomass / proxy", "X")}
        for field, label, guess in [
            ("N", "Elemental nitrogen", "N"),
            ("q", "Intracellular quota", "q"),
            ("run", "Culture run id", "run_id"),
            ("replicate", "Technical replicate id", "replicate"),
        ]:
            value = choose(label, guess, True)
            if value != "(absent)":
                mapping[field] = value
        units = {"time": st.selectbox("Time unit", list(TIME_FACTORS), key="guide_time_unit")}
        proxy = st.checkbox("Biomass column is OD / cell count", key="guide_use_proxy")
        calibration = st.session_state.get("active_dw_calibration") if proxy else None
        if proxy:
            if calibration is None:
                st.info("First fit paired measurements in the OD / cell count workspace, then return here.")
                return
            if calibration.origin != ("SYNTHETIC" if synthetic else "MEASURED"):
                st.error("Synthetic proxy conversions cannot be applied to measured uploads (or vice versa).")
                return
            st.caption(
                f"Active conversion: {calibration.species}; {calibration.conditions}; domain {calibration.domain} {calibration.canonical_signal_unit}"
            )
            units["X"] = st.selectbox(
                "Biomass proxy unit",
                [calibration.signal_unit, calibration.canonical_signal_unit],
                key="guide_proxy_unit",
            )
        else:
            units["X"] = st.selectbox("Dry-weight unit", list(DW_FACTORS), key="guide_x_unit")
        if "N" in mapping:
            units["N"] = st.selectbox("Nitrogen unit (elemental N only)", list(N_FACTORS), key="guide_n_unit")
        if "q" in mapping:
            units["q"] = st.selectbox("Quota unit", ["g_N/g_DW"], key="guide_q_unit")
        st.caption(
            "Time is elapsed from inoculation; it is never shifted. Missing measurement cells are omitted. Without a replicate column, each row gets its own technical id. Separate cultures need separate run ids."
        )
        if st.button("Apply mapping and conversions", key="guide_apply_map"):
            try:
                observations = map_observations(frame, mapping, units, calibration=calibration)
                st.session_state.guide_observations = observations
                st.session_state.guide_proxy = calibration.report() if calibration else None
                _next(st, 2)
            except (ValueError, TypeError) as exc:
                st.error(str(exc))
        return
    data = st.session_state.get("guide_observations")
    if data is None:
        st.info("Complete Step 2: map columns and confirm units.")
        return
    if index == 2:
        _clear(st, "job", "fit", "cv")
        st.dataframe(data, width="stretch", hide_index=True)
        st.write(
            f"{data.run_id.nunique()} culture run(s); {len(data)} measurements. Canonical units: {dict(data.groupby('observable').unit.first())}."
        )
        st.warning(
            "N means elemental nitrogen mass, not nitrate-ion mass. Dry weight is not carbon mass. Check the assay basis before continuing."
        )
        if (data.value < 0).any():
            st.info(
                "Negative raw assays are retained for additive errors. Log-normal errors require strictly positive observations."
            )
        confirmed = st.checkbox(
            "I confirm the units, culture/technical replicate ids, and times from inoculation",
            key="guide_confirm_units",
        )
        if st.button("Continue to model", disabled=not confirmed, key="guide_to_model"):
            st.session_state.guide_confirmed = True
            _next(st, 3)
        return
    if not st.session_state.get("guide_confirmed"):
        st.info("Complete Step 3: check the converted units and replicate identities.")
        return
    if index == 3:
        _clear(st, "job", "fit", "cv")
        _model_form(st, data, synthetic)
        return
    config = st.session_state.get("guide_job")
    if config is None:
        st.info("Complete Step 4: supply all model parameters, run conditions, search bounds and error SDs.")
        return
    signature = hashlib.sha256(
        raw
        + data.to_csv(index=False).encode()
        + json.dumps(config, sort_keys=True).encode()
        + json.dumps(st.session_state.get("guide_proxy"), sort_keys=True).encode()
    ).hexdigest()
    try:
        runs, search, errors = load_job(config, data)
    except (ValueError, TypeError, KeyError) as exc:
        st.error(str(exc))
        return
    if index == 4:
        st.write(
            f"Model: {config['kind']} / {config['light']}. {len(runs)} runs; {len(search)} shared fitted parameter(s)."
        )
        st.caption(
            "Search limits are numerical assumptions, not verified species ranges. Profiling can take minutes; results will appear below."
        )
        st.dataframe(runs[0].model.provenance(), width="stretch", hide_index=True)
        st.write(f"Noise: {errors.kind}; fixed SDs {errors.scales}. Parameters to fit: {config['search']}.")
        if st.button("Fit and check identifiability", key="guide_fit_button"):
            with st.spinner("Fitting shared parameters and reoptimizing likelihood profiles..."):
                try:
                    st.session_state.guide_fit = (signature, fit_joint(runs, search, errors))
                except (ValueError, RuntimeError) as exc:
                    st.error(str(exc))
        bundle = st.session_state.get("guide_fit")
        if bundle and bundle[0] == signature:
            st.success("Calculation finished. Read the profile flags in Step 6 before using any estimate.")
        if st.button("Compute whole-run held-out error", disabled=len(runs) < 2, key="guide_cv_button"):
            with st.spinner("Refitting and profiling each training fold..."):
                try:
                    st.session_state.guide_cv = (signature, leave_one_run_out(runs, search, errors))
                except (ValueError, RuntimeError) as exc:
                    st.error(str(exc))
        if len(runs) < 2:
            st.info(
                "Held-out evaluation needs at least two independent cultures; one-run in-sample error cannot replace it."
            )
        if st.button("Read result and export report", key="guide_to_result"):
            _next(st, 5)
        return
    bundle = st.session_state.get("guide_fit")
    if not bundle or bundle[0] != signature:
        st.info("No current fit. Run Step 5 after confirming all inputs.")
        return
    result = bundle[1]
    for message in plain_language(result):
        st.info(message)
    st.caption(
        f"Interval method: {result.report()['interval_method']}. Confidence: {result.confidence:.0%}. "
        "Marginal intervals conditional on fixed inputs; empirical coverage is not established."
    )
    st.dataframe(result.table(), width="stretch", hide_index=True)
    st.dataframe(result.metrics, width="stretch", hide_index=True)
    for observable, group in result.predictions.groupby("observable"):
        fig = go.Figure()
        for run_id, frame in group.groupby("run_id"):
            ordered = frame.sort_values("time_day")
            fig.add_scatter(x=ordered.time_day, y=ordered.value, mode="markers", name=f"{run_id}: observed")
            fig.add_scatter(
                x=ordered.time_day, y=ordered.predicted, mode="lines", name=f"{run_id}: in-sample model"
            )
        fig.update_layout(xaxis_title="Time (day)", yaxis_title=f"{observable} ({group.unit.iloc[0]})")
        st.plotly_chart(fig, width="stretch")
    cv_bundle = st.session_state.get("guide_cv")
    cv = cv_bundle[1] if cv_bundle and cv_bundle[0] == signature else None
    if cv:
        st.dataframe(cv.folds, width="stretch", hide_index=True)
        st.dataframe(cv.metrics, width="stretch", hide_index=True)
    else:
        st.warning("Held-out error not computed. In-sample error is not predictive accuracy.")
    title = st.text_input("Report title", "AlgaTwin cultivation fit", key="guide_report_title", max_chars=200)
    try:
        payload = report_payload(
            result,
            title=title,
            input_sha256=digest,
            cv=cv,
            proxy_calibration=st.session_state.get("guide_proxy"),
        )
        st.download_button(
            "Download HTML report",
            report_html(payload),
            "alga_twin_report.html",
            "text/html",
            key="guide_html",
        )
        st.download_button(
            "Download PDF report",
            report_pdf(payload),
            "alga_twin_report.pdf",
            "application/pdf",
            key="guide_pdf",
        )
        st.download_button(
            "Download full report evidence (JSON)",
            json.dumps(payload, indent=2, allow_nan=False),
            "alga_twin_report.json",
            "application/json",
            key="guide_json",
        )
        st.download_button(
            "Download reusable model configuration",
            json.dumps(config, indent=2),
            "alga_twin_job.json",
            "application/json",
            key="guide_job_download",
        )
        st.download_button(
            "Download mapped observations",
            data.to_csv(index=False),
            "alga_twin_observations.csv",
            "text/csv",
            key="guide_obs_download",
        )
    except (ValueError, ImportError) as exc:
        st.error(str(exc))


def _model_form(st, data, synthetic):
    species_choice = st.radio(
        "Species / strain", [SPECIES, "I don't know my strain"], key="guide_species_choice"
    )
    species = "SYNTHETIC" if synthetic else (SPECIES if species_choice == SPECIES else "UNKNOWN STRAIN")
    catalogue = c_minutissima_preset() if species_choice == SPECIES else {}
    ranges = [
        {"parameter": name, **asdict(p)}
        for name, p in catalogue.items()
        if p.status == "VERIFIED" and p.low is not None and p.high is not None
    ]
    if ranges:
        st.dataframe(pd.DataFrame(ranges), width="stretch", hide_index=True)
    else:
        st.info(
            "No executable VERIFIED-range preset is available for this selection. No species values are filled automatically."
        )
    if not synthetic:
        st.warning(
            "Missing extinction stays unset. Use the species evidence / measure extinction workspace. Unknown strains require their own measurements; another species' parameters are not substituted."
        )
    kind = st.selectbox("Guided nutrient model", ["monod", "droop"], key="guide_kind")
    light = st.selectbox("Guided light response", ["monod", "haldane", "han"], key="guide_light")
    temperature = st.checkbox("Guided CTMI temperature factor", key="guide_temperature")
    diurnal = st.checkbox("Guided diurnal half-sine light", key="guide_diurnal")
    exponent = st.number_input(
        "Explicit extinction exponent s", min_value=0.01, max_value=1.0, value=1.0, key="guide_exponent"
    )
    schema = parameter_schema(kind, light, temperature, diurnal, exponent)
    demo = (
        demo_model_parameters(
            kind, light=light, temperature=temperature, diurnal=diurnal, extinction_exponent=exponent
        )
        if synthetic
        else {}
    )
    context = st.text_input(
        "Strain, assay methods and conditions for your parameter inputs",
        value="SYNTHETIC teaching assumptions" if synthetic else "",
        key=f"guide_context_{synthetic}",
    )
    rows = [
        {
            "parameter": name,
            "value": demo[name].value if synthetic else (exponent if name == "extinction_exponent" else None),
            "unit": unit,
            "basis": basis,
            "source": demo[name].source if synthetic else None,
        }
        for name, (unit, basis) in schema.items()
    ]
    st.caption(
        "Enter every fixed or initial parameter value. User-supplied values remain UNVERIFIED; source URLs are recorded, not verified by entry. Exponent is chosen above; coefficient units change with it. The loss rate applies throughout day and night."
    )
    records = st.data_editor(
        pd.DataFrame(rows),
        hide_index=True,
        width="stretch",
        disabled=["parameter", "unit", "basis"],
        key=f"guide_parameters_{synthetic}_{kind}_{light}_{temperature}_{diurnal}_{exponent}",
        column_config={"value": st.column_config.NumberColumn(required=True)},
    )
    run_rows = []
    worked, _ = _worked_wide() if synthetic else (None, None)
    worked_runs = {r["run_id"]: r for r in worked["runs"]} if worked else {}
    for run_id in data.run_id.unique():
        r = worked_runs.get(run_id, {})
        c = r.get("conditions", {})
        run_rows.append(
            {
                "run_id": run_id,
                "X0_g_DW_L": c.get("biomass_initial_g_L"),
                "N0_mg_N_L": c.get("nitrogen_initial_mg_L"),
                "q0_g_N_g_DW": 0.06 if synthetic and kind == "droop" else None,
                "light_umol_m2_s": c.get("incident_light_umol_m2_s"),
                "path_m": c.get("optical_path_m"),
                "temperature_C": 25.0 if synthetic and temperature else None,
            }
        )
    st.caption(
        "Initial conditions are supplied independently at inoculation. No noisy first measurement is silently reused as a known initial state. Light is constant or the peak of the selected diurnal schedule; path is metres."
    )
    conditions = st.data_editor(
        pd.DataFrame(run_rows),
        hide_index=True,
        width="stretch",
        disabled=["run_id"],
        key=f"guide_run_conditions_{synthetic}_{kind}_{temperature}_{','.join(data.run_id.unique())}",
    )
    eligible = [
        name
        for name in schema
        if name not in {"extinction_exponent", "period_day", "daylight_day", "dawn_day"}
    ]
    selected = st.multiselect(
        "Shared parameters to fit",
        eligible,
        default=["mu_max_day"] if "mu_max_day" in eligible else ["han_k"],
        key=f"guide_selected_{kind}_{light}_{temperature}_{diurnal}",
    )
    search_rows = []
    for name in selected:
        default = (
            {"low": 0.3, "high": 1.8, "initial": 0.7}
            if synthetic and name == "mu_max_day"
            else {"low": None, "high": None, "initial": None}
        )
        search_rows.append({"parameter": name, **default, "scale": "log"})
    search = st.data_editor(
        pd.DataFrame(search_rows, columns=["parameter", "low", "high", "initial", "scale"]),
        hide_index=True,
        width="stretch",
        disabled=["parameter"],
        key=f"guide_search_{synthetic}_{kind}_{light}_{','.join(selected)}",
        column_config={"scale": st.column_config.SelectboxColumn(options=["linear", "log"], required=True)},
    )
    noise = st.radio("Guided observation errors", ["additive", "log-normal"], key="guide_noise")
    st.caption(
        "Supply a fixed measurement SD in each observable's unit for additive errors, or a dimensionless log-SD for log-normal errors. These are assumptions unless independently measured."
    )
    noise_rows = [
        {
            "observable": obs,
            "SD": {"X": 0.003, "N": 0.3}.get(obs) if synthetic and noise == "additive" else None,
            "unit": unit if noise == "additive" else "dimensionless",
        }
        for obs, unit in data.groupby("observable").unit.first().items()
    ]
    scales = st.data_editor(
        pd.DataFrame(noise_rows),
        hide_index=True,
        width="stretch",
        disabled=["observable", "unit"],
        key=f"guide_scales_{synthetic}_{noise}_{','.join(sorted(data.observable.unique()))}",
    )
    if not st.button("Confirm model and all explicit assumptions", key="guide_confirm_model"):
        return
    try:
        if not context.strip() or not selected:
            raise ValueError("Supply input conditions/methods and select at least one parameter to fit")
        params = {}
        for row in records.to_dict("records"):
            value = float(row["value"])
            if not np.isfinite(value):
                raise ValueError(f"{row['parameter']} is unset; supply your own evidence/value")
            if row["parameter"] == "extinction_exponent" and value != exponent:
                raise ValueError("Set extinction exponent above the table so coefficient units match")
            source = row["source"] if pd.notna(row["source"]) and str(row["source"]).strip() else None
            params[row["parameter"]] = asdict(
                Parameter(
                    value,
                    None,
                    None,
                    row["unit"],
                    source,
                    "UNVERIFIED",
                    species,
                    context,
                    row["basis"],
                    "DEMO" if synthetic else "MEASURED",
                    "synthetic_assumption" if synthetic else "user_supplied_not_verified",
                )
            )
        proxy = st.session_state.get("guide_proxy")
        if proxy and proxy["species"] != species and not synthetic:
            raise ValueError(
                "Proxy calibration strain differs from the chosen species; fit a matching paired calibration"
            )
        runs = []
        for row in conditions.to_dict("records"):
            initial = [float(row["X0_g_DW_L"]), float(row["N0_mg_N_L"])]
            if kind == "droop":
                initial.append(float(row["q0_g_N_g_DW"]))
            runs.append(
                {
                    "run_id": row["run_id"],
                    "origin": "SYNTHETIC" if synthetic else "MEASURED",
                    "conditions": {
                        "biomass_initial_g_L": initial[0],
                        "nitrogen_initial_mg_L": initial[1],
                        "incident_light_umol_m2_s": float(row["light_umol_m2_s"]),
                        "optical_path_m": float(row["path_m"]),
                    },
                    "initial_state": initial,
                    "temperature_c": float(row["temperature_C"]) if temperature else None,
                }
            )
        config = {
            "format_version": 1,
            "kind": kind,
            "light": light,
            "diurnal": diurnal,
            "parameters": params,
            "runs": runs,
            "search": {
                row["parameter"]: {
                    key: (str(row[key]) if key == "scale" else float(row[key]))
                    for key in ("low", "high", "initial", "scale")
                }
                for row in search.to_dict("records")
            },
            "error_model": {
                "kind": noise,
                "scales": {
                    row["observable"]: [float(row["SD"]), row["unit"]] for row in scales.to_dict("records")
                },
            },
        }
        load_job(config, data)
        json.dumps(config, allow_nan=False)
        st.session_state.guide_job = config
        _next(st, 4)
    except (ValueError, TypeError, KeyError) as exc:
        st.error(f"Model is incomplete or inconsistent: {exc}. Missing fields have no fallback values.")
