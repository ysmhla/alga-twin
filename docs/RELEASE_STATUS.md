# Release status — 2026-10-26

Main is the **unreleased 0.8.2.dev0 usability patch**: guided landing, a blank
CSV template, declared upload origin, file-removal/origin invalidation and a
current-fit report gate. No model equations/defaults changed. CITATION.cff
continues to cite the archived v0.8.1 release below; no DOI is assigned to this
development snapshot. Local development checks: 158 tests passed in 277.10 s;
Ruff, strict docs, citation schema and development build/Twine checks passed.
See VERIFICATION.md for scope.

The [v0.8.1 GitHub ALPHA pre-release](https://github.com/ysmhla/alga-twin/releases/tag/v0.8.1)
is published from f2db7f8ebd4c3d000e2441094f5f2934ec90dd2d with four verified assets.
Its exact-source scientific, distribution and docs CI passed; see VERIFICATION.md.
[Zenodo v0.8.1 archive](https://zenodo.org/records/23665342) is published with
verified version DOI **10.5281/zenodo.23665342** (MIT; four matching files).
Human scholarly review remains pending.

v0.8.1 passed 156 local tests/Ruff and current-source cloud checks:
Python 3.12 156 tests/Ruff and both tutorials; Python 3.11 145 tests/one optional
skip/Ruff. Distribution/citation/installed-wheel checks passed on both Python
versions; strict docs builds passed. Exact source:
2b303b502f9c7236c7cdfa6961d83ee6279c4979. See VERIFICATION.md for CI links and scope.
The compatible-import fix requires no service reboot. Live v0.8.1 comparison, ranking and actual JSON exports were checked in a fresh
session; the public docs site is deployed at https://ysmhla.github.io/alga-twin/ .
See smoke/v0_8_1/README.md for source and screenshots. Package/docs/citation/paper
preparation and Zenodo software publication are complete; final paper author/
related-work review and any PyPI account publication remain pending.

Step 6 passed 155 local tests/Ruff plus cloud CI 40244015427: Python 3.12
155 tests and both real-kernel tutorials; Python 3.11 144 tests/one optional skip.
Exact source: af118784d1bf8bba824f8a2ab7f81faf1edd3e8c. The initial cached-import rollout issue is fixed in v0.8.1. See DECISION_SUPPORT.md for the new conditional methods.

Steps 1–7 engineering deliverables are implemented (7/7 engineering packages),
including the archived software release and unsubmitted paper draft. This counts
implementation, not all scientific/human acceptance criteria or a PyPI upload.
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
- SOFTWARE PUBLISHED: GitHub ALPHA release and Zenodo version DOI; docs live.
- PUBLICATION PENDING: optional PyPI upload and final paper author/related-work review/submission.
- NOT BUILT: optional MCMC or streaming estimator (deferred until suitable independent data).
