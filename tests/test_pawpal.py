"""Basic behavior tests for PawPal+ core classes."""

from pawpal_system import Pet, Task


def test_mark_complete_changes_status():
    """Calling mark_complete() flips a task from not-completed to completed."""
    task = Task("Morning walk", duration=30)

    assert task.completed is False  # starts incomplete
    task.mark_complete()
    assert task.completed is True   # now marked done


def test_add_task_increases_pet_task_count():
    """Adding a task to a Pet grows that pet's task list by one."""
    pet = Pet("Biscuit", species="Golden Retriever")

    assert len(pet.tasks) == 0
    pet.add_task(Task("Feeding", duration=10))
    assert len(pet.tasks) == 1
