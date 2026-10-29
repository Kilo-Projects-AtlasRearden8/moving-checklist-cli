# Moving Checklist CLI

A local-first Python CLI that generates room-by-room moving checklists and
address-change timelines from a single move date. It also tracks your moving
budget and alerts you to overspending.

Built by **Asdale Dynamics, LLC** — beginner-friendly, plain-English tools for
life admin, small business, and accessible productivity. No API keys, no
network calls, no secrets. Your data stays on your machine as plain JSON files.

## Who this is for

Anyone facing a move who wants a clear, step-by-step plan: what to pack room by
room, when to change your address, and how to keep moving costs from creeping
up. Written in a warm, never-condescending tone, with ADHD-friendly small steps
and low-energy productivity in mind.

## Install

```bash
# From this folder
pip install -e .

# Or run directly
python -m moving_checklist.cli --help
```

The CLI entry point is `moving-checklist` once installed.

## Quick start

1. Initialize a plan with your move date:

   ```bash
   moving-checklist init --move-date 2026-12-01 \
     --from-address "123 Old St, Indianapolis, IN" \
     --to-address "456 New Ave, Indianapolis, IN"
   ```

2. Generate the room-by-room checklist and address-change timeline:

   ```bash
   moving-checklist generate --plan-id 2026-12-01
   ```

3. See what's due or overdue, plus any budget overspending alerts:

   ```bash
   moving-checklist alerts --plan-id 2026-12-01
   ```

4. Export everything to CSV:

   ```bash
   moving-checklist export --plan-id 2026-12-01 --out ./moving-export
   ```

## Commands

| Command | What it does |
|---------|--------------|
| `init` | Create a new move plan anchored to a move date |
| `generate` | Build room-by-room tasks + address-change timeline |
| `show` | Summarize a plan (dates, task counts, progress) |
| `timeline` | List address-change deadlines before/after the move |
| `budget set` | Set an estimated amount for a budget category |
| `budget spend` | Record actual spend for a category |
| `budget show` | Show estimated vs. actual spending with variances |
| `alerts` | Show due/overdue tasks and overspending alerts |
| `export` | Write checklist, timeline, and budget to CSV files |

## Storage

Plans are saved as JSON files under `~/.moving-checklist` by default. Nothing
is sent anywhere — this tool is local-first and makes no network requests.

## Budget & overspending alerts

Use `budget set` to estimate what each moving category will cost (truck rental,
packing supplies, deposits, etc.), then `budget spend` as you spend. The `alerts`
command flags any category where actual spend exceeds the estimate, so you can
catch overspending early.

## Testing

```bash
pip install pytest
pytest
```

Tests cover date math (due dates, past/full move dates) and checklist logic
(room tasks, timeline items, room subsets).

## License

MIT License

Copyright (c) 2026 Asdale Dynamics, LLC

See the [LICENSE](LICENSE) file for details.

## About

Asdale Dynamics, LLC (Indiana, formed October 2026) is founded by Dylan Asdale,
a registered nurse turned AI author and founder. The LLC publishes beginner-friendly
AI education, books and guides, and practical open-source tools — like this one —
that anyone can use, modify, or sell. Learn more at dylanasdale.github.io.
