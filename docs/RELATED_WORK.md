# Related work — HUMAN REVIEW PENDING

This table has **not been checked by the human researcher**. No first-of-kind,
novelty, superiority or completeness claim is made. Documentation was read for
the scope below; these are not head-to-head performance experiments. Absence
of a feature from this table does not mean the other tool lacks it.

| Tool / source | Scope read from primary documentation | Relationship to AlgaTwin | Evidence / limit |
|---|---|---|---|
| [pyFOOMB](https://github.com/MicroPhen/pyFOOMB) | Python bioprocess framework; Assimulo/CVode integration, pygmo calibration and worked notebooks | A general framework to assess before maintaining a separate engine | Author README reread 2026-10-26; no comparative execution |
| [pyPESTO](https://pypesto.readthedocs.io/en/latest/) | Parameter estimation toolbox; optimization, profiling and sampling interfaces | Optional benchmark integration actually uses pyPESTO 0.7.0 for full-data profiles; native gates/CV remain explicit | Official docs plus executed repository benchmark; not a speed comparison |
| [PEtab](https://petab.readthedocs.io/en/latest/) | Shared parameter-estimation problem specification; version 2 supports non-SBML model formats | AlgaTwin exports PEtab 2 native-model problems with an explicit reader; generic SBML/AMICI import not claimed | Official format docs plus actual libpetab checks |
| [NLoed](https://github.com/ingallslab/NLoed) | Nonlinear expected-Fisher experimental design, fitting and diagnostic tools using CasADi | AlgaTwin currently ranks supplied candidate runs with finite differences and a profile-supported plug-in fit; this is a narrower implementation | Author README read; not executed; full primary article was access-blocked in this session |
| [PEtab Select](https://petab-select.readthedocs.io/en/latest/) | Model-space formats, Python/CLI search; AIC/AICc/BIC; calibration delegated to external tools | A relevant model-selection integration candidate; AlgaTwin currently compares a small explicit same-data set with its own profile gates | Official introduction read 2026-10-26; not installed or benchmarked here |
| [REALM raceway model](https://zenodo.org/records/15579693), [DOI 10.5281/zenodo.15579693](https://doi.org/10.5281/zenodo.15579693), v1 | MATLAB mechanistic raceway simulator; biological, engineering mass-balance and thermal components; weather inputs | An algal-process comparator with broader stated physical scope than this reduced batch prototype | Author-deposited description read 2026-10-26; files not downloaded/executed; licence UNVERIFIED because the retrieved Rights section did not expose a value |
| AlgaTwin | Audited C. minutissima catalogue, provenance/units, constrained batch models, conditional calibration and reports | Narrow application workflow and transparent refusals; comparative necessity and novelty remain for human review | SYNTHETIC engineering evidence only; measured benchmarks and novice study pending |

Review required: verify scope/version statements, add omitted comparable algal
and bioprocess software, decide whether extending an existing framework is more
appropriate, and assess any scholarly contribution only after evidence exists.
The prototype's implemented components alone do not establish research novelty.

## Agent source audit — 2026-10-26

The sources above were checked as documentation, not as human approval or a
systematic review. The pyPESTO documentation actually displays version 0.7.0;
its pinned `/en/v0.7.0/` URL was inaccessible, so the read source is the official
`/en/latest/` page displaying that version. PEtab explicitly documents version 2
support for non-SBML formats. The NLoed README also describes profile likelihood,
identifiability diagnostics and prediction uncertainty; those existing methods
must not be claimed as AlgaTwin inventions. No method or parameter was imported
from REALM, and no data licence was inferred from its public availability.

**Engineering assessment (inference):** the defensible scope is a narrow
microalgal evidence/unit workflow and transparent reporting. Existing estimation,
experimental-design and model-selection projects merit integration assessment.
Whether this warrants a separate scholarly software contribution is unresolved;
neither this source audit nor an agent walkthrough satisfies the requested human
related-work check or demonstrates superiority.
