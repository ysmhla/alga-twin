# Release status — v0.2.1 (2026-10-25)

## Implemented and verified locally

- Single-species batch Monod/light numerical model and nitrate-as-N balance.
- CSV ingestion, constrained fitting and synthetic recovery checks.
- Virtual Reactor, LightScope, ScenarioLab, TrustLens, sampled planner, CLI and exports.
- Real Streamlit runtime workflow test in addition to the original 33 tests.
- Local Streamlit server startup, health endpoint and HTML response.
- CI and Docker/Streamlit/Render deployment configuration files.

## Remaining gates

- **PUBLISHED:** All 43 project files are public at https://github.com/ysmhla/alga-twin after explicit user authorization.
- **PASS:** GitHub Actions on Python 3.11 and 3.12: https://github.com/ysmhla/alga-twin/actions/runs/40177389592 (source commit `42b524388b1e666caf0f690fc95e2b4591e80f57`).
- **NOT DEPLOYED:** Hosted Streamlit application.
- **NOT TESTED:** Visual dashboard browser interaction and Docker build/run.
- **NOT VALIDATED:** Independent measured cultivation data.
- **NOT BUILT:** Droop quota, formal uncertainty intervals, global optimisation, sensor ingestion and photoinhibition.

The source is published. The hosted service and independent scientific validation remain pending. Streamlit sign-in requires agreement to its Terms of Service; that step awaits separate confirmation. See [verification](VERIFICATION.md).
