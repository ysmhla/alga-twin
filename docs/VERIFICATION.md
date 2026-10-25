# Verification record — v0.3.0, 2026-10-25

## Current implementation

| Check | Result | Evidence and scope |
|---|---|---|
| Local pytest, Python 3.12 | PASS: 62 tests | Includes the original scientific workflows, explicit synthetic configurations and optical cases |
| Parameter/unit evidence tests | PASS | tests/test_parameters_optics.py: statuses, missing species data, bases/units, f_C, overrides, synthetic recovery and failure cases |
| Optical model limiting/conservation cases | PASS | s=1/s=0.5: zero light, clear medium, zero biomass, conserved X+Y*N/1000, monotonic N and positivity |
| Real Streamlit workflows | PASS | tests/test_streamlit_runtime.py: LITERATURE gate, explicit DEMO, provenance, sublinear UI, calibration, scenario snapshots and planner invalidation |
| Ruff lint | PASS | ruff check src app.py tests |
| Ruff formatting | PASS | ruff format --check src app.py tests |
| Current cloud CI | PENDING | The v0.2.1 result does not certify v0.3 |
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

Streamlit 1.66.1, Plotly 6.9.0 and Ruff 0.17.2 were used locally. Deprecated
use_container_width arguments were replaced by width="stretch"; Streamlit >=1.50
is required. No pixel-level usability, <5-minute completion, independent prediction
accuracy, confidence intervals or novel-method claims are made.

## Historical evidence

v0.2.1 passed 34 tests on cloud Python 3.11 and 3.12 in
https://github.com/ysmhla/alga-twin/actions/runs/40177389592.
The old local HTTP health check also applied to v0.2.1, not proof of hosting.
