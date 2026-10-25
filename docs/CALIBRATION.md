# Conditional calibration and identifiability — v0.5.0

## What runs today

`fit_joint` fits selected shared parameters across multiple culture runs using
Monod or Droop and their light/temperature options. Every run supplies its own
initial state and controlled conditions. The same fixed biological parameters
must agree across runs; diurnal control settings can differ. Initial X/N must
agree with the explicit starting fields in each run's conditions. `fit_experiment`
adapts the original single-run Monod workflow to the same profile gate.

Inputs require explicit `FitParameter(low,high,initial,scale)` search settings
and `ErrorModel(kind,scales)`. Search bounds are algorithm assumptions, not
verified physiological ranges. They are stored separately from Parameter source
bounds. The baseline adapter offers labelled synthetic settings only in DEMO;
research calls require explicit noise SDs and search bounds. No new species
preset, carbon fraction, missing source value or verified range is invented.

## Data and replicates

A `CalibrationRun` contains an id, model, initial state, observations and origin.
Long-form columns are:

| Column | Meaning |
|---|---|
| time_day | Nonnegative days from supplied initial state, maximum 365 |
| observable | X or N; q additionally for Droop |
| value | Finite observation; omit missing observations entirely |
| unit | Exact canonical unit: g_DW/liter, mg_N/liter, g_N/g_DW |
| replicate | Technical measurement identifier within a culture run |

Duplicate `(time,observable,replicate)` identities are rejected. Technical
replicates remain individual likelihood contributions; they are not averaged
or silently deduplicated. Separate biological cultures require separate run
ids. The likelihood assumes conditional independence of measurement errors;
correlated technical replicates, random culture effects and uncertain initial
states are not modelled. Do not present repeated readings of the same assay as
independent replicates without justification.

Origin is explicitly SYNTHETIC, MEASURED (caller assertion) or UNSPECIFIED.
Origin labels do not establish a licence or independent validation. Different
origins are not pooled. The legacy adapter tags known synthetic fixtures;
otherwise it uses UNSPECIFIED. Parameter tier and measurement origin are distinct.
The legacy adapter conditions on the first observed X/N, excludes t=0 from its
likelihood, and holds those initial states fixed. Generic runs may include
independent t=0 observations of a separately supplied initial state.

At least three distinct positive-time run/time events and more than
`number_of_parameters+1` post-zero scalar measurements are required. This is an
explicit conservative input screen, not a mathematical identifiability theorem.
Profiles can still reject denser data with too little N or light variation.

## Likelihoods and numerical estimates

Let f be a deterministic model prediction at a measured state/time.

    Additive: y = f + e; e ~ Normal(0,sigma²)
      r = (f-y)/sigma
      NLL = sum[0.5*r² + log(sigma) + 0.5*log(2*pi)]

    Log-normal: log(y) = log(f) + e; e ~ Normal(0,sigma_log²)
      r = [log(f)-log(y)]/sigma_log
      NLL = sum[0.5*r² + log(sigma_log) + log(y) + 0.5*log(2*pi)]

Additive SD uses each observation's unit. Log-normal SD is dimensionless, and f
is its conditional **median**, not arithmetic mean. Zero/negative observations
are rejected for log-normal errors; no pseudocount is added. Additive normal
errors allow negative raw assay observations without clipping. This does not
make negative physical concentrations admissible. Censoring/detection limits,
heteroscedastic variance functions and fitted variance parameters are NOT BUILT.

Canonical units also fix the reference scale inside log densities; NLL values
are comparable only for identical data, units and error definitions.

Noise SDs are fixed, caller-supplied assumptions/measurements, not estimated from
these data. Intervals condition on them. Pre-specify SDs or determine them from
independent measurements; estimating them from all runs before held-out scoring
would leak information. No automatic full-data noise estimation occurs here.

SciPy bounded least squares minimizes sum(r²). Coordinates map finite search
bounds to [0,1], linearly or logarithmically. Initial, 0.25 and 0.75-coordinate
starts are optimized; this is a local multistart search, not a global guarantee.
Model/unit/initial-state validation checks search endpoints and coupled quota
or CTMI corners before fitting. Fitting extinction exponent or diurnal control
times is not supported. Re-estimating exponent-dependent coefficient units
requires a separate explicit optical calibration.

## Profiles and refusal gate

For each selected parameter, hold it fixed and reoptimize **all** other selected
parameters. Profile delta deviance is `2*(NLL_profile-NLL_best)`; fixed noise and
data make the additive constants cancel. The initial grid is eleven points
(seven in the legacy adapter), plus the optimum and local probes at ±0.01 in
search coordinates. Nuisance starts use the joint optimum and nearest cached
profile solution. Crossing brackets are refined by Brent's method to 1e-5 in
search coordinates.

The threshold is `chi2.ppf(confidence,df=1)`. At confidence=0.95 it is calculated,
not hard-coded. Reported intervals carry the method name:
**Reoptimized profile likelihood; marginal chi-square(df=1) asymptotic cutoff;
fixed noise scales**. They are pointwise/marginal, not simultaneous, posterior,
prediction or empirically calibrated coverage intervals.

The output withholds a parameter value and interval when:

- The sampled profile is flat (delta spread <=1e-3), or the ±0.01 minimum
  neighborhood remains within this tolerance: NOT IDENTIFIABLE at this resolution.
- Either cutoff is unreached within bounds, the optimum is within 1e-4 of a
  coordinate boundary, or the sampled acceptance region is disconnected:
  NOT IDENTIFIABLE / unsupported under the supplied search.
- Optimization/profile convergence fails, or profiling finds a materially better
  common optimum: PROFILE FAILED, with no parameter point/interval.

A better optimum found in profiling invalidates the complete estimate vector.
`JointFitResult.values()` refuses it if any fitted parameter is unsupported.
Training curves/residual metrics can remain as descriptive fit diagnostics;
they are not forecasts with an identified parameter vector. Profiles expose
search-grid values, not disguised point estimates. The legacy UI/CLI also
withhold their parameter object when the gate fails; fitted metrics never bypass it.

Finite grids and multistart searches can miss additional modes or narrow valleys.
Bounds and the numerical flatness tolerance affect decisions. A refusal at finite
bounds is not proof of structural non-identifiability or an infinite interval.
Expand justified bounds, increase numerical resolution and collect informative
measurements as needed. Asymptotic cutoffs can have poor coverage for scarce,
nonlinear data; no coverage/independent predictive-validity claim is made.
Optional MCMC and bootstrap cutoff calibration are NOT BUILT.

## Whole-run cross-validation

`leave_one_run_out` removes a complete run, fits and profiles the remaining runs,
then scores the excluded run only if all selected training parameters pass.
Training starts, supplied SDs/bounds and model choice remain pre-specified;
no full-data fit is used to initialize folds. Initial conditions for the excluded
run are supplied inputs, so scoring is conditional on known starting state.
Later held-out observations never enter the training objective or profile.

Exports label each error row `in-sample` or `held-out`, include run/observable,
origin, unit, sample count, RMSE, MAE, NLL and held-out fold. Unsupported/failed
training folds have a status/reason and no held-out score. There is no automatic
imputation of failed-fold scores or optimistic aggregation. Synthetic holdouts
check code behavior; no independent biological evaluation has been performed.

## Python, CLI and Streamlit

```python
from alga_twin.calibration import fit_joint, leave_one_run_out
from alga_twin.calibration_io import load_job, synthetic_job

config, observations = synthetic_job()  # all source parameters UNVERIFIED
runs, search, errors = load_job(config, observations)
result = fit_joint(runs, search, errors)
print(result.table())
cv = leave_one_run_out(runs, search, errors)
print(cv.folds)
print(cv.metrics)  # split column separates in-sample from held-out
```

Save `config` as JSON and `observations` as CSV to use:

    alga-twin fit-joint --config job.json --observations observations.csv --output fit.json --cross-validate

The command writes a JSON evidence report plus `.profiles.csv`, `.in_sample.csv`
and, when requested, `.held_out.csv`. Return code is 1 when the full-data profile
gate withholds the estimate vector. Fold refusals remain separately visible even
when the full-data fit is supported. Config schema version 1 explicitly requires
all four condition fields and all active parameter evidence records; the loader
does not insert missing species/example values.

Streamlit: select DEMO, then Workspace → Joint calibration. The seeded worked
example is SYNTHETIC. A paired JSON/CSV upload applies no fallback to partial
uploads. This workspace accepts DEMO/UNVERIFIED records; explicit research
configurations can use the Python/CLI API. A full non-modeller mapping wizard is
work package 5. Changing configuration, CSV or baseline likelihood controls
invalidates the corresponding displayed results.

## Method sources actually read

Raue et al. (2009), DOI [10.1093/bioinformatics/btp358](https://doi.org/10.1093/bioinformatics/btp358),
Eq. 8 and Section 4/Eq. 10, describes likelihood thresholds and nuisance
reoptimization. The [author-uploaded full text](https://www.researchgate.net/publication/221996729_Structural_and_Practical_Identifiability_Analysis_of_Partially_Observed_Dynamical_Models_by_Exploiting_the_Profile_Likelihood)
was read. Its upload-page date differs from the paper year; bibliographic year
2009 was checked against [PubMed](https://pubmed.ncbi.nlm.nih.gov/19505944/).
Our finite-bound refusal heuristics and implementation are specified above;
we do not claim the paper validates them for microalgae.

The likelihood parameterisation was checked against official
[SciPy lognorm](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.lognorm.html),
[least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html)
and [chi2](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chi2.html)
documentation. [pyPESTO profile documentation](https://pypesto.readthedocs.io/en/develop/api/pypesto.profile.html)
also describes the one-degree-of-freedom threshold. This release uses its own
SciPy implementation; pyPESTO was not run as part of this calibration package.
