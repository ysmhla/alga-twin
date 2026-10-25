# C. minutissima parameter audit — 2026-10-25

This records source reading, not an independently validated species preset.

## Species and mass basis

Martínez, Mairet & Bernard (2018), Theory of turbid microalgae cultures,
[DOI 10.1016/j.jtbi.2018.07.016](https://doi.org/10.1016/j.jtbi.2018.07.016),
Table 1 does NOT list C. minutissima. Its C. pyrenoidosa entry is a single
0.200 m²/g carbon, not a dry-weight range. Author-posted full text was read at
https://www.researchgate.net/publication/326452706_Theory_of_turbid_microalgae_cultures.
The experimental source behind the cited review was not independently established.

Bernard & Lu, [arXiv:2108.10009v1](https://arxiv.org/html/2108.10009v1), section 5.2,
uses 0.2 m²/g and 10 m^-1 numerically. Its notation omits the explicit carbon basis.
The background value is not a universal measured medium range. Neither coefficient
populates the minutissima preset. Legacy 12 L/(g DW m) and 0.3 m^-1 remain only in
explicitly selected UNVERIFIED DEMO assumptions.

## Source-read records

López Muñoz & Bernard (2021), Processes 9(3):496,
[DOI 10.3390/pr9030496](https://doi.org/10.3390/pr9030496), Tables 1–3, sections
2.3/3.1 and Appendix A were read in publisher-supplied full text at
https://www.researchgate.net/publication/349936349_Modeling_the_Influence_of_Temperature_Light_Intensity_and_Oxygen_Concentration_on_Microalgal_Growth_Rate.

| Record | Point | Unit / qualification |
|---|---:|---|
| Haldane mu_opt | 0.64 | day^-1 |
| I_opt | 150 | micromole photons m^-2 s^-1 |
| alpha | 0.006 | m² s micromole^-1 day^-1 |
| A_G, A_m | 22.4, 17.6 | dimensionless |
| E_G, E_m | 1.14e5, 1.21e5 | J/mol |
| T0 | 35 | °C reference; not Tmax |
| LOT optimum | 29.3 | °C; low-oxygen result, not CTMI triplet |
| Km | 0.203 | printed (L/mg O2)^n; conflicts with normalized oxygen in Eq. 3 |
| n | 0.09 | dimensionless; adopted, not independently identified for this species |

No complete minutissima CTMI cardinal triplet is reported. Table 3's dynamic
oxygen/respiration parameters belong to D. salina and are not transferred.
Conditions: light 30–550 micromole/m²/s; light-response measurements at 10/30/35°C;
pH uncontrolled; oxygen assumed 135% saturation. Fitting: Haldane regression;
CTMI-assisted Hinshelwood calibration; MATLAB nlinfit/Levenberg–Marquardt.
Entries are points without verified ranges. Km remains UNVERIFIED (unit conflict).
Source verification does not establish AlgaTwin validation.

## Runtime policy

Missing quantities remain None/NO_SPECIES_DATA; f_C is unset. Source equation and
evidence type are explicit. Direct extinction fitting uses only user measurements;
it neither digitises nor downloads datasets. Future benchmark ingestion requires
its separate licence and metadata checks.
