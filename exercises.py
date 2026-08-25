"""Practice exercises with reference solutions, used by the GUI to grade answers.

These 30 questions target the nine recurring mistakes catalogued in
sql-concepts-review.html, weighted by how often each one showed up, and are
built on the fulfilment side of the schema -- warehouses, inventory, shipments
and returns. Each question carries:

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

The one structural fact worth holding onto: an order can be SPLIT across
warehouses, so orders have 0..n shipments as well as 0..n lines. Joining both
children in one query multiplies the rows and inflates every total.
"""

EXERCISES = [
    # ================================================================= C2 grain
    dict(
        id=1, ledger="Q072", concept="C2", tier="Grain",
        title="Freight per order",
        prompt="Total freight cost for each order that has at least one shipment.\n\n"
               "Return: order_id, total_freight",
        solution="SELECT order_id, SUM(freight_cost) FROM shipments GROUP BY order_id",
        trap_sql="SELECT s.order_id, SUM(s.freight_cost) FROM shipments s"
                 " JOIN order_items oi ON oi.order_id = s.order_id"
                 " GROUP BY s.order_id",
        note="Freight lives on the shipment, not the line. Joining order_items repeats "
               "each freight cost once per line -- here that turns 7,932 into 23,436.",
    ),
    dict(
        id=2, ledger="Q073", concept="C2", tier="Grain",
        title="Stock per product across warehouses",
        prompt="For every product stocked in at least one warehouse: the total quantity "
               "on hand summed across all warehouses. One row per product.\n\n"
               "Return: product_id, total_on_hand",
        solution="SELECT product_id, SUM(quantity_on_hand) FROM inventory GROUP BY product_id",
        trap_sql="SELECT product_id, SUM(quantity_on_hand) FROM inventory"
                 " GROUP BY product_id, warehouse_id",
        note="Adding warehouse_id to the GROUP BY changes what one row means: you get "
             "one row per warehouse, not per product. The key list defines the grain.",
    ),
    dict(
        id=3, ledger="Q074", concept="C2", tier="Grain",
        title="Revenue and freight side by side",
        prompt="For each shipped order that has at least one shipment: its revenue "
               "(sum over its lines) and its freight (sum over its shipments). Both "
               "children must be aggregated separately.\n\n"
               "Return: order_id, revenue, freight",
        solution="WITH rev AS (SELECT oi.order_id,"
                 "   SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS r"
                 "   FROM order_items oi JOIN orders o ON o.order_id = oi.order_id"
                 "   WHERE o.status = 'shipped' GROUP BY oi.order_id),"
                 " frt AS (SELECT order_id, SUM(freight_cost) AS f"
                 "   FROM shipments GROUP BY order_id)"
                 " SELECT rev.order_id, rev.r, frt.f FROM rev JOIN frt USING(order_id)",
        trap_sql="SELECT o.order_id,"
                 " SUM(oi.quantity * oi.unit_price * (1 - oi.discount)), SUM(s.freight_cost)"
                 " FROM orders o JOIN order_items oi ON oi.order_id = o.order_id"
                 " JOIN shipments s ON s.order_id = o.order_id"
                 " WHERE o.status = 'shipped' GROUP BY o.order_id",
        note="Two one-to-many children joined in one query is the classic fan-out: every "
             "line repeats per shipment AND every freight cost repeats per line, so both "
             "totals inflate. Aggregate each branch to one row per order first, then join.",
    ),
    dict(
        id=4, ledger="Q075", concept="C2", tier="Grain",
        title="Units sold against units returned",
        prompt="For each category: the total units sold on shipped orders, and the total "
               "units returned. Categories with sales but no returns must still appear, "
               "with 0 returned.\n\nReturn: category name, units_sold, units_returned",
        solution="SELECT c.name, SUM(oi.quantity),"
                 " COALESCE(SUM(r.quantity), 0)"
                 " FROM order_items oi"
                 " JOIN orders o ON o.order_id = oi.order_id"
                 " JOIN products p ON p.product_id = oi.product_id"
                 " JOIN categories c ON c.category_id = p.category_id"
                 " LEFT JOIN returns r ON r.order_id = oi.order_id"
                 "                    AND r.product_id = oi.product_id"
                 " WHERE o.status = 'shipped' GROUP BY c.category_id",
        trap_sql="SELECT c.name, SUM(oi.quantity), SUM(r.quantity)"
                 " FROM order_items oi"
                 " JOIN orders o ON o.order_id = oi.order_id"
                 " JOIN products p ON p.product_id = oi.product_id"
                 " JOIN categories c ON c.category_id = p.category_id"
                 " JOIN returns r ON r.order_id = oi.order_id"
                 "               AND r.product_id = oi.product_id"
                 " WHERE o.status = 'shipped' GROUP BY c.category_id",
        note="An inner join to returns throws away every line that was never returned, so "
             "units_sold collapses to 'units sold that later came back'. The join type "
             "decides the population you are summing over.",
    ),

    # ================================================================= C7 NULLs
    dict(
        id=5, ledger="Q076", concept="C7", tier="NULLs",
        title="Delivered or still in transit",
        prompt="Every shipment, showing its delivery date, or the text 'in transit' where "
               "it has not arrived yet.\n\nReturn: shipment_id, order_id, delivery_status",
        solution="SELECT shipment_id, order_id, COALESCE(delivered_at, 'in transit')"
                 " FROM shipments",
        trap_sql="SELECT shipment_id, order_id,"
                 " CASE WHEN delivered_at = NULL THEN 'in transit' ELSE delivered_at END"
                 " FROM shipments",
        note="Nothing equals NULL -- not even NULL. `delivered_at = NULL` is never true, "
             "so the CASE falls through to ELSE and hands back the NULL you were trying "
             "to replace. Use IS NULL, or COALESCE.",
    ),
    dict(
        id=6, ledger="Q077", concept="C7", tier="NULLs",
        title="Average days in transit",
        prompt="For each carrier, the average number of days from shipped_at to "
               "delivered_at. Shipments still in transit have no transit time yet and "
               "must not count towards the average.\n\n"
               "Return: carrier, avg_transit_days",
        solution="SELECT carrier, AVG(julianday(delivered_at) - julianday(shipped_at))"
                 " FROM shipments WHERE delivered_at IS NOT NULL GROUP BY carrier",
        trap_sql="SELECT carrier,"
                 " SUM(julianday(delivered_at) - julianday(shipped_at)) / COUNT(*)"
                 " FROM shipments GROUP BY carrier",
        note="AVG divides by the number of NON-NULL values; dividing by COUNT(*) divides "
             "by every row including the ones still in transit, dragging the average down.",
    ),
    dict(
        id=7, ledger="Q078", concept="C7", tier="NULLs",
        title="Value of counted stock",
        prompt="For each warehouse, the value of the stock that has actually been "
               "physically counted: quantity_on_hand x unit_cost, over inventory lines "
               "with a last_counted_at date. Lines never counted are excluded.\n\n"
               "Return: warehouse name, counted_value",
        solution="SELECT w.name, SUM(i.quantity_on_hand * p.unit_cost)"
                 " FROM inventory i"
                 " JOIN warehouses w ON w.warehouse_id = i.warehouse_id"
                 " JOIN products p ON p.product_id = i.product_id"
                 " WHERE i.last_counted_at IS NOT NULL GROUP BY w.warehouse_id",
        trap_sql="SELECT w.name, SUM(i.quantity_on_hand * p.unit_cost)"
                 " FROM inventory i"
                 " JOIN warehouses w ON w.warehouse_id = i.warehouse_id"
                 " JOIN products p ON p.product_id = i.product_id"
                 " GROUP BY w.warehouse_id",
        note="'Never counted' is a real state, not a zero. Dropping the IS NOT NULL "
             "filter quietly reports uncounted stock as if it had been verified.",
    ),
    dict(
        id=8, ledger="Q079", concept="C7", tier="NULLs",
        title="Quantities matching no reorder level",
        prompt="Inventory lines whose quantity_on_hand does not equal the reorder_level "
               "of ANY line in the table. reorder_level is NULL where no policy has been "
               "agreed -- an unknown is not a value, so it must not knock out rows.\n\n"
               "Return: warehouse_id, product_id, quantity_on_hand",
        solution="SELECT i.warehouse_id, i.product_id, i.quantity_on_hand FROM inventory i"
                 " WHERE NOT EXISTS (SELECT 1 FROM inventory x"
                 "                   WHERE x.reorder_level = i.quantity_on_hand)",
        trap_sql="SELECT i.warehouse_id, i.product_id, i.quantity_on_hand FROM inventory i"
                 " WHERE i.quantity_on_hand NOT IN (SELECT reorder_level FROM inventory)",
        note="NOT IN against a set containing a NULL is never true, so it returns zero "
             "rows -- silently, with no error. NOT EXISTS is the safe form for anti-joins.",
    ),

    # ==================================================== C1 aggregates in WHERE
    dict(
        id=9, ledger="Q080", concept="C1", tier="Aggregates in WHERE",
        title="Pricey shipments for their carrier",
        prompt="Shipments whose freight_cost is above the average freight_cost for THAT "
               "SHIPMENT'S OWN carrier.\n\n"
               "Return: shipment_id, carrier, freight_cost",
        solution="SELECT s.shipment_id, s.carrier, s.freight_cost FROM shipments s"
                 " WHERE s.freight_cost > (SELECT AVG(x.freight_cost) FROM shipments x"
                 "                         WHERE x.carrier = s.carrier)",
        trap_sql="SELECT s.shipment_id, s.carrier, s.freight_cost FROM shipments s"
                 " WHERE s.freight_cost > (SELECT AVG(freight_cost) FROM shipments)",
        note="The comparison has to be correlated to each row's own carrier. A plain "
             "scalar subquery compares everything to one global average instead.",
    ),
    dict(
        id=10, ledger="Q081", concept="C1", tier="Aggregates in WHERE",
        title="Busier than the average warehouse",
        prompt="Warehouses that have dispatched more shipments than the average number "
               "of shipments per warehouse.\n\n"
               "Return: warehouse name, shipment_count",
        solution="SELECT w.name, COUNT(*) FROM shipments s"
                 " JOIN warehouses w ON w.warehouse_id = s.warehouse_id"
                 " GROUP BY s.warehouse_id"
                 " HAVING COUNT(*) > (SELECT AVG(n) FROM"
                 "   (SELECT COUNT(*) AS n FROM shipments GROUP BY warehouse_id))",
        trap_sql="SELECT w.name, COUNT(*) FROM shipments s"
                 " JOIN warehouses w ON w.warehouse_id = s.warehouse_id"
                 " GROUP BY s.warehouse_id"
                 " HAVING COUNT(*) > (SELECT AVG(freight_cost) FROM shipments)",
        note="'More than the average per group' needs two passes: count per warehouse, "
             "then average those counts. Comparing a count against the average of some "
             "other column runs clean and means nothing.",
    ),
    dict(
        id=11, ledger="Q082", concept="C1", tier="Aggregates in WHERE",
        title="Categories with above-average margin",
        prompt="Categories whose AVERAGE unit margin (unit_price - unit_cost) is above "
               "the average unit margin across all products.\n\n"
               "Return: category name, avg_margin",
        solution="SELECT c.name, AVG(p.unit_price - p.unit_cost) FROM products p"
                 " JOIN categories c ON c.category_id = p.category_id"
                 " GROUP BY c.category_id"
                 " HAVING AVG(p.unit_price - p.unit_cost) >"
                 "   (SELECT AVG(unit_price - unit_cost) FROM products)",
        trap_sql="SELECT c.name, AVG(p.unit_price - p.unit_cost) FROM products p"
                 " JOIN categories c ON c.category_id = p.category_id"
                 " WHERE (p.unit_price - p.unit_cost) >"
                 "   (SELECT AVG(unit_price - unit_cost) FROM products)"
                 " GROUP BY c.category_id",
        note="WHERE filters rows BEFORE grouping, so you end up averaging only the "
             "already-above-average products -- a different question, and every category "
             "with one good product passes. The group-level test belongs in HAVING.",
    ),

    # =============================================== C3 PARTITION BY vs GROUP BY
    dict(
        id=12, ledger="Q083", concept="C3", tier="Window vs GROUP BY",
        title="Shipment beside its order's freight",
        prompt="Every shipment, one row each, with its own freight cost and the total "
               "freight of the order it belongs to.\n\n"
               "Return: shipment_id, order_id, freight_cost, order_freight",
        solution="SELECT shipment_id, order_id, freight_cost,"
                 " SUM(freight_cost) OVER (PARTITION BY order_id) FROM shipments",
        trap_sql="SELECT shipment_id, order_id, freight_cost, SUM(freight_cost)"
                 " FROM shipments GROUP BY order_id",
        note="GROUP BY collapses the 44 split orders down to one row each and loses the "
             "individual shipments. PARTITION BY keeps every row and scopes the total.",
    ),
    dict(
        id=13, ledger="Q084", concept="C3", tier="Window vs GROUP BY",
        title="Share of a product's stock",
        prompt="For every inventory line: the quantity on hand and what fraction of that "
               "PRODUCT'S total stock across all warehouses it represents (0 to 1).\n\n"
               "Return: warehouse_id, product_id, quantity_on_hand, share_of_product",
        solution="SELECT warehouse_id, product_id, quantity_on_hand,"
                 " quantity_on_hand * 1.0 / SUM(quantity_on_hand)"
                 "   OVER (PARTITION BY product_id) FROM inventory",
        trap_sql="SELECT warehouse_id, product_id, quantity_on_hand,"
                 " quantity_on_hand * 1.0 / SUM(quantity_on_hand)"
                 "   OVER (PARTITION BY warehouse_id) FROM inventory",
        note="Partition by the thing the share is OF. Partitioning by warehouse gives "
             "each line's share of its warehouse, which is a different question with "
             "equally plausible-looking numbers.",
    ),
    dict(
        id=14, ledger="Q085", concept="C3", tier="Window vs GROUP BY",
        title="First shipment of each order",
        prompt="For each order that has shipments, the details of its EARLIEST shipment "
               "by shipped_at, breaking ties by the lower shipment_id.\n\n"
               "Return: order_id, shipment_id, shipped_at, carrier",
        solution="WITH ranked AS (SELECT order_id, shipment_id, shipped_at, carrier,"
                 "  ROW_NUMBER() OVER (PARTITION BY order_id"
                 "                     ORDER BY shipped_at, shipment_id) AS rn"
                 "  FROM shipments)"
                 " SELECT order_id, shipment_id, shipped_at, carrier"
                 " FROM ranked WHERE rn = 1",
        trap_sql="SELECT order_id, MIN(shipment_id), shipped_at, carrier"
                 " FROM shipments GROUP BY order_id",
        note="MIN() on one column does not drag the rest of its row along. The lowest "
             "shipment_id is not necessarily the earliest shipment, and shipped_at and "
             "carrier come from whichever row the engine happened to hold. Rank, then "
             "filter -- that is what ROW_NUMBER is for.",
    ),

    # ================================================================= C5 COUNT
    dict(
        id=15, ledger="Q086", concept="C5", tier="COUNT",
        title="Warehouses stocking each product",
        prompt="Every product with the number of warehouses that stock it. The three "
               "stocked nowhere must appear with 0.\n\n"
               "Return: product_id, warehouse_count",
        solution="SELECT p.product_id, COUNT(i.warehouse_id) FROM products p"
                 " LEFT JOIN inventory i ON i.product_id = p.product_id"
                 " GROUP BY p.product_id",
        trap_sql="SELECT p.product_id, COUNT(*) FROM products p"
                 " LEFT JOIN inventory i ON i.product_id = p.product_id"
                 " GROUP BY p.product_id",
        note="The outer join manufactures one all-NULL row for a product stocked nowhere, "
             "and COUNT(*) counts it -- reporting 1 warehouse where there are none.",
    ),
    dict(
        id=16, ledger="Q087", concept="C5", tier="COUNT",
        title="Dispatched versus delivered",
        prompt="For each carrier: how many shipments it has been given, and how many of "
               "those have actually been delivered.\n\n"
               "Return: carrier, dispatched, delivered",
        solution="SELECT carrier, COUNT(*), COUNT(delivered_at) FROM shipments"
                 " GROUP BY carrier",
        trap_sql="SELECT carrier, COUNT(*), COUNT(shipment_id) FROM shipments"
                 " GROUP BY carrier",
        note="COUNT(expr) counts rows where expr is NOT NULL. Counting a NOT NULL column "
             "like shipment_id just re-counts the rows -- the column has to be the "
             "nullable one that encodes the thing you are asking about.",
    ),
    dict(
        id=17, ledger="Q088", concept="C5", tier="COUNT",
        title="Warehouse activity",
        prompt="For each warehouse: the number of shipments dispatched, the number of "
               "DISTINCT orders they belonged to, and the number of DISTINCT carriers "
               "used.\n\nReturn: warehouse name, shipments, distinct_orders, distinct_carriers",
        solution="SELECT w.name, COUNT(*), COUNT(DISTINCT s.order_id),"
                 " COUNT(DISTINCT s.carrier)"
                 " FROM shipments s JOIN warehouses w ON w.warehouse_id = s.warehouse_id"
                 " GROUP BY s.warehouse_id",
        trap_sql="SELECT w.name, COUNT(*), COUNT(s.order_id), COUNT(s.carrier)"
                 " FROM shipments s JOIN warehouses w ON w.warehouse_id = s.warehouse_id"
                 " GROUP BY s.warehouse_id",
        note="Without DISTINCT you are counting rows, not things. An order split into two "
             "shipments from the same warehouse would be counted twice.",
    ),

    # ====================================================== C6 alias vs formula
    dict(
        id=18, ledger="Q089", concept="C6", tier="Alias vs formula",
        title="Margin percentage",
        prompt="For each product: its price, its cost, the margin in dollars, and the "
               "margin as a percentage OF THE PRICE (0 to 100).\n\n"
               "Return: name, unit_price, unit_cost, margin, margin_pct",
        solution="SELECT name, unit_price, unit_cost, unit_price - unit_cost,"
                 " 100.0 * (unit_price - unit_cost) / unit_price FROM products",
        trap_sql="SELECT name, unit_price, unit_cost, unit_price - unit_cost,"
                 " 100.0 * (unit_price - unit_cost) / unit_cost FROM products",
        note="Dividing by cost gives MARKUP, not margin -- it can exceed 100%, which "
             "margin never can. Read the alias and ask what the denominator should be.",
    ),
    dict(
        id=19, ledger="Q090", concept="C6", tier="Alias vs formula",
        title="Freight as a share of revenue",
        prompt="For each shipped order that has both lines and shipments: freight as a "
               "percentage OF revenue (0 to 100). Aggregate each side separately first.\n\n"
               "Return: order_id, freight_pct_of_revenue",
        solution="WITH rev AS (SELECT oi.order_id,"
                 "   SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS r"
                 "   FROM order_items oi JOIN orders o ON o.order_id = oi.order_id"
                 "   WHERE o.status = 'shipped' GROUP BY oi.order_id),"
                 " frt AS (SELECT order_id, SUM(freight_cost) AS f"
                 "   FROM shipments GROUP BY order_id)"
                 " SELECT rev.order_id, 100.0 * frt.f / rev.r"
                 " FROM rev JOIN frt USING(order_id)",
        trap_sql="WITH rev AS (SELECT oi.order_id,"
                 "   SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS r"
                 "   FROM order_items oi JOIN orders o ON o.order_id = oi.order_id"
                 "   WHERE o.status = 'shipped' GROUP BY oi.order_id),"
                 " frt AS (SELECT order_id, SUM(freight_cost) AS f"
                 "   FROM shipments GROUP BY order_id)"
                 " SELECT rev.order_id, 100.0 * rev.r / frt.f"
                 " FROM rev JOIN frt USING(order_id)",
        note="'A as a share of B' puts B on the bottom. Inverting it produces numbers in "
             "the hundreds that still look like a plausible percentage at a glance.",
    ),
    dict(
        id=20, ledger="Q091", concept="C6", tier="Alias vs formula",
        title="Return rate by product",
        prompt="For products that have had at least one return: units sold on shipped "
               "orders, units returned, and the return rate as a percentage OF UNITS "
               "SOLD (0 to 100).\n\n"
               "Return: product_id, units_sold, units_returned, return_rate_pct",
        solution="WITH sold AS (SELECT oi.product_id, SUM(oi.quantity) AS s"
                 "   FROM order_items oi JOIN orders o ON o.order_id = oi.order_id"
                 "   WHERE o.status = 'shipped' GROUP BY oi.product_id),"
                 " back AS (SELECT product_id, SUM(quantity) AS b"
                 "   FROM returns GROUP BY product_id)"
                 " SELECT sold.product_id, sold.s, back.b, 100.0 * back.b / sold.s"
                 " FROM sold JOIN back USING(product_id)",
        trap_sql="WITH sold AS (SELECT oi.product_id, SUM(oi.quantity) AS s"
                 "   FROM order_items oi JOIN orders o ON o.order_id = oi.order_id"
                 "   WHERE o.status = 'shipped' GROUP BY oi.product_id),"
                 " back AS (SELECT product_id, SUM(quantity) AS b"
                 "   FROM returns GROUP BY product_id)"
                 " SELECT sold.product_id, sold.s, back.b,"
                 " 100.0 * back.b / (sold.s - back.b)"
                 " FROM sold JOIN back USING(product_id)",
        note="Returned over kept is a ratio; returned over sold is the rate. They agree "
             "when returns are rare, which is exactly why the mistake survives review.",
    ),

    # ====================================================== C9 integer division
    dict(
        id=21, ledger="Q092", concept="C9", tier="Integer division",
        title="Delivery rate by carrier",
        prompt="For each carrier, the percentage of its shipments that have been "
               "delivered, 0 to 100.\n\nReturn: carrier, pct_delivered",
        solution="SELECT carrier, 100.0 * COUNT(delivered_at) / COUNT(*)"
                 " FROM shipments GROUP BY carrier",
        trap_sql="SELECT carrier, 100 * COUNT(delivered_at) / COUNT(*)"
                 " FROM shipments GROUP BY carrier",
        note="Two integer counts divide to an integer in SQLite, so every carrier lands "
             "on a whole number and the fraction is gone before ROUND could see it. "
             "100.0 forces the whole expression to a real.",
    ),
    dict(
        id=22, ledger="Q093", concept="C9", tier="Integer division",
        title="Capacity used",
        prompt="For each warehouse: total units on hand, its capacity, and units on hand "
               "as a percentage of capacity (0 to 100).\n\n"
               "Return: warehouse name, units_on_hand, capacity_units, pct_of_capacity",
        solution="SELECT w.name, SUM(i.quantity_on_hand), w.capacity_units,"
                 " 100.0 * SUM(i.quantity_on_hand) / w.capacity_units"
                 " FROM warehouses w JOIN inventory i ON i.warehouse_id = w.warehouse_id"
                 " GROUP BY w.warehouse_id",
        trap_sql="SELECT w.name, SUM(i.quantity_on_hand), w.capacity_units,"
                 " 100 * SUM(i.quantity_on_hand) / w.capacity_units"
                 " FROM warehouses w JOIN inventory i ON i.warehouse_id = w.warehouse_id"
                 " GROUP BY w.warehouse_id",
        note="Both quantity_on_hand and capacity_units are INTEGER, so the whole "
             "expression stays integer and every warehouse reports 0% -- a number wrong "
             "enough to notice, but only if you look.",
    ),

    # ============================================================= C4 CTE scope
    dict(
        id=23, ledger="Q094", concept="C4", tier="CTE scope",
        title="Orders where freight bites",
        prompt="Shipped orders where freight is more than 8% of revenue, showing the date "
               "the order was placed. Build revenue and freight in CTEs first.\n\n"
               "Return: order_id, order_date, revenue, freight",
        solution="WITH rev AS (SELECT oi.order_id, o.order_date,"
                 "   SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS r"
                 "   FROM order_items oi JOIN orders o ON o.order_id = oi.order_id"
                 "   WHERE o.status = 'shipped' GROUP BY oi.order_id),"
                 " frt AS (SELECT order_id, SUM(freight_cost) AS f"
                 "   FROM shipments GROUP BY order_id)"
                 " SELECT rev.order_id, rev.order_date, rev.r, frt.f"
                 " FROM rev JOIN frt USING(order_id) WHERE frt.f > 0.08 * rev.r",
        trap_sql="WITH rev AS (SELECT oi.order_id,"
                 "   SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS r"
                 "   FROM order_items oi JOIN orders o ON o.order_id = oi.order_id"
                 "   WHERE o.status = 'shipped' GROUP BY oi.order_id),"
                 " frt AS (SELECT order_id, SUM(freight_cost) AS f"
                 "   FROM shipments GROUP BY order_id)"
                 " SELECT rev.order_id, rev.order_date, rev.r, frt.f"
                 " FROM rev JOIN frt USING(order_id) WHERE frt.f > 0.08 * rev.r",
        note="The CTE is a wall: the outer query can see only the columns the CTE "
             "selected, never the tables behind it. order_date has to be carried through "
             "explicitly. List what the outer query needs before you write the CTE.",
    ),

    # =================================================================== general
    dict(
        id=24, ledger="Q095", concept="GEN", tier="General",
        title="Large established warehouses",
        prompt="Warehouses opened before 2020 with a capacity above 300000 units.\n\n"
               "Return: name, city, capacity_units, opened_on",
        solution="SELECT name, city, capacity_units, opened_on FROM warehouses"
                 " WHERE opened_on < '2020-01-01' AND capacity_units > 300000",
        trap_sql="SELECT name, city, capacity_units, opened_on FROM warehouses"
                 " WHERE opened_on < '2020-01-01' OR capacity_units > 300000",
        note="'A and B' is not 'A or B'. With only four rows the difference is easy to "
             "eyeball -- on a real table it would not be.",
    ),
    dict(
        id=25, ledger="Q096", concept="GEN", tier="General",
        title="Carriers by freight spend",
        prompt="The 2 carriers we have spent the most with in TOTAL. Break ties by "
               "carrier name, A-Z.\n\nReturn: carrier, total_freight, shipments",
        solution="SELECT carrier, SUM(freight_cost), COUNT(*) FROM shipments"
                 " GROUP BY carrier ORDER BY SUM(freight_cost) DESC, carrier ASC LIMIT 2",
        trap_sql="SELECT carrier, SUM(freight_cost), COUNT(*) FROM shipments"
                 " GROUP BY carrier ORDER BY AVG(freight_cost) DESC, carrier ASC LIMIT 2",
        note="Biggest total spend is not highest cost per shipment. DPD averages more "
             "per parcel than UPS but UPS carries more of them, so the two orderings "
             "disagree. Sort by the measure the question actually names.",
    ),
    dict(
        id=26, ledger="Q097", concept="GEN", tier="General",
        title="Why things come back",
        prompt="For each return reason: how many returns and the total refunded.\n\n"
               "Return: reason, returns, total_refunded",
        solution="SELECT reason, COUNT(*), SUM(refund_amount) FROM returns GROUP BY reason",
        trap_sql="SELECT reason, COUNT(*), SUM(quantity) FROM returns GROUP BY reason",
        note="Units and money are not interchangeable. Check you summed the column the "
             "question named.",
    ),
    dict(
        id=27, ledger="Q098", concept="GEN", tier="General",
        title="Loyalty programme uptake",
        prompt="How many customers sit in each loyalty tier. Customers who never enrolled "
               "have a NULL tier and must be reported under the label 'not enrolled'.\n\n"
               "Return: tier, customers",
        solution="SELECT COALESCE(loyalty_tier, 'not enrolled'), COUNT(*)"
                 " FROM customers GROUP BY COALESCE(loyalty_tier, 'not enrolled')",
        trap_sql="SELECT loyalty_tier, COUNT(*) FROM customers"
                 " WHERE loyalty_tier IS NOT NULL GROUP BY loyalty_tier",
        note="Filtering the NULLs out answers a narrower question than the one asked. "
             "GROUP BY does keep NULL as its own group -- but it will be labelled NULL, "
             "not 'not enrolled', so you still have to say what you want.",
    ),
    dict(
        id=28, ledger="Q099", concept="GEN", tier="General",
        title="Below the reorder line",
        prompt="Inventory lines that have fallen to or below their reorder level. Lines "
               "with no reorder policy cannot be below one.\n\n"
               "Return: warehouse_id, product_id, quantity_on_hand, reorder_level",
        solution="SELECT warehouse_id, product_id, quantity_on_hand, reorder_level"
                 " FROM inventory"
                 " WHERE reorder_level IS NOT NULL AND quantity_on_hand <= reorder_level",
        trap_sql="SELECT warehouse_id, product_id, quantity_on_hand, reorder_level"
                 " FROM inventory"
                 " WHERE quantity_on_hand <= reorder_level OR reorder_level IS NULL",
        note="A line with no reorder policy is not a line below its reorder point -- "
             "there is nothing to be below. Sweeping the NULLs in turns 6 rows into 35 "
             "and would put 29 healthy lines on a restock report.",
    ),
    dict(
        id=29, ledger="Q100", concept="GEN", tier="General",
        title="Split orders",
        prompt="Orders that were shipped from more than one DISTINCT warehouse.\n\n"
               "Return: order_id, warehouses_used",
        solution="SELECT order_id, COUNT(DISTINCT warehouse_id) FROM shipments"
                 " GROUP BY order_id HAVING COUNT(DISTINCT warehouse_id) > 1",
        trap_sql="SELECT order_id, COUNT(DISTINCT warehouse_id) FROM shipments"
                 " GROUP BY order_id HAVING COUNT(*) > 1",
        note="Two shipments is not two warehouses -- an order can be split into two "
             "parcels from the same site. Count the thing the question names.",
    ),
    dict(
        id=30, ledger="Q101", concept="GEN", tier="General",
        title="Longest outstanding deliveries",
        prompt="The 5 shipments that have been in transit longest: no delivered_at, "
               "oldest shipped_at first. Break ties by the lower shipment_id.\n\n"
               "Return: shipment_id, order_id, carrier, shipped_at",
        solution="SELECT shipment_id, order_id, carrier, shipped_at FROM shipments"
                 " WHERE delivered_at IS NULL"
                 " ORDER BY shipped_at ASC, shipment_id ASC LIMIT 5",
        trap_sql="SELECT shipment_id, order_id, carrier, shipped_at FROM shipments"
                 " WHERE delivered_at IS NULL"
                 " ORDER BY shipped_at DESC, shipment_id ASC LIMIT 5",
        note="Longest in transit means the OLDEST dispatch date, so ascending. Sorting "
             "descending gives you the newest shipments, which are the least worrying.",
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
