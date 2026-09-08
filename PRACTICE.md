# SQL practice exercises

Thirty questions on the college schema, re-seeded and larger again: **83,000
enrolments** across 964 sections. Same tables -- see [schema.sql](schema.sql).

Harder than the last set in two different ways.

**The first 24** keep the shape -- one concept each, the prompt states the grain
-- but the SQL is longer and the traps are subtler. Several need two CTEs where
one would have done, and several traps now return a *plausible* answer rather
than an obviously broken one.

**The efficiency stage is where the difficulty really moves.** Last time the fast
form was the obvious form: stop wrapping the column in a function and you were
done. These six are the opposite -- the naive query is the readable one, and the
fix is something you would not guess:

| # | The fix |
|---|---|
| 25 | **add** a predicate that filters nothing, to unlock a composite index |
| 26 | change which **columns you mention**, to keep the index covering |
| 27 | reorder an `ORDER BY` to match the index's own column order |
| 28 | group by the bare column so the index can supply the grouping |
| 29 | prefer a correlated `NOT EXISTS` **over** a `LEFT JOIN` anti-join |
| 30 | order by the driving table, not the joined one |

Question 29 is the one to sit with: it runs directly against the usual advice
that a correlated subquery should be rewritten as a join. Here the join builds
83,000 rows to find 572, and the subquery asks one indexed question per student.

Each prompt still names the plan to aim for, so you know when you have arrived.
What it does not say is how. **Press F6** for the plan and timing.

| Stage | Questions |
|---|---|
| 1 - Warm-up | 1-4 |
| 2 - First joins | 5-9 |
| 3 - Recursion | 10-13 |
| 4 - Dates, sets and pivots | 14-18 |
| 5 - Window functions | 19-22 |
| 6 - Grain and correlation | 23-24 |
| 7 - Query efficiency | 25-30 |

## Things the data does on purpose

- **Nine indexes**, several reachable only if a query is restructured. The two
  composites -- `students(campus_id, funding_band)` and
  `payments(status, billed_on)` -- are usable from the LEFT only, which is what
  questions 25 and 27 turn on. `students(name COLLATE NOCASE)` needs the
  collation because `LIKE` is case-insensitive and a BINARY index cannot serve
  it.
- **`grade` is NULL unless the enrolment completed** -- 26,527 of 82,911. Every
  comparison against those returns NULL, so they fall through every `WHEN` and
  land in whatever `ELSE` you wrote.
- **572 students never enrolled**, which is what question 29 counts, and why the
  anti-join has 83,000 rows to discard.
- **`prerequisites` is a graph**, but no course is currently reachable by two
  paths of different lengths -- so `MIN` and `MAX` over hop counts agree, and
  question 11 asks you to know which you meant rather than punishing you.
- **Dates are TEXT.** Subtracting coerces to years and returns 0.

## 1 - Warm-up (4)

Four questions on a single table. Same idea as before, harder execution --
a pivot with a NULL column, two aggregate conditions relating to each other,
a CASE whose ELSE catches what you did not intend.

1. **Funding mix by campus** (Q372)

   One row per campus id, with the number of its students on each
   funding band as columns -- and a fourth column for those with no
   band recorded.

   The four columns must account for every student at that campus. One
   table, no joins.

   *Return: campus_id, self, grant, sponsor, unrecorded*

2. **Busy days that were not all withdrawals** (Q373)

   Dates on which more than 400 enrolments were made, where fewer than
   a fifth of them were withdrawn.

   Both conditions are about the day as a whole, not about individual
   rows. One table, no joins.

   *Return: enrolled_on, enrolments, withdrawn*

3. **Grade bands, including the ungraded** (Q374)

   Put every enrolment into one of four bands and count them:

       'distinction' grade 70 or more
       'pass'        grade 40 to 69
       'fail'        grade below 40
       'ungraded'    no grade recorded

   All 82,911 enrolments land in exactly one band.

   *Return: band, enrolments*

4. **Marks by band, and how many carry one** (Q375)

   One row per enrolment status: how many enrolments have it, how many
   carry a grade, the average grade, and the average computed over ALL
   of that status's rows treating a missing grade as zero.

   Two of the statuses have no grades at all, so their true average is
   NULL while their zero-filled average is 0.

   *Return: status, enrolments, graded, avg_grade, avg_with_zeros*

## 2 - First joins (5)

Two or three tables. The recurring theme is conditions that cannot be
expressed as a filter on a row, because they are about a whole set of rows.

5. **Online teaching per course** (Q376)

   One row for every course: id, code, and how many of its sections are
   delivered ONLINE.

   Six courses have none. They must appear with 0, so all 34 courses
   come back.

   *Return: course_id, code, online_sections*

6. **Straight to level 4** (Q377)

   Students who have enrolled on a LEVEL-4 course but never on a
   level-1 one.

   Courses sit under sections, which carry the enrolment. Exactly one
   student qualifies out of the 2,687 who have taken anything at level
   4.

   *Return: student_id, name*

7. **Courses that sit alongside each other** (Q378)

   Pairs of courses in the same department at the same level, where the
   two carry a DIFFERENT number of credits.

   Each pair once, ordered so code_a belongs to the lower course_id.

   *Return: department_id, code_a, code_b*

8. **Courses nobody has scheduled** (Q379)

   Every course that has never had a section scheduled.

   Write it as an outer join that keeps the non-matches, rather than
   with NOT IN. There are 6.

   *Return: course_id, code*

9. **Instructors who mentor nobody** (Q380)

   Every instructor who is nobody's mentor. Twelve of the sixteen
   qualify.

   mentor_id contains a NULL, for the instructor at the top, which is
   what makes the obvious answer wrong.

   *Return: instructor_id, name*

## 3 - Recursion (4)

Now carrying values through the walk, not just collecting ids: a depth
counter, a hop count, and one query that recurses and then filters what it
found.

10. **Everyone under Margaret Ashworth, with their depth** (Q381)

    Everyone below Margaret Ashworth in the mentoring tree, with how
    many levels below her they sit.

    Her direct mentees are 1, their mentees 2, and so on. Fifteen rows;
    Margaret herself is not among them.

    *Return: instructor_id, name, depth*

11. **What Machine Learning needs, and how far back** (Q382)

    Every course CMP401 depends on, at any depth, with the FEWEST hops
    from CMP401 to that course.

    A course reachable both directly and through another counts as 1.
    CMP401 itself is not in the answer.

    *Return: code, hops*

12. **What is blocked by Programming Foundations** (Q383)

    Every course that requires CMP101 'Programming Foundations',
    directly or indirectly.

    Travel the other way along prerequisites from question 11.

    *Return: code, title*

13. **Courses that depend on nothing** (Q384)

    Starting from CMP401 and walking its prerequisites at any depth,
    which of the courses reached have NO prerequisites of their own --
    the foundations of its dependency tree.

    CMP401 itself is excluded.

    *Return: code, title*

## 4 - Dates, sets and pivots (5)

Date arithmetic inside an aggregate, two levels of date extraction in one
query, and integer division quietly destroying a set of percentages.

14. **How much of each term had passed** (Q385)

    One row per term: its name, its length in whole days, and the
    average number of whole days INTO the term at which its enrolments
    were made.

    An enrolment made before the term starts counts as a negative number
    of days. All six terms appear.

    *Return: term_id, name, term_days, avg_days_in*

15. **The busiest month of each academic year** (Q386)

    For each academic year -- taken as the calendar year of the
    enrolment date -- the single month with the most enrolments.

    Months are 'YYYY-MM'. One row per year present in the data.

    *Return: year, month, enrolments*

16. **Billed in a month nobody enrolled** (Q387)

    Months in which at least one payment was billed but NO enrolment was
    made. Months are 'YYYY-MM'. Nine qualify.

    *Return: month*

17. **Books that changed their status between levels** (Q388)

    Textbooks that are marked REQUIRED on at least one course and merely
    recommended (required = 0) on at least one other.

    *Return: book_id, title*

18. **Status mix by term, as percentages** (Q389)

    One row per term: the term name, and the percentage of its
    enrolments in each of the three statuses.

    The three percentages on each row add up to 100. All six terms
    appear.

    *Return: term_id, name, pct_completed, pct_active, pct_withdrawn*

## 5 - Window functions (4)

Two windows over the same column doing opposite jobs; a percentage change
that must divide by the previous value; the default frame versus a real one.

19. **Term on term, in percentage terms** (Q390)

    One row per term in term order: the name, its enrolments, and the
    percentage change from the term before.

    The first term has nothing before it, so its change is NULL. A fall
    is negative.

    *Return: term_id, name, enrolments, pct_change*

20. **Cumulative share of enrolments** (Q391)

    One row per term in term order: the name, its enrolments, the
    running total up to and including it, and that running total as a
    percentage of all enrolments.

    The last term's percentage is 100.

    *Return: term_id, name, enrolments, running_total, pct_so_far*

21. **The two biggest courses in each faculty** (Q392)

    For each faculty, the two courses with the most enrolments, with
    their rank.

    If two courses tie for second, both appear. Rank within the faculty,
    highest first.

    *Return: faculty, code, enrolments, rank*

22. **Three-term rolling average** (Q393)

    One row per term in order: the name, its enrolments, and the average
    over that term and the two before it.

    The first term averages just itself, the second two terms, and every
    term after that three.

    *Return: term_id, name, enrolments, rolling_avg*

## 6 - Grain and correlation (2)

A CTE referenced twice so a row can be compared to its own group, and three
measures at three grains where COUNT(DISTINCT) rescues one column and hides
that the other two are wrong.

23. **Courses busier than their department's average** (Q394)

    Courses whose enrolment count is above the average enrolment count
    of the courses in THEIR OWN department.

    Only courses with at least one enrolment take part, on both sides of
    the comparison.

    *Return: code, department_id, enrolments*

24. **Three measures per term** (Q395)

    One row per term: how many sections it has, how many enrolments were
    made on them, and how many assessments those sections set.

    Sections is the parent; the other two are independent children of
    it. All six terms appear.

    *Return: term_id, sections, enrolments, assessments*

## 7 - Query efficiency (6)

**Graded on the query PLAN.** Unlike the last set, the fast form is NOT the
obvious form in any of these -- the naive query is the readable one and the
fix is something you would not guess. Each prompt names the plan to aim for.
It does not tell you how to get there. Press F6 and work backwards.

25. **Make the query longer to make it faster** (Q396)

    How many students are on the 'grant' funding band.

    There is an index on students(campus_id, funding_band). The obvious
    query cannot use it. Your plan must say SEARCH, not SCAN -- and the
    fix is to ADD something to the WHERE clause, not to change what is
    there.

    *Plan must not contain: `SCAN`*

    *Return: one row, one column: the count*

26. **Keep the index covering** (Q397)

    Every withdrawn enrolment's status and grade.

    There is an index on enrolments(status, grade). Return ONLY what
    that index already holds and SQLite never has to open the table at
    all. Your plan must say COVERING INDEX.

    *Plan must contain: `COVERING INDEX`*

    *Return: status, grade*

27. **Sort in the order the index is already in** (Q398)

    The first 20 payments ordered by status and then by billing date,
    returning just the id.

    There is an index on payments(status, billed_on). Order by those two
    columns in the order the index holds them and no sort is needed at
    all. Your plan must NOT contain 'TEMP B-TREE'.

    *Plan must not contain: `TEMP B-TREE`*

    *Return: payment_id*

28. **Group in the order the index is already in** (Q399)

    How many payments were billed on each distinct date.

    GROUP BY normally sorts to bring each group together -- but
    payments(billed_on) is indexed, and an index is already grouped.
    Your plan must NOT contain 'TEMP B-TREE'.

    *Plan must not contain: `TEMP B-TREE`*

    *Return: billed_on, payments*

29. **The anti-join that should not be a join** (Q400)

    How many students have never enrolled on anything.

    The LEFT JOIN ... IS NULL form works and is three times slower,
    because it joins 83,000 rows to throw nearly all of them away. Write
    the form that asks the question per student instead: your plan must
    contain 'CORRELATED SCALAR SUBQUERY'.

    *Plan must contain: `CORRELATED SCALAR SUBQUERY`*

    *Return: one row, one column: the count*

30. **Order by the table you are driving** (Q401)

    The 20 earliest enrolments that belong to a student, returning the
    enrolment id.

    Every enrolment has a student, so the join changes nothing about
    WHICH rows come back -- but ordering by a column of the joined table
    forces a sort of all 83,000. Order by the driving table's indexed
    column instead. Your plan must NOT contain 'TEMP B-TREE'.

    *Plan must not contain: `TEMP B-TREE`*

    *Return: enrolment_id*
## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a SELECT alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
371 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
