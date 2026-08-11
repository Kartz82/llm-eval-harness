"""Run a dataset against a target, score it, gate on pass-rate, detect regressions."""
from __future__ import annotations

from dataclasses import dataclass, field

from .cases import Case
from .evaluators import CheckResult, evaluate
from .targets import Response, Target


@dataclass
class CaseOutcome:
    case_id: str
    passed: bool
    checks: list[CheckResult]
    response: Response


@dataclass
class RunReport:
    outcomes: list[CaseOutcome] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.outcomes)

    @property
    def passed(self) -> int:
        return sum(o.passed for o in self.outcomes)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0

    @property
    def passed_ids(self) -> set[str]:
        return {o.case_id for o in self.outcomes if o.passed}


def run_suite(target: Target, cases: list[Case]) -> RunReport:
    report = RunReport()
    for case in cases:
        resp = target.run(case)
        checks = evaluate(case, resp)
        report.outcomes.append(
            CaseOutcome(case.id, all(c.passed for c in checks), checks, resp)
        )
    return report


def gate(report: RunReport, threshold: float) -> bool:
    """True if the run meets the release bar."""
    return report.pass_rate >= threshold


def regressions(report: RunReport, baseline_passed_ids: set[str]) -> list[str]:
    """Cases that passed in the baseline but fail now."""
    return sorted(baseline_passed_ids - report.passed_ids)
