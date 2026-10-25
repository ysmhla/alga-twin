# Release status — v0.4.0 (2026-10-25)

Steps 1 and 2 engineering are implemented: parameter evidence/units, optical helper,
common model interface, Monod/Droop, Haldane/steady-state Han, CTMI, diurnal forcing,
N-loss ledger and a separate synthetic model workspace with provenance export.
Local verification passed: 100 tests (Python 3.12), Ruff lint/format and compileall.
Cloud Python 3.11 and 3.12 passed 100 tests and Ruff each: https://github.com/ysmhla/alga-twin/actions/runs/40197007799.
Source commit: 8bf5527a21491ee6a636bf94f2dcf38e41f0ffee. See VERIFICATION.md.

Missing C. minutissima values and f_C remain unset. All new numerical fixtures are
SYNTHETIC / UNVERIFIED. No species parameter ranges are invented. Eq. 9's printed
high-light branch discrepancy and the amended analytic check are documented in
SELECTABLE_MODELS.md. No independent biological validation is claimed.

- NOT DEPLOYED: hosted app. Streamlit sign-in/terms remain pending.
- NOT TESTED: visual browser layout and Docker build/run.
- NOT VALIDATED: independent cultivation/optical data.
- NOT BUILT: joint calibration, profile likelihood/identifiability, licensed
  benchmark/PEtab pipeline, experiment recommendation, model-support selection,
  OD calibration, tutorial/report/user-testing workflows and publication package.
