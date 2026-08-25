# SQL practice exercises

These 30 questions target the nine recurring mistakes in
`sql-concepts-review.html` -- the patterns that produced the same class of bug
more than once. Roughly three quarters of them drill those directly; the rest
keep general skills fresh.

**Work through them in the GUI**: double-click `SQL Practice.bat`, or run
`python gui.py`. It grades your answer against the expected result and, when you
get it right, tells you which mistake the question was built to catch. Progress
is saved between sessions.

To run queries by hand instead:

```
python q.py "SELECT ..."
```

or `python q.py` on its own for an interactive prompt (blank line runs, `\q` quits).

The tables: `categories`, `suppliers`, `products`, `employees`, `customers`,
`orders`, `order_items`, `reviews`, `payments`, `warehouses`, `inventory`,
`shipments`, `returns`. See [schema.sql](schema.sql).

## The one structural fact to hold onto

An order has 0..n **lines** and, separately, 0..n **shipments** -- it can be
split across warehouses. Joining both children in a single query multiplies the
rows: every line repeats once per shipment and every freight cost repeats once
per line. On this data that turns 7,932 of freight into 23,436. Aggregate each
branch to one row per order first, then join.

Other things the data does on purpose:

- **`discount` is a rate**, not a percentage. Line revenue is
  `quantity * unit_price * (1 - discount)`. There is no stored total.
- **Rows are deliberately missing or NULL**: three products are stocked in no
  warehouse, ten shipped orders have no shipment record, 20 shipments are still
  in transit, and `reorder_level`, `last_counted_at`, `loyalty_tier` and
  `lead_time_days` are NULL for a minority. Anti-joins and NULL handling need
  something real to bite on.


## Grain -- aggregate at the level of your answer

*5 occurrences. Ask before every GROUP BY: what does one output row represent?*

1. Total freight cost for each order that has at least one shipment.
   *Return: order_id, total_freight*

2. For every product stocked in at least one warehouse: the total quantity on
   hand summed across all warehouses. One row per product.
   *Return: product_id, total_on_hand*

3. For each shipped order that has at least one shipment: its revenue (sum over
   its lines) and its freight (sum over its shipments). Both children must be
   aggregated separately.
   *Return: order_id, revenue, freight*

4. For each category: the total units sold on shipped orders, and the total units
   returned. Categories with sales but no returns must still appear, with 0
   returned.
   *Return: category name, units_sold, units_returned*


## NULL is contagious and easily destroyed

*Nothing equals NULL, aggregates skip it, and an unknown is not a zero.*

5. Every shipment, showing its delivery date, or the text 'in transit' where it
   has not arrived yet.
   *Return: shipment_id, order_id, delivery_status*

6. For each carrier, the average number of days from shipped_at to delivered_at.
   Shipments still in transit have no transit time yet and must not count
   towards the average.
   *Return: carrier, avg_transit_days*

7. For each warehouse, the value of the stock that has actually been physically
   counted: quantity_on_hand x unit_cost, over inventory lines with a
   last_counted_at date. Lines never counted are excluded.
   *Return: warehouse name, counted_value*

8. Inventory lines whose quantity_on_hand does not equal the reorder_level of ANY
   line in the table. reorder_level is NULL where no policy has been agreed --
   an unknown is not a value, so it must not knock out rows.
   *Return: warehouse_id, product_id, quantity_on_hand*


## Aggregates can't live in WHERE

*3 occurrences. WHERE runs one row at a time; the summary does not exist yet.*

9. Shipments whose freight_cost is above the average freight_cost for THAT
   SHIPMENT'S OWN carrier.
   *Return: shipment_id, carrier, freight_cost*

10. Warehouses that have dispatched more shipments than the average number of
   shipments per warehouse.
   *Return: warehouse name, shipment_count*

11. Categories whose AVERAGE unit margin (unit_price - unit_cost) is above the
   average unit margin across all products.
   *Return: category name, avg_margin*


## PARTITION BY is not GROUP BY

*3 occurrences. GROUP BY collapses rows; PARTITION BY scopes a per-row calculation.*

12. Every shipment, one row each, with its own freight cost and the total freight
   of the order it belongs to.
   *Return: shipment_id, order_id, freight_cost, order_freight*

13. For every inventory line: the quantity on hand and what fraction of that
   PRODUCT'S total stock across all warehouses it represents (0 to 1).
   *Return: warehouse_id, product_id, quantity_on_hand, share_of_product*

14. For each order that has shipments, the details of its EARLIEST shipment by
   shipped_at, breaking ties by the lower shipment_id.
   *Return: order_id, shipment_id, shipped_at, carrier*


## COUNT(*) vs COUNT(column)

*3 occurrences. COUNT(*) counts rows; COUNT(expr) counts rows where expr is not NULL.*

15. Every product with the number of warehouses that stock it. The three stocked
   nowhere must appear with 0.
   *Return: product_id, warehouse_count*

16. For each carrier: how many shipments it has been given, and how many of those
   have actually been delivered.
   *Return: carrier, dispatched, delivered*

17. For each warehouse: the number of shipments dispatched, the number of DISTINCT
   orders they belonged to, and the number of DISTINCT carriers used.
   *Return: warehouse name, shipments, distinct_orders, distinct_carriers*


## Make the alias match the formula

*4 occurrences. These run clean and return confidently wrong numbers.*

18. For each product: its price, its cost, the margin in dollars, and the margin
   as a percentage OF THE PRICE (0 to 100).
   *Return: name, unit_price, unit_cost, margin, margin_pct*

19. For each shipped order that has both lines and shipments: freight as a
   percentage OF revenue (0 to 100). Aggregate each side separately first.
   *Return: order_id, freight_pct_of_revenue*

20. For products that have had at least one return: units sold on shipped orders,
   units returned, and the return rate as a percentage OF UNITS SOLD (0 to
   100).
   *Return: product_id, units_sold, units_returned, return_rate_pct*


## Integer division truncates

*In SQLite `5/2` is `2`. The review is wrong that SQLite auto-converts.*

21. For each carrier, the percentage of its shipments that have been delivered, 0
   to 100.
   *Return: carrier, pct_delivered*

22. For each warehouse: total units on hand, its capacity, and units on hand as a
   percentage of capacity (0 to 100).
   *Return: warehouse name, units_on_hand, capacity_units, pct_of_capacity*


## A CTE is a wall

*2 occurrences. Only the columns the CTE selects exist outside it.*

23. Shipped orders where freight is more than 8% of revenue, showing the date the
   order was placed. Build revenue and freight in CTEs first.
   *Return: order_id, order_date, revenue, freight*


## General practice

*Not tied to a specific weak spot.*

24. Warehouses opened before 2020 with a capacity above 300000 units.
   *Return: name, city, capacity_units, opened_on*

25. The 2 carriers we have spent the most with in TOTAL. Break ties by carrier
   name, A-Z.
   *Return: carrier, total_freight, shipments*

26. For each return reason: how many returns and the total refunded.
   *Return: reason, returns, total_refunded*

27. How many customers sit in each loyalty tier. Customers who never enrolled have
   a NULL tier and must be reported under the label 'not enrolled'.
   *Return: tier, customers*

28. Inventory lines that have fallen to or below their reorder level. Lines with
   no reorder policy cannot be below one.
   *Return: warehouse_id, product_id, quantity_on_hand, reorder_level*

29. Orders that were shipped from more than one DISTINCT warehouse.
   *Return: order_id, warehouses_used*

30. The 5 shipments that have been in transit longest: no delivered_at, oldest
   shipped_at first. Break ties by the lower shipment_id.
   *Return: shipment_id, order_id, carrier, shipped_at*


## The one concept with no question here

**Alias scope follows clause order.** Logical order is `FROM` -> `WHERE` ->
`GROUP BY` -> `HAVING` -> window functions -> `SELECT` -> `ORDER BY` -> `LIMIT`,
and a name only exists after the step that creates it. Postgres and SQL Server
reject a SELECT alias in `WHERE`; SQL Server and Oracle reject one in `GROUP BY`.

There is no graded question for this because **SQLite will not punish you for
it**. It is more permissive than every engine the review names -- it happily
accepts an alias in `WHERE`:

```sql
SELECT unit_price * 2 AS d FROM products WHERE d > 100   -- runs fine in SQLite
```

A question this engine cannot enforce would teach the wrong lesson. Keep the
rule for portability, and reach for a CTE when you want a real column to filter
or group by.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the 71
retired ones. New questions must not repeat anything in that ledger.

Stuck? Ask and I'll walk through the approach rather than hand over the answer
-- unless you want the answer, in which case say so.
