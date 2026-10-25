"""Synthetic observation-model units, limiting case, mass conversion and refusals."""

import numpy as np
import pandas as pd
import pytest

from alga_twin.biomass_calibration import fit_biomass_calibration
from alga_twin.wizard_data import map_observations, read_wide_csv


def fit(x=None, y=None, **changes):
    x = np.linspace(0, 1, 8) if x is None else np.asarray(x)
    y = 0.04 + 0.5 * x if y is None else np.asarray(y)
    options = {
        "kind": "OD",
        "signal_unit": "dimensionless",
        "dry_weight_unit": "g_DW/liter",
        "degree": 1,
        "species": "SYNTHETIC",
        "conditions": "SYNTHETIC teaching pairs; no instrument",
        "origin": "SYNTHETIC",
    }
    options.update(changes)
    return fit_biomass_calibration(
        pd.DataFrame({"signal": x, "dry_weight": y}), **options
    )


def test_linear_quadratic_recovery_and_zero_curvature_limit():
    linear, quadratic = fit(), fit(degree=2)
    x = np.linspace(0, 1, 51)
    assert linear.coefficients == pytest.approx((0.04, 0.5), abs=1e-12)
    assert quadratic.coefficients == pytest.approx((0.04, 0.5, 0), abs=1e-12)
    assert linear.r_squared == pytest.approx(1)
    np.testing.assert_allclose(
        linear.predict(x, unit="dimensionless"),
        quadratic.predict(x, unit="dimensionless"),
    )
    levels = np.linspace(0, 1, 8)
    nonlinear = fit(y=0.04 + 0.4 * levels + 0.1 * levels**2, degree=2)
    assert nonlinear.coefficients == pytest.approx((0.04, 0.4, 0.1))
    assert nonlinear.report()["interval"] is None
    assert nonlinear.status == "UNVERIFIED"


def test_cell_and_dw_units_preserve_total_dry_mass():
    cells_ml = np.linspace(0, 1e6, 8)
    y = 0.04 + cells_ml * 5e-7
    a = fit(cells_ml, y, kind="cell_count", signal_unit="cells/mL")
    b = fit(
        cells_ml * 1000,
        y * 1000,
        kind="cell_count",
        signal_unit="cells/L",
        dry_weight_unit="g_DW/meter**3",
    )
    np.testing.assert_allclose(
        a.predict(cells_ml, unit="cells/mL"),
        b.predict(cells_ml * 1000, unit="cells/L"),
    )
    assert (a.predict([1e6], unit="cells/mL") * 2)[0] == pytest.approx(
        (b.predict([1e9], unit="cells/L") * 2)[0]
    )
    assert a.coefficients == pytest.approx(b.coefficients)
    with pytest.raises(ValueError, match="dry weight"):
        fit(dry_weight_unit="g_C/liter")
    with pytest.raises(ValueError, match="Choose OD"):
        fit(signal_unit="absorbance/cm")


def test_conversion_refuses_extrapolation_bad_shapes_and_insufficient_data():
    result = fit()
    for value in (-1e-12, 1 + 1e-12):
        with pytest.raises(ValueError):
            result.predict([value], unit="dimensionless")
    with pytest.raises(ValueError, match="increasing"):
        fit(y=np.linspace(0.6, 0.1, 8))
    with pytest.raises(ValueError, match="increasing"):
        x = np.linspace(0, 1, 8)
        fit(x, 0.2 + x - 0.8 * x * x, degree=2)
    for x, y in [
        ([0, 1], [0.1, 0.5]),
        ([1] * 5, [0.1, 0.2, 0.3, 0.4, 0.5]),
        ([0, 1, 2, 3], [0.2] * 4),
    ]:
        with pytest.raises(ValueError):
            fit(x, y)
    with pytest.raises(ValueError, match="finite"):
        fit(y=[np.nan] * 8)
    with pytest.raises(ValueError, match="strain"):
        fit(conditions="")


def test_wide_mapping_units_replicates_missing_values_and_ids():
    data = read_wide_csv(
        b"culture,hour,DW,N,tech\n001,0,100,0.04,01\n001,24,200,,01\n001,24,210,0.02,02\n"
    )
    result = map_observations(
        data,
        {"run": "culture", "time": "hour", "X": "DW", "N": "N", "replicate": "tech"},
        {"time": "hour", "X": "g_DW/meter**3", "N": "g_N/liter"},
    )
    assert set(result.run_id) == {"001"} and set(result.replicate) == {"01", "02"}
    assert len(result) == 5 and set(result.time_day) == {0, 1}
    assert result.loc[result.observable.eq("X"), "value"].tolist() == pytest.approx([0.1, 0.2, 0.21])
    assert result.loc[result.observable.eq("N"), "value"].tolist() == pytest.approx([40, 20])
    assert set(result.unit) == {"g_DW/liter", "mg_N/liter"}


def test_wide_proxy_range_and_unit_refusals():
    data = pd.DataFrame({"t": [0, 1, 2, 3], "x": [0, 0.2, 0.7, 1.0]})
    mapping = {"time": "t", "X": "x"}
    units = {"time": "day", "X": "dimensionless"}
    with pytest.raises(ValueError, match="first calibrate"):
        map_observations(data, mapping, units)
    result = map_observations(data, mapping, units, calibration=fit())
    np.testing.assert_allclose(result.value, 0.04 + 0.5 * data.x)
    data.loc[3, "x"] = 1.01
    with pytest.raises(ValueError, match="Extrapolation refused"):
        map_observations(data, mapping, units, calibration=fit())
    with pytest.raises(ValueError, match="own existing"):
        map_observations(data, {"time": "t", "X": "t"}, {"time": "day", "X": "g_DW/liter"})
    data["other"] = 1.0
    with pytest.raises(ValueError, match="elemental nitrogen"):
        map_observations(
            data,
            {**mapping, "N": "other"},
            {**units, "X": "g_DW/liter", "N": "mg_NO3/liter"},
        )


def test_wide_no_time_shift_or_silent_bad_cell_drop():
    data = pd.DataFrame({"t": [2, 3, 4, 5], "x": [0.1, 0.2, 0.3, 0.4]})
    args = ({"time": "t", "X": "x"}, {"time": "day", "X": "g_DW/liter"})
    assert map_observations(data, *args).time_day.min() == 2
    data.loc[2, "x"] = np.inf
    with pytest.raises(ValueError, match="finite"):
        map_observations(data, *args)
    data["x"] = [".1", ".2", "bad", ".3"]
    with pytest.raises(ValueError):
        map_observations(data, *args)
    with pytest.raises(ValueError, match="2 MB"):
        read_wide_csv(b"a" * 2_000_001)
    with pytest.raises(ValueError, match="unique"):
        read_wide_csv(b"time,time\n0,1\n")
