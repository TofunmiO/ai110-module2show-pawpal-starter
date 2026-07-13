"""PawPal+ demo script.

Builds an owner with two pets and several tasks (added out of order on
purpose), then exercises the new sorting and filtering methods before
generating a daily plan. Run with:  python3 main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def build_owner() -> Owner:
    """Sample owner with two pets and their care tasks.

    Tasks are added out of chronological order so sort_by_time() has real
    work to do — Grooming (no fixed time) and the evening feed come first
    in the code, the morning tasks come later.
    """
    owner = Owner(name="Tofunmi", time_available=90)  # 90 minutes today

    # --- Pet 1: a dog ---
    biscuit = Pet(name="Biscuit", animal_type="dog")
    biscuit.add_task(Task("Grooming", duration=25, priority=3))  # no fixed time
    biscuit.add_task(Task("Morning walk", duration=30, priority=1, preferred_time="08:15"))
    biscuit.add_task(
        Task("Insulin shot", duration=5, priority=1, is_required=True, preferred_time="08:00")
    )

    # --- Pet 2: a cat ---
    whiskers = Pet(name="Whiskers", animal_type="cat")
    whiskers.add_task(Task("Evening feed", duration=10, priority=1, preferred_time="18:00"))
    # Same 08:15 slot as Biscuit's Morning walk — two tasks at the same time.
    whiskers.add_task(Task("Play/enrichment", duration=20, priority=2, preferred_time="08:15"))

    owner.add_pet(biscuit)
    owner.add_pet(whiskers)
    return owner


def print_tasks(label: str, tasks: list[Task]) -> None:
    """Print a labeled list of tasks with their time and pet."""
    print(label)
    for task in tasks:
        when = task.preferred_time or "(flexible)"
        who = task.pet.name if task.pet else "?"
        done = " [done]" if task.completed else ""
        print(f"  {when:>10} — {task.name} for {who}{done}")
    print()


def main() -> None:
    owner = build_owner()

    print(f"Owner: {owner.name} — {owner.time_available} min available")
    print(f"Pets: {', '.join(p.name for p in owner.pets)}")
    print(f"Total tasks: {len(owner.all_tasks())}\n")

    scheduler = Scheduler(owner, start_hour=8)

    # --- Sorting: tasks were added out of order; sort_by_time() fixes that ---
    print_tasks("Tasks in the order they were added:", owner.all_tasks())
    print_tasks("Tasks sorted by time (sort_by_time):", scheduler.sort_by_time())

    # --- Filtering: by pet, then by completion status ---
    print_tasks("Filtered to Biscuit's tasks (filter_tasks):", owner.filter_tasks(pet_name="Biscuit"))

    # --- Recurring tasks: completing one auto-creates the next occurrence ---
    grooming = owner.filter_tasks(pet_name="Biscuit")[0]  # the "Grooming" task
    upcoming = grooming.mark_complete()
    print(
        f"Marked '{grooming.name}' complete → auto-created next "
        f"{upcoming.frequency} occurrence due {upcoming.due_date}.\n"
    )

    # The status filter now shows the split: the finished one is done, and the
    # freshly-spawned next occurrence shows up as pending.
    print_tasks("Still pending (filter_tasks completed=False):", owner.filter_tasks(completed=False))
    print_tasks("Already completed (filter_tasks completed=True):", owner.filter_tasks(completed=True))

    # --- Conflict detection: lightweight warning, no crash on bad data ---
    warning = scheduler.conflict_warning()
    if warning:
        print(warning + "\n")

    # --- The daily plan (also reports conflicts in its reasoning) ---
    scheduler.generate_daily_plan()
    print(scheduler.explain())


if __name__ == "__main__":
    main()
