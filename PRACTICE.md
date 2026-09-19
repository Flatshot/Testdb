# SQL practice exercises

Thirty questions on the railway schema, re-seeded so no answer from the previous
set carries over. Twenty-two are SELECT questions across the usual tiers, at the
same level as the last two sets. **The last eight are writable** -- graded on
the state of the database after your script runs, not on what a query returns
-- and each takes a construct neither earlier set did.

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
instead is triggers, views, transactions, and DML driven by subqueries and CTEs
-- and each of questions 23 to 30 is one of those.

**How they run.** Press Run and your script executes, statement by statement,
in a private in-memory copy of the database. Nothing you write can reach the
real file. The copy **persists across Runs of the same question** -- so you can
run an `UPDATE`, then a `SELECT`, and see what it did -- and **Reset** throws it
away and starts again from the seeded data. Moving to another question also
starts fresh, so no question depends on what another one wrote. If your
script ends in a statement that returns rows -- a `SELECT`, or a `DELETE ...
RETURNING` -- the results pane shows that; otherwise it shows the question's
*probe* query, which is what **Check answer** compares. Check always grades a
fresh copy, so nothing you ran earlier can affect the grade. The status bar
reports how many statements ran and how many rows changed; on question 24 that
count is the difference between right and wrong.

**Driver statements.** Questions 27 and 28 run statements of their own *after*
yours -- two cancellations and a repeat that your counter must ignore, and
three salary updates of which your trigger must refuse exactly one. A refusal
is reported in the status bar as what it is, not as an error.

| # | Construct |
|---|---|
| 23 | `DELETE` in foreign-key order, with `RETURNING` -- children before parents |
| 24 | `UPDATE ... FROM` a grouped subquery, and the guard that keeps it to the blanks |
| 25 | `WITH ... INSERT` into a table with a primary key and NOT NULLs, minding the grain |
| 26 | two transactions -- `COMMIT` ends one, and a `ROLLBACK` outside any is an error |
| 27 | a trigger that maintains a summary count, gated by `WHEN` on `OLD` and `NEW` |
| 28 | a `BEFORE UPDATE` trigger with `RAISE()`, where `OLD` and `NEW` must not be swapped |
| 29 | an unpivot saved as a view, and the copy-paste slip a view hides |
| 30 | a recursive CTE feeding an `INSERT`, and where its stop condition lands |

**A trigger runs once per row.** `NEW` is the row being written, `OLD` the row
being replaced or removed; an UPDATE trigger has both, and the `WHEN` clause
compares them. `RAISE(ABORT, 'message')` is a function; a `SELECT` that
produces a row executes it, so the `WHERE` or `WHEN` is the condition.

## Things the data does on purpose

- **Unit 12 has 399 rows in `service_units`**, which is why question 23
  cannot delete it first.
- **163 incidents have no quantified delay**, and question 24 fills
  them from the timetable.
- **Some services sold no tickets** -- question 25's LEFT JOIN is what keeps
  them in the service count.
- **Service 79 is already cancelled**, and question 27 re-cancels it to see
  whether your counter notices.
- **Staff 4 earns 40,713**, the salary question 28 sets it to again.
- **Two stations opened on the same day** (question 13), and **two pairs of
  services depart at the same minute on 2025-04-07** (questions 4 and 22), so
  the tiebreaks are real.
- **The timetable is not flat.** Services per day run from 6 to
  27, thinner at weekends and in winter.

## 1 - Warm-up (3)

Three questions on one or two tables: a decade band from integer division,
COUNT(*) against COUNT(column), and two conditions that belong in HAVING.

1. **The fleet by decade** (Q612)

   How many units were built in each decade, with their average seats to the
   nearest seat. Label the decade by its first year: 1990, 2000, 2010.

   *Return: decade, units, avg_seats*

2. **Delay by line** (Q613)

   One row per line: how many incidents, how many of them have a quantified
   delay, and the average delay of those to one decimal.

   Incidents whose delay was never quantified must not pull the average down.

   *Return: line_id, incidents, quantified, avg_delay*

3. **Well-served towns** (Q614)

   Towns with three or more stations, at least one of which is step-free, with
   the station count and the step-free count.

   Both conditions describe the town.

   *Return: town, stations, step_free_stations*

## 2 - Sequences and strings (4)

`stops` is keyed on (service_id, stop_seq). Top-1 per service with a tiebreak, a
word count with no split function, LEAD along a day's departures, and a UNION
that must not double anyone.

4. **Where each service lost the most time** (Q615)

   For every service that ran on 2025-04-07: the stop at which it was latest
   -- actual arrival minus scheduled, in minutes -- and by how much. One row
   per service; when two stops tie, the earlier one.

   Unrecorded arrivals do not count.

   *Return: service_id, stop_seq, late_minutes*

5. **Counting the words in a name** (Q616)

   Every station with the length of its name in characters and in words. There
   is no split function: count the spaces.

   *Return: station_id, chars, words*

6. **Until the next departure** (Q617)

   Line 2's services on 2025-04-07 in departure order, each with the NEXT
   one's departure time and the minutes until it. The last service of the day
   has neither.

   *Return: service_id, depart_time, next_depart, minutes_until*

7. **Everyone with authority** (Q618)

   Staff who are managers by role OR who have someone reporting to them --
   each person once, whichever way they qualify. Ordered by staff_id.

   Some managers also have reports; they must not appear twice.

   *Return: staff_id, name*

## 3 - Unpivot and set ops (3)

Twelve quarters as rows with a share of the year, a self-join counted per town,
and INTERSECT then EXCEPT across three lines.

8. **Each quarter's share of its year** (Q619)

   Network-wide footfall for each quarter of each year as ROWS, with the
   percentage of that YEAR's total it is, to two decimals. Twelve rows,
   labelled q1 to q4.

   *Return: year, quarter, footfall, pct_of_year*

9. **Pairs of stations in the same town** (Q620)

   For every town with at least two stations, how many PAIRS of stations it
   has -- a town with three stations has three pairs, one with four has six.

   *Return: town, pairs*

10. **On two lines, never on a third** (Q621)

    Units that have worked on BOTH line 2 and line 3 but have never worked on
    line 1.

    *Return: unit_id*

## 4 - Dates and times (4)

A month key that survives a year boundary, text against integer in a CASE,
julianday for days between dates, and a modifier chain to the first full week.

11. **Cancellation rate by month** (Q622)

    For each month of the timetable: services scheduled, services cancelled,
    and the cancellation rate as a percentage to one decimal. Eighteen rows --
    January 2025 and January 2026 are different months.

    *Return: month, services, cancelled, pct*

12. **Departures by time of day** (Q623)

    How many services depart in the morning (before 10:00), at midday (10:00
    up to but not including 14:00) and later.

    Three rows, labelled 'morning', 'midday', 'later'.

    *Return: band, services*

13. **Days since the previous opening** (Q624)

    Every station in the order it opened, with the number of days since the
    previous station opened. The first has none. Two stations opened on the
    same day; order those by station_id, and the second shows 0.

    *Return: station_id, opened_on, days_since_previous*

14. **The first full week of each month** (Q625)

    How many services ran in the first full week of each month: the first
    Monday through the Sunday after it. Eighteen months.

    Modifiers: 'start of month', then 'weekday 1' for the Monday, which stays
    put if the 1st already is one.

    *Return: month, services*

## 5 - Joins and grain (4)

A date filter that must live in ON, two children of one parent at different
grains, an absence an inner join cannot find, and COUNT(DISTINCT) as an all-or-
none test.

15. **Every unit's June 2025** (Q626)

    Every unit of rolling stock with the number of services it worked in June
    2025. Units that worked none -- and the five that have never worked at all
    -- must appear with 0, so all 50 rows come back.

    *Return: unit_id, workings*

16. **Seats offered and tickets sold, per line** (Q627)

    For each line: the total seats it has run -- every unit on every service
    -- and the total tickets sold on it.

    Units and tickets both hang off `services`, at different grains. Joined
    together they multiply.

    *Return: line_id, seats, tickets*

17. **Services that sold nothing** (Q628)

    Services scheduled on 2025-05-08 that sold no tickets at all. Write it
    with an outer join.

    *Return: service_id, line_id*

18. **Sold only one class** (Q629)

    Services in January 2025 that sold at least four tickets, all of the same
    class -- with the ticket count and that class.

    *Return: service_id, tickets, class*

## 6 - Window functions (4)

A centred frame, top-2 per model, a share of a town without a GROUP BY, and
ROW_NUMBER against RANK when the number is a running order.

19. **A centred three-month average** (Q630)

    Tickets sold per month, each with the average of that month, the one
    before and the one after, to one decimal. At the two ends, average what is
    there.

    *Return: month, tickets, centred_avg*

20. **The two hardest-working units of each model** (Q631)

    For each model, its two units with the most workings -- rows in
    service_units -- and the count. Fourteen rows; ties by the lower unit_id.

    *Return: model, unit_id, workings*

21. **Each station's share of its town** (Q632)

    Every station's 2025 footfall and what percentage of its TOWN's 2025
    footfall that is, to two decimals. A town with one station reads 100.

    *Return: station_id, town, footfall, pct_of_town*

22. **Running order for the day** (Q633)

    Every service scheduled on 2025-04-07, cancelled or not, numbered in
    departure order from 1. Two pairs depart at the same minute; number those
    by service_id, so the numbers run 1 to 24 with no gaps or repeats.

    *Return: position, service_id, depart_time*

## 7 - Changing the data (8)

Writable questions: your script runs in a sandbox copy of the database and the
question's probe query reads the result. DELETE in foreign-key order, UPDATE ...
FROM, a CTE feeding an INSERT, two transactions, two triggers, an unpivot view
and a recursive INSERT -- what SQLite has instead of a procedural language.

23. **Scrap a unit that has worked** (Q634)

    Unit 12 is being scrapped. Delete it from `rolling_stock` -- but it has
    hundreds of rows in `service_units`, and with foreign keys on, a
    referenced row cannot go. Remove those first, then the unit.

    Add RETURNING unit_id, model to the second DELETE so the results pane
    shows what went.

    *Checked: how many units remain, and how many service_units rows still name unit 12*

24. **Borrow a delay from the timetable** (Q635)

    163 incidents have no delay_minutes. For each, use the worst lateness
    recorded at any stop of its service -- actual arrival minus scheduled, in
    whole minutes -- as the delay. Incidents that already have a delay keep
    it.

    One UPDATE ... FROM, with the per-service worst lateness as a grouped
    subquery in the FROM.

    *Checked: incidents, how many are quantified, the delay total, and how many delays are under ten minutes*

25. **A summary table, built from a CTE** (Q636)

    Create `line_summary (line_id INTEGER PRIMARY KEY, services, tickets,
    revenue_pence)`, all NOT NULL, and fill it: per line, how many services it
    scheduled, how many tickets it sold and the revenue. Every line has all
    three.

    Use a WITH clause in front of the INSERT to compute the rows, and mind the
    grain: services with no tickets still count as services.

    *Checked: SELECT * FROM line_summary*

26. **Commit one, roll back the other** (Q637)

    Two separate transactions. In the first, give every driver a 5% raise and
    COMMIT. In the second, give every guard 5% -- then think better of it and
    ROLLBACK.

    Whole pounds: CAST(ROUND(salary * 1.05) AS INTEGER). Each transaction
    needs its own BEGIN; there is no such thing as rolling back a statement
    that was never inside one.

    *Checked: total salary by role*

27. **A count that keeps itself right** (Q638)

    Create `line_cancellations (line_id INTEGER PRIMARY KEY, cancelled INTEGER
    NOT NULL)` filled with each line's current cancellation count, then a
    trigger that adds one whenever a service's cancelled flag goes from 0 to 1
    -- and does nothing when a service already cancelled is 'cancelled' again.

    After your script, the question cancels services 5 and 6 (line 2), then
    re-cancels service 79 (line 3), which already was.

    *Checked: the table, in line order*

28. **No pay cuts** (Q639)

    Write a trigger that refuses any UPDATE that would LOWER a member of
    staff's salary. Raises go through; so does setting a salary to the value
    it already has.

    After your script, the question runs three updates: staff 2 to 50000 (a
    raise), staff 3 to 30000 (a cut), staff 4 to its current 40713. Exactly
    one should be refused.

    *Checked: the three salaries*

29. **The footfall table, long** (Q640)

    Create a view `footfall_long (station_id, year, quarter, footfall)` that
    presents station_footfall one row per quarter, with quarter as the number
    1 to 4. 720 rows when selected.

    *Checked: COUNT(*), SUM(footfall) and COUNT(DISTINCT quarter) over the view*

30. **A calendar table for July** (Q641)

    Create a table `days (day TEXT PRIMARY KEY)` and fill it with every date
    in July 2025, generated -- not typed -- by a recursive CTE feeding an
    INSERT. 31 rows.

    *Checked: how many rows, the first and the last*

## The one concept with no question here

**Alias scope follows clause order.** SQLite accepts a `SELECT` alias in `WHERE`
where Postgres and SQL Server do not, so it cannot be graded here. Keep the rule
for portability, and reach for a CTE when you want a real column to filter on.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
611 retired ones.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
