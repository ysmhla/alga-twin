# Usability evidence and outstanding acceptance

**Timed novice upload-to-report study: NOT TESTED.** No human timings, participant
feedback, five observed human issues or <5-minute success claim is available.
AppTest is automated widget/state verification, not a novice usability study.
The engineering items below must not be presented as human study observations.

## Five engineering findings and fixes

| Finding from code review/automated checks | Fix/evidence |
|---|---|
| OD/cell count had no paired DW conversion; growth CSV required preconverted data | Separate linear/quadratic helper, residuals/R-squared, units and extrapolation refusal; test_biomass_wizard + test_guided_ui |
| The literature stop occurred before workspace navigation, hiding non-simulation tasks | Workspace navigation precedes the gate; guided/OD paths accessible while baseline literature simulation still blocks missing values |
| Initial wizard Continue button modified an already-created Streamlit widget key and crashed (reproduced by AppTest) | Pending-stage value applied before next widget creation; end-to-end AppTest now traverses six steps |
| New input/mapping/model choices could leave an old report or proxy conversion available | Source/config signatures and conservative invalidation; back-navigation/source-removal and proxy-change AppTests |
| CSV library silently mangles duplicate headings, obscuring the intended mapping | Check original CSV header before pandas; duplicate-column refusal test |

These fixes do not establish that the interface is understandable to a new user.
Research setup still requires complete parameter evidence and noise assumptions;
there is no claim that an unknown strain with missing inputs can be fitted in
five minutes.

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

The PDF report is generated and locally rendered for visual review; its page
preview is **a report preview, not an app screenshot**. The current environment
does not permit a browser connection to the local app or local-file browser
previews. Actual app browser screenshots and public-host smoke checks remain
pending a reachable deployed app. No pixel review of the Streamlit app is claimed.
Streamlit Cloud account setup/sign-in/terms also require the account holder as
applicable. See DEPLOYMENT.md for the prepared smoke checklist.
