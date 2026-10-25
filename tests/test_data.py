import numpy as np
import pandas as pd
import pytest

from alga_twin.data import read_experiment_csv, validate_experiment


def test_accept_biomass_only():
    frame=read_experiment_csv(b'time_day,biomass_g_L\n1,0.1\n2,0.2\n3,0.3\n4,0.4\n')
    assert list(frame.columns)==['time_day','biomass_g_L','nitrate_n_mg_L']
    assert frame.time_day.iloc[0]==0
    assert frame.nitrate_n_mg_L.isna().all()


def test_sparse_nitrogen_is_preserved():
    frame=read_experiment_csv(b'time_day,biomass_g_L,nitrate_n_mg_L\n0,.1,70\n1,.2,\n2,.3,40\n3,.4,10\n')
    assert np.isnan(frame.nitrate_n_mg_L.iloc[1])


@pytest.mark.parametrize('text',[
    'time_day,biomass_g_L\n0,.1\n1,.2\n2,.3\n3,-.4\n',
    'time_day,biomass_g_L\n0,.1\n1,.2\n1,.3\n3,.4\n',
    'time_day,biomass_g_L\n0,.1\n1,.2\n2,fail\n3,.4\n',
    'time_day,biomass_g_L\n0,.1\n1,.2\n2,.3\n',
])
def test_invalid_files(text):
    with pytest.raises(ValueError):
        read_experiment_csv(text.encode())


def test_nonfinite_nitrogen_rejected():
    bad=pd.DataFrame({'time_day':[0,1,2,3], 'biomass_g_L':[.1,.2,.3,.4], 'nitrate_n_mg_L':[20,np.inf,10,5]})
    with pytest.raises(ValueError):
        validate_experiment(bad)


def test_custom_column_mapping():
    frame = read_experiment_csv(
        b"Day,dry_weight,nitrateN\n0,0.1,70\n1,0.2,55\n2,0.3,40\n3,0.4,22\n",
        column_map={"time_day": "Day", "biomass_g_L": "dry_weight", "nitrate_n_mg_L": "nitrateN"},
    )
    assert frame.iloc[-1]["biomass_g_L"] == 0.4


def test_invalid_mapping_duplicate_source_column():
    with pytest.raises(ValueError, match="different"):
        read_experiment_csv(
            b"Day,dry_weight\n0,0.1\n1,0.2\n2,0.3\n3,0.4\n",
            column_map={"time_day": "Day", "biomass_g_L": "Day"},
        )
