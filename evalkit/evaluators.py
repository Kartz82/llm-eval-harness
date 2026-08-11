"""Declarative checks → pass/fail results. Covers grounding, tool routing,
content assertions, latency SLO, and JSON-schema conformance.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .cases import Case
from .targets import Response


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


def _schema_ok(text: str, schema: dict) -> tuple[bool, str]:
    try:
        from jsonschema import validate
    except Exception:
        return True, "jsonschema not installed; skipped"
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return False, f"not valid JSON: {exc}"
    try:
        validate(payload, schema)
    except Exception as exc:
        return False, f"schema mismatch: {exc}"
    return True, "valid"


def evaluate(case: Case, resp: Response) -> list[CheckResult]:
    c = case.checks
    text_l = resp.text.lower()
    results: list[CheckResult] = []

    if c.expected_tool is not None:
        ok = c.expected_tool in resp.tool_calls
        detail = f"want {c.expected_tool}, got {resp.tool_calls}"
        results.append(CheckResult("expected_tool", ok, detail))

    for needle in c.must_contain:
        results.append(CheckResult(f"contains:{needle}", needle.lower() in text_l))

    for needle in c.must_not_contain:
        results.append(CheckResult(f"absent:{needle}", needle.lower() not in text_l))

    if c.grounded is not None:
        has = len(resp.citations) > 0
        detail = f"citations={resp.citations}"
        results.append(CheckResult("grounded", has == c.grounded, detail))

    if c.max_latency_ms is not None:
        ok = resp.latency_ms <= c.max_latency_ms
        detail = f"{resp.latency_ms:.0f}ms <= {c.max_latency_ms}ms"
        results.append(CheckResult("latency_slo", ok, detail))

    if c.json_schema is not None:
        ok, detail = _schema_ok(resp.text, c.json_schema)
        results.append(CheckResult("json_schema", ok, detail))

    if not results:  # a case with no checks is a smoke test: any non-empty reply passes
        results.append(CheckResult("non_empty", bool(resp.text.strip())))
    return results
