# SQL practice exercises

Thirty questions on the railway schema, re-seeded so no answer from the previous
set carries over. Twenty-two are SELECT questions across the usual tiers, at the
same level as the last set. **The last eight are writable** -- graded on the
state of the database after your script runs, not on what a query returns --
and each takes a construct the previous set did not.

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
instead is triggers, views, transactions with savepoints, and DML driven by
subqueries -- and each of questions 23 to 30 is one of those.

**How they run.** Press Run and your script executes, statement by statement,
in a private in-memory copy of the database. Nothing you write can reach the
real file. The copy **persists across Runs of the same question** -- so you can
run an `UPDATE`, then a `SELECT`, and see what it did -- and **Reset** throws it
away and starts again from the seeded data. Moving to another question also
starts fresh, so no question depends on what another one wrote. If your
script ends in a `SELECT`, the results pane shows that; otherwise it shows the
question's *probe* query, which is what **Check answer** compares. Check always
grades a fresh copy, so nothing you ran earlier can affect the grade. The status
bar reports how many statements ran and how many rows changed.

**Driver statements.** Questions 27 and 28 run statements of their own *after*
yours -- one insert that should pass through your view's trigger, and one
delete that your trigger should catch. A refusal is reported in the status bar
as what it is, not as an error.

| # | Construct |
|---|---|
| 23 | `DELETE` with a `NOT IN` subquery -- and why the subquery's column must be NOT NULL |
| 24 | `UPDATE` with a correlated subquery in `SET` |
| 25 | `INSERT ... SELECT`, and the type affinity that lets a REAL into an INTEGER column |
| 26 | nested `SAVEPOINT`s -- `RELEASE` merges, it does not commit |
| 27 | an `INSTEAD OF INSERT` trigger, the only kind a view accepts |
| 28 | an `AFTER DELETE` trigger, where `OLD` is all there is |
| 29 | a view with a computed column, and the filter it must carry |
| 30 | `ALTER TABLE` -- rename, add with a default, drop -- and what it refuses |

**A trigger runs once per row.** `NEW` is the row being written, `OLD` the row
being replaced or removed; an INSERT trigger has only `NEW`, a DELETE trigger
only `OLD`. On a view, only `INSTEAD OF` is allowed -- the view has no rows for
a BEFORE or AFTER to be before or after.

## Things the data does on purpose

- **7 stations are on no line's route** and still have footfall rows,
  which is what question 23 deletes.
- **174 incidents have no quantified delay**, and question 24 fills
  them in by kind.
- **Every station has 2023, 2024 and 2025 footfall rows** and no 2026 row, so
  question 25's insert collides with nothing.
- **Service 1 ran on 2025-01-01 and first calls at station 25**, which is the
  ticket question 27 drives through the view.
- **Three incidents were reported on 2025-01-02**, the ones question 28
  deletes.
- **4,725 stops have no recorded arrival**, and question 29's view must
  leave them out.
- **The timetable is not flat.** Services per day run from 6 to
  27, thinner at weekends and in winter.
- **`price_pence` and the footfall quarters are INTEGER.** Exact until you
  divide, and a REAL written into one stays a REAL.

## 1 - Warm-up (3)

Three questions on one or two tables: an average that must not be a truncated
division, pence into pounds, and a pair of conditions that belong in HAVING.

1. **Seats by model** (Q582)

   One row per model of rolling stock: how many units, the seats across all of
   them, and the average seats per unit to the nearest seat.

   *Return: model, units, total_seats, avg_seats*

2. **Takings per operator, in pounds** (Q583)

   One row per operator: how many tickets were sold on its services, and the
   revenue in POUNDS to two decimals.

   price_pence is an integer.

   *Return: operator, tickets, revenue_pounds*

3. **Common, roomy models** (Q584)

   Models with at least 5 units whose average seats per unit is above 200,
   with the unit count and that average to the nearest seat.

   Both conditions describe the model as a whole, not any one unit.

   *Return: model, units, avg_seats*

## 2 - Sequences and strings (4)

`stops` is keyed on (service_id, stop_seq). LAG along that sequence twice --
once where the partition matters, once where NULL does -- a surname split, and a
set difference between two kinds of day.

4. **The shortest leg of each service** (Q585)

   For every service that ran on 2025-03-03: the fewest minutes between one
   scheduled call and the next.

   A leg belongs to one service. The gap must never be measured from the
   previous service's last stop to this one's first.

   *Return: service_id, shortest_leg*

5. **Surnames on the payroll** (Q586)

   How many staff share each surname. Every name is exactly two words; the
   surname is the second.

   Most common first, ties by surname.

   *Return: surname, staff*

6. **Lateness, stop by stop** (Q587)

   For service 311, each stop's lateness in minutes -- actual arrival minus
   scheduled -- and how much that changed since the previous stop.

   A stop with no recorded arrival has NULL lateness and NULL change, and so
   does the stop after it. The first stop's change is NULL.

   *Return: stop_seq, late_minutes, change*

7. **Days with trouble but no cancellations** (Q588)

   Dates on which at least one incident was reported but NO service was
   cancelled.

   Incidents are dated by reported_at, cancellations by run_date. One column,
   one row per date.

   *Return: day*

## 3 - Unpivot and set ops (3)

Twelve quarters as rows, a self-join on a derived value, and a two-column
INTERSECT over ordered pairs.

8. **Station 5, quarter by quarter** (Q589)

   Station 5's footfall as one ROW per quarter, across every year it has a row
   for, labelled like '2024-q3'. Twelve rows, earliest first.

   *Return: period, footfall*

9. **Opened in the same year** (Q590)

   Pairs of stations that opened in the same calendar year, with the year.
   Each pair once, the lower station_id first.

   *Return: station_a, station_b, year*

10. **Formations both lines have used** (Q591)

    Two-unit formations -- the front unit and the rear unit, in that order --
    that have run on both line 1 and line 2.

    A formation is ordered: unit 9 leading unit 8 is not the same as unit 8
    leading unit 9. Position 1 is the front.

    *Return: front_unit, rear_unit*

## 4 - Dates and times (4)

A quarter built from the month, journey times across two tables, ages in
completed years, and a modifier chain to the last week of the month.

11. **Incidents by quarter** (Q592)

    How many incidents were reported in each calendar quarter, labelled like
    '2025-Q3', earliest first. Six quarters.

    strftime has no quarter code: build it from the month.

    *Return: quarter, incidents*

12. **Journey time by line** (Q593)

    For each line, the average scheduled journey in minutes, to one decimal:
    from the service's departure to its LAST scheduled call.

    The departure time is in `services`; the calls are in `stops`. Cancelled
    services have no stops and must not count.

    *Return: line_id, avg_minutes*

13. **How old each station is** (Q594)

    Every station's age in completed years on 2026-06-30.

    A station opened on 1952-11-18 is 73 that day, not 74: its anniversary has
    not come round yet.

    *Return: station_id, age*

14. **The last week of each month** (Q595)

    How many services ran in the last seven days of each month -- the 25th to
    the 31st of a 31-day month, the 22nd to the 28th of February 2026.
    Eighteen months.

    Build the window with date modifiers, not a day-of-month number.

    *Return: month, services*

## 5 - Joins and grain (4)

A filter that must live in ON, two children of one parent summed, a NOT IN that
a single NULL empties, and a group condition that only HAVING can express.

15. **Drivers based in each town** (Q596)

    Every town with the number of DRIVERS based at its stations. Towns with
    none must appear with 0, so all 20 towns come back.

    *Return: town, drivers*

16. **Takings and delay per operator** (Q597)

    For each operator: total ticket revenue in pence, and total quantified
    delay minutes, across its services.

    Tickets and incidents both hang off `services`. Joining both at once
    multiplies every ticket by the service's incidents, and the other way
    round.

    *Return: operator, revenue, delay_minutes*

17. **Staff who manage nobody** (Q598)

    Members of staff to whom nobody reports.

    The one person at the top reports to nobody -- reports_to is NULL there --
    and that single row is enough to make one obvious phrasing return nothing
    at all.

    *Return: staff_id, name*

18. **Lost time at every stop** (Q599)

    Services on 2025-01-10 that arrived later than scheduled at EVERY stop,
    with their number of stops.

    A stop with no recorded arrival is not a late one, so a service with an
    unrecorded stop does not qualify.

    *Return: service_id, stops*

## 6 - Window functions (4)

A seven-day rolling frame, a rank and an aggregate over the same partition, a
share of a partition, and top-N per group from the other end.

19. **The week's tickets, rolling** (Q600)

    For each day of January 2025: tickets sold that day, and the total over
    the seven days ending that day -- for the first six days, over as many
    days as there are.

    *Return: day, tickets, seven_day_total*

20. **Pay rank within the role** (Q601)

    Every member of staff with their salary's rank within their ROLE -- 1 for
    the best paid -- and how many pounds behind that role's top salary they
    are.

    *Return: staff_id, role, salary, rank_in_role, behind_top*

21. **Each kind's share of the line's delay** (Q602)

    For every line and kind of incident: the quantified delay minutes, and
    what percentage of THAT LINE's delay minutes it is, to two decimals.

    Each line's five percentages add to 100.

    *Return: line_id, kind, delay_minutes, pct_of_line*

22. **The three latest incidents on each line** (Q603)

    For each line, its three most recently reported incidents. Eighteen rows.
    When two were reported on the same day, the higher incident_id is the more
    recent.

    *Return: line_id, incident_id, reported_at*

## 7 - Changing the data (8)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. DELETE and UPDATE by subquery, INSERT
... SELECT, nested savepoints, a trigger on a view, a trigger on a delete, a
computed view and ALTER TABLE -- what SQLite has instead of a procedural
language.

23. **Footfall for stations nobody calls at** (Q604)

    Some stations are on no line's route, yet they have footfall rows. Delete
    the footfall rows of every station that no service has ever called at. 21
    rows go, for 7 stations.

    One DELETE, with a subquery that finds the stations.

    *Checked: how many footfall rows remain, and for how many stations*

24. **Fill in the unquantified delays** (Q605)

    174 incidents have no delay_minutes. Fill each one in with the average
    delay of the quantified incidents of the SAME kind, rounded to a whole
    minute.

    One UPDATE, with a subquery that depends on the row being updated.

    *Checked: total delay minutes and how many incidents are quantified, per kind*

25. **Next year's budget** (Q606)

    Give every station a 2026 footfall row in which each quarter is its 2025
    figure up 10%, rounded to a whole number. Sixty new rows from one INSERT
    ... SELECT.

    The quarter columns are INTEGER. What you insert should be stored as
    integers, not as 25801.6.

    *Checked: per year, the rows, the total footfall, and how many q1 values are stored as integers*

26. **Two savepoints, one raise** (Q607)

    In one transaction: give every guard a 2% raise; set a savepoint; give
    every dispatcher 2%; set a second savepoint; give every manager 2%;
    RELEASE the second savepoint; roll back to the first; commit.

    Whole pounds: CAST(ROUND(salary * 1.02) AS INTEGER). Only the guards'
    raise should survive -- releasing a savepoint does not commit what came
    after it.

    *Checked: total salary by role*

27. **A view you can insert through** (Q608)

    Create a view `open_returns` over `tickets` -- ticket_id, service_id,
    from_station, class, price_pence, sold_at -- for tickets with no
    destination. Then make it writable: a trigger so that an INSERT into the
    view lands in `tickets` with to_station NULL.

    After your script, the question inserts one ticket through the view:
    service 1, from station 25, 'standard', 1200 pence, sold 2025-01-01.

    *Checked: how many open returns there are, and the newest ticket's destination, price and class*

28. **A recycle bin for incidents** (Q609)

    Create a table `incidents_bin` with the same five columns as `incidents`,
    and a trigger so that every incident deleted from `incidents` is copied
    into it first.

    After your script, the question deletes the three incidents reported on
    2025-01-02.

    *Checked: that none of those three remain, and what the bin holds*

29. **A view of lateness** (Q610)

    Create a view `late_stops (service_id, stop_seq, station_id,
    late_minutes)`: each recorded arrival's lateness in whole minutes, actual
    minus scheduled.

    Stops with no recorded arrival must not appear in it at all -- a NULL
    lateness is not a lateness. Just under five thousand stops are like that.

    *Checked: COUNT(*), SUM, MIN and MAX of late_minutes over the view*

30. **Reshape the fleet table** (Q611)

    Three ALTER TABLE statements on `rolling_stock`: rename `seats` to
    `seat_count`; add `in_service INTEGER NOT NULL`, which must be 1 for every
    existing unit; drop `refurbished_year`.

    A NOT NULL column added to a table that already has rows needs something
    to put in them.

    *Checked: unit_id, seat_count and in_service for units 1 to 3, and how many columns the table has*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
581 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
