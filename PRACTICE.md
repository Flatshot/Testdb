# SQL practice exercises

Thirty questions on a **new schema**. The repair-depot tables are gone; this is
a further-education college. Five sets in a row ran on the same fourteen tables,
and the joins had become muscle memory -- so the tables, the columns and the
relationships are all different now. Read [schema.sql](schema.sql) first.

Difficulty is pitched at the same level as the last set, and the same two rules
apply:

- **one concept each.** Nothing stacks a window function on top of a self-join
  on top of a date trick.
- **the prompt states the grain.** "One row per course", "all 84 sections come
  back", "12 rows across 9 programmes".

Coverage is even this time rather than weighted to one tier: 4 recursion, 4
window functions, 4 joins, 4 aggregation, 3 subqueries and EXISTS, 3 dates, 2
set operations, 2 NULLs, 2 grain, 2 general.

**The recursion questions are the ones that changed most.** The last three sets
walked a supervisor chain; `prerequisites` here is a genuine directed **graph**:

- a course can require several others, and be required by several others
- three courses are reachable from the same starting course by **two different
  paths**, so `UNION ALL` would list them twice where `UNION` would not
- the deepest chain runs **three hops**, so a self-join cannot reach the bottom
- levels only ever point downward, so the graph is acyclic and a walk always
  terminates

Only one of the four is a hierarchy at all. The others measure depth, and
generate a month series that no table contains.

**Work through them in the GUI**: double-click `SQL Practice.bat` on Windows or
`sql-practice.command` on macOS/Linux, or run `python gui.py`. It grades your
answer against the expected result and, when you get it right, tells you which
mistake the question was built to catch. Progress is saved between sessions.

To run queries by hand instead:

```
python q.py "SELECT ..."
```

or `python q.py` on its own for an interactive prompt (blank line runs,
`\q` quits).

The tables: `campuses`, `departments`, `instructors`, `students`, `courses`,
`prerequisites`, `terms`, `sections`, `enrolments`, `assessments`, `textbooks`,
`course_books`, `payments`. See [schema.sql](schema.sql).

## Things the data does on purpose

- **`prerequisites` is a graph, not a tree.** 30 edges over 34 courses; 11
  courses require nothing, 4 courses are required by more than one other, and 3
  are reachable from the same start by two paths of different lengths.
- **`NOT IN` is a trap here.** `sections.instructor_id` is NULL for 6 unstaffed
  sections and `instructors.mentor_id` is NULL at the top of the tree, so
  `x NOT IN (SELECT that_column ...)` returns nothing at all.
- **Enrolment clusters around terms; billing does not.** 22 months have a
  payment billed and only 14 have an enrolment: 9 months bill without
  enrolling, 1 enrols without billing -- which is what `EXCEPT` and a
  generated series are for.
- **`grade` is NULL unless the enrolment completed.** 328 of 500 are graded;
  the other 172 are active or withdrawn. `AVG` skips them, `SUM/COUNT(*)` does
  not.
- **Dates are TEXT.** `paid_on - billed_on` does not error -- it coerces to
  numbers and returns nonsense. Use `julianday()` for arithmetic; `<` and `>`
  on ISO dates are fine as strings.
- **18 distinct months** of assessment deadlines across two academic years, so
  `strftime('%m', ...)` collapses two Novembers into one bucket.
- **Sections have two independent children.** 10 have no enrolments, 10 have no
  assessments, and only 1 has neither -- three different sets, so joining both
  fans out rather than filtering.
- **Payment `status` is UPPERCASE** (`PAID`, `DUE`, `LATE`, `WAIVED`) while
  enrolment `status` and section `delivery` are lowercase. The inconsistency is
  deliberate.
- **30 distinct list prices and 23 distinct copy counts**, so
  `SUM(copies) * AVG(price)` and `SUM(copies * price)` genuinely disagree.
- **A three-level mentoring tree.** One instructor has no mentor, 12 mentor
  nobody. Deep enough that a single self-join cannot reach the bottom.
- **Deliberate gaps**: 6 courses never scheduled, 9 students never enrolled, 7
  textbooks on no reading list, 1 section with neither students nor
  assessments.
- **Nullable on purpose**: `grade` (172), `instructor_id` on sections (6),
  `mentor_id` (1), `pay_grade` (2), `funding_band` (7), `copies_held` (10),
  `pages` (3), `paid_on` (52).

## Recursion (4)

An anchor row, then a step that joins back to the CTE itself, run over and
over until a pass returns nothing. Four questions, and only the last is a
hierarchy -- the others walk a dependency graph, measure depth, and
generate rows that are not in any table.

1. **Everything Machine Learning depends on** (Q252)

   Course CMP401 'Machine Learning' has prerequisites, and those have
   prerequisites of their own. List every course it depends on, at any
   depth.

   Five courses qualify. Two are direct prerequisites; the rest are
   reached through them. CMP401 itself is not in the answer.

   *Return: course_id, code, title*

2. **How deep does the chain go** (Q253)

   For every course that has at least one prerequisite, how many hops
   it is from that course to its most distant prerequisite.

   A course whose prerequisites have none of their own is 1. If any
   path runs three courses back, it is 3. Where two paths differ in
   length, take the longer.

   *Return: course_id, code, depth*

3. **Every month, including the quiet ones** (Q254)

   How many enrolments were made in each month from 2024-08 to 2026-05
   inclusive, as 'YYYY-MM'.

   Nobody enrols in August or over the summer, so several months have
   none. Those months must still appear, with 0. That is 22 rows, not
   the 14 a GROUP BY gives you.

   *Return: month, enrolments*

4. **How far below the top** (Q255)

   Every instructor, with how many levels below the top of the
   mentoring tree they sit.

   One instructor has no mentor -- they are level 0. Anyone mentored by
   them is 1, anyone mentored by those is 2. All 16 appear.

   *Return: instructor_id, name, level*

## Window functions (4)

A calculation that sees a set of rows around each row without collapsing
them. PARTITION BY says which rows it may see, ORDER BY orders them inside
that set. Four questions, each isolating one part.

5. **Top of each programme, ties and all** (Q256)

   The highest mark achieved in each programme, and who got it. Only
   graded enrolments count.

   Three programmes have two students tied on the top mark. Both must
   appear, so the answer is 12 rows across 9 programmes.

   *Return: programme, student_id, name, grade*

6. **Term on term** (Q257)

   One row per term, in term order: the term name, how many enrolments
   were made on its sections, and the change from the term before.

   The first term has nothing before it, so its change is NULL -- leave
   it NULL rather than turning it into 0. All six terms appear.

   *Return: term_id, name, enrolments, change*

7. **Billed so far** (Q258)

   One row per calendar month in which anything was billed: the month
   as 'YYYY-MM', the amount billed in it, and the running total of
   everything billed up to and including that month.

   The running total on the last month equals the total of every
   payment row in the table.

   *Return: month, month_total, running_total*

8. **Share of the enrolments by faculty** (Q259)

   One row per faculty: the faculty, how many enrolments its
   departments' courses attracted, and that count as a percentage of
   all enrolments.

   Four faculties, and the four percentages add up to 100.

   *Return: faculty, enrolments, pct_of_total*

## Joins (4)

Four questions where the answer hinges on the rows that DON'T match -- the
unscheduled course, the section with no withdrawals, the textbook nobody
assigns -- plus one on pairing a table with itself.

9. **Every course, scheduled or not** (Q260)

   One row for every course in the catalogue: its id, code, and how
   many sections have ever been scheduled for it.

   Six courses have never been scheduled. They must appear with 0, so
   all 34 courses come back.

   *Return: course_id, code, sections*

10. **Withdrawals per section** (Q261)

    One row for every section: its id, its room, and how many of its
    enrolments were WITHDRAWN.

    Most sections have none. They must appear with 0, so all 84 sections
    come back.

    *Return: section_id, room, withdrawals*

11. **Classmates on the same programme** (Q262)

    Pairs of students on the same programme at the same campus.

    Each pair once, not twice: Ann with Bob, never also Bob with Ann,
    and nobody paired with themselves. Order each pair so that student_a
    is the LOWER student_id. There are 52 pairs.

    *Return: programme, student_a, student_b*

12. **Textbooks nobody assigns** (Q263)

    Every textbook that appears on no course reading list at all.

    Write it as an outer join that keeps the non-matches, rather than
    with NOT IN. There are 7 such books.

    *Return: book_id, title*

## Aggregation (4)

GROUP BY and the functions that ride on it. Four questions on the parts
that are easy to get subtly wrong rather than outright wrong.

13. **Graded and not** (Q264)

    One row per term: its name, how many enrolments were made on its
    sections, and how many of those carry a grade.

    Active and withdrawn enrolments have no grade, so the two counts
    differ in every term.

    *Return: term_id, name, enrolments, graded*

14. **Which programmes were busy in 2026** (Q265)

    Counting only enrolments made on or after 2026-01-01, one row per
    programme, keeping the programmes with at least 10 of them.

    Six of the nine programmes clear the bar.

    *Return: programme, enrolments*

15. **Enrolment status by delivery mode** (Q266)

    One row per delivery mode, with the number of its enrolments in each
    of the three statuses side by side as columns.

    Three delivery modes, and the three columns together account for
    every enrolment.

    *Return: delivery, completed, active, withdrawn*

16. **Average mark, where there is one** (Q267)

    One row per programme: how many enrolments its students made, how
    many of those carry a grade, and the average of the grades that
    exist.

    Only completed enrolments are graded, so in every programme the
    average must be over the graded ones alone -- not over everyone
    enrolled. All nine programmes appear.

    *Return: programme, enrolments, graded, avg_grade*

## Subqueries & EXISTS (3)

Asking a question about a row without changing what a row is. Three
questions: EXISTS instead of a join, NOT EXISTS instead of NOT IN, and a
subquery that has to be re-evaluated per row.

17. **Students who have reached level 4** (Q268)

    Every student who has ever enrolled on a level-4 course.

    Courses sit under sections and sections carry the enrolment. One row
    per student, however many level-4 courses they took -- and several
    took more than one.

    *Return: student_id, name*

18. **Never taught online** (Q269)

    Every instructor who has never taught a section delivered ONLINE.
    Two of the sixteen qualify.

    Watch out: some online sections have no instructor assigned at all,
    which is what makes the obvious answer wrong.

    *Return: instructor_id, name*

19. **Dear for its own publisher** (Q270)

    Every textbook priced above the average list_price of the books from
    ITS OWN publisher -- not above the average across the whole
    catalogue.

    One row per book.

    *Return: book_id, title, publisher, list_price*

## Dates (3)

Dates are TEXT in SQLite. Three questions on doing arithmetic on them,
comparing them across a join, and grouping by them without losing the year.

20. **The five slowest payments to settle** (Q271)

    The five settled payments that took the longest from being billed to
    being paid, longest first.

    Days must be a whole number. Break ties on days by payment_id
    ascending, so the five are unambiguous.

    *Return: payment_id, billed_on, paid_on, days*

21. **Enrolled before the term began** (Q272)

    How many enrolments were made BEFORE their term's start date, broken
    down by term.

    The enrolment date is on the enrolment; the start date is on the
    term, reached through the section. All six terms have some.

    *Return: term_id, name, early_enrolments*

22. **Assessment deadlines by month** (Q273)

    One row per calendar month in which any assessment falls due: the
    month as 'YYYY-MM', and how many are due in it.

    The data spans two academic years, so November 2024 and November
    2025 are different months and must not be added together. There are
    18 such months.

    *Return: month, assessments*

## NULLs (2)

Two questions on the same fact from opposite directions: a comparison
against NULL is neither true nor false, so it never matches and never
excludes -- it just quietly drops the row.

23. **Settled, outstanding, or waived** (Q274)

    Classify every payment into one of three states and count them:

        'settled'     if paid_on has a date
        'waived'      if it has no paid_on and status is WAIVED
        'outstanding' otherwise

    All 136 payments land in exactly one state.

    *Return: state, payments*

24. **Everyone not funding themselves** (Q275)

    Count students by funding band, excluding the self-funded, and
    counting the ones with NO funding band recorded as 'none'.

    41 of the 60 students are not self-funded -- seven of them because
    they have no band at all.

    *Return: band, students  (band is 'grant', 'sponsor' or 'none')*

## Set operations (2)

Stacking two result sets rather than joining them. Two questions: one on
EXCEPT having a direction, one on INTERSECT not being UNION.

25. **Billed in a month nobody enrolled** (Q276)

    Months in which at least one payment was billed but NO enrolment was
    made. Months are 'YYYY-MM'.

    Billing runs all year while enrolment clusters around the terms, so
    this catches the quiet months. Nine qualify.

    *Return: month*

26. **Required reading on a first-year course** (Q277)

    Textbooks that are BOTH marked required (required = 1) on some
    course AND appear on the reading list of a level-1 course.

    The two need not be the same course: a book required on a level-3
    course and merely recommended on a level-1 one still counts. Fifteen
    books qualify.

    *Return: book_id, title*

## Grain (2)

What one row means. Two questions: what happens when two child tables meet
over the same parent, and where the multiplication goes.

27. **Students and assessments on each section** (Q278)

    One row per section: how many students are enrolled on it, and how
    many assessments it has.

    The two are independent -- a section can have many of one and none
    of the other. A section with none of something shows 0, not NULL.
    All 84 sections appear.

    *Return: section_id, students, assessments*

28. **What the library spent by publisher** (Q279)

    One row per publisher, with the total value of the library copies
    held across all reading lists.

    Each course_books row is worth copies_held * list_price. Rows with
    no copies_held recorded contribute nothing. Every line must be
    priced on its own copies and its own book.

    *Return: publisher, value*

## General (2)

One on CASE branch order, one on counting above the grain of a join.

29. **Courses by credit band** (Q280)

    Put every course into one of three bands by credits and count them:

        'major'    30 credits or more
        'standard' 15 to 29 credits
        'short'    everything else

    All 34 courses land in exactly one band.

    *Return: band, courses*

30. **How many departments does each campus actually run** (Q281)

    One row per campus: its name, how many DISTINCT departments have had
    a section scheduled, and how many sections that was in total.

    The path runs campus -> department -> course -> section, so the same
    department is reached once per section. All four campuses appear,
    and no campus has more than three departments.

    *Return: name, departments, sections*

## The one concept with no question here

**Alias scope follows clause order.** Logical order is `FROM` -> `WHERE` ->
`GROUP BY` -> `HAVING` -> window functions -> `SELECT` -> `ORDER BY` ->
`LIMIT`, and a name only exists after the step that creates it. Postgres and
SQL Server reject a SELECT alias in `WHERE`; SQL Server and Oracle reject one
in `GROUP BY`.

There is no graded question for this because **SQLite will not punish you for
it**. It happily accepts an alias in `WHERE`:

```sql
SELECT list_price * 2 AS d FROM textbooks WHERE d > 100   -- fine in SQLite
```

Keep the rule for portability, and reach for a CTE when you want a real
column to filter or group by -- which is also how the top-N-per-group
questions above have to be written, since a window function cannot appear in
`WHERE` on any engine.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
251 retired ones. New questions must not repeat anything in that ledger.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
