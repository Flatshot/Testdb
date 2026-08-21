# SQL practice exercises

**The easiest way to work through these is the GUI** — double-click
`SQL Practice.bat`, or run `python gui.py`. It has 30 of the questions below
built in and grades your answer against the expected result, so you get told
whether you got it right. Progress is saved between sessions.

The list below is the fuller set, for working by hand. Run queries with:

```
python q.py "SELECT ..."
```

or `python q.py` on its own for an interactive prompt (blank line runs, `\q` quits).

The tables: `categories`, `suppliers`, `products`, `employees`, `customers`,
`orders`, `order_items`, `reviews`. See [schema.sql](schema.sql) for columns.

Line revenue is `quantity * unit_price * (1 - discount)` — there is no stored
total, on purpose. Most order-level questions restrict to `status = 'shipped'`.

## Warm-up — SELECT, WHERE, ORDER BY

1. All products costing more than $100, most expensive first.
2. Customers in Norway or Sweden.
3. Products that are discontinued, or out of stock, or both.
4. The 5 most recently hired employees.
5. Products whose name contains "Monitor" (case-insensitive).

## Joins

6. Every product with its category name and supplier name.
7. Orders placed in March 2025, with the customer's full name and the sales rep who took them.
8. Each employee alongside their manager's name — the CEO must still appear, with no manager. *(self-join + outer join)*
9. Customers who have never placed an order. *(anti-join)*
10. Products that have never been ordered. There are three.

## Aggregation — GROUP BY, HAVING

11. Number of products in each category, highest first.
12. Average, minimum, and maximum salary per department.
13. Total shipped revenue per customer, top 10.
14. Customers with more than 8 orders. *(HAVING, not WHERE)*
15. Categories whose average product price exceeds $75.
16. For each supplier: how many products, and how many of those are discontinued.

## NULL handling

17. Orders that have not shipped. Which statuses do they have?
18. Average rating per product, counting only reviews that include a written comment.
19. Why does `COUNT(*)` differ from `COUNT(ship_date)` on `orders`? Show both in one query.
20. Every employee with their manager's name, substituting `'none'` where there is no manager.

## Subqueries and CTEs

21. Products priced above the average price *within their own category*. *(correlated subquery)*
22. The single highest-value shipped order, with the customer's name.
23. Customers whose lifetime spend is above the overall customer average. *(CTE)*
24. For each category, the most expensive product. *(then redo it with a window function)*
25. Orders containing at least one product from the "Electronics" category. *(EXISTS)*

## Window functions

26. Rank products by total shipped revenue, showing the rank number.
27. Running monthly revenue total across the whole order window.
28. Each order's value alongside that customer's average order value, and the difference.
29. Per category, the top 3 products by revenue. *(ROW_NUMBER in a subquery)*
30. Month-over-month revenue change, in dollars and percent. *(LAG)*
31. Days between each customer's consecutive orders. *(LAG over PARTITION BY customer)*

## Dates

32. Orders per month for 2025. *(`strftime('%Y-%m', order_date)`)*
33. Average days between order and shipment, per sales rep.
34. Employees who have worked more than 4 years as of 2026-08-01.
35. Customers who ordered within 30 days of signing up.

## Set operations and harder combinations

36. Countries that appear as a customer country but not as a supplier country. *(EXCEPT)*
37. Products whose average rating is below 3 *and* which have sold more than 20 units.
38. The sales rep with the highest revenue in each quarter of 2025.
39. For each customer: first order date, last order date, order count, and total spend, in one row.
40. Reviewers who rated a product 5 but never bought anything else from that product's category.

---

Stuck on one? Ask and I'll walk through the approach rather than just handing
over the answer — unless you want the answer, in which case say so.
