import pytest
from ppt_engine.ledger import LedgerEntry, DataLedger, compare_slide_values


def entry(value=120):
    return LedgerEntry(id="revenue", value=value, unit="亿元", definition="年度营业收入",
                       source="annual report p.10", time="2025")


def test_register_and_resolve():
    ledger = DataLedger()
    ledger.register(entry())
    assert ledger.resolve("revenue").value == 120


def test_conflicting_registration_rejected():
    ledger = DataLedger()
    ledger.register(entry())
    with pytest.raises(ValueError):
        ledger.register(entry(121))


def test_cross_slide_inconsistency():
    issues = compare_slide_values({"s1": {"revenue": 120}, "s2": {"revenue": 121}})
    assert len(issues) == 1
