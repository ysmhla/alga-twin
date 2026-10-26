# Related work — HUMAN REVIEW PENDING

This table has **not been checked by the human researcher**. No first-of-kind,
novelty, superiority or completeness claim is made. Documentation was read for
the scope below; these are not head-to-head performance experiments. Absence
of a feature from this table does not mean the other tool lacks it.

| Tool / source | Scope read from primary documentation | Relationship to AlgaTwin | Evidence / limit |
|---|---|---|---|
| [pyFOOMB](https://github.com/MicroPhen/pyFOOMB) | Object-oriented programmatic bioprocess modelling and calibration | A relevant general bioprocess framework; assess contribution/integration before asserting a need for a separate tool | Author repository/README; not run in this project |
| [pyPESTO](https://pypesto.readthedocs.io/en/latest/) | Parameter estimation toolbox; optimization, profiling and sampling interfaces | Optional benchmark integration actually uses pyPESTO 0.7.0 for full-data profiles; native gates/CV remain explicit | Official docs plus executed repository benchmark; not a speed comparison |
| [PEtab](https://petab.readthedocs.io/en/latest/) | Shared parameter-estimation problem specification; version 2 supports non-SBML model formats | AlgaTwin exports PEtab 2 native-model problems with an explicit reader; generic SBML/AMICI import not claimed | Official format docs plus actual libpetab checks |
| [NLoed](https://github.com/ingallslab/NLoed) | Nonlinear expected-Fisher experimental design, fitting and diagnostic tools using CasADi | AlgaTwin currently ranks supplied candidate runs with finite differences and a profile-supported plug-in fit; this is a narrower implementation | Author README read; not executed; full primary article was access-blocked in this session |
| AlgaTwin | Audited C. minutissima catalogue, provenance/units, constrained batch models, conditional calibration and reports | Narrow application workflow and transparent refusals; comparative necessity and novelty remain for human review | SYNTHETIC engineering evidence only; measured benchmarks and novice study pending |

Review required: verify scope/version statements, add omitted comparable algal
and bioprocess software, decide whether extending an existing framework is more
appropriate, and assess any scholarly contribution only after evidence exists.
The prototype's implemented components alone do not establish research novelty.
