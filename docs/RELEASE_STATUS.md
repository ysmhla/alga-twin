# Release status — v0.2.1 (2026-10-25)

## Implemented and verified locally

- Single-species batch Monod/light numerical model and nitrate-as-N balance.
- CSV ingestion, constrained fitting and synthetic recovery checks.
- Virtual Reactor, LightScope, ScenarioLab, TrustLens, sampled planner, CLI and exports.
- Real Streamlit runtime workflow test in addition to the original 33 tests.
- Local Streamlit server startup, health endpoint and HTML response.
- CI and Docker/Streamlit/Render deployment configuration files.

## Remaining gates

- **BLOCKED:** Public GitHub repository creation was rejected by automatic approval review because explicit authorization for the public publication destination was required. No repository was created and no files were published. Requested destination: `ysmhla/alga-twin`.
- **NOT DEPLOYED:** Hosted Streamlit application.
- **NOT TESTED:** Visual browser interaction, Docker build/run and remote GitHub Actions.
- **NOT VALIDATED:** Independent measured cultivation data.
- **NOT BUILT:** Droop quota, formal uncertainty intervals, global optimisation, sensor ingestion and photoinhibition.

The package is prepared for publication, not an already published or scientifically validated service. See [verification](VERIFICATION.md).
