# SQL practice exercises

Thirty questions on the repair-depot schema, re-seeded again so no answer from
the previous set carries over.

This set is deliberately **easier** than the last one, and there is **no
recursion in it at all** -- that mechanism has had two sets in a row. Two rules
shaped every question:

- **one concept each.** Nothing stacks a window function on top of a self-join
  on top of a date trick. If you know the one idea being drilled, the query is
  short -- no reference solution in the set is longer than six lines.
- **the prompt states the grain.** Where the last set left you to work out what
  one row meant, these say it outright: "one row per depot", "one row per
  month", "all 14 technicians come back".

**Nine of the thirty are window functions**, the area that has come up most:

| The idea | Questions |
|---|---|
| `PARTITION BY` -- present, absent, or wrong | 3, 8 |
| The frame: running vs rolling vs whole-table | 1, 5, 7 |
| Ranking, and what happens on a tie | 4, 6 |
| `LAG` and `LEAD` along a series | 2, 8 |
| A window instead of a `GROUP BY`, keeping the detail rows | 9 |

The other twenty-one keep the breadth, one idea at a time: `COUNT(*)` vs
`COUNT(col)`, `WHERE` vs `HAVING`, conditional aggregation, outer joins that
keep the zeroes, self-joins, anti-joins, `EXISTS` and `NOT EXISTS`,
correlation, `= NULL` and `<>` against nullable columns, `julianday` and
`strftime`, `EXCEPT` and `INTERSECT`, fan-out from two child tables,
`SUM(a * b)`, and the order of `CASE` branches.

**Work through them in the GUI**: double-click `SQL Practice.bat` on Windows or
`sql-practice.command` on macOS/Linux, or run `python gui.py`. It grades your
answer against the expected result and, when you get it right, tells you which
mistake the question was built to catch. Progress is saved between sessions.

To run queries by hand instead:

```
python q.py "SELECT ..."
```

or `python q.py` on its own for an interactive prompt (blank line runs,
`\q` quits).

The tables: `regions`, `customers`, `sites`, `machines`, `depots`,
`technicians`, `contracts`, `parts`, `work_orders`, `parts_used`,
`labor_entries`, `inspections`, `part_stock`, `invoices`. See
[schema.sql](schema.sql).

## Things the data does on purpose

- **14 technicians in a 3-level reporting chain.** One reports to nobody
  (`supervisor_id` NULL); 10 supervise nobody. Deep enough that a single
  self-join cannot reach the bottom, and that only the person at the top has
  anyone *indirectly* beneath them.
- **`NOT IN` is a trap here.** `supervisor_id` contains a NULL, and so does
  `work_orders.technician_id` -- 15 work orders have nobody assigned. Any
  `x NOT IN (SELECT that_column ...)` returns nothing at all.
- **Invoices run one month past the work.** 19 months have an invoice issued
  and only 18 have a work order opened, so the two calendars are not the same
  set -- which is what `EXCEPT` is for.
- **Only 6 of the 10 score bands are populated.** A `GROUP BY` can only return
  groups the data already contains; the empty bands do not appear at all.
- **Dates are TEXT.** `closed_at - opened_at` does not error -- it coerces to
  numbers and returns nonsense. Use `julianday()` for arithmetic; `<` and `>`
  on ISO dates are fine as strings.
- **18 distinct months** of work orders, so `strftime('%m', ...)` collapses
  two Januaries into one bucket.
- **`closed_at` is NULL for cancelled jobs as well as open ones.** It tells
  you a job has no end date, not why.
- **Invoice `status` is UPPERCASE** (`PAID`, `PENDING`, `OVERDUE`, `VOID`),
  and 2 invoices are VOID -- so `status <> 'PAID'` is wider than "unpaid".
- **14 distinct labour rates and 4 distinct discounts**, so `SUM(h) * rate`
  and `SUM(h * rate)` genuinely disagree.
- **Some parts are stocked but never fitted (2), some fitted but stocked
  nowhere (3), and two are neither** -- three different sets, on purpose.
  Four parts have never been fitted at all.
- **`discount` is a rate**, not a percentage: `quantity * unit_price *
  (1 - discount)`.
- **Nullable on purpose**: `cert_level` (4), `response_hours` (10),
  `reorder_level` (19), `last_counted_at`, `warranty_until` (21), `score` (29),
  `weight_grams` (2), `account_tier` (3), `end_date` (11), `paid_on`, and
  `technician_id` on work orders (15).

## Window functions (9)

A calculation that sees a set of rows around each row without collapsing
them. PARTITION BY says which rows it may see, ORDER BY orders them inside
that set, and a ROWS clause narrows it further. Nine questions, each
isolating one of those three.

1. **Invoicing, month by month and so far** (Q222)

   One row per calendar month in which any invoice was issued: the
   month, what was invoiced in it, and the running total of everything
   invoiced up to and including that month.

   Months are 'YYYY-MM'. The running total on the last month equals the
   total of every invoice in the table.

   *Return: month, month_total, running_total*

2. **Month on month** (Q223)

   One row per month in which any work order was opened: the month, how
   many were opened, and the change from the month before.

   The earliest month has no month before it, so its change is NULL --
   leave it NULL rather than turning it into 0.

   *Return: month, work_orders, change*

3. **The latest job on each machine** (Q224)

   For every machine that has ever had a work order, its most recent
   one. One row per machine -- machines with no work orders at all do
   not appear.

   No machine has two work orders opened on the same date, so 'most
   recent' is never a tie.

   *Return: machine_id, work_order_id, opened_at*

4. **Busiest at each depot, ties and all** (Q225)

   The busiest technician at each depot, counting work orders they are
   the assigned technician on.

   One depot has two technicians tied on the same count. Both of them
   must appear -- five rows in total, not four.

   *Return: depot_id, technician_id, name, work_orders*

5. **Three-month rolling average** (Q226)

   One row per month in which any work order was opened: the month, how
   many were opened, and the average over that month and the two months
   before it.

   The first month averages just itself, the second averages two
   months, and every month after that averages three.

   *Return: month, work_orders, rolling_avg*

6. **Quartiles of workload** (Q227)

   Every technician who has logged any labour, with their total hours
   and which quarter of the workforce they fall into by hours: 1 for
   the busiest quarter, 4 for the quietest.

   Fourteen technicians split into four groups, so the first two groups
   get four each and the last two get three.

   *Return: technician_id, total_hours, quartile*

7. **Share of the invoiced total** (Q228)

   One row per work-order priority: the priority, the total invoiced on
   work orders of that priority, and that total as a percentage of
   everything invoiced.

   Only work orders that actually have an invoice count. The four
   percentages add up to 100.

   *Return: priority, invoiced, pct_of_total*

8. **How long until the machine is seen again** (Q229)

   Every work order, with the number of whole days until the NEXT work
   order opened on the same machine.

   The most recent work order on each machine has nothing after it, so
   its gap is NULL. One row per work order -- all 180.

   *Return: machine_id, work_order_id, opened_at, days_to_next*

9. **Each entry against its technician's average** (Q230)

   Every labour entry dated in January 2026, with the average hours of
   the January entries belonging to that same technician.

   One row per entry, not one per technician: the same average repeats
   down each technician's entries.

   *Return: entry_id, technician_id, hours, tech_avg*

## Aggregation (4)

GROUP BY and the functions that ride on it. Four questions on the parts
that are easy to get subtly wrong rather than outright wrong.

10. **Certified and not** (Q231)

    One row per depot: how many technicians it has, and how many of them
    have a certification level recorded.

    Four technicians company-wide have no cert_level, so the two counts
    differ at the depots those technicians work from.

    *Return: depot_id, depot_name, technicians, certified*

11. **Which priorities were busy in 2026** (Q232)

    Counting only work orders opened on or after 2026-01-01, one row per
    priority, keeping the priorities with at least 15 of them.

    Two of the four priorities clear the bar.

    *Return: priority, work_orders*

12. **Invoice status by priority** (Q233)

    One row per work-order priority, with the number of its invoices in
    each of three statuses side by side as columns.

    Every priority has at least one PAID invoice; some have zero PENDING
    or zero OVERDUE, and those must show as 0.

    *Return: priority, paid, pending, overdue*

13. **Average score, where there is one** (Q234)

    One row per inspection result: how many inspections had that result,
    how many of them carry a score, and the average of the scores that
    exist.

    Plenty of inspections have no score at all. The average must be over
    the scored ones only.

    *Return: result, inspections, scored, avg_score*

## Joins (4)

Four questions where the answer hinges on the rows that DON'T match -- the
unused part, the technician with no critical jobs, the machine nobody has
touched -- plus one on pairing a table with itself.

14. **Every part, used or not** (Q235)

    One row for every part in the catalogue: its id, its name, and the
    number of DISTINCT work orders it has been used on.

    Four parts have never been used on anything. They must appear with
    0, so all 40 parts come back.

    *Return: part_id, name, work_orders*

15. **Critical jobs per technician** (Q236)

    One row for every technician: id, name, and how many CRITICAL work
    orders they are the assigned technician on.

    Five technicians have never been assigned one. They must appear with
    0, so all 14 technicians come back.

    *Return: technician_id, name, critical_jobs*

16. **Hired the same year, same depot** (Q237)

    Pairs of technicians who work from the same depot and were hired in
    the same calendar year.

    Each pair once, not twice: Ann with Bob, never also Bob with Ann,
    and nobody paired with themselves. Three pairs exist.

    *Return: depot_id, name_a, name_b*

17. **Machines nobody has touched** (Q238)

    Every machine that has never had a single work order raised against
    it.

    Write it as an outer join that keeps the non-matches, rather than
    with NOT IN. There are 27 such machines.

    *Return: machine_id, serial*

## Subqueries & EXISTS (3)

Asking a question about a row without changing what a row is. Three
questions: EXISTS instead of a join, NOT EXISTS instead of NOT IN, and a
subquery that has to be re-evaluated per row.

18. **Customers still under warranty somewhere** (Q239)

    Every customer who owns at least one machine whose warranty runs
    beyond 2026-01-01.

    Machines belong to sites and sites belong to customers. One row per
    customer, however many qualifying machines they own -- three
    customers own two apiece.

    *Return: customer_id, name*

19. **Never on a critical job** (Q240)

    Every technician who has never been the assigned technician on a
    critical work order. Five of the fourteen qualify.

    Watch out: three critical work orders have no technician assigned at
    all, which is what makes the obvious answer wrong.

    *Return: technician_id, name*

20. **Dear for its own category** (Q241)

    Every part costing more than the average unit_cost of the parts in
    ITS OWN category -- not more than the average across the whole
    catalogue.

    One row per part.

    *Return: part_id, name, category, unit_cost*

## NULLs (2)

Two questions on the same fact from opposite directions: a comparison
against NULL is neither true nor false, so it never matches and never
excludes -- it just quietly drops the row.

21. **Ended, running, or open-ended** (Q242)

    Classify every contract into one of three states as of 2026-08-01,
    and count them:

        'open-ended' if end_date is missing entirely
        'ended'      if end_date is before 2026-08-01
        'active'     otherwise

    All 34 contracts land in exactly one state.

    *Return: state, contracts*

22. **Everyone who is not level 5** (Q243)

    Count technicians by certification level, excluding level 5, and
    counting the ones with NO certification level as 'none'.

    Twelve of the fourteen technicians are not level 5 -- four of them
    because they have no level at all.

    *Return: level, technicians  (level is text: '1'..'4' or 'none')*

## Dates (3)

Dates are TEXT in SQLite. Three questions on doing arithmetic on them,
naming parts of them, and grouping by them without losing the year.

23. **The five slowest jobs to close** (Q244)

    The five closed work orders that took the longest from opening to
    closing, longest first.

    Days must be a whole number. Break ties on days by work_order_id
    ascending, so the five are unambiguous.

    *Return: work_order_id, opened_at, closed_at, days*

24. **Which day of the week is busiest** (Q245)

    How many work orders were opened on each day of the week, across the
    whole data set. Seven rows, Sunday first.

    Name the day rather than numbering it.

    *Return: day_name, work_orders*

25. **Inspections by month, across two years** (Q246)

    One row per calendar month in which any inspection happened: the
    month as 'YYYY-MM', and how many inspections it held.

    The data spans two calendar years, so February 2025 and February
    2026 are different months and must not be added together.

    *Return: month, inspections*

## Set operations (2)

Stacking two result sets rather than joining them. Two questions: one on
EXCEPT having a direction, one on INTERSECT not being UNION.

26. **Invoiced in a month nothing opened** (Q247)

    Months in which at least one invoice was issued but NO work order
    was opened. Months are 'YYYY-MM'.

    Invoices trail the work that produced them, so this catches the tail
    end of the data set. Exactly one month qualifies.

    *Return: month*

27. **Low on stock and needed for critical work** (Q248)

    Parts that are BOTH below their reorder level in at least one depot
    AND have been used on at least one critical work order.

    Only stock lines that actually have a reorder_level count. Three
    parts satisfy both conditions.

    *Return: part_id, name*

## Grain (2)

What one row means. Two questions: what happens when two child tables meet
over the same parent, and where the multiplication goes.

28. **Parts and labour on the critical jobs** (Q249)

    One row per CRITICAL work order, with what was spent on parts and
    what was spent on labour.

    Parts spend is quantity * unit_price * (1 - discount) summed; labour
    is hours * rate summed. A job with none of one or the other shows 0,
    not NULL. All 21 critical work orders appear.

    *Return: work_order_id, parts_cost, labour_cost*

29. **Spend by part category** (Q250)

    One row per part category that has ever been used, with the total
    spent on it.

    Each parts_used line is worth quantity * unit_price * (1 -
    discount), and every line must be priced on its own quantity, price
    and discount.

    *Return: category, spend*

## General (1)

One question on CASE.

30. **Machines by age band** (Q251)

    Put every machine into one of three bands by installed_on and count
    them:

        '2024 or later'  installed on or after 2024-01-01
        '2021 to 2023'   installed on or after 2021-01-01
        'before 2021'    everything else

    All 98 machines land in exactly one band.

    *Return: band, machines*

## The one concept with no question here

**Alias scope follows clause order.** Logical order is `FROM` -> `WHERE` ->
`GROUP BY` -> `HAVING` -> window functions -> `SELECT` -> `ORDER BY` ->
`LIMIT`, and a name only exists after the step that creates it. Postgres and
SQL Server reject a SELECT alias in `WHERE`; SQL Server and Oracle reject one
in `GROUP BY`.

There is no graded question for this because **SQLite will not punish you for
it**. It happily accepts an alias in `WHERE`:

```sql
SELECT unit_cost * 2 AS d FROM parts WHERE d > 100   -- runs fine in SQLite
```

Keep the rule for portability, and reach for a CTE when you want a real
column to filter or group by -- which is also how the top-N-per-group
questions above have to be written, since a window function cannot appear in
`WHERE` on any engine.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
221 retired ones. New questions must not repeat anything in that ledger.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
