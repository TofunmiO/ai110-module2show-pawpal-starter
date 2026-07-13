"""PawPal+ core domain model.

Implemented from diagrams/uml_draft.mmd.

Ownership chain:  Owner --owns--> Pet --has--> Task
The Scheduler reads tasks only through Owner.all_tasks(), so it never needs
to know how an Owner stores its pets.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, timedelta


@dataclass
class Task:
    """A single unit of pet care (a walk, a feeding, a dose of meds)."""

    name: str
    duration: int  # minutes this task takes
    priority: int = 2  # 1 = high, 2 = medium, 3 = low (lower sorts first)
    frequency: str = "daily"  # "daily" | "weekly" | anything else = one-off
    preferred_time: str | None = None  # "HH:MM" fixed start, or None = flexible
    due_date: date | None = None  # calendar day this task is due (None = unscheduled)
    is_required: bool = False  # True = never skipped (e.g. meds)
    completed: bool = False  # marked done for the day
    pet: Pet | None = None  # the pet this task belongs to (set by Pet.add_task)

    def fits_in(self, remaining_minutes: int) -> bool:
        """Return True if this task can fit in the remaining time budget."""
        return self.duration <= remaining_minutes

    def mark_complete(self) -> Task | None:
        """Mark this task done. If it recurs, create and attach the next occurrence.

        A "daily" or "weekly" task automatically spawns a fresh, not-yet-done
        copy dated to its next occurrence and adds it to the same pet, so the
        next plan picks it up. Returns that new Task, or None if the task
        doesn't recur (or was already complete, so we don't spawn duplicates).
        """
        if self.completed:
            return None
        self.completed = True

        upcoming = self.next_occurrence()
        if upcoming is not None and self.pet is not None:
            self.pet.add_task(upcoming)  # persist it (also sets upcoming.pet)
        return upcoming

    def next_occurrence(self) -> Task | None:
        """Return a fresh copy of this task for its next daily/weekly occurrence.

        The copy starts incomplete with its due_date set relative to today
        (when it was completed): +1 day for "daily", +7 days for "weekly".
        timedelta handles month/year/leap-year rollovers accurately. Returns
        None for one-off tasks.
        """
        step = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}.get(self.frequency)
        if step is None:
            return None  # not a recurring task — nothing to repeat
        # Next due date is measured from today (when the task was completed),
        # so a daily task done today recurs tomorrow regardless of its old date.
        next_due = date.today() + step
        # replace() clones the dataclass; reset completed and drop the pet link
        # (add_task re-attaches it) so the new instance stands on its own.
        return replace(self, completed=False, due_date=next_due, pet=None)


@dataclass
class Pet:
    """A pet and the list of care tasks it needs."""

    name: str
    animal_type: str = ""  # dog, cat, etc.
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet and link the task back to this pet."""
        task.pet = self
        self.tasks.append(task)


@dataclass
class Owner:
    """The pet owner: manages pets and exposes all their tasks."""

    name: str
    time_available: int  # minutes available today
    preferences: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets (flattened)."""
        tasks: list[Task] = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
    ) -> list[Task]:
        """Return tasks narrowed by pet name and/or completion status.

        Each filter is optional: an argument left as None is ignored. So
        filter_tasks() with no arguments behaves like all_tasks(), while
        filter_tasks(pet_name="Biscuit", completed=False) returns only
        Biscuit's tasks that still need doing.
        """
        result: list[Task] = []
        for task in self.all_tasks():
            # Skip tasks belonging to a different pet (or none) when filtering by pet.
            if pet_name is not None and (task.pet is None or task.pet.name != pet_name):
                continue
            # Skip tasks whose status doesn't match when filtering by completion.
            if completed is not None and task.completed != completed:
                continue
            result.append(task)
        return result


class Scheduler:
    """The 'brain': retrieves, organizes, and schedules tasks for an owner.

    generate_daily_plan() fills in the result attributes below; explain() then
    reads them instead of re-computing the schedule.
    """

    def __init__(self, owner: Owner, start_hour: int = 8) -> None:
        """Create a scheduler for an owner, planning from start_hour."""
        self.owner = owner
        self.start_hour = start_hour
        self.entries: list[tuple[str, Pet | None, Task]] = []  # (start_time, pet, task)
        self.skipped: list[Task] = []  # tasks cut because time ran out
        self.conflicts: list[tuple[Task, Task]] = []  # pairs set to overlapping times
        self.reasoning: str = ""  # why the plan looks the way it does

    def sort_tasks(self) -> list[Task]:
        """Order tasks (via the Owner): required first, then by priority, then shortest."""
        return sorted(
            self.owner.all_tasks(),
            key=lambda t: (not t.is_required, t.priority, t.duration),
        )

    def sort_by_time(self, tasks: list[Task] | None = None) -> list[Task]:
        """Order tasks by their preferred "HH:MM" start time.

        "HH:MM" strings are fixed-width and zero-padded, so plain string
        comparison already matches clock order ("08:05" < "08:15" < "18:00").
        Tasks with no fixed time (preferred_time is None) get the fallback
        "99:99", which sorts after any real time, so they fall to the end.
        """
        if tasks is None:
            tasks = self.owner.all_tasks()
        return sorted(tasks, key=lambda t: t.preferred_time or "99:99")

    def detect_conflicts(self, tasks: list[Task] | None = None) -> list[tuple[Task, Task]]:
        """Find pairs of tasks set to overlapping time slots.

        A task occupies the slot [preferred_time, preferred_time + duration).
        Two tasks conflict when their slots overlap — whether they belong to
        the same pet or different pets. Only tasks with a fixed preferred_time
        that aren't completed can conflict; flexible tasks have no slot.
        Tasks that merely touch (one starts exactly when another ends) do not
        conflict. Returns (task_a, task_b) pairs, earliest start first.

        Note: a task whose preferred_time is unparseable (e.g. "8am") is
        silently skipped rather than crashing the check, so a conflict
        involving that task will go undetected.
        """
        if tasks is None:
            tasks = self.owner.all_tasks()

        # Build (start, end, task) minute-windows for timed, pending tasks.
        windows: list[tuple[int, int, Task]] = []
        for task in tasks:
            if task.preferred_time is None or task.completed:
                continue
            start = self._to_minutes(task.preferred_time)
            if start is None:
                continue  # unparseable time — skip it rather than crash
            windows.append((start, start + task.duration, task))
        # Sort by start only: never compare the Task objects (they aren't
        # orderable), which would crash on two identical (start, end) windows.
        windows.sort(key=lambda w: w[0])

        conflicts: list[tuple[Task, Task]] = []
        for i in range(len(windows)):
            _a_start, a_end, a_task = windows[i]
            for j in range(i + 1, len(windows)):
                b_start, _b_end, b_task = windows[j]
                if b_start >= a_end:
                    break  # sorted by start: nothing further can overlap a_task
                conflicts.append((a_task, b_task))
        return conflicts

    def conflict_warning(self) -> str:
        """Lightweight, crash-proof conflict check that returns a warning string.

        Wraps detect_conflicts() (which skips malformed times rather than
        raising) and formats the result as a message. Returns "" when there
        are no conflicts, so callers can simply:

            warning = scheduler.conflict_warning()
            if warning:
                print(warning)
        """
        conflicts = self.detect_conflicts()
        if not conflicts:
            return ""
        lines = [f"⚠ {len(conflicts)} time conflict(s) detected:"]
        for a_task, b_task in conflicts:
            a_who = a_task.pet.name if a_task.pet else "?"
            b_who = b_task.pet.name if b_task.pet else "?"
            lines.append(
                f"  {a_task.name} ({a_task.preferred_time}, {a_who}) overlaps "
                f"{b_task.name} ({b_task.preferred_time}, {b_who})"
            )
        return "\n".join(lines)

    def generate_daily_plan(self) -> None:
        """Build the plan within the time budget, filling entries/skipped/reasoning.

        Fixed-time tasks are anchored at their preferred_time (so the plan
        matches what conflict detection reports); flexible tasks fill the
        earliest free gaps around them. Completed and future-dated tasks are
        skipped entirely.
        """
        self.entries = []
        self.skipped = []
        remaining = self.owner.time_available

        # Only plan tasks that are still pending and due today or earlier.
        eligible = [
            task
            for task in self.owner.all_tasks()
            if not task.completed
            and not (task.due_date is not None and task.due_date > date.today())
        ]

        # Split into fixed-time (a parseable preferred_time) and flexible tasks.
        fixed: list[tuple[int, Task]] = []
        flexible: list[Task] = []
        for task in eligible:
            start = self._to_minutes(task.preferred_time) if task.preferred_time else None
            if start is None:
                flexible.append(task)  # no time (or unparseable) — place it in a gap
            else:
                fixed.append((start, task))
        fixed.sort(key=lambda pair: pair[0])  # by clock time

        occupied: list[tuple[int, int]] = []  # (start, end) minutes already taken

        def place(task: Task, start: int) -> None:
            self.entries.append((self._format_time(start), task.pet, task))
            occupied.append((start, start + task.duration))

        # 1) Anchor fixed-time tasks at their requested time (earliest first).
        for start, task in fixed:
            # Required tasks (e.g. meds) are always placed, even if over budget.
            if task.is_required or task.fits_in(remaining):
                place(task, start)
                remaining -= task.duration
            else:
                self.skipped.append(task)

        # 2) Fill flexible tasks into the earliest free gaps, by importance.
        flexible.sort(key=lambda t: (not t.is_required, t.priority, t.duration))
        for task in flexible:
            if not (task.is_required or task.fits_in(remaining)):
                self.skipped.append(task)
                continue
            start = self._earliest_free(task.duration, occupied, self.start_hour * 60)
            place(task, start)
            remaining -= task.duration

        # Show the plan in chronological order (HH:MM strings sort by clock).
        self.entries.sort(key=lambda entry: entry[0])

        self.conflicts = self.detect_conflicts()
        self.reasoning = self._build_reasoning(remaining)

    def explain(self) -> str:
        """Explain the plan by reading entries, skipped, and reasoning."""
        if not self.entries and not self.skipped:
            return "No plan generated yet — call generate_daily_plan() first."

        lines = [f"Daily plan for {self.owner.name}:"]
        for start, pet, task in self.entries:
            who = pet.name if pet else "?"
            lines.append(
                f"  {start} — {task.name} for {who} "
                f"({task.duration} min) [priority {task.priority}]"
            )
        if self.skipped:
            lines.append("Skipped (not enough time):")
            for task in self.skipped:
                lines.append(f"  - {task.name} ({task.duration} min)")
        if self.conflicts:
            lines.append("Time conflicts (tasks set to overlapping slots):")
            for a_task, b_task in self.conflicts:
                a_who = a_task.pet.name if a_task.pet else "?"
                b_who = b_task.pet.name if b_task.pet else "?"
                lines.append(
                    f"  ! {a_task.name} ({a_task.preferred_time}, {a_who}) "
                    f"overlaps {b_task.name} ({b_task.preferred_time}, {b_who})"
                )
        lines.append("")
        lines.append(self.reasoning)
        return "\n".join(lines)

    # --- helpers -----------------------------------------------------------

    @staticmethod
    def _format_time(total_minutes: int) -> str:
        """Turn minutes-since-midnight into a HH:MM clock string."""
        hours = (total_minutes // 60) % 24
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"

    @staticmethod
    def _earliest_free(
        duration: int, occupied: list[tuple[int, int]], from_minute: int
    ) -> int:
        """Earliest start >= from_minute where `duration` fits without overlap.

        Walks the already-occupied (start, end) windows in order; the task
        slots into the first gap big enough, otherwise lands after everything.
        """
        start = from_minute
        for begin, end in sorted(occupied):
            if start + duration <= begin:
                return start  # fits in the gap before this block
            start = max(start, end)  # otherwise jump past the block
        return start

    @staticmethod
    def _to_minutes(preferred_time: str) -> int | None:
        """Parse "HH:MM" into minutes-since-midnight; return None if malformed.

        Returning None instead of raising lets conflict checks skip a bad time
        (e.g. "8am", "8:00:00", None) rather than crash the whole schedule.
        """
        try:
            hours, minutes = preferred_time.split(":")
            return int(hours) * 60 + int(minutes)
        except (ValueError, AttributeError):
            return None

    def _build_reasoning(self, remaining: int) -> str:
        """Summarize the scheduling decisions for explain()."""
        parts = [
            f"Scheduled {len(self.entries)} task(s) from a "
            f"{self.owner.time_available} min budget (fixed times anchored, "
            f"flexible tasks filled in by priority)."
        ]
        if remaining < 0:
            parts.append(f"Went {-remaining} min over budget to keep required tasks.")
        elif remaining > 0:
            parts.append(f"{remaining} min still free.")
        if self.skipped:
            names = ", ".join(t.name for t in self.skipped)
            parts.append(f"Dropped low-priority tasks that no longer fit: {names}.")
        if self.conflicts:
            pairs = ", ".join(f"{a.name}/{b.name}" for a, b in self.conflicts)
            parts.append(
                f"Warning: {len(self.conflicts)} time conflict(s) to resolve: {pairs}."
            )
        return " ".join(parts)
