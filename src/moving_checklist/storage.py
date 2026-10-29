"""Local-first JSON storage for move plans.

No network calls, no API keys. Plans live as plain JSON files on disk, defaulting
to a ``~/.moving-checklist`` directory (configurable via the ``storage_dir``
argument).
"""

from __future__ import annotations

import json
from pathlib import Path

from .models import MovePlan, iso_now

DEFAULT_STORAGE_DIR = Path.home() / ".moving-checklist"


class StorageError(IOError):
    """Raised when reading or writing a plan file fails."""


class Storage:
    """Read/write move plans as local JSON files."""

    def __init__(self, storage_dir: str | Path | None = None) -> None:
        self.storage_dir = Path(storage_dir or DEFAULT_STORAGE_DIR)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, plan_id: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in plan_id)
        return self.storage_dir / f"{safe}.json"

    def list_plans(self) -> list[Path]:
        return sorted(self.storage_dir.glob("*.json"))

    def save(self, move_plan: MovePlan, plan_id: str | None = None) -> str:
        """Persist a plan and return the plan id used as the filename stem."""
        plan_id = plan_id or move_plan.move_date
        move_plan.updated_at = iso_now()
        path = self._path_for(plan_id)
        try:
            path.write_text(json.dumps(move_plan.to_dict(), indent=2) + "\n", encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"Failed to save plan to {path}: {exc}") from exc
        return plan_id

    def load(self, plan_id: str) -> MovePlan:
        path = self._path_for(plan_id)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise StorageError(f"No plan found for id {plan_id!r} at {path}") from exc
        except (json.JSONDecodeError, OSError) as exc:
            raise StorageError(f"Failed to read plan {plan_id!r}: {exc}") from exc
        return MovePlan.from_dict(data)

    def delete(self, plan_id: str) -> None:
        path = self._path_for(plan_id)
        try:
            path.unlink()
        except FileNotFoundError as exc:
            raise StorageError(f"No plan found for id {plan_id!r}") from exc
