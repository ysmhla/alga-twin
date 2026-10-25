# Deployment and release checklist

## Streamlit Community Cloud

1. Use the existing GitHub repository `ysmhla/alga-twin`.
2. Use its checked `main` branch; do **not** flatten the `src/alga_twin` directory.
3. Confirm the `Scientific Python CI` GitHub Actions workflow completes on Python 3.11 and 3.12.
4. In [Streamlit Community Cloud](https://share.streamlit.io/), create a new app with repository `ysmhla/alga-twin`, branch `main`, entry point `app.py`.
5. No secret values are needed. Verify that LITERATURE initially blocks missing species parameters; explicitly select DEMO and check charts, tabs and exports.
6. Run the public deployment smoke checklist below before publicising the link.

This repository contains **deployment configuration**, not proof that hosting was deployed. GitHub connection alone does not publish a Streamlit Cloud app.

## Render deployment (alternate hosting)

The repository includes a [Render Blueprint](../render.yaml) with a Python service, dependency installation, Streamlit run command bound to `$PORT` and an HTTP health check. Import the GitHub repository in Render and approve the deployment plan. Billing/plan selection and account authorization are handled by the hosting provider, not this project. No actual Render deploy was performed in preparation of this release.

## Local run

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Docker

```bash
docker build --tag alga-twin:0.3 .
docker run --rm --publish 8501:8501 alga-twin:0.3
```

Default local URL: `http://localhost:8501`.

## Smoke checklist

- [ ] Startup loads with no import/asset errors.
- [ ] LITERATURE is the initial screen; missing species parameters do not trigger simulation.
- [ ] Direct extinction helper rejects invalid units/signals.
- [ ] Explicitly selected DEMO identifies all parameter assumptions as UNVERIFIED.
- [ ] `Fit supported parameters` returns estimates and diagnostics.
- [ ] `Virtual Reactor` responds to irradiance and nitrogen sliders.
- [ ] `LightScope` heatmap reflects optical attenuation.
- [ ] `ScenarioLab` stores two conditions and exports comparisons.
- [ ] `Run manifest` downloads JSON with model revision and input checksum.
- [ ] Invalid/empty uploads show a validation error and do not crash process.
- [ ] Guided workflow maps units, profiles and exports HTML/PDF reports.
- [ ] Changed source/mapping/model choices withhold stale reports.
- [ ] Paired OD/cell-count helper refuses extrapolation and shows residuals/R-squared.
- [ ] Unknown-strain and missing species inputs remain unset.
- [ ] Save actual app screenshots; a rendered report is not an app screenshot.
- [ ] Mobile and desktop layouts remain readable.

## Limitations for public hosting

The app deliberately has no persistent user storage; session data may be reset when the service restarts. No authentication. Use only non-confidential experiments on public third-party hosting. Python dependency ranges are constrained, but there is no frozen lockfile in this alpha release. CI tests numerical kernel and synthetic demo, not full browser automation.

## Current hosting prerequisite (2026-10-26)

The observed https://share.streamlit.io/ screen requires account sign-in and
states that signing in accepts its Terms of Service. The account holder must
review/complete that step. [Captured screen](../assets/hosting-pending.jpg).
No app was deployed and no public AlgaTwin app URL is available. After sign-in,
use repository ysmhla/alga-twin, branch main, entry point app.py; complete the
smoke checklist and real app screenshots before claiming deployment.
