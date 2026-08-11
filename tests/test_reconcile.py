"""SQL data-reconciliation tests."""
from evalkit.reconcile import reconcile


def test_detects_missing_extra_and_mismatched():
    source = [
        {"id": "1", "amount": 10},
        {"id": "2", "amount": 20},
        {"id": "3", "amount": 30},
    ]
    target = [
        {"id": "1", "amount": 10},   # match
        {"id": "2", "amount": 99},   # mismatched amount
        {"id": "4", "amount": 40},   # extra (and 3 missing)
    ]
    res = reconcile(source, target, key="id", compare_cols=["amount"])
    assert [r["id"] for r in res.missing_in_target] == ["3"]
    assert [r["id"] for r in res.extra_in_target] == ["4"]
    assert [r["id"] for r in res.mismatched] == ["2"]
    assert res.clean is False


def test_clean_when_identical():
    rows = [{"id": "1", "v": "a"}, {"id": "2", "v": "b"}]
    res = reconcile(rows, list(rows), key="id")
    assert res.clean is True
