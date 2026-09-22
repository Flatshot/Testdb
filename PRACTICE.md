# SQL practice exercises

Thirty questions on the railway schema, re-seeded so no answer from the previous
set carries over. This set changes the buckets: after three warm-ups, sixteen
questions cover four areas no earlier set touched -- **JSON**, **hierarchies**,
**NULL logic and subquery forms**, and **distributions** -- then three familiar
shapes, and **the eight writable questions** on constructs none of the four
earlier writable stages used.

| Stage | Questions |
|---|---|
| 1 - Warm-up | 1-3 |
| 2 - JSON | 4-7 |
| 3 - Hierarchies | 8-11 |
| 4 - NULL logic and subqueries | 12-15 |
| 5 - Distributions | 16-19 |
| 6 - Familiar mix | 20-22 |
| 7 - Changing the data | 23-30 |

## The writable stage

SQLite has no stored procedures, variables, loops or TRY/CATCH. What it has
instead is constraints, triggers, views, conflict clauses and DML driven by
expressions -- and each of questions 23 to 30 is one of those.

**How they run.** Press Run and your script executes, statement by statement,
in a private in-memory copy of the database. Nothing you write can reach the
real file. The copy **persists across Runs of the same question** -- so you can
run an `UPDATE`, then a `SELECT`, and see what it did -- and **Reset** throws it
away and starts again from the seeded data. Moving to another question also
starts fresh, so no question depends on what another one wrote. If your
script ends in a statement that returns rows, the results pane shows that;
otherwise it shows the question's *probe* query, which is what **Check answer**
compares. Check always grades a fresh copy, so nothing you ran earlier can
affect the grade. The status bar reports how many statements ran and how many
rows changed; on question 24 that count is the difference between right and
wrong.

**Driver statements.** Questions 25, 27, 29 and 30 run statements of their own
*after* yours -- inserts that your constraint, trigger, index or STRICT table
should refuse, or let through. A refusal is reported in the status bar as what
it is, not as an error.

| # | Construct |
|---|---|
| 23 | `CASE` inside an `UPDATE`, and what a `CASE` with no `ELSE` returns |
| 24 | `ON CONFLICT DO UPDATE ... WHERE` -- an upsert that only improves a row |
| 25 | `CREATE TABLE` with PRIMARY KEY, REFERENCES, NOT NULL, CHECK and DEFAULT |
| 26 | the rebuild-a-table migration, and why `PRAGMA foreign_keys` must go off first |
| 27 | `RAISE(IGNORE)` -- a trigger that drops one row of a multi-row INSERT |
| 28 | a view whose SELECT starts with `WITH RECURSIVE`: a calendar that stores nothing |
| 29 | `CREATE UNIQUE INDEX` as a constraint on an existing table |
| 30 | a `STRICT` table, where the declared type is a rule and not a hint |

**Two schema tables you can query.** `sqlite_master` holds every object's
CREATE statement -- question 26's probe reads it for the word CHECK.
`pragma_index_list('t')` and `pragma_index_info('name')` describe a table's
indexes; question 29's probe counts the unique ones.

## Things the data does on purpose

- **4 stations have never been surveyed** for step-free access, which
  question 1 counts and question 12's logic is about.
- **The staff tree is five levels deep**, forty people under one, and the top
  person reports to nobody -- questions 8 to 11 walk it in four directions.
- **178 incidents have no quantified delay**, which is what makes
  question 12's NOT go wrong.
- **30 units have never been refurbished**, so question 13 has NULLs
  to move.
- **No Class 170 unit has more than 242 seats**, while every other model
  reaches 300 -- question 14's target.
- **Station 3's q1 figures are 41,704 for 2024 and 36,020 for 2025**,
  one below and one above what question 24 sends.
- **Service 10 is line 4 at 06:09 on 2025-01-01**, the slot question 29's
  driver tries to reuse, and **the last ticket_id is 34,460**.
- **The timetable is not flat.** Services per day run from 6 to
  27, thinner at weekends and in winter.

**One SQLite quirk to know.** In this build, `json_group_array(x ORDER BY y)`
emits the sort keys instead of `x` when `x` and `y` come from different joined
tables; `group_concat` does not. Question 5 asks for a subquery for that reason.

## 1 - Warm-up (3)

Three familiar questions: counting the NULLs rather than the values, a row count
that COUNT(DISTINCT) would get wrong, and a LEFT JOIN whose count must not
multiply.

1. **Stations per town, surveyed or not** (Q672)

   One row per town: how many stations it has, and how many of them have never
   been surveyed for step-free access.

   An unsurveyed station has step_free NULL.

   *Return: town, stations, unsurveyed*

2. **Front and rear** (Q673)

   One row per position in the train: how many workings there have been at
   that position -- rows of service_units -- and the average seats of the
   units that took it, to one decimal.

   *Return: position, workings, avg_seats*

3. **Services and first-class sales, per line** (Q674)

   For each line: how many services it scheduled, and how many first-class
   tickets it sold.

   Services with no tickets still count as services.

   *Return: line_id, services, first_class*

## 2 - JSON (4)

New ground. SQLite has had JSON built in since 3.38: json_object builds a
document, json_group_array aggregates into an array, json_each unnests text into
rows, and a subquery nests one inside another.

4. **A unit as a JSON object** (Q675)

   Units 1 to 8, each as one JSON object with keys model, seats, built and
   refurbished -- numbers as numbers, and a unit never refurbished carrying a
   JSON null.

   Use json_object. Building JSON by gluing strings together is the trap.

   *Return: unit_id, doc*

5. **A route as a JSON array** (Q676)

   For the first service that ran (not cancelled) on each line -- the lowest
   service_id -- its calling points as a JSON array of station NAMES in stop
   order.

   json_group_array is the aggregate. Give it the names and the order from a
   subquery that joins stops to stations first.

   *Return: line_id, route*

6. **A list handed in as JSON** (Q677)

   An app sends the station ids it wants as JSON text: '[5, 12, 40, 58]'.
   Return each of those stations' name and town, by unnesting the array with
   json_each and joining -- no IN list typed by hand.

   *Return: station_id, name, town*

7. **A nested document per line** (Q678)

   Each line as one JSON object: its name under 'line', its colour under
   'colour', and under 'towns' a JSON array of the DISTINCT towns it calls in,
   alphabetical.

   A subquery builds the array; json_object nests it.

   *Return: line_id, doc*

## 3 - Hierarchies (4)

The staff tree is five levels deep. One recursive CTE, pointed four ways: depth
from the top, the chain of names, the managers above one person, and the
headcount below every manager at once.

8. **How far down the tree** (Q679)

   Every member of staff with their depth in the reporting tree: 0 for the one
   person who reports to nobody, 1 for those who report to them, and so on.
   Forty rows.

   *Return: staff_id, depth*

9. **The chain, written out** (Q680)

   Every member of staff with the chain of names from the top of the tree down
   to them, joined by ' > ' -- so the top person's chain is just their own
   name.

   *Return: staff_id, chain*

10. **Everyone above staff 37** (Q681)

    The managers above staff member 37, all the way to the top, with how many
    steps up each one is: 1 for the direct manager.

    This walks UP the tree, so the step follows reports_to from the person,
    not from the top.

    *Return: staff_id, name, steps_up*

11. **Headcount below each manager** (Q682)

    For everyone who has at least one person below them: how many people are
    under them at ANY depth -- reports, reports of reports, and so on.

    Seed the recursion with every person as their own root, then count what
    each root reaches.

    *Return: staff_id, headcount_below*

## 4 - NULL logic and subqueries (4)

Three-valued logic and NOT, where NULLs sort and how to move them, ALL and ANY
written as MAX and MIN, and an average of sums that needs two levels.

12. **Not known to be long** (Q683)

    Per kind of incident, how many are NOT over 30 minutes -- and an incident
    whose delay was never quantified is not over 30 minutes either, so it
    counts.

    *Return: kind, incidents*

13. **Never refurbished goes last** (Q684)

    Every unit numbered by refurbishment year, earliest first -- and the units
    NEVER refurbished numbered after all the others, not before. Ties by
    unit_id.

    *Return: unit_id, refurbished_year, position*

14. **As many seats as every Class 170** (Q685)

    Units with at least as many seats as EVERY Class 170 unit -- the biggest
    Class 170s themselves included.

    SQLite has no ALL or ANY. 'At least as many as every one of them' is a
    comparison with one number from a subquery -- which number?

    *Return: unit_id, model, seats*

15. **The average service's takings** (Q686)

    For each line, the average revenue PER SERVICE, to the nearest penny --
    add up each service's tickets first, then average those totals. Services
    with no tickets do not count.

    An aggregate of an aggregate needs two levels.

    *Return: line_id, avg_service_revenue*

## 5 - Distributions (4)

NTILE tiers, PERCENT_RANK against CUME_DIST, a standard deviation by hand, and a
histogram from integer division.

16. **The fleet in three tiers** (Q687)

    Split the fifty units into three tiers by seats -- tier 1 the smallest --
    as evenly as possible, ties by unit_id. One row per tier with how many
    units it holds and its smallest and largest seat count.

    *Return: tier, units, min_seats, max_seats*

17. **Where a salary sits in its role** (Q688)

    Every member of staff with their salary's PERCENT_RANK within their role,
    to three decimals: 0 for the lowest paid in the role, 1 for the highest.

    *Return: staff_id, role, salary, pct_rank*

18. **How spread out the prices are** (Q689)

    For each class, the average ticket price and its population standard
    deviation, both in pence to one decimal.

    SQLite has no STDDEV. The variance is the mean of the squares minus the
    square of the mean; sqrt() is built in.

    *Return: class, avg_price, stddev*

19. **Ticket prices in five-pound bands** (Q690)

    A histogram of ticket prices: how many tickets fall in each five-pound
    band, the band labelled by where it starts in pounds -- 0, 5, 10... A
    ticket at exactly 10.00 belongs to the 10 band.

    *Return: band, tickets*

## 6 - Familiar mix (3)

Top-1 per group, a self-join along the stop sequence, and a date spine counting
the days nothing happened.

20. **Each line's worst service** (Q691)

    For each line, the service that lost the most quantified delay minutes
    across its incidents, and how many. One row per line; ties by the lower
    service_id.

    *Return: line_id, service_id, delay_minutes*

21. **Consecutive calls on line 1** (Q692)

    The pairs of stations that line 1's services call at one after the other:
    each (this stop, next stop) pair once. Nine pairs for a ten-station route.

    *Return: from_station, to_station*

22. **Days with no incidents, per month** (Q693)

    For each month of the timetable, how many days had NO incident reported at
    all. Eighteen months, every one of which has some quiet days.

    A day with nothing reported has no row anywhere; generate the days first.

    *Return: month, quiet_days*

## 7 - Changing the data (8)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. CASE in an UPDATE, a conditional
upsert, a table with four kinds of constraint, the rebuild-a-table migration,
RAISE(IGNORE), a recursive view, a UNIQUE index and a STRICT table.

23. **A raise that depends on the role** (Q694)

    One UPDATE that gives every member of staff a raise by role: managers 2%,
    drivers 4%, everyone else 3%. Whole pounds: CAST(ROUND(salary * factor) AS
    INTEGER).

    The factor is a CASE expression. Think about what CASE returns for a role
    you did not list.

    *Checked: total salary by role*

24. **Update only if it is an improvement** (Q695)

    Two revised q1 figures for station 3 arrive: 35000 for 2025 and 90000 for
    2024. Both rows exist. Write two UPSERTs that create the row if missing
    and otherwise update q1 -- but ONLY when the new figure is higher than the
    stored one. The 2025 figure is lower and must be ignored.

    Use (3, 2025, 35000, 30136, 31843, 38990) and (3, 2024, 90000, 0, 0, 0) as
    the VALUES.

    *Checked: station 3's year, q1 and q2*

25. **A table that defends itself** (Q696)

    Create `station_notes`: note_id INTEGER PRIMARY KEY; station_id that must
    reference stations; note, TEXT, required, 1 to 80 characters; noted_on,
    TEXT, defaulting to '2026-07-01'.

    After your script, the question inserts three notes: a good one for
    station 5, one for station 999, and an empty one. Exactly one should land.

    *Checked: SELECT * FROM station_notes*

26. **Add a constraint by rebuilding the table** (Q697)

    `operators` needs a CHECK (since_year >= 1900). ALTER TABLE cannot add
    one, so rebuild: create the new table, copy the rows, drop the old one,
    rename the new one into place.

    Services reference operators, so DROP TABLE is refused while foreign keys
    are on. Turn them off for the rebuild and back on after -- a PRAGMA, not a
    transaction, since PRAGMA foreign_keys is a no-op inside one.

    *Checked: the row count, whether the table's SQL now has a CHECK, and how many services would be orphaned*

27. **Drop the bad row, keep the rest** (Q698)

    Write a trigger that silently discards any ticket inserted with a price of
    0 -- no error, the other rows of the same INSERT still land.

    After your script, the question inserts three tickets in ONE statement;
    the middle one is free. Two should land.

    *Checked: id and price of every ticket after the last existing one*

28. **A calendar that stores nothing** (Q699)

    Create a view `calendar (day)` that yields every date from 2025-01-01 to
    2026-06-30 inclusive -- 546 rows -- generated by a recursive CTE inside
    the view. It stores no rows.

    *Checked: the count, first and last day, and how many days in it have no incident*

29. **One service per slot** (Q700)

    No two services may share a line, date and departure time. Enforce that
    with a UNIQUE index on `services`.

    After your script, the question inserts two services on line 4 for
    2025-01-01: one at 06:09, which service 10 already holds, and one at
    06:10. Exactly one should be refused.

    *Checked: line 4's services that day, and how many unique indexes services has beyond its primary key*

30. **A table that refuses the wrong type** (Q701)

    Create `unit_mileage (unit_id INTEGER PRIMARY KEY referencing
    rolling_stock, miles INTEGER NOT NULL)` as a STRICT table, so that a REAL
    can never be stored in the INTEGER column.

    After your script, the question inserts miles of 120500, 98000.5 and
    '77000' for units 1, 2 and 3. One should be refused; one should be
    converted.

    *Checked: unit_id, miles and typeof(miles)*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
671 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
