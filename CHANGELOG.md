# Changelog

## 0.6.0 — 2026-10-25

- Add benchmark metadata schema and fail-closed licence/unit/basis/species/hash loaders.
- Include only a clearly labelled, seeded SYNTHETIC fixture with repository MIT permission evidence.
- Export PEtab 2 native-model bundles, an explicit reader and actual libpetab format checks.
- Run actual pyPESTO full-data profiles/optimization against the exported likelihood;
  native SciPy profile gates and whole-run CV remain separately labelled.
- Write licence-bearing scoreboards with distinct in-sample/held-out errors and fold coverage.
- Add equivalence, limiting-case, conservation, licence refusal and unsupported-inference tests.
- Optional benchmark toolchain requires Python 3.12+ (PEtab 0.9); core Python 3.11 remains supported.
- Measured benchmarks, generic SBML/AMICI import and independent biological evaluation remain pending.


## 0.5.0 — 2026-10-25

- Fit selected shared parameters across runs with additive/log-normal errors and explicit SDs/bounds.
- Preserve technical replicates; reject duplicate identities, unit errors and mixed data origins.
- Reoptimize nuisance parameters for each profile; withhold unsupported points/intervals.
- Apply the profile gate to the existing single-run UI/CLI too.
- Add whole-run refitting/profiling cross-validation with separate training/held-out metrics.
- Add an equivalent log-nitrogen numerical coordinate for near-depletion likelihoods, without pseudocounts.
- Add explicit JSON jobs/long CSV, joint Streamlit workspace and fit-joint CLI exports.
- Keep independent biological evaluation, empirical coverage, optional MCMC and supported model comparison pending.


## 0.4.0 — 2026-10-25

- Add ModelBase interface, retained Monod adapter and reduced N-quota Droop model.
- Add Haldane and steady-state Han light, CTMI and explicit half-sine diurnal forcing.
- Track removed nitrogen for zero/nonzero loss mass-balance accounting.
- Add explicit synthetic model workspace, evidence table and trajectory/provenance exports.
- Document the arXiv v1 Eq. 9 second-branch discrepancy; compare both compensation roots
  and the zero-depth boundary, with analytic/numerical regression checks.
- Keep missing C. minutissima values/f_C unset; no source parameters transferred.
- New model fitting, independent biological evaluation and hosting remain pending.


## 0.3.0 — 2026-10-25

- Added immutable parameter evidence records, units/basis checks and C. minutissima source catalogue.
- Removed implicit numerical model defaults; synthetic parameters require explicit DEMO selection or CLI --demo.
- Kept extinction/carbon fraction and unsupported species parameters unset; no cross-species substitution.
- Added optional sublinear extinction with exponent-dependent coefficient units.
- Added direct dry-biomass/transmission extinction fitting and diagnostics, without automatic preset promotion.
- Added provenance tables/exports and verified-range override warnings; no unsupported ranges invented.
- Updated model equations, source audit, regression tests and CI lint. Replaced deprecated Streamlit width arguments.
- Breaking API: extinction_L_per_g_m renamed extinction_a0; Parameters requires eight numerical fields.
- No new biological validation, confidence intervals or advanced growth-model claims.

## 0.2.1 — 2026-10-25

- Added a real Streamlit runtime workflow regression test.
- Verified calibration, slider response, scenario snapshots and planner state invalidation.
- Verified local HTTP health and HTML responses.
- Updated release evidence and outstanding publication/validation gates.

## 0.2.0 — 2026-10-25

- Added TrustLens local sensitivities and heuristic calibration-domain warnings.
- Added sampled non-dominated experiment-planning grid.
- Added package CLI (`alga-twin simulate` and `alga-twin fit`).
- Saved model parameter snapshots with each ScenarioLab scenario.
- Fixed reactor default slider value when calibration irradiance is above 700.
- Clarified biomass extinction coefficient units (L g⁻¹ m⁻¹).
- Added scientific demo preview and expanded architecture/release documentation.

## [0.1.0] — 2026-10-25

- Initial single-species batch Monod-light numerical model and nutrient balance.
- Reproducible synthetic cultivation observations and strict single-run CSV ingestion.
- Constrained limited-parameter calibration with illustrative noise scaling.
- Streamlit data studio, virtual reactor, light heatmap and scenario comparison.
- Result/manifests CSV and JSON downloads, tests, CI and deployment scaffolding.
- **Not independently validated.** Future models and optimisation are not implemented.
