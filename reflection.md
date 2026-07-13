# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
    - An app that helps a pet owner plan care tasks for their pet. 

- What classes did you include, and what responsibilities did you assign to each?
    - Owner class: 
        - Attributes: name, time_available, preferences, list of pet
        - Methods: add a pet(pet), all_tasks()
    - Pet class:
        - Attributes: name, animal_type, list of Task
        - Methods: add a task(task)
    -Task Class:
        - Attributes: name, duration, priority
        - Methods: fits_in(remaining_minutes)
    - Scheduler class: 
        - Attributes: owner
        - Methods: sort_task(), generate_daily_plan(), explain() 


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

    - Added pet as an attribute to Task class. 
    Why: Each task now links to its pet, so the plan can show which pet a task is for.

    - In Task class: Changed priority attribute from a word to a number (1 = high) 
    Why: so tasks sort by importance, not alphabetically.

    - Task class: added is_required attribute as a boolean.
    Why: so mandatory tasks like meds are never skipped when time runs out.

    - Task class: added frequency (daily/weekly) attribution and completed (done for the day) attributes, plus a mark_done() method, to track what still needs scheduling.

    - Scheduler class: Instead of generate_daily_plan() method returning a plain list[Task], Scheduler now holds three attributes it fills in — the scheduled tasks with times (entries), the cut tasks (skipped), and the reasoning.
    - Why (the Scheduler change): A plain list forgets the times and what was dropped, but explain() method needs both. Storing them on Scheduler lets explain() method read the decisions instead of re-computing the schedule. The Scheduler also reads tasks only through Owner.all_tasks(), so it never depends on how an Owner stores its pets.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

    - Tradeoff: detect_conflicts() silently drops any task whose preferred_time is malformed or unparseable (e.g. "8am", "8.00", "8:00:00"). _to_minutes() can't read those, returns None, and the task is skipped before any comparison happens. (Tasks with no time aren't a loss — those are just flexible tasks that legitimately have no slot to clash with.) So the scheduler trades "never crash on a bad time string" for "might silently miss a real conflict."

- Why is that tradeoff reasonable for this scenario?
A crash is the worst outcome for this user. A busy owner opens the app in the morning to see their plan — if one typo'd time crashed the whole scheduler, they'd get nothing: no plan, no meds reminder, no conflict warnings for any pet. Degrading gracefully beats failing completely. The cost is also narrow and recoverable: the dropped task doesn't disappear — it still shows in the task list and gets scheduled as a flexible task in a free gap, so it's only "not time-checked," not lost. The real downside is that the skip is silent — the owner is never told a time couldn't be read, so they might assume everything was checked. 


## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)? 
    -Test design & writing, Connecting logic to the UI, Debugging , Refactoring, and Documentation & UML .
- What kinds of prompts or questions were most helpful?
    - Explicit scoped requests attaching revelant files
    - Review/list before you build
    - Probing follow-ups
    - Constraints on style and scope 
    - Telling it my observations from actually running it and edge cases it should consider based on my experience testing the app from the UI
    - Asking for honesty

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

    - In `app.py`, the AI wanted the "Add task" button to build a real `Task` object and attach it with `pet.add_task(...)`, instead of saving tasks as plain dictionaries in a temporary list. Before accepting, I stopped and asked whether tasks would still persist as I clicked around, or whether the `Owner` now handled that. The answer: they persist, because the pet lives on the `Owner`, which is stored in `st.session_state` (Streamlit's memory that survives re-runs). Only once I understood that did I accept the edit.

- How did you evaluate or verify what the AI suggested?

    - I ran the app and tested it from the UI: added tasks, clicked around, and confirmed they stayed on screen instead of disappearing. I also had the AI explain *why* it worked (the owner-in-session_state chain) rather than trusting the code blindly, and cross-checked that the change removed a duplicate copy of the data instead of adding one.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test? UI and if logic implemented showed on the UI front
- Why were these tests important? It showed a lot of new logic impleented were not showing on the UI and the user would not have had access to thiis which annuls the point of the improvements made tot he app.

**b. Confidence**

- How confident are you that your scheduler works correctly? 4/5
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with? The completion and seeing all the ideas come to live and be functional

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
Sometimes they over do and make it unecessarily complicaated  and verbose which can increase noise and take focus from the core functionalities.
AI says it implenented soenthing and i check myself especially on the UI front and it does not show and when i peobe AI, it is because it is buried under a condition AI set which shows AI didn't consider some cases where it prevents the code from doing sonehting useful in the case of an edge case.
Discovered AI said it was done implementing and it actually skipped some parts. Testing and verification iis iso important