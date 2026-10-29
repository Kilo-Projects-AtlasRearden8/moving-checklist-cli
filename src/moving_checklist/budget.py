"""Budget tracking and overspending alerts.

Categories track estimated vs. actual spend. An overspending alert fires when a
category's actual exceeds its estimate (optionally beyond a tolerance threshold).
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import BudgetCategory


@dataclass(frozen=True)
class OverspendAlert:
    category: str
    estimated: float
    actual: float
    variance: float


def check_overspend(
    categories: list[BudgetCategory],
    *,
    tolerance: float = 0.0,
) -> list[OverspendAlert]:
    """Return categories whose actual spend exceeds estimated spend.

    ``tolerance`` allows a small buffer (e.g. 0.05 means 5% over is OK).
    """
    alerts: list[OverspendAlert] = []
    for cat in categories:
        threshold = cat.estimated * (1.0 + tolerance)
        if cat.actual > threshold:
            alerts.append(
                OverspendAlert(
                    category=cat.name,
                    estimated=cat.estimated,
                    actual=cat.actual,
                    variance=cat.variance,
                )
            )
    return alerts


def format_alert(alert: OverspendAlert) -> str:
    return (
        f"OVERSPEND ALERT: {alert.category} — "
        f"actual ${alert.actual:.2f} exceeds estimated ${alert.estimated:.2f} "
        f"(over by ${alert.variance:.2f})."
    )


def total_estimated(categories: list[BudgetCategory]) -> float:
    return sum(c.estimated for c in categories)


def total_actual(categories: list[BudgetCategory]) -> float:
    return sum(c.actual for c in categories)


def total_variance(categories: list[BudgetCategory]) -> float:
    return total_actual(categories) - total_estimated(categories)
