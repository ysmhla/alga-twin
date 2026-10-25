# Research-grade roadmap — C. minutissima

Progress counts completed work packages, not elapsed effort or scientific validation.

| Group | Scope | Status |
|---|---|---|
| 1 | Parameter evidence, basis/units, extinction and provenance UI | Implemented; source coverage incomplete and explicit |
| 2 | Shared model interface; Droop, Haldane/Han, CTMI, diurnal light | Implemented in synthetic workspace; no independent biological validation |
| 3 | Multi-run error models, profiles/identifiability and held-out evaluation | Implemented; 119 tests/Ruff passed locally and cloud Python 3.11/3.12; conditional intervals and synthetic holdouts only |
| 4 | Licensed candidate datasets, PEtab/pyPESTO benchmark/scoreboard | Pipeline implemented; full verification in progress; measured datasets pending human input |
| 5 | OD calibration, wizard, reports, tutorials, observed usability, hosting | Pending; width deprecations fixed only |
| 6 | Information-based experiment ranking and supported model selection | Pending |
| 7 | Packaging/publication, docs site, DOI and honest JOSS draft | Pending |

Steps 1–3 locally/cloud verified; Step 4 pipeline implemented with final checks pending. Step 1: source audit, parameter dataclass, optical model/helper, provenance UI and
local verification are implemented. A full species-specific parameter set and
reported ranges are NOT established. LITERATURE simulation is blocked rather
than silently importing another species or synthetic values. Tests are synthetic
and independent laboratory validation remains absent.

Any future model change must update MODEL.md and add unit, limiting-case and
mass-balance tests. README must agree with VERIFICATION.md. Run pytest and Ruff
before reporting completion. No inferred source values, unlicensed digitisation,
novelty claim or interval without a method. Streaming estimators stay deferred
until suitable independent data exist.
