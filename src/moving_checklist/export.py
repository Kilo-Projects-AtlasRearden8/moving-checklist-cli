"""CSV export for checklists and budgets."""

from __future__ import annotations

import csv
from pathlib import Path

from .models import MovePlan


def export_checklist_csv(move_plan: MovePlan, path: str | Path) -> Path:
    """Write checklist tasks to a CSV file at ``path``. Returns the path."""
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            ["id", "room", "title", "description", "days_before_move", "priority", "status", "due_date"]
        )
        for t in move_plan.tasks:
            writer.writerow(
                [t.id, t.room, t.title, t.description, t.days_before_move, t.priority.value, t.status.value, t.due_date or ""]
            )
    return path


def export_timeline_csv(move_plan: MovePlan, path: str | Path) -> Path:
    """Write address-change timeline to a CSV file at ``path``. Returns the path."""
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "title", "description", "days_before_move", "priority", "status", "due_date"])
        for a in move_plan.timeline:
            writer.writerow(
                [a.id, a.title, a.description, a.days_before_move, a.priority.value, a.status.value, a.due_date or ""]
            )
    return path


def export_budget_csv(move_plan: MovePlan, path: str | Path) -> Path:
    """Write budget categories to a CSV file at ``path``. Returns the path."""
    path = Path(path)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "name", "estimated", "actual", "variance", "is_over", "note"])
        for b in move_plan.budget:
            writer.writerow(
                [b.id, b.name, b.estimated, b.actual, b.variance, b.is_over, b.note]
            )
    return path


def export_all_csv(move_plan: MovePlan, directory: str | Path) -> list[Path]:
    """Export checklist, timeline, and budget CSVs into ``directory``."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in move_plan.move_date)
    return [
        export_checklist_csv(move_plan, directory / f"{safe}_checklist.csv"),
        export_timeline_csv(move_plan, directory / f"{safe}_timeline.csv"),
        export_budget_csv(move_plan, directory / f"{safe}_budget.csv"),
    ]
