# AlgaTwin 2.0 — Project Master Plan

**Working title:** AlgaTwin — An Open, Calibrated Digital Twin for Microalgal Photobioreactors  
**Version:** Concept specification 2.0  
**Date:** 25 October 2026  
**Status:** PLANNED — NOT BUILT / NOT TESTED / NOT VALIDATED  
**Initial scope:** Single-species *Chlorella* batch cultivation in a well-mixed, externally illuminated photobioreactor  
**Stack:** Python, NumPy, SciPy, pandas, Pydantic, Plotly, Streamlit, pytest, Ruff, GitHub Actions  

> **Product promise:** Upload experimental observations, fit a scientifically constrained microalgal growth model, explore reactor scenarios, quantify limitations, and design better subsequent experiments. Recommendations are hypotheses, not experimentally proven outcomes.

## 1. Why this project

Researchers spend time choosing light schedules, nutrient concentrations, inoculum density and harvest time, while experimental observations may be scattered across spreadsheets. A controlled computational model can help compare plausible operating conditions and document assumptions, but model quality depends on data coverage and physics. AlgaTwin aims to connect laboratory records to transparent mathematical predictions and experimental design.

**Primary persona:** PhD student or bioprocess researcher running repeatable *Chlorella* cultivations at lab scale.  
**Secondary:** Engineering researcher investigating light limitation and resource-use trade-offs.  
**Not initially for:** industrial process safety control, multi-species ecology, clinical/food safety claims, unvalidated scale-up, autonomous real-world hardware control.

### Defining workflow
1. Start the demonstration dataset or upload experimental CSV.
2. Map column names and units, inspect data-quality diagnostics.
3. Select the simplest scientifically supportable model.
4. Fit constrained parameters; review parameter dependence and residuals.
5. Compare baseline model against held-out cultivation runs where available.
6. Explore light, initial nitrogen, path length, and inoculum density scenarios.
7. Inspect prediction uncertainty and domain-of-validity warnings.
8. Save the run configuration and export a reproducible scientific report.
9. Optionally receive feasible candidate conditions for the next experiment.

## 2. Positioning and real novelty

The field already has general-purpose bioprocess model platforms such as pyFOOMB and detailed algal models. Thus, the claim **'first microalgal simulator' must NOT be made**. AlgaTwin's design hypothesis is that a narrow but well-integrated, open, user-friendly *microalgae-specific* tool can be useful if it combines these six modules:
- **SmartFit:** guided CSV mapping, constrained multi-start calibration, and parameter bounds.
- **TrustLens:** identifiability warnings, residual inspection, validation splits and uncertainty.
- **LightScope:** reactor-path light attenuation and spatial response integration.
- **ScenarioLab:** saved scenario comparisons using the SAME calibrated baseline.
- **NextBest:** feasible next-experiment proposals, initially based on sensitivity.
- **ReproPack:** data provenance, model equation/version, environment and seeded settings.

These are planned differentiators, not verified unique inventions. Do a gap review and feedback interviews before making a novelty claim.

## 3. Strict scope boundary

**MVP / v0.1:** One batch species, constant or defined periodic surface irradiance, fixed temperature, no CO2/pH dynamic balance, no chemical inhibition except chosen simple light function, well-mixed liquid with 1D optical path. Both nutrient and biomass concentration can be observed at sparse timestamps.

**v1.0:** Working data import, basic/Monod-light model, CSV calibration, multiple runs, scenario comparisons, first uncertainty diagnostics and runnable app.

**v1.5:** Internal-quota Droop model, photoinhibition where supported, statistical experiment planning, improved uncertainty and validation.

**v2.0:** Advanced optimization, rich reactor geometries, optional light/dark schedules, validated observation models, multi-species support only after new datasets and modelling research.

**Explicitly not supported in v1.0:** broad taxonomic generalization, CO2-limited predictions, detailed mixing/CFD, rigorous reactor scale-up, photosynthetic efficiency prediction independent of calibration, or accurate predictions outside measured conditions.

## 4. Scientific models

### 4.1 Units and states

Core states: `X(t)` = dry biomass concentration [g DW/L]; `N(t)` = dissolved available nitrogen in **mg N/L** or g N/L, but all internal calculations use one canonical unit. Time in days. `I0(t)` = photosynthetically active photon flux density at the illuminated surface [µmol photons/m²/s]. Optical depth/path `L` in metres. Document whether an experiment reports nitrate-as-N, NO3-, ammonium-as-N, or total nitrogen: these are not interchangeable.

### 4.2 Baseline exponential model

`dX/dt = (mu - kd) X`. Used only as a numerical and fitting baseline; it does not predict depletion or self-shading.

### 4.3 Monod + light + nutrient (primary)

Define the local normalized light response `fI(I) = I / (KI + I)` for positive `I` (saturating, no photoinhibition). Define incident illumination `I0(t)` (may follow a photoperiod). Simplified attenuation:

`I(z,t) = I0(t) * exp(-(k0 + kX*X(t)) * z)` for `0 <= z <= L`.

Average **light-dependent growth function**, not necessarily the function of mean light:

`fbar(X,t) = (1/L) * integral_0^L fI(I(z,t)) dz`.

`mu_g = mu_max * [N/(KN + N)] * fbar(X,t)`

`dX/dt = (mu_g - kd) * X`

`dN/dt = -mu_g * X / Y_XN`

The nutrient equation is a **growth-associated constant-yield simplification**. Biomass decay is not returned automatically to nutrient; maintenance uptake and nutrient recycling are absent. This must be stated. For time-varying feeding, add corresponding inputs only in a future explicitly tested model.

The coefficients `k0`, `kX`, `KI`, `KN`, `Y_XN`, `mu_max`, `kd` should NOT all be fit from one short biomass curve. Some must be fixed from measured optical properties, separately calibrated, or constrained from independent runs.

### 4.4 Droop internal quota (later)

Use an explicitly selected and consistently dimensioned quota model, e.g. `Q` [mass N/mass dry biomass], `rho(N)` nutrient uptake [mass N / mass biomass / day]. Example:

`mu_g = mu_max * max(0, 1 - Qmin/Q) * fbar(X,t)`

`dX/dt = (mu_g - kd)*X` ; `dQ/dt = rho(N) - mu_g*Q` ; `dN/dt = -rho(N)*X`.

This is a conceptual retained-biomass quota balance. Treatment of cell loss, quota transfer, releases, multiple nutrients, and feeding requires explicit conservation-consistent extensions. Positivity and `Q >= Qmin` require numerical checks or reformulation. Do not automatically default to Droop merely because it has more detail.

### 4.5 Physical considerations

- Reactor shape determines **optical path**, illumination area, and the appropriate light field approximation, not just reactor volume.
- For non-planar cylinders or multi-sided light, do not reuse slab formula unmodified; either use validated effective optical path or a separate geometry module.
- Numerical depth integration via Gaussian quadrature or a sufficiently resolved layer discretization; test convergence.
- `I0 = 0` must yield zero light-associated growth, while biomass loss may continue.
- Positivity, finite outputs and unit consistency are mandatory solver invariants.
- Carbon limitation, pH drift, temperature sensitivity and dark respiration beyond the chosen `kd` remain omitted; communicate when extrapolation is unsafe.

## 5. CSV contracts and observation models

### Core timeseries (illustrative, SYNTHETIC ONLY)

```csv
experiment_id,time_day,biomass_g_L,nitrate_mg_N_L
EXP01,0,0.10,25.0
EXP01,2,0.16,22.1
EXP01,4,0.29,17.5
EXP01,6,0.48,10.4
EXP01,8,0.61,4.2
EXP01,10,0.64,1.1
```

### Metadata YAML (SYNTHETIC EXAMPLE)

```yaml
experiment_id: EXP01
species: Chlorella_vulgaris
cultivation_mode: batch
reactor_geometry: planar_equivalent
reactor_volume_L: 1.0
optical_path_m: 0.05
incident_par_umol_m2_s: 150
photoperiod_light_h: 24
temperature_C: 25
biomass_measurement: dry_weight
nutrient_basis: nitrate_as_N
source_type: synthetic
```

### Data import capabilities

- P0: `.csv` and supplied schema template; user column mapping; units; time ordering; labels of replicate/condition.
- P0: Detect missing timestamps, duplicate keys, nonphysical negative values, unknown measurement units, outlier candidates without auto-deletion.
- P0: Provenance for any transformation and interpolation; no invented measurements.
- P1: Support long-format observations containing separate timestamps for each variable.
- P1: Observation mapping `OD = a*X + b` only when user supplies appropriate calibration information; otherwise OD observations may fit an OD proxy with explicit limits, but cannot be reported as g/L.
- P1: Cell counts with suitable biological and instrument calibration; retain cell-count measurement model separately from true biomass state.
- P1: Standard deviations, per-observation weights, replicate hierarchy, outlier sensitivity check.
- P2: time-varying light and feed event files, independent pH/temperature observations, manual data-entry form.

### Modes

1. **Demo:** synthetic dataset with an unmissable synthetic label; known parameters for recovery tests.
2. **Basic:** biomass time series; restricted parameter fitting and cautious interpolation.
3. **Mechanistic:** biomass, nutrient series, irradiance/optical metadata; conditional richer fitting.

The source data itself never silently changes when a user switches scenario.

## 6. Parameter estimation / identifiability

Algorithm design:
1. Validate schema and units; infer measurement availability.
2. Build a model-data compatibility table and choose a small candidate parameter subset.
3. Fix certain parameters by measurement or documented priors/bounds; record those choices.
4. Normalize/weight residuals by observed-variable scale or supplied measurement SD.
5. Numerically solve ODE with `scipy.integrate.solve_ivp`; reject failed simulations.
6. Optimize bounded robust objective with `scipy.optimize.least_squares`, seeded multi-start initial guesses. Differential evolution optional when local starts repeatedly fail; report compute costs.
7. Inspect optimizer convergence, fit residuals, Jacobian rank / singular values / collinearity; perform profile or bootstrap analysis when appropriate.
8. Compare simpler vs richer models on held-out runs, not just training RMSE.
9. Return `fitted`, `fixed`, `weakly identified`, `not estimated` labels per parameter.
10. Produce structured JSON result including data checksum, model version, solver settings and random seed.

**Crucial limitation:** Small observation count plus many unknown parameters leads to non-identifiability. Avoid fitting `mu_max`, `KN`, `KI`, `kX`, `kd` and `Y_XN` simultaneously from a single biomass time series. A highly precise optimizer number does not imply a physically identified parameter.

## 7. Validation and uncertainty

### Three evidence grades
- **Demonstration:** Synthetic numbers generated by the very same equation; only proves software mechanics.
- **Historical data fit:** Reproduces observations used in calibration; not out-of-sample prediction.
- **Independent validation:** Parameters calibrated on some runs, predictions evaluated on different cultivation run(s). This is the key scientific evidence grade.

### Evaluation metrics
- RMSE and MAE in the actual measurement units, plus normalized RMSE when defined.
- Parameter recovery error on synthetic ground-truth cases.
- Prediction interval coverage and interval width on independent experimental runs.
- Residual autocorrelation and condition-specific bias diagnostics.
- Baseline-vs-advanced model comparison across experiments, not only per-timepoint shuffled splits.
- Solver accuracy/convergence and conservation/positivity checks.

### Uncertainty plans
- MVP: sensitivity envelopes and explicit range from plausible fixed parameters (label these scenario bands, NOT statistical 95% confidence intervals).
- Next: weighted residual/bootstrap estimates with documented assumptions, or profile-likelihood intervals.
- Later: Bayesian inference for selected models only if runtime and data support it.
- Extrapolation warnings: outside observed light, N, X0, optical path, measurement system, strain or temperature.

## 8. Optimisation and next-experiment design

### Scenario optimizer, P1
Input: feasible `I0`, initial `N`, initial `X`, photoperiod, optical path, cultivation time; constraints from user. Candidate objectives:
- `maximize X(T)` [g/L]
- `maximize [X(T)-X(0)]/T` [g/L/day]
- `minimize incident photons or estimated light-energy proxy per predicted biomass` (only if energy assumptions known)
- Pareto comparison between biomass and resource costs when units are explicit.

Search via grid/coarse Latin hypercube + SciPy bounded optimizer; seed and log random search. Compare against no-optimization baseline and show constraint satisfaction. Never claim real optimal operating points until independent validation.

### NextBest experiment proposal, P2
Different objective from maximising yield: maximise information about uncertain parameters. Start with finite-difference sensitivity / predicted response separation under candidate conditions and measurement schedule. Later formal information-matrix or Bayesian expected information gain. Report whether the candidate is designed for productivity exploration or for reducing uncertainty; do not conflate the two.

## 9. Interface design

**Pages**
1. **Overview** — clear value proposition, demonstration button, scientific status and limitations.
2. **Experiment Library** — demonstration, uploaded experiments, data provenance and condition table.
3. **SmartFit** — column mapping, model selection, parameter fitting progress, fitted/fixed labels and residuals.
4. **Virtual Reactor** — geometry/path slider, incident PAR, initial biomass and nutrient; real-time plots.
5. **LightScope** — heatmap of local irradiance over depth and cultivation day; depth integral diagnostic.
6. **ScenarioLab** — save/restore scenario cards; curves and difference plots with consistent units.
7. **TrustLens** — independent validation metrics, uncertainty grade, identifiability, warnings and applicability domain.
8. **NextBest** — feasible candidate tests, uncertainty trade-off and export of experimental plan (later).
9. **Export & Methods** — downloadable plots, CSV/JSON config, solver versions, literature citations and assumptions.

**Visual principles:** restrained scientific design, accessible contrast, compact controls; teal/green reserved for culture and biomass; clearly distinguish observations (points), fitted curves (solid), forecasts (dashed), uncertainty (bands), and missing/assumed information (labels).

**Performance controls:** cache *pure* deterministic simulation output keyed by parameters and model version. Do not globally cache user-uploaded private data; cap file size, timepoints, simulation length and optimisation evaluation budgets.

## 10. Implementation architecture

```text
alga-twin/
├── README.md
├── LICENSE
├── CITATION.cff
├── pyproject.toml
├── .github/
│   ├── workflows/ci.yml
│   └── ISSUE_TEMPLATE/
├── src/alga_twin/
│   ├── core/
│   │   ├── states.py
│   │   ├── units.py
│   │   ├── models/baseline.py
│   │   ├── models/monod_light.py
│   │   ├── models/droop.py          # future
│   │   ├── light.py
│   │   └── solver.py
│   ├── data/
│   │   ├── schemas.py
│   │   ├── importers.py
│   │   ├── observations.py
│   │   └── provenance.py
│   ├── fitting/
│   │   ├── objectives.py
│   │   ├── calibrate.py
│   │   └── identifiability.py
│   ├── analysis/
│   │   ├── validation.py
│   │   ├── uncertainty.py
│   │   └── sensitivity.py
│   ├── planning/
│   │   ├── scenarios.py
│   │   ├── optimisation.py
│   │   └── next_experiment.py
│   ├── export/
│   │   └── reproducibility.py
│   └── cli.py
├── app/
│   ├── Home.py
│   ├── pages/
│   └── components/
├── examples/
│   ├── demo_synthetic.csv
│   ├── demo_metadata.yaml
│   └── example_calibration.ipynb
├── data_sources/
│   └── README.md             # attribution + acquisition script, no unlicensed redistribution
├── tests/
│   ├── unit/
│   ├── integration/
│   └── scientific/
├── benchmarks/
│   └── README.md
└── docs/
    ├── equations.md
    ├── data_schema.md
    ├── validation_protocol.md
    ├── limitations.md
    └── roadmap.md
```

**Default technical choices:** Python 3.11+ with supported-version matrix; NumPy/SciPy for ODEs and numerical optimisation; pandas for data; Pydantic for schemas; Pint optional for robust units; Plotly + Streamlit for visualization; pytest and Ruff for tests/style; `uv`/lockfile for reproducible packaging; GitHub Actions for CI. Avoid backend microservices, database, Docker orchestration and advanced frontend framework until genuinely necessary.

## 11. Data candidates

**A. Hiltunen et al. (2025), Zenodo DOI 10.5281/zenodo.15687789**  
Contains four *Chlorella vulgaris* cultivation experiments, daily cell density and pH, dry weight at selected sampling days, and nutrient measurements initially/finally. Good candidate for condition comparison and cell-density model exploration. **Not automatically a dense dry-weight + nutrient time-series dataset**. Inspect spreadsheet sheets, measurement columns and license before choosing exact calibration objectives.

**B. Tiwari et al. (2025), Zenodo record 17177597**  
Real curated endpoint yield dataset and larger **augmented** datasets. Potentially useful for scenario-range or baseline explorations; augmented samples must not be treated as independent experimentally measured time-series evidence.

**C. Own laboratory data**  
If usage rights and quality allow, prepare separate independent runs for model calibration and validation. Do not infer rights to publish datasets merely from authorship/collaboration.

**Data governance:** provide acquisition script/links, citations, README source matrix, explicit original license, transformation steps, checksum, and provenance. Publish only redistributable samples.

## 12. Phases, work packages and gates

The time estimates below are **planning estimates for focused individual development**, not execution promises. Hardware experiments and externally sourced data can create substantial delays.

| Phase | Window | Build tasks | Exit gate |
|---|---|---|---|
| P0 — Research spec & data audit | Week 1 | Domain assumptions, data schemas, review candidate datasets, literature/equations | Model spec + clearly bounded scope + selected dataset with documented gaps |
| P1 — Scientific kernel | Weeks 2–3 | Baseline and Monod+light RHS, `solve_ivp`, light integration, positivity | Reference scenarios produce stable, physically interpretable outputs; scientific unit tests pass |
| P2 — CSV & calibration | Weeks 4–5 | Import wizard, canonical units, bounded least-squares, residuals, multi-start | Synthetic parameter recovery + transparent failure on insufficient data |
| P3 — Dashboard | Weeks 6–7 | Streamlit pages, growth charts, light heatmap, saved scenarios | User can demo without coding; datasets and assumptions clearly labelled |
| P4 — Trust & validation | Weeks 8–9 | Independent-run holdout, uncertainty types, sensitivity, warnings | Validation report is reproducible; no misleading accuracy badges |
| P5 — Optimisation & launch | Weeks 10–11 | Scenario optimiser, export, docs, tests, CI, walkthrough video | v1.0 release checklist passes; public demo deploys |
| R1 — Research extension | Weeks 12+ | Droop, experiment selection, photoinhibition, alternative models | Must pass separate data-identifiability/validation gates |

For a part-time solo contributor, expect longer than the nominal 10–11-week plan; no external validation outcome is guaranteed by that date.

### Milestone definitions

**M0 — Model specification complete:** equations, physical assumptions, dimensional analysis, parameter table, reference test cases, source-linked method notes.

**M1 — Synthetic scientific engine complete:** solve ODEs; physical variables nonnegative within tolerance; no negative growth due solely to software instability; continuity in parameter sweeps; grid refinement converges.

**M2 — Calibration reliable:** fitting known synthetic parameters within predeclared tolerance under informative synthetic observation regimes; correctly flags non-identification with insufficient data.

**M3 — Scientific demo usable:** CSV upload, plotting, bounded controls, labelled predictions, light profile and scenario difference all operate under automated smoke tests.

**M4 — Real dataset report:** reproducible fit and held-out-run evaluation where data supports it, with a frank limits section. If dense nutrient data are missing, say so and restrict inference.

**M5 — Public release:** README video/GIF, install instructions, example dataset, `CITATION.cff`, license, CI passing, release tag, changelog and issue templates.

## 13. Acceptance tests

### Physical/numerical
- Nonnegative finite X, N, I at valid inputs, within documented numerical tolerance.
- Under positive light and nutrient, growth may occur when growth rate exceeds losses.
- Under zero light, growth term vanishes; no artificially positive light-mediated growth.
- Constant zero/limited nutrient cannot create unaccounted nutrient mass.
- Increased biomass with other conditions fixed cannot increase transmitted light in Beer–Lambert slab formulation.
- Integration results remain stable when optical grid resolution increases.
- Units/time-step changes produce equivalent trajectories after conversion.
- Solver failures cause explicit failure messages instead of silently producing curves.

### Data/calibration
- Unsupported unit or invalid negative concentration gives actionable error.
- Synthetic truth recovery is evaluated only on identifiable synthetic data.
- Fitting never changes uploaded raw observations.
- Fixed parameters and initial guesses are logged.
- Too-short data produces `insufficient evidence` instead of false certainty.
- Training fit and independent-run validation never confused.

### Usability/software
- New user can run `pip install -e .` and `streamlit run app/Home.py`.
- Public demo can load without proprietary hardware, API key or inaccessible dataset.
- GitHub CI tests Python-supported versions; static checks, examples smoke tests, deterministic seeds.
- An exported reproducibility package can rerun the exact model with versioned settings.
- Uploaded data are not persisted or exposed by default on a public shared deployment.

## 14. GitHub showcase and launch

**Suggested short description:** `An open, data-calibrated digital twin for microalgal photobioreactors—simulate, fit, validate and design experiments.`

README hero sequence:
1. Header/title and one-sentence promise.
2. Video/GIF: upload `Chlorella` demo CSV → fit model → move light slider → compare growth/uncertainty.
3. Three screenshots: SmartFit, LightScope, ScenarioLab.
4. Clear ‘Demonstration data are synthetic’ label when applicable.
5. Quickstart (two commands), example notebook and actual model limits.
6. Equations + reproducible scientific validation, links to source references.
7. Tests/coverage/CI badges only when actually configured and verified.
8. Citation, license, contributing, changelog, future roadmap, known limitations.

**Open-source release plan:** MIT/BSD-3-Clause/Apache-2.0 license chosen after dependency review; public GitHub Issues and a few labelled `good first issue` tasks; semantic tags (`v0.1.0`, `v1.0.0`). Encourage contributions only after baseline quality and docs exist.

**Differentiation to avoid:** never claim 'industry ready', 'first-ever', 'AI-perfect yield prediction', 'Digital Twin validated' without matching evidence. An offline unvalidated mechanistic simulator is more accurately a *digital twin prototype / modelling workbench* until tied to real repeated observations.

## 15. Team/time/cost assumptions

**Suggested people:** scientific lead (experimental design, unit and model checks), Python scientific computing lead, and optionally a frontend/documentation contributor. One person can build first version with restricted scope.

**Infrastructure:** Open-source stack and local development largely free; optional Streamlit Community Cloud is available for public demonstrations, subject to service limits and confidentiality. No GPU needed for primary SciPy ODE and local optimiser. Hardware, experiments, calibrated sensors and publication-quality data acquisition are a separate budget; cannot assume zero cost.

**Key risks / mitigations:**
- Poor data coverage → start with simple models; mark fixed/estimated parameters; gather repeated experimental runs.
- Light physics oversimplification → explicit geometry limit; avoid generalized scale-up claims; integrate local light function.
- Identifiability issues → restrict fitted parameters; profile/correlation analysis; advise informative measurements.
- Numerical instability → positivity constraints/checks, convergence tests and clear solver error.
- Model overfitting → independent-run holdout, baseline comparisons, residual bias analysis.
- False confidence → distinguish synthetic demo, calibration fit and externally validated forecast.
- Scope explosion → release batch Monod-light version before Droop, IoT, LLM or CFD.
- Copyright/data rights → source links and appropriate permission rather than unverified raw redistribution.

## 16. Detailed initial GitHub issue backlog

1. `docs: specify canonical physical quantities and measurement units` — acceptance: signed-off unit table and equation references.
2. `feat(core): baseline growth ODE + tested solver wrapper` — test no light, zero biomass, reproducible time grids.
3. `feat(light): spatial Beer-Lambert irradiance + quadrature` — monotonic depth tests and quadrature convergence.
4. `feat(models): nutrient-coupled Monod light model` — conservation/positivity and parameter sensitivity tests.
5. `feat(data): CSV schema validator and metadata importer` — friendly invalid-data messages.
6. `feat(fitting): weighted constrained least squares` — synthetic identifiable recovery fixture.
7. `feat(fitting): parameter status and weak-identification warnings` — known underdetermined case flagged.
8. `feat(app): QuickStart and synthetic demo` — first-time user flow passes.
9. `feat(app): interactive reactor + LightScope` — expected visual update on slider change.
10. `feat(app): scenario snapshot & comparison` — no accidental recalibration per slider change.
11. `feat(analysis): held-out run diagnostics + metrics` — explicit train/validation IDs.
12. `feat(export): ReproPack JSON/CSV + model version` — local rerun matches within tolerance.
13. `feat(planning): bounded objective search + constraints` — respects feasible search bounds.
14. `ci: test/lint/package and sample app smoke test` — clean repository CI.
15. `docs: limitations, data citations, methods and tutorial` — review by scientist unfamiliar with code.

## 17. Go/no-go and research-quality gates

**Go** if synthetic tests recover identifiable parameters, the simpler Monod-light model exhibits stable sensible behavior, and a real dataset supports at least limited evaluation with documented measurement mapping.  
**Re-scope** if data cannot support nutrient or optical parameters: make that limitation central and target basic biomass-only modeling until better data exist.  
**Do not claim validation** on a dataset used solely for fitting or on augmented synthetic data.  
**Do not extend to multi-species** until first-species predictions have independent validation.

### Potential manuscript/workshop contribution
- An open, reproducible microalgal modelling workflow.
- Comparison of fitting fidelity vs independent-run generalisation under sparse measurements.
- Assessment of experimental designs that improve parameter identifiability.

Whether this is publishable depends on demonstrated novelty and results, not on software existence alone.

## 18. References, tools and starting evidence (accessed October 2026)

- Schediwy et al., *Microalgal kinetics — a guideline for photobioreactor design and process development* (2019). https://pmc.ncbi.nlm.nih.gov/articles/PMC6999068/
- Benavides et al., *Parameter identification of Droop model: an experimental case study* (2015). https://pubmed.ncbi.nlm.nih.gov/26033327/
- Benavides et al., *Parameter Identification of the Droop Model using Optimal Experiment Design* (2015). https://www.sciencedirect.com/science/article/pii/S2405896315000956
- Huesemann et al., *A validated model to predict microalgae growth in outdoor pond cultures* (2016). https://www.sciencedirect.com/science/article/pii/S2211926415300989
- Riihiaho et al., *Photobioreactor design utilizing procedural three-dimensional modelling and ray tracing* (2025). https://pubmed.ncbi.nlm.nih.gov/39876793/
- pyFOOMB project. https://github.com/MicroPhen/pyFOOMB
- REALM dynamic raceway simulator dataset/software. https://zenodo.org/records/15579693
- Hiltunen et al., Chlorella cultivation observations. https://zenodo.org/records/15687789
- Tiwari et al., microalgae real and augmented ML datasets. https://zenodo.org/records/17177597
- SciPy ODE solver. https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html
- SciPy robust least squares. https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html
- Streamlit Community Cloud deployment. https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app

---

## Final recommendation

**Start with a narrow, honest and technically excellent model:** single-species *Chlorella*, batch reactor, Monod + depth-integrated light attenuation, 2-state mass balances, user-provided CSV, restricted calibration, scenario comparison, and reproducible validation. Grow into Droop, active experiment design, and live IoT integration only as data supports them.

**The GitHub reputation builder is not model complexity by itself; it is reproducibility, numerical correctness, clear assumptions, external evidence, thoughtful user experience and documented limitations.**
