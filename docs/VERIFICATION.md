# Verification record — v0.5.0, 2026-10-25

## Current implementation

| Check | Result | Evidence and scope |
|---|---|---|
| Local full pytest, Python 3.12 | PASS: 119 tests | Full suite, 265.33 s; synthetic inference/physics and real Streamlit AppTest |
| Ruff lint/format and compileall | PASS | ruff check; ruff format --check (29 files); compileall src app.py tests |
| Joint calibration | PASS | Noisy additive/log-normal recovery, nuisance profiles, flat/sparse/failed cases, confounding and whole-run leakage/refusal tests |
| Log-nitrogen numerical coordinates | PASS | Unit/limiting checks, original-coordinate agreement, Monod/Droop N ledger with/without loss |
| Real Streamlit workflows | PASS | Baseline gate, weak-data refusal and joint profiles/whole-run CV |
| Current cloud Python 3.11/3.12 | NOT YET RUN | Historical checks below do not certify v0.5 |
| Hosted deployment | NOT DEPLOYED | No public app URL |
| Visual browser/usability testing | NOT TESTED | AppTest is not pixel review or a timed novice study |
| Docker build/run | NOT TESTED | No build/run claim |
| Independent biological evaluation | NOT VALIDATED | Recovery and held-out code checks use synthetic data |
| Empirical interval coverage | NOT ESTABLISHED | Named marginal asymptotic profiles condition on specified fixed parameters/SDs |

## Reproduce

    python -m pip install -r requirements.txt -e '.[dev]'
    python -m pytest -q
    python -m ruff check src app.py tests
    python -m ruff format --check src app.py tests
    python -m compileall -q src app.py tests

No novice <5-minute completion, independent biological predictive accuracy,
finite-sample interval coverage or novelty claim is made. Optional MCMC,
censored likelihoods, random culture effects and supported model comparison
remain unimplemented. See CALIBRATION.md for explicit assumptions/refusal rules.
Streamlit >=1.50 is required; deprecated use_container_width is not used.

## Historical evidence

v0.4.0 passed 100 tests and Ruff on Python 3.11/3.12:
https://github.com/ysmhla/alga-twin/actions/runs/40197007799;
source commit 8bf5527a21491ee6a636bf94f2dcf38e41f0ffee.
v0.3.0 passed 62 tests and Ruff on Python 3.11/3.12 in
https://github.com/ysmhla/alga-twin/actions/runs/40182152435,
source commit 6746dde6bf07151c75511731c5f9eb17e296935b.
v0.2.1 passed 34 tests on cloud Python 3.11/3.12 in
https://github.com/ysmhla/alga-twin/actions/runs/40177389592.
The old local HTTP health check applied to v0.2.1, not proof of hosting.
