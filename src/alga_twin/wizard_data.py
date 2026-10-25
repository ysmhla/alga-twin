"""Explicit wide CSV mapping and unit conversion; no biological defaults."""

import csv
from io import BytesIO

import numpy as np
import pandas as pd

from .biomass_calibration import DW_FACTORS, BiomassCalibration

TIME_FACTORS = {"day": 1.0, "hour": 1 / 24}
N_FACTORS = {"mg_N/liter": 1.0, "g_N/liter": 1000.0}


def read_wide_csv(raw: bytes) -> pd.DataFrame:
    if not raw or len(raw) > 2_000_000:
        raise ValueError("Upload a nonempty UTF-8 CSV of at most 2 MB")
    headings = next(csv.reader(BytesIO(raw).read().decode("utf-8-sig").splitlines()), [])
    if not headings or len(headings) != len(set(headings)) or any(not name.strip() for name in headings):
        raise ValueError("Use unique, nonempty CSV column headings")
    # Preserve identifiers such as 001 until explicit numeric field conversion.
    frame = pd.read_csv(BytesIO(raw), dtype=str, encoding="utf-8-sig")
    if not 1 <= len(frame) <= 5000 or not frame.columns.is_unique:
        raise ValueError("Use 1-5000 rows and unique column headings")
    return frame


def map_observations(
    data: pd.DataFrame,
    mapping: dict[str, str],
    units: dict[str, str],
    *,
    calibration: BiomassCalibration | None = None,
) -> pd.DataFrame:
    """Convert wide technical measurements to canonical long data without time shifting.

    Missing X/N/q cells are omitted; missing metadata and malformed cells refuse.
    Without a replicate column each row gets a distinct technical row id.
    Independent biological cultures must have separate run_id values.
    """
    allowed = {"time", "X", "N", "q", "run", "replicate"}
    if not {"time", "X"} <= mapping.keys() or not mapping.keys() <= allowed:
        raise ValueError("Map time and X; optional N, q, run and technical replicate")
    if len(set(mapping.values())) != len(mapping) or not set(mapping.values()) <= set(data.columns):
        raise ValueError("Each mapped field needs its own existing column")
    observables = set(mapping) & {"X", "N", "q"}
    if set(units) != observables | {"time"} or units["time"] not in TIME_FACTORS:
        raise ValueError("Confirm a supported unit for every mapped measurement and time")
    if calibration is None and units["X"] not in DW_FACTORS:
        raise ValueError("X must be dry weight; first calibrate OD/cell count with paired dry weights")
    if "N" in units and units["N"] not in N_FACTORS:
        raise ValueError("N must be elemental nitrogen, not nitrate-ion mass")
    if "q" in units and units["q"] != "g_N/g_DW":
        raise ValueError("Quota must be g_N/g_DW")
    times = pd.to_numeric(data[mapping["time"]], errors="raise").to_numpy(float)
    times = times * TIME_FACTORS[units["time"]]
    if np.any(~np.isfinite(times)) or np.any(times < 0) or times.max() > 365:
        raise ValueError(
            "Time must be finite, nonnegative and <=365 days from inoculation; no automatic shifting"
        )
    runs = (
        data[mapping["run"]].astype("string")
        if "run" in mapping
        else pd.Series("run-1", index=data.index)
    )
    reps = (
        data[mapping["replicate"]].astype("string")
        if "replicate" in mapping
        else pd.Series([f"row-{i}" for i in range(len(data))], index=data.index)
    )
    if (
        runs.isna().any()
        or reps.isna().any()
        or runs.str.strip().eq("").any()
        or reps.str.strip().eq("").any()
    ):
        raise ValueError("Run and technical replicate identifiers cannot be missing")
    frames = []
    for obs in ("X", "N", "q"):
        if obs not in mapping:
            continue
        present = (
            data[mapping[obs]].notna()
            & data[mapping[obs]].astype(str).str.strip().ne("")
        )
        value = pd.to_numeric(data.loc[present, mapping[obs]], errors="raise").to_numpy(float)
        if np.any(~np.isfinite(value)):
            raise ValueError("Measurements must be finite; omit missing values instead of infinity")
        if obs == "X":
            value = (
                calibration.predict(value, unit=units[obs])
                if calibration
                else value * DW_FACTORS[units[obs]]
            )
            unit = "g_DW/liter"
        elif obs == "N":
            value, unit = value * N_FACTORS[units[obs]], "mg_N/liter"
        else:
            unit = "g_N/g_DW"
        frames.append(
            pd.DataFrame(
                {
                    "run_id": runs[present],
                    "time_day": times[present],
                    "observable": obs,
                    "value": value,
                    "unit": unit,
                    "replicate": reps[present],
                }
            )
        )
    result = pd.concat(frames, ignore_index=True)
    if result.empty or len(result) > 15000 or set(result.run_id) != set(runs):
        raise ValueError("Every declared run needs measurements; at most 15000 mapped measurements")
    if result.duplicated(["run_id", "time_day", "observable", "replicate"]).any():
        raise ValueError("Duplicate measurement identity; distinct technical repeats need distinct ids")
    return result.sort_values(
        ["run_id", "time_day", "observable"], kind="stable"
    ).reset_index(drop=True)
