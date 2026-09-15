# SQL practice exercises

Thirty questions on the railway schema, re-seeded so no answer from the previous
set carries over. Same tables -- see [schema.sql](schema.sql) -- and the same
difficulty. **Twenty are shapes you have practised; ten use mechanisms no
earlier set did.**

| Stage | Questions |
|---|---|
| 1 - Warm-up | 1-3 |
| 2 - Sequences and strings | 4-7 |
| 3 - Pivot and set ops | 8-10 |
| 4 - Dates and times | 11-14 |
| 5 - Joins and grain | 15-18 |
| 6 - Window functions | 19-26 |
| 7 - Query efficiency | 27-30 |

## The ten new shapes

| # | Mechanism |
|---|---|
| 8 | **Pivot** -- rows into columns by conditional aggregation |
| 9 | **`FILTER (WHERE ...)`** -- the same idea, readable, and it composes with `DISTINCT` |
| 11 | **A date spine** -- generate the calendar so days with nothing appear as 0 |
| 12 | **A `CROSS JOIN` spine** -- every line x kind x quarter, zeros included |
| 16 | **Gaps and islands** -- date minus `ROW_NUMBER` is constant across a run |
| 21 | **`RANGE` frames** -- a frame measured in values, not rows |
| 22 | **`EXCLUDE`** -- dropping the current row and its peers from a frame |
| 23 | **Named windows** -- `WINDOW w AS (...)` used by three functions |
| 24 | **Islands, partitioned** -- the same trick per group |
| 25 | **A median** -- SQLite has none, and even-sized groups need both middles |

Two of these come in pairs. **11 then 12** is a spine in one dimension, then
two. **16 then 24** is island-finding over one series, then per group. Solve
each pair in order; the second is the first plus a `PARTITION BY` or a
`CROSS JOIN`.

The single idea behind 11 and 12 is worth stating plainly: **a `GROUP BY` can
only return groups the data contains.** A day with no incidents has no row to
group, so no amount of rewriting will produce it. You have to generate the rows
you want and `LEFT JOIN` the data onto them -- and then count a column from the
right-hand table, because `COUNT(*)` would count the spine row itself and report
1 where you wanted 0.

## The efficiency stage

Those four **open with a query already in the editor** -- correct, but slow.
**Reset** restores the original and **F6** shows the plan and timing.

| # | The starter's mistake | Measured |
|---|---|---|
| 27 | an aggregate subquery correlated to the row | 4,376 ms -> 5.3 ms |
| 28 | a correlation added to an `IN` that did not need one | 2.0 ms -> 0.19 ms |
| 29 | a TEXT date compared as a number | 2.4 ms -> 0.68 ms |
| 30 | a join that does not fan out, but costs the covering index | 2.0 ms -> 0.88 ms |

**27 reverses Q491 on purpose.** There, lifting an aggregate into a CTE was the
mistake, because the CTE computed far more than the outer query needed. Here it
is the fix, because it computes three numbers that every row wants. Neither
"use a CTE" nor "avoid one" is the rule -- ask what the subquery costs and how
often it runs.

**30 is not the fan-out of question 17.** The row count is identical and nothing
is double-counted. The join's only damage is that `idx_tickets_class` stops
being a *covering* index, so each of the 2,680 matches needs a second read into
the table. Both plans name the same index; only the word COVERING differs, and
that word is the whole cost.

## Things the data does on purpose

- **`to_station` is NULL on many tickets**, so `NOT IN` against it returns
  nothing while `EXCEPT` and `NOT EXISTS` behave.
- **Lines share no stations**, but their rolling-stock pools overlap -- which is
  what makes the set operations in 7 and 10 have an answer.
- **Every line has had every kind of incident**, so questions about what a line
  has escaped need a finer grain than kind.
- **55 of 60 stations never start a service.**
- **Every ticket is sold on the day of travel**, so there is no booking window
  to measure.
- **The timetable is not flat.** Services per day run from 6 to 27, thinner at
  weekends and in winter.
- **`price_pence` is an INTEGER.** Exact until you divide, and `/ 100`
  truncates.

## 1 - Warm-up (3)

Three questions on a single table -- rounding to a stated number of places, a
condition about a group rather than a row, and integer division.

1. **How full the trains are** (Q522)

   One row per model of rolling stock: how many units, the smallest and
   largest seat count, and the average.

   Round the average to one decimal.

   *Return: model, units, fewest, most, avg_seats*

2. **Busy roles** (Q523)

   Roles with more than five staff, and their average salary to the nearest
   pound.

   The condition is about the role as a whole, not about any one person.

   *Return: role, staff, avg_salary*

3. **Revenue by class in pounds** (Q524)

   One row per class: how many tickets and the total revenue in POUNDS, to two
   decimals.

   price_pence holds whole pence.

   *Return: class, tickets, revenue*

## 2 - Sequences and strings (4)

`stops` is keyed on (service_id, stop_seq), so every stop knows where it sits in
its own journey. Gaps between consecutive rows, ordering inside an aggregate, a
frame default, and a set operation.

4. **How long between stops** (Q525)

   For service 200, the gap in minutes between each stop's scheduled arrival
   and the one before it.

   Stop 1 has no predecessor, so report NULL for it.

   *Return: stop_seq, gap_minutes*

5. **The calling pattern, backwards** (Q526)

   For service 200, its stations as one string in REVERSE calling order --
   terminus first -- joined with ' > '.

   One row, one column.

   *Return: pattern*

6. **Where each service came from** (Q527)

   Take the lowest-numbered service on each line -- six services. For every
   stop of those six, give the station that service started from, repeated on
   each of its rows.

   *Return: service_id, stop_seq, origin*

7. **Models both lines use** (Q528)

   Models of rolling stock that have worked on line 1 AND on line 6.

   Four of the seven models qualify.

   *Return: model*

## 3 - Pivot and set ops (3)

Turning rows into columns -- the reverse of the unpivot you have done before --
with CASE and then with the FILTER clause, plus two questions where the answer
is a comparison between two whole result sets rather than a filter on one.

8. **Classes across the top** (Q529)

   One row per line with THREE columns of counts -- advance, first and
   standard -- rather than three rows per line.

   This is the reverse of unpivoting: values that were rows in the `class`
   column become columns of their own. Six rows.

   *Return: line_name, advance, first, standard*

9. **Filtered aggregates** (Q530)

   One row per line: how many DISTINCT services sold at least one first-class
   ticket, and how many sold any ticket at all.

   Both are counts of distinct services over the same joined rows, differing
   only in which rows each one is allowed to see. SQLite has a clause for
   exactly that.

   *Return: line_name, services_with_first, services_selling*

10. **Units line 1 keeps to itself** (Q531)

    Units that have worked on line 1 but never on line 2.

    Seven units qualify.

    *Return: unit_id*

## 4 - Dates and times (4)

Two questions on generating the calendar rather than grouping it, so that days
and combinations with no data still appear; two on modifier chains and on why
subtracting dates as numbers does not work.

11. **Every day of March, including the quiet ones** (Q532)

    Every date in March 2025 with the number of incidents reported that day --
    including the days with none, which must appear as 0.

    Thirty-one rows. The days with no incidents are not in the incidents table
    at all, so grouping it can never produce them: you have to generate the
    calendar and hang the data off it.

    *Return: day, incidents*

12. **Every line, every kind, every quarter** (Q533)

    For each line, each kind of incident and each quarter of 2025, how many
    incidents there were -- including the combinations that never happened, as
    0.

    Label quarters '2025Q1' to '2025Q4'. Six lines x five kinds x four
    quarters, so 120 rows whatever the data does.

    *Return: line_id, kind, quarter, incidents*

13. **The first Monday of each month** (Q534)

    How many services ran on the first MONDAY of each month.

    Build that date with modifiers. One row per month, all eighteen.

    *Return: month, services*

14. **How long staff have served** (Q535)

    Staff bucketed by length of service as at 2026-06-30: 'under 5 years', '5
    to 15', 'over 15'.

    *Return: band, staff*

## 5 - Joins and grain (4)

What one row of the result MEANS. An outer join that must not count its own
NULLs, a run of consecutive dates collapsed into islands, a fan-out that
DISTINCT cannot repair, and an all-or-none test.

15. **Every station, tickets or not** (Q536)

    Every station with the number of tickets bought TO it. Stations nobody
    travels to must appear with 0, so all 60 come back.

    *Return: station_id, name, tickets*

16. **The longest quiet spell** (Q537)

    The three longest runs of CONSECUTIVE days on which line 1 had no incident
    at all.

    Only count days the timetable actually ran. Longest first, then earliest.

    *Return: days, started, ended*

17. **Revenue and incidents together** (Q538)

    One row per operator: total ticket revenue in pence and the number of
    incidents.

    Both hang off `services`. A SUM cannot be rescued by DISTINCT, so the fan-
    out has to be avoided rather than undone.

    *Return: operator, revenue, incidents*

18. **Units that only ever work one line** (Q539)

    Units of rolling stock that have run, and have only ever run on a single
    line -- with that line.

    *Return: unit_id, line_id*

## 6 - Window functions (8)

Eight questions, eight mechanisms: a running frame, top-N per group, a frame
measured in values rather than rows, EXCLUDE, a window named once and used three
times, islands per partition, a median built by hand, and PARTITION BY choosing
a denominator.

19. **Revenue month by month, accumulating** (Q540)

    Ticket revenue by month with a running total.

    *Return: month, revenue, running_total*

20. **The best-earning service on each line** (Q541)

    For each line, the single service that took the most money.

    Ties broken by the lower service_id. Six rows.

    *Return: line_id, service_id, revenue*

21. **Units of a similar size** (Q542)

    For each unit, how many units in the whole fleet have a seat count within
    20 of its own -- itself included.

    'Within 20' is about the VALUES, not about neighbouring rows, so the frame
    has to be measured in seats rather than in positions. Fifty rows.

    *Return: unit_id, seats, similar_units*

22. **Everyone but your equals** (Q543)

    For each unit: its seat count, how many units its MODEL has, and how many
    of those are not on the same seat count as it.

    The last column is the model's fleet minus this unit's tied group. There
    is a frame clause for that -- no arithmetic needed.

    *Return: unit_id, seats, model_units, others*

23. **One window, three questions** (Q544)

    Incidents by month, with a running total, a running average and the
    running maximum.

    All three use the same window. Define it ONCE in a WINDOW clause and refer
    to it by name rather than repeating it. Round the average to two decimals.

    *Return: month, incidents, running_total, running_avg, running_max*

24. **Each line's best quiet streak** (Q545)

    For every line, the length of its longest run of consecutive timetabled
    days with no incident.

    Six rows. Same island-finding as question 16, but partitioned -- each line
    has to be numbered separately.

    *Return: line_id, longest_streak*

25. **The median unit** (Q546)

    The MEDIAN seat count for each model of rolling stock.

    SQLite has no median function. Several models have an even number of
    units, and for those the median is the average of the two middle values --
    not either one of them.

    *Return: model, median_seats*

26. **Share of the line's revenue** (Q547)

    For every service that sold tickets, its revenue and what percentage of
    its LINE's revenue that is.

    Within a line the percentages add to 100. Round to four decimals.

    *Return: service_id, line_id, revenue, pct_of_line*

## 7 - Query efficiency (4)

Graded on the plan, not just the rows. Each is a join or an aggregate over two
or three tables, so the plan runs to four or five lines and the work is finding
WHICH line is expensive.

27. **An average recalculated thirty thousand times** (Q548)

    How many tickets on lines 1 and 2 cost more than the average for their own
    class, one row per line.

    The editor's query asks for that average inside the WHERE clause, where it
    is correlated to the row -- so it is worked out again for every ticket,
    and the query takes about four SECONDS. Your plan must not contain
    'CORRELATED'.

    *Plan must not contain: `CORRELATED`*

    *Return: line_id, tickets*

28. **A correlation that buys nothing** (Q549)

    How many services have had at least one incident.

    The editor's query uses IN with a subquery, and has added a condition
    tying the subquery back to the outer row. It returns the right answer.
    Take the condition out -- IN already compares the value -- and the
    subquery can be evaluated once instead of per row. Your plan must not
    contain 'CORRELATED'.

    *Plan must not contain: `CORRELATED`*

    *Return: one row, one column: the count*

29. **A date treated as a number** (Q550)

    How many tickets were sold on services running in 2026 or later.

    run_date is TEXT in 'YYYY-MM-DD' and is indexed. The editor's query
    compares it as a number, which gets the right answer and loses the index.
    Your plan must not contain 'SCAN'.

    *Plan must not contain: `SCAN`*

    *Return: one row, one column: the count*

30. **The join that costs a covering index** (Q551)

    The class and price of every first-class ticket over 2900 pence, cheapest
    first, ties by ticket_id.

    The editor's query joins `services`. It adds no column, and because every
    ticket has a service it removes no row either -- but idx_tickets_class
    holds only class and price_pence, so reaching service_id forces a lookup
    into the table for all 2,680 matches. Your plan must contain 'COVERING
    INDEX'.

    *Plan must contain: `COVERING INDEX`*

    *Return: class, price_pence*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
521 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
