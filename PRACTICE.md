# SQL practice exercises

Thirty questions on the railway schema, re-seeded so no answer from the previous
set carries over. Twenty-two are SELECT questions across the usual tiers. **The
last eight are writable** -- graded on the state of the database after your
script runs, not on what a query returns. They replace the efficiency stage.

| Stage | Questions |
|---|---|
| 1 - Warm-up | 1-3 |
| 2 - Sequences and strings | 4-7 |
| 3 - Unpivot and set ops | 8-10 |
| 4 - Dates and times | 11-14 |
| 5 - Joins and grain | 15-18 |
| 6 - Window functions | 19-22 |
| 7 - Changing the data | 23-30 |

## The writable stage

SQLite has no stored procedures, variables, loops or TRY/CATCH. What it has
instead is triggers, views, transactions with savepoints, upsert, and DML driven
by subqueries -- and each of questions 23 to 30 is one of those.

**How they run.** Press Run and your script executes, statement by statement,
in a private in-memory copy of the database. Nothing you write can reach the
real file. The copy **persists across Runs of the same question** -- so you can
run an `UPDATE`, then a `SELECT`, and see what it did -- and **Reset** throws it
away and starts again from the seeded data. Moving to another question also
starts fresh, so no question depends on what another one wrote. If your
script ends in a `SELECT`, the results pane shows that; otherwise it shows the
question's *probe* query, which is what **Check answer** compares. Check always
grades a fresh copy, so nothing you ran earlier can affect the grade. The status
bar reports how many statements ran and how many rows changed; on question 23
that count is the difference between right and wrong.

**Driver statements.** Questions 27 and 28 run statements of their own *after*
yours -- three inserts that your trigger should let through or refuse, three
updates your audit trigger should log or ignore. A refusal is reported in the
status bar as what it is, not as an error.

| # | Construct |
|---|---|
| 23 | `UPDATE` with a guard, and why "rows changed" matters |
| 24 | `CREATE TABLE ... AS SELECT`, then `DELETE` -- copy before you remove |
| 25 | `INSERT ... ON CONFLICT DO UPDATE`, against `INSERT OR IGNORE` |
| 26 | `SAVEPOINT`, `ROLLBACK TO`, `COMMIT` -- and why plain `ROLLBACK` loses everything |
| 27 | a `BEFORE INSERT` trigger with `RAISE()`, enforcing a rule no `CHECK` can see |
| 28 | an `AFTER UPDATE OF salary ... WHEN` audit trigger |
| 29 | a view -- and a fan-out saved in one is a fan-out every time it is used |
| 30 | a generated column, where declaring it REAL does not make the division real |

**A trigger is a SELECT that calls `RAISE`.** `RAISE(ABORT, 'message')` is a
function; a `SELECT` that produces a row executes it, so the `WHERE` is the
condition. `NEW.col` and `OLD.col` are the row after and before -- the same pair
T-SQL calls `inserted` and `deleted`, except that SQLite's trigger runs once per
row rather than once per statement.

## Things the data does on purpose

- **Cancelled services have no stops, tickets, units or incidents**, which is
  what lets question 24 delete them with foreign keys on.
- **Fourteen units built before 2010 have already been refurbished.** Question
  23's guard is what keeps their years.
- **Station 1 already has a 2025 footfall row**, so question 25's insert
  collides -- that is the point.
- **Service 1 ran on 2025-01-01**, and question 27 drives one incident either
  side of it plus one on the day.
- **54 of 60 stations never start a service**, and five units
  have never run at all.
- **The timetable is not flat.** Services per day run from 6 to 27, thinner at
  weekends and in winter.
- **`price_pence` is an INTEGER.** Exact until you divide, and `/ 100`
  truncates -- in a query, and in a generated column.

## 1 - Warm-up (3)

Three questions on one table: rounding to the nearest pound, a share that needs
a float somewhere, and a condition that belongs in HAVING.

1. **Pay by role** (Q552)

   One row per role: how many staff, the lowest and highest salary, and the
   average to the nearest pound.

   *Return: role, staff, lowest, highest, avg_salary*

2. **Each class's share of the tickets** (Q553)

   One row per class: how many tickets, and what percentage of all tickets
   that is, to two decimals.

   *Return: class, tickets, pct*

3. **Large, well-paid roles** (Q554)

   Roles with at least 8 staff whose average salary is above 40000, with the
   count and the average to the nearest pound.

   Both conditions are about the role as a whole.

   *Return: role, staff, avg_salary*

## 2 - Sequences and strings (4)

`stops` is keyed on (service_id, stop_seq). LAG and LEAD along that sequence, a
string idiom for the last word of a name, and a set difference between two
lines' towns.

4. **Minutes between calls** (Q555)

   For service 301, the minutes between each stop's scheduled arrival and the
   previous stop's.

   The first stop has no previous, so its gap is NULL.

   *Return: stop_seq, gap_minutes*

5. **The last word of a station's name** (Q556)

   How many stations end in each word -- 'Bridge', 'Halt', 'Parkway' and so
   on. Only stations whose name has more than one word.

   Most common first, ties by the word.

   *Return: last_word, stations*

6. **Minutes until the next call** (Q557)

   For service 301, each stop with the minutes until the NEXT scheduled
   arrival.

   The last stop has none, so it is NULL.

   *Return: stop_seq, minutes_to_next*

7. **Towns line 3 serves that line 5 does not** (Q558)

   Towns with a station on line 3's route that have NO station on line 5's
   route.

   The two lines share three towns; four are line 3's alone.

   *Return: town*

## 3 - Unpivot and set ops (3)

Four quarter columns turned into rows, a self-join across two years, and
relational division -- models that have worked every line.

8. **The network by quarter, 2024** (Q559)

   Total footfall across every station for each quarter of 2024, as four ROWS
   labelled 'q1' to 'q4'.

   *Return: quarter, footfall*

9. **Busier than the year before** (Q560)

   Stations whose total footfall in 2025 was higher than in 2024, with both
   totals.

   *Return: station_id, footfall_2025, footfall_2024*

10. **Models on every line** (Q561)

    Models of rolling stock that have worked on ALL six lines.

    Do not hard-code the six.

    *Return: model*

## 4 - Dates and times (4)

Weekday against weekend, a share by day of the week, ages from two year columns,
and a modifier chain to the second Monday.

11. **Weekdays and weekends, by month** (Q562)

    For each month, how many services ran on weekdays and how many at the
    weekend.

    *Return: month, weekday, weekend*

12. **Which day of the week sells** (Q563)

    How many tickets were sold on each day of the week, and what percentage of
    all tickets that is, to two decimals.

    Report the day as strftime's number, 0 for Sunday through 6, in that
    order.

    *Return: weekday, tickets, pct*

13. **How old units are when refurbished** (Q564)

    For each model, the average age in years at which its units were
    refurbished, to one decimal.

    Units never refurbished must not count at all.

    *Return: model, avg_age*

14. **The second Monday of each month** (Q565)

    How many services ran on the SECOND Monday of each month.

    Build it with modifiers. All eighteen months.

    *Return: month, services*

## 5 - Joins and grain (4)

An outer join counted correctly, two children of one parent, an anti-join, and a
group condition that only HAVING can express.

15. **Staff based at each station** (Q566)

    Every station with the number of staff based there -- stations with nobody
    must appear with 0, so all 60 rows come back.

    *Return: station, staff*

16. **Tickets and units per service** (Q567)

    For services 1 to 10: how many tickets each sold and how many units it was
    formed of.

    Both hang off `services`, so a service with 6 tickets and 2 units produces
    12 joined rows. The counts must survive that.

    *Return: service_id, tickets, units*

17. **Units that have never run** (Q568)

    Units of rolling stock that have never been assigned to a service. Write
    it as an outer join that keeps the non-matches.

    *Return: unit_id, model*

18. **Services formed of two units** (Q569)

    Which services running on 2025-06-02 are made up of exactly two units?
    Leave out services with one unit, or with three or more.

    For each, build one text column called formation: the two unit ids joined
    by a plus sign, front unit first. In service_units, position 1 is the
    front of the train, so a service with unit 3 at position 1 and unit 7 at
    position 2 shows as 3+7.

    *Return: service_id, formation*

## 6 - Window functions (4)

A running total per partition, a ranking of aggregates, a share of a day, and
top-N per group.

19. **Incidents accumulating, per line** (Q570)

    Incidents by line and month, with a running total that restarts for each
    line.

    *Return: line_id, month, incidents, running_total*

20. **Lines by revenue** (Q571)

    Every line with its ticket revenue in pence and its rank, 1 for the
    highest.

    *Return: line_name, revenue, rank*

21. **Share of the day's takings** (Q572)

    For every service on 2025-05-05 that sold tickets: its revenue and what
    percentage of that DAY's revenue it is, to two decimals.

    The percentages add to 100.

    *Return: service_id, revenue, pct_of_day*

22. **Three best services per line** (Q573)

    For each line, its three highest-earning services. Eighteen rows; ties by
    the lower service_id.

    *Return: line_id, service_id, revenue*

## 7 - Changing the data (8)

Writable questions: your script runs in a throwaway copy of the database and the
question's probe query reads the result. UPDATE, archive-and-delete, upsert,
savepoints, two triggers, a view and a generated column -- what SQLite has
instead of a procedural language.

23. **Refurbish the old fleet** (Q574)

    Record a 2026 refurbishment for every unit built before 2010 that has
    never been refurbished. Units that HAVE been refurbished must keep their
    existing year.

    23 units change. Write the UPDATE.

    *Checked: refurbished_year, grouped by whether the unit was built before 2010*

24. **Archive the cancellations** (Q575)

    Move the cancelled services out of `services`: create a table
    `cancelled_services` holding copies of all 314 cancelled rows, then delete
    them from `services`.

    Two statements. CREATE TABLE ... AS SELECT builds a table and fills it in
    one go.

    *Checked: how many services remain, how many of those are cancelled, and how many rows the archive holds*

25. **Insert or update, in one statement** (Q576)

    Station 1's 2025 footfall row exists. Write ONE INSERT that would create
    it if it did not, and -- since it does -- updates q1 to 22000 while
    leaving q2, q3 and q4 alone.

    Use the values (1, 2025, 22000, 24295, 17202, 17975).

    *Checked: that row, and the table's row count*

26. **A raise, half of which is withdrawn** (Q577)

    In one transaction: give every driver a 3% raise, then set a savepoint,
    then give every guard 3% too -- then roll back to the savepoint so the
    guards' raise is undone, and commit.

    Keep salaries whole pounds: CAST(ROUND(salary * 1.03) AS INTEGER). The
    drivers' raise must survive; the guards' must not.

    *Checked: total salary by role for drivers and guards*

27. **A rule no CHECK can express** (Q578)

    An incident cannot be reported before its service ran. Write a trigger
    that refuses any INSERT into `incidents` whose reported_at is earlier than
    that service's run_date. Same day is fine.

    After your script, the question inserts three incidents for service 1
    (which ran 2025-01-01): reported 2024-12-31, 2025-01-01 and 2025-01-02.
    Exactly one should be refused.

    *Checked: which of the three landed*

28. **An audit trail for pay changes** (Q579)

    Create a table `salary_audit (staff_id, old_salary, new_salary)` and a
    trigger that writes a row to it whenever a member of staff's salary
    ACTUALLY changes -- not when some other column is updated, and not when a
    salary is set to the value it already had.

    After your script, the question runs three UPDATEs: staff 2's salary to
    50000, staff 3's salary to itself, and staff 4's name to itself. Exactly
    one audit row should result.

    *Checked: the audit table*

29. **A view that does not lie** (Q580)

    Create a view `line_revenue (line_name, revenue_pence)` giving each line's
    total ticket revenue.

    Six rows when selected. Be careful what you join: a view is a saved query,
    and a fan-out saved is a fan-out every time anyone uses it.

    *Checked: SELECT * FROM line_revenue*

30. **A column that computes itself** (Q581)

    Add a column `price_pounds` to `tickets` that is always the price in
    pounds, as a REAL -- computed from price_pence, never stored out of step
    with it.

    A generated column. ALTER TABLE can add one as long as it is VIRTUAL.

    *Checked: price_pounds for tickets 1 to 3*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
551 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
