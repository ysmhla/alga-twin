# Verification record — 2026-10-25

Verified locally with Python 3.12. Streamlit 1.66.1 and Plotly 6.9.0 were installed from the package registry alongside the scientific package.

| Gate | Result | Evidence / caveat |
|---|---|---|
| Scientific kernel, CSV importer, CLI and exports | PASS | Original 33 tests rerun successfully |
| Real Streamlit widget runtime | PASS | `tests/test_streamlit_runtime.py`, using `streamlit.testing.v1.AppTest` rather than a fake UI |
| Interactive workflow | PASS | Seven tabs render; darkness reduces growth; calibration converges; changing inputs invalidates active fit; saved scenarios preserve parameter snapshots; nine-point planner completes; changing conditions invalidates planner display; clear resets scenarios |
| HTTP server | PASS | Actual `streamlit run app.py` process returned HTTP 200 and `ok` at `/_stcore/health`, and HTTP 200 HTML at `/` |
| Python compilation and fatal-error lint | PASS | Commands below |
| Visual browser verification | NOT TESTED | Cloud browser could not reach the local server; no rendered browser screenshot is claimed |
| GitHub publication and cloud CI | BLOCKED | Public repository creation was rejected by automatic approval review pending explicit user authorization |
| Hosted Streamlit deployment | NOT DEPLOYED | No hosting application has been created |
| Docker build/run | NOT TESTED | Docker executable is unavailable |
| Independent laboratory validation | NOT VALIDATED | Calibration recovery uses synthetic data only |

## Reproduce

```bash
python -m pip install -r requirements.txt -e '.[dev]'
python -m pytest -q
python -m compileall -q src app.py tests
python -m ruff check --select E9,F63,F7,F82 src app.py tests
```

The real Streamlit test is skipped when Streamlit is absent, allowing scientific-package-only installations. CI installs dashboard dependencies, so it executes the test.

Streamlit currently emits deprecation notices for `use_container_width`; the exercised workflow still passes. No claim of pixel-level UI quality, cloud availability, independent predictive accuracy or formal uncertainty intervals is made.
