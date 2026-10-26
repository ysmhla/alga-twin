# AlgaTwin

A Python research prototype for batch microalgal growth, evidence-bearing
parameters, conditional multi-run calibration and experimental design.

**ALPHA — no independent biological validation.** Shipped data and worked
parameter assumptions are SYNTHETIC / UNVERIFIED. Missing *Chlorella minutissima*
parameters remain unset. No other species' extinction values or assumed carbon
fraction are substituted. Do not treat simulations as production reactor advice.

The wheel provides the Python API and `alga-twin` CLI. The Streamlit dashboard,
notebooks, licensed benchmark fixture and full documentation are distributed in
the source archive/repository. Optional tools: `reports`, `tutorials`, `benchmark`
(Python 3.12 required), `app`, `docs` and `dev` extras. Core Python: 3.11+.

- [Source and setup](https://github.com/ysmhla/alga-twin)
- [Public Streamlit demo](https://alga-twin.streamlit.app/)
- [Equations and units](https://github.com/ysmhla/alga-twin/blob/main/docs/MODEL.md)
- [Verification and limitations](https://github.com/ysmhla/alga-twin/blob/main/docs/VERIFICATION.md)
- [Parameter-source audit](https://github.com/ysmhla/alga-twin/blob/main/docs/PARAMETER_AUDIT.md)
- [Calibration](https://github.com/ysmhla/alga-twin/blob/main/docs/CALIBRATION.md)
- [Decision support](https://github.com/ysmhla/alga-twin/blob/main/docs/DECISION_SUPPORT.md)

Includes Monod/Droop N models, saturation/Haldane/steady-state Han light,
optional CTMI/diurnal forcing, nitrogen accounting, explicit additive/log-normal
likelihoods, profile gates and whole-run holdouts. Flat/unsupported profiles
withhold parameter estimates. AIC/BIC selection is conditional and in-sample;
Fisher planning reports local expected reductions, not confidence intervals.
No optional extra creates missing species evidence or measured datasets.

Example after installing a built wheel:

```bash
alga-twin simulate --demo --days 2 --light 180 --nitrogen 70 --output simulation.csv
```

The `--demo` flag explicitly selects teaching assumptions. Research jobs require
complete evidence-bearing parameter records and user-specified units/noise/bounds.
See the repository for reproducible synthetic verification and source reading.

MIT licence. Cite the [v0.8.1 software archive](https://zenodo.org/records/23665342),
version DOI **10.5281/zenodo.23665342**, and release metadata in CITATION.cff.
No PyPI upload or independent biological validation is established.
