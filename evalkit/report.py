"""Render a RunReport to JSON (for baselines) and Markdown (for humans/CI)."""
from __future__ import annotations

import json
from pathlib import Path

from .runner import RunReport


def to_dict(report: RunReport) -> dict:
    return {
        "total": report.total,
        "passed": report.passed,
        "failed": report.failed,
        "pass_rate": round(report.pass_rate, 4),
        "cases": [
            {
                "id": o.case_id,
                "passed": o.passed,
                "checks": [
                    {"name": c.name, "passed": c.passed, "detail": c.detail} for c in o.checks
                ],
                "reply": o.response.text,
                "tool_calls": o.response.tool_calls,
                "citations": o.response.citations,
                "latency_ms": round(o.response.latency_ms, 1),
            }
            for o in report.outcomes
        ],
    }


def to_markdown(report: RunReport) -> str:
    lines = [
        "# LLM Eval Report",
        "",
        f"**Pass rate:** {report.passed}/{report.total} "
        f"({report.pass_rate * 100:.1f}%)",
        "",
        "| Case | Result | Failed checks | Latency |",
        "|------|--------|---------------|---------|",
    ]
    for o in report.outcomes:
        badge = "✅" if o.passed else "❌"
        failed = ", ".join(c.name for c in o.checks if not c.passed) or "—"
        lines.append(
            f"| {o.case_id} | {badge} | {failed} | {o.response.latency_ms:.0f}ms |"
        )
    return "\n".join(lines) + "\n"


def write_report(report: RunReport, path: str | Path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.suffix == ".json":
        p.write_text(json.dumps(to_dict(report), indent=2), encoding="utf-8")
    else:
        p.write_text(to_markdown(report), encoding="utf-8")
    return p
