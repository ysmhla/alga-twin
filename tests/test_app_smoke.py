"""Run dashboard top-level code with a very small Streamlit stand-in.

This checks default scientific-demo rendering paths even in an offline test
runtime where the Streamlit package itself is not installed. It does NOT
replace a live browser test; Streamlit widgets are mocked.
"""

from __future__ import annotations

import runpy
import sys
import types
from io import BytesIO
from pathlib import Path

import pytest


class FakeState(dict):
    def __getattr__(self, key):
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value


class Widget:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def __getattr__(self, _key):
        return lambda *_a, **_kw: None


@pytest.mark.parametrize("with_upload", [False, True])
def test_dashboard_default_demo_path(monkeypatch, with_upload):
    fake = types.ModuleType("streamlit")
    fake.session_state = FakeState()
    fake.sidebar = Widget()
    figures = []

    def number_input(_name, _min, _max, value, *_args, **_kw):
        return 1000.0 if with_upload and "Measured incident light" in _name else value

    def slider(_name, _min, _max, value, *_args, **_kw):
        assert _min <= value <= _max, f"Streamlit default out of range for {_name}: {value}"
        return value

    fake.set_page_config = lambda **_kwargs: None
    fake.markdown = lambda *_args, **_kwargs: None
    fake.caption = lambda *_args, **_kwargs: None
    fake.info = lambda *_args, **_kwargs: None
    fake.success = lambda *_args, **_kwargs: None
    fake.warning = lambda *_args, **_kwargs: None
    fake.error = lambda *_args, **_kwargs: None
    fake.latex = lambda *_args, **_kwargs: None
    fake.code = lambda *_args, **_kwargs: None
    fake.dataframe = lambda *_args, **_kwargs: None
    fake.download_button = lambda *_args, **_kwargs: None
    fake.metric = lambda *_args, **_kwargs: None
    fake.plotly_chart = lambda figure, **_kwargs: figures.append(figure)
    fake.columns = lambda items, **_kwargs: [
        Widget() for _ in range(items if isinstance(items, int) else len(items))
    ]
    fake.tabs = lambda items, **_kwargs: [Widget() for _ in items]
    fake.expander = lambda *_args, **_kwargs: Widget()
    fake.spinner = lambda *_args, **_kwargs: Widget()

    def upload(*_args, **_kwargs):
        if not with_upload:
            return None
        obj = BytesIO(b"time_day,biomass_g_L,nitrate_n_mg_L\n0,.1,70\n1,.2,60\n2,.3,50\n3,.4,40\n")
        obj.name = "test.csv"
        return obj

    fake.file_uploader = upload
    fake.radio = lambda _label, options, **_kw: options[1]
    fake.selectbox = lambda _label, options, index=0, **_kw: (
        "Baseline workflow" if _label == "Workspace" else options[index]
    )
    fake.number_input = number_input
    fake.slider = slider
    fake.text_input = lambda *_args, **kwargs: kwargs.get("value", "")
    fake.button = lambda *_args, **_kwargs: False
    fake.rerun = lambda: None
    monkeypatch.setitem(sys.modules, "streamlit", fake)
    root = Path(__file__).resolve().parents[1]
    runpy.run_path(str(root / "app.py"), run_name="__main__")
    assert len(figures) >= 5
