"""PawPal+ core domain model.

Class skeletons generated from diagrams/uml_draft.mmd.
Attributes and method signatures only — no logic yet.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Task:
    """A single unit of pet care (e.g. a walk, a feeding, a dose of meds)."""

    name: str
    duration: int  # minutes
    priority: str  # "high" | "medium" | "low"

    def fits_in(self, remaining_minutes: int) -> bool:
        """Return True if this task can fit in the remaining time budget."""
        raise NotImplementedError


@dataclass
class Pet:
    """A pet that owns a list of care tasks."""

    name: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet."""
        raise NotImplementedError


@dataclass
class Owner:
    """The pet owner and their scheduling constraints."""

    name: str
    time_available: int  # minutes available today
    preferences: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        raise NotImplementedError

    def all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        raise NotImplementedError


class DailyPlan:
    """Generates and explains a daily care plan for an owner."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def sort_tasks(self) -> list[Task]:
        """Return the owner's tasks ordered for scheduling (e.g. by priority)."""
        raise NotImplementedError

    def generate_daily_plan(self) -> list[Task]:
        """Build the daily plan, respecting the owner's time budget."""
        raise NotImplementedError

    def explain(self) -> str:
        """Explain why the plan was chosen the way it was."""
        raise NotImplementedError
