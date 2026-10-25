# Architecture and scientific trust boundaries

## Boundaries

- **Data ingestion:** `alga_twin.data` accepts one cultivation run, with user-mapped source columns. Units must already be correct; no uncalibrated optical density conversion is performed.
- **Scientific core:** `alga_twin.model` solves a single-species, batch two-state Monod/light model. The reactor is well mixed and the light gradient is an **effective one-dimensional** approximation, not hydrodynamics.
- **Calibration:** `alga_twin.calibration` implements shared multi-run likelihoods, nuisance-reoptimized profiles, refusal gates and whole-run holdouts. `fitting` adapts baseline mu/yield estimation to the same gate. Noise SDs, initial states and fixed parameters condition the intervals.
- **Trust diagnostics:** `alga_twin.trust` computes local finite-difference elasticities and heuristic scenario departure warnings. These are **not** confidence intervals.
- **Scenario design:** `alga_twin.planner` performs a bounded discrete sample of surface light / initial nitrogen settings and marks non-dominated samples. This is neither guaranteed global optimisation nor validated experimental advice.
- **Interfaces:** Streamlit UI in `app.py`; scriptable `alga_twin` CLI in `alga_twin.cli`. Scientific logic is independent of UI.
- **Parameter evidence:** alga_twin.parameters separates species/source records from explicit numerical configurations; alga_twin.extinction fits user transmission measurements without source-data fabrication. LITERATURE blocks incomplete species configurations; DEMO requires selection.
- **Provenance:** `alga_twin.reporting` emits JSON run information and source-data checksum.

## Data flow

```text
CSV/DEMO --> strict ingest --> conditions --> constrained fit ----+
                                      |                           |
                                      +-------> scientific ODE <---+
                                                      |
                             +------------------------+-------------------+
                             |                        |                   |
                       LightScope                TrustLens           Planner grid
                             |                        |                   |
                             +------------------------+-------------------+
                                                      |
                                     Streamlit charts + CSV/JSON exports
```

## Mathematical conventions

- Dry biomass `X` in g/L.
- Extracellular nitrate-as-elemental-nitrogen `N` in mg N/L.
- Incident irradiance in µmol photons m⁻² s⁻¹.
- Optical path in metres.
- Extinction a0 in L^s (g DW)^-s m^-1, with dimensionless exponent 0 < s <= 1.
- Yield in g biomass/g elemental nitrogen.
- Rate constants in day⁻¹.

The solver tracks nitrogen consumption from **gross** biomass growth; a biomass-loss term removes biomass without explicit nitrogen recycling. This is not intended as a complete reactor elemental balance under cell death.

## Deployment and limitations

`requirements.txt` installs the editable package and UI runtime. Streamlit Community Cloud can use `app.py` directly; `Dockerfile` is a separate container option. No secrets, database, or external APIs are required. Deploying the code does **not** scientifically validate its predictions. User uploads reside in the application service memory during processing; only share non-confidential data with public hosting.

## Extending the model

`models.py` now exposes ModelBase.rhs/params/states and explicit Monod/Droop models,
with selectable Haldane or steady-state Han light, CTMI and diurnal forcing.
`optimum.py` keeps the printed Eq. 9 diagnostic separate from the general
boundary/compensation-root optimum. `model_ui.py` exposes these through an explicit
synthetic workspace. `calibration_io.py` loads explicit evidence-bearing jobs;
`calibration_ui.py` exposes joint profiles and labelled fold results. The baseline
calibration uses the same refusal gate. Joint models are not connected to the
legacy planner; supported model comparison remains pending. These models have
state/unit specifications and synthetic conservation/limiting tests, but no
independent biological evaluation. See SELECTABLE_MODELS.md and MODEL.md.
