"""SQL-based data reconciliation.

Loads two row sets (e.g. a source system vs the pipeline's output) into an in-memory
SQLite database and uses SQL to find rows that are missing, extra, or mismatched —
the kind of data-quality gate an AI/data QA engineer owns.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field


@dataclass
class ReconResult:
    missing_in_target: list[dict] = field(default_factory=list)  # in source, not target
    extra_in_target: list[dict] = field(default_factory=list)  # in target, not source
    mismatched: list[dict] = field(default_factory=list)  # same key, differing values

    @property
    def clean(self) -> bool:
        return not (self.missing_in_target or self.extra_in_target or self.mismatched)


def _load(conn: sqlite3.Connection, table: str, rows: list[dict], cols: list[str]) -> None:
    col_defs = ", ".join(f'"{c}"' for c in cols)
    conn.execute(f'CREATE TABLE {table} ({col_defs})')
    placeholders = ", ".join("?" for _ in cols)
    conn.executemany(
        f'INSERT INTO {table} VALUES ({placeholders})',
        [tuple(r.get(c) for c in cols) for r in rows],
    )


def reconcile(
    source: list[dict],
    target: list[dict],
    key: str,
    compare_cols: list[str] | None = None,
) -> ReconResult:
    cols = list({k for r in source + target for k in r} | {key})
    compare_cols = compare_cols or [c for c in cols if c != key]

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _load(conn, "src", source, cols)
    _load(conn, "tgt", target, cols)

    missing = [
        dict(r)
        for r in conn.execute(
            f'SELECT s.* FROM src s LEFT JOIN tgt t ON s."{key}"=t."{key}" '
            f'WHERE t."{key}" IS NULL'
        )
    ]
    extra = [
        dict(r)
        for r in conn.execute(
            f'SELECT t.* FROM tgt t LEFT JOIN src s ON t."{key}"=s."{key}" '
            f'WHERE s."{key}" IS NULL'
        )
    ]
    mism_clause = " OR ".join(f's."{c}" IS NOT t."{c}"' for c in compare_cols)
    mismatched = [
        dict(r)
        for r in conn.execute(
            f'SELECT s."{key}" AS "{key}" FROM src s JOIN tgt t ON s."{key}"=t."{key}" '
            f'WHERE {mism_clause}'
        )
    ] if compare_cols else []

    conn.close()
    return ReconResult(missing_in_target=missing, extra_in_target=extra, mismatched=mismatched)
