"""Write reproducible SYNTHETIC decision artifacts; not a measured benchmark."""

import json
from pathlib import Path

from alga_twin import __version__
from alga_twin.decision_io import load_experiments, load_selection, synthetic_decision_problem
from alga_twin.experiment_design import rank_experiments
from alga_twin.model_selection import compare_models


def main():
    out = Path(__file__).resolve().parents[1] / "docs" / "decision_example"
    out.mkdir(exist_ok=True)
    config, data, proposals = synthetic_decision_problem()
    candidates, errors = load_selection(config, data)
    comparison = compare_models(candidates, errors, **config["decision"])
    reports = {"model_comparison": comparison.report()}
    if comparison.recommendation:
        chosen = next(c for c in candidates if c.name == comparison.recommendation)
        ranking = rank_experiments(chosen.runs, comparison.fits[chosen.name], load_experiments(proposals))
        reports["experiment_ranking"] = ranking.report()
    for name, value in {"problem": config, "proposals": proposals, **reports}.items():
        (out / f"{name}.json").write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    data.to_csv(out / "SYNTHETIC_observations.csv", index=False)
    (out / "LICENCE.txt").write_text((out.parents[1] / "LICENSE").read_text())
    (out / "README.md").write_text(
        f"# SYNTHETIC conditional decision example — v{__version__}\n\n"
        "Licence: MIT (LICENCE.txt). Origin: SYNTHETIC. All model inputs are UNVERIFIED / DEMO.\n\n"
        "Generated with `python examples/decision_support.py`. No measured or digitised data.\n"
        "Decision thresholds and fixed noise are explicit teaching assumptions, not biological ranges.\n"
        "Selection is in-sample, conditional on fixed values/initial states/noise. No held-out error\n"
        "is computed by this example. Profile intervals retain their named method; Fisher SD/volume\n"
        "ratios are local approximations, not intervals or empirical coverage.\n\n"
        f"Observed result: {comparison.status}; {comparison.recommendation}.\n"
    )
    print(f"{comparison.status}: {comparison.recommendation}; artifacts: {out}")


if __name__ == "__main__":
    main()
