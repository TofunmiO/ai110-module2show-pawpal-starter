"""Basic behavior tests for PawPal+ core classes."""

from datetime import date, timedelta

from pawpal_system import Owner, Pet, Task, Scheduler


def test_mark_complete_changes_status():
    """Calling mark_complete() flips a task from not-completed to completed."""
    task = Task("Morning walk", duration=30)

    assert task.completed is False  # starts incomplete
    task.mark_complete()
    assert task.completed is True   # now marked done


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet grows that pet's task list by one."""
    pet = Pet("Biscuit", animal_type="dog")

    assert len(pet.tasks) == 0
    pet.add_task(Task("Feeding", duration=10))
    assert len(pet.tasks) == 1


# --- Sorting by time -------------------------------------------------------

def test_sort_by_time_orders_by_clock_and_puts_flexible_last():
    """Fixed times come out in clock order; timeless tasks fall to the end."""
    owner = Owner("T", time_available=120)
    pet = Pet("Biscuit", "dog")
    pet.add_task(Task("Evening", 10, preferred_time="18:00"))
    pet.add_task(Task("Flexible", 10))  # no time
    pet.add_task(Task("Morning", 10, preferred_time="08:05"))
    owner.add_pet(pet)

    names = [t.name for t in Scheduler(owner).sort_by_time()]
    assert names == ["Morning", "Evening", "Flexible"]


# --- Filtering by pet / status --------------------------------------------

def test_filter_tasks_by_pet_and_status():
    """filter_tasks narrows by pet name and by completion status, and composes."""
    owner = Owner("T", time_available=120)
    biscuit = Pet("Biscuit", "dog")
    whiskers = Pet("Whiskers", "cat")
    # frequency="once" so completing Walk doesn't spawn a recurring successor
    # (that's covered by the recurrence tests); keeps this test about filtering.
    biscuit.add_task(Task("Walk", 30, frequency="once"))
    biscuit.add_task(Task("Meds", 5))
    whiskers.add_task(Task("Feed", 10))
    owner.add_pet(biscuit)
    owner.add_pet(whiskers)
    biscuit.tasks[0].mark_complete()  # Walk done

    assert {t.name for t in owner.filter_tasks(pet_name="Biscuit")} == {"Walk", "Meds"}
    assert {t.name for t in owner.filter_tasks(completed=True)} == {"Walk"}
    assert {t.name for t in owner.filter_tasks(completed=False)} == {"Meds", "Feed"}
    assert [t.name for t in owner.filter_tasks(pet_name="Biscuit", completed=False)] == ["Meds"]


# --- Recurring tasks -------------------------------------------------------

def test_completing_daily_task_spawns_next_occurrence_tomorrow():
    """A completed daily task auto-creates an incomplete copy due today + 1 day."""
    pet = Pet("Biscuit", "dog")
    walk = Task("Walk", 30, frequency="daily")
    pet.add_task(walk)

    upcoming = walk.mark_complete()

    assert upcoming is not None
    assert upcoming.completed is False
    assert upcoming.due_date == date.today() + timedelta(days=1)
    assert upcoming in pet.tasks  # attached to the same pet
    assert upcoming.pet is pet


def test_completing_weekly_task_spawns_next_occurrence_in_a_week():
    """A completed weekly task's successor is due today + 7 days."""
    pet = Pet("Biscuit", "dog")
    bath = Task("Bath", 40, frequency="weekly")
    pet.add_task(bath)

    upcoming = bath.mark_complete()

    assert upcoming.due_date == date.today() + timedelta(weeks=1)


def test_one_off_task_does_not_recur():
    """A non-daily/weekly task spawns no successor when completed."""
    task = Task("Vet visit", 60, frequency="once")
    assert task.mark_complete() is None


def test_completing_twice_does_not_spawn_duplicates():
    """Re-marking an already-complete task is a no-op (no duplicate spawned)."""
    pet = Pet("Biscuit", "dog")
    walk = Task("Walk", 30, frequency="daily")
    pet.add_task(walk)

    walk.mark_complete()
    count_after_first = len(pet.tasks)
    assert walk.mark_complete() is None
    assert len(pet.tasks) == count_after_first


# --- Conflict detection ----------------------------------------------------

def test_detect_conflicts_flags_overlap_across_pets():
    """Two tasks whose time windows overlap are flagged, even on different pets."""
    owner = Owner("T", time_available=300)
    a = Pet("A", "dog")
    b = Pet("B", "cat")
    a.add_task(Task("Walk", 30, preferred_time="08:15"))  # 08:15-08:45
    b.add_task(Task("Play", 20, preferred_time="08:30"))  # 08:30-08:50
    owner.add_pet(a)
    owner.add_pet(b)

    conflicts = Scheduler(owner).detect_conflicts()
    assert len(conflicts) == 1


def test_touching_slots_do_not_conflict():
    """One task ending exactly when the next starts is not a conflict."""
    owner = Owner("T", time_available=300)
    pet = Pet("A", "dog")
    pet.add_task(Task("Walk", 30, preferred_time="08:00"))  # 08:00-08:30
    pet.add_task(Task("Feed", 10, preferred_time="08:30"))  # starts at 08:30
    owner.add_pet(pet)

    assert Scheduler(owner).detect_conflicts() == []


def test_conflict_warning_returns_message_and_never_crashes_on_bad_time():
    """conflict_warning returns a string; a malformed time is skipped, not raised."""
    owner = Owner("T", time_available=300)
    pet = Pet("A", "dog")
    pet.add_task(Task("Walk", 30, preferred_time="08:15"))
    pet.add_task(Task("Feed", 10, preferred_time="08:15"))  # same slot -> conflict
    pet.add_task(Task("Oops", 10, preferred_time="8am"))    # malformed -> skipped
    owner.add_pet(pet)

    warning = Scheduler(owner).conflict_warning()
    assert isinstance(warning, str)
    assert "conflict" in warning.lower()


def test_detect_conflicts_handles_identical_windows_without_crashing():
    """Two tasks with the same start AND duration must not crash the sort."""
    owner = Owner("T", time_available=300)
    a = Pet("A", "dog")
    b = Pet("B", "cat")
    a.add_task(Task("Walk", 30, preferred_time="08:00"))  # 08:00-08:30
    b.add_task(Task("Run", 30, preferred_time="08:00"))   # identical window
    owner.add_pet(a)
    owner.add_pet(b)

    conflicts = Scheduler(owner).detect_conflicts()
    assert len(conflicts) == 1


def test_conflict_warning_empty_when_no_conflicts():
    """No conflicts -> empty string, so callers can just do `if warning:`."""
    owner = Owner("T", time_available=300)
    pet = Pet("A", "dog")
    pet.add_task(Task("Walk", 30, preferred_time="08:00"))
    owner.add_pet(pet)

    assert Scheduler(owner).conflict_warning() == ""


# --- Plan honors fixed times ----------------------------------------------

def test_plan_anchors_fixed_times_and_gap_fills_flexible():
    """Fixed tasks land at their preferred_time; flexible tasks fill the gaps."""
    owner = Owner("T", time_available=300)
    pet = Pet("Rex", "dog")
    pet.add_task(Task("Vet", 30, preferred_time="09:00"))
    pet.add_task(Task("Walk", 20, preferred_time="08:00"))
    pet.add_task(Task("Brush", 15))  # flexible -> should slot into the gap
    owner.add_pet(pet)

    scheduler = Scheduler(owner, start_hour=8)
    scheduler.generate_daily_plan()
    placed = {task.name: start for start, _pet, task in scheduler.entries}

    assert placed["Walk"] == "08:00"   # anchored
    assert placed["Vet"] == "09:00"    # anchored
    assert placed["Brush"] == "08:20"  # filled the 08:20-09:00 gap


def test_plan_skips_completed_and_future_recurring_occurrences():
    """Completed tasks and future-dated spawns don't appear in today's plan."""
    owner = Owner("T", time_available=300)
    pet = Pet("Rex", "dog")
    walk = Task("Walk", 20, frequency="daily")
    pet.add_task(walk)
    owner.add_pet(pet)

    walk.mark_complete()  # completes Walk and spawns tomorrow's Walk
    scheduler = Scheduler(owner)
    scheduler.generate_daily_plan()

    # Neither the finished Walk nor its future occurrence should be scheduled.
    assert scheduler.entries == []
