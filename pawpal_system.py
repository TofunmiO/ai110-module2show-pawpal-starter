"""PawPal+ core domain model.

Implemented from diagrams/uml_draft.mmd.

Ownership chain:  Owner --owns--> Pet --has--> Task
The Scheduler reads tasks only through Owner.all_tasks(), so it never needs
to know how an Owner stores its pets.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Task:
    """A single unit of pet care (a walk, a feeding, a dose of meds)."""

    name: str
    duration: int  # minutes this task takes
    priority: int = 2  # 1 = high, 2 = medium, 3 = low (lower sorts first)
    frequency: str = "daily"  # "daily" | "weekly"
    is_required: bool = False  # True = never skipped (e.g. meds)
    completed: bool = False  # marked done for the day
    pet: Pet | None = None  # the pet this task belongs to (set by Pet.add_task)

    def fits_in(self, remaining_minutes: int) -> bool:
        """Return True if this task can fit in the remaining time budget."""
        return self.duration <= remaining_minutes

    def mark_complete(self) -> None:
        """Mark this task complete so the scheduler skips it."""
        self.completed = True


@dataclass
class Pet:
    """A pet and the list of care tasks it needs."""

    name: str
    species: str = ""
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
        self.reasoning: str = ""  # why the plan looks the way it does

    def sort_tasks(self) -> list[Task]:
        """Order tasks (via the Owner): required first, then by priority, then shortest."""
        return sorted(
            self.owner.all_tasks(),
            key=lambda t: (not t.is_required, t.priority, t.duration),
        )

    def generate_daily_plan(self) -> None:
        """Build the plan within the time budget, filling entries/skipped/reasoning."""
        self.entries = []
        self.skipped = []
        remaining = self.owner.time_available
        cursor = self.start_hour * 60  # minutes since midnight

        for task in self.sort_tasks():
            if task.completed:
                continue
            # Required tasks (e.g. meds) are always placed, even if over budget.
            if task.is_required or task.fits_in(remaining):
                self.entries.append((self._format_time(cursor), task.pet, task))
                remaining -= task.duration
                cursor += task.duration
            else:
                self.skipped.append(task)

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

    def _build_reasoning(self, remaining: int) -> str:
        """Summarize the scheduling decisions for explain()."""
        parts = [
            f"Scheduled {len(self.entries)} task(s) from a "
            f"{self.owner.time_available} min budget (required tasks first, "
            f"then by priority)."
        ]
        if remaining < 0:
            parts.append(f"Went {-remaining} min over budget to keep required tasks.")
        elif remaining > 0:
            parts.append(f"{remaining} min still free.")
        if self.skipped:
            names = ", ".join(t.name for t in self.skipped)
            parts.append(f"Dropped low-priority tasks that no longer fit: {names}.")
        return " ".join(parts)
