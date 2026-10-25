# AlgaTwin v0.3 — model, units and parameter evidence

## Equations implemented today

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

Single-species, well-mixed batch; fixed illumination/path. No quota, temperature,
pH, CO2, mixing, feeding, photoinhibition or diurnal dynamics. Haldane, LOT and CTMI
records are catalogue entries only; those growth models are NOT BUILT in this step.

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
