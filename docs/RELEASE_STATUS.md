# Release status — v0.8.0 verification in progress, 2026-10-26

Step 6 implementation passed 155 local tests (215.24 s), Ruff lint/format,
compilation and pip check. Cloud and live rollout checks remain in progress.
No v0.8 cloud/deployment claim is made here yet. See DECISION_SUPPORT.md for the new conditional methods.

Steps 1–5 software engineering are implemented (5/7 engineering packages).
Step 5 human acceptance remains incomplete: no independent novice <5-minute
upload-to-report study or five observed human issues/fixes has been conducted.
Measured benchmark/biological evaluation also remains pending human data.

**Public demo deployed:** https://alga-twin.streamlit.app/ . App settings explicitly
showed public/searchable. Python 3.12.15 and Streamlit 1.66.1 were observed after
selecting/rebuilding the runtime. Actual app screenshots, three-run SYNTHETIC
fit/profile/CV checks, parsed HTML/PDF/JSON downloads and checksums are in
[smoke/README.md](smoke/README.md). Initial browser artifacts record v0.7.0/source
0b1090d45c2741996e66047058d7b73c1957b945. All 3/3 synthetic holdouts scored. A separate fresh session verified the deployed
v0.7.1 header and full interval-method/confidence caption after rollout.

The v0.7.1 UI-only patch keeps full interval method/confidence visible above all
result tables. No model, likelihood, parameter default or numerical report law
changes. Current-source cloud run 40240500191 passed 143 tests/Ruff and both tutorials on
Python 3.12, and 132 tests/one optional skip/Ruff on Python 3.11. Source:
3b69d4a56059b8b207f3b8e0f13010ada78f2074. Local targeted UI checks, Ruff lint/format,
compilation and dependency checks passed; see VERIFICATION.md for exact scope.

C. minutissima source gaps, extinction and f_C remain unset. No cross-species
transplants or invented ranges are supplied. Conditional profile intervals do
not establish empirical coverage; proxy-calibration uncertainty is not propagated.
No biological validation, novelty or operational-recommendation claim is made.

- PENDING HUMAN INPUT: legally reusable measured datasets/metadata and novice-study observations.
- NOT VALIDATED: independent biological/optical predictions or interval coverage.
- NOT TESTED: human novice/mobile/measured-upload browser acceptance and Docker/Render deployment.
- NOT BUILT: publication/DOI/docs site,
  optional MCMC or streaming estimator (deferred until suitable independent data).
