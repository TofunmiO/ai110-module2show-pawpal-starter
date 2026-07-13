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

    - Tradeoff: detect_conflicts() silently drops any task whose preferred_time is missing or malformed or not put in the format HH:MM

- Why is that tradeoff reasonable for this scenario?
A crash is the worst outcome for this user. A busy owner opens the app in the morning to see their plan. If one typo'd time string ("8am") crashed the whole scheduler, they'd get nothing — no plan, no meds reminder, no conflict warnings for any pet. The app's job is to stay useful and never blow up in someone's face; a rare, recoverable missed check is an acceptable price for that reliability.


## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
