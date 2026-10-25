# AlgaTwin v0.7 — model, units and parameter evidence

## Retained baseline equations

X is g dry biomass/L; N is mg elemental nitrogen/L (not nitrate ion); t is days;
I is micromole photons/m²/s; z and L are metres.

    epsilon(X) = a0 * X^s + a1
    I(z) = I0 * exp(-epsilon(X) * z)
    F(X) = (1/L) integral_0^L I(z)/(K_I + I(z)) dz
    mu_g = mu_max * N/(K_N + N) * F(X)
    dX/dt = (mu_g - k_loss) * X
    dN/dt = -1000 * mu_g * X / Y_XN

| Parameter | Solver unit |
|---|---|
| mu_max, k_loss | day^-1 |
| K_N | mg elemental N/L |
| K_I | micromole photons m^-2 s^-1 |
| Y_XN | g DW/g N |
| a0 (extinction_a0) | L^s (g DW)^-s m^-1 |
| a1 (background_extinction_m_inv) | m^-1 |
| s (extinction_exponent) | dimensionless; 0 < s <= 1 |

The linear baseline is exactly s=1. The optional sublinear law is the family in
Bernard & Lu, [arXiv:2108.10009v1](https://arxiv.org/html/2108.10009v1), Eq. 3.
a0 must be re-estimated for a different s. This is effective attenuation, not a
radiative-transfer/scattering solver. epsilon*z is dimensionless.

Pint treats dry biomass, carbon and elemental nitrogen as distinct dimensions
(g_DW, g_C, g_N). The nutrient equation's 1000 converts g N to mg N. At zero
loss, X + Y_XN*N/1000 is conserved under either optical law. With loss, its
derivative is -k_loss*X; removed biomass/nitrogen is not recycled.

RK45 uses rtol=1e-8, atol=1e-10, max_step=0.12 day, with 16-point Gauss–Legendre
quadrature across depth. Derivatives use nonnegative X/N; rounding-level negative
outputs are clipped, not treated as measurements. Time starts at zero, increases
strictly, and ends within 365 days.

## Evidence and absence of scientific defaults

Parameter records contain value, low, high, unit, source URL, status, species,
conditions, basis, tier, evidence and source locator. VERIFIED means checked
source transcription, not independent validation or strain transferability.

- LITERATURE: audited records; reported points never acquire inferred ranges.
- DEMO: explicitly selected synthetic assumptions; all values are UNVERIFIED.
- MEASURED: user optical estimates; UNVERIFIED, with method and residuals.

Parameters requires all eight numerical fields. simulate and fit_experiment reject
missing parameter configurations. demo_parameters() is an explicit opt-in factory;
the CLI also requires --demo. Source-free explicit user inputs receive UNVERIFIED
provenance. Numeric overrides revoke verified status; the source value/range and
warning are retained separately. Arbitrary URLs are not automatically verified.

The former linear-only extinction_L_per_g_m field is renamed extinction_a0. Its
unit depends on s; inconsistent unit/basis metadata is rejected before simulation.
Experimental conditions are separate inputs; example starting conditions are
illustrations, not recommendations.

## C. minutissima gate

The catalogue is not a complete runnable Monod preset. Extinction, carbon fraction,
Monod and CTMI cardinal gaps remain unset. Haldane/LOT values belong to their own
equations and cannot fill Monod gaps. No verified ranges were established from the
audited sources. See [source audit](PARAMETER_AUDIT.md).

LITERATURE is the initial app screen. It shows provenance and the direct optical
helper, then stops growth simulation/fitting rather than falling back to synthetic
values. DEMO must be explicitly selected, also when uploading growth data. Uploaded
data do not verify its fixed assumptions.

For linear carbon coefficient k_C in m²/g C, dry-weight conversion is:

    a0_DW = 1000 * k_C * f_C      [L/(g DW m)]

f_C is g C/g DW and stays unset. For general s, first convert to litre-based
carbon units, then multiply by f_C^s. The helper requires explicit f_C in (0,1];
it does not certify that input or transfer coefficients between species.

## Direct extinction measurement

CSV columns: biomass, incident, transmitted, path. Select dry-weight/path units
explicitly. Light readings must share calibrated photon-flux units, spectral
response, geometry and medium. OD, watts/m² and carbon biomass are rejected.

    epsilon_observed = ln(incident/transmitted) / path_m

Constrained least squares fits epsilon=a0*X^s+a1: a0/a1 nonnegative; s=1 fixed
or s fitted in (0,1]. There is no invented physiological upper bound. For free-s
optimization, the initial 0.5 and lower numerical bound 1e-4 are algorithm settings,
not biological values or a literature range. The biomass variable is scaled by
its observed maximum to improve numerical conditioning.

Require a medium blank (X=0) and >=3 distinct positive biomasses for a linear fit,
or >=5 for free s. Reject non-finite/zero signals, invalid paths, transmission
above incidence, flat attenuation and ill-conditioned Jacobians. These are
screening heuristics, not profile-likelihood identifiability proofs.

Output method, residuals, in-sample R², measured biomass domain and UNVERIFIED,
MEASURED parameter records. No interval, out-of-domain prediction, or automatic
preset promotion is supplied. Independent optical measurements are needed for
predictive evaluation. Log-transmission noise may be heteroscedastic; sensor
uncertainty propagation is not implemented.

## Scope and calibration limitations

The retained baseline workflow uses fixed illumination/path and no quota or
temperature. The selectable synthetic workspace adds the reduced models below.
No model includes dynamic pH, CO2, mixing, feeding, photoadaptation or oxygen.
The LOT records remain catalogue entries only.

The baseline adapter estimates mu_max and, with >=3 nutrient observations,
yield, now subject to reoptimized profile gates. The joint API supports shared
selected parameters and whole-run held-out evaluation; noise SDs and search
bounds remain explicit assumptions. See the v0.5 section below. Independent
biological validation, empirical interval coverage and model-support selection
remain unestablished. Changing calibration inputs invalidates displayed fits;
saved baseline scenarios retain their parameter snapshots.

## Executable checks

Tests cover evidence statuses, mass bases and units, explicit f_C, missing defaults,
override warnings, synthetic optical recovery and unit invariance, and invalid or
uninformative transmission data. Both optical laws have zero-light, transparent
and zero-biomass limiting checks, monotonic nitrogen, positivity and zero-loss
conservation. s=1 is compared to the original affine formula.

No independent cultivation or optical dataset has validated AlgaTwin.

## Selectable model interface (v0.4.0)

`ModelBase.rhs(t, state)`, `params` (Parameter records) and `states` support
MonodModel (X,N) and DroopModel (X,N,q). All numerical biological parameters are
explicit, finite and accompanied by source/status metadata. Missing values,
carbon-based quotas, incompatible solver units, mixed species and mixing DEMO
with research tiers are rejected. No new research defaults are introduced.
The Streamlit synthetic workspace exposes these laws with a provenance export.
See [implementation source audit and Eq. 9 correction](SELECTABLE_MODELS.md).

Use the same epsilon(X)=a0 X^s+a1 and I(z,t)=Is(t) exp(-epsilon z).
Define G(t,X)=depth-average local potential growth multiplied by optional phi(T).
Monod in this interface uses mu_g=G*N/(K_N+N), retaining the baseline equations.
Droop uses:

    rho(N,q) = rho_max * N/(K_N+N) * max(0, 1-q/Q_max)
    mu_g = G(t,X) * max(0, 1-Q_0/q)
    dX/dt = (mu_g-R)*X
    dN/dt = -1000*rho*X
    dq/dt = rho-mu_g*q
    dN_removed/dt = 1000*R*q*X
    N_total = N + 1000*q*X + N_removed = constant

q, Q_0 and Q_max are **g N/g DW**; rho_max is g N/(g DW day).
R and G are day^-1; N and N_removed are mg elemental N/L.
Initial Q_0<=q<=Q_max is required. At Q_0 growth is zero; at Q_max uptake is
zero. Uptake can continue in darkness, and stored N can support growth at N=0.
The loss convention removes biomass-associated N at the same specific rate R
as biomass, with no dissolved recycling; it is not a carbon-only respiration
model. A separate ledger closes the N balance. In Monod its ledger derivative
is 1000*R*X/Y_XN. No carbon or oxygen balance is claimed.

### Monod relation is a quota-equilibrium limit

For constant G=g>0 and dq/dt=0, let u=rho_max*N/(K_N+N).
Then q*=(u+g*Q_0)/(g+u/Q_max) and the effective growth is Monod in N:

    mu_eff,max = g*rho_max*(1-Q_0/Q_max)/(rho_max+g*Q_0)
    K_eff = K_N*g*Q_0/(rho_max+g*Q_0)
    mu_eff(N) = mu_eff,max * N/(K_eff+N)

This is not a transient equality or a claim of identical fixed-yield biomass
trajectories: storage changes apparent yield. Scaling dq alone to force a fast
limit would violate mass balance and is not implemented. The exponential test
uses constant/saturating light, transparent medium, saturating N and initialized
equilibrium quota for Droop; its exponent includes the quota factor.

### Local light laws

    Saturation: g(I) = mu_max * I/(K_I+I)
    Haldane:   g(I) = mu_max * I/[I + (mu_max/alpha)*(I/I_opt-1)^2]
    Han steady: g(I) = k*sigma*I / [(k_d/k_r)*tau*(sigma*I)^2 + tau*sigma*I + 1]

Haldane mu_max is the local peak at I_opt; for Droop this is potential growth
before the quota factor, not the realized maximum. alpha is m² s/(umol day),
I_opt and K_I are umol photons/(m² s). Initial slope is alpha; high light
inhibits Haldane/Han. Average the local response across depth, not the response
at average light. Han sigma has m² s/(umol day), tau is day, k_r is day^-1 and
k_d,k are dimensionless. All Han kinetic times must first use the same day base.
The steady-state conversion is:

    alpha = k*sigma
    I_opt = sqrt(k_r/(k_d*tau*sigma²))
    mu_max = k*sigma/[tau*sigma + 2*sqrt(k_d*tau*sigma²/k_r)]

This option has no A/B/C transient states or photoadaptation dynamics.

### Optional temperature and illumination forcing

Temperature is an explicit constant condition in degrees Celsius, not a fitted
species preset. The CTMI cardinal factor is:

    phi(T) = (T-Tmax)*(T-Tmin)^2 /
      [(Topt-Tmin)*((Topt-Tmin)*(T-Topt)-(Topt-Tmax)*(Topt+Tmin-2*T))]

phi=0 outside the open cardinal interval and phi(Topt)=1. Require
Tmin<Topt<Tmax and 2*Topt>Tmin+Tmax to avoid an internal pole/negative factors.
The implementation multiplies the entire local light response by phi(T),
keeping I_opt/alpha shape fixed; it does not implement LOT oxygen/temperature
coupling or infer missing C. minutissima cardinal parameters.

Diurnal forcing is a chosen, phenomenological half sine, not a literature
parameterisation of a species. With phase=(t-dawn) modulo period:

    Is(t) = I_peak*sin(pi*phase/daylight)  for 0<=phase<daylight
            0                            otherwise

period, daylight and dawn are explicit days; 0<daylight<=period. At constant-light
mode the conditions' incident light is used directly. At diurnal mode it is the
peak. Respiration/loss R acts throughout day/night and defaults to no value in
the engine (the DEMO factory explicitly supplies zero). Temperature scaling of
respiration is not assumed.

### Numerical verification and limits

The common solver uses RK45, rtol=1e-10, atol=1e-12, max step 0.05 day;
diurnal max step is additionally at most period/96. Integration splits at
dawn/dusk so dense interpolation does not cross light switches. Composite
16-point Gaussian quadrature uses optical segments <=2 and integrates to
min(optical depth,745), discarding only the exponential dark tail. State units
are distinct Pint dimensions. Tiny negative X/N (>=-1e-7) are clipped; materially
negative concentrations or quota violations >1e-8 are errors. Nitrogen ledger
conservation, monotonic N within 1e-8 mg/L, quota limits, darkness, saturation,
transparent/thick optics, Han equivalence/normalization, cardinal limits and the
amended Eq. 9 analytic acceptance have synthetic tests. No independent
out-of-sample biological validation is established.

## Calibration and numerical coordinates (v0.5.0)

`calibration.py` shares selected parameters across runs, preserving separate
controlled light/N/temperature conditions, supplied initial states and technical
replicate observations. Model biology is unchanged. Active model parameters
remain source/status records; search bounds and assumed observation SDs are
stored as separate algorithm inputs. Complete equations, refusal thresholds,
input schema and limitations are in [CALIBRATION.md](CALIBRATION.md).

For observation y and prediction f, additive residuals are `(f-y)/sigma`; sigma
has the corresponding state unit. For log-normal errors the residual is
`(log(f)-log(y))/sigma_log`, with dimensionless sigma_log and f interpreted as
conditional median. NLL adds log(sigma)+0.5*log(2*pi) per observation; log-normal
NLL additionally adds log(y). No SD is implicitly estimated from pooled runs.
Technical repeats contribute individually under a stated independent-error
assumption. Biological replicates are separate run ids.

To retain near-depleted nitrogen in log-normal likelihoods, optional numerical
coordinates use u=log(N/N_ref), with N_ref=1 mg N/L (a unit reference,
not a noise floor or biological parameter):

    Monod: du/dt = -1000*G*X / [Y_XN*(K_N+N)]
    Droop: du/dt = -1000*rho_max*(1-q/Q_max)*X / (K_N+N)
    N = N_ref*exp(u)

This is an equivalent numerical transformation for N(0)>0, not a change of
physical states, equations, mass basis, noise floor or measured values. At
N>1e-100 the implementation uses the equivalent `(dN/dt)/N`; below it, the
analytic expression avoids underflow/division by zero. `log_N` preserves the
prediction in log units even if exp(u) underflows in a display column. Log-normal
likelihoods consume that log prediction; no concentration pseudocount is used.
At N(0)=0 the ordinary physical-coordinate solver remains available. Zero or
negative log-normal observations are rejected. Biomass underflow resulting in
non-finite log predictions is rejected rather than replaced by a floor.

`simulate_model` now exposes positive rtol/atol/max_step_day algorithm settings;
its defaults remain 1e-10/1e-12/0.05 day. Calibration uses 1e-8/1e-10/0.5 day and
log N when initial N>0; dawn/dusk splitting and diurnal period/96 cap remain.
Tests compare log/physical-coordinate trajectories and verify N conservation
with and without loss for Monod/Droop. No carbon/oxygen balance is added.

Bounded multistart least squares estimates the selected parameters. At each
profile point all nuisance parameters are reoptimized. Only supported two-sided,
connected, interior profiles yield a point estimate and a named marginal
asymptotic profile interval (`chi2.ppf(confidence,1)`). Flat/open/boundary,
disconnected or failed profiles withhold estimates/intervals. A detected better
profile optimum invalidates the common result. The original single-run fitter
uses this gate too; it conditions on the first observed X/N and excludes time-zero
observations from the likelihood. Sensitivity or optimizer convergence alone
never establishes identifiability.

Leave-one-whole-run-out refits/reprofiles training runs only, using pre-specified
noise/search/model choices. Only supported training fits score the held-out run.
RMSE, MAE and NLL retain split/run/state/unit/origin/fold labels. Starting states
are treated as supplied conditions; their uncertainty is not propagated.
Synthetic held-out tests check leakage/refusal behavior, not biological validity.
MCMC, censored errors, random culture effects and empirically calibrated coverage
remain unimplemented. No independent cultivation dataset has validated AlgaTwin.


## Benchmark/PEtab exchange (v0.6.0)

No new biological equation, parameter default or numerical state law is added.
PEtab 2.0 tables plus a versioned alga_twin_native_v1 JSON model invoke the
existing ModelBase implementation, optics, units, likelihood and solver settings.
The explicit reader uses libpetab's public Model/Problem interfaces and official
validators. It reconstructs initial states/controls from condition/experiment
TSVs, observations/replicates from measurement TSVs and bounds/noise from their
tables. It does not load a duplicate original calibration job. Package version
and file hashes must match. Stock libpetab from_yaml/SBML/AMICI compatibility is
not claimed; see ../benchmark/README.md for the supported subset.

Native SciPy profile gates determine reported values/intervals and whole-run CV.
Real pyPESTO 0.7.0 Powell optimization and full-bound parameter_profile provide
a separate full-data cross-check of the exported likelihood. Material optimum
mismatch or external failure refuses the benchmark result. Profile grids are
not permission to display an unsupported point estimate. Search-coordinate
steps are algorithm settings, not biological ranges or priors.

Unit/basis checks, likelihood/trajectory round-trip tests, a dark/transparent
limit and Monod/Droop nitrogen-ledger tests check export fidelity. Scoreboards
retain observable units and distinguish full-data in-sample RMSE from held-out
RMSE. Failed folds withhold held-out aggregation. Each dataset carries licence,
source/origin and permission evidence; neither a DOI nor metadata syntax
establishes rights, source verification or biological validity. All currently
shipped data are SYNTHETIC. Independent biological evaluation is pending human
candidate datasets with recorded permission to reuse/redistribute.

## Empirical OD/cell-count observation model (v0.7)

This measurement conversion does not alter the growth ODEs or their N ledger.
Paired samples fit an intercept-inclusive polynomial by equal-weight ordinary
least squares:

\[
X_{DW}(S)=c_0+c_1S \quad\text{or}\quad X_{DW}(S)=c_0+c_1S+c_2S^2.
\]

Here X_DW is g dry weight/L. S is dimensionless OD for a specified wavelength,
path/blank/dilution, or cells/L for a specified counting method. Cells/mL is
explicitly multiplied by 1000. Input DW in g_DW/meter^3 is multiplied by 0.001
to obtain g_DW/liter; carbon mass is rejected, and no f_C is assumed.
Coefficient c_k has units (g_DW/L)/(unit of S)^k; c0 is g_DW/L. Coefficients are
reported in ascending physical powers, but calculations use a centered/scaled
S coordinate to avoid poor conditioning with large cell counts. There is no
forced zero intercept. Replicated pairs receive equal per-row weight, so more
technical repeats at a level increase that level's weight; no random-effects or
errors-in-variables model is implied.

More rows than fitted coefficients, sufficient distinct signal levels, and
varying DW are required. Slopes at both domain endpoints must be nonnegative
with a strictly positive slope somewhere. For a degree <=2 polynomial this
establishes monotonicity across the domain; endpoint fitted concentrations must
be nonnegative within numerical roundoff. Conversion refuses S outside the
measured closed interval. A quadratic with c2=0 reduces to the linear map;
changing cells/mL to cells/L or the DW concentration unit preserves converted
concentration and mass X_DW*reactor volume. Unit/limiting-case/mass-conversion
tests cover these properties; existing Monod/Droop N-balance tests still apply.

Residuals are measured DW minus fitted DW, in g_DW/L. The displayed descriptive
in-sample R-squared is 1 - sum(residual^2)/sum((measured-mean(measured))^2).
It is not independent accuracy, interval coverage or evidence for instrument/
strain transfer. No coefficient interval is estimated and proxy-conversion
uncertainty is not propagated into growth profile intervals. All paired-fit
coefficients remain UNVERIFIED with explicit SYNTHETIC/MEASURED origin, species,
conditions and OLS method; they do not become literature presets.

## Guided mapping and report scope (v0.7)

The wizard performs only explicit conversions: hours/24 -> days;
g_DW/meter^3/1000 -> g_DW/L; g_N/L*1000 -> mg_N/L; quota g_N/g_DW unchanged.
It does not convert nitrate-ion mass, radiometric light, carbon or OD without a
matched proxy calibration. It does not shift time zero or derive initial states
from noisy first observations. Missing measurement cells are omitted; missing
ids/metadata, nonnumeric/infinite cells and duplicate measurement identities
refuse. Raw assay negatives are retained for additive-error fitting, as in the
joint inference API; physical model states remain subject to the existing gate.

Only source-reported VERIFIED ranges are eligible for species range presets;
none currently forms an executable C. minutissima preset. The unknown-strain
path keeps all biological inputs blank. Structural exponent selection is
explicit, with coefficient units updated. User-entered research values have
MEASURED tier / UNVERIFIED / user_supplied_not_verified evidence: this describes
their input channel, not certification that they were measured or source-read.

HTML/PDF reports retain profile method/confidence, support flags, provenance,
initial/forcing/noise/search assumptions and input hashes. In-sample versus
held-out errors keep separate split labels and observable units; failed folds
are not pooled into a selectively optimistic score. Unsupported point estimates
and intervals are withheld. Descriptive curves remain in-sample only. PDF table
numbers are rounded to six significant figures; JSON retains full precision.
All scientific interpretation remains conditional, with no independent
biological validation claim. See GUIDED_WORKFLOW.md and USABILITY.md.
