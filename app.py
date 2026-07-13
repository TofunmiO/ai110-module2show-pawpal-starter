import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to PawPal+.

Enter your owner, pet, and task details below. The app builds them into
`Owner`/`Pet`/`Task` objects and runs your `Scheduler` to produce a daily plan.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner")
owner_name = st.text_input("Owner name", value="Jordan")
time_available = st.number_input(
    "Time available today (minutes)", min_value=5, max_value=600, value=90, step=5
)

# --- The "vault": create the Owner once, then reuse it across re-runs. ---
# Streamlit re-runs this whole script on every interaction, so we only build
# the Owner if it isn't already stored in session_state.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name, time_available=int(time_available))

# Fetch the persisted Owner and keep its basic info in sync with the inputs.
owner = st.session_state.owner
owner.name = owner_name
owner.time_available = int(time_available)

st.markdown("### Pets")
pcol1, pcol2 = st.columns(2)
with pcol1:
    new_pet_name = st.text_input("Pet name", value="Mochi")
with pcol2:
    new_animal_type = st.selectbox("Animal type", ["dog", "cat", "other"])

if st.button("Add pet"):
    name = new_pet_name.strip()
    existing_names = {p.name.lower() for p in owner.pets}
    if not name:
        st.warning("Enter a pet name first.")
    elif name.lower() in existing_names:
        st.warning(f"A pet named '{name}' already exists.")
    else:
        # Owner.add_pet stores the new Pet on the owner (which lives in
        # session_state), so pets persist across re-runs.
        owner.add_pet(Pet(name=name, animal_type=new_animal_type))

if owner.pets:
    st.write("Current pets: " + ", ".join(f"{p.name} ({p.animal_type})" for p in owner.pets))
else:
    st.info("No pets yet. Add one above.")

st.markdown("### Tasks")

# Task.priority is a number (1 = high); map the friendly labels to it.
PRIORITY_MAP = {"high": 1, "medium": 2, "low": 3}

if not owner.pets:
    st.caption("Add a pet before adding tasks.")
else:
    # Pick which pet this task belongs to (by index, so duplicate names are safe).
    idx = st.selectbox(
        "Pet for this task",
        range(len(owner.pets)),
        format_func=lambda i: owner.pets[i].name,
    )
    selected_pet = owner.pets[idx]

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    if st.button("Add task"):
        # Pet.add_task stores the Task on the chosen pet (and sets its back-link).
        selected_pet.add_task(
            Task(
                name=task_title,
                duration=int(duration),
                priority=PRIORITY_MAP[priority],
            )
        )

    if selected_pet.tasks:
        st.write(f"Tasks for {selected_pet.name}:")
        st.table(
            [
                {
                    "title": t.name,
                    "duration_minutes": t.duration,
                    "priority": t.priority,
                }
                for t in selected_pet.tasks
            ]
        )
    else:
        st.info(f"No tasks yet for {selected_pet.name}. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Runs your Scheduler on the tasks above.")

if st.button("Generate schedule"):
    if not owner.all_tasks():
        st.warning("Add at least one task first.")
    else:
        scheduler = Scheduler(owner)
        scheduler.generate_daily_plan()

        st.markdown("#### Daily plan")
        st.table(
            [
                {
                    "time": start,
                    "task": task.name,
                    "pet": p.name if p else "?",
                    "min": task.duration,
                    "priority": task.priority,
                }
                for start, p, task in scheduler.entries
            ]
        )
        if scheduler.skipped:
            st.caption(
                "Skipped (no time): "
                + ", ".join(t.name for t in scheduler.skipped)
            )
        st.markdown("**Why this plan**")
        st.write(scheduler.reasoning)
