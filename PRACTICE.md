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
`orders`, `order_items`, `reviews`, `payments`. See [schema.sql](schema.sql).

Two things the data does on purpose:

- **`discount` is a rate**, not a percentage. Line revenue is
  `quantity * unit_price * (1 - discount)`. There is no stored total.
- **Some rows are deliberately missing or NULL**: four customers have never
  ordered, three products have never sold, 22 orders have no payment row,
  `helpful_votes` / `weight_grams` / `commission_rate` are NULL for a minority.
  Anti-joins and NULL handling need something to bite on.


## Grain -- aggregate at the level of your answer

*5 occurrences. Ask before every GROUP BY: what does one output row represent?*

1. Total shipped revenue for each category.
   *Return: category name, revenue*

2. For each department: how many employees, and the total salary bill.
   *Return: department, employee_count, total_salary*

3. Total amount each customer has actually paid: sum the amount of their payments
   with status 'PAID'. Only customers with at least one such payment.
   *Return: customer_id, total_paid*

4. For each month of 2025: how many orders were placed, and how many DIFFERENT
   customers placed them. Month as YYYY-MM.
   *Return: month, order_count, distinct_customers*


## NULL is contagious and easily destroyed

*Nothing equals NULL, aggregates skip it, and a WHERE on the optional side of an outer join deletes it.*

5. helpful_votes is NULL when nobody has voted yet, which is not the same as zero
   votes. Return the average helpful_votes across all reviews two ways:
   excluding the unknowns, then treating every unknown as 0.
   *Return: avg_excluding_unknown, avg_unknown_as_zero*

6. Every order, with the amount of its PAID payment beside it, or NULL where
   there is no paid payment. All 165 orders must appear.
   *Return: order_id, paid_amount*

7. Employees who are not anybody's manager.
   *Return: employee_id, employee_name (first + space + last)*

8. Total annual compensation for every employee: salary, plus commission of
   salary x commission_rate. Staff not on a commission scheme have a NULL rate
   and simply earn their salary. All 12 employees must appear.
   *Return: employee_name (first + space + last), total_comp*


## Aggregates can't live in WHERE

*3 occurrences. WHERE runs one row at a time; the summary does not exist yet.*

9. Payments with status 'PAID' whose amount is greater than the average amount of
   all PAID payments.
   *Return: payment_id, order_id, amount*

10. The single sales rep who has taken the most orders.
   *Return: rep_name (first + space + last), order_count*

11. Categories whose average review rating is higher than the average rating
   across every review in the database.
   *Return: category name, avg_rating*


## PARTITION BY is not GROUP BY

*3 occurrences. GROUP BY collapses rows; PARTITION BY scopes a per-row calculation.*

12. Every line of every shipped order, keeping one row per line, with the revenue
   of that line and the revenue of the whole order beside it.
   *Return: order_id, product_id, line_revenue, order_revenue*

13. Every PAID payment with a running cumulative total of that customer's paid
   amounts, ordered by paid_at then payment_id.
   *Return: payment_id, customer_id, amount, running_total*

14. Every review with the rating of the previous review OF THE SAME PRODUCT,
   ordered by review_date then review_id. NULL where it is the first.
   *Return: review_id, product_id, rating, prev_rating*


## COUNT(*) vs COUNT(column)

*3 occurrences. COUNT(*) counts rows; COUNT(expr) counts rows where expr is not NULL.*

15. Every customer with the number of orders they have placed. The four who have
   never ordered must appear with 0.
   *Return: customer_id, order_count*

16. For each payment method: the total number of payments, and how many of them
   have status 'PAID'.
   *Return: method, total_payments, paid_count*

17. For each product that has at least one review: the number of reviews, how many
   included a written comment, and how many had helpful_votes recorded.
   *Return: product name, review_count, with_comment, with_votes*


## Make the alias match the formula

*4 occurrences. These run clean and return confidently wrong numbers.*

18. For every order line: the gross value before discount, the discount amount in
   dollars, and the net revenue. discount is a RATE (0.05 = 5%).
   *Return: order_id, product_id, gross, discount_amount, net*

19. For each country, the percentage of that country's customers who have placed
   at least one order. A percentage of the country's own customers, 0 to 100.
   *Return: country, pct_with_orders*

20. For each month, how many payments settled (status 'PAID', bucketed by paid_at)
   and the CHANGE in that count versus the previous month. NULL for the first
   month. Month as YYYY-MM.
   *Return: month, paid_count, change_vs_prev*


## Integer division truncates

*In SQLite `5/2` is `2`. The review is wrong that SQLite auto-converts.*

21. What percentage of all orders have a ship_date? One row, one column, 0 to 100.
   *Return: pct_shipped*

22. For each category: the total weight in grams of its products that have a
   recorded weight, and the mean grams per weighed product. Products with no
   recorded weight are excluded from both. Only categories with at least one
   weighed product.
   *Return: category name, total_grams, mean_grams*


## A CTE is a wall

*2 occurrences. Only the columns the CTE selects exist outside it.*

23. For every customer with at least two shipped orders, their SECOND most
   valuable one. Rank each customer's shipped orders by value descending and
   take number 2.
   *Return: customer_id, order_id, order_date, order_value*


## General practice

*Not tied to a specific weak spot.*

24. For payments with status 'PAID' only: how many per method and the total
   amount.
   *Return: method, paid_count, total_amount*

25. Products with a recorded weight over 5000 grams.
   *Return: name, weight_grams*

26. Orders whose payment settled on the same date the order was placed.
   *Return: order_id, order_date, amount*

27. The 5 products with the most reviews.
   *Return: product name, review_count*

28. Customers who have had at least one payment refunded. One row per customer.
   *Return: customer_id, customer_name (first + space + last)*

29. Employees who were hired BEFORE the manager they report to.
   *Return: employee_name, manager_name, employee_hire_date, manager_hire_date*

30. Categories with at least 10 reviews across all their products, with the
   average rating.
   *Return: category name, review_count, avg_rating*


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

Writing a question SQLite cannot enforce would teach the wrong lesson. Keep the
rule in mind for portability, and reach for a CTE when you want a real column to
filter or group by.

---

Every question is recorded in [QUESTIONS.md](QUESTIONS.md), along with the 41
retired ones. New questions must not repeat anything in that ledger.

Stuck? Ask and I'll walk through the approach rather than hand over the answer
-- unless you want the answer, in which case say so.
