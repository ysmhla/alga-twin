# Verification record — 2026-10-26

## Final usability-patch source — cloud and live retest verified

Exact executable source: **c3bbf121d4ea923fa0073d027f69a059afbc108c**.
[Scientific CI 40342968193](https://github.com/ysmhla/alga-twin/actions/runs/40342968193)
passed Python 3.12 **160 tests in 243.23 s**, Ruff and both real-kernel tutorials;
Python 3.11 **149 passed, 1 skipped in 342.32 s**, Ruff. Distribution/citation/
installed-wheel checks passed in 40342967956; docs build/deploy passed in 40342968057.
The later evidence-only commit changes no executable code or published artifact.

A separate fresh public browser session uploaded the labelled synthetic CSV and
fitted it using this final source. Returning to Step 1 retained the SYNTHETIC
choice and active filename. Clicking the explicit reset, then selecting Step 6,
showed “Start with Step 1” with zero PDF-report controls. [Exact reset evidence](smoke/v0_8_2_dev/reset_evidence.json).
This was not timed and is not substituted for the earlier source-806 rehearsal.
No new human novice or biological acceptance claim follows from either check.

## Return-navigation and explicit reset follow-up

After the browser rehearsal exposed confusing retained-source display on return
to Step 1, the declaration was retained outside temporary widget state, the
active filename was made explicit and a dedicated reset changes the uploader key.
Local Python 3.12 `pytest -q`: **160 passed in 287.20 s**. Repository-wide Ruff
lint/format passed (91 files); no model or likelihood changed. The three reset
regressions exercise native removal, origin relabelling and explicit clearing
independently after an actual fitted synthetic job. The earlier 158-test source
and its browser timing are identified separately below.

## Actual hosted CSV-to-report rehearsal

Source **806212f064cbd6a9f3bfa099a2cd4f39fe18f64c** passed cloud scientific
[CI 40339593674](https://github.com/ysmhla/alga-twin/actions/runs/40339593674):
Python 3.12 **158 passed in 432.02 s**, Ruff and both real-kernel tutorials;
Python 3.11 **147 passed, 1 skipped in 348.81 s**, Ruff. Distribution 40339594065
and docs 40339593518 passed. A fresh public app session displayed 0.8.2.dev0 and
the guided landing. A real file-picker CSV upload, mapping, explicit unit/model
checks, joint fitting, 3/3 whole-run holdouts and HTML/PDF/JSON exports were exercised.
The downloaded reports were parsed for original source hash, SYNTHETIC origins,
DEMO/UNVERIFIED parameters, interval method and training/held-out separation.

Agent interaction time: **192.868 seconds**, with exact start/end/setup and retry
boundaries in [the evidence](smoke/v0_8_2_dev/browser_evidence.json). This is not
an independent human novice result or biological validation. The first JSON
path was unavailable; a separate retry succeeded and was parsed. These observations
must not be attributed to a later source revision without a separate retest.
[Actual reports and screenshots scope](smoke/v0_8_2_dev/README.md).

## Unreleased 0.8.2.dev0 agent usability fixes

Local Python 3.12 `pytest -q`: **158 passed in 277.10 s**. Repository-wide Ruff
lint/format passed (91 files); strict MkDocs, CFF schema, `pip check` and
`git diff --check` passed. A separate development wheel/source build and strict
Twine checks passed; the existing published v0.8.1 distribution files were not
replaced. The release citation/DOI still identify v0.8.1, not this development code.

New actual Streamlit regressions cover the empty guided landing, explicit
uploaded SYNTHETIC origin/DEMO parameter provenance, invalidation after relabelling
or removing the file, and withholding report navigation before a current fit.
The file-uploader return is patched with real CSV bytes in AppTest; this does not
stand in for a browser file-picker test. No model, likelihood or species default
changed. Desktop/source findings and their evidence types are in USABILITY.md;
no human participant, biological dataset or novice timing has been fabricated.

The preceding DOI/docs commit d1aaedf7fe9dd3eb6900bc0b257db225b18b0943 also
completed scientific CI [40332769045](https://github.com/ysmhla/alga-twin/actions/runs/40332769045),
distribution checks 40332769227 and docs deployment 40332768958 successfully.
These are distinct from the local development checks above.

## Post-archive citation/docs and tutorial formatting check

After adding the real archive DOI and formatting only tutorial imports/code
examples, local Python 3.12 `pytest -q` passed **156 tests in 256.23 s**.
`ruff check .` and `ruff format --check .` passed (91 formatted files), as did
CITATION.cff schema validation, `mkdocs build --strict`, `git diff --check` and
`pip check`. No model, likelihood, parameter default or published artifact changed.

Both tutorial notebooks executed through the existing `--in-process` runner
(4 and 6 code cells). A local TCP Jupyter-kernel attempt failed with socket
permission errors; it is not reported as a successful real-kernel run. The
previous release-source cloud real-kernel checks remain recorded below. Generated
report outputs were not substituted for the original checked-in teaching artifacts.

## Published v0.8.1 release source

Release/tag source: f2db7f8ebd4c3d000e2441094f5f2934ec90dd2d.
[Scientific CI 40292325912](https://github.com/ysmhla/alga-twin/actions/runs/40292325912):
Python 3.12 **156 passed in 268.58 s**, Ruff/import/compilation and both real-kernel
tutorials; Python 3.11 **145 passed, one optional skip in 349.82 s**, Ruff/import/compilation.
Distribution/citation/actual installed-wheel checks passed in run 40292325963
on both versions; strict docs build/deployment passed in run 40292325816.

[The public ALPHA pre-release](https://github.com/ysmhla/alga-twin/releases/tag/v0.8.1)
was opened and its four uploaded assets checked. GitHub SHA-256 digests matched
the local wheel, source archive, installed smoke and manifest byte-for-byte.
The tag/source artifacts are retained. Later publication bookkeeping changes no
model or parameter default. The later Zenodo archive is verified below. PyPI
upload and journal submission are absent; human review/metadata/data/usability
requirements remain pending.

## Zenodo archival publication — verified

[Software record 23665342](https://zenodo.org/records/23665342) is published under
MIT, version 0.8.1, creator Ram Yash. The actual downloaded public JSON reports
`is_published: true`, `is_draft: false`, `status: published`; all four file sizes
and MD5 values equal local release files. Version DOI 10.5281/zenodo.23665342 and
concept DOI 10.5281/zenodo.23665341 were followed separately; both resolved to the
published v0.8.1 record. [Exact evidence](smoke/v0_8_1/zenodo_evidence.json).
No published tag/archive was rebuilt or rewritten to insert the later DOI.
CITATION.cff and main-branch publication documentation record the real identifier.
Archival publication supplies no independent biological validation or human
usability evidence.

## v0.8.1 packaging and incremental deployment — verified source

Exact tested source: 2b303b502f9c7236c7cdfa6961d83ee6279c4979.

| Check | Actual result |
|---|---|
| Local Python 3.12 full suite | 156 passed in 626.97 s |
| Local Ruff lint/format, compileall, pip check | PASS |
| Cloud Python 3.12 scientific suite | 156 passed in 239.34 s; Ruff, compilation/import and both real-kernel tutorials PASS |
| Cloud Python 3.11 scientific suite | 145 passed, one optional PEtab skip in 231.51 s; Ruff and compilation/import PASS |
| Cloud distribution checks, Python 3.11/3.12 | PASS: citation schema, wheel/source build, strict Twine, actual wheel install, Monod/Droop N ledger, CLI/refusal and pip check; artifacts uploaded |
| Strict MkDocs cloud/local build | PASS; public site deployed by run 40291099481 |

[Scientific CI 40290016419](https://github.com/ysmhla/alga-twin/actions/runs/40290016419),
[distribution CI 40290016328](https://github.com/ysmhla/alga-twin/actions/runs/40290016328),
[docs build 40290016434](https://github.com/ysmhla/alga-twin/actions/runs/40290016434).
The first distribution run 40289598030 failed correctly: project metadata was
omitted from the initial commit, causing module/wheel versions to differ. The
matching pyproject change is included in the successful exact source above.
Local build/Twine and real installed-wheel checks also passed; no performance
comparison follows from these test durations.

The hosted v0.8 workspace initially failed importing a new name from an already
cached calibration module. A stable independent provenance helper removes that
new-export dependency; a direct source-version import avoids stale header text.
This changes neither likelihood nor growth/nitrogen equations. A subprocess
regression exercises the missing-export scenario with an actual fit. No service
reboot or cache-clearing operation is part of this fix. Live v0.8.1 verification passed in a fresh browser session from merged source
5cd79163d38b505378e992b26e2e2e1add93fd7d. The new workspace loaded, fitted four
SYNTHETIC model candidates and produced top-three Fisher reasons. Actual hosted
JSON exports were downloaded and parsed for version/origin/method/gates; the
dark control had zero information gain. No manual service reboot/cache-clearing
action was performed. The public docs home/navigation loaded after Pages run
40291099481. [Current screenshots and exact exports](smoke/v0_8_1/README.md).
This is agent engineering smoke, not a human novice or biological study.

Step 7 includes modern distribution metadata/manifest, publication CI,
documentation source, schema-valid citation metadata, paper.md/paper.bib and
RELATED_WORK.md. The subsequent Zenodo publication is recorded above. Final paper
author, affiliation/funding and human related-work review remain incomplete. No PyPI
upload, journal acceptance or independent biological validation is claimed.

## v0.8.0 decision support — verified source

Exact tested source: af118784d1bf8bba824f8a2ab7f81faf1edd3e8c.
[Cloud CI 40244015427](https://github.com/ysmhla/alga-twin/actions/runs/40244015427):

| Current source check | Actual result |
|---|---|
| Local Python 3.12 full suite | 155 passed in 215.24 s |
| Local lint/format, compileall, pip check | PASS |
| Cloud Python 3.12 | 155 passed in 422.26 s; Ruff, compilation/import and both real-kernel tutorials PASS |
| Cloud Python 3.11 | 144 passed, one optional PEtab skip in 206.29 s; Ruff and compilation/import PASS |
| New targeted decision tests | 12 passed in 22.71 s, including actual Streamlit state checks |

Worked SYNTHETIC artifacts were actually generated by examples/decision_support.py.
Monod/saturation was conditionally recommended; the alternative Haldane profile
was unsupported and both tested Droop alternatives failed the approximate residual
screen. Fisher ordering among the four explicit choices put higher-light/higher-N
first and the dark control last with zero information gain. These are conditional
teaching results, not species experiments or held-out accuracy.

No measured data, biological defaults or growth RHS changed. See DECISION_SUPPORT.md.
The initial live rollout needed the v0.8.1 compatibility fix; current live evidence is recorded above.

## Previous v0.7.1 patch

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
