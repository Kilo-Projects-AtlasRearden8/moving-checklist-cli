"""Tests for date-math logic."""

from __future__ import annotations

from datetime import date

import pytest

from moving_checklist.dates import (
    MoveDateError,
    compute_due_date,
    days_between,
    days_until,
    is_past,
    parse_move_date,
    validate_move_date,
)


def test_parse_move_date_valid():
    assert parse_move_date("2026-11-15") == date(2026, 11, 15)


def test_parse_move_date_invalid():
    with pytest.raises(MoveDateError):
        parse_move_date("not-a-date")
    with pytest.raises(MoveDateError):
        parse_move_date("15-11-2026")


def test_compute_due_date_before():
    move = date(2026, 11, 15)
    assert compute_due_date(move, 14) == date(2026, 11, 1)


def test_compute_due_date_move_day():
    move = date(2026, 11, 15)
    assert compute_due_date(move, 0) == date(2026, 11, 15)


def test_compute_due_date_after():
    move = date(2026, 11, 15)
    assert compute_due_date(move, -3) == date(2026, 11, 18)


def test_days_between():
    assert days_between(date(2026, 11, 1), date(2026, 11, 15)) == 14
    assert days_between(date(2026, 11, 15), date(2026, 11, 1)) == -14


def test_days_until_relative():
    today = date(2026, 11, 1)
    move = date(2026, 11, 15)
    assert days_until(move, today) == 14


def test_is_past():
    assert is_past(date(2026, 11, 1), date(2026, 11, 2))
    assert not is_past(date(2026, 11, 15), date(2026, 11, 1))


def test_validate_move_date_rejects_past():
    today = date.today()
    yesterday = date(today.year, today.month, today.day) - __import__("datetime").timedelta(days=1)
    with pytest.raises(MoveDateError):
        validate_move_date(yesterday.isoformat())


def test_validate_move_date_allow_past():
    today = date.today()
    yesterday = date(today.year, today.month, today.day) - __import__("datetime").timedelta(days=1)
    result = validate_move_date(yesterday.isoformat(), allow_past=True)
    assert result == yesterday


def test_compute_due_date_crosses_month():
    move = date(2026, 3, 1)
    assert compute_due_date(move, 5) == date(2026, 2, 24)
