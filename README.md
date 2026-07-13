# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info 
- Let a user view tasks (duration + priority) 
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning) 
<!-- - Include tests for the most important scheduling behaviors -->

## ✨ Features

The scheduling logic lives in `pawpal_system.py`. These are the algorithms it implements:

- **Priority sorting** (`Scheduler.sort_tasks`) — orders tasks by a three-level key: *required first*, then by priority number (1 = high), then by shortest duration as a tiebreaker. This is the order the planner uses to decide what gets placed first.
- **Sorting by time** (`Scheduler.sort_by_time`) — arranges tasks in clock order by their `preferred_time` ("HH:MM"). Zero-padded time strings sort correctly as plain strings; tasks with no fixed time fall back to `"99:99"` so they land at the end.
- **Weighted prioritization** (`Task.urgency_score`, `Scheduler.prioritize_by_urgency`, `Scheduler.urgency_report`) — a scoring model that folds *required status*, *priority*, *how many days a task is overdue*, and *brevity* into a single urgency number, then ranks tasks by it. Unlike `sort_tasks`'s fixed key order, blending the factors lets an overdue low-priority task overtake a fresh high-priority one — and it's the only sorter that considers `due_date`. `urgency_report()` renders the ranking (with scores and "overdue Nd" tags) as text.
- **Time-budgeted daily plan with gap-filling** (`Scheduler.generate_daily_plan`) — anchors fixed-time tasks at their requested slot (earliest first), then slots flexible tasks into the earliest free gaps by importance. It respects the owner's minute budget, always places *required* tasks even if that goes over budget, skips completed and future-dated tasks, and returns the plan in chronological order.
- **Conflict warnings** (`Scheduler.detect_conflicts`, `Scheduler.conflict_warning`) — treats each timed task as a half-open window `[start, start + duration)` and flags any overlap, whether same pet or different pets. Tasks that merely touch (one ends as the next starts) don't conflict, and malformed times are skipped rather than crashing. `conflict_warning()` returns a ready-to-display string (empty when there are no conflicts).
- **Daily / weekly recurrence** (`Task.mark_complete`, `Task.next_occurrence`) — completing a recurring task automatically spawns a fresh, incomplete copy dated to its next occurrence (+1 day for daily, +7 days for weekly) and re-attaches it to the same pet. One-off tasks don't recur, and re-completing an already-done task never spawns a duplicate.
- **Filtering** (`Owner.filter_tasks`) — narrows tasks by pet name and/or completion status; each filter is optional and the two compose.
- **Plan explanation** (`Scheduler.explain`) — renders the finished plan as human-readable text: scheduled entries, skipped tasks, conflicts, and a plain-language summary of the reasoning.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
tofunmio@Oluwatofunmis-MacBook-Air ai110-module2show-pawpal-starter % python3 main.py
Owner: Tofunmi — 90 min available
Pets: Biscuit, Whiskers
Total tasks: 5

Daily plan for Tofunmi:
  08:00 — Insulin shot for Biscuit (5 min) [priority 1]
  08:05 — Feeding for Whiskers (10 min) [priority 1]
  08:15 — Morning walk for Biscuit (30 min) [priority 1]
  08:45 — Play/enrichment for Whiskers (20 min) [priority 2]
  09:05 — Grooming for Biscuit (25 min) [priority 3]

Scheduled 5 task(s) from a 90 min budget (required tasks first, then by priority).
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
python -m pytest
```

```
(.venv) tofunmio@Oluwatofunmis-MacBook-Air ai110-module2show-pawpal-starter % python -m pytest
======================== test session starts =========================
platform darwin -- Python 3.14.5, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/tofunmio/Documents/codepath-ai110/pawpal/ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 29 items                                                   

tests/test_pawpal.py .............................                 [100%]

========================= 29 passed in 0.01s =========================
(.venv) tofunmio@Oluwatofunmis-MacBook-Air ai110-module2show-pawpal-starter % 
```

The tests in `tests/test_pawpal.py` cover the core scheduling behaviors:

- **Sorting** — tasks come back in the right order (by clock time, and by required → priority → duration).
- **Weighted prioritization** — the urgency score ranks required above optional, is 0 for completed tasks, and lets an overdue lower-priority task overtake a fresh higher-priority one; `urgency_report()` tags overdue tasks and hints when nothing is pending.
- **Recurrence** — completing a daily/weekly task spawns its next occurrence (tomorrow / +7 days), one-off tasks don't recur, and re-completing spawns no duplicates.
- **Filtering** — `Owner.filter_tasks()` narrows by pet name and/or completion status, and the two filters compose.
- **Conflict detection** — overlapping time slots are flagged (including duplicate times), while touching slots and malformed times are handled without crashing.
- **Daily plan** — fixed times are anchored and flexible tasks fill the gaps, the budget is respected (required tasks placed even when over budget, optional ones skipped), and completed/future-dated tasks are left out.
- **Edge cases** — empty owners/pets and zero-minute budgets.

- Note: Confidence level based on system reliability is 4/5.

## 📐 Smarter Scheduling

Beyond the basic priority sort, PawPal+ implements several "smarter" scheduling
behaviors, all in `pawpal_system.py`:

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting by time | `Scheduler.sort_by_time()` | Orders tasks by `preferred_time`; flexible (timeless) tasks sort last |
| Weighted prioritization | `Task.urgency_score()`, `Scheduler.prioritize_by_urgency()`, `Scheduler.urgency_report()` | Blends required/priority/overdue-days/brevity into one urgency score; the only sorter that escalates **overdue** tasks so they can outrank fresher, higher-priority ones |
| Filtering | `Owner.filter_tasks()` | By pet name and/or completion status (each filter optional) |
| Conflict detection | `Scheduler.detect_conflicts()`, `Scheduler.conflict_warning()` | Flags overlapping time slots (same or different pets); returns a crash-proof warning string |
| Recurring tasks | `Task.mark_complete()`, `Task.next_occurrence()` | Completing a daily/weekly task auto-spawns its next occurrence |


## 📸 Demo Walkthrough

PawPal+ runs as a Streamlit app (`streamlit run app.py`). You set how much time you have today, add your pets, give each pet its care tasks, and let it build a plan. Tasks can be filtered by status (all/pending/done) and sorted by time, priority, or urgency.

A typical run:

1. Add a pet, e.g. Biscuit the dog.
2. Add a few tasks for Biscuit — a morning walk, meds, feeding.
3. Sort or filter the task list to see what's still pending.
4. Click Generate schedule to build today's plan.
5. Read the plan, any conflict warnings, and the note explaining why it's ordered that way.

Along the way the Scheduler sorts tasks by time and priority, warns about overlapping times, keeps required tasks even when time is tight, and creates tomorrow's copy of a daily task once you complete it today.

Here's the same thing from the command line (`python main.py`):

```
(.venv) tofunmio@Oluwatofunmis-MacBook-Air ai110-module2show-pawpal-starter % python main.py
Owner: Tofunmi — 90 min available
Pets: Biscuit, Whiskers
Total tasks: 6

Tasks in the order they were added:
  (flexible) — Grooming for Biscuit
       08:15 — Morning walk for Biscuit
       08:00 — Insulin shot for Biscuit
  (flexible) — Nail trim for Biscuit
       18:00 — Evening feed for Whiskers
       08:15 — Play/enrichment for Whiskers

Tasks sorted by time (sort_by_time):
       08:00 — Insulin shot for Biscuit
       08:15 — Morning walk for Biscuit
       08:15 — Play/enrichment for Whiskers
       18:00 — Evening feed for Whiskers
  (flexible) — Grooming for Biscuit
  (flexible) — Nail trim for Biscuit

Tasks by urgency (highest first):
  [134.6] Insulin shot for Biscuit (5 min, priority 1)
  [ 43.8] Nail trim for Biscuit (15 min, priority 3, overdue 2d)
  [ 34.2] Evening feed for Whiskers (10 min, priority 1)
  [ 32.5] Morning walk for Biscuit (30 min, priority 1)
  [ 23.3] Play/enrichment for Whiskers (20 min, priority 2)
  [ 12.9] Grooming for Biscuit (25 min, priority 3)

Filtered to Biscuit's tasks (filter_tasks):
  (flexible) — Grooming for Biscuit
       08:15 — Morning walk for Biscuit
       08:00 — Insulin shot for Biscuit
  (flexible) — Nail trim for Biscuit

Marked 'Grooming' complete → auto-created next daily occurrence due 2026-07-14.

Still pending (filter_tasks completed=False):
       08:15 — Morning walk for Biscuit
       08:00 — Insulin shot for Biscuit
  (flexible) — Nail trim for Biscuit
  (flexible) — Grooming for Biscuit
       18:00 — Evening feed for Whiskers
       08:15 — Play/enrichment for Whiskers

Already completed (filter_tasks completed=True):
  (flexible) — Grooming for Biscuit [done]

⚠ 1 time conflict(s) detected:
  Morning walk (08:15, Biscuit) overlaps Play/enrichment (08:15, Whiskers)

Daily plan for Tofunmi:
  08:00 — Insulin shot for Biscuit (5 min) [priority 1]
  08:15 — Morning walk for Biscuit (30 min) [priority 1]
  08:15 — Play/enrichment for Whiskers (20 min) [priority 2]
  08:45 — Nail trim for Biscuit (15 min) [priority 3]
  18:00 — Evening feed for Whiskers (10 min) [priority 1]
Already done:
  ✓ Grooming for Biscuit
Time conflicts (tasks set to overlapping slots):
  ! Morning walk (08:15, Biscuit) overlaps Play/enrichment (08:15, Whiskers)

Scheduled 5 task(s) from a 90 min budget (fixed times anchored, flexible tasks filled in by priority). 10 min still free. Warning: 1 time conflict(s) to resolve: Morning walk/Play/enrichment.
(.venv) tofunmio@Oluwatofunmis-MacBook-Air ai110-module2show-pawpal-starter % 
```
