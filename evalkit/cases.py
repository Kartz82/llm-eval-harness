"""Eval case model + YAML loader.

A dataset is a list of cases; each case pairs an input with a set of declarative
``checks`` the target's response must satisfy.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Checks:
    expected_tool: str | None = None
    must_contain: list[str] = field(default_factory=list)
    must_not_contain: list[str] = field(default_factory=list)
    grounded: bool | None = None  # response must carry >=1 citation
    max_latency_ms: int | None = None
    json_schema: dict | None = None


@dataclass
class Case:
    id: str
    input: str
    checks: Checks
    scopes: list[str] = field(default_factory=list)  # authorization context
    description: str = ""


def _to_case(raw: dict) -> Case:
    checks = Checks(**(raw.get("checks") or {}))
    return Case(
        id=raw["id"],
        input=raw["input"],
        checks=checks,
        scopes=list(raw.get("scopes", [])),
        description=raw.get("description", ""),
    )


def load_cases(path: str | Path) -> list[Case]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Dataset {path} must be a YAML list of cases.")
    return [_to_case(item) for item in data]
