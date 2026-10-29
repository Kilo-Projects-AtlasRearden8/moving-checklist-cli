"""Tests for checklist generation logic."""

from __future__ import annotations

from datetime import date

from moving_checklist.checklist import generate_checklist
from moving_checklist.models import Priority, TaskStatus


def test_generate_checklist_creates_tasks():
    move = date(2026, 11, 15)
    plan = generate_checklist(move)
    assert len(plan.tasks) > 0
    assert len(plan.timeline) > 0


def test_tasks_have_due_dates_before_move():
    move = date(2026, 11, 15)
    plan = generate_checklist(move)
    for t in plan.tasks:
        assert t.due_date is not None
        due = date.fromisoformat(t.due_date)
        assert due <= move or due == date.fromisoformat(t.due_date)


def test_urgent_move_day_tasks_present():
    move = date(2026, 11, 15)
    plan = generate_checklist(move)
    move_day = [t for t in plan.tasks if t.days_before_move == 0]
    assert any("final walkthrough" in t.title.lower() for t in move_day)


def test_timeline_includes_usps():
    move = date(2026, 11, 15)
    plan = generate_checklist(move)
    usps = [t for t in plan.timeline if "USPS" in t.title]
    assert len(usps) == 1
    assert usps[0].days_before_move == 14


def test_subset_rooms_limits_tasks():
    move = date(2026, 11, 15)
    full = generate_checklist(move)
    kitchen = generate_checklist(move, rooms=["Kitchen"])
    assert len(kitchen.tasks) < len(full.tasks)
    assert all(t.room == "Kitchen" for t in kitchen.tasks)


def test_all_tasks_pending_by_default():
    move = date(2026, 11, 15)
    plan = generate_checklist(move)
    assert all(t.status == TaskStatus.PENDING for t in plan.tasks)
    assert all(t.status == TaskStatus.PENDING for t in plan.timeline)


def test_priorities_valid():
    move = date(2026, 11, 15)
    plan = generate_checklist(move)
    for t in plan.tasks:
        assert t.priority in (Priority.URGENT, Priority.HIGH, Priority.MEDIUM, Priority.LOW)
