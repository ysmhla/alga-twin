# Verification record — 2026-10-26

## Current v0.7.1 patch

UI-only change: the complete profile interval method/confidence remains visible
above result tables, including when the table requires horizontal scrolling.
No growth equation, likelihood, biological default or report computation changed.
Targeted UI checks: **11 passed in 51.69 s**; local Ruff lint/format, compileall
and pip check passed. Full current-source cloud run **40240500191** certifies
3b69d4a56059b8b207f3b8e0f13010ada78f2074:

| Current-source check | Result |
|---|---|
| Cloud Python 3.12 | PASS: 143 tests in 363.57 s; Ruff, compilation/import and both real-kernel tutorials |
| Cloud Python 3.11 | PASS: 132 tests, one optional PEtab skip in 297.51 s; Ruff and compilation/import |
| Actual benchmark-extra installation | PASS with petab 0.9.0 and pypesto 0.7.0; local pip check also passed |

[CI evidence](https://github.com/ysmhla/alga-twin/actions/runs/40240500191).
Durations are the full scientific test suite, not a novice upload-to-report timing.
The first patch run (40240019299) failed before tests during dependency install:
a version edit accidentally changed the pyPESTO pin. Its verified 0.7.0 pin was
restored; the successful exact-source run above supersedes that failed attempt.

## Deployed numerical source / browser evidence

| Check | Observed result / scope |
|---|---|
| Public demo | DEPLOYED: https://alga-twin.streamlit.app/ ; main/app.py; public/searchable setting observed |
| Hosted runtime | Python 3.12.15 / Streamlit 1.66.1 after rebuild; provider replaced PyArrow 26 with 24 |
| Actual app screenshots | CAPTURED: assets/screenshots; desktop literature gate, proxy refusal, guided result |
| Hosted SYNTHETIC fit / CV | Three cultures/48 measurements; 3/3 folds scored; separate training/held-out errors |
| Hosted reports | HTML/PDF/JSON actually downloaded and parsed; hashes in smoke/browser_evidence.json; seven-page PDF all seven pages rendered/reviewed |
| Live refusal/state checks | Paired-DW extrapolation refused; changing model setup withheld old PDF |
| Current local pre-caption full pytest | 143 passed in 192.33 s; unchanged numerical source, full optional benchmark stack |
| v0.7.0 source cloud 3.12 | 143 tests/Ruff (203.89 s) and both real-kernel notebooks; run 40222521288, source edc3ffc4ecaa95a0628f6a0a27d58d6018945ea2 |
| v0.7.0 source cloud 3.11 | 132 tests, one optional PEtab module skip/Ruff (117.21 s), same run |
| Independent novice <5-minute / five observed human issues | NOT TESTED; agent browser checks are not a human study |
| Mobile / measured-CSV browser acceptance | NOT TESTED; file/unit/refusal APIs have automated coverage |
| Independent biological evaluation / empirical coverage | NOT VALIDATED / NOT ESTABLISHED; synthetic evidence only |

[Scoped browser record and actual exports](smoke/README.md). Initial browser
artifacts were captured from 0b1090d45c2741996e66047058d7b73c1957b945 (v0.7.0).
The later caption patch does not alter their numerical computations. A fresh
post-rollout browser session displayed v0.7.1, completed the SYNTHETIC fit and
showed the full method/confidence caption (assets/screenshots/interval-method-visible.jpg). No measured
cultivation data, inferred species ranges, f_C or proxy-uncertainty propagation
is supplied. Method/status/origin and licence fields retain their stated limits.

## Reproduce

    python3.12 -m pip install -r requirements.txt -e '.[dev,benchmark,tutorials]'
    python3.12 -m pytest -q
    python3.12 -m ruff check src app.py tests benchmark tutorials/execute_tutorials.py
    python3.12 -m ruff format --check src app.py tests benchmark tutorials/execute_tutorials.py
    python3.12 -m compileall -q src app.py tests benchmark tutorials/execute_tutorials.py
    python3.12 -m pip check
    python3.12 tutorials/execute_tutorials.py

Python 3.12 is required for the optional PEtab 0.9 benchmark toolchain. Core
app/CLI still support Python 3.11. Native PEtab reader is explicit; generic
SBML/AMICI interoperability is not claimed. Committed tutorial outputs retain
their actual local IPython in-process method; cloud CI separately executed both
with real Jupyter kernels. No local kernel-run or human-usability claim follows.

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


v0.6.0 passed 130 local/cloud Python 3.12 tests and Ruff; Python 3.11 core passed
119 tests, 1 optional benchmark-module skip. Local full run: 384.12 s; CI:
https://github.com/ysmhla/alga-twin/actions/runs/40211930328; source
d5ba18bc3a7cd8a61aff214eede3031c88bdf5e9. Recorded benchmark/results/synthetic_v0_6
contains three runs/48 measurements, 13 external pyPESTO profile points, zero
PEtab format issues and 3/3 native CV folds scored. These artifacts retain their
original v0.6 version; they are not measured biological evidence.
