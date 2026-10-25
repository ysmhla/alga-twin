"""Exports preserve profile gates, methods, provenance and split labels."""

import hashlib
import json
from dataclasses import asdict, replace
from io import BytesIO

import pandas as pd
import pytest

from alga_twin.calibration import (
    CrossValidationResult,
    JointFitResult,
    ParameterEstimate,
)
from alga_twin.calibration_io import load_job, synthetic_job
from alga_twin.fit_report import report_html, report_payload, report_pdf


@pytest.fixture
def result():
    config, data = synthetic_job()
    runs, search, errors = load_job(config, data)
    predictions = data.copy()
    predictions["predicted"] = predictions.value
    predictions["origin"], predictions["split"] = "SYNTHETIC", "in-sample"
    # Fixture exercises presentation, not an inference/coverage claim.
    provenance = tuple(
        {
            "run_id": r.run_id,
            "origin": r.origin,
            "kind": r.model.kind,
            "light": r.model.light,
            "conditions": asdict(r.model.conditions),
            "parameters_before_fitting": [{"parameter": n, **asdict(p)} for n, p in r.model.params.items()],
        }
        for r in runs
    )
    metrics = pd.DataFrame(
        [
            {
                "run_id": r.run_id,
                "observable": "X",
                "split": "in-sample",
                "origin": "SYNTHETIC",
                "n": 8,
                "unit": "g_DW/liter",
                "rmse": 0.0,
                "mae": 0.0,
            }
            for r in runs
        ]
    )
    return JointFitResult(
        {
            "mu_max_day": ParameterEstimate(
                0.9, (0.8, 1.0), "1/day", "IDENTIFIABLE", "SYNTHETIC report fixture"
            )
        },
        pd.DataFrame({"parameter": ["mu_max_day"], "value": [0.9], "delta_deviance": [0.0]}),
        predictions,
        metrics,
        True,
        0.0,
        0.95,
        3.84,
        search,
        errors,
        provenance,
        0.001,
    )


def payload(result, **kwargs):
    return report_payload(
        result,
        title="SYNTHETIC <script>alert('test')</script>",
        input_sha256=hashlib.sha256(b"SYNTHETIC fixture").hexdigest(),
        **kwargs,
    )


def test_html_is_standalone_escaped_and_preserves_interval_method_and_origins(result):
    evidence = payload(result)
    html = report_html(evidence)
    assert "<script>" not in html and "&lt;script&gt;" in html
    assert "<svg" in html and "<circle" in html
    assert "Not computed." in html and "In-sample error is not predictive accuracy" in html
    for text in [
        "Reoptimized profile likelihood",
        "asymptotic",
        "SYNTHETIC",
        "UNVERIFIED",
        "source",
        "basis",
        "input_sha256",
    ]:
        assert text in html
    assert evidence["parameters"][0]["interval"] == (0.8, 1.0)
    assert evidence["metrics_in_sample"][0]["split"] == "in-sample"
    json.dumps(evidence, allow_nan=False)


def test_report_suppresses_unsupported_estimate_even_if_caller_supplies_one(result):
    unsupported = replace(
        result,
        estimates={
            "mu_max_day": ParameterEstimate(
                12345.6789, (123, 456), "1/day", "NOT IDENTIFIABLE", "Flat synthetic profile"
            )
        },
    )
    evidence = payload(unsupported)
    assert not evidence["supported"]
    assert evidence["parameters"][0]["value"] is None
    assert evidence["parameters"][0]["interval"] is None
    assert "12345.6789" not in report_html(evidence)
    assert "not reliable forecasts" in " ".join(evidence["messages"])


def test_report_records_failed_folds_without_pooled_success_claim(result):
    cv = CrossValidationResult(
        pd.DataFrame(
            [
                {"held_out": r["run_id"], "status": "NOT IDENTIFIABLE", "reason": "SYNTHETIC failure fixture"}
                for r in result.provenance
            ]
        ),
        pd.DataFrame(),
        pd.DataFrame(),
    )
    evidence = payload(result, cv=cv)
    assert not evidence["cross_validation"]["all_folds_scored"]
    assert evidence["cross_validation"]["metrics"] == []
    assert "NOT IDENTIFIABLE" in report_html(evidence)
    with pytest.raises(ValueError, match="folds"):
        payload(result, cv=replace(cv, folds=cv.folds.iloc[:1]))
    with pytest.raises(ValueError, match="SHA256"):
        report_payload(result, title="test", input_sha256="bad")


def test_pdf_has_fit_method_flags_provenance_and_page_numbers(result):
    pytest.importorskip("reportlab")
    pypdf = pytest.importorskip("pypdf")
    pdf = report_pdf(payload(result))
    assert pdf.startswith(b"%PDF-")
    reader = pypdf.PdfReader(BytesIO(pdf))
    assert len(reader.pages) >= 3
    text = " ".join(page.extract_text() for page in reader.pages)
    for term in [
        "SYNTHETIC",
        "UNVERIFIED",
        "IDENTIFIABLE",
        "Reoptimized profile likelihood",
        "dry_weight",
        "input",
        "Page 1",
        "In-sample fit",
        "Held-out evaluation",
    ]:
        assert term.lower() in text.lower()
    assert "independent biological validation" in text
