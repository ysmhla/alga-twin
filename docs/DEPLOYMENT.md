# Deployment and smoke record

## Current public demo — 2026-10-26

**DEPLOYED:** https://alga-twin.streamlit.app/

Repository ysmhla/alga-twin, branch main, entry point app.py. App settings showed
**public and searchable**. Python 3.12 was selected and rebuilt; logs confirmed
Python 3.12.15 and Streamlit 1.66.1. Initial smoke source was
0b1090d45c2741996e66047058d7b73c1957b945 (v0.7.0). See
[actual browser evidence, hashes and exports](smoke/README.md).

The prior account sign-in/terms prerequisite was completed by the account holder.
assets/hosting-pending.jpg is historical evidence, not the current status.
No new permissions or viewer email invitations were added during smoke checks.
No application secrets were required. Changes pushed to main can restart the
Streamlit session; uploads are not intentionally persisted by the app.

## Observed live smoke checklist

- [x] App startup and literature provenance loaded without an app traceback.
- [x] LITERATURE initially blocks missing species parameters without a synthetic fallback.
- [x] Explicitly selected SYNTHETIC conversion shows UNVERIFIED assumptions, residuals and in-sample R-squared.
- [x] Paired-DW helper refuses signal extrapolation beyond its measured domain.
- [x] Guided SYNTHETIC example maps units and fits/reprofiles three cultures.
- [x] Three whole-run held-out folds score; training/held-out rows stay separate.
- [x] HTML/PDF/JSON reports download with methods, flags, origins and provenance.
- [x] Revisiting model inputs withholds stale report exports.
- [x] Actual desktop app screenshots captured.
- [x] Invalid non-measurement CSV upload refused without falling back to simulation.
- [x] Baseline DEMO zero-light/zero-loss export retained constant biomass and N.
- [ ] Actual measured-CSV upload-to-report browser acceptance (requires human data/inputs).
- [ ] Independent novice <5-minute completion and five observed issues/fixes.
- [ ] Mobile layout, full baseline scenario/planner browser sweep and Docker build/run.

Automated tests separately cover missing/invalid data, unit conversions, quota/N
balances, profile refusal, unknown-strain blank inputs and widget-state changes.
They do not establish human usability or biological validation. No Streamlit
deprecation appeared in retained console messages for tested paths; the retained
browser-extension metadata errors are not an app scientific result.

## Recreate hosting

Use Streamlit Community Cloud -> Deploy from repo -> ysmhla/alga-twin -> main ->
app.py. In app settings select Python 3.12 (covered in CI). Select a free public
URL; account-holder actions handle sign-in, terms and any new access request.
Confirm the page actually loads and run the scoped smoke checklist before
claiming deployment. Do not publish confidential experiments on a public demo.

## Local / alternate hosting

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    streamlit run app.py

render.yaml and Dockerfile remain configuration examples. **Render deployment
and Docker build/run: NOT TESTED.** No claim of a frozen dependency lockfile,
production hardening, persistence/authentication or independent biological
validation is made for this alpha prototype.


## Current documentation and incremental update check — 2026-10-26

Public MkDocs site: https://ysmhla.github.io/alga-twin/ . GitHub Pages is configured
for Actions. Strict build/deployment 40291099481 completed from merged v0.8.1
source 5cd79163d38b505378e992b26e2e2e1add93fd7d; the actual public home/navigation
was inspected. mkdocs.yml targets the repository's main branch for Edit links.

The live app displayed v0.8.1 and completed the new SYNTHETIC model-selection and
Fisher ranking/export smoke without a manual reboot/cache-clearing action. New
modules import the job-identity helper independently of a cached calibration API;
a subprocess regression checks that observed missing-export failure. This is a
compatibility measure, not a guarantee about every provider's hot-reload behaviour.
See smoke/v0_8_1/README.md and VERIFICATION.md for source/counts/limits.
