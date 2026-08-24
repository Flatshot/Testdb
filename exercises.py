"""Practice exercises with reference solutions, used by the GUI to grade answers.

These 30 questions target the nine recurring mistakes catalogued in
sql-concepts-review.html, weighted by how often each one showed up. Each
question carries:

  concept   the review section it drills (C1..C9), or "GEN"
  solution  one correct answer
  trap_sql  the tempting WRONG query -- check_questions.py asserts the grader
            rejects it, which is what proves the question actually has teeth
  note      the lesson, shown in the GUI once you get it right

Grading compares your result against the reference as an unordered multiset of
rows, with floats rounded to 2 decimals. Row order never matters and you do not
need to remember ROUND(). Column count and values do matter -- each prompt
states exactly what to return.

Spoiler warning: the reference SQL is in this file.

REVENUE is always quantity * unit_price * (1 - discount) from order_items,
restricted to orders with status = 'shipped' unless stated otherwise.
"""

EXERCISES = [
    # ================================================================= C2 grain
    dict(
        id=1, ledger="Q042", concept="C2", tier="Grain",
        title="Revenue per category",
        prompt="Total shipped revenue for each category.\n\n"
               "Return: category name, revenue",
        solution="SELECT c.name, SUM(oi.quantity * oi.unit_price * (1 - oi.discount))"
                 " FROM order_items oi"
                 " JOIN orders o ON o.order_id = oi.order_id"
                 " JOIN products p ON p.product_id = oi.product_id"
                 " JOIN categories c ON c.category_id = p.category_id"
                 " WHERE o.status = 'shipped' GROUP BY c.category_id",
        trap_sql="SELECT c.name, SUM(oi.quantity * oi.unit_price) * (1 - AVG(oi.discount))"
                 " FROM order_items oi"
                 " JOIN orders o ON o.order_id = oi.order_id"
                 " JOIN products p ON p.product_id = oi.product_id"
                 " JOIN categories c ON c.category_id = p.category_id"
                 " WHERE o.status = 'shipped' GROUP BY c.category_id",
        note="Every row-level term belongs INSIDE the SUM. Pulling the discount out "
             "applies one averaged discount to the whole bucket.",
    ),
    dict(
        id=2, ledger="Q043", concept="C2", tier="Grain",
        title="Headcount and payroll by department",
        prompt="For each department: how many employees, and the total salary bill.\n\n"
               "Return: department, employee_count, total_salary",
        solution="SELECT department, COUNT(*), SUM(salary) FROM employees GROUP BY department",
        trap_sql="SELECT department, COUNT(*), SUM(salary) FROM employees"
                 " GROUP BY department, salary",
        note="Grouping keys define the bucket; aggregates describe it. salary is a "
             "row-level column, so it can never be a grouping key.",
    ),
    dict(
        id=3, ledger="Q044", concept="C2", tier="Grain",
        title="Settled money per customer",
        prompt="Total amount each customer has actually paid: sum the amount of their "
               "payments with status 'PAID'. Only customers with at least one such "
               "payment.\n\nReturn: customer_id, total_paid",
        solution="SELECT o.customer_id, SUM(p.amount) FROM payments p"
                 " JOIN orders o ON o.order_id = p.order_id"
                 " WHERE p.status = 'PAID' GROUP BY o.customer_id",
        trap_sql="SELECT o.customer_id, SUM(p.amount) FROM payments p"
                 " JOIN orders o ON o.order_id = p.order_id"
                 " JOIN order_items oi ON oi.order_id = o.order_id"
                 " WHERE p.status = 'PAID' GROUP BY o.customer_id",
        note="Joining a second one-to-many table repeats the parent value once per "
             "child row. Sum a value at the grain it actually lives at.",
    ),
    dict(
        id=4, ledger="Q045", concept="C2", tier="Grain",
        title="Monthly orders and distinct buyers",
        prompt="For each month of 2025: how many orders were placed, and how many "
               "DIFFERENT customers placed them. Month as YYYY-MM.\n\n"
               "Return: month, order_count, distinct_customers",
        solution="SELECT strftime('%Y-%m', order_date), COUNT(*), COUNT(DISTINCT customer_id)"
                 " FROM orders WHERE order_date >= '2025-01-01' AND order_date < '2026-01-01'"
                 " GROUP BY strftime('%Y-%m', order_date)",
        trap_sql="SELECT strftime('%Y-%m', order_date), COUNT(*), COUNT(customer_id)"
                 " FROM orders WHERE order_date >= '2025-01-01' AND order_date < '2026-01-01'"
                 " GROUP BY strftime('%Y-%m', order_date)",
        note="COUNT(customer_id) counts rows that have a customer, not distinct "
             "customers. Ask what one output row is meant to represent.",
    ),

    # ================================================================= C7 NULLs
    dict(
        id=5, ledger="Q046", concept="C7", tier="NULLs",
        title="Two averages over a nullable column",
        prompt="helpful_votes is NULL when nobody has voted yet, which is not the same "
               "as zero votes. Return the average helpful_votes across all reviews two "
               "ways: excluding the unknowns, then treating every unknown as 0.\n\n"
               "Return: avg_excluding_unknown, avg_unknown_as_zero",
        solution="SELECT AVG(helpful_votes), AVG(COALESCE(helpful_votes, 0)) FROM reviews",
        trap_sql="SELECT AVG(helpful_votes),"
                 " 1.0 * SUM(helpful_votes) / COUNT(helpful_votes) FROM reviews",
        note="AVG divides by the count of NON-NULL values, not the row count. To treat "
             "missing as zero you must say so with COALESCE.",
    ),
    dict(
        id=6, ledger="Q047", concept="C7", tier="NULLs",
        title="Keeping the outer join",
        prompt="Every order, with the amount of its PAID payment beside it, or NULL "
               "where there is no paid payment. All 165 orders must appear.\n\n"
               "Return: order_id, paid_amount",
        solution="SELECT o.order_id, p.amount FROM orders o"
                 " LEFT JOIN payments p ON p.order_id = o.order_id AND p.status = 'PAID'",
        trap_sql="SELECT o.order_id, p.amount FROM orders o"
                 " LEFT JOIN payments p ON p.order_id = o.order_id"
                 " WHERE p.status = 'PAID'",
        note="ON decides what matches; WHERE decides what survives. A WHERE on the "
             "optional side filters out the NULL rows and silently makes it an inner join.",
    ),
    dict(
        id=7, ledger="Q048", concept="C7", tier="NULLs",
        title="Employees who manage nobody",
        prompt="Employees who are not anybody's manager.\n\n"
               "Return: employee_id, employee_name (first + space + last)",
        solution="SELECT e.employee_id, e.first_name || ' ' || e.last_name FROM employees e"
                 " WHERE NOT EXISTS (SELECT 1 FROM employees m"
                 "                   WHERE m.manager_id = e.employee_id)",
        trap_sql="SELECT e.employee_id, e.first_name || ' ' || e.last_name FROM employees e"
                 " WHERE e.employee_id NOT IN (SELECT manager_id FROM employees)",
        note="manager_id contains a NULL (the CEO reports to nobody), and NOT IN against "
             "a set containing NULL is never true -- it returns zero rows. Use NOT EXISTS.",
    ),
    dict(
        id=8, ledger="Q049", concept="C7", tier="NULLs",
        title="Total compensation",
        prompt="Total annual compensation for every employee: salary, plus commission "
               "of salary x commission_rate. Staff not on a commission scheme have a "
               "NULL rate and simply earn their salary. All 12 employees must appear.\n\n"
               "Return: employee_name (first + space + last), total_comp",
        solution="SELECT first_name || ' ' || last_name,"
                 " salary * (1 + COALESCE(commission_rate, 0)) FROM employees",
        trap_sql="SELECT first_name || ' ' || last_name,"
                 " salary * (1 + commission_rate) FROM employees",
        note="NULL propagates through arithmetic: anything times NULL is NULL. Seven of "
             "the twelve are not on a scheme, so the naive formula wipes out their pay.",
    ),

    # ==================================================== C1 aggregates in WHERE
    dict(
        id=9, ledger="Q050", concept="C1", tier="Aggregates in WHERE",
        title="Above-average payments",
        prompt="Payments with status 'PAID' whose amount is greater than the average "
               "amount of all PAID payments.\n\nReturn: payment_id, order_id, amount",
        solution="SELECT payment_id, order_id, amount FROM payments"
                 " WHERE status = 'PAID'"
                 "   AND amount > (SELECT AVG(amount) FROM payments WHERE status = 'PAID')",
        trap_sql="SELECT payment_id, order_id, amount FROM payments"
                 " WHERE status = 'PAID' GROUP BY payment_id HAVING amount > AVG(amount)",
        note="WHERE sees one row at a time, so the average does not exist yet. Give it "
             "its own scope in a scalar subquery. HAVING here compares each payment to "
             "itself and quietly returns nothing.",
    ),
    dict(
        id=10, ledger="Q051", concept="C1", tier="Aggregates in WHERE",
        title="Busiest sales rep",
        prompt="The single sales rep who has taken the most orders.\n\n"
               "Return: rep_name (first + space + last), order_count",
        solution="SELECT e.first_name || ' ' || e.last_name, COUNT(*) FROM orders o"
                 " JOIN employees e ON e.employee_id = o.employee_id"
                 " GROUP BY e.employee_id ORDER BY COUNT(*) DESC LIMIT 1",
        trap_sql="SELECT e.first_name || ' ' || e.last_name, COUNT(*) FROM orders o"
                 " JOIN employees e ON e.employee_id = o.employee_id"
                 " GROUP BY e.employee_id ORDER BY COUNT(*) DESC",
        note="'Which group has the most' is a two-pass problem -- MAX(COUNT(*)) is "
             "illegal almost everywhere. ORDER BY ... DESC LIMIT 1 is the simple answer, "
             "and the LIMIT is the part that is easy to forget.",
    ),
    dict(
        id=11, ledger="Q052", concept="C1", tier="Aggregates in WHERE",
        title="Categories rated above the overall mean",
        prompt="Categories whose average review rating is higher than the average "
               "rating across every review in the database.\n\n"
               "Return: category name, avg_rating",
        solution="SELECT c.name, AVG(r.rating) FROM reviews r"
                 " JOIN products p ON p.product_id = r.product_id"
                 " JOIN categories c ON c.category_id = p.category_id"
                 " GROUP BY c.category_id"
                 " HAVING AVG(r.rating) > (SELECT AVG(rating) FROM reviews)",
        trap_sql="SELECT c.name, AVG(r.rating) FROM reviews r"
                 " JOIN products p ON p.product_id = r.product_id"
                 " JOIN categories c ON c.category_id = p.category_id"
                 " GROUP BY c.category_id HAVING AVG(r.rating) > AVG(r.rating)",
        note="HAVING compares a group against a CONSTANT, never against other groups. "
             "The global average has to come from a subquery with its own scope.",
    ),

    # =============================================== C3 PARTITION BY vs GROUP BY
    dict(
        id=12, ledger="Q053", concept="C3", tier="Window vs GROUP BY",
        title="Line detail beside the order total",
        prompt="Every line of every shipped order, keeping one row per line, with the "
               "revenue of that line and the revenue of the whole order beside it.\n\n"
               "Return: order_id, product_id, line_revenue, order_revenue",
        solution="SELECT oi.order_id, oi.product_id,"
                 " oi.quantity * oi.unit_price * (1 - oi.discount),"
                 " SUM(oi.quantity * oi.unit_price * (1 - oi.discount))"
                 "   OVER (PARTITION BY oi.order_id)"
                 " FROM order_items oi JOIN orders o ON o.order_id = oi.order_id"
                 " WHERE o.status = 'shipped'",
        trap_sql="SELECT oi.order_id, oi.product_id,"
                 " oi.quantity * oi.unit_price * (1 - oi.discount),"
                 " SUM(oi.quantity * oi.unit_price * (1 - oi.discount))"
                 " FROM order_items oi JOIN orders o ON o.order_id = oi.order_id"
                 " WHERE o.status = 'shipped' GROUP BY oi.order_id",
        note="GROUP BY collapses rows and loses the detail. PARTITION BY keeps every "
             "row and just scopes the calculation. You wanted one row per line.",
    ),
    dict(
        id=13, ledger="Q054", concept="C3", tier="Window vs GROUP BY",
        title="Running total per customer",
        prompt="Every PAID payment with a running cumulative total of that customer's "
               "paid amounts, ordered by paid_at then payment_id.\n\n"
               "Return: payment_id, customer_id, amount, running_total",
        solution="SELECT p.payment_id, o.customer_id, p.amount,"
                 " SUM(p.amount) OVER (PARTITION BY o.customer_id"
                 "                     ORDER BY p.paid_at, p.payment_id)"
                 " FROM payments p JOIN orders o ON o.order_id = p.order_id"
                 " WHERE p.status = 'PAID'",
        trap_sql="SELECT p.payment_id, o.customer_id, p.amount,"
                 " SUM(p.amount) OVER (PARTITION BY o.customer_id)"
                 " FROM payments p JOIN orders o ON o.order_id = p.order_id"
                 " WHERE p.status = 'PAID'",
        note="ORDER BY inside OVER changes the frame from 'the whole partition' to "
             "'start through current row'. Without it you get the partition total on "
             "every row, not a running total.",
    ),
    dict(
        id=14, ledger="Q055", concept="C3", tier="Window vs GROUP BY",
        title="Previous review for the same product",
        prompt="Every review with the rating of the previous review OF THE SAME PRODUCT, "
               "ordered by review_date then review_id. NULL where it is the first.\n\n"
               "Return: review_id, product_id, rating, prev_rating",
        solution="SELECT review_id, product_id, rating,"
                 " LAG(rating) OVER (PARTITION BY product_id ORDER BY review_date, review_id)"
                 " FROM reviews",
        trap_sql="SELECT review_id, product_id, rating,"
                 " LAG(rating) OVER (PARTITION BY rating ORDER BY review_date, review_id)"
                 " FROM reviews",
        note="Partition by the thing that makes rows a separate series -- the product. "
             "Partitioning by the column you are measuring walls each value off from "
             "itself. If the partition column and the measured column match, it is wrong.",
    ),

    # ================================================================= C5 COUNT
    dict(
        id=15, ledger="Q056", concept="C5", tier="COUNT",
        title="Orders per customer, including none",
        prompt="Every customer with the number of orders they have placed. The four who "
               "have never ordered must appear with 0.\n\n"
               "Return: customer_id, order_count",
        solution="SELECT cu.customer_id, COUNT(o.order_id) FROM customers cu"
                 " LEFT JOIN orders o ON o.customer_id = cu.customer_id"
                 " GROUP BY cu.customer_id",
        trap_sql="SELECT cu.customer_id, COUNT(*) FROM customers cu"
                 " LEFT JOIN orders o ON o.customer_id = cu.customer_id"
                 " GROUP BY cu.customer_id",
        note="An unmatched LEFT JOIN produces one all-NULL row, and COUNT(*) counts it "
             "-- so a customer with no orders reports 1. Name a column from the "
             "optional side.",
    ),
    dict(
        id=16, ledger="Q057", concept="C5", tier="COUNT",
        title="Paid payments per method",
        prompt="For each payment method: the total number of payments, and how many of "
               "them have status 'PAID'.\n\nReturn: method, total_payments, paid_count",
        solution="SELECT method, COUNT(*),"
                 " SUM(CASE WHEN status = 'PAID' THEN 1 ELSE 0 END)"
                 " FROM payments GROUP BY method",
        trap_sql="SELECT method, COUNT(*),"
                 " COUNT(CASE WHEN status = 'PAID' THEN 1 ELSE 0 END)"
                 " FROM payments GROUP BY method",
        note="ELSE 0 makes every row non-NULL, so COUNT counts all of them. Memorise the "
             "pairing: COUNT with no ELSE, or SUM with ELSE 0.",
    ),
    dict(
        id=17, ledger="Q058", concept="C5", tier="COUNT",
        title="How complete is each product's feedback",
        prompt="For each product that has at least one review: the number of reviews, "
               "how many included a written comment, and how many had helpful_votes "
               "recorded.\n\nReturn: product name, review_count, with_comment, with_votes",
        solution="SELECT p.name, COUNT(*), COUNT(r.comment), COUNT(r.helpful_votes)"
                 " FROM products p JOIN reviews r ON r.product_id = p.product_id"
                 " GROUP BY p.product_id",
        trap_sql="SELECT p.name, COUNT(*), COUNT(r.comment),"
                 " COUNT(COALESCE(r.helpful_votes, 0))"
                 " FROM products p JOIN reviews r ON r.product_id = p.product_id"
                 " GROUP BY p.product_id",
        note="COUNT(expr) counts rows where expr is NOT NULL. COALESCE fills the NULL "
             "in before COUNT can see it, so the count collapses to the row count.",
    ),

    # ====================================================== C6 alias vs formula
    dict(
        id=18, ledger="Q059", concept="C6", tier="Alias vs formula",
        title="Gross, discount, and net",
        prompt="For every order line: the gross value before discount, the discount "
               "amount in dollars, and the net revenue. discount is a RATE "
               "(0.05 = 5%).\n\n"
               "Return: order_id, product_id, gross, discount_amount, net",
        solution="SELECT order_id, product_id, quantity * unit_price,"
                 " quantity * unit_price * discount,"
                 " quantity * unit_price * (1 - discount) FROM order_items",
        trap_sql="SELECT order_id, product_id, quantity * unit_price,"
                 " quantity * unit_price * (1 - discount),"
                 " quantity * unit_price * discount FROM order_items",
        note="total * discount is the money taken OFF; total * (1 - discount) is what "
             "is left. Read every alias back against the formula to its left.",
    ),
    dict(
        id=19, ledger="Q060", concept="C6", tier="Alias vs formula",
        title="Conversion rate by country",
        prompt="For each country, the percentage of that country's customers who have "
               "placed at least one order. A percentage of the country's own customers, "
               "0 to 100.\n\nReturn: country, pct_with_orders",
        solution="SELECT cu.country,"
                 " 100.0 * COUNT(DISTINCT o.customer_id) / COUNT(DISTINCT cu.customer_id)"
                 " FROM customers cu LEFT JOIN orders o ON o.customer_id = cu.customer_id"
                 " GROUP BY cu.country",
        trap_sql="SELECT cu.country,"
                 " 100.0 * COUNT(DISTINCT o.customer_id) / COUNT(*)"
                 " FROM customers cu LEFT JOIN orders o ON o.customer_id = cu.customer_id"
                 " GROUP BY cu.country",
        note="After the join, COUNT(*) counts order rows, not customers -- so the "
             "denominator is wrong and the 'percentage' is not one. Check that the "
             "denominator is the population the name claims.",
    ),
    dict(
        id=20, ledger="Q061", concept="C6", tier="Alias vs formula",
        title="Change in paid volume",
        prompt="For each month, how many payments settled (status 'PAID', bucketed by "
               "paid_at) and the CHANGE in that count versus the previous month. NULL "
               "for the first month. Month as YYYY-MM.\n\n"
               "Return: month, paid_count, change_vs_prev",
        solution="WITH m AS (SELECT strftime('%Y-%m', paid_at) AS mo, COUNT(*) AS n"
                 "           FROM payments WHERE status = 'PAID' GROUP BY mo)"
                 " SELECT mo, n, n - LAG(n) OVER (ORDER BY mo) FROM m",
        trap_sql="WITH m AS (SELECT strftime('%Y-%m', paid_at) AS mo, COUNT(*) AS n"
                 "           FROM payments WHERE status = 'PAID' GROUP BY mo)"
                 " SELECT mo, n, LAG(n) OVER (ORDER BY mo) FROM m",
        note="LAG gives you the PREVIOUS value, not the change. The change is current "
             "minus previous -- the subtraction is yours to write.",
    ),

    # ====================================================== C9 integer division
    dict(
        id=21, ledger="Q062", concept="C9", tier="Integer division",
        title="Percentage of orders shipped",
        prompt="What percentage of all orders have a ship_date? One row, one column, "
               "0 to 100.\n\nReturn: pct_shipped",
        solution="SELECT 100.0 * COUNT(ship_date) / COUNT(*) FROM orders",
        trap_sql="SELECT 100 * COUNT(ship_date) / COUNT(*) FROM orders",
        note="In SQLite integer / integer is an integer -- 92 instead of 92.12. The "
             "fraction is thrown away before ROUND could ever see it. Force a decimal "
             "with 100.0. (The review is wrong that SQLite auto-converts; it does not.)",
    ),
    dict(
        id=22, ledger="Q063", concept="C9", tier="Integer division",
        title="Mean weight per weighed product",
        prompt="For each category: the total weight in grams of its products that have "
               "a recorded weight, and the mean grams per weighed product. Products with "
               "no recorded weight are excluded from both. Only categories with at least "
               "one weighed product.\n\nReturn: category name, total_grams, mean_grams",
        solution="SELECT c.name, SUM(p.weight_grams),"
                 " 1.0 * SUM(p.weight_grams) / COUNT(p.weight_grams)"
                 " FROM categories c JOIN products p ON p.category_id = c.category_id"
                 " WHERE p.weight_grams IS NOT NULL GROUP BY c.category_id",
        trap_sql="SELECT c.name, SUM(p.weight_grams),"
                 " SUM(p.weight_grams) / COUNT(p.weight_grams)"
                 " FROM categories c JOIN products p ON p.category_id = c.category_id"
                 " WHERE p.weight_grams IS NOT NULL GROUP BY c.category_id",
        note="SUM of integers over COUNT of integers is still integer division. Multiply "
             "by 1.0 first. AVG() would have been fine here -- it returns a real -- but "
             "the moment you write the division yourself, you own the type.",
    ),

    # ============================================================= C4 CTE scope
    dict(
        id=23, ledger="Q064", concept="C4", tier="CTE scope",
        title="Each customer's second-biggest order",
        prompt="For every customer with at least two shipped orders, their SECOND most "
               "valuable one. Rank each customer's shipped orders by value descending "
               "and take number 2.\n\n"
               "Return: customer_id, order_id, order_date, order_value",
        solution="WITH vals AS ("
                 "  SELECT o.order_id, o.customer_id, o.order_date,"
                 "         SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS val"
                 "  FROM orders o JOIN order_items oi ON oi.order_id = o.order_id"
                 "  WHERE o.status = 'shipped' GROUP BY o.order_id),"
                 " ranked AS ("
                 "  SELECT customer_id, order_id, order_date, val,"
                 "         ROW_NUMBER() OVER (PARTITION BY customer_id"
                 "                            ORDER BY val DESC) AS rn"
                 "  FROM vals)"
                 " SELECT customer_id, order_id, order_date, val FROM ranked WHERE rn = 2",
        trap_sql="WITH vals AS ("
                 "  SELECT o.order_id, o.customer_id,"
                 "         SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS val"
                 "  FROM orders o JOIN order_items oi ON oi.order_id = o.order_id"
                 "  WHERE o.status = 'shipped' GROUP BY o.order_id),"
                 " ranked AS ("
                 "  SELECT customer_id, order_id, val,"
                 "         ROW_NUMBER() OVER (PARTITION BY customer_id"
                 "                            ORDER BY val DESC) AS rn"
                 "  FROM vals)"
                 " SELECT customer_id, order_id, order_date, val FROM ranked WHERE rn = 2",
        note="A CTE is a wall: only the columns it SELECTs exist outside it. order_date "
             "was dropped on the way through, so the outer query cannot name it. List "
             "what the outer query needs before you write the CTE.",
    ),

    # =================================================================== general
    dict(
        id=24, ledger="Q065", concept="GEN", tier="General",
        title="Settled money by method",
        prompt="For payments with status 'PAID' only: how many per method and the total "
               "amount.\n\nReturn: method, paid_count, total_amount",
        solution="SELECT method, COUNT(*), SUM(amount) FROM payments"
                 " WHERE status = 'PAID' GROUP BY method",
        trap_sql="SELECT method, COUNT(*), SUM(amount) FROM payments"
                 " WHERE status = 'paid' GROUP BY method",
        note="String comparison is case-sensitive here: status is stored uppercase, so "
             "'paid' matches nothing and you get an empty result rather than an error.",
    ),
    dict(
        id=25, ledger="Q066", concept="GEN", tier="General",
        title="Heavy items",
        prompt="Products with a recorded weight over 5000 grams.\n\n"
               "Return: name, weight_grams",
        solution="SELECT name, weight_grams FROM products WHERE weight_grams > 5000",
        trap_sql="SELECT name, weight_grams FROM products WHERE weight_grams > 5000"
                 " OR weight_grams IS NULL",
        note="NULL is unknown, not heavy. A missing weight is not evidence of anything.",
    ),
    dict(
        id=26, ledger="Q067", concept="GEN", tier="General",
        title="Paid on the day of order",
        prompt="Orders whose payment settled on the same date the order was placed.\n\n"
               "Return: order_id, order_date, amount",
        solution="SELECT o.order_id, o.order_date, p.amount FROM orders o"
                 " JOIN payments p ON p.order_id = o.order_id"
                 " WHERE p.paid_at = o.order_date",
        trap_sql="SELECT o.order_id, o.order_date, p.amount FROM orders o"
                 " JOIN payments p ON p.order_id = o.order_id"
                 " WHERE p.paid_at >= o.order_date",
        note="Straightforward -- but note that rows where paid_at is NULL drop out of "
             "both versions, because NULL fails every comparison.",
    ),
    dict(
        id=27, ledger="Q068", concept="GEN", tier="General",
        title="Most reviewed products",
        prompt="The 5 products with the most reviews. Six products are tied on 6 "
               "reviews each, so break ties by product name, A-Z.\n\n"
               "Return: product name, review_count",
        solution="SELECT p.name, COUNT(*) FROM products p"
                 " JOIN reviews r ON r.product_id = p.product_id"
                 " GROUP BY p.product_id ORDER BY COUNT(*) DESC, p.name ASC LIMIT 5",
        trap_sql="SELECT p.name, COUNT(r.review_id) FROM products p"
                 " LEFT JOIN reviews r ON r.product_id = p.product_id"
                 " GROUP BY p.product_id ORDER BY COUNT(r.review_id) ASC LIMIT 5",
        note="Two lessons: read the direction (MOST, not least), and note that without "
             "the name tiebreak this question has no single answer -- six products tie "
             "on 6 reviews, so ORDER BY count alone lets the engine pick any of them.",
    ),
    dict(
        id=28, ledger="Q069", concept="GEN", tier="General",
        title="Customers with a refund",
        prompt="Customers who have had at least one payment refunded. One row per "
               "customer.\n\nReturn: customer_id, customer_name (first + space + last)",
        solution="SELECT DISTINCT cu.customer_id, cu.first_name || ' ' || cu.last_name"
                 " FROM customers cu JOIN orders o ON o.customer_id = cu.customer_id"
                 " JOIN payments p ON p.order_id = o.order_id"
                 " WHERE p.status = 'REFUNDED'",
        trap_sql="SELECT cu.customer_id, cu.first_name || ' ' || cu.last_name"
                 " FROM customers cu JOIN orders o ON o.customer_id = cu.customer_id"
                 " JOIN payments p ON p.order_id = o.order_id"
                 " WHERE p.status = 'REFUNDED'",
        note="A customer with two refunds appears twice without DISTINCT. 'Customers "
             "who...' means one row per customer.",
    ),
    dict(
        id=29, ledger="Q070", concept="GEN", tier="General",
        title="Hired before their manager",
        prompt="Employees who were hired BEFORE the manager they report to.\n\n"
               "Return: employee_name, manager_name, employee_hire_date, manager_hire_date",
        solution="SELECT e.first_name || ' ' || e.last_name,"
                 " m.first_name || ' ' || m.last_name, e.hire_date, m.hire_date"
                 " FROM employees e JOIN employees m ON m.employee_id = e.manager_id"
                 " WHERE e.hire_date < m.hire_date",
        trap_sql="SELECT e.first_name || ' ' || e.last_name,"
                 " m.first_name || ' ' || m.last_name, e.hire_date, m.hire_date"
                 " FROM employees e LEFT JOIN employees m ON m.employee_id = e.manager_id"
                 " WHERE e.hire_date < m.hire_date OR m.employee_id IS NULL",
        note="The CEO has no manager, so there is nothing to compare -- an employee with "
             "no manager is not an employee hired before their manager.",
    ),
    dict(
        id=30, ledger="Q071", concept="GEN", tier="General",
        title="Well-reviewed categories",
        prompt="Categories with at least 10 reviews across all their products, with the "
               "average rating.\n\nReturn: category name, review_count, avg_rating",
        solution="SELECT c.name, COUNT(*), AVG(r.rating) FROM categories c"
                 " JOIN products p ON p.category_id = c.category_id"
                 " JOIN reviews r ON r.product_id = p.product_id"
                 " GROUP BY c.category_id HAVING COUNT(*) >= 10",
        trap_sql="SELECT c.name, COUNT(*), AVG(r.rating) FROM categories c"
                 " JOIN products p ON p.category_id = c.category_id"
                 " JOIN reviews r ON r.product_id = p.product_id"
                 " GROUP BY c.category_id HAVING COUNT(*) >= 100",
        note="A count of the whole group cannot be tested in WHERE, which runs one row "
             "at a time before any grouping happens. That filter belongs in HAVING.",
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
