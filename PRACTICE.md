# SQL practice exercises

Thirty questions on the railway schema, re-seeded so no answer from the previous
set carries over. Same tables -- see [schema.sql](schema.sql) -- and the same
difficulty.

**Two changes in balance.** The efficiency stage drops from six questions to
**four**, and the slots go back to the other tiers: windows and recursion had
only two questions last time and now has four. And every question is new -- this
set uses shapes the last one left alone, including `LAST_VALUE` and its frame,
journey durations, unpivoting to find each station's busiest quarter, and a
recursive walk that builds a string as it goes.

| Stage | Questions |
|---|---|
| 1 - Warm-up | 1-4 |
| 2 - Sequences and strings | 5-9 |
| 3 - Unpivot and set ops | 10-13 |
| 4 - Dates and times | 14-17 |
| 5 - Joins and grain | 18-22 |
| 6 - Windows and recursion | 23-26 |
| 7 - Query efficiency | 27-30 |

## The efficiency stage

Those four **open with a query already in the editor** — one that returns the
right answer by a slow route. Nothing to work out about what to select; only the
plan is wrong. **Reset** restores the original if you lose it, and **F6** shows
the plan and timing for whatever you have written.

| # | The fix |
|---|---|
| 27 | **add** a predicate that filters nothing, to reach a composite index |
| 28 | mixed `ORDER BY` directions cannot walk one index |
| 29 | here the **join beats `EXISTS`** |
| 30 | `DISTINCT` on a bare column, so the index supplies the deduplication |

**Question 29 contradicts the previous set on purpose.** Q431 taught that a
correlated `NOT EXISTS` beats a `LEFT JOIN` anti-join, and its plan assertion
*demanded* the subquery. Q460 is the same shape on the same schema and the advice
reverses — because `stops` is indexed on `station_id` alone while the inner
condition also tests `stop_seq`, so every probe seeks to a station and then reads
thousands of its rows.

The rule was never "prefer `NOT EXISTS`". It is: **check whether the index covers
what the subquery actually asks.**

## Things the data does on purpose

- **`stops` is indexed on `station_id` only.** That single omission is what makes
  question 29 invert the previous set's lesson.
- **Every ticket is sold on the day of travel**, so booking-window questions have
  nothing to find — which is why the dates tier uses modifiers instead.
- **`to_station` is NULL on 2,017 tickets**, so `NOT IN` against it returns
  nothing at all while `EXCEPT` and an anti-join behave.
- **54 of 60 stations never start a service**, which is what makes the outer join
  in question 20 visible rather than theoretical.
- **`price_pence` is an INTEGER.** Exact until you divide, and `/ 100` truncates.
- **`||` binds tighter than `*`** in SQLite — question 2 turns on that.

## 1 - Warm-up (4)

Four questions on a single table -- COUNT versus COUNT(col), integer
arithmetic, two aggregate conditions, and money stored as pence.

1. **Refurbished, and not** (Q432)

   One row per model of rolling stock: how many units exist, and how
   many of those have been refurbished.

   refurbished_year is NULL for a unit that never has been. One table,
   no joins.

   *Return: model, units, refurbished*

2. **Stations by the decade they opened** (Q433)

   How many stations opened in each decade, as a label like '1890s'.

   opened_on is a date. All 60 stations land in exactly one decade.

   *Return: decade, stations*

3. **Roles that are numerous and well paid** (Q434)

   Roles with more than 5 staff whose average salary is above 32000.

   Both conditions are about the role as a whole. One table, no joins.

   *Return: role, staff, avg_salary*

4. **What a ticket costs, by class** (Q435)

   One row per class: the cheapest, dearest and average ticket price in
   POUNDS.

   price_pence holds whole pence. Average to two decimals; the min and
   max are exact.

   *Return: class, cheapest, dearest, average*

## 2 - Sequences and strings (5)

`stops` is keyed on (service_id, stop_seq), so every stop knows where it sits
in its own journey. Five questions on first, last, next and in-order.

5. **The five longest journeys** (Q436)

   The five services that take the longest from their first scheduled
   arrival to their last, in minutes.

   Longest first; break ties by the lower service_id.

   *Return: service_id, minutes*

6. **Where this service ends up** (Q437)

   For service 1, every stop with the name of the station the service
   FINISHES at -- repeated on every row.

   *Return: stop_seq, station, destination*

7. **The five longest waits between stops** (Q438)

   Across every service, the five largest gaps between one scheduled
   arrival and the next on the SAME journey.

   Report the stop the gap arrives at. Largest first; break ties by
   service_id then stop_seq.

   *Return: service_id, stop_seq, minutes*

8. **Always in the middle** (Q439)

   Stations that a service calls at, but which are never the FIRST stop
   of any service and never the LAST.

   *Return: station_id, name*

9. **The first three calls** (Q440)

   For service 1, its first THREE stations as a single string joined
   with ' -> ', in stop order.

   One row, one column.

   *Return: opening_legs*

## 3 - Unpivot and set ops (4)

`station_footfall` is stored WIDE -- four quarter columns per station-year.
SQL has no unpivot operator, so turning it long is something you build.

10. **Quarterly totals for the whole network** (Q441)

    Total footfall across ALL stations in each quarter of 2025.

    The table is wide -- q1 to q4 side by side -- so this needs turning
    long before it can be grouped. Four rows.

    *Return: quarter, footfall*

11. **Each station's busiest quarter** (Q442)

    For each station in 2025, which quarter was its busiest.

    No station ties for its own maximum. One row per station.

    *Return: station_id, quarter, footfall*

12. **Arrived at, never departed from** (Q443)

    Station-and-class pairs that appear as the DESTINATION of a ticket
    but never as the origin of a ticket of that same class.

    Set operators compare whole rows, so both sides are two columns
    wide. Tickets with no destination cannot contribute.

    *Return: station_id, class*

13. **Grew in both directions** (Q444)

    Stations whose Q1 footfall rose from 2024 to 2025 AND whose Q4
    footfall did too.

    *Return: station_id*

## 4 - Dates and times (4)

Dates and times are TEXT. Four questions on arithmetic, extraction and
modifiers -- including one where the obvious modifier order is wrong on
exactly one day in seven.

14. **Incidents by week** (Q445)

    How many incidents were reported in each week, where a week is
    labelled by the MONDAY it starts on.

    Build that Monday with date modifiers. An incident reported on a
    Monday belongs to the week starting that same day.

    *Return: week_start, incidents*

15. **The busiest departure hour** (Q446)

    How many services depart in each hour of the day.

    depart_time is 'HH:MM'. Report the hour as the two-character text it
    appears as, so '06' not 6.

    *Return: hour, services*

16. **Cancellations by day of the week** (Q447)

    For each day of the week, how many services ran and how many were
    cancelled.

    Name the day rather than numbering it. cancelled is 1 or 0. Seven
    rows.

    *Return: day_name, services, cancelled*

17. **Months when incidents rose** (Q448)

    One row per month in which any incident was reported: the month as
    'YYYY-MM', how many there were, and how many more or fewer than the
    month before.

    The first month has nothing before it, so its change is NULL.

    *Return: month, incidents, change*

## 5 - Joins and grain (5)

What one row means. Anti-joins, conditions that belong in ON, two children of
one parent, and COUNT(DISTINCT) counting the right thing.

18. **Stations no ticket is bought to** (Q449)

    Every station that is never the destination of a ticket.

    Write it as an outer join that keeps the non-matches, rather than
    with NOT IN.

    *Return: station_id, name*

19. **Revenue by line** (Q450)

    One row per line: its name and the total ticket revenue in POUNDS,
    to two decimals.

    Tickets belong to services, services to lines. All six lines have
    revenue.

    *Return: line_name, revenue*

20. **Where journeys begin, counted** (Q451)

    One row for every station: its name, and how many services START
    there -- that is, have it as their first stop.

    Most stations never start a service. They must appear with 0, so all
    60 stations come back.

    *Return: name, services_starting*

21. **Tickets and incidents per line** (Q452)

    One row per line: how many tickets were sold on its services, and
    how many incidents were reported on them.

    Both hang off services but are independent of each other. All six
    lines appear.

    *Return: line_name, tickets, incidents*

22. **Units that get around** (Q453)

    Rolling stock units that have worked on more than one LINE.

    A unit is linked to services through service_units, and a service
    belongs to a line.

    *Return: unit_id, lines_worked*

## 6 - Windows and recursion (4)

Four this time rather than two: ranking, a rolling frame, and two recursive
walks -- one carrying a counter, one building a string as it goes.

23. **Lines ranked by revenue** (Q454)

    The six lines ranked by total ticket revenue in pence, highest
    first, with their rank.

    If two lines tied they would share a rank.

    *Return: line_name, revenue_pence, rank*

24. **Three-month rolling average of incidents** (Q455)

    One row per month in which any incident was reported: the month, the
    count, and the average over that month and the two before it.

    The first month averages just itself, the second two months.

    *Return: month, incidents, rolling_avg*

25. **The chain of command** (Q456)

    For every member of staff, their reporting line from the very top
    down to them, as one string joined with ' > '.

    The person with no manager is just their own name. Everyone else is
    their manager's chain with their own name on the end.

    *Return: staff_id, chain*

26. **How deep the hierarchy runs** (Q457)

    Every member of staff with how many levels below the top they sit.

    The person with no manager is 0, their direct reports 1, and so on.
    All 40 appear.

    *Return: staff_id, name, level*

## 7 - Query efficiency (4)

**Graded on the query PLAN.** Each opens with a query already in the editor
that is correct and slow; the **Reset** button puts it back. Four different
causes -- and question 29 deliberately contradicts the last set.

27. **Add a condition to make it faster** (Q458)

    How many tickets cost more than 90 pounds.

    There is an index on tickets(class, price_pence) -- class first. The
    editor's query cannot use it. Make the plan say SEARCH instead of
    SCAN, by ADDING to the WHERE clause rather than changing what is
    there.

    *Plan must not contain: `SCAN`*

    *Return: one row, one column: the count*

28. **One direction or the other, not both** (Q459)

    Every ticket id, ordered by class descending and price descending.

    The editor's query sorts all 40,702 rows. An index can be walked
    forwards or backwards, but not one column each way. Your plan must
    NOT contain 'TEMP B-TREE'.

    *Plan must not contain: `TEMP B-TREE`*

    *Return: ticket_id*

29. **When the join beats the subquery** (Q460)

    How many stations are the FIRST stop of at least one service.

    The editor's NOT EXISTS-style query is correct and slow. stops is
    indexed on station_id alone, and the inner test also checks stop_seq
    -- so each probe reads thousands of rows. Rewrite it as a join. Your
    plan must NOT contain 'CORRELATED'.

    *Plan must not contain: `CORRELATED`*

    *Return: one row, one column: the count*

30. **Let the index do the deduplicating** (Q461)

    The distinct ticket classes.

    tickets(class, price_pence) is indexed, and an index is already
    grouped by its leading column -- so the deduplication is free if you
    let it happen. Your plan must NOT contain 'TEMP B-TREE'.

    *Plan must not contain: `TEMP B-TREE`*

    *Return: class*
## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
431 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
