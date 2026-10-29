"""Room-by-room moving checklist generation.

Generates checklist tasks and address-change timeline items anchored to the
move date. All dates are computed relative to the move date so the user can
plan ahead step by step.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .dates import compute_due_date
from .models import AddressChange, MovePlan, Priority, Task, TaskStatus

# Room templates: room -> list of (title, days_before_move, priority, description)
ROOM_TEMPLATES: dict[str, list[tuple[str, int, str, str]]] = {
    "Kitchen": [
        ("Pack non-essential dishes & glassware", 21, "medium", "Wrap breakables in packing paper; label boxes fragile."),
        ("Pack small appliances rarely used", 14, "medium", "Toaster, blender, coffee maker not needed daily."),
        ("Clean oven & microwave", 7, "medium", "Leave appliances move-in ready for the next resident."),
        ("Defrost & clean refrigerator", 1, "high", "Defrost at least 24 hours before move; wipe clean."),
        ("Pack pantry foods", 7, "medium", "Donate unopened non-perishables; toss expired items."),
        ("Pack daily dishes & cookware", 1, "high", "Keep one plate/bowl/cup per person until move day."),
        ("Clean cabinets & countertops", 2, "medium", "Wipe down all surfaces before vacating."),
    ],
    "Bathroom": [
        ("Pack extra toiletries & cleaning supplies", 14, "medium", "Keep daily-use items until move day."),
        ("Scrub shower, tub & tiles", 5, "medium", "Leave the bathroom clean for the next resident."),
        ("Clean sink & mirror", 2, "medium", "Final wipe-down before moving out."),
        ("Pack daily toiletries", 1, "high", "Toothbrush, medication, razor in a first-night box."),
        ("Empty trash & disinfect toilet", 1, "medium", "Final cleaning pass on move day."),
    ],
    "Bedroom": [
        ("Pack out-of-season clothing", 21, "medium", "Box winter/summer clothes not needed now."),
        ("Pack shoes & accessories", 14, "medium", "Wrap pairs together; label clearly."),
        ("Pack books & decor", 14, "medium", "Wrap breakables; label boxes by room."),
        ("Pack most clothing", 7, "medium", "Keep a week of outfits out until move day."),
        ("Pack remaining clothes & linens", 1, "high", "Last outfits and bedding go in day-of bags."),
        ("Strip beds & wash linens", 1, "medium", "Make beds fresh or pack bedding for the new place."),
    ],
    "Living Room": [
        ("Pack decor, picture frames & knickknacks", 14, "medium", "Wrap frames individually; label fragile."),
        ("Pack books, games & media", 14, "medium", "Box books in small boxes (they get heavy)."),
        ("Disassemble shelving & side tables", 7, "medium", "Keep screws & hardware in labeled bags."),
        ("Pack electronics & remotes", 3, "high", "Photo cable setups before unplugging."),
        ("Vacuum carpets & dust surfaces", 2, "medium", "Final clean before handing over keys."),
    ],
    "Home Office": [
        ("Back up computer files", 21, "high", "External drive or cloud backup before packing anything."),
        ("Pack reference files & paperwork", 14, "medium", "Sort keep/shred/scan; shred sensitive documents."),
        ("Pack desk supplies & stationery", 7, "medium", "Keep pens/notepad for move-day notes."),
        ("Disassemble desk & chair", 2, "medium", "Keep hardware bags taped to the furniture."),
        ("Pack computer & peripherals", 1, "high", "Original boxes preferred; label cables."),
    ],
    "Closet": [
        ("Pack seasonal items", 21, "medium", "Coats, boots, holiday decor not needed now."),
        ("Pack extra linens & blankets", 14, "medium", "Vacuum-seal bags save space."),
        ("Sort donate vs. keep", 14, "medium", "Drop off donations before move day."),
        ("Pack remaining clothes", 3, "high", "Keep a suitcase of clothes for the first week."),
    ],
    "Garage": [
        ("Pack tools & hardware", 14, "medium", "Toolbox first; label power tools & cords."),
        ("Drain fuel from lawn equipment", 3, "high", "Mowers & trimmers can't move with gas/oil."),
        ("Pack garden supplies", 7, "medium", "Pots, soil, tools in sturdy boxes."),
        ("Clean garage floor & sweep", 1, "medium", "Leave it tidy for the next resident."),
    ],
    "General / Whole Home": [
        ("Confirm moving truck or movers", 14, "high", "Reserve date/time; get confirmation in writing."),
        ("Gather packing supplies", 21, "medium", "Boxes, tape, markers, bubble wrap, labels."),
        ("Label every box by room & contents", 3, "medium", "Color-coded stickers speed up unloading."),
        ("Pack a first-night / essentials box", 1, "high", "Toiletries, meds, chargers, snacks, change of clothes."),
        ("Do a final walkthrough", 0, "urgent", "Check all rooms, closets, cabinets; turn off lights & lock up."),
    ],
}

# Address-change timeline items anchored to the move date.
TIMELINE_ITEMS: list[tuple[str, int, str, str]] = [
    ("Notify landlord / give notice (if renting)", 30, "high", "Check your lease for required notice period."),
    ("Reserve moving truck or hire movers", 21, "high", "Get a written quote and confirm the move date."),
    ("File USPS change of address", 14, "urgent", "Start mail forwarding online or at the post office."),
    ("Notify banks & credit card companies", 14, "high", "Update billing address for all accounts."),
    ("Transfer or cancel utilities", 14, "high", "Schedule shutoff at old home and setup at new home."),
    ("Update auto & home/renters insurance", 14, "medium", "Confirm coverage at the new address."),
    ("Notify employer & payroll", 14, "medium", "Update address for W-2s and direct deposit."),
    ("Update subscriptions & streaming services", 10, "medium", "Magazines, meal kits, streaming, cloud storage."),
    ("Notify doctors, dentists & pharmacy", 10, "medium", "Transfer prescriptions if moving far."),
    ("Update voter registration", 7, "medium", "Register at your new address."),
    ("Update driver's license / vehicle registration", 7, "medium", "Most states require updates within 30 days of moving."),
    ("Notify schools & daycare", 14, "medium", "Transfer records if changing districts."),
    ("Confirm mail forwarding started", -1, "medium", "Check that mail is arriving at the new address."),
    ("Cancel or transfer internet & cable", -3, "medium", "Schedule installation at the new home."),
]


@dataclass
class GeneratedPlan:
    """Result of generating a checklist + timeline from a move date."""

    tasks: list[Task]
    timeline: list[AddressChange]


def generate_checklist(
    move_date: date,
    rooms: list[str] | None = None,
) -> GeneratedPlan:
    """Generate room-by-room tasks and an address-change timeline.

    Parameters
    ----------
    move_date:
        The planned move date.
    rooms:
        Optional subset of room names to include. When omitted, all template
        rooms are included.
    """
    if rooms is None:
        rooms = list(ROOM_TEMPLATES.keys())

    tasks: list[Task] = []
    counter = 0
    for room in rooms:
        for title, days, priority, description in ROOM_TEMPLATES.get(room, []):
            counter += 1
            tasks.append(
                Task(
                    id=f"task-{counter:03d}",
                    room=room,
                    title=title,
                    description=description,
                    days_before_move=days,
                    priority=Priority(priority),
                    status=TaskStatus.PENDING,
                    due_date=compute_due_date(move_date, days).isoformat(),
                )
            )

    timeline: list[AddressChange] = []
    counter = 0
    for title, days, priority, description in TIMELINE_ITEMS:
        counter += 1
        timeline.append(
            AddressChange(
                id=f"tl-{counter:03d}",
                title=title,
                description=description,
                days_before_move=days,
                priority=Priority(priority),
                status=TaskStatus.PENDING,
                due_date=compute_due_date(move_date, days).isoformat(),
            )
        )

    return GeneratedPlan(tasks=tasks, timeline=timeline)


def apply_plan_to_move_plan(
    move_date: date,
    move_plan: MovePlan,
    rooms: list[str] | None = None,
) -> MovePlan:
    """Generate tasks/timeline and attach them to an existing :class:`MovePlan`."""
    generated = generate_checklist(move_date, rooms=rooms)
    move_plan.tasks = generated.tasks
    move_plan.timeline = generated.timeline
    return move_plan
