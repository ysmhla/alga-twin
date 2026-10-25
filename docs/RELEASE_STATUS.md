# Release status — v0.7.0 (2026-10-26)

Steps 1–4 engineering are implemented. Step 5 core UI is implemented and locally
checked: paired OD/cell-count -> DW OLS; six-step upload/mapping/units/model/fit/
report workflow; blank unknown-strain inputs; profile-gated HTML/PDF/JSON reports;
two executed SYNTHETIC tutorials. Local Python 3.12 passed 143 tests (195.43 s),
Ruff lint/format, compilation and pip check. Targeted UI/report checks: 21 passed.
Cloud Python 3.12 passed 143 tests/Ruff (203.89 s) and both real-kernel notebooks;
Python 3.11 passed 132 tests, 1 optional benchmark skip and Ruff (117.21 s).
CI: https://github.com/ysmhla/alga-twin/actions/runs/40222521288; source
edc3ffc4ecaa95a0628f6a0a27d58d6018945ea2. See VERIFICATION.md for exact evidence.

Committed tutorial outputs use an explicit IPython in-process fallback because
local Jupyter TCP/IPC sockets were refused. The cloud CI separately executed both
notebooks with real Jupyter kernels successfully; no local kernel-run claim.
PDF seven-page report was rendered/reviewed. Streamlit AppTest is actual widget
verification, not browser pixel review or a human usability study. Report proxy
uncertainty is not propagated into conditional growth-profile intervals.

The observed hosting page requires sign-in/Terms of Service acceptance; the
account holder must complete that step. assets/hosting-pending.jpg is evidence
of this prerequisite, not an app screenshot or deployment proof.

Step 5 acceptance is incomplete: public app hosting/account setup, app browser
screenshots, <5-minute novice completion and five actually observed human issues
are pending. USABILITY.md records five engineering findings/fixes separately.
No fabricated timing, participant feedback or validation claim is made.

- PENDING HUMAN INPUT: measured candidate datasets and reuse/redistribution evidence.
- NOT VALIDATED: independent cultivation/optical predictions or interval coverage.
- NOT DEPLOYED: hosted app; account setup/sign-in/terms remain pending.
- NOT TESTED: Streamlit pixel/mobile review, timed novice study and Docker build/run.
- NOT BUILT: supported model selection, information-based experiment recommender,
  publication/DOI/docs-site release, optional MCMC and streaming state estimation.

C. minutissima verified-range coverage is incomplete; extinction/f_C remain unset.
No other species parameters are transplanted. Example biological values and data
are SYNTHETIC / UNVERIFIED. Previous benchmark artifacts retain their v0.6 version;
PEtab 0.9 extra requires Python 3.12 and the explicit native reader. Generic
SBML/AMICI compatibility and pyPESTO-based CV are not claimed.
