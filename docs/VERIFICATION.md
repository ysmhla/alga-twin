# Verification record — v0.7.0, 2026-10-26

| Check | Result | Evidence and scope |
|---|---|---|
| Local full pytest, Python 3.12 | PASS: 143 tests | 192.33 s; includes optional benchmark toolchain and actual Streamlit AppTest |
| Ruff lint/format, compileall, pip check | PASS | Current source; tutorials runner included in lint/format; no broken requirements |
| Targeted wizard/proxy/report/existing UI checks | PASS: 21 tests | 53.17 s; column/unit refusals, profile export gate, six-step navigation and stale-state handling |
| Proxy observation model | VERIFIED NUMERICALLY ONLY | Linear/quadratic recovery, zero-curvature limit, cell/DW units, mass conversion, extrapolation/nonphysical refusal |
| Tutorials | EXECUTED IN-PROCESS | Both SYNTHETIC notebooks, 4 + 6 code cells, IPython; PNG plot and actual fit/CV/report outputs saved |
| Real Jupyter kernel locally | UNAVAILABLE | TCP/IPC socket binding refused by environment; no local kernel-run claim |
| HTML/PDF/JSON report | GENERATED | Actual SYNTHETIC shared fit, all 3/3 synthetic CV folds scored; PDF seven pages rendered/visually inspected |
| Streamlit browser screenshot / pixel review | NOT TESTED | Browser cannot connect to local app; local-file browser preview prohibited; AppTest is not pixel review |
| Current cloud Python 3.11/3.12 | PENDING | Source not yet certified by current cloud run; historical v0.6 evidence below |
| Hosted deployment | NOT DEPLOYED | Account setup/sign-in/terms pending; no public app URL |
| Timed novice study / five observed human issues | NOT TESTED | Engineering findings/fixes are labelled separately in USABILITY.md |
| Independent biological evaluation | NOT VALIDATED | Only synthetic inference/held-out checks; measured datasets pending human input |
| Empirical interval coverage | NOT ESTABLISHED | Conditional marginal asymptotic profile intervals; proxy conversion uncertainty not propagated |

No dynamics were changed. MODEL.md adds empirical observation equations/units and
mapping/report assumptions; new unit, limiting-case and total-DW conversion tests
complement existing Monod/Droop nitrogen balances. No complete VERIFIED-range
C. minutissima preset is invented; missing biological inputs, extinction and f_C
stay unset. Unknown-strain inputs require explicit user evidence.

## Reproduce

Full benchmark checks require Python 3.12+; app/CLI still support Python 3.11:

    python3.12 -m pip install -r requirements.txt -e '.[dev,benchmark,tutorials]'
    python3.12 -m pytest -q
    python3.12 -m ruff check src app.py tests benchmark tutorials/execute_tutorials.py
    python3.12 -m ruff format --check src app.py tests benchmark tutorials/execute_tutorials.py
    python3.12 -m compileall -q src app.py tests benchmark tutorials/execute_tutorials.py
    python3.12 -m pip check
    python3.12 tutorials/execute_tutorials.py

Use `--in-process` only when kernel sockets are unavailable; the output metadata
records that method. Both committed notebooks use this explicit local fallback.
The current Python 3.12 CI includes a real kernel tutorial execution step; its
result will be recorded only after observed completion. Formats require the
explicit native PEtab reader; stock SBML/AMICI interoperability is not claimed.
PEtab 0.9 requires Python 3.12; its optional module skips on core Python 3.11.

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
