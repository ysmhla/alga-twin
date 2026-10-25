# Release status — v0.3.0 (2026-10-25)

Step 1 engineering is implemented: parameter records, unit/mass-basis guards,
C. minutissima catalogue, explicit DEMO gate, linear/sublinear extinction,
user optical-fit helper, provenance UI/exports and override warnings.

No verified minutissima parameter ranges were established in the audited papers.
Research simulation remains blocked for the incomplete literature preset.
Missing parameters and f_C are unset; source points do not become arbitrary ranges.

Local verification: 62 tests passed; Ruff lint and format checks passed. Cloud CI passed on Python 3.11 and 3.12, with 62 tests and Ruff lint on each:
https://github.com/ysmhla/alga-twin/actions/runs/40182152435. See VERIFICATION.md for exact limits and commands.

- NOT DEPLOYED: hosted app. Streamlit sign-in/terms remain pending.
- NOT TESTED: visual browser layout and Docker build/run.
- NOT VALIDATED: independent cultivation/optical data.
- NOT BUILT: selectable Droop/Haldane/CTMI growth models, joint calibration,
  profile likelihood, benchmark suite, experiment recommendation, tutorial/report
  workflows and publication package. See RESEARCH_ROADMAP.md.
