# SQL practice exercises

Thirty questions on the repair-depot schema, re-seeded with fresh data so no
answer from the previous set carries over.

The last set was weighted 15/30 toward **grain**. This one deliberately goes
broad instead: set operations, recursive CTEs, correlated subqueries,
conditional aggregation, date arithmetic and gap analysis, and the window
frames past a plain running total. Grain drops to two questions.

One thread carries over. Three questions drill the **bare column under
`GROUP BY`** -- where SQLite quietly hands back one arbitrary row's value
instead of raising an error. It is worth knowing that 'arbitrary' in practice
means *the first row scanned*, which is right often enough to survive a spot
check and wrong exactly when it matters.

**Work through them in the GUI**: double-click `SQL Practice.bat` on Windows or
`sql-practice.command` on macOS/Linux, or run `python gui.py`. It grades your answer against the expected result and, when
you get it right, tells you which mistake the question was built to catch.
Progress is saved between sessions.

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

- **14 technicians in a 3-level reporting chain.** One reports to
  nobody (`supervisor_id` NULL); 10 supervise nobody. Deep enough that a
  single self-join cannot reach the bottom.
- **`NOT IN` is a trap here.** `supervisor_id` contains a NULL, so
  `x NOT IN (SELECT supervisor_id ...)` returns nothing at all.
- **Dates are TEXT.** `paid_on - issued_on` does not error -- it coerces to
  numbers and returns 0. Use `julianday()` for arithmetic; `<` and `>` on ISO
  dates are fine as strings.
- **18 distinct months** of work orders, so `strftime('%m', ...)` collapses
  two Januaries into one bucket.
- **`closed_at` is NULL for cancelled jobs as well as open ones.** It tells
  you a job has no end date, not why.
- **Invoice `status` is UPPERCASE** (`PAID`, `PENDING`, `OVERDUE`, `VOID`).
- **Some parts are stocked but never fitted, some fitted but stocked
  nowhere, and two are neither** -- three different sets, on purpose.
- **`discount` is a rate**, not a percentage: `quantity * unit_price *
  (1 - discount)`.
- **Nullable on purpose**: `cert_level`, `response_hours`, `reorder_level`,
  `last_counted_at`, `warranty_until`, `score`, `weight_grams`,
  `account_tier`, `paid_on`, `technician_id` on work orders.

## Set operations (3)

UNION / UNION ALL / EXCEPT: comparing whole sets rather than filtering rows.

1. **Parts only the urgent jobs need** (Q132)

   Parts that have been fitted on at least one 'critical' work order and
   never on a 'low' one.

   This is a comparison between two SETS of parts, not a filter on
   individual rows: a part used on both must not appear.

   *Return: part_id, name, category*

2. **Two kinds of orphan** (Q133)

   One list of problem parts, each labelled with its problem:

   'stocked but never fitted' -- held in a depot, never used
   'fitted but stocked nowhere' -- used on jobs, held nowhere

   Parts that are neither stocked nor fitted have neither problem and must
   not appear.

   *Return: part_id, name, issue*

3. **Everything that happened, by month** (Q134)

   Depot activity per calendar month, counting two kinds of event together:
   every labour visit and every inspection.

   Two events on the same date are two events. A month with a visit and an
   inspection on the same day counts 2, not 1.

   *Return: month, events*

## Recursive CTEs (2)

Walking a chain of unknown depth -- an anchor row, then a step that joins the
table back to the CTE itself.

4. **How deep in the chain** (Q135)

   Every technician with their depth in the reporting chain. The one
   technician who reports to nobody is depth 1, anyone reporting to them is
   depth 2, and so on.

   The chain here runs three levels deep, so a single self-join cannot
   reach the bottom.

   *Return: technician_id, name, depth*

5. **Who is at the top of your chain** (Q136)

   For every technician, the name of the person at the very top of their
   reporting chain -- not their immediate supervisor, but the one who
   reports to nobody.

   That person is their own top, so they appear with their own name.

   *Return: technician_id, name, top_manager*

## Subqueries & EXISTS (3)

Correlated subqueries, EXISTS versus a join, and the NOT IN / NULL trap.

6. **Nobody reports to them** (Q137)

   Technicians who supervise nobody, with the depot they work from.

   Watch out: supervisor_id is NULL for the one technician at the top of
   the chain, and that NULL is inside the set you are testing against.

   *Return: technician_id, name, depot_name*

7. **Above your own priority's average** (Q138)

   Closed work orders whose labour cost is above the average labour cost of
   closed jobs at the SAME priority.

   Each job is measured against its own priority band, not against all
   jobs. Labour cost is hours * rate summed over the visits.

   *Return: work_order_id, priority, labor_cost*

8. **Customers with something overdue** (Q139)

   Customers who have at least one OVERDUE invoice, with their region.

   One row per customer, however many overdue invoices they have. An
   invoice reaches a customer through its work order, machine and site.

   *Return: customer_id, name, region_name*

## Conditional aggregation (3)

Turning rows into columns: SUM(CASE WHEN ... THEN 1 ELSE 0 END) rather than a
WHERE filter.

9. **Stock policy at a glance** (Q140)

   For each depot, three counts of its stock lines in one row: how many are
   below their reorder level, how many are at or above it, and how many
   have no reorder policy set at all.

   The three counts must add up to the depot's total stock lines.

   *Return: depot_id, name, below, at_or_above, no_policy*

10. **Job status by priority, side by side** (Q141)

   For each priority, how many work orders are open, how many closed and
   how many cancelled -- as three columns on one row per priority, not
   three rows.

   *Return: priority, open_jobs, closed_jobs, cancelled_jobs*

11. **Critical hours versus the rest** (Q142)

   For each technician who has logged labour: hours logged on critical work
   orders, and hours logged on everything else.

   Every technician who has logged anything appears, including those who
   have never touched a critical job -- they show 0.

   *Return: technician_id, name, critical_hours, other_hours*

## Dates & gaps (4)

Bucketing by month, arithmetic on TEXT dates, and gaps between consecutive
events.

12. **Work opened by month** (Q143)

   How many work orders were opened in each calendar month, across the
   whole data set.

   The data spans 18 distinct months, so 18 rows -- January 2025 and
   January 2026 are different months.

   *Return: month, work_orders*

13. **Days between callouts** (Q144)

   For machines with at least 3 work orders: every work order except each
   machine's first, with the number of days since the previous work order
   ON THAT MACHINE.

   Order within a machine by opened_at, then work_order_id.

   *Return: machine_id, work_order_id, opened_at, days_since_previous*

14. **Slow payers** (Q145)

   Invoices that were paid more than 30 days after they were issued, with
   how many whole days they took.

   Unpaid invoices have paid_on NULL and are not late -- they are
   unresolved. Leave them out.

   *Return: invoice_id, issued_on, paid_on, days_to_pay*

15. **Month on month** (Q146)

   Work orders opened per calendar month, with the change from the previous
   month -- this month's count minus last month's.

   The earliest month has no previous month, so its change is NULL.

   *Return: month, work_orders, change_from_previous*

## Window frames (4)

NTILE, LAG, LAST_VALUE, top-N per group, and the frame clause that decides
what the window can see.

16. **Quartiles of workload** (Q147)

   Technicians who have logged labour, split into 4 equal-sized groups by
   total hours logged -- the busiest quarter in group 1, the quietest in
   group 4.

   Order by hours descending, then technician_id, so the split is
   deterministic.

   *Return: technician_id, name, total_hours, quartile*

17. **Three-month rolling average** (Q148)

   Work orders opened per calendar month, with a rolling average over this
   month and the two before it.

   The first month's average is its own count; the second month's is the
   mean of two. From the third month on it is always three.

   *Return: month, work_orders, rolling_avg_3*

18. **The latest job on each machine** (Q149)

   For every machine that has any work orders: the date and priority of its
   most recent one.

   Exactly one row per machine. Where two work orders share the latest
   date, take the higher work_order_id.

   *Return: machine_id, opened_at, priority*

19. **Top two parts in each category** (Q150)

   Within each part category, the 2 parts with the highest total spend
   across all work orders.

   Spend on a part is quantity * unit_price * (1 - discount), summed over
   every time it was fitted. Break ties on part_id ascending.

   *Return: category, part_id, name, spend*

## Silent sampling (3)

A bare column beside an aggregate. SQLite returns one arbitrary row's value
instead of raising an error.

20. **High scores per verdict** (Q151)

   For each inspection result: how many inspections were recorded, and how
   many of them scored 80 or above.

   Inspections with no score recorded count toward the first number and not
   the second.

   *Return: result, inspections, high_scores*

21. **The newest site of each customer** (Q152)

   For every customer: how many sites they have, and the city of their most
   recently added site -- the one with the highest site_id.

   Half the answers happen to match the customer's oldest site too, so
   checking a few rows will not tell you whether you are right.

   *Return: customer_id, sites, newest_site_city*

22. **Longest-serving technician per depot** (Q153)

   For each depot: how many technicians are based there, and the name of
   the one hired earliest.

   Ties on hire date go to the lower technician_id.

   *Return: depot_id, technicians, longest_serving*

## Self-joins (2)

Pairing a table with itself without producing every pair twice.

23. **Depot colleagues** (Q154)

   Every pair of technicians who work out of the same depot, with the depot
   name.

   Each pair once, not twice, and nobody paired with themselves. List the
   lower technician_id first.

   *Return: depot_name, technician_a, technician_b*

24. **Rival sites in one city** (Q155)

   Pairs of sites in the same city that belong to DIFFERENT customers.

   Each pair once, lower site_id first. Two sites of the same customer in
   one city are not a pair.

   *Return: city, site_a, site_b*

## Grain (2)

Two one-to-many children of the same parent multiply each other.

25. **Parts and inspections on one job** (Q156)

   Closed work orders that have both parts fitted and at least one
   inspection: the total parts cost and the number of inspections.

   Parts cost is quantity * unit_price * (1 - discount) summed over the
   job's parts.

   *Return: work_order_id, parts_cost, inspections*

26. **Regions, customers and depots** (Q157)

   For each region: how many customers are based there and how many depots
   it has.

   One region has no depot at all and must show 0, not disappear.

   *Return: region_id, name, customers, depots*

## NULLs (2)

NULL is unknown -- not zero, not empty, and never equal to anything.

27. **Expired, not merely unknown** (Q158)

   Machines whose warranty ran out before 2026-01-01, with the model and
   the expiry date.

   A machine that was never registered for warranty has warranty_until
   NULL. An unknown expiry is not an expired one, so those must not appear.

   *Return: machine_id, model, warranty_until*

28. **Response times by account tier** (Q159)

   For each account tier: how many contracts those customers hold, how many
   of the contracts agreed a response time, and the average agreed response
   time.

   Some customers were never graded, so their tier is NULL. That is a tier
   in its own right here and gets its own row.

   *Return: account_tier, contracts, with_sla, avg_response_hours*

## General (2)

Keeping the rest sharp.

29. **Stock value by region** (Q160)

   For each region that has a depot: how many depots it has, and the total
   value of stock held across them.

   A stock line's value is quantity_on_hand * the part's unit_cost.

   *Return: region_name, depots, stock_value*

30. **Oldest jobs still open** (Q161)

   The 5 work orders that are still open and have been open longest,
   counting days up to 2026-07-20.

   Only status 'open' counts. Cancelled jobs also have closed_at NULL, but
   they are not open. Oldest first, then work_order_id ascending.

   *Return: work_order_id, machine_id, opened_at, days_open*

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
