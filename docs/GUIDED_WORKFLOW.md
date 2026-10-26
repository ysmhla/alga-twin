# Guided upload to report

Public demo: https://alga-twin.streamlit.app/ . [Observed browser checks](smoke/README.md)
use explicitly labelled SYNTHETIC data; the [development rehearsal](smoke/v0_8_2_dev/README.md)
also exercises the actual file picker. Human novice acceptance is pending.

**Guided upload to report** is the landing workspace. It is accessible
without switching the research gate to DEMO. Its initial choice is **Upload my
measurements**, with user-declared MEASURED origin; teaching data require an
explicit SYNTHETIC worked-example or uploaded-data-origin selection. This origin
is retained in the job/report and is not independently verified. Switching origin
or removing the uploaded file clears all dependent results. The active filename
is displayed on return to Step 1; **Remove current CSV and results** resets the
uploader and all cached calculation state.

1. Download the blank CSV template if needed and fill it with your own data,
   then upload a UTF-8 wide CSV (<=2 MB, <=5000 rows). The template headings are
   time_day (days since inoculation), X (g DW/L), optional N (mg elemental N/L),
   run_id (culture) and replicate (technical reading). Other headings/units can
   be mapped in Step 2. The template contains no fabricated observations. One row is a sampling/technical
   measurement event; independent biological cultures need separate run ids.
2. Map time and biomass, optional elemental N, quota, run and technical replicate
   columns. Select each unit. The conversion preview is long-form, with all
   identities preserved. Time is from inoculation; no automatic zero shift.
3. Check the canonical units, culture ids and technical repeats. Missing
   measurement cells are omitted; malformed values are refused. Negative noisy
   assays are retained for additive errors, but cannot use log-normal errors.
4. Choose Monod/Droop and saturation/Haldane/steady-state Han light, optional CTMI
   and diurnal forcing. Supply every parameter/condition/initial state. Choose
   shared fitted parameters, numerical search bounds and fixed measurement SDs.
   These algorithm limits are not physiological ranges. Parameters remain
   UNVERIFIED after entry; typing a source URL does not verify it. The MEASURED
   tier records user-supplied research inputs, with evidence
   `user_supplied_not_verified`; it does not certify that an input was measured.
5. Fit/reprofile. Optionally compute leave-one-whole-run-out error with >=2
   independent cultures. Settings should be prespecified; repeated choice based
   on held-out errors invalidates their interpretation as untouched evaluation.
6. After a current fit exists, read the plain-language flags and split errors. Download self-contained HTML,
   PDF, complete evidence JSON, mapped data and reusable model-job JSON.

The app keys results to input bytes, converted data, complete configuration and
the proxy conversion. Revisiting mapping/units/model clears downstream results;
changing/removing the source clears all dependent work. A stale estimate/report
is withheld until a current fit exists. Uploads are kept in session memory, not
intentionally saved by the app; hosting infrastructure may have separate logs.

## Species and source gaps

The C. minutissima choice uses the audited catalogue only. Only source-reported
VERIFIED ranges are eligible as range presets. **No executable verified-range
preset currently exists.** Audited point values are not silently assigned ranges
or inserted into another growth equation. Extinction, f_C and a complete CTMI
triplet remain unset. Select the baseline workspace/LITERATURE gate to inspect
the catalogue and **Measure extinction directly** helper.

**I don't know my strain** keeps research parameter fields blank. Supply your own
inputs/methods or obtain identification/measurements; no other species' parameters
are substituted. Only the structural extinction exponent is explicitly selected
above the table, with matching coefficient units. Initial states are separately
supplied at inoculation; a noisy first observation is not silently treated as a
known initial condition.

## OD/cell-count helper

Open **OD / cell count calibration**. Upload paired proxy/DW measurements and map
the columns. Specify OD wavelength, cuvette path, blank/dilution, counting method,
strain and dry-weight assay in the conditions field. Choose linear/quadratic
equal-weight OLS with intercept. The helper shows in-sample R-squared, fitted
curve and residual scatter/table. It refuses insufficient/distinct levels,
nonfinite/negative pairs, decreasing/nonphysical curves and extrapolation.

The current-session conversion can be selected in wizard mapping. A measured
upload cannot use a SYNTHETIC conversion. Species identity must match; the app
does not establish transferability between instruments or conditions. All user
conversion estimates remain UNVERIFIED. No conversion interval is estimated and
its uncertainty is **not propagated** into growth-profile intervals; this is
explicit in the app/report. OD-to-DW calibration is not an extinction estimate.

## Reports and interpretation

Both formats include fit/data curves per run/state, estimate/interval method and
identifiability flags, fixed-noise assumptions, numerical search limits, input
hashes, origins, run conditions and complete parameter provenance. The HTML also
embeds full profile/point evidence as escaped text; JSON is the machine-readable
source. PDF uses embedded bundled fonts and wrapped/paginated tables; unusually
unsupported glyphs are escaped, while JSON retains the original strings. PDF
numbers use six significant figures for readable tables; JSON retains full
floating-point precision.

The complete interval method/confidence also appears above result tables, so
horizontal scrolling cannot hide it. Unsupported estimates/intervals are withheld. Descriptive training curves can
still appear; they are not supported forecasts. Held-out error is marked **not
computed** until requested. Failed folds retain their flags; no selectively
pooled successful-fold accuracy is reported. Synthetic held-outs are engineering
checks, not biological validation. Intervals are named conditional marginal
asymptotic likelihood intervals; empirical coverage is not established.

See [MODEL](MODEL.md), [calibration](CALIBRATION.md),
[verification](VERIFICATION.md), [usability status](USABILITY.md) and
[two executed teaching notebooks](https://github.com/ysmhla/alga-twin/blob/main/tutorials/README.md).
