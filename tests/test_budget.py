"""Tests for budget tracking and overspending alerts."""

from __future__ import annotations

from moving_checklist.budget import (
    check_overspend,
    format_alert,
    total_actual,
    total_estimated,
    total_variance,
)
from moving_checklist.models import BudgetCategory


def _cat(name, estimated, actual):
    return BudgetCategory(id="x", name=name, estimated=estimated, actual=actual)


def test_no_alert_when_under_budget():
    cats = [_cat("Truck", 200.0, 150.0)]
    assert check_overspend(cats) == []


def test_alert_when_over_budget():
    cats = [_cat("Truck", 200.0, 250.0)]
    alerts = check_overspend(cats)
    assert len(alerts) == 1
    assert alerts[0].category == "Truck"
    assert alerts[0].variance == 50.0


def test_tolerance_allows_small_overage():
    cats = [_cat("Truck", 200.0, 208.0)]  # 4% over
    assert check_overspend(cats, tolerance=0.05) == []


def test_totals():
    cats = [_cat("A", 100.0, 120.0), _cat("B", 200.0, 150.0)]
    assert total_estimated(cats) == 300.0
    assert total_actual(cats) == 270.0
    assert total_variance(cats) == -30.0


def test_format_alert():
    a = check_overspend([_cat("Boxes", 50.0, 80.0)])[0]
    msg = format_alert(a)
    assert "OVERSPEND ALERT" in msg
    assert "Boxes" in msg
