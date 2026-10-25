# Release status — v0.5.0 (2026-10-25)

Steps 1–3 engineering are implemented. Local v0.5 verification passed: 119 tests,
Ruff lint/format and compileall. Current cloud CI is pending.
Source evidence/units, optical helper and selectable models remain in place.
Calibration now shares selected parameters across runs, preserves technical
replicates, supports additive/log-normal errors with explicit SDs, computes
nuisance-reoptimized profiles and withholds unsupported estimates/intervals.
The baseline UI/CLI uses the same gate. Whole-run holdouts refit/reprofile
training data, with separate in-sample/held-out metrics and failed-fold reasons.
Explicit JSON jobs/long CSV, joint Streamlit workspace and fit-joint CLI run.
See MODEL.md, CALIBRATION.md and VERIFICATION.md for assumptions and checks.

Missing C. minutissima values/f_C remain unset; no species range is invented.
All provided example data/biological parameters are SYNTHETIC / UNVERIFIED.
Optional log-N integration preserves near-depletion likelihoods without adding
pseudocounts. Named marginal asymptotic intervals do not establish empirical
coverage or independent biological validation.

- NOT DEPLOYED: hosted app; sign-in/terms remain pending.
- NOT TESTED: visual browser layout, timed novice studies and Docker build/run.
- NOT VALIDATED: independent cultivation/optical data.
- NOT BUILT: licensed benchmark/PEtab pipeline, supported model comparison,
  information-based experiment recommender, OD calibration/full wizard,
  HTML/PDF reports, tutorials/observed usability and publication package.
- Optional MCMC, detection-limit/correlated-error models: NOT BUILT.
