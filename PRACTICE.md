# SQL practice exercises

Thirty questions on a **new schema**: a regional railway. The college is retired
after six consecutive sets -- see [schema.sql](schema.sql).

**The schema is shaped differently, not just about something different.** Its
central fact is an **ordered sequence inside a parent**: `stops` is keyed on
`(service_id, stop_seq)`, so every stop knows where it sits in its own journey.
That makes a family of questions natural that no previous schema could host
honestly -- the first and last station, the next station, the gap since the
previous one, the whole route as a single string.

Three more shapes were chosen to reach concepts no earlier set covered:

| | |
|---|---|
| `station_footfall` | **wide** -- four quarter columns per station-year. Turning it long is an **unpivot**, and SQL has no operator for one |
| `tickets.price_pence` | money as **INTEGER**, so arithmetic meets integer division |
| `tickets.class` | a category whose natural order is **not alphabetical**, so sorting needs `CASE` in `ORDER BY` |

Concepts appearing here for the first time: `GROUP_CONCAT`, `CASE` inside
`ORDER BY`, `FIRST_VALUE`/`LAST_VALUE`, forward-looking frames
(`1 FOLLOWING AND UNBOUNDED FOLLOWING`), `UNION ALL` unpivoting, multi-column set
operations, `date()` modifiers, and `'HH:MM'` arithmetic.

Recursion is deliberately down to **one** question, from eight across the last
three sets.

## The efficiency stage now opens filled in

Each of the last six **starts with a query already in the editor** that returns
the right answer by a slow route. Nothing to work out about what to select --
the task is only to improve the plan.

```
Right rows, but the query plan contains 'SCAN', which this question asks you
to avoid.
```

Press **F6** for the plan and timing, change the query, press F6 again. The
checker guarantees each starter is genuinely correct and genuinely rejected, so
there is always something real to fix.

| Stage | Questions |
|---|---|
| 1 - Warm-up | 1-4 |
| 2 - Sequences and strings | 5-10 |
| 3 - Unpivot and set ops | 11-14 |
| 4 - Dates and times | 15-18 |
| 5 - Joins and grain | 19-22 |
| 6 - Windows and recursion | 23-24 |
| 7 - Query efficiency | 25-30 |

## Things the data does on purpose

- **Every service on a line calls at the same stations in the same order**, so a
  route is a property of the line. Six lines, 50 stations on one of them, 10 on
  none.
- **Cancelled services have no stops at all** -- 409 of them.
- **A unit works one or two lines, never all six**, because each line draws from
  an overlapping pool. Five units have never run.
- **Tickets are for journeys the service actually makes**: `from_station` and
  `to_station` are stations on its own route, and `to_station` is always later
  in the journey than `from_station`.
- **`actual_arrive` is NULL where a stop was skipped**, so lateness is unknown
  rather than zero.
- **`'HH:MM'` compares correctly as text** -- fixed width and zero padded -- but
  subtracting it coerces to a number and reads `'09:47'` as 9.

## 1 - Warm-up (4)

Single table. Integer money, a category whose order is not alphabetical,
NULL as its own case, and string surgery.

1. **Revenue in pounds** (Q402)

   Total ticket revenue, in POUNDS, to two decimal places.

   price_pence is an INTEGER column holding whole pence. One table, no
   joins.

   *Return: one row, one column: the total in pounds*

2. **Classes in price order** (Q403)

   The three ticket classes with how many were sold, ordered from most
   expensive class to cheapest: first, then standard, then advance.

   That is not alphabetical order, and it is not the order of any
   column in the table. One table, no joins.

   *Return: class, tickets, sort_order  (1, 2, 3 for first, standard,
advance -- the grader ignores row order, so the ordering has to be a
VALUE you return)*

3. **Step-free access, surveyed and not** (Q404)

   Classify every station by its step_free value and count them:

       'step free'     step_free is 1
       'not step free' step_free is 0
       'not surveyed'  step_free is NULL

   All 60 stations land in exactly one bucket. One table, no joins.

   *Return: access, stations*

4. **Stations named after their town** (Q405)

   Stations whose name is the town name plus a suffix -- that is, the
   name starts with the town and is longer than it.

   A station whose name IS exactly its town does not qualify.

   *Return: station_id, name, town, suffix  (the part after the town and the space)*

## 2 - Sequences and strings (6)

The stage this schema exists for. `stops` is keyed on (service_id, stop_seq),
so every stop knows its place in its own journey -- which makes LAG, LEAD,
FIRST_VALUE, forward-looking frames and GROUP_CONCAT natural rather than
contrived.

5. **The whole route on one line** (Q406)

   For service 1, its route as a SINGLE string: every station it calls
   at, in stop order, joined with ' -> '.

   One row, one column.

   *Return: route*

6. **Where each line starts and ends** (Q407)

   For each LINE, the station its services start from and the station
   they end at.

   Every service on a line calls at the same stations in the same
   order, so take any one service on it -- the lowest service_id -- and
   report its first and last stop.

   *Return: line_name, origin, destination*

7. **Minutes between stops** (Q408)

   For service 1, each stop with the number of scheduled minutes since
   the PREVIOUS stop on that journey.

   The first stop has nothing before it, so its gap is NULL. Times are
   'HH:MM' and no service crosses midnight.

   *Return: stop_seq, sched_arrive, minutes_since_previous*

8. **The next station on the journey** (Q409)

   For service 1, each stop with the name of the station it calls at
   NEXT.

   The final stop has nothing after it, so its next station is NULL.

   *Return: stop_seq, station, next_station*

9. **How much of the journey is still to come** (Q410)

   For service 1, each stop with the number of stops STILL AHEAD of it
   on that journey.

   The final stop has 0 ahead of it; the first has all the rest.

   *Return: stop_seq, stops_ahead*

10. **Every station's place in the line** (Q411)

    For service 1, each stop with the name of the station the service
    STARTED from -- repeated on every row.

    *Return: stop_seq, station, origin*

## 3 - Unpivot and set ops (4)

SQL has no UNPIVOT operator and no PIVOT operator. Both directions are done
by hand, and set operators match on whole rows rather than single columns.

11. **Four columns into four rows** (Q412)

    station_footfall holds one row per station-year with q1, q2, q3 and
    q4 side by side. Turn 2025 long again: one row per station per
    quarter.

    Quarters are the integers 1 to 4.

    *Return: station_id, quarter, footfall*

12. **Stations that grew two years running** (Q413)

    Stations whose total footfall rose from 2023 to 2024 AND again from
    2024 to 2025.

    Total footfall for a year is the four quarters added up.

    *Return: station_id*

13. **Bought from there, never bought to there** (Q414)

    Station-and-class pairs that appear as the ORIGIN of a ticket but
    never as the destination of a ticket of that same class.

    Set operators compare WHOLE ROWS, so both sides here are two columns
    wide. Tickets with no destination recorded cannot contribute to the
    second list. There are 18 such pairs.

    *Return: station_id, class*

14. **And back to wide again** (Q415)

    One row per line, with the number of its services in each of the
    three ticket classes as columns.

    A service with no tickets of a class counts 0.

    *Return: line_name, first, standard, advance*

## 4 - Dates and times (4)

date() modifiers rather than string surgery, %w versus integers, and 'HH:MM'
which compares correctly as text but cannot be subtracted.

15. **Services by calendar month** (Q416)

    One row per calendar month, giving the FIRST DAY of that month as a
    date and how many services ran in it.

    Use a date modifier rather than string surgery -- the answer must be
    a real date like '2025-03-01', not '2025-03'.

    *Return: month_start, services*

16. **Weekends versus weekdays** (Q417)

    How many services ran at the weekend and how many midweek.

    Saturday and Sunday are the weekend.

    *Return: part_of_week, services*

17. **How late did it actually arrive** (Q418)

    For service 1, each stop where the train arrived LATE, with how many
    minutes late it was.

    Skipped stops have no actual_arrive and are not late -- they are
    unknown. Times are 'HH:MM'.

    *Return: stop_seq, sched_arrive, actual_arrive, minutes_late*

18. **The last service of each month** (Q419)

    For each calendar month, the run_date of the last day in that month
    on which any service ran.

    Build the month's last day with date modifiers rather than assuming
    30 or 31.

    *Return: month_start, last_running_day*

## 5 - Joins and grain (4)

Outer joins that keep the zeroes, an anti-join, and two child tables that
multiply when joined to the same parent.

19. **Every station, called at or not** (Q420)

    One row per station: id, name, and how many services call there.

    Ten stations are on no line at all. They must appear with 0, so all
    60 come back.

    *Return: station_id, name, calls*

20. **Units that have never run** (Q421)

    Rolling stock that has never been assigned to any service.

    Write it as an outer join that keeps the non-matches. There are 5.

    *Return: unit_id, model*

21. **Stations a journey begins at** (Q422)

    Stations that are the FIRST stop of at least one service.

    Six qualify -- one per line. One row per station, however many
    thousand services start there.

    *Return: station_id, name*

22. **Three measures per line** (Q423)

    One row per line: how many services it ran, how many tickets were
    sold on them, and how many incidents were reported.

    Services is the parent; tickets and incidents are independent
    children of it. All six lines appear.

    *Return: line_id, services, tickets, incidents*

## 6 - Windows and recursion (2)

Two questions. Recursion is deliberately light here -- it has had eight
across the last three sets.

23. **Revenue accumulating through the year** (Q424)

    One row per calendar month of 2025: the month start, that month's
    ticket revenue in pounds, and the running total for the year to that
    point.

    *Return: month_start, revenue, running_total*

24. **Everyone under the top manager** (Q425)

    Everyone below the one member of staff who reports to nobody, with
    how many levels below they sit.

    Their direct reports are 1, those people's reports 2. 39 rows.

    *Return: staff_id, name, level*

## 7 - Query efficiency (6)

**These open with the slow query already in the editor.** It returns the right
answer; only the plan is wrong. Press F6 to see what it is doing, change it,
press F6 again. Grading checks the plan as well as the rows, so the query you
were handed is by definition not yet a pass.

25. **Group the way the index already is** (Q426)

    How many services ran on each distinct date.

    The editor's query sorts all 13,104 rows into a temporary structure
    first. services.run_date is indexed, and an index is already grouped
    -- your plan must NOT contain 'TEMP B-TREE'.

    *Plan must not contain: `TEMP B-TREE`*

    *Opens with a slow query already in the editor.*

    *Return: run_date, services*

26. **A year of services, without scanning** (Q427)

    How many services ran during 2025.

    The editor already contains a query that gets this right by reading
    all 13,104 rows. services.run_date is indexed -- make the plan say
    SEARCH instead of SCAN.

    *Plan must not contain: `SCAN`*

    *Opens with a slow query already in the editor.*

    *Return: one row, one column: the count*

27. **Sort the way the index already is** (Q428)

    The first 20 ticket ids ordered by class, then price, then
    ticket_id.

    The editor's query sorts all 40,686 tickets to return 20. There is
    an index on tickets(class, price_pence) and an index is already
    sorted. Your plan must NOT contain 'TEMP B-TREE'.

    *Plan must not contain: `TEMP B-TREE`*

    *Opens with a slow query already in the editor.*

    *Return: ticket_id*

28. **Keep the index covering** (Q429)

    The class and price of every first-class ticket.

    The editor's query finds the right rows but has to open the table
    for each one. tickets(class, price_pence) already holds everything
    this question needs -- your plan must say COVERING INDEX.

    *Plan must contain: `COVERING INDEX`*

    *Opens with a slow query already in the editor.*

    *Return: class, price_pence*

29. **Names beginning with Alan** (Q430)

    Staff whose name starts with 'Alan'.

    staff.name is indexed. The editor's query cannot use that index --
    make the plan say SEARCH.

    *Plan must not contain: `SCAN`*

    *Opens with a slow query already in the editor.*

    *Return: staff_id, name*

30. **The anti-join that should not be a join** (Q431)

    How many stations no service calls at.

    The editor's query joins 105,821 stops to 60 stations and throws
    nearly all of it away -- it takes about 36ms. Ask the question once
    per station instead: your plan must contain 'CORRELATED SCALAR
    SUBQUERY'.

    *Plan must contain: `CORRELATED SCALAR SUBQUERY`*

    *Opens with a slow query already in the editor.*

    *Return: one row, one column: the count*
## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a SELECT alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
401 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
