# SQL practice exercises

Thirty questions on the railway schema, re-seeded so no answer from the previous
set carries over. Same tables -- see [schema.sql](schema.sql) -- and the same
difficulty, with the balance shifted: **ten of the thirty are window
functions**, up from six.

| Stage | Questions |
|---|---|
| 1 - Warm-up | 1-3 |
| 2 - Sequences and strings | 4-7 |
| 3 - Unpivot and set ops | 8-10 |
| 4 - Dates and times | 11-14 |
| 5 - Joins and grain | 15-18 |
| 6 - Window functions | 19-26 |
| 7 - Query efficiency | 27-30 |

## The window stage

Eight of the ten window questions sit in stage 6, and no two want the same
thing. If one of them feels like a repeat of another, look again at the frame:

| # | What it needs |
|---|---|
| 19 | a frame ending at the current row, and an aggregate nested in a window |
| 20 | a fixed trailing frame, where `2 PRECEDING` covers three rows |
| 21 | `RANK` against `DENSE_RANK`, on data with real ties |
| 22 | `PARTITION BY` deciding which total the percentage is out of |
| 23 | `CUME_DIST`, which is not `PERCENT_RANK` |
| 24 | `SUM(COUNT(*)) OVER ()` -- a window running over grouped rows |
| 25 | `ROW_NUMBER` inside a subquery, because a window cannot go in `WHERE` |
| 26 | a frame that looks FORWARD |

The other two are in stage 2, where the sequence is a journey rather than a
series: `LEAD` in question 4, and `LAST_VALUE` in question 5. Question 7 is the
control -- the same answer a window would give, written without one.

Two defaults cause most window bugs, and both appear here. **`OVER ()` with no
`ORDER BY` sees the whole partition on every row**, so it gives a grand total
where you wanted a running one. **`OVER (ORDER BY x)` with no frame stops at
the current row**, which is why `FIRST_VALUE` works out of the box and
`LAST_VALUE` silently returns the row it is standing on.

## The efficiency stage

Those four **open with a query already in the editor** -- correct, but slow.
Nothing to work out about what to select; only the plan is wrong. **Reset**
restores the original and **F6** shows the plan and timing for what you have
written.

| # | The starter's mistake | Measured |
|---|---|---|
| 27 | `COALESCE` wrapped round the JOIN KEY | 3,742 ms -> 1.0 ms |
| 28 | a correlated `EXISTS` that cannot reach the selective filter | 30.9 ms -> 3.1 ms |
| 29 | `GROUP BY` before an `ORDER BY ... LIMIT 50` | 7.9 ms -> 0.05 ms |
| 30 | a join that adds no column but multiplies the rows | 57.5 ms -> 3.8 ms |

**27 is the biggest gap this practice set has produced.** Everyone learns that a
function on a filtered column blocks the index. The same slip on a *join key*
costs four thousand times rather than a few, because a filter is evaluated once
per row while a join key is probed once per row of the other table.

**28 and 29 argue opposite sides on purpose.** 28 punishes a correlated
subquery: it is locked to the correlation you gave it, and the selective filter
lives in a third table it cannot start from. 29 rewards one, because removing
the `GROUP BY` is what lets the index supply the order so the `LIMIT` can stop
early. Neither "prefer joins" nor "prefer subqueries" is the rule. The question
is always which table the work is allowed to start from.

## Things the data does on purpose

- **`to_station` is NULL on 1,703 tickets**, so `NOT IN` against it returns
  nothing at all while `EXCEPT` and `NOT EXISTS` behave. Question 9.
- **`step_free` is NULL for 4 stations**, which makes `= 1`, `<> 0` and
  `IS NOT 0` three different questions. Question 18.
- **`delay_minutes` is missing on many incidents**, so `COUNT(*)` and
  `COUNT(delay_minutes)` disagree and `AVG` quietly ignores them. Question 1.
- **`seats` has heavy ties** -- 14 units share one value -- which is what
  makes `RANK` and `DENSE_RANK` diverge in question 21.
- **55 of 60 stations never start a service.**
- **The timetable is not flat.** Services per day run from 6 to 27, thinner at
  weekends and in winter, so question 11 has a shape to find and question 12
  lands on a different count each month.
- **`price_pence` is an INTEGER.** Exact until you divide, and `/ 100`
  truncates.

## 1 - Warm-up (3)

Three questions on a single table -- COUNT(*) against COUNT(col), integer
arithmetic that has to survive a division, and a CASE whose branches overlap.

1. **Delay by kind of incident** (Q492)

   One row per kind of incident: how many there were, how many have a delay
   recorded, and the average delay in minutes.

   delay_minutes is NULL when nobody logged one. Those incidents still count
   in the first column. Round the average to two decimals.

   *Return: kind, incidents, recorded, avg_delay*

2. **What a ticket costs** (Q493)

   One row per class: how many tickets, and the cheapest and dearest price in
   POUNDS.

   price_pence holds whole pence. Give the pounds to two decimals.

   *Return: class, tickets, cheapest, dearest*

3. **Units by size** (Q494)

   Put every unit of rolling stock into a size band by its seat count and
   count them:

   - 'large' 250 or more
   - 'medium' 150 up to but not including 250
   - 'small' everything else

   All 50 units land in exactly one band.

   *Return: band, units*

## 2 - Sequences and strings (4)

`stops` is keyed on (service_id, stop_seq), so every stop knows where it sits in
its own journey. Two window functions that reach along that sequence, one string
question, and one that asks for the same answer a window would give you --
without using one.

4. **The next station** (Q495)

   For service 100, every stop with the name of the station it calls at NEXT.

   The last stop has nothing after it, so its next station is NULL. Ten rows.

   *Return: stop_seq, station, next_station*

5. **Where each service finishes** (Q496)

   For the first service of each line on 2025-03-05, every stop alongside the
   name of the station that service TERMINATES at -- repeated on each of its
   rows.

   Six services, each with its own terminus. The answer is the last row of
   each service's own sequence, so you need a window that can see past the
   current row.

   *Return: service_id, stop_seq, terminus*

6. **Stations named after their town** (Q497)

   Stations whose name STARTS WITH their town but is not simply the town on
   its own -- 'Marsden Riverside' in Marsden qualifies, plain 'Marsden' does
   not.

   Report what follows the town, with no leading space: 'Riverside'.

   *Return: station_id, name, suffix*

7. **Origin and destination** (Q498)

   For the first service of each line, the station it starts from and the
   station it ends at.

   Both come from `stops`, at opposite ends of the same sequence. Six rows.

   *Return: service_id, origin, destination*

## 3 - Unpivot and set ops (3)

`station_footfall` is one row per station-year with four quarter columns, which
has to be turned on its side before you can compare them. Three questions on
that, on NULL in a NOT IN, and on counting distinct things rather than rows.

8. **Each station's busiest quarter** (Q499)

   For 2025, which quarter each station was busiest in, and the figure.

   station_footfall stores q1..q4 as four COLUMNS of one row, so they have to
   become four rows before you can compare them. Report the quarter as
   'q1'..'q4'. Sixty rows.

   *Return: station_id, quarter, footfall*

9. **Travelled from, never travelled to** (Q500)

   Stations that appear as a ticket's origin but never as any ticket's
   destination.

   to_station is NULL on open tickets. Five stations qualify -- if you get
   none, that is why.

   *Return: station_id*

10. **Models that do not get everywhere** (Q501)

    Models of rolling stock that have worked on some lines but not all six,
    with how many lines they have worked.

    A model that has worked all six does not qualify. Do not hard code the
    six.

    *Return: model, lines*

## 4 - Dates and times (4)

Dates are TEXT in 'YYYY-MM-DD' and times are 'HH:MM'. Four questions on pulling
parts out, on chaining modifiers to reach a particular weekday, and on the
difference between elapsed years and calendar ones.

11. **The week's shape** (Q502)

    How many services ran on each day of the week, Monday first.

    Label the days 'Mon' through 'Sun'. The timetable is thinner at weekends,
    so the numbers should fall away at the end.

    *Return: day, services*

12. **The last Friday of each month** (Q503)

    How many services ran on the last FRIDAY of each month.

    Build that date with modifiers rather than assuming which day it falls on.
    One row per month.

    *Return: month, services*

13. **The longest-serving staff** (Q504)

    The five longest-serving members of staff as at 2026-06-30, in whole
    years.

    Longest first; break ties by staff_id.

    *Return: staff_id, name, years*

14. **When services depart** (Q505)

    How many services depart in each hour of the day.

    depart_time is TEXT in 'HH:MM'. Report the hour as a two-digit string, in
    order.

    *Return: hour, services*

## 5 - Joins and grain (4)

Four questions where the join is not the difficulty -- what one row of the
result MEANS is. Question 15 fans out and 17 deliberately does not; they are
worth reading side by side.

15. **Tickets and incidents per line** (Q506)

    One row per line: how many tickets it sold and how many incidents it had.

    Both hang off `services`, so a service with tickets AND incidents produces
    a row for every combination. The counts must survive that.

    *Return: line_name, tickets, incidents*

16. **Stations nobody travels from** (Q507)

    Stations that are not the origin of a single ticket.

    Write it as an outer join that keeps the non-matches rather than as a
    subquery.

    *Return: station_id, name*

17. **Seats each line has run** (Q508)

    One row per line: the total seats it has run, counting every unit on every
    service.

    A service may be formed of more than one unit and each unit has its own
    seat count. Four tables, and no fan-out to undo.

    *Return: line_name, seats*

18. **Staff at step-free stations** (Q509)

    Staff whose base station is recorded as step-free, with the station's
    name.

    *Return: staff_id, name, station*

## 6 - Window functions (8)

The centre of this set. Eight questions, eight mechanisms: a frame that ends at
the current row and one that starts there, a fixed trailing frame, ties under
RANK and DENSE_RANK, a PARTITION BY that decides a denominator, a percentile, an
aggregate nested inside a window, and ROW_NUMBER doing work that WHERE cannot.

19. **Revenue accumulating** (Q510)

    Ticket revenue by month, with a running total alongside.

    The running total on the last row should equal every ticket ever sold.
    Eighteen rows.

    *Return: month, revenue, running_total*

20. **A three-month view of incidents** (Q511)

    Incidents by month, with the average over that month and the two before
    it.

    The first month averages just itself, the second averages two. Round to
    two decimals.

    *Return: month, incidents, rolling_avg*

21. **Two ways to rank a tie** (Q512)

    The twenty units with the most seats, each with its position by both RANK
    and DENSE_RANK.

    Several units share a seat count, which is the entire point -- the two
    columns must differ somewhere. Most seats first, ties broken by unit_id.

    *Return: unit_id, seats, rank, dense_rank*

22. **Each unit's share of its model** (Q513)

    For every unit, how many services it has worked and what percentage that
    is of its MODEL's total workings.

    Within each model the percentages add to 100. Round to two decimals.

    *Return: unit_id, model, workings, pct_of_model*

23. **Where a station sits in the network** (Q514)

    Every station's total 2025 footfall, with the fraction of stations at or
    below it -- quietest first, so the busiest station scores 1.0.

    Round to three decimals. Sixty rows.

    *Return: station_id, footfall, cume_dist*

24. **Each line's share of the timetable** (Q515)

    One row per line: how many services it ran, and what percentage of all
    services that is.

    The percentages add to 100. Round to two decimals.

    *Return: line_name, services, pct*

25. **The two best days each line had** (Q516)

    For each line, its two highest-earning services by ticket revenue.

    Twelve rows. Break ties by the lower service_id. A window function cannot
    go in WHERE, which shapes the whole query.

    *Return: line_id, service_id, revenue*

26. **Stops still to come** (Q517)

    For service 100, each stop and how many stops remain after it.

    The last stop has 0 remaining. This needs a frame that looks FORWARD,
    which is not what ORDER BY gives you by default.

    *Return: stop_seq, remaining*

## 7 - Query efficiency (4)

Graded on the plan, not just the rows. Each is a join or an aggregate over two
or three tables, so the plan runs to four or five lines and the work is finding
WHICH line is expensive.

27. **A guard that costs four seconds** (Q518)

    How many tickets were sold on lines 3 and 4, one row per line.

    The editor's query wraps the ticket side of the JOIN in COALESCE --
    defensive, harmless-looking, and it takes about four SECONDS.
    tickets.service_id is indexed. Your plan must not contain 'SCAN'.

    *Plan must not contain: `SCAN`*

    *Return: line_id, tickets*

28. **When EXISTS is the slow one** (Q519)

    The stations that line 2 calls at.

    The editor's query uses a correlated EXISTS, which is normally the tidy
    way to write this. Here it is ten times slower than the join it replaced.
    Your plan must not contain 'CORRELATED SCALAR SUBQUERY'.

    *Plan must not contain: `CORRELATED SCALAR SUBQUERY`*

    *Return: station_id, name*

29. **Fifty rows after grouping eleven thousand** (Q520)

    The 50 most recent services with a count of the tickets each sold. Most
    recent first, ties broken by service_id.

    The editor's query groups all 11,107 services and sorts the lot to hand
    back 50. services.run_date is indexed. Your plan must not contain 'B-TREE
    FOR ORDER BY'.

    *Plan must not contain: `B-TREE FOR ORDER BY`*

    *Return: service_id, run_date, tickets*

30. **The join that pays for itself twice** (Q521)

    Tickets sold per line, one row per line.

    The editor's query joins `stops` as well -- it adds no column to the
    result, but it multiplies every service by its seven or eight stops, and
    the COUNT(DISTINCT) then exists only to undo that. Your plan must not
    contain 'count(DISTINCT)'.

    *Plan must not contain: `count(DISTINCT)`*

    *Return: line_name, tickets*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
491 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
