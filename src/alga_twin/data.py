"""A deliberately strict and documented single-run experimental CSV contract."""

from __future__ import annotations

from io import BytesIO

import numpy as np
import pandas as pd

COLUMNS = ("time_day", "biomass_g_L", "nitrate_n_mg_L")
MAX_BYTES = 2_000_000
MAX_ROWS = 5_000


def read_experiment_csv(raw: bytes, *, column_map: dict[str, str] | None = None) -> pd.DataFrame:
    if len(raw) > MAX_BYTES:
        raise ValueError("CSV too large (maximum 2 MB)")
    try:
        data = pd.read_csv(BytesIO(raw), encoding="utf-8-sig")
    except (UnicodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise ValueError("Invalid UTF-8 CSV") from exc
    if len(data) > MAX_ROWS:
        raise ValueError("Too many records (maximum 5,000)")
    if column_map is not None:
        targets = {"time_day", "biomass_g_L", "nitrate_n_mg_L"}
        if not {"time_day", "biomass_g_L"}.issubset(column_map) or any(k not in targets for k in column_map):
            raise ValueError("Column mapping must define time_day and biomass_g_L")
        if len(set(column_map.values())) != len(column_map):
            raise ValueError("Each measurement must map to a different CSV column")
        if any(column not in data.columns for column in column_map.values()):
            raise ValueError("Selected column was not found in CSV")
        data = data[list(column_map.values())].rename(columns={v: k for k, v in column_map.items()})
    return validate_experiment(data)


def validate_experiment(source: pd.DataFrame) -> pd.DataFrame:
    """Validate a single cultivation run; preserve missing nitrogen observations."""
    df = source.copy()
    if df.columns.duplicated().any():
        raise ValueError("CSV has duplicate column names")
    required = ("time_day", "biomass_g_L")
    missing = [col for col in required if col not in df]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")
    if "nitrate_n_mg_L" not in df:
        df["nitrate_n_mg_L"] = np.nan
    if len(df) < 4 or len(df) > MAX_ROWS:
        raise ValueError("Single-run CSV must contain 4–5,000 observations")
    for col in COLUMNS:
        try:
            df[col] = pd.to_numeric(df[col], errors="raise").astype(float)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Column {col} must contain numeric values") from exc
    if df[["time_day", "biomass_g_L"]].isna().any().any():
        raise ValueError("Time and biomass values cannot be missing")
    if df[["time_day", "biomass_g_L"]].isin([np.inf, -np.inf]).any().any():
        raise ValueError("Time and biomass must be finite")
    n_present = df["nitrate_n_mg_L"].dropna()
    if not np.isfinite(n_present).all():
        raise ValueError("Nitrogen values must be finite when present")
    df = df.sort_values("time_day").reset_index(drop=True)
    t, x = df["time_day"].to_numpy(), df["biomass_g_L"].to_numpy()
    if (t < 0).any() or t[-1] - t[0] > 365 or (np.diff(t) <= 0).any():
        raise ValueError("Time must be unique, nonnegative, and span at most 365 days")
    if (x <= 0).any() or (x > 100).any():
        raise ValueError("Dry biomass must be positive and at most 100 g/L")
    if (n_present < 0).any() or (n_present > 10000).any():
        raise ValueError("Nitrogen observations must be 0–10,000 mg N/L")
    # Normalize the first observation as local time zero for calibration.
    df["time_day"] = df["time_day"] - t[0]
    return df[list(COLUMNS)]
