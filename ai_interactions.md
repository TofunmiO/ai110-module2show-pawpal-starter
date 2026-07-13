# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF7)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**Agent used:** Claude Code (Opus 4.8)

**What task did you give the agent?**

Add a third algorithmic scheduling capability that goes beyond the basic
requirements (the prompt suggested things like "next available slot" or
"weighted prioritization"), and document the agent workflow here in
`ai_interactions.md`. I left the *choice* of algorithm to the agent, with the
constraint that it fit the existing design and not just duplicate the two
sorters already there (`sort_tasks`, `sort_by_time`).

**Which files were modified?**

| File | Change |
|------|--------|
| `pawpal_system.py` | Added `Task.urgency_score()` + four `ClassVar` weight constants, and `Scheduler.prioritize_by_urgency()` and `Scheduler.urgency_report()` |
| `tests/test_pawpal.py` | Added 5 tests for the scoring model (required-beats-optional, completed=0, overdue overtakes fresh, full ranking order, overdue tag / empty hint) |
| `main.py` | Added an overdue "Nail trim" task and printed `urgency_report()` in the demo |
| `app.py` | Added "urgency" as a third sort option and an `urgency` column to the task table |
| `README.md` | Documented the feature in Features + Smarter Scheduling table, refreshed the CLI sample output and the test count (24 → 29) |

**What did the agent do?**

1. Read the whole project first (`pawpal_system.py`, tests, `README.md`,
   `main.py`, `app.py`, `reflection.md`) instead of jumping straight to code.
2. Chose **weighted prioritization** over "next available slot" — reasoning
   that `_earliest_free` already does gap-finding, whereas a weighted score was
   genuinely new *and* filled a real gap: nothing in the system considered
   `due_date` for ranking, and my own `reflection.md` had flagged "overdue /
   past-due tasks" as an untested edge case.
3. Implemented `Task.urgency_score()` — blends required status, priority,
   days-overdue, and a quick-win bonus into one number — plus a `Scheduler`
   ranking method and a text report, matching the file's existing docstring
   style and `ClassVar` conventions.
4. Wrote 5 tests, wired the feature into the CLI demo and the Streamlit sort
   options, and updated the README.
5. Ran `pytest` before and after (24 → 29 passing) and ran `main.py` to capture
   real output for the README rather than inventing it.

**What did you have to verify or fix manually?**

- Checked the weights actually behave as claimed: ran `main.py` and confirmed
  the overdue priority-3 "Nail trim" really does jump above the priority-1
  tasks in the urgency ranking (score 43.8 vs 34.2/32.5) — that's the whole
  point of the feature, so I didn't take the docstring's word for it.
- Confirmed it's a *distinct* algorithm, not a reskin of `sort_tasks`: the
  overdue-escalation case is one a fixed lexicographic key order cannot
  produce, and there's a test locking that in.
- Made sure the dataclass weights are `ClassVar`, not accidental instance
  fields that would show up in `Task(...)` constructor args.
- Verified the README's pasted CLI output matches the actual current run
  (task count 6, the new urgency block, the plan now including Nail trim), so
  the docs don't drift from the code.

---

## Prompt Comparison (SF11)

> Compare two different prompts (or two different models) on the same task.

| | Option A | Option B |
|-|----------|----------|
| **Model / tool used** | | |
| **Prompt** | | |
| **Response summary** | | |
| **What was useful** | | |
| **Problems noticed** | | |
| **Decision** | | |

**Which approach did you use in your final implementation and why?**

<!-- Your conclusion -->
