# STATUS

## What was built

A local-first Python CLI (`moving-checklist`) that generates room-by-room moving
checklists and address-change timelines from a single move date. It also tracks
moving expenses and alerts to overspending.

Components:
- `src/moving_checklist/models.py` — data models (Task, AddressChange, BudgetCategory, MovePlan, Priority, TaskStatus)
- `src/moving_checklist/dates.py` — date math anchored to the move date (due dates, days until, past/future validation)
- `src/moving_checklist/checklist.py` — room-by-room checklist templates (Kitchen, Bathroom, Bedroom, Living Room, Home Office, Closet, Garage, General) plus address-change timeline items (USPS change of address, banks, utilities, insurance, employer, etc.)
- `src/moving_checklist/storage.py` — local JSON storage under `~/.moving-checklist` (no network, no keys)
- `src/moving_checklist/export.py` — CSV export for checklist, timeline, and budget
- `src/moving_checklist/budget.py` — estimated vs. actual spend with overspending alerts and tolerance support
- `src/moving_checklist/cli.py` — argparse CLI: init, generate, show, timeline, budget set/spend/show, alerts, export
- `tests/test_dates.py`, `tests/test_checklist.py`, `tests/test_budget.py` — 23 tests covering date math and checklist/budget logic
- `pyproject.toml` — packaging with `moving-checklist` console script, pytest/ruff config
- `LICENSE` — MIT, copyright exactly "Copyright (c) 2026 Asdale Dynamics, LLC"
- `README.md` — credits Asdale Dynamics, LLC; beginner-friendly usage guide
- `.gitignore` — standard Python ignores

Credits Asdale Dynamics, LLC throughout (LICENSE copyright line and README).

## How to run

Install:
```bash
pip install -e .
```
(or run directly with `PYTHONPATH=src python3 -m moving_checklist.cli`)

Example workflow:
```bash
moving-checklist init --move-date 2026-12-01 \
  --from-address "123 Old St" --to-address "456 New Ave"
moving-checklist generate --plan-id 2026-12-01
moving-checklist show --plan-id 2026-12-01
moving-checklist timeline --plan-id 2026-12-01
moving-checklist budget set --plan-id 2026-12-01 --category Truck --estimated 200
moving-checklist budget spend --plan-id 2026-12-01 --category Truck --amount 250
moving-checklist alerts --plan-id 2026-12-01
moving-checklist export --plan-id 2026-12-01 --out ./moving-export
```

Tests:
```bash
PYTHONPATH=src python3 -m pytest tests/
```

Lint:
```bash
ruff check src/ tests/
```

## Verification results

- Tests: 23 passed (date math + checklist/budget logic)
- Ruff lint: all checks passed
- Build: wheel builds successfully (`moving_checklist_cli-0.1.0-py3-none-any.whl`)
- CLI: verified end-to-end — init, generate, show, timeline, budget set/spend/show, alerts, export all run correctly
- Overspending alert fires when actual exceeds estimated (with tolerance support)
- CSV export writes checklist, timeline, and budget files
- Local JSON storage under `~/.moving-checklist`, no network calls, no API keys, no secrets

Git: initialized and committed as `0aa42f2` on branch `master`, identity Dylan Asdale <dylanasdale@users.noreply.github.com>. No remote, no push, no co-author trailers.

## Known gaps

- No `mypy`/`pyright` typecheck configured or run (mypy not installed in environment); type annotations are present throughout.
- Tests use `PYTHONPATH=src` rather than an installed package in CI (no CI workflows present, per requirements).
- Timeline/room template data is hardcoded; no per-plan customization of individual task due dates beyond generation.
- Budget categories persist in the plan JSON; no separate budget file.
- No GUI, no web interface, no notifications/reminders beyond the `alerts` command.
- Move date validation rejects past dates by default (use `--move-date` with a future date).
