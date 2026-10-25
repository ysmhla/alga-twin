# Release status — v0.7.0 (2026-10-26)

Steps 1–4 engineering are implemented. Step 5 core UI is implemented and locally
checked: paired OD/cell-count -> DW OLS; six-step upload/mapping/units/model/fit/
report workflow; blank unknown-strain inputs; profile-gated HTML/PDF/JSON reports;
two executed SYNTHETIC tutorials. Local Python 3.12 passed 143 tests (192.33 s),
Ruff lint/format, compilation and pip check. Targeted UI/report checks: 21 passed.
Current cloud certification is pending. See VERIFICATION.md for exact evidence.

Tutorial code cells ran with an explicit IPython in-process fallback because
local Jupyter TCP/IPC sockets were refused; this is not a local kernel-run claim.
PDF seven-page report was rendered/reviewed. Streamlit AppTest is actual widget
verification, not browser pixel review or a human usability study. Report proxy
uncertainty is not propagated into conditional growth-profile intervals.

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
