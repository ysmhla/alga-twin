# Selectable batch models — v0.4.0

## Entry points and evidence

`alga_twin.models.ModelBase` exposes ordered `states`, `state_units`, read-only
`params` evidence records and `rhs(t, state)`. `MonodModel` has X,N;
`DroopModel` has X,N,q. `simulate_model` integrates either interface and a
separate removed-N accounting ledger. Model choice does not establish that data
can identify its parameters. Fitting through this interface is implemented in calibration.py; see CALIBRATION.md.

The Streamlit DEMO tier offers Workspace → Selectable models (SYNTHETIC).
Choose nutrient/light laws, optional CTMI, diurnal illumination and loss.
Every fixture is SYNTHETIC / UNVERIFIED with no literature bounds. These controls
are assumptions, not species ranges. The initial LITERATURE gate remains intact;
no C. pyrenoidosa or Isochrysis values fill C. minutissima gaps. All active
parameters appear in a provenance table and downloadable manifest.

```python
import numpy as np
from alga_twin.demo import demo_model_parameters
from alga_twin.model import Conditions
from alga_twin.models import DroopModel, simulate_model

# Explicitly synthetic: not a C. minutissima preset.
params = demo_model_parameters("droop", "haldane", temperature=True, diurnal=True)
model = DroopModel(params, Conditions(), light="haldane", temperature_c=25, diurnal=True)
result = simulate_model(model, np.linspace(0, 8, 81), [0.1, 60, 0.09])
print(result[["time_day", "X", "N", "q", "removed_n_mg_L", "total_n_mg_L"]])
```

`MonodModel.from_baseline(parameters, conditions)` adapts the existing explicit
Monod configuration. Its trajectories are regression-compared to `simulate`.
The original simulator, CLI fitting, TrustLens and planner retain their baseline
scope. They retain their Monod scope; the joint interface fits selected Droop parameters. Conditional model-support selection is implemented separately; see DECISION_SUPPORT.md.

## Source audit for this implementation

| Item | Source actually read | Use and restriction |
|---|---|---|
| Quota uptake/growth | Bernard, Masci & Sciandra, MATHMOD 2009, *A photobioreactor model in nitrogen limited conditions*, Eqs. 1,2,8,24 | Reduced batch quota structure; no source numerical values imported |
| Respiration/N loss | Same paper, text preceding Eq. 9 | Equal specific biomass/N loss, exported to explicit ledger; no dissolved recycling |
| Haldane law | López Muñoz & Bernard 2021, Eq. 1; Bernard & Lu 2021, Eq. 1 | Potential gross rate before quota/N factor and optional loss |
| CTMI | López Muñoz & Bernard 2021, Appendix A, A1–A2 | Cardinal shape only; complete C. minutissima triplet remains unset |
| Han steady-state conversion | Bernard & Lu 2021, Appendix A, Eqs. 19–20 | Steady state only, not a dynamic photosystem solver |
| Optical optimum | Bernard & Lu 2021, Eqs. 8–9 | Printed second branch discrepancy documented below |
| Bernard & Rémond 2012 | DOI/title/abstract checked, full text unavailable in this audit | Full-text equation verification UNVERIFIED; implementation relies on the read 2021 primary articles |

Primary links:

- [MATHMOD 2009 proceedings, paper 270](https://www.eurosim.info/fileadmin/user_upload_argesim/ARGESIM_Publications_OA/MATHMOD_Publications_OA/MATHMOD_2009_AR34_35/full_papers/270.pdf)
- [López Muñoz & Bernard 2021, DOI 10.3390/pr9030496](https://doi.org/10.3390/pr9030496);
  [publisher full text available through ResearchGate](https://www.researchgate.net/publication/349936349_Modeling_the_Influence_of_Temperature_Light_Intensity_and_Oxygen_Concentration_on_Microalgal_Growth_Rate)
- [Bernard & Lu, arXiv:2108.10009v1](https://arxiv.org/html/2108.10009v1)
- [Bernard & Rémond 2012 abstract, DOI 10.1016/j.biortech.2012.07.022](https://pubmed.ncbi.nlm.nih.gov/22940363/)

The 2009 full photoadaptation/carbon/oxygen model is not implemented. Its Eq. 9
prints different light factors in quota and biomass equations; our reduced model
uses the same potential gross growth in both, consistent with its Eq. 24 and
nitrogen accounting. Its organism/basis is Isochrysis galbana / carbon. Here X is
DW and quota parameters must be supplied on that basis. This structural
adaptation does not perform a carbon-to-DW parameter conversion. f_C is unset.

## Eq. 9 branch discrepancy and amended analytic acceptance

This is our mathematical/numerical finding for arXiv **v1**, not a reported erratum.
Let M=mu_max, J=I_opt, a=alpha, 0<R<M. The compensation equation is

    A I² - B I + C = 0
    A = R M / (a J²)
    B = M - R + 2 R M / (a J)
    C = R M / a
    Delta = (M-R) * (M-R + 4 R M / (a J))
    I_low = 2 C / (B + sqrt(Delta))
    I_high = (B + sqrt(Delta)) / (2 A)

These stable roots avoid cancellation. For
`P(Y)=integral_0^Y [mu(Is exp(-y))-R] dy`, `P'(Y)=mu(Is exp(-Y))-R`.
At incident light between the compensation roots, printed Eq. 9's first branch
selects I_low, the maximum. For incident above I_high its second branch selects
I_high: that stationary point is a minimum. The lower-root candidate can be a
maximum, but its productivity must also exceed the boundary value P(0)=0.
For incident below I_low, printed depth can be negative and inadmissible.

`printed_eq9_depth` is explicitly a diagnostic transcription, never the general
optimiser. `optimal_optical_depth` evaluates all reachable roots and Y=0, then
chooses the largest integrated productivity. At R>=M or zero light the boundary
wins. At R=0 and positive light there is an asymptotic supremum, not a finite
optimum; the result explicitly says `finite=False` and Y=infinity.

Regression tests derive M,J,a from this repository's synthetic configuration,
then use R=M/10 and high light Is=40J. They demonstrate the printed high-light
branch is a local minimum, and the selected positive maximum beats a dense
independent scan. In the applicable first-branch domain, tests compare the
closed form, computed compensation optimum and an independent scalar optimiser.
No paper numerical values are hard-coded, and no cultivation data are claimed.

This is optical-depth productivity in day^-1, not a general biomass-surface
productivity optimum, reactor design recommendation or Droop batch optimum.
An arbitrary Haldane triplet need not correspond to positive Han coefficients;
the forward conversion from positive Han parameters always does.
