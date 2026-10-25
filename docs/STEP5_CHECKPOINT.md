# Step 5 recovery checkpoint — incomplete

This draft preserves recoverable API work after the execution workspace became
unavailable before publishing the full local Step 5 implementation. It is not a
v0.7 release. Main remains at 7dcc1a301ba1728e01619c3cc5a48c1bb591aff3 (v0.6).

## Saved in this draft

- biomass_calibration.py: paired OD/cell-count -> DW linear/quadratic OLS,
  explicit units/species/conditions/origin, residuals and in-sample R-squared;
  extrapolation, unsupported units and nonphysical fits refuse.
- wizard_data.py: wide CSV -> canonical long observations; explicit hour/day,
  DW and elemental-N conversions; technical ids preserved; no time-zero shift.
- Six synthetic tests: recovery, zero-curvature limit, unit invariance/total-DW
  preservation, extrapolation/nonphysical/insufficient-data refusals and mapping.
- MODEL.md equations/units/limits updated. No growth ODE/defaults changed.

These modules/tests were reconstructed from the session implementation and are
not claimed to be a byte-for-byte copy of the former tested local tree. Current
draft CI must certify this exact source independently. README/VERIFICATION must
distinguish that evidence from historical v0.6 and lost-workspace results.

## Local work before the connection was lost

The prior local Step 5 tree additionally included:
biomass_ui.py, wizard_ui.py, fit_report.py, app.py navigation integration,
test_guided_ui.py, test_fit_reports.py, two tutorial notebooks, an execution
runner, HTML/PDF/JSON worked reports and updated docs/dependencies/version.

Observed before workspace loss: 143 full local tests passed in 192.33 seconds;
21 targeted checks passed in 53.17 seconds; Ruff lint/format, compileall and pip
check passed. Both SYNTHETIC notebooks ran all 4 + 6 code cells using an explicit
IPython in-process fallback because Jupyter TCP/IPC sockets were refused.
The seven-page PDF report was rendered/reviewed after embedding fonts to fix
spacing. None of those counts certifies this reconstructed draft. The additional
files/artifacts have not been retrieved or published here, and no working links
to them are claimed.

Original unavailable workspace:
  /workspace/scratch/04308460497f/project/alga-twin

If it becomes available, recover its files and inspect its uncommitted changes
before overwriting anything. Compare the recovered core modules/tests against
this draft, restore the UI/report/tutorial/docs work, rerun pytest and Ruff,
execute notebooks, review reports, then publish/verify cloud checks. Do not infer
a release from the previous local pass.

## Scientific and user acceptance still pending

No executable VERIFIED-range C. minutissima preset is established. Extinction,
f_C and missing biological parameters remain unset. No other species values may
be transplanted. Only explicitly SYNTHETIC teaching fixtures are present.

The core APIs are not yet wired into the app in this draft. User-facing wizard,
reports and tutorials must be recovered/recreated and reverified before those
features can be reported as delivered.

Hosted demo: NOT DEPLOYED. Actual app screenshots/pixel review: NOT TESTED.
Novice <5-minute completion and five observed human usability issues: NOT TESTED.
Engineering review findings are not human observations. Independent biological
validation/empirical interval coverage: NOT ESTABLISHED. Candidate measured
datasets and reuse/redistribution evidence remain human inputs.

## Verification of the current draft

PENDING at checkpoint creation; record exact cloud run/source before claiming
a pass. Historical v0.6 records describe their specified source commit only.
