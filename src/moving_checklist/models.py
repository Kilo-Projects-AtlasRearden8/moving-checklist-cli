"""Data models for the moving checklist CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum


class Priority(str, Enum):
    """How soon a task needs attention relative to the move date."""

    URGENT = "urgent"  # day-of or critical deadline
    HIGH = "high"  # within a few days
    MEDIUM = "medium"  # within a week or two
    LOW = "low"  # can wait, or post-move housekeeping

    def __lt__(self, other: Priority) -> bool:  # pragma: no cover - trivial
        order = {Priority.LOW: 0, Priority.MEDIUM: 1, Priority.HIGH: 2, Priority.URGENT: 3}
        return order[self] < order[other]


class TaskStatus(str, Enum):
    PENDING = "pending"
    DONE = "done"
    SKIPPED = "skipped"


@dataclass
class Task:
    """A single checklist item tied to the move date."""

    id: str
    room: str
    title: str
    description: str = ""
    days_before_move: int = 0  # 0 = move day; negative = after move
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    due_date: str | None = None  # ISO date string, computed at plan time

    def is_due(self, today: date | None = None, move_date: date | None = None) -> bool:
        if not self.due_date:
            return False
        if today is None:
            today = date.today()
        return today >= date.fromisoformat(self.due_date)

    def is_overdue(self, today: date | None = None, move_date: date | None = None) -> bool:
        if not self.due_date:
            return False
        if today is None:
            today = date.today()
        return today > date.fromisoformat(self.due_date)


@dataclass
class AddressChange:
    """An address-change deadline in the timeline."""

    id: str
    title: str
    description: str
    days_before_move: int
    priority: Priority = Priority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    due_date: str | None = None


@dataclass
class BudgetCategory:
    """A budget line item with estimated and actual costs."""

    id: str
    name: str
    estimated: float = 0.0
    actual: float = 0.0
    note: str = ""

    @property
    def variance(self) -> float:
        return self.actual - self.estimated

    @property
    def is_over(self) -> bool:
        return self.actual > self.estimated


@dataclass
class MovePlan:
    """The full move plan: checklist, timeline, and budget."""

    move_date: str  # ISO date
    from_address: str = ""
    to_address: str = ""
    tasks: list[Task] = field(default_factory=list)
    timeline: list[AddressChange] = field(default_factory=list)
    budget: list[BudgetCategory] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "move_date": self.move_date,
            "from_address": self.from_address,
            "to_address": self.to_address,
            "tasks": [
                {
                    "id": t.id,
                    "room": t.room,
                    "title": t.title,
                    "description": t.description,
                    "days_before_move": t.days_before_move,
                    "priority": t.priority.value,
                    "status": t.status.value,
                    "due_date": t.due_date,
                }
                for t in self.tasks
            ],
            "timeline": [
                {
                    "id": a.id,
                    "title": a.title,
                    "description": a.description,
                    "days_before_move": a.days_before_move,
                    "priority": a.priority.value,
                    "status": a.status.value,
                    "due_date": a.due_date,
                }
                for a in self.timeline
            ],
            "budget": [
                {
                    "id": b.id,
                    "name": b.name,
                    "estimated": b.estimated,
                    "actual": b.actual,
                    "note": b.note,
                }
                for b in self.budget
            ],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> MovePlan:
        return cls(
            move_date=data.get("move_date", ""),
            from_address=data.get("from_address", ""),
            to_address=data.get("to_address", ""),
            tasks=[
                Task(
                    id=t["id"],
                    room=t["room"],
                    title=t["title"],
                    description=t.get("description", ""),
                    days_before_move=t.get("days_before_move", 0),
                    priority=Priority(t.get("priority", "medium")),
                    status=TaskStatus(t.get("status", "pending")),
                    due_date=t.get("due_date"),
                )
                for t in data.get("tasks", [])
            ],
            timeline=[
                AddressChange(
                    id=a["id"],
                    title=a["title"],
                    description=a.get("description", ""),
                    days_before_move=a.get("days_before_move", 0),
                    priority=Priority(a.get("priority", "medium")),
                    status=TaskStatus(a.get("status", "pending")),
                    due_date=a.get("due_date"),
                )
                for a in data.get("timeline", [])
            ],
            budget=[
                BudgetCategory(
                    id=b["id"],
                    name=b["name"],
                    estimated=float(b.get("estimated", 0)),
                    actual=float(b.get("actual", 0)),
                    note=b.get("note", ""),
                )
                for b in data.get("budget", [])
            ],
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


def iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")
