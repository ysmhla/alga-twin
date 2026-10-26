# Research-grade roadmap — C. minutissima

Progress counts completed work packages, not elapsed effort or scientific validation.

| Group | Scope | Status |
|---|---|---|
| 1 | Parameter evidence, basis/units, extinction and provenance UI | Implemented; source coverage incomplete and explicit |
| 2 | Shared model interface; Droop, Haldane/Han, CTMI, diurnal light | Implemented in synthetic workspace; no independent biological validation |
| 3 | Multi-run error models, profiles/identifiability and held-out evaluation | Implemented; 119 tests/Ruff passed locally and cloud Python 3.11/3.12; conditional intervals and synthetic holdouts only |
| 4 | Licensed candidate datasets, PEtab/pyPESTO benchmark/scoreboard | Pipeline verified: 130 local/cloud Python 3.12 tests + Ruff; measured datasets pending human input |
| 5 | OD calibration, wizard, reports, tutorials, observed usability, hosting | Software/hosting implemented; public demo, actual app screenshots and SYNTHETIC browser exports checked. Development agent review fixes and actual CSV-to-report/3-fold export rehearsal recorded separately. Human novice timing/five observed issues NOT TESTED |
| 6 | Information-based experiment ranking and supported model selection | Implemented locally; 155 local/cloud Python 3.12 tests/Ruff and both tutorials passed; Python 3.11 144/one skip; live v0.8.1 model comparison/ranking/export smoke passed |
| 7 | Packaging/publication, docs site, DOI and honest JOSS draft | GitHub v0.8.1 ALPHA pre-release published with verified assets; package/docs/citation/paper artifacts implemented; 156 local/cloud Python 3.12 tests plus Python 3.11 core, distribution and strict docs CI passed; public docs and live app smoke passed; Zenodo archive/version DOI 10.5281/zenodo.23665342 published; human paper metadata/review pending |

Steps 1–7 engineering deliverables implemented (7/7 engineering packages), including
GitHub/Zenodo software publication and an unsubmitted paper draft. This count does not
claim all acceptance criteria: Step 5 human novice timing/five observed issues are
still NOT TESTED, and measured-data evaluation remains pending human inputs. Step 1: source audit, parameter dataclass, optical model/helper, provenance UI and
local verification are implemented. A full species-specific parameter set and
reported ranges are NOT established. LITERATURE simulation is blocked rather
than silently importing another species or synthetic values. Tests are synthetic
and independent laboratory validation remains absent.

Any future model change must update MODEL.md and add unit, limiting-case and
mass-balance tests. README must agree with VERIFICATION.md. Run pytest and Ruff
before reporting completion. No inferred source values, unlicensed digitisation,
novelty claim or interval without a method. Streaming estimators stay deferred
until suitable independent data exist.
