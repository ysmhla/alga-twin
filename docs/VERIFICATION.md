# Verification record — v0.6.0, 2026-10-25

## Current implementation

| Check | Result | Evidence and scope |
|---|---|---|
| Local full pytest, Python 3.12 | IN PROGRESS | Final full-suite run pending |
| Ruff lint/format, compileall, pip check | PASS | Current source: all checks passed; no broken requirements |
| Benchmark metadata/licence/units | PASS | Recorded permission, file hashes, bases/species and refusal cases |
| PEtab round-trip / limits / N balance | PASS | Official format validators, likelihood/state/unit preservation, Monod/Droop light/temperature options and dark limit |
| Actual pyPESTO benchmark | EXECUTED, SYNTHETIC ONLY | benchmark/results/synthetic_v0_6: three runs/48 measurements; 13 profile points; NLL difference 9.9476e-13; 3/3 native CV folds scored |
| Benchmark refusal gate | PASS | Unsupported profiles must not produce point estimates or held-out aggregates |
| Current cloud Python 3.11 | NOT YET RUN | Core suite; optional PEtab 0.9 toolchain unavailable on this Python |
| Current cloud Python 3.12 | NOT YET RUN | Full suite with benchmark extra |
| Hosted deployment | NOT DEPLOYED | No public app URL |
| Visual browser/timed novice study | NOT TESTED | AppTest does not establish novice <5-minute usability |
| Independent biological evaluation | NOT VALIDATED | Only synthetic inference/held-out checks |
| Empirical interval coverage | NOT ESTABLISHED | Conditional marginal asymptotic profile intervals |

Current-source targeted benchmark run: **11 tests passed in 49.53 s**, including
PEtab-entry-point permission/unit refusal and flat-profile suppression. The final
full suite and cloud jobs remain pending below.

## Reproduce

Full benchmark checks require Python 3.12+:

    python3.12 -m pip install -r requirements.txt -e '.[dev,benchmark]'
    python3.12 -m pytest -q
    python3.12 -m ruff check src app.py tests benchmark
    python3.12 -m ruff format --check src app.py tests benchmark
    python3.12 -m compileall -q src app.py tests benchmark
    python3.12 -m pip check
    python3.12 benchmark/run_benchmark.py --registry benchmark/registry.json --output /tmp/alga-benchmark

Core app/CLI still support Python 3.11; benchmark tests explicitly skip without
its optional dependencies. Benchmark inference/CV uses the native SciPy profile
gate; external pyPESTO is a full-data profile cross-check, not pyPESTO CV.
The PEtab native reader is required; generic stock from_yaml/SBML/AMICI
compatibility is not claimed. Permission metadata checks do not authenticate
ownership. No measured dataset, biological validation, novelty or empirically
calibrated interval coverage is claimed. MCMC remains optional/unimplemented.

## Historical evidence

v0.5.0 passed 119 tests/Ruff on Python 3.11/3.12:
https://github.com/ysmhla/alga-twin/actions/runs/40207853593;
source commit 53ffe2c117750efa7f8aa86b8e878cbda7f28b97.
v0.4.0 passed 100 tests and Ruff on Python 3.11/3.12:
https://github.com/ysmhla/alga-twin/actions/runs/40197007799;
source commit 8bf5527a21491ee6a636bf94f2dcf38e41f0ffee.
v0.3.0 passed 62 tests and Ruff on Python 3.11/3.12 in
https://github.com/ysmhla/alga-twin/actions/runs/40182152435,
source commit 6746dde6bf07151c75511731c5f9eb17e296935b.
v0.2.1 passed 34 tests on cloud Python 3.11/3.12 in
https://github.com/ysmhla/alga-twin/actions/runs/40177389592.
The old local HTTP health check applied to v0.2.1, not proof of hosting.
