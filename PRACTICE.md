# SQL practice exercises

Thirty questions on the railway schema, re-seeded so no answer from the previous
set carries over. Same tables -- see [schema.sql](schema.sql) -- and the same
difficulty, with one thing raised: **the efficiency questions are harder.**

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

Those four **open with a query already in the editor** -- one that returns the
right answer by a slow route. Nothing to work out about what to select; only the
plan is wrong. **Reset** restores the original if you lose it, and **F6** shows
the plan and timing for whatever you have written.

Previous sets asked these against a single table, so the plan was three lines
and the expensive one was hard to miss. These four join two or three tables:

| # | The starter's mistake | What the plan shows |
|---|---|---|
| 27 | `strftime('%Y', run_date) = '2025'` instead of a range | the join flips to driving from `tickets` and scans all 40,441 |
| 28 | `ORDER BY t.sold_at \|\| ''` alongside `LIMIT 20` | `USE TEMP B-TREE`, so 40,441 rows sort to return 20 |
| 29 | re-formatting a date already stored as `YYYY-MM-DD` | a temp b-tree **and** the join driven from the wrong side |
| 30 | aggregating every ticket in a CTE, then filtering outside it | `MATERIALIZE` -- 40,441 rows of work to answer about 2,000 |

**Two of them punish advice that is usually good.** Question 29's `strftime` call
changes no values whatsoever -- run_date is already in that format. It changes
the *expression*, and the index is on the column, which is enough to lose it.
Question 30 lifts an aggregate into a CTE and rewrites a correlated subquery as
a join, both normally improvements: but a materialised CTE cannot see the outer
`WHERE`, so it computes the whole table before throwing away 95% of it.

`MATERIALIZE` in a plan is the tell. It means SQLite built a subquery result in
full before using any of it, and no outer filter reached inside.

## Things the data does on purpose

- **`to_station` is NULL on 1,999 tickets**, so `NOT IN` against it returns
  nothing at all while `EXCEPT` and `NOT EXISTS` behave. Question 13.
- **`step_free` is NULL for 4 stations** -- neither step-free nor not, so a
  two-way CASE loses them. Question 2.
- **`actual_arrive` is missing on 4,648 stops.** A service can have most of its
  arrivals logged and still not be fully reported. Question 6.
- **54 of 60 stations never start a service**, which is what makes the outer
  join in question 18 visible rather than theoretical.
- **Every ticket is sold on the day of travel**, so booking-window questions
  have nothing to find -- which is why the dates tier uses modifiers instead.
- **The reporting tree is five levels deep**, up from two. Question 25 cannot be
  answered with a join.
- **`price_pence` is an INTEGER.** Exact until you divide, and `/ 100`
  truncates.

## 1 - Warm-up (4)

Four questions on one or two tables -- a CASE over a nullable flag, two
aggregate conditions in different clauses, and integer arithmetic that has to
survive division.

1. **Incidents by severity** (Q462)

   Put every incident into one of three bands by delay_minutes and count them:

   - 'major' 60 or more
   - 'medium' 20 up to but not including 60
   - 'minor' everything else

   All 1,143 incidents land in exactly one band.

   *Return: band, incidents*

2. **Step-free, not step-free, unknown** (Q463)

   Classify every station by step_free and count them:

   - 'yes' step_free is 1
   - 'no' step_free is 0
   - 'unknown' step_free is not recorded

   All 60 stations land in exactly one class.

   *Return: access, stations*

3. **Roles with a wide pay spread** (Q464)

   Roles with at least 5 staff where the highest salary is more than 1.8 times
   the lowest.

   Both conditions are about the role as a whole. One table, no joins.

   *Return: role, staff, lowest, highest*

4. **How long until refurbishment** (Q465)

   One row per model: how many units exist, how many have been refurbished,
   and the average number of years between building and refurbishment for
   those that have.

   refurbished_year is NULL for a unit that never has been, and those must not
   drag the average down.

   *Return: model, units, refurbished, avg_years*

## 2 - Sequences and strings (5)

`stops` is keyed on (service_id, stop_seq), so every stop knows where it sits in
its own journey. Five questions on ordering inside a group: concatenating in
order, an all-or-none test, and three different window frames over the same
sequence.

5. **Every station a line calls at** (Q466)

   For each line, a single comma-separated string of the distinct stations it
   calls at, in alphabetical order.

   No spaces around the commas -- the default separator is what you want. Six
   rows.

   *Return: line_name, stations*

6. **Services reported all the way** (Q467)

   Services on line 1 during June 2025 where EVERY stop has an actual_arrive
   recorded.

   A service with one unrecorded stop does not qualify, however many of its
   other stops were logged.

   *Return: service_id*

7. **Minutes into the journey** (Q468)

   For service 1, each stop with how many minutes after the FIRST scheduled
   arrival it happens.

   The first stop is 0.

   *Return: stop_seq, minutes_in*

8. **How far through the journey** (Q469)

   For service 1, each stop with how far through the journey it is, as a
   percentage of the total number of stops.

   The last stop is 100. Round to two decimals.

   *Return: stop_seq, pct_through*

9. **The two shortest legs** (Q470)

   For service 1, the two SHORTEST gaps between consecutive scheduled
   arrivals, in minutes.

   Report the stop the gap arrives at, shortest first, breaking ties by the
   lower stop_seq.

   *Return: stop_seq, minutes*

## 3 - Unpivot and set ops (4)

`station_footfall` is one row per station-year with four quarter columns, which
has to be turned on its side before you can compare quarters. Four questions on
that and on comparing two row sets.

10. **Quarter on quarter, network wide** (Q471)

    Network-wide footfall for each quarter of 2025, with the change from the
    quarter before.

    Q1 has nothing before it, so its change is NULL. Four rows.

    *Return: quarter, footfall, change*

11. **Busy in both years** (Q472)

    Stations in the ten busiest by total footfall in 2023 AND still in the ten
    busiest in 2025.

    Total footfall for a year is its four quarters added up.

    *Return: station_id*

12. **Towns on more than one line** (Q473)

    Towns whose stations are served by more than one line.

    A town may have several stations; count the DISTINCT lines reaching any of
    them. 13 towns qualify.

    *Return: town, lines*

13. **Stations nobody buys a ticket to** (Q474)

    Stations that are not the destination of a single ticket.

    tickets.to_station is NULL on open tickets, where no destination was
    chosen. There are 23 such stations -- if you get 0 rows, the NULLs are the
    reason, and the note explains why.

    *Return: station_id*

## 4 - Dates and times (4)

Dates are TEXT in 'YYYY-MM-DD'. Four questions on pulling parts out, comparing
against a value the data supplies, and the modifier arithmetic that gets you to
a month boundary.

14. **When tickets are bought** (Q475)

    How many tickets were sold on each day of the week, named rather than
    numbered. Seven rows.

    *Return: day_name, tickets*

15. **Younger than the oldest station** (Q476)

    The five stations that opened LONGEST after the network's oldest station,
    in whole years.

    Longest first; break ties by station_id.

    *Return: station_id, name, years_after*

16. **Services on the last day of the month** (Q477)

    How many services ran on the final calendar day of each month.

    Build that day with date modifiers rather than assuming 30 or 31. One row
    per month that has any.

    *Return: month, services*

17. **Early or late in the month** (Q478)

    How many incidents were reported in the first half of a month (day 1 to
    15) and how many in the second.

    Two rows.

    *Return: half, incidents*

## 5 - Joins and grain (5)

Five questions where the join is not the difficulty -- what one row of the
result MEANS is. Two of them fan out and one deliberately does not.

18. **Step-free stations nobody calls at** (Q479)

    Stations recorded as step-free that no service ever calls at.

    Write the 'never called at' part as an outer join that keeps the non-
    matches.

    *Return: station_id, name*

19. **Seats offered by each line** (Q480)

    One row per line: the total number of seats it has run, counting every
    unit on every service.

    A service may be formed of more than one unit, and each unit has its own
    seat count.

    *Return: line_name, seats*

20. **Staff based at each station** (Q481)

    One row for every station: its name, and how many staff are based there.

    Most stations have none. They must appear with 0, so all 60 stations come
    back.

    *Return: name, staff*

21. **Tickets and incidents per operator** (Q482)

    One row per operator: how many tickets were sold on its services, and how
    many incidents were reported on them.

    Both hang off services but are independent of each other.

    *Return: operator_name, tickets, incidents*

22. **Units that have run in both positions** (Q483)

    Units that have run in position 1 AND also in position 2.

    *Return: unit_id*

## 6 - Windows and recursion (4)

Running totals, shares of a partition, quartiles, and a walk down a reporting
tree that is five levels deep, so a single join reaches only the first of them.

23. **Ticket sales accumulating** (Q484)

    One row per month in which any ticket was sold: the month as 'YYYY-MM',
    how many were sold, and the running total up to and including that month.

    The last month's running total is every ticket.

    *Return: month, tickets, running_total*

24. **Each unit's share of its model's work** (Q485)

    One row per unit that has ever run: its id, its model, how many service-
    slots it has filled, and that as a percentage of all slots filled by units
    of the SAME model.

    Within each model the percentages add up to 100.

    *Return: unit_id, model, slots, pct_of_model*

25. **Everyone under one manager** (Q486)

    Every member of staff below Nerys Fothergill in the reporting tree --
    their reports, their reports' reports, and so on.

    They are not in the answer. Only three of the 18 report to them directly,
    which is why a single join is not enough.

    *Return: staff_id, name*

26. **Stations by footfall quartile** (Q487)

    Every station's 2025 total footfall, with which quarter of the network it
    falls into: 1 for the busiest quarter, 4 for the quietest.

    60 stations split evenly into four groups of 15.

    *Return: station_id, footfall, quartile*

## 7 - Query efficiency (4)

Graded on the plan, not just the rows. Each of these is a join or an aggregate
over two or three tables, so the plan runs to four or five lines -- the work is
finding WHICH line is expensive.

27. **One function, three tables slower** (Q488)

    Total ticket revenue in pence for each line, counting only services that
    ran during 2025.

    The editor's query is correct and reads all 40,441 tickets to do it.
    services.run_date is indexed. Look at the FIRST line of the plan -- it
    says which table the whole join is driven from, and fixing the filter
    changes it. Your plan must not contain 'SCAN'.

    *Plan must not contain: `SCAN`*

    *Return: line_name, revenue_pence*

28. **Twenty rows, forty thousand sorted** (Q489)

    The 20 earliest-sold ticket ids, of tickets attached to a service.

    Every ticket has a service, so the join changes nothing about which rows
    qualify -- but the editor's query still sorts all 40,441 to return 20.
    tickets.sold_at is indexed. Your plan must not contain 'TEMP B-TREE'.

    *Plan must not contain: `TEMP B-TREE`*

    *Return: ticket_id*

29. **Reformatting a date that was already formatted** (Q490)

    Daily ticket revenue: one row per run_date with the total pence taken on
    services running that day.

    run_date is already stored as 'YYYY-MM-DD', and it is indexed. The
    editor's query formats it again before grouping, which costs both a sort
    and the chance to drive the join from services. Same 546 rows either way.
    Your plan must not contain 'TEMP B-TREE'.

    *Plan must not contain: `TEMP B-TREE`*

    *Return: run_date, revenue_pence*

30. **The CTE that computes too much** (Q491)

    For every service on line 2, how many tickets it sold -- 0 if none.

    The editor's query aggregates the WHOLE ticket table in a CTE and then
    joins one line's worth of it. A materialised CTE cannot see the outer
    filter, so it does 40,441 rows of work to answer a question about 2,000.
    Your plan must not contain 'MATERIALIZE'.

    *Plan must not contain: `MATERIALIZE`*

    *Return: service_id, tickets*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
461 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
