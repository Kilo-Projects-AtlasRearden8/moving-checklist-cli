"""Command-line interface for the moving checklist tool."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import date

from .budget import check_overspend, format_alert, total_actual, total_estimated, total_variance
from .checklist import apply_plan_to_move_plan
from .dates import days_until, validate_move_date
from .export import export_all_csv
from .models import BudgetCategory, MovePlan
from .storage import Storage

PROG = "moving-checklist"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description=(
            "Generate room-by-room moving checklists and address-change timelines "
            "from a move date. Local-first: stores plans as JSON on your machine, "
            "with CSV export and overspending alerts."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_plan_args(p: argparse.ArgumentParser) -> None:
        p.add_argument("--move-date", required=True, help="Move date (YYYY-MM-DD)")
        p.add_argument("--from-address", default="", help="Current address")
        p.add_argument("--to-address", default="", help="New address")

    def add_plan_id(p: argparse.ArgumentParser) -> None:
        p.add_argument("--plan-id", default=None, help="Plan id (defaults to move date)")

    # init
    p_init = sub.add_parser("init", help="Create a new move plan")
    add_plan_args(p_init)
    p_init.set_defaults(func=_cmd_init)

    # generate
    p_gen = sub.add_parser("generate", help="Generate room-by-room checklist + timeline")
    add_plan_id(p_gen)
    p_gen.add_argument(
        "--rooms",
        default=None,
        help="Comma-separated subset of rooms (e.g. Kitchen,Bedroom)",
    )
    p_gen.set_defaults(func=_cmd_generate)

    # show
    p_show = sub.add_parser("show", help="Show a move plan summary")
    add_plan_id(p_show)
    p_show.set_defaults(func=_cmd_show)

    # timeline
    p_tl = sub.add_parser("timeline", help="Show the address-change timeline")
    add_plan_id(p_tl)
    p_tl.set_defaults(func=_cmd_timeline)

    # budget
    p_budget = sub.add_parser("budget", help="Budget tracking commands")
    budget_sub = p_budget.add_subparsers(dest="budget_command", required=True)
    p_budget_set = budget_sub.add_parser("set", help="Set a budget category estimate")
    add_plan_id(p_budget_set)
    p_budget_set.add_argument("--category", required=True, help="Category name")
    p_budget_set.add_argument("--estimated", type=float, required=True, help="Estimated amount")
    p_budget_set.set_defaults(func=_cmd_budget_set)
    p_budget_spend = budget_sub.add_parser("spend", help="Record actual spend for a category")
    add_plan_id(p_budget_spend)
    p_budget_spend.add_argument("--category", required=True, help="Category name")
    p_budget_spend.add_argument("--amount", type=float, required=True, help="Amount spent")
    p_budget_spend.set_defaults(func=_cmd_budget_spend)
    p_budget_show = budget_sub.add_parser("show", help="Show the budget")
    add_plan_id(p_budget_show)
    p_budget_show.set_defaults(func=_cmd_budget_show)

    # alerts
    p_alerts = sub.add_parser("alerts", help="Show due tasks and overspending alerts")
    add_plan_id(p_alerts)
    p_alerts.set_defaults(func=_cmd_alerts)

    # export
    p_export = sub.add_parser("export", help="Export plan to CSV files")
    add_plan_id(p_export)
    p_export.add_argument("--out", default="./export", help="Output directory for CSVs")
    p_export.set_defaults(func=_cmd_export)

    return parser


def _storage() -> Storage:
    return Storage()


def _plan_id(args: argparse.Namespace) -> str:
    return getattr(args, "plan_id", None) or args.move_date


def _load_or_init(args: argparse.Namespace) -> MovePlan:
    storage = _storage()
    plan_id = _plan_id(args)
    try:
        return storage.load(plan_id)
    except Exception:
        move_date = validate_move_date(args.move_date)
        return MovePlan(
            move_date=move_date.isoformat(),
            from_address=args.from_address,
            to_address=args.to_address,
            created_at=args.__dict__.get("created_at") or "",
        )


def _cmd_init(args: argparse.Namespace) -> int:
    validate_move_date(args.move_date)
    storage = _storage()
    plan_id = _plan_id(args)
    plan = MovePlan(
        move_date=args.move_date,
        from_address=args.from_address,
        to_address=args.to_address,
        created_at="",
    )
    storage.save(plan, plan_id)
    print(f"Initialized move plan '{plan_id}' (move date {args.move_date}).")
    print(f"Storage: {storage.storage_dir}")
    return 0


def _cmd_generate(args: argparse.Namespace) -> int:
    storage = _storage()
    plan_id = _plan_id(args)
    try:
        plan = storage.load(plan_id)
    except Exception:
        print(f"No plan found for '{plan_id}'. Run 'init' first.", file=sys.stderr)
        return 1
    rooms = None
    if args.rooms:
        rooms = [r.strip() for r in args.rooms.split(",") if r.strip()]
    move_date = date.fromisoformat(plan.move_date)
    apply_plan_to_move_plan(move_date, plan, rooms=rooms)
    storage.save(plan, plan_id)
    print(f"Generated {len(plan.tasks)} checklist tasks and {len(plan.timeline)} timeline items.")
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    storage = _storage()
    plan_id = _plan_id(args)
    try:
        plan = storage.load(plan_id)
    except Exception as exc:
        print(f"Error loading plan '{plan_id}': {exc}", file=sys.stderr)
        return 1
    move_date = date.fromisoformat(plan.move_date)
    remaining = days_until(move_date)
    print(f"Move plan: {plan_id}")
    print(f"  Move date: {plan.move_date} ({remaining} day(s) from now)")
    print(f"  From: {plan.from_address or '(not set)'}")
    print(f"  To: {plan.to_address or '(not set)'}")
    print(f"  Tasks: {len(plan.tasks)} | Timeline: {len(plan.timeline)} | Budget categories: {len(plan.budget)}")
    done = sum(1 for t in plan.tasks if t.status.value == "done")
    print(f"  Completed tasks: {done}/{len(plan.tasks)}")
    return 0


def _cmd_timeline(args: argparse.Namespace) -> int:
    storage = _storage()
    plan_id = _plan_id(args)
    try:
        plan = storage.load(plan_id)
    except Exception as exc:
        print(f"Error loading plan '{plan_id}': {exc}", file=sys.stderr)
        return 1
    if not plan.timeline:
        print("No timeline items yet. Run 'generate' first.")
        return 0
    print(f"Address-change timeline (move date {plan.move_date}):")
    print("-" * 70)
    for a in sorted(plan.timeline, key=lambda x: (x.days_before_move, x.title)):
        mark = "x" if a.status.value == "done" else " "
        print(f"  [{mark}] {a.due_date}  ({a.days_before_move:+d} days)  {a.title}")
        print(f"         {a.description}")
    return 0


def _cmd_budget_set(args: argparse.Namespace) -> int:
    storage = _storage()
    plan_id = _plan_id(args)
    try:
        plan = storage.load(plan_id)
    except Exception as exc:
        print(f"Error loading plan '{plan_id}': {exc}", file=sys.stderr)
        return 1
    for cat in plan.budget:
        if cat.name == args.category:
            cat.estimated = args.estimated
            break
    else:
        plan.budget.append(BudgetCategory(id=f"budget-{len(plan.budget)+1:03d}", name=args.category, estimated=args.estimated))
    storage.save(plan, plan_id)
    print(f"Set budget for '{args.category}': estimated ${args.estimated:.2f}")
    return 0


def _cmd_budget_spend(args: argparse.Namespace) -> int:
    storage = _storage()
    plan_id = _plan_id(args)
    try:
        plan = storage.load(plan_id)
    except Exception as exc:
        print(f"Error loading plan '{plan_id}': {exc}", file=sys.stderr)
        return 1
    for cat in plan.budget:
        if cat.name == args.category:
            cat.actual += args.amount
            break
    else:
        plan.budget.append(
            BudgetCategory(id=f"budget-{len(plan.budget)+1:03d}", name=args.category, estimated=0.0, actual=args.amount)
        )
    storage.save(plan, plan_id)
    print(f"Recorded ${args.amount:.2f} spent on '{args.category}'.")
    return 0


def _cmd_budget_show(args: argparse.Namespace) -> int:
    storage = _storage()
    plan_id = _plan_id(args)
    try:
        plan = storage.load(plan_id)
    except Exception as exc:
        print(f"Error loading plan '{plan_id}': {exc}", file=sys.stderr)
        return 1
    if not plan.budget:
        print("No budget categories yet. Use 'budget set' to add one.")
        return 0
    print(f"Budget (move date {plan.move_date}):")
    print("-" * 58)
    for b in plan.budget:
        flag = "  <-- OVER" if b.is_over else ""
        print(f"  {b.name}: estimated ${b.estimated:>9.2f}  actual ${b.actual:>9.2f}  variance ${b.variance:+.2f}{flag}")
    print("-" * 58)
    est = total_estimated(plan.budget)
    act = total_actual(plan.budget)
    var = total_variance(plan.budget)
    print(f"  TOTAL: estimated ${est:>9.2f}  actual ${act:>9.2f}  variance ${var:+.2f}")
    return 0


def _cmd_alerts(args: argparse.Namespace) -> int:
    storage = _storage()
    plan_id = _plan_id(args)
    try:
        plan = storage.load(plan_id)
    except Exception as exc:
        print(f"Error loading plan '{plan_id}': {exc}", file=sys.stderr)
        return 1
    today = date.today()
    move_date = date.fromisoformat(plan.move_date)

    due = [t for t in plan.tasks if t.is_due(today, move_date) and t.status.value != "done"]
    overdue = [t for t in plan.tasks if t.is_overdue(today, move_date) and t.status.value != "done"]
    alerts = check_overspend(plan.budget)

    print(f"Status for '{plan_id}' (move date {plan.move_date}):")
    if overdue:
        print(f"  OVERDUE tasks ({len(overdue)}):")
        for t in overdue:
            print(f"    - {t.due_date}  {t.room}: {t.title}")
    if due:
        print(f"  DUE tasks ({len(due)}):")
        for t in due:
            print(f"    - {t.due_date}  {t.room}: {t.title}")
    if not overdue and not due:
        print("  No tasks due or overdue today.")
    if alerts:
        print("  BUDGET ALERTS:")
        for a in alerts:
            print(f"    {format_alert(a)}")
    else:
        print("  No overspending alerts.")
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    storage = _storage()
    plan_id = _plan_id(args)
    try:
        plan = storage.load(plan_id)
    except Exception as exc:
        print(f"Error loading plan '{plan_id}': {exc}", file=sys.stderr)
        return 1
    files = export_all_csv(plan, args.out)
    for f in files:
        print(f"Wrote {f}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
