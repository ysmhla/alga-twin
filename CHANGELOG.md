# Changelog

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
