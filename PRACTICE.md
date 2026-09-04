# SQL practice exercises

Thirty questions on the college schema, re-seeded so no answer from the previous
set carries over. **The tables are the same**, so the schema you learned last
time still applies -- see [schema.sql](schema.sql).

**What changed is the order.** The last set was grouped by concept, which put all
four recursion questions at numbers 1-4 -- the hardest mechanism before any
warm-up. This set is graded **easy to hard**, and the stage names are the ramp:

| Stage | Questions | What it is |
|---|---|---|
| 1 - Warm-up | 1-6 | one table, no joins |
| 2 - First joins | 7-12 | two tables, outer joins, EXISTS |
| 3 - Recursion | 13-16 | the gentlest in the set |
| 4 - Dates, sets and pivots | 17-22 | |
| 5 - Window functions | 23-27 | |
| 6 - Grain and correlation | 28-30 | the ones needing most care |

Work them in order and each leans on the one before.

**The recursion questions are all one shape on purpose.** An anchor that is a
single obvious row; a step that is a single join back to the CTE. Nothing else.
What varies between them is only where you start and which way you travel:

1. **up** a mentor chain — `instructors`, one hop at a time
2. **down** a prerequisite chain — a course whose ancestry is a straight line
3. **up** a prerequisite chain — the same table, the other column
4. **down** a branching one — where `UNION` and `UNION ALL` finally differ

If the mechanism didn't land last time, 13 and 14 are the two to sit with. They
are the smallest complete recursive queries this schema can produce.

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

- **`prerequisites` is a graph, not a tree.** 36 edges over 34 courses; 11
  courses require nothing, the deepest chain runs 3 hops, and 11 course pairs
  are reachable by two different paths — which is why `UNION` vs `UNION ALL`
  changes the answer in question 16 but not in 14.
- **A three-level mentoring tree.** One instructor has no mentor, 12 mentor
  nobody. Deep enough that a single self-join cannot reach the bottom, which is
  question 13's whole point.
- **`NOT IN` is a trap here.** `sections.instructor_id` is NULL for 13
  unstaffed sections (6 of them online) and `instructors.mentor_id` is NULL at
  the top, so `x NOT IN (SELECT that_column ...)` returns nothing at all.
- **Enrolment clusters around terms; billing does not.** 22 months have a
  payment billed and only 14 have an enrolment: 9 months bill without enrolling,
  1 enrols without billing — which is what `EXCEPT` is for.
- **`grade` is NULL unless the enrolment completed.** 292 of 432 are graded; the
  other 140 are active or withdrawn. `AVG` skips them, `SUM/COUNT(*)` does not.
- **Dates are TEXT.** `paid_on - billed_on` does not error — it coerces to
  numbers and returns nonsense. Use `julianday()` for arithmetic; `<` and `>` on
  ISO dates are fine as strings.
- **17 distinct months** of assessment deadlines across two academic years, so
  `strftime('%m', ...)` collapses two Novembers into one bucket.
- **Sections have two independent children.** 9 have no enrolments and 6 have no
  assessments — different sets, so joining both fans out rather than filtering.
- **Payment `status` is UPPERCASE** (`PAID`, `DUE`, `LATE`, `WAIVED`) while
  enrolment `status` and section `delivery` are lowercase. Deliberate.
- **30 distinct list prices and 23 distinct copy counts**, so
  `SUM(copies) * AVG(price)` and `SUM(copies * price)` genuinely disagree.
- **Deliberate gaps**: 7 courses never scheduled, 9 students never enrolled, 6
  textbooks on no reading list.
- **Nullable on purpose**: `grade` (140), `paid_on` (55), `instructor_id` on
  sections (13), `funding_band` (12), `copies_held` (9), `pay_grade` (3),
  `pages` (3), `mentor_id` (1).

## 1 - Warm-up (6)

Six questions on a single table, no joins at all. If you are rusty, start
here -- each one isolates a single behaviour of GROUP BY, CASE or NULL.

1. **Funding recorded, and not** (Q282)

   One row per campus id: how many students it has, and how many of
   them have a funding band recorded.

   Twelve students company-wide have no funding_band, so the two counts
   differ. One table, no joins.

   *Return: campus_id, students, with_band*

2. **Which payment statuses were common in 2025** (Q283)

   Counting only payments billed during the 2025 calendar year, one row
   per status, keeping the statuses with at least 10 of them.

   Three of the four statuses clear the bar. One table, no joins.

   *Return: status, payments*

3. **Textbooks by price band** (Q284)

   Put every textbook into one of three bands by list_price and count
   them:

       'premium'  100 or more
       'standard' 50 up to but not including 100
       'budget'   everything else

   All 30 textbooks land in exactly one band.

   *Return: band, textbooks*

4. **Settled, waived, or still owing** (Q285)

   Classify every payment into one of three states and count them:

       'settled' if paid_on has a date
       'waived'  if it has no paid_on and status is WAIVED
       'owing'   otherwise

   All 122 payments land in exactly one state.

   *Return: state, payments*

5. **Everyone not funding themselves** (Q286)

   Count students by funding band, excluding the self-funded, and
   counting the ones with NO band recorded as 'none'.

   46 of the 60 students are not self-funded -- twelve of them because
   they have no band at all.

   *Return: band, students  ('grant', 'sponsor' or 'none')*

6. **Average page count, where it is known** (Q287)

   One row per publisher: how many textbooks they have, how many of
   those record a page count, and the average of the page counts that
   exist.

   Three publishers have a book with no page count. The average must be
   over the recorded ones only. One table, no joins.

   *Return: publisher, books, with_pages, avg_pages*

## 2 - First joins (6)

Two tables at a time. Four of the six hinge on the rows that DON'T match --
the unscheduled course, the instructor teaching no online sections, the
textbook nobody assigns.

7. **Every course, scheduled or not** (Q288)

   One row for every course in the catalogue: its id, code, and how
   many sections have ever been scheduled for it.

   Seven courses have never been scheduled. They must appear with 0, so
   all 34 courses come back.

   *Return: course_id, code, sections*

8. **Online teaching per instructor** (Q289)

   One row for every instructor: id, name, and how many sections they
   teach that are delivered ONLINE.

   Five instructors teach none. They must appear with 0, so all 16
   instructors come back.

   *Return: instructor_id, name, online_sections*

9. **Courses that sit alongside each other** (Q290)

   Pairs of courses in the same department at the same level.

   Each pair once, not twice, and no course paired with itself. Order
   each pair so that code_a belongs to the LOWER course_id. There are 4
   pairs.

   *Return: department_id, code_a, code_b*

10. **Textbooks nobody assigns** (Q291)

    Every textbook that appears on no course reading list at all.

    Write it as an outer join that keeps the non-matches, rather than
    with NOT IN. There are 6 such books.

    *Return: book_id, title*

11. **Students who have reached level 4** (Q292)

    Every student who has ever enrolled on a level-4 course.

    Courses sit under sections and sections carry the enrolment. One row
    per student, however many level-4 courses they took -- and some took
    two. 25 students qualify.

    *Return: student_id, name*

12. **Never taught online** (Q293)

    Every instructor who has never taught a section delivered ONLINE.
    Five of the sixteen qualify.

    Watch out: six online sections have no instructor assigned at all,
    which is what makes the obvious answer wrong.

    *Return: instructor_id, name*

## 3 - Recursion (4)

Deliberately the gentlest questions in the set, and all four are the same
shape: an anchor that is ONE obvious row, and a step that is ONE join back
to the CTE. No depth counters, no generated series, no labels carried down
a tree. Only the direction of travel and the table change.

13. **Anil Chaudhary's line of mentors** (Q294)

    Anil Chaudhary, then their mentor, then that person's mentor, and so
    on up to the instructor who has no mentor.

    Three rows: Anil themselves, then two above. Start with Anil in the
    anchor and follow mentor_id upward one hop at a time.

    *Return: instructor_id, name*

14. **What Interaction Design needs, all the way down** (Q295)

    Course DES301 'Interaction Design' has a prerequisite, and that has
    one of its own. List every course DES301 depends on, at any depth.

    This chain is a straight line -- exactly one prerequisite at each
    hop -- so it is two rows. DES301 itself is not in the answer.

    *Return: code, title*

15. **What is blocked by Visual Communication** (Q296)

    The other way round. Every course that requires DES101 'Visual
    Communication', directly or indirectly -- that is, every course a
    student could not take until they had passed it.

    Two courses. Same table and same shape as question 14, but you
    travel along the other column.

    *Return: code, title*

16. **What Machine Learning needs, all the way down** (Q297)

    The same question as 14, but on a course whose prerequisites branch:
    everything CMP401 'Machine Learning' depends on, at any depth.

    Five courses. Three are direct, and the rest are reached through
    them -- one course is reachable by TWO different paths and must
    still appear once.

    *Return: code, title*

## 4 - Dates, sets and pivots (6)

Dates are TEXT in SQLite, and set operators stack results rather than
joining them. Six questions on doing both correctly.

17. **The five slowest payments to settle** (Q298)

    The five settled payments that took the longest from being billed to
    being paid, longest first.

    Days must be a whole number. Break ties on days by payment_id
    ascending, so the five are unambiguous.

    *Return: payment_id, billed_on, paid_on, days*

18. **Assessment deadlines by month** (Q299)

    One row per calendar month in which any assessment falls due: the
    month as 'YYYY-MM', and how many are due in it.

    The data spans two academic years, so the same month name recurs and
    the two must not be added together. There are 17 such months.

    *Return: month, assessments*

19. **Enrolled before the term began** (Q300)

    How many enrolments were made BEFORE their term's start date, broken
    down by term.

    The enrolment date is on the enrolment; the start date is on the
    term, reached through the section. All six terms have some.

    *Return: term_id, name, early_enrolments*

20. **Billed in a month nobody enrolled** (Q301)

    Months in which at least one payment was billed but NO enrolment was
    made. Months are 'YYYY-MM'.

    Billing runs all year while enrolment clusters around the terms, so
    this catches the quiet months. Nine qualify.

    *Return: month*

21. **Required reading on a first-year course** (Q302)

    Textbooks that are BOTH marked required (required = 1) on some
    course AND appear on the reading list of a level-1 course.

    The two need not be the same course: a book required on a level-3
    course and merely recommended on a level-1 one still counts. Ten
    books qualify.

    *Return: book_id, title*

22. **Enrolment status by term** (Q303)

    One row per term, with the number of its enrolments in each of the
    three statuses side by side as columns.

    All six terms appear, and the three columns together account for
    every enrolment.

    *Return: term_id, name, completed, active, withdrawn*

## 5 - Window functions (5)

A calculation that sees a set of rows around each row without collapsing
them. PARTITION BY says which rows it may see, ORDER BY orders them inside
that set. Five questions, each isolating one part.

23. **Term on term** (Q304)

    One row per term, in term order: the term name, how many enrolments
    were made on its sections, and the change from the term before.

    The first term has nothing before it, so its change is NULL -- leave
    it NULL rather than turning it into 0. All six terms appear.

    *Return: term_id, name, enrolments, change*

24. **Billed so far** (Q305)

    One row per calendar month in which anything was billed: the month
    as 'YYYY-MM', the amount billed in it, and the running total of
    everything billed up to and including that month.

    The running total on the last month equals the total of every
    payment in the table. 22 months.

    *Return: month, month_total, running_total*

25. **Share of the enrolments by faculty** (Q306)

    One row per faculty: the faculty, how many enrolments its
    departments' courses attracted, and that count as a percentage of
    all enrolments.

    Four faculties, and the four percentages add up to 100.

    *Return: faculty, enrolments, pct_of_total*

26. **The most recent run of each course** (Q307)

    For every course that has ever been scheduled, its latest section by
    term. One row per course -- courses never scheduled do not appear,
    so 27 rows.

    No course runs twice in the same term, so 'latest' is never a tie.

    *Return: course_id, section_id, term_id*

27. **Top of each programme, ties and all** (Q308)

    The highest mark achieved in each programme, and who got it. Only
    graded enrolments count.

    Two programmes have two students tied on the top mark. Both must
    appear, so the answer is 11 rows across 9 programmes.

    *Return: programme, student_id, name, grade*

## 6 - Grain and correlation (3)

The three that need the most care: a subquery that must run per row, two
child tables that multiply when joined together, and arithmetic that has
to happen inside the aggregate rather than outside it.

28. **Bigger than its own department's average** (Q309)

    Every course worth more credits than the average for ITS OWN
    department -- not more than the average across the whole catalogue.

    One row per course. Twelve qualify.

    *Return: course_id, code, department_id, credits*

29. **Students and assessments on each section** (Q310)

    One row per section: how many students are enrolled on it, and how
    many assessments it has.

    The two are independent -- a section can have many of one and none
    of the other. A section with none of something shows 0, not NULL.
    All 70 sections appear.

    *Return: section_id, students, assessments*

30. **What the library holds, by faculty** (Q311)

    One row per faculty, with the total value of the library copies held
    on its courses' reading lists.

    Each course_books row is worth copies_held * list_price. Rows with
    no copies_held recorded contribute nothing. Every line must be
    priced on its own copies and its own book.

    *Return: faculty, value*

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
281 retired ones. New questions must not repeat anything in that ledger.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
