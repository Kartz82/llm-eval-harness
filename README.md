# LLM Eval / Regression Harness

A test harness for **LLM and agent quality**: run a dataset of cases against a
target, assert **grounding, citations, tool routing, authorization behavior,
latency SLOs and JSON-schema** conformance, then **gate CI** on pass-rate and
**detect regressions** against a baseline. Ships with **SQL data reconciliation**
and a **k6 perf gate** so one repo covers the AI-Tester surface.

Runs free on a Mac — the default `mock` target is offline and deterministic, so
tests and the CI gate need no LLM key.

## Why this exists

Validates AI systems the way an AI Tester / Quality Engineer does: declarative
checks, release gates, regression tracking, data reconciliation, and performance.

| JD capability | Where |
|---|---|
| Validate responses / grounding / citations | `evalkit/evaluators.py` (grounded, contains, absent) |
| Agent routing + tool-authorization checks | `expected_tool`, authorized-vs-denied refund cases (`datasets/support_agent.yaml`) |
| Regression suites + release gates in CI/CD | `evalkit/runner.py` gate + regressions, `.github/workflows/ci.yml` |
| API / integration testing | `HttpAgentTarget` runs the suite against a live agent API (`evalkit/targets.py`) |
| Data reconciliation (SQL) | `evalkit/reconcile.py` (in-memory SQLite diff) |
| Performance testing | `perf/k6_smoke.js` (p95 + error-rate SLO gate) |
| LLM-as-judge (faithfulness) | `evalkit/judge.py` (optional, Gemini) |
| Observability validation | optional Langfuse hook (`evalkit/config.py`) |

## Targets

- **mock** — deterministic offline agent; `good` and `broken` modes prove the harness catches failures. (default, CI)
- **http** — evaluates a live agent exposing `POST /chat` (e.g. the companion Support Agent).
- **gemini** — direct Gemini text target for pure-generation evals.

## Quickstart (offline, no key)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest                                  # unit + suite tests
python -m evalkit.run --dataset datasets/support_agent.yaml --target mock --report out/report.md
echo "exit code = $?"                   # 0 = gate passed
```

Evaluate a live agent instead:

```bash
python -m evalkit.run --dataset datasets/support_agent.yaml --target http \
  --report out/report.md --baseline out/baseline.json
```

## Release gate & regressions

`evalkit.run` exits non-zero when pass-rate is below `--threshold` **or** any case
that passed in the `--baseline` now fails — drop it into CI to block releases.

## Data reconciliation

```python
from evalkit.reconcile import reconcile
res = reconcile(source_rows, target_rows, key="id", compare_cols=["amount"])
assert res.clean  # no missing / extra / mismatched rows
```

## Performance gate

```bash
k6 run -e BASE_URL=http://localhost:8000 perf/k6_smoke.js
```

## Tech

Python · Pydantic · PyYAML · jsonschema · SQLite · httpx · k6 · Gemini (optional) · Langfuse (optional) · GitHub Actions
