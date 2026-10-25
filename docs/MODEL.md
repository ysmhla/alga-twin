# AlgaTwin v0.4 — model, units and parameter evidence

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

Existing growth fitting estimates mu_max and, with >=3 nutrient observations,
yield. It uses multistart bounded least squares and assumed noise floors, not a
replicate error model. No profiles, formal intervals or independent-run
cross-validation exist. All RMSE is in-sample. Sensitivity and convergence do not
establish identifiability. Changes to entered calibration conditions invalidate
fits; saved scenarios preserve their parameters.

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
