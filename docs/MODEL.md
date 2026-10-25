# AlgaTwin v0.2 — Scientific specification

## States, dimensional conventions

- `X`: dry biomass concentration [g DW L^-1]
- `N`: externally available nitrate **as elemental nitrogen** [mg N L^-1]
- `t`: cultivation time [day]
- `I`: irradiance [µmol photons m^-2 s^-1]
- `L`: effective optical path [m]

## Governing equations

Gross specific growth rate:

```
mu_g = mu_max * N/(K_N + N) * <f(I)>
<f(I)> = (1/L) * integral_0^L [ I(z)/(K_I + I(z)) ] dz
I(z) = I0 * exp(-(k0 + kX * X) * z)
```

Balance equations:

```
dX/dt = (mu_g - k_loss) * X

dN/dt = -1000 * mu_g * X / Y_XN
```

The factor `1000` converts consumed g elemental N/L to mg N/L; `Y_XN` is g biomass per g elemental nitrogen consumed. Biomass loss in this prototype does not recycle nutrients. Light integration is numerical (16-point Gauss–Legendre quadrature), evaluated at every numerical solver step; we do not substitute a growth response at average irradiance.

## Physical scope

Single species, well-mixed batch, constant incident light, fixed reactor path, no changes to temperature/pH/CO2, external nitrate-N as sole explicit limiting nutrient, no luxury uptake/quota, no photoinhibition, no maintenance uptake, no fed-batch, no biomass-light scattering model beyond effective Beer–Lambert absorption.

This is **a research modelling prototype** rather than a validated 'digital replica' of any laboratory reactor. For dense/shallow cultures a simple exponential optical model may be inadequate.

## Initial illustrative parameters

| Parameter | Default | Unit | Treatment in fitting |
|---|---:|---|---|
| `mu_max_day` | 0.95 | day^-1 | Fitted |
| `k_n_mg_L` | 5 | mg N/L | Fixed |
| `k_i_umol_m2_s` | 85 | µmol photons/m²/s | Fixed |
| `biomass_yield_g_per_gN` | 8 | g DW/g N | Fitted only with >=3 nitrate observations |
| `extinction_L_per_g_m` | 12 | L g^-1 m^-1 | Fixed |
| `background_extinction_m_inv` | 0.3 | m^-1 | Fixed |
| `loss_rate_day` | 0 | day^-1 | Fixed |

These are **illustrative** values and are not asserted as *Chlorella* physiology constants.

## Calibration and identifiability

The current estimator minimises scaled residuals for the two observed states, with deterministic multistart bounded least squares. Scale factors are assumed rough noise floors, not measured variance. Fitting does not account for correlated observations, errors-in-variables, replicate structure or parameter confidence intervals. For biomass-only data the yield stays fixed; from a single trajectory neither all optical nor all kinetic parameters are separately identifiable.

Fitting depends on metadata entered manually (I0, L, nitrate N0 if first N observation is missing). Changing those conditions invalidates stored fits.

The reported RMSE is **in-sample**. Independent run testing is NOT implemented. No parameter credible/confidence intervals or field-ready parameter recommendations are currently available.

## Numerical and implementation notes

- `solve_ivp` RK45 with rtol=1e-8, atol=1e-10, maximum step=0.12 day.
- Nonnegative initial conditions validated. Rounding-level negative nitrogen states are clipped for presentation; derivatives use N=max(0,N).
- Time interval must begin at zero and end within 365 days.
- Initial biomass for fitting comes from first observed dry biomass; initial N from first measured time-zero N or manually supplied sidebar value.
- Calibration computes reference predictions only at measured time points; virtual experiments may use denser time grids.

## Planned validation

1. Test conservation of `X + Y_XN * N/1000` at zero biomass loss.
2. Verify monotonic cumulative nitrogen consumption for positive growth.
3. Compare optical response under low and high biomass or path length.
4. Parameter recovery from clean synthetic data; failure cases flagged.
5. Independent experiments, not shuffled timepoints from a single culture, for any claim of generalization.

## References and general context

- Monod, J. (1949): growth of bacterial cultures (classical nutrient-limited growth formulation).
- Droop, M. R. (1973): nutrient status and growth (quota model, future work).
- SciPy [`solve_ivp`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html) and [`least_squares`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html).

**No parameter in this implementation was empirically calibrated to a peer-reviewed experimental dataset at project creation.**
