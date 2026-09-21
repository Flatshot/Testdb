# SQL practice exercises

Thirty questions on the railway schema, re-seeded so no answer from the previous
set carries over. Twenty-two are SELECT questions across the usual tiers, at the
same level as the last three sets. **The last eight are writable** -- graded on
the state of the database after your script runs, not on what a query returns
-- and each takes a construct none of the earlier sets did.

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
instead is triggers, views, transactions with conflict clauses, and DML driven
by subqueries -- and each of questions 23 to 30 is one of those.

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

**Driver statements.** Questions 27 and 28 run statements of their own *after*
yours -- a delete your trigger must cascade, and two inserts of which your
trigger must fill in exactly one. A refusal is reported in the status bar as
what it is, not as an error.

| # | Construct |
|---|---|
| 23 | `UPDATE` against `INSERT OR REPLACE` -- and what "replace" really does to a row |
| 24 | `DELETE` driven by `ROW_NUMBER` in a subquery: a keep list for top-N per group |
| 25 | a multi-row `INSERT` with named columns, an assigned id and a defaulted flag |
| 26 | `OR IGNORE` against `OR ROLLBACK` inside a transaction -- the nearest thing to TRY/CATCH |
| 27 | a `BEFORE DELETE` trigger that cascades by hand, and when foreign keys are checked |
| 28 | an `AFTER INSERT` trigger that fills in the row just written, gated by `WHEN` |
| 29 | a view built on another view, and a month key frozen into it |
| 30 | an index, and the leading-column rule that decides whether a lookup can use it |

**A trigger runs once per row.** `NEW` is the row being written, `OLD` the row
being replaced or removed. SQLite cannot change `NEW` in a BEFORE trigger; the
idiom for a default is an AFTER INSERT trigger that updates the row by
`NEW.rowid`. A trigger body may hold several statements.

## Things the data does on purpose

- **Station 7's 2024 row has rowid 20**, which question 23's probe reads
  to tell an update from a replace.
- **971 incidents on six lines**, of which question 24 keeps eighteen.
- **The last service_id is 11,141**, so question 25's three new rows are
  everything after it.
- **'Southwell' is already a station and 'Southwell Parkway' is not**, which is
  what question 26's two inserts run into.
- **Service 1 has 8 stops, 4 tickets, 2 units and no incidents**, and ends at
  station 46 -- question 27 deletes it and question 28 defaults a ticket to it.
- **`staff` has indexes on name and reports_to and none on base_station**,
  which question 30 adds.
- **The timetable is not flat.** Services per day run from 6 to
  27, thinner at weekends and in winter.

## 1 - Warm-up (3)

Three questions on one or two tables: a share that needs a float, counting the
NULLs rather than the values, and a rate that AVG computes in one word.

1. **Incidents by kind** (Q642)

   One row per kind of incident: how many, and what percentage of all
   incidents that is, to two decimals.

   *Return: kind, incidents, pct*

2. **Open returns by class** (Q643)

   One row per class: tickets sold, how many of them are open returns -- no
   destination recorded -- and what percentage of the class that is, to two
   decimals.

   *Return: class, tickets, open_returns, pct*

3. **Big operators that cancel** (Q644)

   Operators that scheduled at least 2750 services AND cancelled more than 3%
   of them, with the service count and the rate to two decimals.

   Both conditions describe the operator as a whole.

   *Return: operator, services, cancel_pct*

## 2 - Sequences and strings (4)

`stops` is keyed on (service_id, stop_seq). Two LAGs over one named window, a
handle from two string functions, NTH_VALUE and its frame, and a symmetric
difference.

4. **Legs that ran slow** (Q645)

   For service 500, each leg's scheduled minutes and actual minutes -- from
   the previous stop's arrival to this one's, timetabled and as it happened --
   and the minutes lost, actual minus scheduled.

   The first stop has no leg, so it is NULL across.

   *Return: stop_seq, sched_leg, actual_leg, lost*

5. **A handle for every member of staff** (Q646)

   Every member of staff with a login handle: the name in lower case with the
   space replaced by a dot -- 'Gareth Sedgwick' becomes 'gareth.sedgwick'.

   *Return: staff_id, handle*

6. **The second call** (Q647)

   For every service that ran on 2025-04-07, the station_id of its SECOND stop
   -- one row per service, and no row of NULLs.

   Use NTH_VALUE, and mind its frame.

   *Return: service_id, second_call*

7. **One line or the other, not both** (Q648)

   Towns with a station on line 4's route or on line 5's, but NOT on both.

   Each line calls in eight towns; three are shared.

   *Return: town*

## 3 - Unpivot and set ops (3)

Twelve quarters as rows with a LAG over them, a non-equi self-join on a distance
in days, and relational division from the other side.

8. **Station 9, quarter on quarter** (Q649)

   Station 9's footfall as one row per quarter across all three years,
   labelled like '2024-q3', with the change from the previous quarter. Twelve
   rows in order; the first has no change.

   *Return: period, footfall, change*

9. **Opened within a year of each other** (Q650)

   Pairs of stations that opened within 365 days of one another, each pair
   once with the lower station_id first, and both dates.

   Not 'the same calendar year': December and the following January count.

   *Return: station_a, station_b, opened_a, opened_b*

10. **Lines that have run every model** (Q651)

    Lines on which every model of rolling stock has worked at least once. Do
    not hard-code the number of models.

    *Return: line_id*

## 4 - Dates and times (4)

Two counts by weekday that must not multiply, printf for h:mm, a week number
that needs its year, and 'start of year' across a boundary.

11. **Incident rate by day of the week** (Q652)

    For each day of the week -- strftime's number, 0 for Sunday -- how many
    services ran, how many incidents were reported, and incidents per hundred
    services to one decimal.

    Services and incidents are counted from different tables; do not let one
    multiply the other.

    *Return: weekday, services, incidents, per_100*

12. **Journey time as hours and minutes** (Q653)

    For every service that ran on 2025-03-03, its scheduled journey --
    departure to last call -- formatted as 'h:mm', so 72 minutes shows as
    '1:12' and 50 as '0:50'.

    *Return: service_id, journey*

13. **Tickets by week of 2025** (Q654)

    How many tickets were sold in each week of 2025, numbered by strftime's
    '%W' -- week 00 is the days before the first Monday. Only 2025.

    *Return: week, tickets*

14. **Day of the year, across the boundary** (Q655)

    For incidents reported between 2025-12-28 and 2026-01-04, the day of the
    year each fell on: 1 for the 1st of January, 365 for the 31st of December.
    Oldest first, then incident_id.

    Build it from the 'start of year' modifier, not from a hard-coded date.

    *Return: incident_id, reported_at, day_of_year*

## 5 - Joins and grain (4)

A chain of joins only as outer as its weakest link, three children counted at
once, an anti-join through a foreign key, and a none-of condition in HAVING.

15. **Incidents while each unit was in the train** (Q656)

    Every unit of rolling stock with the number of incidents that happened on
    services it was part of. Units with none -- and the five that have never
    run -- must appear with 0, so all 50 rows come back.

    *Return: unit_id, incidents*

16. **Three counts per service** (Q657)

    For every service scheduled on 2025-03-03: how many stops, how many units
    and how many tickets. Three children of one parent; a cancelled service
    has none of any and shows zeros.

    *Return: service_id, stops, units, tickets*

17. **Based where no train stops** (Q658)

    Staff whose base station is one that no service has ever called at.

    *Return: staff_id, name, base_station*

18. **Clean days** (Q659)

    Days in January 2025 on which NO service was cancelled, with how many
    services ran.

    *Return: day, services*

## 6 - Window functions (4)

A running total divided by a grand total, LAG with an offset of twelve, a share
whose partition names the denominator, and a running maximum.

19. **How far through the year's takings** (Q660)

    For each month of 2025: that month's ticket revenue in pence, and the
    percentage of the YEAR's revenue taken by the end of it, to two decimals.
    December reads 100.

    *Return: month, revenue, cumulative_pct*

20. **Year on year, by month** (Q661)

    Tickets sold per month, each with the count for the SAME month a year
    earlier and the difference. The first twelve months have no earlier year,
    so those two columns are NULL.

    *Return: month, tickets, year_before, change*

21. **Each operator's share of each line** (Q662)

    For every line and operator: how many services, and what percentage of
    THAT LINE's services the operator ran, to two decimals. Each line's four
    percentages add to 100.

    *Return: line_id, operator_id, services, pct_of_line*

22. **Records set** (Q663)

    For each day of January 2025: tickets sold, the highest daily count seen
    so far that month (today included), and 1 if today set or equalled that
    record, else 0.

    *Return: day, tickets, record_so_far, is_record*

## 7 - Changing the data (8)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. UPDATE against REPLACE, a windowed
DELETE, a multi-row INSERT, conflict clauses in a transaction, two triggers, a
stacked view and an index -- what SQLite has instead of a procedural language.

23. **Correct a row without replacing it** (Q664)

    Station 7's 2024 q3 footfall was mis-keyed. Set it to 70000, leaving the
    other three quarters as they are -- and leaving the ROW as it is: the same
    physical row, corrected, not a new row in its place.

    INSERT OR REPLACE looks like an update and is not one.

    *Checked: the row's rowid and its four quarters*

24. **Prune the incident log** (Q665)

    Keep only the three most recent incidents on each line and delete the
    rest. 'Most recent' is by reported_at, then by the higher incident_id.

    A DELETE cannot use a window function directly; number the rows in a
    subquery and delete what is not in the keep list.

    *Checked: per line, how many incidents remain and the earliest date among them*

25. **Three extra services** (Q666)

    Add three services to the timetable in ONE INSERT: line 1, operator 2, on
    2026-07-01, departing 07:15, 11:40 and 16:05. Let the table assign the ids
    and default the cancelled flag; name the columns you supply.

    *Checked: line, operator, date, departure and cancelled flag for every service after the last existing id*

26. **Insert if absent, and carry on** (Q667)

    In one transaction: give every guard a 3% raise, then add two stations --
    'Southwell' and 'Southwell Parkway', both in town Southwell, opened
    2026-07-01, step_free 1 -- and commit. 'Southwell' already exists and
    station names are UNIQUE: that insert must be skipped, not fail, and the
    transaction must still commit.

    Whole pounds: CAST(ROUND(salary * 1.03) AS INTEGER).

    *Checked: the station count, the guards' total salary, and whether 'Southwell Parkway' exists*

27. **Cascade by hand** (Q668)

    The foreign keys on `services` do not cascade, so deleting a service with
    stops, tickets, units or incidents fails. Write a trigger that removes a
    service's rows from all FOUR child tables whenever the service itself is
    deleted.

    After your script, the question deletes service 1, which has 8 stops, 4
    tickets and 2 units.

    *Checked: whether service 1 still exists, and how many stops, tickets and units still name it*

28. **Fill in the blank on the way in** (Q669)

    A ticket inserted with no destination should be given one: the last stop
    of its service. Write a trigger that fills to_station after such an insert
    -- and leaves alone any ticket that arrived with a destination.

    After your script, the question inserts two tickets on service 1 from
    station 49: one with to_station NULL, one with to_station 35.

    *Checked: the destination of every ticket after the last existing id*

29. **A view over a view** (Q670)

    Create `line_daily (line_id, run_date, services)` -- services per line per
    day -- and then `line_monthly (line_id, month, services)` built ON TOP OF
    line_daily, summing its rows by '%Y-%m'.

    Eighteen rows per line in the monthly view: January 2025 and January 2026
    are different months.

    *Checked: line 1's rows of line_monthly, in month order*

30. **An index the lookup can use** (Q671)

    Staff are looked up by base station -- `WHERE base_station = ?` -- and
    there is no index for it. Create one that lets that lookup SEARCH instead
    of SCAN. Name it as you like.

    An index helps a lookup only if the looked-up column is its FIRST column.

    *Checked: whether any index on staff has base_station as its leading column, and how many staff are based at station 14*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
641 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
