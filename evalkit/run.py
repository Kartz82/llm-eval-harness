"""CLI: run an eval suite, write a report, and gate CI on pass-rate + regressions.

    python -m evalkit.run --dataset datasets/support_agent.yaml --target mock \
        --report out/report.md --baseline out/baseline.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .cases import load_cases
from .config import settings
from .report import to_markdown, write_report
from .runner import gate, regressions, run_suite
from .targets import build_target


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="evalkit")
    p.add_argument("--dataset", required=True)
    p.add_argument("--target", default=None, help="mock | http | gemini")
    p.add_argument("--report", default=None, help="output path (.md or .json)")
    p.add_argument("--threshold", type=float, default=settings.pass_threshold)
    p.add_argument("--baseline", default=None, help="JSON report to detect regressions against")
    args = p.parse_args(argv)

    cases = load_cases(args.dataset)
    target = build_target(args.target)
    report = run_suite(target, cases)

    print(to_markdown(report))
    if args.report:
        print(f"report written: {write_report(report, args.report)}")

    regs: list[str] = []
    if args.baseline and Path(args.baseline).exists():
        baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
        baseline_ids = {c["id"] for c in baseline["cases"] if c["passed"]}
        regs = regressions(report, baseline_ids)
        if regs:
            print(f"REGRESSIONS vs baseline: {regs}")

    ok = gate(report, args.threshold) and not regs
    print(
        f"GATE: {'PASS' if ok else 'FAIL'} "
        f"(pass_rate={report.pass_rate:.2%}, threshold={args.threshold:.2%})"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
