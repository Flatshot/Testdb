"""Practice exercises with reference solutions, used by the GUI to grade answers.

Grading compares your result against the reference as an unordered multiset of
rows, with floats rounded to 2 decimals. So row order never matters and you do
not need to remember ROUND() -- but the number of columns, and the values in
them, do have to match. Each prompt states exactly which columns to return.

Spoiler warning: the reference SQL lives in this file. Don't read it if you
want the exercises to stay interesting.

REVENUE is always: quantity * unit_price * (1 - discount), taken from
order_items, and restricted to orders with status = 'shipped' unless a
question says otherwise.
"""

EXERCISES = [
    # ------------------------------------------------------------------ warm-up
    dict(
        id=1, tier="Warm-up", title="Expensive products",
        prompt="Every product costing more than $100.\n\nReturn: name, unit_price",
        solution="SELECT name, unit_price FROM products WHERE unit_price > 100",
    ),
    dict(
        id=2, tier="Warm-up", title="Nordic customers",
        prompt="Customers based in Norway or Sweden.\n\nReturn: first_name, last_name, country",
        solution="SELECT first_name, last_name, country FROM customers"
                 " WHERE country IN ('Norway', 'Sweden')",
    ),
    dict(
        id=3, tier="Warm-up", title="Unavailable stock",
        prompt="Products that are discontinued, or have no units in stock, or both.\n\n"
               "Return: name, units_in_stock, discontinued",
        solution="SELECT name, units_in_stock, discontinued FROM products"
                 " WHERE discontinued = 1 OR units_in_stock = 0",
    ),
    dict(
        id=4, tier="Warm-up", title="Newest hires",
        prompt="The 5 most recently hired employees.\n\nReturn: first_name, last_name, hire_date",
        solution="SELECT first_name, last_name, hire_date FROM employees"
                 " ORDER BY hire_date DESC LIMIT 5",
    ),
    dict(
        id=5, tier="Warm-up", title="Search by name",
        prompt="Products whose name contains the word 'Monitor'.\n\nReturn: name, unit_price",
        solution="SELECT name, unit_price FROM products WHERE name LIKE '%Monitor%'",
    ),

    # -------------------------------------------------------------------- joins
    dict(
        id=6, tier="Joins", title="Product catalogue",
        prompt="Every product with the name of its category and its supplier.\n\n"
               "Return: product name, category name, supplier name",
        solution="SELECT p.name, c.name, s.name FROM products p"
                 " JOIN categories c ON c.category_id = p.category_id"
                 " JOIN suppliers s ON s.supplier_id = p.supplier_id",
    ),
    dict(
        id=7, tier="Joins", title="Orders in a month",
        prompt="Orders placed in March 2025, with the customer's full name (first and last "
               "joined by a space) and the last name of the sales rep credited.\n\n"
               "Return: order_id, customer_name, rep_last_name",
        solution="SELECT o.order_id, cu.first_name || ' ' || cu.last_name, e.last_name"
                 " FROM orders o"
                 " JOIN customers cu ON cu.customer_id = o.customer_id"
                 " JOIN employees e ON e.employee_id = o.employee_id"
                 " WHERE o.order_date >= '2025-03-01' AND o.order_date < '2025-04-01'",
    ),
    dict(
        id=8, tier="Joins", title="Who reports to whom",
        prompt="Every employee with their manager's full name. The CEO reports to nobody "
               "and must still appear, with NULL for the manager.\n\n"
               "Return: employee_name, manager_name",
        solution="SELECT e.first_name || ' ' || e.last_name,"
                 " m.first_name || ' ' || m.last_name"
                 " FROM employees e LEFT JOIN employees m ON m.employee_id = e.manager_id",
    ),
    dict(
        id=9, tier="Joins", title="Customers who never bought",
        prompt="Customers who have never placed a single order.\n\n"
               "Return: customer_id, first_name, last_name",
        solution="SELECT cu.customer_id, cu.first_name, cu.last_name FROM customers cu"
                 " WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = cu.customer_id)",
    ),
    dict(
        id=10, tier="Joins", title="Products that never sold",
        prompt="Products that have never appeared on any order.\n\nReturn: product_id, name",
        solution="SELECT p.product_id, p.name FROM products p"
                 " WHERE NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.product_id = p.product_id)",
    ),

    # -------------------------------------------------------------- aggregation
    dict(
        id=11, tier="Aggregation", title="Products per category",
        prompt="How many products are in each category?\n\nReturn: category name, product_count",
        solution="SELECT c.name, COUNT(*) FROM categories c"
                 " JOIN products p ON p.category_id = c.category_id GROUP BY c.category_id",
    ),
    dict(
        id=12, tier="Aggregation", title="Pay by department",
        prompt="Average, minimum, and maximum salary for each department.\n\n"
               "Return: department, avg_salary, min_salary, max_salary",
        solution="SELECT department, AVG(salary), MIN(salary), MAX(salary)"
                 " FROM employees GROUP BY department",
    ),
    dict(
        id=13, tier="Aggregation", title="Best customers",
        prompt="The 10 customers who have generated the most shipped revenue.\n\n"
               "Return: customer_id, customer_name (first + space + last), revenue",
        solution="SELECT cu.customer_id, cu.first_name || ' ' || cu.last_name,"
                 " SUM(oi.quantity * oi.unit_price * (1 - oi.discount))"
                 " FROM customers cu"
                 " JOIN orders o ON o.customer_id = cu.customer_id"
                 " JOIN order_items oi ON oi.order_id = o.order_id"
                 " WHERE o.status = 'shipped'"
                 " GROUP BY cu.customer_id"
                 " ORDER BY SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) DESC LIMIT 10",
    ),
    dict(
        id=14, tier="Aggregation", title="Frequent buyers",
        prompt="Customers who have placed more than 8 orders (any status).\n\n"
               "Return: customer_id, order_count",
        solution="SELECT customer_id, COUNT(*) FROM orders"
                 " GROUP BY customer_id HAVING COUNT(*) > 8",
    ),
    dict(
        id=15, tier="Aggregation", title="Premium categories",
        prompt="Categories whose average product price is above $75.\n\n"
               "Return: category name, avg_price",
        solution="SELECT c.name, AVG(p.unit_price) FROM categories c"
                 " JOIN products p ON p.category_id = c.category_id"
                 " GROUP BY c.category_id HAVING AVG(p.unit_price) > 75",
    ),
    dict(
        id=16, tier="Aggregation", title="Supplier breakdown",
        prompt="For each supplier: how many products they supply, and how many of those "
               "are discontinued (0 if none).\n\n"
               "Return: supplier name, product_count, discontinued_count",
        solution="SELECT s.name, COUNT(*), SUM(p.discontinued) FROM suppliers s"
                 " JOIN products p ON p.supplier_id = s.supplier_id GROUP BY s.supplier_id",
    ),

    # -------------------------------------------------------------------- nulls
    dict(
        id=17, tier="NULLs", title="Not yet shipped",
        prompt="Orders that have no ship date.\n\nReturn: order_id, status",
        solution="SELECT order_id, status FROM orders WHERE ship_date IS NULL",
    ),
    dict(
        id=18, tier="NULLs", title="Ratings with words",
        prompt="Average rating per product, counting ONLY reviews that include a written "
               "comment. Products with no commented reviews should not appear.\n\n"
               "Return: product name, avg_rating, review_count",
        solution="SELECT p.name, AVG(r.rating), COUNT(*) FROM products p"
                 " JOIN reviews r ON r.product_id = p.product_id"
                 " WHERE r.comment IS NOT NULL GROUP BY p.product_id",
    ),
    dict(
        id=19, tier="NULLs", title="COUNT(*) vs COUNT(col)",
        prompt="One row showing the total number of orders next to the number of orders "
               "that have a ship date. The gap is what COUNT(column) skips.\n\n"
               "Return: total_orders, orders_with_ship_date",
        solution="SELECT COUNT(*), COUNT(ship_date) FROM orders",
    ),
    dict(
        id=20, tier="NULLs", title="Substituting for NULL",
        prompt="Every employee with their manager's full name, but show the text 'none' "
               "instead of NULL for the CEO.\n\nReturn: employee_name, manager_name",
        solution="SELECT e.first_name || ' ' || e.last_name,"
                 " COALESCE(m.first_name || ' ' || m.last_name, 'none')"
                 " FROM employees e LEFT JOIN employees m ON m.employee_id = e.manager_id",
    ),

    # ------------------------------------------------------- subqueries and CTEs
    dict(
        id=21, tier="Subqueries", title="Pricier than its peers",
        prompt="Products priced above the average price WITHIN THEIR OWN CATEGORY "
               "(not the overall average).\n\nReturn: product name, category name, unit_price",
        solution="SELECT p.name, c.name, p.unit_price FROM products p"
                 " JOIN categories c ON c.category_id = p.category_id"
                 " WHERE p.unit_price > (SELECT AVG(x.unit_price) FROM products x"
                 "                       WHERE x.category_id = p.category_id)",
    ),
    dict(
        id=22, tier="Subqueries", title="Biggest single order",
        prompt="The single most valuable shipped order.\n\n"
               "Return: order_id, customer_name (first + space + last), order_value",
        solution="WITH ov AS (SELECT o.order_id, o.customer_id,"
                 "  SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS val"
                 "  FROM orders o JOIN order_items oi ON oi.order_id = o.order_id"
                 "  WHERE o.status = 'shipped' GROUP BY o.order_id)"
                 " SELECT ov.order_id, cu.first_name || ' ' || cu.last_name, ov.val"
                 " FROM ov JOIN customers cu ON cu.customer_id = ov.customer_id"
                 " ORDER BY ov.val DESC LIMIT 1",
    ),
    dict(
        id=23, tier="Subqueries", title="Above-average spenders",
        prompt="Customers whose lifetime shipped spend is above the average lifetime spend "
               "across all customers who have bought anything.\n\n"
               "Return: customer_id, customer_name, lifetime_spend",
        solution="WITH spend AS (SELECT cu.customer_id,"
                 "  cu.first_name || ' ' || cu.last_name AS nm,"
                 "  SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS total"
                 "  FROM customers cu JOIN orders o ON o.customer_id = cu.customer_id"
                 "  JOIN order_items oi ON oi.order_id = o.order_id"
                 "  WHERE o.status = 'shipped' GROUP BY cu.customer_id)"
                 " SELECT customer_id, nm, total FROM spend"
                 " WHERE total > (SELECT AVG(total) FROM spend)",
    ),
    dict(
        id=24, tier="Subqueries", title="Flagship per category",
        prompt="The most expensive product in each category.\n\n"
               "Return: category name, product name, unit_price",
        solution="SELECT c.name, p.name, p.unit_price FROM products p"
                 " JOIN categories c ON c.category_id = p.category_id"
                 " WHERE p.unit_price = (SELECT MAX(x.unit_price) FROM products x"
                 "                       WHERE x.category_id = p.category_id)",
    ),
    dict(
        id=25, tier="Subqueries", title="Orders touching a category",
        prompt="The ids of all orders containing at least one product from the "
               "'Electronics' category. Each order id once.\n\nReturn: order_id",
        solution="SELECT DISTINCT o.order_id FROM orders o"
                 " JOIN order_items oi ON oi.order_id = o.order_id"
                 " JOIN products p ON p.product_id = oi.product_id"
                 " JOIN categories c ON c.category_id = p.category_id"
                 " WHERE c.name = 'Electronics'",
    ),

    # ---------------------------------------------------------- window functions
    dict(
        id=26, tier="Window functions", title="Revenue leaderboard",
        prompt="The top 10 products by shipped revenue, each with its rank (1 = highest). "
               "Use a window function for the rank.\n\n"
               "Return: product name, revenue, revenue_rank",
        solution="WITH pr AS (SELECT p.name AS nm,"
                 "  SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS rev"
                 "  FROM order_items oi JOIN orders o ON o.order_id = oi.order_id"
                 "  JOIN products p ON p.product_id = oi.product_id"
                 "  WHERE o.status = 'shipped' GROUP BY p.product_id)"
                 " SELECT nm, rev, RANK() OVER (ORDER BY rev DESC) FROM pr"
                 " ORDER BY rev DESC LIMIT 10",
    ),
    dict(
        id=27, tier="Window functions", title="Running revenue",
        prompt="Shipped revenue per calendar month, plus a running cumulative total "
               "across months. Month formatted as YYYY-MM.\n\n"
               "Return: month, monthly_revenue, running_total",
        solution="WITH m AS (SELECT strftime('%Y-%m', o.order_date) AS mo,"
                 "  SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS rev"
                 "  FROM orders o JOIN order_items oi ON oi.order_id = o.order_id"
                 "  WHERE o.status = 'shipped' GROUP BY mo)"
                 " SELECT mo, rev, SUM(rev) OVER (ORDER BY mo) FROM m",
    ),
    dict(
        id=28, tier="Window functions", title="Top 2 per category",
        prompt="For each category, the 2 products with the highest shipped revenue, "
               "with their position (1 or 2) within the category.\n\n"
               "Return: category name, product name, revenue, position",
        solution="WITH pr AS (SELECT c.name AS cat, p.name AS prod,"
                 "  SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS rev"
                 "  FROM order_items oi JOIN orders o ON o.order_id = oi.order_id"
                 "  JOIN products p ON p.product_id = oi.product_id"
                 "  JOIN categories c ON c.category_id = p.category_id"
                 "  WHERE o.status = 'shipped' GROUP BY p.product_id),"
                 " r AS (SELECT cat, prod, rev,"
                 "  ROW_NUMBER() OVER (PARTITION BY cat ORDER BY rev DESC) AS rn FROM pr)"
                 " SELECT cat, prod, rev, rn FROM r WHERE rn <= 2",
    ),

    # -------------------------------------------------------------------- dates
    dict(
        id=29, tier="Dates", title="Orders by month",
        prompt="How many orders were placed in each month of 2025? Month as YYYY-MM.\n\n"
               "Return: month, order_count",
        solution="SELECT strftime('%Y-%m', order_date), COUNT(*) FROM orders"
                 " WHERE order_date >= '2025-01-01' AND order_date < '2026-01-01'"
                 " GROUP BY strftime('%Y-%m', order_date)",
    ),
    dict(
        id=30, tier="Dates", title="Fulfilment speed",
        prompt="Average number of days between order date and ship date for each sales "
               "rep, counting only orders that actually shipped.\n\n"
               "Return: rep_name (first + space + last), avg_days_to_ship",
        solution="SELECT e.first_name || ' ' || e.last_name,"
                 " AVG(julianday(o.ship_date) - julianday(o.order_date))"
                 " FROM orders o JOIN employees e ON e.employee_id = o.employee_id"
                 " WHERE o.ship_date IS NOT NULL GROUP BY e.employee_id",
    ),
]

BY_ID = {ex["id"]: ex for ex in EXERCISES}
TIERS = list(dict.fromkeys(ex["tier"] for ex in EXERCISES))


def normalise(rows):
    """Canonical form for comparison: floats rounded, rows sorted, order ignored."""
    out = []
    for row in rows:
        out.append(tuple(
            round(v, 2) if isinstance(v, float) else v
            for v in row
        ))
    # Sort by a string key so mixed types and None never blow up the comparison.
    return sorted(out, key=lambda r: [(v is None, str(v)) for v in r])


def compare(user_rows, expected_rows):
    """Return (passed, message) describing how the two result sets line up."""
    got, want = normalise(user_rows), normalise(expected_rows)

    if got == want:
        return True, f"Correct - {len(want)} row(s) matched."

    if not user_rows:
        return False, f"Your query returned no rows; expected {len(want)}."

    got_cols = len(got[0]) if got else 0
    want_cols = len(want[0]) if want else 0
    if got_cols != want_cols:
        return False, (f"Wrong number of columns: you returned {got_cols}, "
                       f"expected {want_cols}. Check the 'Return:' line in the question.")

    if len(got) != len(want):
        extra = len(got) - len(want)
        direction = f"{extra} too many" if extra > 0 else f"{-extra} too few"
        return False, (f"Wrong number of rows: you returned {len(got)}, "
                       f"expected {len(want)} ({direction}).")

    missing = [r for r in want if r not in got]
    unexpected = [r for r in got if r not in want]
    detail = ""
    if missing:
        detail += f"\n  Expected but missing:  {missing[0]}"
    if unexpected:
        detail += f"\n  Returned but wrong:    {unexpected[0]}"
    return False, (f"Right row count ({len(got)}), but the values differ "
                   f"in {len(missing)} row(s).{detail}")
