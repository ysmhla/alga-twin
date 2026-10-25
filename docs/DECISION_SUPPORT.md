# Conditional model support and experiment planning

Open **Workspace -> Model support and next experiment**. The initial path asks
for complete explicit problems. Choose **SYNTHETIC worked example** deliberately
for teaching values; these are UNVERIFIED/DEMO and are not C. minutissima presets.
The UI compares Monod/Droop with saturation/Haldane light on identical data and
shows top three supplied next experiments with reasons. It exports full JSON
with hashes, parameter evidence, assumptions, profile methods and decisions.

## Reproducible Python use

```python
from alga_twin.decision_io import (
    synthetic_decision_problem, load_selection, load_experiments,
)
from alga_twin.model_selection import compare_models
from alga_twin.experiment_design import rank_experiments

config, observations, proposals = synthetic_decision_problem()
candidates, errors = load_selection(config, observations)
comparison = compare_models(candidates, errors, **config['decision'])
print(comparison.table)
if comparison.recommendation:
    selected = next(c for c in candidates if c.name == comparison.recommendation)
    fit = comparison.fits[selected.name]
    ranking = rank_experiments(selected.runs, fit, load_experiments(proposals))
    print(ranking.top3[['candidate', 'reason']])
```

The worked proposals have two initial states because the demonstrated supported
model is Monod. For a selected Droop model, supply its explicit third initial
quota; a missing quota is refused. `candidate_prediction` can inspect a proposed
trajectory without fabricating assay observations. See MODEL.md for equations,
units and nitrogen conservation. No biological defaults were changed.

## Honest interpretation

- All candidates must use the same original observations, units, culture ids,
  technical ids, origins, initial X/N and forcing. One fixed error model is
  shared. Full job descriptions explicitly supply every fixed parameter/q0.
- AIC/BIC are in-sample quantities, with k counting fitted shared parameters.
  They do not replace whole-run CV. More states/fixed constants do not become
  unpenalized fitted nuisance parameters: these results explicitly condition on
  their supplied values. Rerun with uncertainty in those inputs when available.
- Flat/open/disconnected profiles withhold points and criteria. Numerical/profile
  failures make the comparison INCOMPLETE. Too few observations, unsupported
  profiles or an approximate lack-of-fit rejection can yield NO SUPPORTABLE MODEL.
- A fixed-noise chi-square(n-k) screen is a labelled local/large-sample
  approximation for nonlinear models, not an established small-sample test.
  Its alpha and both criterion windows must be supplied. Worked settings
  (2, 2, 0.01) are explicit teaching decisions, not biological constants or a
  source-verified rule. If AIC/BIC windows have no common eligible candidate,
  report CRITERIA DISAGREE. Parsimony order is exported, not a novelty claim.
- Fisher planning requires a current profile-supported parameter vector and a
  nonsingular, numerically stable information matrix. Flat profiles require more
  data/design judgment; this local planner refuses to use their hidden optimizer
  coordinates. No regularizer hides missing information.
- A proposed experiment supplies no data. Expected reductions assume independent
  stated noise and known initial/fixed parameters, conditional on one model and
  fitted point. These are local SD/volume ratios, not intervals or guarantees.
  Rankings can change with noise, model, bounds and assumptions; sensitivity to
  those choices is not automatically integrated over a posterior.
- Constraints, safe light/N settings, costs and duration/sample budgets must be
  set by the researcher. Different budgets rank by total information only.
  The top three are among supplied choices; no global optimum is claimed.
- Candidate changes invalidate displayed rankings. Changed observations, model,
  provenance or noise cannot reuse a stale fit. Exports retain the full current
  fit and proposed configurations, method and numerical controls.

## Sources actually read

- R Core `stats::AIC` official documentation: formulas, maximized likelihood and
  same-data requirement, https://stat.ethz.ch/R-manual/R-devel/library/stats/html/AIC.html .
- NIST/SEMATECH e-Handbook, D-optimal designs: determinant criterion, model and
  candidate-set dependence, https://www.itl.nist.gov/div898/handbook/pri/section5/pri521.htm .
- SciPy official `scipy.stats.chi2` documentation: degrees of freedom and survival
  function used for the explicitly approximate residual screen,
  https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chi2.html .

These are method sources, not C. minutissima parameter evidence. The Fisher
linearization and volume-ratio algebra implemented here are stated explicitly
in MODEL.md. No new physiological citation, DOI, value or range was inferred.
NLoed's primary article was located but full text was access-blocked in this
session; it is not used as verified full-text evidence here.
