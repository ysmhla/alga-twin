"""Reproducible command-line entry points for scripted use without Streamlit."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from .data import read_experiment_csv
from .demo import demo_parameters
from .fitting import fit_experiment
from .model import Conditions, simulate
from .parameters import provenance_rows
from .reporting import model_dataframe_to_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AlgaTwin research prototype — illustrative, not validated")
    sub = parser.add_subparsers(dest="command", required=True)
    simulate_command = sub.add_parser("simulate", help="Write illustrative time series to CSV")
    simulate_command.add_argument("--days", type=float, default=12.0)
    simulate_command.add_argument("--light", type=float, default=180.0)
    simulate_command.add_argument("--nitrogen", type=float, default=70.0)
    simulate_command.add_argument("--biomass", type=float, default=0.1)
    simulate_command.add_argument("--path-cm", type=float, default=5.0)
    simulate_command.add_argument("--output", type=Path, required=True)
    fit_command = sub.add_parser("fit", help="Fit restricted Monod-light parameter subset from strict CSV")
    fit_command.add_argument("--input", type=Path, required=True)
    fit_command.add_argument("--light", type=float, required=True, help="Measured irradiance in umol/m²/s")
    fit_command.add_argument("--path-cm", type=float, required=True)
    fit_command.add_argument("--initial-nitrogen", type=float, default=70.0)
    fit_command.add_argument("--output", type=Path, required=True)
    for command in (simulate_command, fit_command):
        command.add_argument(
            "--demo", action="store_true", help="Explicitly use UNVERIFIED synthetic parameters"
        )
    args = parser.parse_args(argv)
    if not args.demo:
        parser.error(
            "No complete literature Monod preset exists. Supply --demo for synthetic assumptions only."
        )
    if args.command == "simulate":
        c = Conditions(args.biomass, args.nitrogen, args.light, args.path_cm / 100.0)
        times = np.linspace(0, args.days, int(max(2, np.ceil(args.days * 12))) + 1)
        frame = simulate(times, c, demo_parameters())
        args.output.write_bytes(model_dataframe_to_csv(frame))
        print(f"Wrote {len(frame)} ILLUSTRATIVE timepoints: {args.output}")
    else:
        data = read_experiment_csv(args.input.read_bytes())
        c = Conditions(float(data.biomass_g_L.iloc[0]), args.initial_nitrogen, args.light, args.path_cm / 100)
        result = fit_experiment(data, c, demo_parameters())
        payload = {
            "success": result.success,
            "parameters": asdict(result.parameters),
            "parameter_provenance": provenance_rows(result.parameters),
            "fitted_names": result.fitted_names,
            "rmse_biomass_g_L": result.rmse_biomass_g_L,
            "rmse_nitrogen_mg_L": result.rmse_nitrogen_mg_L,
            "warnings": result.warnings,
            "scientific_status": "In-sample only, not independently validated",
        }
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote constrained in-sample fit: {args.output}")
        if not result.success:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
