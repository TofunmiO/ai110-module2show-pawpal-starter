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
collected 24 items                                                   

tests/test_pawpal.py ........................                  [100%]

========================= 24 passed in 0.01s =========================
(.venv) tofunmio@Oluwatofunmis-MacBook-Air ai110-module2show-pawpal-starter % 
```

The tests in `tests/test_pawpal.py` cover the core scheduling behaviors:

- **Sorting** — tasks come back in the right order (by clock time, and by required → priority → duration).
- **Recurrence** — completing a daily/weekly task spawns its next occurrence (tomorrow / +7 days), one-off tasks don't recur, and re-completing spawns no duplicates.
- **Filtering** — `Owner.filter_tasks()` narrows by pet name and/or completion status, and the two filters compose.
- **Conflict detection** — overlapping time slots are flagged (including duplicate times), while touching slots and malformed times are handled without crashing.
- **Daily plan** — fixed times are anchored and flexible tasks fill the gaps, the budget is respected (required tasks placed even when over budget, optional ones skipped), and completed/future-dated tasks are left out.
- **Edge cases** — empty owners/pets and zero-minute budgets.

## 📐 Smarter Scheduling

Beyond the basic priority sort, PawPal+ implements four "smarter" scheduling
behaviors, all in `pawpal_system.py`:

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Sorting by time | `Scheduler.sort_by_time()` | Orders tasks by `preferred_time`; flexible (timeless) tasks sort last |
| Filtering | `Owner.filter_tasks()` | By pet name and/or completion status (each filter optional) |
| Conflict detection | `Scheduler.detect_conflicts()`, `Scheduler.conflict_warning()` | Flags overlapping time slots (same or different pets); returns a crash-proof warning string |
| Recurring tasks | `Task.mark_complete()`, `Task.next_occurrence()` | Completing a daily/weekly task auto-spawns its next occurrence |


## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
