# Release status — v0.6.0 (2026-10-25)

Steps 1–3 remain implemented. Step 4 benchmark engineering is implemented;
final full local/cloud checks are in progress. Metadata/licence/units/hash
loaders, a labelled synthetic fixture, PEtab 2 native-model exchange,
actual pyPESTO full-data profiles and licence-bearing split scoreboards run.
Native SciPy gates/whole-run CV remain the reported inference engine.
The recorded synthetic run has three runs, 48 measurements, 13 external
profile points, zero PEtab format issues and 3/3 held-out folds scored.
See benchmark/README.md and docs/VERIFICATION.md for scope/evidence.

The optional PEtab 0.9 benchmark toolchain requires Python 3.12+; core app/CLI
remain Python 3.11 compatible. Native exports require the explicit reader;
stock from_yaml/SBML/AMICI compatibility is NOT IMPLEMENTED. Source DOI
syntax and provider licence records are not independent verification of
ownership or scientific validity. No measured dataset is present.

C. minutissima missing parameters/f_C stay unset. All example biological
parameters and data remain SYNTHETIC / UNVERIFIED, with no invented range/DOI.
Conditional profile intervals do not establish empirical coverage.

- PENDING HUMAN INPUT: measured candidate datasets and recorded reuse/redistribution permission.
- NOT VALIDATED: independent cultivation/optical predictions.
- NOT DEPLOYED: hosted app; sign-in/terms remain pending.
- NOT TESTED: pixel review, timed novice studies and Docker build/run.
- NOT BUILT: supported model selection, information-based experiment recommender,
  OD calibration/full wizard, HTML/PDF reports, tutorials/observed usability,
  publication/DOI/docs-site package and optional MCMC.
