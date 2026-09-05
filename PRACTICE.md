# SQL practice exercises

Thirty questions on the college schema, re-seeded so no answer from the previous
set carries over. **The tables are the same** -- see [schema.sql](schema.sql).

Same **easy-to-hard ramp** as the last set, and the same difficulty: one concept
per question, every prompt states its grain.

| Stage | Questions | What it is |
|---|---|---|
| 1 - Warm-up | 1-6 | one table, no joins |
| 2 - First joins | 7-12 | two tables, outer joins, EXISTS |
| 3 - Recursion | 13-16 | the gentlest in the set |
| 4 - Dates, sets and pivots | 17-22 | |
| 5 - Window functions | 23-27 | |
| 6 - Grain and correlation | 28-30 | the ones needing most care |

**What is new is the questions.** Each reaches its concept through a different
table or relationship than last time, so none is the previous set with the
constants swapped. `COUNT(*)` vs `COUNT(col)` is now about staffed sections
rather than funded students; the self-join is a room clash rather than a pair of
courses; the fan-out is two children of `students` rather than of `sections`.

**The four recursion questions are four different shapes** this time, rather
than one shape from four starting points:

1. **down a tree from its root** — 15 people below the top, of whom only 3 are
   direct, so a single join is visibly not enough
2. **down a straight chain** — two hops, no branching anywhere
3. **up a branching chain** — one course, five things blocked by it
4. **a walk that includes its own starting row** — and where `UNION` and
   `UNION ALL` finally disagree

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
`course_books`, `payments`.

## Things the data does on purpose

- **`prerequisites` is a graph, not a tree.** 30 edges over 34 courses; 11
  courses require nothing, the deepest chain runs 3 hops, and 5 course pairs are
  reachable by two different routes — which is why `UNION` vs `UNION ALL`
  changes the answer in question 16 but not in 14.
- **A three-level mentoring tree.** One instructor has no mentor and mentors 3
  people directly, but 15 sit below them in total. 12 mentor nobody.
- **`NOT IN` is a trap here.** `instructors.mentor_id` is NULL at the top and
  `sections.instructor_id` is NULL for 12 unstaffed sections, so
  `x NOT IN (SELECT that_column ...)` returns nothing at all.
- **Enrolment clusters around terms; billing does not.** 22 months have a
  payment billed and only 14 have an enrolment.
- **`grade` is NULL unless the enrolment completed.** 373 of 550 are graded; the
  other 177 are active or withdrawn. `AVG` skips them, `SUM/COUNT(*)` does not.
- **Dates are TEXT.** `ends_on - starts_on` does not error — it coerces to
  numbers and returns nonsense. Use `julianday()` for arithmetic; `<` and `>` on
  ISO dates are fine as strings.
- **18 distinct months** of assessment deadlines and 14 of enrolments, across
  two academic years — so `strftime('%m', ...)` halves the row count.
- **Assessment weights do not always add up.** 20 of the 74 sections that have
  assessments have weights totalling something other than 1. Deliberate: it is
  what question 30 looks for, and it needs rounding before comparison.
- **Sections have two independent children**, and so do students. 5 sections
  have no enrolments and 11 have no assessments — different sets, so joining
  both fans out rather than filtering.
- **Payment `status` is UPPERCASE** (`PAID`, `DUE`, `LATE`, `WAIVED`) while
  enrolment `status` and section `delivery` are lowercase. Deliberate.
- **30 distinct list prices and 20 distinct copy counts**, so
  `SUM(copies) * AVG(price)` and `SUM(copies * price)` genuinely disagree.
- **Deliberate gaps**: 6 courses never scheduled, 9 students never enrolled, 6
  textbooks on no reading list.
- **Nullable on purpose**: `grade` (177), `paid_on` (51), `copies_held` (13),
  `instructor_id` on sections (12), `funding_band` (9), `pay_grade` (7),
  `pages` (4), `mentor_id` (1).

## 1 - Warm-up (6)

Six questions on a single table, no joins at all. Each isolates one
behaviour of GROUP BY, CASE or NULL.

1. **Staffed and unstaffed** (Q312)

   One row per delivery mode: how many sections use it, and how many of
   those have an instructor assigned.

   Some sections are scheduled but not yet staffed, so the two counts
   differ in every mode. One table, no joins.

   *Return: delivery, sections, staffed*

2. **Which assessment kinds cluster in 2026** (Q313)

   Counting only assessments due on or after 2026-01-01, one row per
   kind, keeping the kinds with at least 15 of them.

   Two of the four kinds clear the bar. One table, no joins.

   *Return: kind, assessments*

3. **Instructors by pay band** (Q314)

   Put every instructor into one of three bands by hourly_rate and
   count them:

       'senior'   70 or more
       'standard' 50 up to but not including 70
       'junior'   everything else

   All 16 instructors land in exactly one band.

   *Return: band, instructors*

4. **Graded, dropped, or still going** (Q315)

   Classify every enrolment into one of three states and count them:

       'graded'      if grade has a value
       'dropped'     if it has no grade and status is withdrawn
       'in progress' otherwise

   All 550 enrolments land in exactly one state.

   *Return: state, enrolments*

5. **Everyone not on the top pay grade** (Q316)

   Count instructors by pay grade, excluding grade 5, and counting the
   ones with NO pay grade recorded as 'none'.

   15 of the 16 instructors are not on grade 5 -- seven of them because
   they have no grade at all.

   *Return: grade, instructors  (text: '1'..'4' or 'none')*

6. **Average copies held, where it is known** (Q317)

   One row per required flag (0 and 1): how many reading-list entries
   have it, how many of those record a copies_held figure, and the
   average of the figures that exist.

   Plenty of entries have no copy target set. The average must be over
   the recorded ones only. One table, no joins.

   *Return: required, entries, with_copies, avg_copies*

## 2 - First joins (6)

Two tables at a time. Four of the six hinge on the rows that DON'T match --
the student who never enrolled, the department with no level-4 course, the
instructor nobody reports to.

7. **Every student, enrolled or not** (Q318)

   One row for every student on the books: id, name, and how many
   enrolments they have made.

   Nine students have never enrolled on anything. They must appear with
   0, so all 60 students come back.

   *Return: student_id, name, enrolments*

8. **Level-4 courses per department** (Q319)

   One row for every department: id, name, and how many LEVEL-4 courses
   it owns.

   Only three departments run anything at level 4. The other six must
   appear with 0, so all 9 departments come back.

   *Return: department_id, name, level4_courses*

9. **Room clashes** (Q320)

   Pairs of sections booked into the same room in the same term.

   Each pair once, not twice, and no section paired with itself. Order
   each pair so that section_a is the LOWER section_id. There are 51
   pairs.

   *Return: term_id, room, section_a, section_b*

10. **Students who never enrolled** (Q321)

    Every student who has never enrolled on anything at all.

    Write it as an outer join that keeps the non-matches, rather than
    with NOT IN. There are 9 such students.

    *Return: student_id, name*

11. **Courses with an unstaffed section** (Q322)

    Every course that has at least one section with no instructor
    assigned.

    One row per course, however many unstaffed sections it has -- and
    some have more than one. Nine courses qualify.

    *Return: course_id, code*

12. **Instructors who mentor nobody** (Q323)

    Every instructor who is nobody's mentor. Twelve of the sixteen
    qualify.

    Watch out: one instructor -- the one at the top -- has no mentor
    themselves, so mentor_id contains a NULL. That is what makes the
    obvious answer wrong.

    *Return: instructor_id, name*

## 3 - Recursion (4)

Still the gentlest questions in the set -- an anchor that is one obvious
row and a step that is one join back to the CTE. But these are four
different SHAPES rather than the same walk four times: down a tree, down a
straight chain, up a branching one, and one whose anchor is its own answer.

13. **Everyone under Margaret Ashworth** (Q324)

    Margaret Ashworth is the one instructor with no mentor. List
    everyone below her: the people she mentors, the people they mentor,
    and so on.

    Fifteen rows -- everyone except Margaret herself. Only three are her
    direct mentees, which is why a single join is not enough.

    *Return: instructor_id, name*

14. **What Audit and Assurance needs** (Q325)

    Course ACC301 'Audit and Assurance' has a prerequisite, and that has
    one of its own. List every course ACC301 depends on, at any depth.

    This chain is a straight line -- exactly one prerequisite at each
    hop -- so it is two rows. ACC301 itself is not in the answer.

    *Return: code, title*

15. **What is blocked by Computer Systems** (Q326)

    The other way round. Every course that requires CMP110 'Computer
    Systems', directly or indirectly -- everything a student could not
    take until they had passed it.

    Five courses, and the chain branches: two require it directly, and
    the rest come through those.

    *Return: code, title*

16. **A full study plan for Machine Learning** (Q327)

    Everything a student must pass to finish CMP401 'Machine Learning'
    -- every course it depends on at any depth, AND CMP401 itself.

    Six courses. Unlike question 14 this one branches, and one course is
    reachable by two different routes but must still appear once.

    *Return: code, title*

## 4 - Dates, sets and pivots (6)

Dates are TEXT in SQLite, and set operators stack results rather than
joining them. Six questions on doing both correctly.

17. **How long each term runs** (Q328)

    One row per term: its name, and how many whole days it lasts from
    starts_on to ends_on.

    All six terms appear, and every length is a whole number between 70
    and 90.

    *Return: term_id, name, days*

18. **Enrolments by month** (Q329)

    One row per calendar month in which any enrolment was made: the
    month as 'YYYY-MM', and how many were made in it.

    The data spans two academic years, so the same month name recurs and
    the two must not be added together. There are 14 such months.

    *Return: month, enrolments*

19. **Deadlines after the term ends** (Q330)

    Assessments whose due date falls AFTER the end of the term their
    section runs in.

    The due date is on the assessment; the end date is on the term,
    reached through the section. There are 13.

    *Return: assessment_id, title, due_on, ends_on*

20. **First-year reading that never reappears** (Q331)

    Textbooks that appear on a LEVEL-1 course's reading list but on no
    LEVEL-3 course's list.

    Eight books qualify. A book on both a level-1 and a level-3 course
    is excluded, even if the two are in different departments.

    *Return: book_id, title*

21. **Students who have both finished and dropped** (Q332)

    Students who have BOTH completed at least one enrolment AND
    withdrawn from at least one.

    The two need not be the same course. 37 students qualify.

    *Return: student_id, name*

22. **Assessment kinds by term** (Q333)

    One row per term, with the number of its assessments of each kind
    side by side as columns.

    All six terms appear, and the four columns together account for
    every assessment.

    *Return: term_id, name, essay, exam, project, practical*

## 5 - Window functions (5)

A calculation that sees a set of rows around each row without collapsing
them. PARTITION BY says which rows it may see, ORDER BY orders them inside
that set. Five questions, each isolating one part.

23. **Month on month** (Q334)

    One row per calendar month in which any enrolment was made: the
    month as 'YYYY-MM', how many were made, and the change from the
    month before.

    The earliest month has nothing before it, so its change is NULL --
    leave it NULL rather than turning it into 0. 14 months.

    *Return: month, enrolments, change*

24. **Enrolments so far** (Q335)

    One row per term, in term order: the term name, how many enrolments
    were made on its sections, and the running total of enrolments up to
    and including that term.

    The running total on the last term equals every enrolment in the
    table. All six terms appear.

    *Return: term_id, name, enrolments, running_total*

25. **Share of the billing by status** (Q336)

    One row per payment status: the status, the total amount billed
    under it, and that total as a percentage of everything billed.

    Four statuses, and the four percentages add up to 100.

    *Return: status, billed, pct_of_total*

26. **Each student's first enrolment** (Q337)

    For every student who has ever enrolled, their earliest enrolment by
    date. One row per student -- students who never enrolled do not
    appear, so 51 rows.

    Break ties on date by the lower enrolment_id, so each student's
    first is unambiguous.

    *Return: student_id, enrolment_id, enrolled_on*

27. **Top of each campus, ties and all** (Q338)

    The highest mark achieved by students at each campus, and who got
    it. Only graded enrolments count.

    Every campus has students tied on its top mark, so the answer is 8
    rows across 4 campuses, not 4.

    *Return: campus_id, student_id, name, grade*

## 6 - Grain and correlation (3)

The three that need most care: a subquery that must run per row, two child
tables that multiply when joined together, and an aggregate condition that
only HAVING can express.

28. **Paid above their own department's average** (Q339)

    Every instructor on a higher hourly_rate than the average for THEIR
    OWN department -- not higher than the average across the whole
    college.

    Seven qualify. Be careful: the college-wide version also returns
    seven, so a row count will not tell you which one you wrote.

    *Return: instructor_id, name, department_id, hourly_rate*

29. **Enrolments and payments per student** (Q340)

    One row per student: how many enrolments they have made, and how
    many payments have been billed to them.

    The two are independent -- a student can have many of one and none
    of the other. A student with none of something shows 0, not NULL.
    All 60 students appear.

    *Return: student_id, enrolments, payments*

30. **Sections whose marking does not add up** (Q341)

    An assessment's weight is its share of the section's final mark, so
    a section's weights should total 1. Find the sections where they do
    not.

    Round the total to 2 decimals before comparing, or floating-point
    noise will report almost every section. 20 of the 74 sections that
    have assessments are wrong.

    *Return: section_id, total_weight*

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

Keep the rule for portability, and reach for a CTE when you want a real column
to filter or group by -- which is also how the top-N-per-group questions have to
be written, since a window function cannot appear in `WHERE` on any engine.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
311 retired ones. New questions must not repeat anything in that ledger.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
