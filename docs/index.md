# AlgaTwin

Transparent batch microalgal modelling, explicit parameter evidence and
conditional calibration. **ALPHA: no independent biological validation.**

[Open the public demo](https://alga-twin.streamlit.app/) ·
[Source and installation](https://github.com/ysmhla/alga-twin) ·
[Archived v0.8.1 software / DOI](https://zenodo.org/records/23665342)

## Try the teaching workflow

1. Open the app and choose **Guided upload to report**.
2. Select **SYNTHETIC worked example** explicitly.
3. Follow column mapping and unit checks, then choose the supplied DEMO model.
4. Fit, review the identifiability gate and read/export the report.
5. Open **Model support and next experiment** for synthetic model comparison
   and top-three proposed experiments with reasons.

See [the full guided workflow](GUIDED_WORKFLOW.md). A human novice timing study
has not been conducted; no under-five-minute acceptance claim is made.

## Bring your own Chlorella minutissima data

Missing source ranges, extinction and carbon fraction remain unset. The species
catalogue is not a complete executable preset. Use matched dry-weight and optical
measurements, explicit units and legally reusable data. [Read the source audit](PARAMETER_AUDIT.md)
and [model equations/units](MODEL.md) before selecting fixed assumptions.

[Calibration](CALIBRATION.md) separates in-sample fit from whole-run held-out
errors. Flat/unsupported profiles withhold point estimates. [Decision support](DECISION_SUPPORT.md)
conditions model choice and local Fisher experiment ranking on explicit fixed
inputs and noise; expected uncertainty reduction is not a confidence interval.

## Check what is established

- [Actual test, CI and browser evidence](VERIFICATION.md).
- [Current implementation and unresolved acceptance](RELEASE_STATUS.md).
- [Publication/DOI status](PUBLICATION.md).
- [Unreviewed related-work table](RELATED_WORK.md): no novelty claim.
- [MIT licence](https://github.com/ysmhla/alga-twin/blob/main/LICENSE).

The Python API/CLI are available from built source distributions/wheels. The
source checkout includes the Streamlit app, benchmark and tutorials. The v0.8.1
software archive is published with version DOI **10.5281/zenodo.23665342**.
No PyPI upload or journal acceptance is established.
