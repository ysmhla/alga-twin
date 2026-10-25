"""One report payload for escaped standalone HTML and paginated PDF exports."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime
from html import escape
from io import BytesIO
from pathlib import Path

import pandas as pd

from . import __version__
from .calibration import CrossValidationResult, JointFitResult


def plain_language(result: JointFitResult) -> list[str]:
    messages = [
        "The fitted curves describe these uploaded measurements. Independent biological validation is absent.",
        "Intervals are conditional on your fixed parameters, initial conditions and specified measurement noise.",
    ]
    if result.supported:
        messages.append(
            "The selected parameters passed the numerical profile gate within your search bounds."
        )
    else:
        messages.append(
            "Your data do not support all selected parameters. Unsupported point estimates and intervals are withheld; "
            "descriptive fitted curves are not reliable forecasts."
        )
    if {"mu_max_day", "extinction_a0"} <= result.estimates.keys() and not result.supported:
        messages.append(
            "Your data may not separate maximum growth rate from light absorption. "
            "Measure extinction directly or collect runs at different light levels."
        )
    for name, estimate in result.estimates.items():
        if estimate.status != "IDENTIFIABLE":
            messages.append(f"{name}: {estimate.status}. {estimate.reason}")
    if all(run["origin"] == "SYNTHETIC" for run in result.provenance):
        messages.append("SYNTHETIC teaching data: numerical behavior only, not laboratory evidence.")
    return messages


def report_payload(
    result: JointFitResult,
    *,
    title: str,
    input_sha256: str,
    cv: CrossValidationResult | None = None,
    proxy_calibration: dict | None = None,
) -> dict:
    if len(input_sha256) != 64 or any(c not in "0123456789abcdef" for c in input_sha256):
        raise ValueError("Supply the SHA256 of the original uploaded/worked-example CSV")
    if not title.strip() or len(title) > 200:
        raise ValueError("Report title must contain 1-200 characters")
    # Never recover suppressed estimates from an optimizer or reconstruct a vector.
    rows = []
    for name, estimate in result.estimates.items():
        record = asdict(estimate)
        if estimate.status != "IDENTIFIABLE" or not result.optimizer_success:
            record["value"], record["interval"] = None, None
        rows.append({"parameter": name, **record})
    payload = {
        "title": title.strip(),
        "software": f"AlgaTwin {__version__}",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "input_sha256": input_sha256,
        "supported": result.supported,
        "messages": plain_language(result),
        "parameters": rows,
        "confidence": result.confidence,
        "interval_method": result.report()["interval_method"],
        "error_model": asdict(result.error_model),
        "search_bounds_not_literature_ranges": {name: asdict(p) for name, p in result.search.items()},
        "metrics_in_sample": result.metrics.to_dict("records"),
        "fit_points_in_sample": result.predictions.to_dict("records"),
        "profiles": result.profiles.to_dict("records"),
        "runs": list(result.provenance),
        "proxy_calibration": proxy_calibration,
        "cross_validation": None,
    }
    if cv is not None:
        expected = {run["run_id"] for run in result.provenance}
        if set(cv.folds.held_out) != expected or len(cv.folds) != len(expected):
            raise ValueError("Cross-validation folds do not match this fit")
        scored = set(cv.folds.loc[cv.folds.status.eq("SCORED"), "held_out"])
        if scored:
            columns = ["run_id", "time_day", "observable", "replicate", "value", "unit", "origin"]
            if not set(columns) <= set(cv.predictions.columns) or set(cv.predictions.run_id) != scored:
                raise ValueError("Cross-validation predictions do not match scored folds")
            wanted = result.predictions[result.predictions.run_id.isin(scored)][columns]
            actual = cv.predictions[columns]
            keys = ["run_id", "time_day", "observable", "replicate"]
            if (
                not wanted.sort_values(keys)
                .reset_index(drop=True)
                .equals(actual.sort_values(keys).reset_index(drop=True))
            ):
                raise ValueError("Cross-validation observations differ from this fit")
        elif not cv.metrics.empty or not cv.predictions.empty:
            raise ValueError("Unscored folds cannot carry scored metrics/predictions")
        # The UI additionally keys fit and CV by the complete input/config hash.
        payload["cross_validation"] = {
            "method": cv.method,
            "folds": cv.folds.to_dict("records"),
            "metrics": cv.metrics.to_dict("records"),
            "all_folds_scored": bool(cv.folds.status.eq("SCORED").all()),
            "scope": "Whole-run held-out errors; no independent biological validation claim",
        }
    else:
        payload["messages"].append(
            "Held-out error was not computed. In-sample error is not predictive accuracy."
        )
    if proxy_calibration:
        if {run["origin"] for run in result.provenance} != {proxy_calibration["origin"]}:
            raise ValueError("Proxy conversion and growth observations must have the same origin")
        payload["messages"].append(
            "Proxy-to-dry-weight conversion uncertainty is not propagated into growth-fit intervals."
        )
    # Avoid invalid JSON and silently serialized NaN in any export.
    json.dumps(payload, allow_nan=False)
    return payload


def _table(rows: list[dict], columns: list[str]) -> str:
    if not rows:
        return "<p>Not computed.</p>"
    return pd.DataFrame(rows).reindex(columns=columns).to_html(index=False, escape=True, na_rep="withheld")


def _short(value):
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, (tuple, list)):
        return "(" + ", ".join(_short(v) for v in value) + ")"
    return str(value)


def _svg_fit(rows: list[dict]) -> str:
    """Small dependency-free scatter/line panels, one per run/observable, with units."""
    import numpy as np

    frame = pd.DataFrame(rows)
    panels = []
    for (run, obs), group in frame.groupby(["run_id", "observable"], sort=False):
        x, y, p = group.time_day.to_numpy(), group.value.to_numpy(), group.predicted.to_numpy()
        xmin, xmax = min(0, x.min()), x.max()
        ymin, ymax = min(0, y.min(), p.min()), max(y.max(), p.max())
        sx = lambda t, lo=xmin, hi=xmax: 55 + 560 * (t - lo) / max(hi - lo, 1e-12)
        sy = lambda v, lo=ymin, hi=ymax: 190 - 145 * (v - lo) / max(hi - lo, 1e-12)
        unique = group.groupby("time_day", sort=True).predicted.mean()
        line = " ".join(f"{sx(t):.3f},{sy(v):.3f}" for t, v in unique.items())
        points = "".join(
            f'<circle cx="{sx(t):.3f}" cy="{sy(v):.3f}" r="3" fill="#1d4c5e"/>'
            for t, v in zip(x, y, strict=True)
        )
        label = escape(f"{run}: {obs} ({group.unit.iloc[0]}) - in-sample")
        ticks = "".join(
            f'<text x="5" y="{sy(v):.2f}" font-size="11">{v:.3g}</text>' for v in np.linspace(ymin, ymax, 4)
        )
        panels.append(
            f'<svg viewBox="0 0 660 235" role="img" aria-label="{label}">'
            f'<text x="55" y="22" font-size="14">{label}</text>'
            '<path d="M55 40 V190 H620" fill="none" stroke="#999"/>'
            f'<polyline points="{line}" fill="none" stroke="#168575" stroke-width="2"/>{points}{ticks}'
            f'<text x="55" y="210">{xmin:g}</text><text x="580" y="210">{xmax:g}</text>'
            '<text x="250" y="230">Time (day); line: model, dots: data</text></svg>'
        )
    return "".join(panels)


def report_html(payload: dict) -> str:
    title = escape(payload["title"])
    sections = [
        f"<h1>{title}</h1><p>{escape(payload['software'])} | {escape(payload['created_at_utc'])}</p>",
        "<h2>What this result means</h2><ul>"
        + "".join(f"<li>{escape(m)}</li>" for m in payload["messages"])
        + "</ul>",
        "<h2>Parameter evidence</h2>"
        + _table(
            payload["parameters"], ["parameter", "value", "interval", "unit", "status", "reason", "method"]
        ),
        f"<p>Confidence: {payload['confidence']:g}. Method: {escape(payload['interval_method'])}</p>",
        "<h2>In-sample fit</h2>" + _svg_fit(payload["fit_points_in_sample"]),
        _table(
            payload["metrics_in_sample"],
            ["run_id", "observable", "split", "origin", "n", "unit", "rmse", "mae"],
        ),
    ]
    cv = payload["cross_validation"]
    sections.append("<h2>Held-out evaluation</h2>")
    if cv:
        sections.extend(
            [
                f"<p>{escape(cv['method'])}. All folds scored: {cv['all_folds_scored']}.</p>",
                _table(cv["folds"], ["held_out", "status", "reason"]),
                _table(
                    cv["metrics"],
                    ["run_id", "observable", "held_out_fold", "split", "origin", "n", "unit", "rmse", "mae"],
                ),
            ]
        )
    else:
        sections.append("<p>Not computed.</p>")
    for run in payload["runs"]:
        sections.append(f"<h2>Run {escape(run['run_id'])}: provenance before fitting</h2>")
        sections.append(
            _table(
                run["parameters_before_fitting"],
                [
                    "parameter",
                    "value",
                    "low",
                    "high",
                    "unit",
                    "basis",
                    "source",
                    "status",
                    "species",
                    "conditions",
                    "tier",
                ],
            )
        )
    evidence = json.dumps(payload, indent=2, allow_nan=False)
    sections.append("<h2>Reproducibility and full numerical evidence</h2><pre>" + escape(evidence) + "</pre>")
    return (
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>'
        + title
        + "</title><style>body{font:15px system-ui;color:#18323c;max-width:1100px;margin:40px auto;padding:0 24px}h1,h2{color:#126758}table{border-collapse:collapse;width:100%;font-size:12px;display:block;overflow:auto}th,td{border:1px solid #ccd6d6;padding:7px;text-align:left;overflow-wrap:anywhere}svg{width:100%;max-width:660px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:10px}@media print{table{display:table;font-size:8px}body{margin:0}svg{max-width:500px}}</style><body>"
        + "".join(sections)
        + "</body></html>"
    )


def report_pdf(payload: dict) -> bytes:
    """Portable PDF with wrapped tables, fit plots and complete parameter provenance."""
    import reportlab
    from reportlab.graphics.shapes import Circle, Drawing, Line, PolyLine, String
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    stream = BytesIO()
    font_dir = Path(reportlab.__file__).parent / "fonts"
    if "AlgaSans" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("AlgaSans", str(font_dir / "Vera.ttf")))
        pdfmetrics.registerFont(TTFont("AlgaSansBold", str(font_dir / "VeraBd.ttf")))
        pdfmetrics.registerFontFamily(
            "AlgaSans", normal="AlgaSans", bold="AlgaSansBold", italic="AlgaSans", boldItalic="AlgaSansBold"
        )
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = "AlgaSansBold" if "Heading" in style.name or style.name == "Title" else "AlgaSans"
    styles.add(
        ParagraphStyle(
            name="SmallEvidence",
            fontName="AlgaSans",
            fontSize=8,
            leading=11,
            spaceAfter=5,
            splitLongWords=True,
        )
    )

    def para(text, style="SmallEvidence"):
        # Built-in Helvetica covers these scientific-text substitutions; no missing glyphs.
        text = (
            _short(text)
            .replace("²", "^2")
            .replace("Δ", "Delta")
            .replace("µ", "micro")
            .replace("−", "-")
            .replace("–", "-")
            .replace("—", "-")
        )
        text = text.encode("ascii", "backslashreplace").decode("ascii")
        return Paragraph(escape(text).replace("\n", "<br/>"), styles[style])

    story = [
        para(payload["title"], "Title"),
        para(f"{payload['software']} | {payload['created_at_utc']}"),
        para("What this result means", "Heading2"),
    ]
    story.extend(para(message, "BodyText") for message in payload["messages"])

    def table(rows, columns, widths):
        if not rows:
            story.append(para("Not computed."))
            return
        cells = [[para(c) for c in columns]]
        cells.extend([[para("withheld" if row.get(c) is None else row[c]) for c in columns] for row in rows])
        obj = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
        obj.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5f1ee")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#c5d4d2")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.extend([obj, Spacer(1, 10)])

    story.append(para("Parameter evidence", "Heading2"))
    table(
        payload["parameters"], ["parameter", "value", "interval", "unit", "status"], [120, 65, 100, 75, 145]
    )
    story.append(para(f"Confidence: {payload['confidence']}. Method: {payload['interval_method']}"))
    for row in payload["parameters"]:
        story.append(para(f"{row['parameter']}: {row['reason']}"))
    story.append(para("In-sample fit", "Heading2"))
    frame = pd.DataFrame(payload["fit_points_in_sample"])
    for (run, obs), data in frame.groupby(["run_id", "observable"], sort=False):
        drawing = Drawing(505, 190)
        drawing.add(
            String(
                45, 174, f"{run}: {obs} ({data.unit.iloc[0]}) - in-sample", fontName="AlgaSans", fontSize=10
            )
        )
        xmin, xmax = min(0, data.time_day.min()), data.time_day.max()
        ymin, ymax = (
            min(0, data.value.min(), data.predicted.min()),
            max(data.value.max(), data.predicted.max()),
        )

        def point(t, y, xmin=xmin, xmax=xmax, ymin=ymin, ymax=ymax):
            return (
                45 + 440 * (t - xmin) / max(xmax - xmin, 1e-12),
                35 + 120 * (y - ymin) / max(ymax - ymin, 1e-12),
            )

        drawing.add(Line(45, 35, 485, 35, strokeColor=colors.grey))
        drawing.add(Line(45, 35, 45, 155, strokeColor=colors.grey))
        ordered = data.groupby("time_day", sort=True).predicted.mean()
        drawing.add(
            PolyLine(
                [c for t, y in ordered.items() for c in point(t, y)],
                strokeColor=colors.HexColor("#168575"),
                strokeWidth=1.5,
            )
        )
        for row in data.itertuples():
            drawing.add(
                Circle(
                    *point(row.time_day, row.value),
                    2.5,
                    fillColor=colors.HexColor("#1d4c5e"),
                    strokeColor=None,
                )
            )
        for t in (xmin, xmax):
            drawing.add(String(point(t, ymin)[0] - 4, 20, f"{t:.3g}", fontName="AlgaSans", fontSize=8))
        for y in (ymin, ymax):
            drawing.add(String(2, point(xmin, y)[1], f"{y:.3g}", fontName="AlgaSans", fontSize=8))
        drawing.add(String(130, 3, "Time (day); line: model; dots: data", fontName="AlgaSans", fontSize=9))
        story.append(drawing)
    table(
        payload["metrics_in_sample"],
        ["run_id", "observable", "split", "unit", "rmse", "mae"],
        [95, 55, 70, 85, 100, 100],
    )
    story.append(para("Held-out evaluation", "Heading2"))
    cv = payload["cross_validation"]
    if cv:
        story.append(para(f"{cv['method']}. All folds scored: {cv['all_folds_scored']}."))
        table(cv["folds"], ["held_out", "status", "reason"], [100, 100, 305])
        table(
            cv["metrics"],
            ["held_out_fold", "run_id", "observable", "split", "unit", "rmse", "mae"],
            [80, 80, 45, 55, 65, 90, 90],
        )
    else:
        story.append(para("Not computed. In-sample error is not held-out accuracy."))
    story.append(para("Assumptions and reproducibility", "Heading2"))
    story.append(para(f"Original input SHA256: {payload['input_sha256']}"))
    story.append(para(f"Error model: {payload['error_model']}"))
    story.append(
        para(f"Search bounds (not literature ranges): {payload['search_bounds_not_literature_ranges']}")
    )
    if payload["proxy_calibration"]:
        story.append(para(f"Proxy calibration: {json.dumps(payload['proxy_calibration'])}"))
    for run in payload["runs"]:
        story.append(para(f"Run {run['run_id']}: {run['origin']}", "Heading2"))
        story.append(para(json.dumps({k: v for k, v in run.items() if k != "parameters_before_fitting"})))
        for record in run["parameters_before_fitting"]:
            table(
                [record],
                ["parameter", "value", "unit", "basis", "status", "tier"],
                [120, 55, 95, 100, 75, 60],
            )
            story.append(
                para(
                    "; ".join(
                        f"{key}: {record.get(key)}"
                        for key in ("species", "conditions", "source", "evidence", "locator", "low", "high")
                    )
                )
            )

    def footer(canvas, doc):
        canvas.setFont("AlgaSans", 8)
        canvas.drawString(45, 24, "AlgaTwin - research prototype; no independent biological validation")
        canvas.drawRightString(A4[0] - 45, 24, f"Page {doc.page}")

    SimpleDocTemplate(
        stream,
        pagesize=A4,
        leftMargin=45,
        rightMargin=45,
        topMargin=40,
        bottomMargin=42,
        title=payload["title"],
        author="AlgaTwin",
    ).build(story, onFirstPage=footer, onLaterPages=footer)
    return stream.getvalue()


def report_digest(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()
