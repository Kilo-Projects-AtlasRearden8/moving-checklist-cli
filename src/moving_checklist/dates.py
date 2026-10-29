"""Date-math and timeline computation for the moving checklist.

All date arithmetic is anchored to the move date. ``days_before_move`` is the
number of days *before* the move date a task should happen, so:

    due_date = move_date - timedelta(days=days_before_move)

Negative values mean after the move date.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


class MoveDateError(ValueError):
    """Raised when a move date is invalid or in the past."""


def parse_move_date(value: str) -> date:
    """Parse an ISO-8601 date string into a :class:`date`."""
    try:
        return date.fromisoformat(value.strip())
    except ValueError as exc:  # pragma: no cover - exercised via CLI
        raise MoveDateError(f"Invalid move date {value!r}; expected YYYY-MM-DD.") from exc


def compute_due_date(move_date: date, days_before_move: int) -> date:
    """Return the calendar date a task with ``days_before_move`` is due."""
    return move_date - timedelta(days=days_before_move)


def days_between(a: date, b: date) -> int:
    """Whole days from ``a`` to ``b`` (b - a)."""
    return (b - a).days


def days_until(move_date: date, today: date | None = None) -> int:
    """Whole days remaining until the move date."""
    if today is None:
        today = date.today()
    return days_between(today, move_date)


def is_past(move_date: date, today: date | None = None) -> bool:
    if today is None:
        today = date.today()
    return today > move_date


def validate_move_date(value: str, *, allow_past: bool = False) -> date:
    """Parse and validate a move date, optionally rejecting past dates."""
    move_date = parse_move_date(value)
    if not allow_past and is_past(move_date):
        raise MoveDateError(f"Move date {value} is in the past.")
    return move_date


@dataclass(frozen=True)
class TimelineEntry:
    """A computed timeline row for display."""

    label: str
    days_before_move: int
    due_date: date
    priority: str

    @property
    def relative_label(self) -> str:
        """Human-friendly relative description of the due date."""
        if self.days_before_move == 0:
            return "Move day"
        if self.days_before_move > 0:
            return f"{self.days_before_move} day(s) before move"
        return f"{-self.days_before_move} day(s) after move"


def build_timeline_rows(
    move_date: date,
    items: list[tuple[str, int, str]],
) -> list[TimelineEntry]:
    """Build sorted timeline rows from ``(title, days_before_move, priority)``."""
    rows = [
        TimelineEntry(
            label=title,
            days_before_move=days,
            due_date=compute_due_date(move_date, days),
            priority=priority,
        )
        for title, days, priority in items
    ]
    rows.sort(key=lambda r: (r.days_before_move, r.label))
    return rows
