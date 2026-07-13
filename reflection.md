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

    - In app.py, the AI wanted the "Add task" button to build a real Task object and attach it with pet.add_task(...), instead of saving tasks as plain dictionaries in a temporary list. Before accepting, I stopped and asked whether tasks would still persist as I clicked around, or whether the Owner now handled that. The answer: they persist, because the pet lives on the Owner, which is stored in st.session_state. Only once I understood that did I accept the edit.

- How did you evaluate or verify what the AI suggested?

    - I ran the app and tested it from the UI: added tasks, clicked around, and confirmed they stayed on screen instead of disappearing. I also had the AI explain why it worked (the owner-in-session_state chain) rather than trusting the code blindly, and cross-checked that the change removed a duplicate copy of the data instead of adding one.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test? 
    -  UI testing and the UI wiring
     -  Recurrence did not come through on the actual app and explain() did not highlight completed plans and showed daily plan as empty when all tasks have been completed.
- Why were these tests important? 
    - The automated tests passed, but manually testing the app revealed that several newly implemented features (preferred_time, frequency, conflict warnings) weren't surfaced in the UI — so a real user couldn't access them. That made the manual test essential: unit tests prove the logic is correct in isolation, but only using the actual app showed the logic wasn't connected to the front end, leaving the improvements useless to the user until wired in.

**b. Confidence**

- How confident are you that your scheduler works correctly? 
    - 4/5
- What edge cases would you test next if you had more time?
    - Resolve and test the future-dated conflict: making detect_conflicts filter on due_date too.
    - Overdue / past-due tasks. 
    - Out-of-range / odd times in the plan path.
    - Three-or-more overlapping tasks. 
    - Frozen-clock recurrence: test month/year/leap-day rollovers without relying on the real date.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with? 
    - Honestly, just seeing it all come together and actually work. The ideas I sketched out in the UML turned into real code that does what it's supposed to — the scheduler sorts tasks, catches time conflicts, and handles recurring ones, and the Streamlit app pulls it all together. Watching a full plan get generated and explained made it click that everything I built is functional and actually runs.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
    - First, I'd fix the conflict check — right now it can flag a task that's due tomorrow as clashing with today's, which isn't right since that task isn't even in today's plan. 
   - Second, I'd add proper input validation, since the time parser will happily accept something like "25:00" without complaining. The scheduler also leans on the real current date for recurring tasks, so I'd make that easier to control instead of tying it to the actual day. 
  -  Finally, I'd add tests for the app itself, not just the scheduler logic.
   

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
    - The biggest thing is that you can't just take AI's word for it — you have to verify. A few times it told me something was implemented, but when I checked myself, especially on the UI side, it wasn't actually showing up. When I probed, it turned out the behavior was buried under a condition the AI had set, which meant it hadn't really thought through the edge cases — cases where its own logic quietly stopped the code from doing something useful. I also caught it saying it was "done" when it had actually skipped parts. On top of that, AI tends to overdo things and make them more complicated and verbose than they need to be, which adds noise and pulls focus away from the core functionality. So the real lesson is that testing and verification matter just as much as the building.


**c. AI strategy**
- Which AI coding assistant features were most effective for building your scheduler?
    - Claude: mainly that it could read my actual code, edit the files directly, and run my tests and the app to check things worked instead of just guessing
- Give one example of an AI suggestion you rejected or modified to keep your system design clean.
    - When I asked the AI to implement the four scheduling features, its first move was to rewrite the entire pawpal_system.py in one edit — all four features plus new fields and a reworked generate_daily_plan() at once. I rejected that and had it add one feature at a time, starting with just sort_by_time(). Working incrementally kept each method small and single-purpose, let me review and test each piece before the next, and avoided a large tangled change I couldn't verify. It also meant we dropped the AI's original weekday-based recurrence idea (is_due(weekday)) in favor of a simpler due_date approach that emerged once we built recurrence on its own.
- How did using separate chat sessions for different phases help you stay organized?
    - Splitting each phase into its own chat kept the AI's context focused. It was also easier to go back and ask the AI when something broke, phase targeted questions becuase the conversations were separate.
- Summarize what you learned about being the "lead architect" when collaborating with powerful AI tools.
    - Being the lead architect meant the AI was fast and capable, but the judgment stayed mine. I had to interrogate and verify answers as well as set the pace, direction, and structure.