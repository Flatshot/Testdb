# SQL practice exercises

These 30 questions are built on the repair-depot schema and weighted hard
toward **grain**. Fifteen of them punish the same mistake: joining two
one-to-many children of the same parent in a single query block. The other
fifteen cover windows, NULLs, COUNT, integer division, aggregate filtering
and CTE scope.

**Work through them in the GUI**: double-click `SQL Practice.bat`, or run
`python gui.py`. It grades your answer against the expected result and, when
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

## The one structural fact to hold onto

A work order has **three independent children**: `parts_used`,
`labor_entries` and `inspections`. A job with 4 parts and 3 visits produces
12 rows if you join both children, so the parts total comes out 3x too big
and the labour total 4x too big.

On this data, joining parts and labour in one block turns a true parts total
of **367,673** into **668,449**, and a true labour total of **49,729** into
**100,933**. Both are wrong, by different factors, so no single correction
rescues them.

Aggregate each branch to one row per work order *first*, then join the
results:

```sql
WITH p AS (SELECT work_order_id, SUM(...) FROM parts_used   GROUP BY work_order_id),
     l AS (SELECT work_order_id, SUM(...) FROM labor_entries GROUP BY work_order_id)
SELECT ... FROM p JOIN l USING(work_order_id)
```

Other things the data does on purpose:

- **`discount` is a rate**, not a percentage. A parts line costs
  `quantity * unit_price * (1 - discount)`. There is no stored total.
- **Rows are deliberately missing or NULL.** Of 180 work
  orders, some have no parts, some no labour, some neither; 23 closed jobs
  were never inspected and 19 were inspected twice. Three parts are stocked
  in no depot, two have never been fitted, two customers have never raised a
  work order. `cert_level`, `response_hours`, `reorder_level`,
  `last_counted_at`, `warranty_until`, `score` and `weight_grams` are NULL
  for a minority. Anti-joins and NULL handling need something real to find.
- **`closed_at` is NULL for open *and* cancelled jobs.** 'Still open' needs
  the status column, not just the NULL.
- **Invoice `status` is UPPERCASE** (`PAID`, `PENDING`, `OVERDUE`, `VOID`).
- **The technician who logged a visit is not always the one the job is
  assigned to.** The assignment is a column on `work_orders`.

## Grain (15)

Joining two one-to-many children of the same parent in one query block. Every
aggregate in that block is then wrong.

1. **What a job actually cost** (Q102)

   Every closed work order that has both parts and labour logged against
   it, with what each side cost and the total.

   Parts cost is quantity * unit_price * (1 - discount), summed over the
   job's parts. Labour cost is hours * rate, summed over the job's visits.

   *Return: work_order_id, parts_cost, labor_cost, total_cost*

2. **Labour's share of the bill** (Q103)

   For closed work orders that have both parts and labour: labour cost as a
   percentage of the whole job cost.

   Whole job cost is parts plus labour. Work each side out separately --
   one row per work order each -- then divide.

   The answer is between 0 and 100 for every job.

   *Return: work_order_id, labor_pct_of_total*

3. **Parts count and hours together** (Q104)

   For every work order that has both parts and labour: how many distinct
   parts were fitted, and how many hours were worked in total.

   A part fitted in quantity 6 still counts as one part.

   *Return: work_order_id, part_lines, total_hours*

4. **Hours, and who signed the job off** (Q105)

   For each work order that has labour logged and an assigned technician:
   the total hours worked on it, and the name of the technician the job is
   assigned to.

   The assignment lives on the work order. Several technicians may have
   logged visits against the same job, so the assigned one is not simply
   whoever appears in labor_entries.

   *Return: work_order_id, technician_name, total_hours*

5. **The missing SUM** (Q106)

   Total parts cost for every work order that used any parts, and the
   number of separate part lines on it.

   Parts cost is quantity * unit_price * (1 - discount).

   Jobs using a single part are the ones to check your answer against: if a
   multi-part job reports the same figure as a one-part job of similar
   size, something is not being added up.

   *Return: work_order_id, part_lines, parts_cost*

6. **Do not go back to the well** (Q107)

   Closed work orders whose labour cost is more than 400, showing when the
   job was opened and how many visits it took.

   Labour cost is hours * rate summed over the visits.

   *Return: work_order_id, opened_at, visits, labor_cost*

7. **Three children, one job** (Q108)

   Closed work orders that have parts, labour AND at least one inspection:
   the parts cost, the total hours, and how many inspections the job
   received.

   *Return: work_order_id, parts_cost, total_hours, inspections*

8. **Contracts and callouts** (Q109)

   For each customer that has at least one contract and at least one work
   order: their total monthly contract fee, and how many work orders have
   been raised across all their sites.

   Contracts hang off the customer. Work orders hang off the customer's
   sites and machines. They are separate branches.

   *Return: customer_id, name, monthly_fee_total, work_orders*

9. **Counting down a chain** (Q110)

   For each customer: how many sites they have, how many machines across
   those sites, and how many work orders across those machines.

   Every customer has at least one site, so all of them appear. Two
   customers have never had a work order raised and must show 0.

   *Return: customer_id, sites, machines, work_orders*

10. **Stock on hand per part** (Q111)

   For every part that is stocked somewhere: the total quantity on hand
   across all depots, and how many depots carry it.

   Three parts are stocked in no depot at all and are correctly absent from
   the answer.

   *Return: part_id, depots_carrying, total_on_hand*

11. **Invoice against actual cost** (Q112)

   For every invoiced work order that has both parts and labour: the
   invoice amount and the true cost of the job, and the difference between
   them.

   True cost is parts plus labour. Difference is invoice minus true cost.

   *Return: work_order_id, invoice_amount, true_cost, difference*

12. **Technician workload** (Q113)

   For each technician who has logged any labour: the total hours they
   logged, and how many distinct work orders they logged them against.

   A technician can log several visits to the same job.

   *Return: technician_id, name, total_hours, jobs_touched*

13. **Depot stock and staff** (Q114)

   For each depot: how many technicians are based there, and the total
   quantity of stock it holds across all part lines.

   Technicians and stock lines are separate children of the depot.

   *Return: depot_id, name, technicians, total_stock*

14. **Cost per hour on the job** (Q115)

   For closed work orders with both parts and labour: the parts cost per
   labour hour.

   That is total parts cost divided by total hours -- each worked out over
   the whole job, not line by line.

   *Return: work_order_id, parts_cost_per_hour*

15. **Busiest machines** (Q116)

   The 5 machines with the most work orders raised against them, showing
   the model and the owning customer.

   Order by the work order count highest first, then by machine_id
   ascending so ties are settled.

   *Return: machine_id, model, customer_name, work_orders*

## Window vs GROUP BY (3)

PARTITION BY does not collapse rows, and an ORDER BY inside OVER() changes the
frame.

16. **Each visit against the job total** (Q117)

   Every labour entry on work order 2, showing the hours on that visit and
   the total hours across the whole job on every row.

   The total is the same value on all of the job's rows -- the individual
   visits are not collapsed.

   *Return: entry_id, work_date, hours, job_total_hours*

17. **First visit to each job** (Q118)

   For every work order that has labour logged: the details of its earliest
   visit.

   Jobs can have two visits on the same date. Where that happens, take the
   one with the lower entry_id, so exactly one row comes back per work
   order.

   *Return: work_order_id, entry_id, work_date, hours*

18. **Running spend per depot** (Q119)

   Every stock line in depot 2, ordered by part_id, with a running total of
   quantity on hand accumulating down that order.

   The first row's running total equals its own quantity; the last row's
   equals the depot's whole stock.

   *Return: part_id, quantity_on_hand, running_total*

## Aggregates in WHERE (2)

A condition on an aggregate belongs in HAVING; WHERE runs before grouping.

19. **Jobs that ran long** (Q120)

   Work orders that took more than 3 visits to close, with the visit count
   and total hours.

   Only closed jobs count.

   *Return: work_order_id, visits, total_hours*

20. **Customers worth chasing** (Q121)

   Customers whose unpaid invoices -- anything not PAID -- come to more
   than 3000 in total, with the amount outstanding and how many invoices
   make it up.

   An invoice belongs to a customer through its work order, machine and
   site.

   *Return: customer_id, name, unpaid_invoices, amount_outstanding*

## CTE scope (1)

The outer query sees only what the CTE selected.

21. **Carry it through the wall** (Q122)

   Closed work orders whose parts cost is above 1200, showing the machine's
   model and the priority the job was raised at.

   Build the parts cost in a CTE first.

   *Return: work_order_id, model, priority, parts_cost*

## COUNT (2)

COUNT(*) counts rows including the phantom row a LEFT JOIN leaves behind;
COUNT(col) skips NULLs.

22. **Inspected, or not** (Q123)

   Every closed work order, with how many inspections it received. Jobs
   never inspected must show 0, not vanish.

   *Return: work_order_id, inspections*

23. **Scored and unscored** (Q124)

   For each inspection result -- pass, fail, conditional -- how many
   inspections were recorded, how many carried a numeric score, and the
   average of those scores.

   Some inspectors record a verdict without a score.

   *Return: result, inspections, with_score, avg_score*

## NULLs (3)

NULL is unknown, not zero and not empty. It never equals anything, and it
drops out of comparisons silently.

24. **Slow to answer** (Q125)

   Contracts with an agreed response time of more than 24 hours, showing
   the customer.

   Four contracts never agreed a response time at all. An unknown response
   time is not a slow one, so those must not appear.

   *Return: contract_id, customer_name, response_hours*

25. **Never certified** (Q126)

   Technicians who have not been certified, with their depot and how many
   labour hours they have logged.

   A technician with no certification has cert_level NULL. Every one of
   them has logged some labour.

   *Return: technician_id, name, depot_name, total_hours*

26. **Parts nobody has fitted** (Q127)

   Parts that have never been used on any work order, with their category
   and unit cost.

   *Return: part_id, name, category, unit_cost*

## Integer division (2)

INTEGER / INTEGER truncates in SQLite.

27. **Average parts per job** (Q128)

   For each work order priority, the average number of part lines per work
   order that used parts.

   Both the part count and the job count are integers. The answer is not a
   whole number -- 'critical' comes to 2.67.

   *Return: priority, jobs, part_lines, avg_lines_per_job*

28. **Stock cover against reorder level** (Q129)

   Stock lines that have a reorder level set, showing quantity on hand as a
   multiple of that level.

   Lines with no agreed reorder policy are excluded. Report the multiple to
   full precision, not rounded down.

   *Return: depot_id, part_id, quantity_on_hand, reorder_level, cover*

## General (2)

Keeping the rest sharp.

29. **Who reports to whom** (Q130)

   Every technician who has a supervisor, with the supervisor's name and
   how much longer the supervisor has been employed, in whole days.

   One technician is the depot manager and reports to nobody, so does not
   appear.

   *Return: technician_name, supervisor_name, supervisor_extra_days*

30. **How long jobs stay open** (Q131)

   For each priority, how many jobs were closed and the average whole days
   from opening to closing.

   Only jobs that actually closed count -- open and cancelled ones both
   have closed_at NULL and must be excluded.

   *Return: priority, closed_jobs, avg_days_open*

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

A question this engine cannot enforce would teach the wrong lesson. Keep the
rule for portability, and reach for a CTE when you want a real column to
filter or group by -- which is also what makes the grain questions above come
out right.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the
101 retired ones. New questions must not repeat anything in that ledger.

Stuck? Ask and I'll walk through the approach rather than hand over the
answer -- unless you want the answer, in which case say so.
