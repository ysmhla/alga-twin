# Hosted browser smoke evidence — 2026-10-26

Licence: MIT, repository LICENSE (copied as LICENCE.txt). All growth observations,
paired conversions and reports here are **SYNTHETIC / UNVERIFIED teaching fixtures**.
No empirical dataset was uploaded, fabricated as measured, downloaded or digitised.

Public URL observed: https://alga-twin.streamlit.app/
Sharing setting observed: **This app is public and searchable**.
Initial smoke source: 0b1090d45c2741996e66047058d7b73c1957b945, version 0.7.0.
Runtime after selecting/rebuilding: Python 3.12.15, Streamlit 1.66.1. The provider
replaced PyArrow 26 with 24 during its build. Settings and rebuilt logs both
confirmed Python 3.12. Initial automatic provisioning briefly used 3.14 before
this change; smoke evidence below was collected after the 3.12 rebuild.

## Observed browser checks

| Check | Observed result |
|---|---|
| Startup/literature gate | v0.7.0 app loaded; C. minutissima gaps stayed None/NO_SPECIES_DATA; no silent DEMO simulation |
| Paired-DW helper | Default upload prompt; explicitly selected SYNTHETIC example fitted; residuals, plot and in-sample R-squared displayed |
| Extrapolation | 1.1 refused outside the fixture's measured signal domain [0.1,1.0]; this is not a species range |
| Conversion export | Actual JSON download parsed: SYNTHETIC, UNVERIFIED, g_DW/L, no interval, OLS method |
| Guided worked example | Explicit SYNTHETIC selection -> column/unit mapping -> confirmation -> explicit assumptions -> shared fit/profile -> result |
| Whole-run holdouts | Three SYNTHETIC cultures/48 observations; all three training profile gates supported scoring; split labels retained |
| Report exports | Actual HTML, PDF and JSON downloaded; origins/methods/provenance checked; PDF first page rendered/visually reviewed |
| Baseline zero-light limit | DEMO scenario at zero light/zero loss exported 145 rows with X=0.1 g DW/L and N=70 mg N/L constant; these are teaching values, not species parameters |
| Stale output | Revisited model step, then result; old PDF button absent until a current model/fit exists |
| Invalid upload | An explicitly invalid, non-measurement software fixture was refused with a clear distinct-column mapping error; no simulation fallback |
| Public visibility | App settings explicitly reported public/searchable; no permission change or email invitation was made |
| Console scope | No Streamlit deprecation in retained 40 warning/error entries; those entries were browser-extension metadata errors |

[Machine evidence / hashes](browser_evidence.json), [actual HTML export](live_synthetic_report.html),
[actual PDF export](live_synthetic_report.pdf), [actual JSON export](live_synthetic_report.json).
PDF table values are rounded; JSON retains full values. Named conditional marginal
asymptotic profile intervals have no established empirical coverage. Synthetic
held-out errors are engineering checks, not independent biological validation.

Screenshots: [literature gate](https://github.com/ysmhla/alga-twin/blob/main/assets/screenshots/literature-gate.jpg),
[proxy refusal](https://github.com/ysmhla/alga-twin/blob/main/assets/screenshots/proxy-extrapolation-refused.jpg),
[guided result](https://github.com/ysmhla/alga-twin/blob/main/assets/screenshots/guided-result.jpg),
[invalid upload](https://github.com/ysmhla/alga-twin/blob/main/assets/screenshots/invalid-upload-refused.jpg).
These are actual app captures; assets/report-preview.png is only a PDF preview.

A browser review found that the method column could fall beyond horizontal
scrolling. The v0.7.1 UI patch also displays the complete method/confidence above
all fit-result tables; its source/tests are tracked in VERIFICATION.md. It does
not change equations, parameters, likelihood or the exported numerical report.
After rollout/restart, the public app displayed v0.7.1; a fresh SYNTHETIC wizard
fit completed and the full method/95% confidence caption was visibly verified.
[Updated live caption capture](https://github.com/ysmhla/alga-twin/blob/main/assets/screenshots/interval-method-visible.jpg).
This phase is recorded separately in browser_evidence.json; original 3/3 CV
exports above retain their actual v0.7.0 provenance.

## Not established by this test

This was an agent-operated software smoke test. It is not a new-human <5-minute
upload-to-report study and provides no five observed human issues. The worked
example does not exercise an actual measured-data upload. Mobile layout, Docker,
independent biological validation, empirical interval coverage and proxy-error
propagation remain untested/unestablished. See ../USABILITY.md for the human
study protocol. No novelty or scientifically validated operational recommendation
is claimed.
