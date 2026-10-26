# Usability evidence and outstanding acceptance

**Timed novice upload-to-report study: NOT TESTED.** No human timings, participant
feedback, five observed human issues or <5-minute success claim is available.
AppTest is automated widget/state verification, not a novice usability study.
The engineering items below must not be presented as human study observations.

## Engineering findings and fixes (not a human study)

| Finding from code review/automated checks | Fix/evidence |
|---|---|
| OD/cell count had no paired DW conversion; growth CSV required preconverted data | Separate linear/quadratic helper, residuals/R-squared, units and extrapolation refusal; test_biomass_wizard + test_guided_ui |
| The literature stop occurred before workspace navigation, hiding non-simulation tasks | Workspace navigation precedes the gate; guided/OD paths accessible while baseline literature simulation still blocks missing values |
| Initial wizard Continue button modified an already-created Streamlit widget key and crashed (reproduced by AppTest) | Pending-stage value applied before next widget creation; end-to-end AppTest now traverses six steps |
| New input/mapping/model choices could leave an old report or proxy conversion available | Source/config signatures and conservative invalidation; back-navigation/source-removal and proxy-change AppTests |
| CSV library silently mangles duplicate headings, obscuring the intended mapping | Check original CSV header before pandas; duplicate-column refusal test |
| Agent browser review: interval-method column can be outside horizontal scrolling | v0.7.1 shows complete method/confidence above all result tables; existing guided AppTest checks readable context |

These fixes do not establish that the interface is understandable to a new user.
Research setup still requires complete parameter evidence and noise assumptions;
there is no claim that an unknown strain with missing inputs can be fitted in
five minutes. An agent browser smoke test is now recorded in smoke/README.md.
The built-in worked example does not exercise file upload; a novice upload
acceptance test requires an actual upload with a documented data origin.

## Additional agent review — 0.8.2.dev0

This is an agent-operated desktop/source review, not an independent participant
study. The pre-fix hosted upload page was inspected and a real file-picker upload
of the repository's MIT-licensed SYNTHETIC CSV reached its preview. No laboratory
measurements, user quotes or novice timing are claimed.

| Observed issue and evidence type | Development fix | Check |
|---|---|---|
| Fresh hosted sessions landed on the incomplete literature gate before the guided task (browser) | Guided upload is the landing workspace; the baseline literature gate remains available | Empty landing AppTest refuses silent demo/report fallback |
| Upload page explained a wide table but offered no downloadable header template or visible 5,000-row limit (browser/source) | Blank template plus heading/unit/culture/technical-repeat guidance and limits | Actual empty landing renders the download; numerical mapping tests retained |
| Uploaded files were always routed as measured, even for a deliberately uploaded synthetic fixture (source, with actual pre-fix upload preview) | Explicit uploaded-data-origin choice; default user-declared MEASURED; explicit SYNTHETIC retains DEMO parameter provenance | Uploaded-byte AppTest checks job run origins and parameter tiers |
| Removing the file without changing input mode returned before clearing previous source/results (source) | Clear dependent data, configuration, fit, CV and proxy state when upload is absent | File-removal regression withholds all old results/report |
| Result-navigation button was enabled before a fit existed (source) | Enable it only for a current signature-matching fit | Actual Streamlit test checks disabled-before-fit and enabled-after-fit |
| Back-navigation made the browser picker/origin display confusing despite retained source bytes (post-fix browser review) | Retain the declaration outside widget state, show the active filename and provide an explicit CSV/results reset with a fresh uploader key | Return-navigation/origin persistence and three reset-path AppTests; live retest recorded separately |
| About screen still called implemented model support/design features future milestones; paper still said no software DOI (source) | Correct feature status and cite the actual released v0.8.1 DOI | Text review; no model or citation identity invented |

Changing the uploaded origin also invalidates a prior synthetic fit/configuration.
The declaration records what the uploader says; it does not independently verify
that measurements are biological observations. The archived v0.8.1 files/tag are
preserved; these changes are an unreleased development snapshot. The [post-deployment CSV-to-report rehearsal](smoke/v0_8_2_dev/README.md)
records actual file-picker uploads, parsed HTML/PDF/JSON exports and 3/3 synthetic
whole-run holdouts. Its 192.868-second agent timing belongs specifically to source
806212f064cbd6a9f3bfa099a2cd4f39fe18f64c, before the later return-navigation/reset patch. None of these
items is substituted into the human participant table below.

## Concrete human study protocol (pending)

Use a new user who has not built the app. Prepare a legally reusable dataset and
complete, prespecified input assumptions separately; record whether this is the
SYNTHETIC worked example or measured data. Do not coach during the timed task.

- Task: upload -> map columns -> check units -> choose model -> fit -> export/read
  report, then correctly identify in-sample vs held-out error and missing values.
- Start timer at first upload interaction; stop when the report is saved and the
  participant explains its main identifiability/validation limitation. Include
  computation time. Record setup/training time separately.
- Record total seconds, completion/refusal/errors, help requests, test environment,
  version, dataset origin, and consented notes. A successful refusal of an
  unsupported model is not equivalent to recovering an estimate.
- Acceptance requested by the human: <300 seconds and five **actually observed**
  issues with subsequent fixes/retests. Record observations below only after the
  test; do not invent participant quotes, timings or issues.

| Participant/session | Version/data origin | Seconds | Outcome | Observed issue | Fix/retest |
|---|---|---|---|---|---|
| NOT TESTED | - | - | Pending human participation | - | - |

## Screenshots and hosting

**Public demo deployed:** https://alga-twin.streamlit.app/ . Actual desktop browser
screenshots, downloaded SYNTHETIC reports and scoped checks are in
[the smoke record](smoke/README.md). Python 3.12.15 was observed after selecting
and rebuilding the runtime. Sharing was explicitly public/searchable.

The three-run synthetic fit/profile/held-out report path worked in agent-operated
browser checks. Proxy extrapolation and stale-report withholding also worked.
These observations do not establish a new user's timing or comprehension. The
human table above remains NOT TESTED; no participant quotes/issues/timings are
invented. Mobile review and real measured-CSV browser acceptance remain pending.
