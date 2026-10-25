# AlgaTwin benchmark scoreboard

Only registered, checked-input problems are attempted. No accepted measured cultivation dataset is present in this registry. SYNTHETIC results verify software behavior, not independent biological prediction accuracy.

Estimates and whole-run CV: AlgaTwin profile-gated SciPy engine. External full-data profile cross-check: pyPESTO. Search bounds/SDs are explicit assumptions; intervals are conditional marginal asymptotic profiles. Incomplete held-out folds are not pooled into an optimistic score.

| Dataset | Origin | Model | In-sample RMSE | Held-out RMSE | Scored folds | Conditional parameter gate | Licence |
|---|---|---|---|---|---|---|---|
| synthetic_batch | SYNTHETIC | monod/monod | N: 0.301342 mg_N/liter; X: 0.00279633 g_DW/liter | N: 0.298713 mg_N/liter; X: 0.00284467 g_DW/liter | 3/3 | SUPPORTED | MIT |

### synthetic_batch

Licence: MIT; https://github.com/ysmhla/alga-twin/blob/main/LICENSE; review status: REPOSITORY_LICENSE.

Attribution: Copyright (c) 2026 AlgaTwin contributors; synthetic software test fixture.

DOI: None; status: NOT_APPLICABLE_SYNTHETIC.

PEtab validation: 0 issue(s); native model reader required. pyPESTO 0.7.0: 13 profile points; NLL difference 9.9476e-13.

Software: AlgaTwin 0.6.0; PEtab 0.9.0; pyPESTO 0.7.0; Python 3.12.14.
