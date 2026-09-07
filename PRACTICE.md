# SQL practice exercises

Thirty questions on the college schema, re-seeded and **scaled up**. Same
tables -- see [schema.sql](schema.sql) -- but two orders of magnitude more rows:

| | before | now |
|---|---|---|
| students | 60 | 4,000 |
| sections | 85 | 774 |
| enrolments | 550 | 67,000 |
| payments | 129 | 7,800 |

**The scale is the point.** At 550 rows every query returns instantly however it
is written, so there is nothing to learn about cost. At 67,000 a table scan
takes 10ms where an index seek takes 0.8ms, and a blocked index on a join costs
150x. You can feel the difference, which means it can be taught.

| Stage | Questions | What it is |
|---|---|---|
| 1 - Warm-up | 1-4 | one table, no joins |
| 2 - First joins | 5-9 | two tables, outer joins, EXISTS |
| 3 - Recursion | 10-13 | the gentlest in the set |
| 4 - Dates, sets and pivots | 14-18 | |
| 5 - Window functions | 19-22 | |
| 6 - Grain and correlation | 23-24 | |
| 7 - Query efficiency | 25-30 | **new** |

Because the tables are now large, the earlier questions aggregate to a dimension
-- per campus, per term, per faculty -- rather than listing rows. "Top mark per
campus" would return 707 rows at this scale and teach nothing.

## The efficiency stage, and how it is graded

Those six **cannot** be graded on their result: the slow form and the fast form
return exactly the same rows. That is precisely what makes the mistake worth
making, and why nothing in the first six stages could have caught it.

So they carry assertions about the **query plan**, checked with
`EXPLAIN QUERY PLAN`. A right answer has to be correct *and* arrive by the
intended route. A correct result reached by scanning 67,000 rows is marked
wrong, and the plan is shown so you can see why:

```
Right rows, but the query plan contains 'SCAN', which this question asks you
to avoid.
  Plan: SCAN enrolments USING COVERING INDEX idx_enrol_date
```

**Press F6** (or the "Explain plan" button) on any query, at any time, to see its
plan and how long it took. Three words carry most of the meaning:

| | |
|---|---|
| `SCAN` | every row of the table is read |
| `SEARCH` | an index is used to jump straight to the matching rows |
| `TEMP B-TREE` | the rows had to be sorted or grouped on the fly |

**One rule explains five of the six questions:** an index is on the COLUMN, not
on expressions of it. `strftime('%Y', enrolled_on)`, `substr(name, 1, 5)`,
`enrolled_on || ''`, `upper(name)` -- each of these is a different column as far
as the index is concerned, so SQLite must compute it for every row to find out
what matches, which is exactly the scan you were trying to avoid. The fix is
always the same shape: test the **bare column**, usually as a range.

## Things the data does on purpose

- **Two indexes exist so the efficiency questions have something to hit or
  miss.** `students(name COLLATE NOCASE)` -- the collation is required, because
  `LIKE` is case-insensitive by default and a plain index cannot serve it. And
  `enrolments(status, grade)`, a composite, usable from the LEFT only: a filter
  on `status` seeks, a filter on `grade` alone must scan.
- **`prerequisites` is a graph, not a tree.** 29 edges over 34 courses; the
  deepest chain runs 3 hops, and some courses are reachable by two routes --
  which is why `UNION` vs `UNION ALL` changes the answer in question 13.
- **A three-level mentoring tree.** The root mentors 3 people directly but 15
  sit below them, so a single join is visibly short.
- **`NOT IN` is a trap here.** `instructors.mentor_id` is NULL at the top and
  `sections.instructor_id` is NULL for unstaffed sections.
- **`grade` is NULL unless the enrolment completed**, so `AVG` and
  `SUM/COUNT(*)` disagree by about a third.
- **Dates are TEXT.** `ends_on - starts_on` coerces to numbers and returns
  nonsense. Use `julianday()`.
- **Deliberate gaps**: 5 courses never scheduled, 6 with no online section.

## 1 - Warm-up (4)

Four questions on a single table, no joins. Each isolates one
behaviour of GROUP BY, CASE or NULL.

1. **Funding recorded, and not** (Q342)

   One row per campus id: how many students it has, and how many of
   them have a funding band recorded.

   Some students have no funding_band, so the two counts differ at
   every campus. One table, no joins.

   *Return: campus_id, students, with_band*

2. **Which enrolment statuses were common in 2026** (Q343)

   Counting only enrolments made on or after 2026-01-01, one row per
   status, keeping the statuses with at least 2,500 of them.

   Two of the three statuses clear the bar. One table, no joins.

   *Return: status, enrolments*

3. **Sections by size** (Q344)

   Put every section into one of three bands by capacity and count
   them:

       'large'  120 or more
       'medium' 60 up to but not including 120
       'small'  everything else

   All 774 sections land in exactly one band.

   *Return: band, sections*

4. **Average mark, where there is one** (Q345)

   One row per campus: how many enrolments its students made, how many
   of those carry a grade, and the average of the grades that exist.

   Only completed enrolments are graded, so the average must be over
   the graded ones alone -- not over everyone enrolled.

   *Return: campus_id, enrolments, graded, avg_grade*

## 2 - First joins (5)

Two tables at a time. Three of the five hinge on the rows that DON'T
match -- the course nobody scheduled, the course with no online section, the
instructor nobody reports to.

5. **Every course, scheduled or not** (Q346)

   One row for every course in the catalogue: its id, code, and how
   many sections have ever been scheduled for it.

   Five courses have never been scheduled. They must appear with 0, so
   all 34 courses come back.

   *Return: course_id, code, sections*

6. **Online teaching per course** (Q347)

   One row for every course: id, code, and how many of its sections are
   delivered ONLINE.

   Six courses have none -- five were never scheduled at all, and one
   runs only in person. They must appear with 0, so all 34 courses come
   back.

   *Return: course_id, code, online_sections*

7. **Courses that sit alongside each other** (Q348)

   Pairs of courses in the same department at the same level.

   Each pair once, not twice, and no course paired with itself. Order
   each pair so that code_a belongs to the LOWER course_id. There are 4
   pairs.

   *Return: department_id, code_a, code_b*

8. **Courses nobody has scheduled** (Q349)

   Every course that has never had a section scheduled.

   Write it as an outer join that keeps the non-matches, rather than
   with NOT IN. There are 5 such courses.

   *Return: course_id, code*

9. **Instructors who mentor nobody** (Q350)

   Every instructor who is nobody's mentor. Twelve of the sixteen
   qualify.

   Watch out: one instructor -- the one at the top -- has no mentor
   themselves, so mentor_id contains a NULL. That is what makes the
   obvious answer wrong.

   *Return: instructor_id, name*

## 3 - Recursion (4)

The gentlest questions in the set: an anchor that is one obvious row and a
step that is one join back to the CTE. Four shapes -- down a tree, down a
straight chain, up a branching one, and one whose anchor is its own answer.

10. **Everyone under Margaret Ashworth** (Q351)

    Margaret Ashworth is the one instructor with no mentor. List
    everyone below her: the people she mentors, the people they mentor,
    and so on.

    Fifteen rows -- everyone except Margaret. Only three are her direct
    mentees, which is why a single join is not enough.

    *Return: instructor_id, name*

11. **What Audit and Assurance needs** (Q352)

    Course ACC301 'Audit and Assurance' has a prerequisite, and that has
    one of its own. List every course ACC301 depends on, at any depth.

    This chain is a straight line -- exactly one prerequisite at each
    hop -- so it is two rows. ACC301 itself is not in the answer.

    *Return: code, title*

12. **What is blocked by Programming Foundations** (Q353)

    The other way round. Every course that requires CMP101 'Programming
    Foundations', directly or indirectly.

    Five courses, and the chain branches: three require it directly, and
    the rest come through those.

    *Return: code, title*

13. **A full study plan for Machine Learning** (Q354)

    Everything a student must pass to finish CMP401 'Machine Learning'
    -- every course it depends on at any depth, AND CMP401 itself.

    Seven courses. This one branches, and some courses are reachable by
    two different routes but must still appear once.

    *Return: code, title*

## 4 - Dates, sets and pivots (5)

Dates are TEXT in SQLite, and set operators stack results rather than
joining them.

14. **How long each term runs** (Q355)

    One row per term: its name, and how many whole days it lasts from
    starts_on to ends_on.

    All six terms appear, and every length is between 70 and 90 days.

    *Return: term_id, name, days*

15. **Enrolments by month** (Q356)

    One row per calendar month in which any enrolment was made: the
    month as 'YYYY-MM', and how many were made in it.

    The data spans two academic years, so the same month name recurs and
    the two must not be added together. There are 14 such months.

    *Return: month, enrolments*

16. **Billed in a month nobody enrolled** (Q357)

    Months in which at least one payment was billed but NO enrolment was
    made. Months are 'YYYY-MM'.

    Billing runs all year while enrolment clusters around the terms.
    Nine months qualify.

    *Return: month*

17. **Required reading on a first-year course** (Q358)

    Textbooks that are BOTH marked required (required = 1) on some
    course AND appear on the reading list of a level-1 course.

    The two need not be the same course. Eleven books qualify.

    *Return: book_id, title*

18. **Enrolment status by term** (Q359)

    One row per term, with the number of its enrolments in each of the
    three statuses side by side as columns.

    All six terms appear, and the three columns together account for
    every enrolment.

    *Return: term_id, name, completed, active, withdrawn*

## 5 - Window functions (4)

A calculation that sees a set of rows around each row without collapsing
them. PARTITION BY says which rows it may see, ORDER BY orders them inside
that set.

19. **Term on term** (Q360)

    One row per term, in term order: the term name, how many enrolments
    were made on its sections, and the change from the term before.

    The first term has nothing before it, so its change is NULL -- leave
    it NULL. All six terms appear.

    *Return: term_id, name, enrolments, change*

20. **Enrolments so far** (Q361)

    One row per term, in term order: the term name, how many enrolments
    were made on its sections, and the running total up to and including
    that term.

    The running total on the last term equals every enrolment in the
    table.

    *Return: term_id, name, enrolments, running_total*

21. **Share of the enrolments by faculty** (Q362)

    One row per faculty: the faculty, how many enrolments its
    departments' courses attracted, and that count as a percentage of
    all enrolments.

    Four faculties, and the four percentages add up to 100.

    *Return: faculty, enrolments, pct_of_total*

22. **The two biggest courses in each faculty** (Q363)

    For each faculty, the two courses with the most enrolments.

    Rank within the faculty by enrolment count, highest first, and keep
    ranks 1 and 2. Four faculties, so 8 rows.

    *Return: faculty, code, enrolments*

## 6 - Grain and correlation (2)

A subquery that must run per row, and two child tables that multiply when
joined together.

23. **Paid above their own department's average** (Q364)

    Every instructor on a higher hourly_rate than the average for THEIR
    OWN department -- not higher than the college average.

    Seven qualify. Be careful: the college-wide version also returns
    seven, so a row count will not tell you which one you wrote.

    *Return: instructor_id, name, department_id, hourly_rate*

24. **Enrolments and assessments per term** (Q365)

    One row per term: how many enrolments were made on its sections, and
    how many assessments those sections set.

    Both hang off sections, but they are independent of each other. All
    six terms appear.

    *Return: term_id, enrolments, assessments*

## 7 - Query efficiency (6)

**Graded on the query PLAN, not just the rows.** Every trap in this stage
returns exactly the right answer and is rejected for how it got there --
because the slow way and the fast way return identical rows, which is what
makes the mistake worth making. Press F6 on anything to see its plan and
timing.

25. **A year of enrolments, without scanning the table** (Q366)

    How many enrolments were made during the 2025 calendar year.

    `enrolments.enrolled_on` is indexed. Write this so the index is USED
    -- your plan must say SEARCH, not SCAN. Press F6 to see it.

    *Plan must not contain: `SCAN`*

    *Return: one row, one column: the count*

26. **Names beginning with Sofia** (Q367)

    Every student whose name starts with 'Sofia'. There are 156.

    `students.name` is indexed. Write this so the plan says SEARCH, not
    SCAN.

    *Plan must not contain: `SCAN`*

    *Return: student_id, name*

27. **Ten earliest enrolments, without sorting 67,000 rows** (Q368)

    The ten earliest enrolments by date, earliest first. Break ties by
    the lower enrolment_id.

    `enrolled_on` is indexed, and an index is already in order -- so
    this should not need a sort at all. Your plan must NOT contain 'TEMP
    B-TREE'.

    *Plan must not contain: `TEMP B-TREE`*

    *Return: enrolment_id, enrolled_on*

28. **Withdrawals, using the composite index** (Q369)

    How many enrolments have status 'withdrawn'.

    There is an index on enrolments(status, grade) -- status first.
    Write this so it is used: the plan must say SEARCH, not SCAN.

    *Plan must not contain: `SCAN`*

    *Return: one row, one column: the count*

29. **Enrolments per day, without a temporary sort** (Q370)

    How many enrolments were made on each distinct date, over the whole
    data set.

    GROUP BY normally sorts to collect the groups together -- but if you
    group by an INDEXED column it can read them in order instead. Your
    plan must NOT contain 'TEMP B-TREE'.

    *Plan must not contain: `TEMP B-TREE`*

    *Return: enrolled_on, enrolments*

30. **What blocking an index does to a join** (Q371)

    How many enrolments belong to students whose name starts with
    'Sofia'.

    This is question 26's filter, now driving a join against 67,000
    enrolments. Written so the index on students.name is usable, it is
    over a hundred times faster. Your plan must not contain 'SCAN'.

    *Plan must not contain: `SCAN`*

    *Return: one row, one column: the count*
## The one concept with no question here

**Alias scope follows clause order.** Logical order is `FROM` -> `WHERE` ->
`GROUP BY` -> `HAVING` -> window functions -> `SELECT` -> `ORDER BY` ->
`LIMIT`, and a name only exists after the step that creates it. Postgres and
SQL Server reject a SELECT alias in `WHERE`.

There is no graded question because **SQLite will not punish you for it** -- it
happily accepts an alias in `WHERE`. Keep the rule for portability, and reach
for a CTE when you want a real column to filter or group by.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
341 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
