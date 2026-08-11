"""Suite + evaluator + gate/regression tests (fully offline via MockTarget)."""
from evalkit.cases import Case, Checks, load_cases
from evalkit.evaluators import evaluate
from evalkit.report import to_dict, to_markdown
from evalkit.runner import gate, regressions, run_suite
from evalkit.targets import MockTarget, Response


def test_good_mock_passes_the_gate(dataset):
    report = run_suite(MockTarget("good"), load_cases(dataset))
    assert report.pass_rate == 1.0
    assert gate(report, 1.0) is True


def test_broken_mock_fails_and_is_flagged_as_regression(dataset):
    cases = load_cases(dataset)
    good = run_suite(MockTarget("good"), cases)
    broken = run_suite(MockTarget("broken"), cases)
    assert gate(broken, 1.0) is False
    # Everything the good build passed is now a regression.
    assert set(regressions(broken, good.passed_ids)) == good.passed_ids


def test_expected_tool_and_grounding_checks():
    case = Case(
        id="t", input="q",
        checks=Checks(expected_tool="search_kb", grounded=True, must_contain=["ok"]),
    )
    good = Response(text="ok", tool_calls=["search_kb"], citations=["a.md"])
    bad = Response(text="nope", tool_calls=[], citations=[])
    assert all(c.passed for c in evaluate(case, good))
    names = {c.name: c.passed for c in evaluate(case, bad)}
    assert names["expected_tool"] is False
    assert names["grounded"] is False


def test_json_schema_and_latency_checks():
    schema = {"type": "object", "required": ["ok"], "properties": {"ok": {"type": "boolean"}}}
    case = Case(id="j", input="q", checks=Checks(json_schema=schema, max_latency_ms=10))
    ok = evaluate(case, Response(text='{"ok": true}', latency_ms=5))
    bad = evaluate(case, Response(text="{bad json", latency_ms=999))
    assert all(c.passed for c in ok)
    failed = {c.name for c in bad if not c.passed}
    assert "json_schema" in failed and "latency_slo" in failed


def test_report_shapes(dataset):
    report = run_suite(MockTarget("good"), load_cases(dataset))
    assert "Pass rate" in to_markdown(report)
    d = to_dict(report)
    assert d["passed"] == d["total"] and len(d["cases"]) == report.total
