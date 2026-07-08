"""PawPal+ demo script.

Builds an owner with two pets and several tasks, then generates and
prints a daily plan. Run with:  python3 main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def build_owner() -> Owner:
    """Create a sample owner with two pets and their care tasks."""
    owner = Owner(name="Tofunmi", time_available=90)  # 90 minutes today

    # --- Pet 1: a dog ---
    biscuit = Pet(name="Biscuit", species="Golden Retriever")
    biscuit.add_task(Task("Morning walk", duration=30, priority=1))
    biscuit.add_task(Task("Insulin shot", duration=5, priority=1, is_required=True))
    biscuit.add_task(Task("Grooming", duration=25, priority=3))

    # --- Pet 2: a cat ---
    whiskers = Pet(name="Whiskers", species="Tabby Cat")
    whiskers.add_task(Task("Feeding", duration=10, priority=1))
    whiskers.add_task(Task("Play/enrichment", duration=20, priority=2))

    owner.add_pet(biscuit)
    owner.add_pet(whiskers)
    return owner


def main() -> None:
    owner = build_owner()

    print(f"Owner: {owner.name} — {owner.time_available} min available")
    print(f"Pets: {', '.join(p.name for p in owner.pets)}")
    print(f"Total tasks: {len(owner.all_tasks())}\n")

    scheduler = Scheduler(owner, start_hour=8)
    scheduler.generate_daily_plan()
    print(scheduler.explain())


if __name__ == "__main__":
    main()
