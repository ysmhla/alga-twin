# Executable SYNTHETIC tutorials

Licence: **MIT**, repository [LICENSE](../LICENSE). All paired observations,
relationships and growth observations in these notebooks are **SYNTHETIC /
UNVERIFIED teaching fixtures**, not C. minutissima data. No external dataset is
downloaded/digitised; no DOI is assigned to these fixtures.

1. [OD/cell count -> dry weight](01_proxy_to_dry_weight.ipynb): explicit units,
   linear/quadratic OLS, residuals, in-sample R-squared and extrapolation refusal.
2. [Upload -> profiled report](02_upload_to_profiled_report.ipynb): column mapping,
   shared-parameter fitting, named conditional profile intervals, whole-run
   synthetic holdouts and HTML/PDF/JSON export.

    pip install -e '.[tutorials,reports]'
    python tutorials/execute_tutorials.py

The runner uses the invoking Python, not a silently selected system kernel.
On Unix a local `--transport ipc` option is available. In socket-restricted
environments use `--in-process`; it executes all code cells with IPython and
records that method in notebook metadata, rather than claiming a Jupyter kernel
run. Current committed outputs were executed using that explicit fallback.
The CI Python 3.12 tutorial step executed both notebooks with real Jupyter
kernels successfully in current v0.7.1 run 40240500191 (previous v0.7.0 run 40222521288 also passed); committed outputs retain the local
in-process method metadata.

Actual worked-example artifacts (SYNTHETIC):
[HTML report](output/synthetic_report.html), [PDF report](output/synthetic_report.pdf),
[complete evidence JSON](output/synthetic_report.json). Numerical intervals are
conditional asymptotic profiles, not calibrated empirical coverage; held-out
errors use synthetic cultures, not independent biological validation. PDF values
are rounded for layout; JSON retains full numerical evidence.

The second notebook also writes the exact SYNTHETIC wide/long CSV inputs and
explicit job JSON beside the reports. They have the same MIT licence/origin;
no candidate biological dataset is introduced.
