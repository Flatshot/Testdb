# SQL practice exercises

Thirty questions on the repair-depot schema, re-seeded again so no answer from
the previous set carries over.

This set was built from the mistakes made working through the last one. It is
weighted half toward what actually went wrong and half toward keeping breadth.

**What went wrong last time, and what drills it here:**

| The mistake | Questions |
|---|---|
| Aggregating at the wrong level, or not at all | 7, 8, 9 |
| `SUM(a) * b` where `SUM(a * b)` was meant | 11, 26, 27 |
| A `LEFT JOIN` filtered in `WHERE`, and `AVG` over missing values | 12, 13 |
| Answering "at least one" when the question said "every" | 14, 23 |
| An `EXISTS` that forgot to correlate | 15 |
| `PARTITION BY` missing, or present when it should not be | 16, 18 |
| The frame default on a window function | 17 |

The six **recursion** questions deliberately vary the *anchor*, which is where
the mechanism is easiest to get wrong:

1. the root's **direct reports** -- not the root itself (branch labels)
2. every row **paired with itself** (how deep the tree goes)
3. walking **upward**, collecting ancestors to sum over
4. a bare **literal**, generating a month spine for two measures at once
5. **one row per parent row**, each expanding into its own series
6. a spine **CROSS JOINed** to a real dimension, for the full grid

The last three are the half of recursion that is not a hierarchy at all, and
the half a `GROUP BY` cannot reach: it can only return groups the data already
contains, so quiet months and empty depot-months silently do not exist.

The rest keeps the breadth: set operations, window frames, date arithmetic,
self-joins and silent sampling.

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
- **`NOT IN` is a trap here.** `supervisor_id` contains a NULL, so
  `x NOT IN (SELECT supervisor_id ...)` returns nothing at all.
- **Only 7 of the 18 months have a critical work order.** The other 11 exist
  in no table, which is what makes generating a month series necessary rather
  than decorative.
- **Only 6 of the 10 score bands are populated.** Same lesson, without dates.
- **Dates are TEXT.** `closed_at - opened_at` does not error -- it coerces to
  numbers and returns nonsense. Use `julianday()` for arithmetic; `<` and `>`
  on ISO dates are fine as strings.
- **18 distinct months** of work orders, so `strftime('%m', ...)` collapses
  two Januaries into one bucket.
- **`closed_at` is NULL for cancelled jobs as well as open ones.** It tells
  you a job has no end date, not why.
- **Invoice `status` is UPPERCASE** (`PAID`, `PENDING`, `OVERDUE`, `VOID`),
  and 7 invoices are VOID -- so `status <> 'PAID'` is wider than "unpaid".
- **14 distinct labour rates and 4 distinct discounts**, so `SUM(h) * rate`
  and `SUM(h * rate)` genuinely disagree.
- **Some parts are stocked but never fitted (2), some fitted but stocked
  nowhere (4), and two are neither** -- three different sets, on purpose.
- **`discount` is a rate**, not a percentage: `quantity * unit_price *
  (1 - discount)`.
- **Nullable on purpose**: `cert_level` (4), `response_hours`,
  `reorder_level`, `last_counted_at`, `warranty_until` (24), `score` (24),
  `weight_grams`, `account_tier` (9), `paid_on`, `technician_id` on work
  orders.

## Recursive CTEs (6)

An anchor row, then a step that joins back to the CTE itself, run over and
over until a pass returns nothing. Six questions, easiest first -- the last
two generate rows rather than walking a hierarchy.

1. **The whole chain, written out** (Q162)

   For every technician, their reporting path from the very top down to
   them, as one string joined with ' > '.

   The technician at the top is just their own name. Everyone else is
   their supervisor's path with their own name on the end -- so a third-
   level technician shows all three names.

   *Return: technician_id, name, path*

2. **Everyone above Nadia Kaur** (Q163)

   Nadia Kaur and every technician above her in the reporting chain, up
   to the one who reports to nobody, with how many steps up each one is.

   Nadia herself is 0 steps, her supervisor is 1, and so on.

   *Return: technician_id, name, steps_up*

3. **Every manager, everyone under them** (Q164)

   Every pair of technicians where the first supervises the second,
   directly or through any number of levels, with how many levels apart
   they are.

   A direct report is 1 level. Nobody is paired with themselves.

   *Return: supervisor_id, subordinate_id, levels*

4. **How many people are under you** (Q165)

   For every technician, how many people sit below them in the chain at
   any depth -- their direct reports, plus those people's reports, and so
   on.

   Technicians who supervise nobody appear with 0.

   *Return: technician_id, name, headcount_below*

5. **Score bands, including the empty ones** (Q166)

   Inspection scores bucketed into bands of ten -- 0-9, 10-19, and so on
   up to 90-99 -- with how many inspections fall in each band.

   All ten bands must appear, including the ones no inspection reached.
   Inspections with no score recorded belong to no band.

   *Return: band_low, inspections*

6. **Critical months, including the quiet ones** (Q167)

   For every calendar month from 2025-02 to 2026-07 inclusive, how many
   critical work orders were opened in it.

   Every month in that window appears, including the many where no
   critical job was opened at all -- those show 0.

   *Return: month, critical_work_orders*


## Set operations (2)

Comparing two SETS of rows, not filtering one. Remember that UNION,
INTERSECT and EXCEPT all deduplicate; only UNION ALL does not.

7. **Stocked in Leeds, not in Coventry** (Q168)

   Parts that Leeds Central holds a stock line for and Coventry Hub does
   not.

   This compares two SETS of parts. A part stocked at both depots must
   not appear, and it makes no difference how many are on hand.

   *Return: part_id, name*

8. **Both kinds of contract** (Q169)

   Customers who hold at least one contract that agreed a response time
   and at least one that did not.

   *Return: customer_id, name*


## Subqueries & EXISTS (3)

Asking a question about each row's own group, and proving something about
EVERY related row by failing to find a counterexample.

9. **Machines nobody has touched** (Q170)

   Machines that have never had a work order raised against them, with
   the site they stand on.

   *Return: machine_id, model, site_name*

10. **Never failed an inspection** (Q171)

   Machines that have been inspected at least once and passed every time
   -- no 'fail' and no 'conditional' among their inspections.

   Machines never inspected at all do not qualify.

   *Return: machine_id, model*

11. **Costlier than its category average** (Q172)

   Parts whose unit cost is above the average unit cost of the parts in
   their OWN category -- not the average across all parts.

   *Return: part_id, name, category, unit_cost*


## Conditional aggregation (3)

Routing rows into columns with CASE inside the aggregate, so one pass
produces several counts and nothing is thrown away first.

12. **Counted and uncounted stock** (Q173)

   For each depot: how many stock lines it holds, how many have ever been
   counted, and how many never have.

   The last two must add up to the first.

   *Return: depot_id, name, stock_lines, counted, never_counted*

13. **Close rate by priority** (Q174)

   For each priority: how many work orders carry it, how many of those
   are closed, and the closed share as a fraction between 0 and 1.

   *Return: priority, work_orders, closed, close_rate*

14. **Every status in one row** (Q175)

   For each technician who has been assigned any work order: how many of
   their work orders are open, how many closed, and how many cancelled --
   three counts on one row.

   A technician with none of a given status shows 0 for it.

   *Return: technician_id, name, open, closed, cancelled*


## Dates & gaps (3)

julianday() for arithmetic, and care about what a NULL date means.

15. **The jobs that dragged** (Q176)

   Work orders that took more than 14 days to close, with how many days
   they took.

   Only jobs that actually closed count. The gap is closed_at minus
   opened_at, in days.

   *Return: work_order_id, opened_at, closed_at, days_open*

16. **Out of warranty when it broke** (Q177)

   Work orders opened after the machine's warranty had already expired.

   Machines with no warranty date recorded are not known to be out of
   warranty, so they do not count.

   *Return: work_order_id, machine_id, opened_at, warranty_until*

17. **How long invoices take to pay** (Q178)

   Across the invoices that have been paid, the average number of days
   between being issued and being paid, and the longest such gap.

   *Return: invoices_paid, avg_days_to_pay, max_days_to_pay*


## Window frames (4)

Aggregates that do not collapse the rows. Mind PARTITION BY (where the
sequence restarts) against ORDER BY (what 'previous' means) -- and that
adding ORDER BY to a window aggregate silently reframes it.

18. **Invoiced so far this year** (Q179)

   Invoice value per calendar month, with a running total that
   accumulates from the first month onwards.

   The running total on the last month equals the whole invoice book.

   *Return: month, invoiced, running_total*

19. **Ranked inside your own depot** (Q180)

   Every technician who has logged labour, with their total hours and
   their rank by hours WITHIN their own depot -- the busiest technician
   at each depot is rank 1.

   Break ties on technician_id ascending.

   *Return: depot_id, technician_id, name, hours, rank_in_depot*

20. **Share of the category** (Q181)

   For each part that has ever been fitted: its total spend, and what
   fraction of its CATEGORY's total spend that represents, as a value
   between 0 and 1.

   Spend on a part is quantity * unit_price * (1 - discount), summed over
   every time it was fitted.

   *Return: category, part_id, name, spend, share_of_category*

21. **Against the best in the depot** (Q182)

   Every technician who has logged labour, with their total hours, the
   highest total logged by anyone at their depot, and the difference
   between the two.

   The busiest technician at each depot shows a difference of 0.

   *Return: depot_id, technician_id, name, hours, depot_best, behind_by*


## Silent sampling (2)

The bare column under GROUP BY, in the arithmetic form that costs real
answers. When a per-row value feeds an aggregate, it goes inside.

22. **What the labour cost each depot** (Q183)

   For each depot, the total cost of all labour logged by the technicians
   based there.

   A visit costs hours * rate, and technicians are not all on the same
   rate.

   *Return: depot_id, name, labour_cost*

23. **Spend by category, after discount** (Q184)

   For each part category, the total spent on its parts across every work
   order.

   A line costs quantity * unit_price * (1 - discount), and lines are not
   all discounted the same.

   *Return: category, spend*


## Self-joins (2)

One table twice, under two aliases. The comparison operator decides whether
you get each pair once, twice, or paired with itself.

24. **Same region, same tier** (Q185)

   Every pair of customers in the same region holding the same account
   tier, with the region name and the tier.

   Each pair once, not twice, and nobody paired with themselves. List the
   lower customer_id first. Customers with no tier recorded do not pair
   up.

   *Return: region_name, account_tier, customer_a, customer_b*

25. **Same depot, same certification** (Q186)

   Every pair of technicians working out of the same depot who hold the
   same certification level, with the depot name and that level.

   Each pair once. List the lower technician_id first.

   *Return: depot_name, cert_level, technician_a, technician_b*


## Grain (2)

What one row of your intermediate result actually represents. Joining to a
child table multiplies the parent; only a GROUP BY puts it back.

26. **Parts and labour on one job** (Q187)

   For each closed work order that has both parts fitted and labour
   logged: the parts total, the labour total, and the two added together.

   Parts total is quantity * unit_price * (1 - discount) summed over the
   parts. Labour total is hours * rate summed over the visits.

   *Return: work_order_id, parts_total, labour_total, job_total*

27. **Contracts and sites per customer** (Q188)

   For each customer: how many contracts they hold and how many sites
   they run.

   Only customers who have at least one of each.

   *Return: customer_id, name, contracts, sites*


## NULLs (2)

Unknown is not zero, not empty, and not equal to itself.

28. **Still running, or merely undated** (Q189)

   For each account tier: how many contracts those customers hold, and
   how many of them have no end date recorded and so are still running.

   Customers who were never graded have no tier. That is a tier in its
   own right here and gets its own row.

   *Return: account_tier, contracts, still_running*

29. **Certified, uncertified, unknown** (Q190)

   For each depot: how many technicians it has, how many have a
   certification level recorded, and the average of those levels.

   Technicians with no level recorded still count toward the headcount,
   and must not drag the average down.

   *Return: depot_id, name, technicians, certified, avg_cert_level*


## General (1)

No single mechanism -- just the query the question asks for.

30. **Money still owed, by region** (Q191)

   For each region, the value of invoices that are not yet settled --
   status PENDING or OVERDUE -- and how many such invoices there are.

   An invoice belongs to the region of the site its machine stands on.
   Regions with nothing outstanding do not appear.

   *Return: region_name, unsettled_invoices, unsettled_value*


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
131 retired ones. New questions must not repeat anything in that ledger.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
