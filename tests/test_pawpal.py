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


# --- Weighted prioritization (urgency scoring) -----------------------------

def test_urgency_score_ranks_required_above_optional():
    """A required task always out-scores any optional one, regardless of priority."""
    required_low = Task("Meds", 5, priority=3, is_required=True)
    optional_high = Task("Walk", 5, priority=1)  # highest optional priority
    assert required_low.urgency_score() > optional_high.urgency_score()


def test_urgency_score_is_zero_for_completed_task():
    """A completed task has nothing left to do, so it scores 0."""
    task = Task("Walk", 30, priority=1, is_required=True)
    task.completed = True
    assert task.urgency_score() == 0.0


def test_overdue_task_can_outrank_a_fresher_higher_priority_task():
    """Enough overdue days let a lower-priority task overtake a fresh higher one.

    This is the behavior a fixed lexicographic sort *cannot* express: here a
    priority-2 task that's a week overdue beats a brand-new priority-1 task.
    """
    today = date(2026, 7, 13)
    overdue_medium = Task(
        "Overdue brush", 20, priority=2, due_date=today - timedelta(days=7)
    )
    fresh_high = Task("Fresh walk", 20, priority=1, due_date=today)

    assert overdue_medium.urgency_score(today) > fresh_high.urgency_score(today)


def test_prioritize_by_urgency_orders_most_urgent_first():
    """Scheduler.prioritize_by_urgency ranks required, then overdue, then priority."""
    today = date(2026, 7, 13)
    owner = Owner("T", time_available=300)
    pet = Pet("Rex", "dog")
    pet.add_task(Task("Meds", 5, priority=2, is_required=True))          # required -> top
    pet.add_task(Task("Overdue walk", 20, priority=2,
                      due_date=today - timedelta(days=3)))              # overdue -> next
    pet.add_task(Task("Fresh play", 20, priority=1, due_date=today))    # fresh high priority
    pet.add_task(Task("Someday groom", 40, priority=3))                 # low, no date -> last
    owner.add_pet(pet)

    names = [t.name for t in Scheduler(owner).prioritize_by_urgency(today=today)]
    assert names == ["Meds", "Overdue walk", "Fresh play", "Someday groom"]


def test_urgency_report_flags_overdue_and_hints_when_empty():
    """urgency_report tags overdue tasks and gives a hint when nothing is pending."""
    today = date(2026, 7, 13)
    owner = Owner("T", time_available=300)
    assert "No pending tasks" in Scheduler(owner).urgency_report(today=today)

    pet = Pet("Rex", "dog")
    pet.add_task(Task("Overdue walk", 20, due_date=today - timedelta(days=2)))
    owner.add_pet(pet)

    report = Scheduler(owner).urgency_report(today=today)
    assert "Overdue walk" in report
    assert "overdue 2d" in report


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


# ===========================================================================
# Additional coverage: priority sort, chronological output, budget rules,
# boundaries, empty inputs, and the future-dated conflict inconsistency.
# ===========================================================================

# --- Sorting correctness: the priority sort used by the planner -----------

def test_sort_tasks_orders_required_then_priority_then_duration():
    """sort_tasks() ranks required-first, then lower priority number, then shorter.

    Exercises all three tiebreakers at once:
      - Meds is required -> must come first despite low (priority 3) priority.
      - Among the rest, priority 1 beats priority 2.
      - Between two priority-2 tasks, the shorter duration wins.
    """
    owner = Owner("T", time_available=300)
    pet = Pet("Rex", "dog")
    pet.add_task(Task("Meds", 5, priority=3, is_required=True))
    pet.add_task(Task("Vet", 30, priority=1))
    pet.add_task(Task("LongWalk", 40, priority=2))
    pet.add_task(Task("ShortWalk", 10, priority=2))
    owner.add_pet(pet)

    names = [t.name for t in Scheduler(owner).sort_tasks()]
    assert names == ["Meds", "Vet", "ShortWalk", "LongWalk"]


def test_plan_entries_are_returned_in_chronological_order():
    """generate_daily_plan() leaves self.entries sorted by clock time."""
    owner = Owner("T", time_available=300)
    pet = Pet("Rex", "dog")
    # Added out of order on purpose.
    pet.add_task(Task("Evening", 20, preferred_time="18:00"))
    pet.add_task(Task("Noon", 20, preferred_time="12:00"))
    pet.add_task(Task("Morning", 20, preferred_time="08:00"))
    owner.add_pet(pet)

    scheduler = Scheduler(owner, start_hour=8)
    scheduler.generate_daily_plan()

    starts = [start for start, _pet, _task in scheduler.entries]
    assert starts == sorted(starts)
    assert starts == ["08:00", "12:00", "18:00"]


# --- Time-budget rules ------------------------------------------------------

def test_required_task_is_placed_even_when_over_budget():
    """A required task is scheduled even when it exceeds the remaining budget."""
    owner = Owner("T", time_available=10)
    pet = Pet("Rex", "dog")
    pet.add_task(Task("Meds", 30, is_required=True))  # 30 min into a 10 min budget
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    scheduler.generate_daily_plan()

    placed = [task.name for _start, _pet, task in scheduler.entries]
    assert "Meds" in placed
    assert scheduler.skipped == []
    assert "over budget" in scheduler.reasoning.lower()


def test_non_required_task_is_skipped_when_it_does_not_fit():
    """A non-required task that exceeds the budget lands in skipped, not entries."""
    owner = Owner("T", time_available=10)
    pet = Pet("Rex", "dog")
    pet.add_task(Task("LongWalk", 30))  # not required, doesn't fit
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    scheduler.generate_daily_plan()

    assert scheduler.entries == []
    assert [t.name for t in scheduler.skipped] == ["LongWalk"]


def test_fits_in_is_inclusive_at_the_exact_boundary():
    """A task whose duration exactly equals the budget still fits (<= boundary)."""
    task = Task("Walk", 30)
    assert task.fits_in(30) is True   # exactly equal -> fits
    assert task.fits_in(29) is False  # one minute short -> does not fit


def test_zero_budget_skips_flexible_but_keeps_required():
    """With no time available, optional tasks are dropped but required ones stay."""
    owner = Owner("T", time_available=0)
    pet = Pet("Rex", "dog")
    pet.add_task(Task("Meds", 5, is_required=True))
    pet.add_task(Task("Walk", 20))  # optional
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    scheduler.generate_daily_plan()

    placed = [task.name for _start, _pet, task in scheduler.entries]
    assert placed == ["Meds"]
    assert [t.name for t in scheduler.skipped] == ["Walk"]


# --- Empty / boundary inputs ------------------------------------------------

def test_owner_with_no_pets_produces_empty_plan_and_explain_hint():
    """No pets -> no tasks -> empty plan, and explain() nudges to generate first."""
    owner = Owner("T", time_available=120)
    scheduler = Scheduler(owner)

    # explain() before any plan tells the caller to generate one.
    assert "generate_daily_plan" in scheduler.explain()

    scheduler.generate_daily_plan()
    assert scheduler.entries == []
    assert scheduler.skipped == []


def test_pet_with_no_tasks_contributes_nothing():
    """A pet with an empty task list doesn't add anything to all_tasks()."""
    owner = Owner("T", time_available=120)
    owner.add_pet(Pet("Ghost", "cat"))  # no tasks
    assert owner.all_tasks() == []


# --- Known inconsistency: future-dated tasks and conflict detection --------

def test_future_dated_task_excluded_from_plan_but_still_flagged_as_conflict():
    """Documents current behavior: detect_conflicts ignores due_date, plan honors it.

    A task due tomorrow is correctly left out of today's plan, yet
    detect_conflicts() (which filters only on `completed`, not `due_date`)
    still pairs it with a same-slot task. If the intended behavior is that
    future tasks never conflict today, this test should flip to assert 0.
    """
    owner = Owner("T", time_available=300)
    pet = Pet("Rex", "dog")
    pet.add_task(Task("Today", 30, preferred_time="08:00"))
    pet.add_task(
        Task("Tomorrow", 30, preferred_time="08:00",
             due_date=date.today() + timedelta(days=1))
    )
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    scheduler.generate_daily_plan()

    planned = [task.name for _start, _pet, task in scheduler.entries]
    assert planned == ["Today"]              # future task excluded from the plan
    assert len(scheduler.detect_conflicts()) == 1  # ...but still flagged as a conflict
