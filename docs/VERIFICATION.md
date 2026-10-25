# Verification record — v0.4.0, 2026-10-25

## Current implementation

| Check | Result | Evidence and scope |
|---|---|---|
| Local pytest, Python 3.12 | PASS: 100 tests | Full suite; 26.84 s; synthetic scientific cases and real Streamlit AppTest |
| Ruff lint/format and compileall | PASS | ruff check; ruff format --check (25 files); compileall src app.py tests |
| Selectable model checks | PASS | tests/test_model_families.py: baseline regression, units, quota equilibrium, N ledger, positivity, light/temperature/diurnal limits, Eq. 9 discrepancy |
| Real Streamlit workflows | PASS | tests/test_streamlit_runtime.py includes new synthetic model workspace |
| Current cloud CI, Python 3.11 / 3.12 | PASS: 100 tests and Ruff each | [Run 40197007799](https://github.com/ysmhla/alga-twin/actions/runs/40197007799); source commit 8bf5527a21491ee6a636bf94f2dcf38e41f0ffee; pytest 26.47 s / 21.38 s; compilation and import checks passed |
| Hosted deployment | NOT DEPLOYED | No public app URL |
| Visual browser verification | NOT TESTED | AppTest is not pixel/browser verification |
| Docker build/run | NOT TESTED | No build/run claim |
| Independent laboratory/optical validation | NOT VALIDATED | Recovery uses explicitly synthetic data only |

## Reproduce

    python -m pip install -r requirements.txt -e '.[dev]'
    python -m pytest -q
    python -m ruff check src app.py tests
    python -m ruff format --check src app.py tests
    python -m compileall -q src app.py tests

No pixel-level usability, <5-minute completion, independent prediction accuracy,
confidence intervals or novel-method claims are made. Streamlit >=1.50 is
required; no deprecated use_container_width arguments remain. New model fitting,
profiles, independent cross-validation and formal model support remain pending.

## Historical evidence

v0.3.0 passed 62 tests and Ruff on Python 3.11/3.12 in
https://github.com/ysmhla/alga-twin/actions/runs/40182152435,
source commit 6746dde6bf07151c75511731c5f9eb17e296935b.
v0.2.1 passed 34 tests on cloud Python 3.11/3.12 in
https://github.com/ysmhla/alga-twin/actions/runs/40177389592.
The old local HTTP health check applied to v0.2.1, not proof of hosting.
