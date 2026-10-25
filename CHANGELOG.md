# Changelog

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
