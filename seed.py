"""Populate testdb with practice data.

Deterministic: the RNG is seeded and no wall-clock dates are used, so running
this twice produces byte-identical data. Safe to re-run -- it clears the tables
first.

    python seed.py
"""

import random
from datetime import date, timedelta

import db

SEED = 7

# Orders span this window. Fixed, not derived from today, so the data set does
# not drift as time passes.
RANGE_START = date(2025, 1, 6)
RANGE_END = date(2026, 8, 14)

# Tables in dependency order; deleted in reverse so foreign keys stay satisfied.
TABLES = [
    "categories",
    "suppliers",
    "products",
    "employees",
    "customers",
    "orders",
    "order_items",
    "reviews",
    "payments",
]

CATEGORIES = [
    ("Electronics", "Consumer electronics and accessories"),
    ("Home & Kitchen", "Cookware, small appliances, and homeware"),
    ("Books", "Print and audio titles"),
    ("Sports & Outdoors", "Fitness, camping, and cycling gear"),
    ("Toys & Games", "Board games, puzzles, and kids' toys"),
    ("Office Supplies", "Stationery, desk gear, and organisation"),
    ("Health & Beauty", "Personal care and wellness"),
    ("Grocery", "Shelf-stable food and drink"),
]

SUPPLIERS = [
    ("Northwind Trading", "United Kingdom", "orders@northwindtrading.example"),
    ("Kestrel Imports", "Germany", "sales@kestrelimports.example"),
    ("Pacific Rim Goods", "Japan", "contact@pacificrimgoods.example"),
    ("Lakeshore Distributors", "United States", "hello@lakeshoredist.example"),
    ("Cedar & Co.", "Canada", "info@cedarandco.example"),
    ("Vallis Supply", "Italy", "vendite@vallissupply.example"),
]

# (name, category, unit_price, units_in_stock, discontinued)
PRODUCTS = [
    ("Aurora 27\" 4K Monitor", "Electronics", 349.99, 42, 0),
    ("Aurora 24\" QHD Monitor", "Electronics", 229.50, 61, 0),
    ("Mechanical Keyboard K87", "Electronics", 119.00, 88, 0),
    ("Wireless Mouse Glide 2", "Electronics", 34.95, 210, 0),
    ("Noise-Cancelling Headphones NC7", "Electronics", 279.00, 35, 0),
    ("USB-C Hub 8-in-1", "Electronics", 59.99, 140, 0),
    ("Portable SSD 1TB", "Electronics", 109.00, 76, 0),
    ("Webcam Clarity Pro", "Electronics", 89.50, 0, 1),
    ("Desk Lamp Halo", "Electronics", 44.00, 95, 0),
    ("Cast Iron Skillet 12\"", "Home & Kitchen", 42.00, 120, 0),
    ("Stainless Stock Pot 8Qt", "Home & Kitchen", 68.75, 54, 0),
    ("Chef's Knife 8\"", "Home & Kitchen", 85.00, 67, 0),
    ("Pour-Over Coffee Set", "Home & Kitchen", 39.99, 143, 0),
    ("Electric Kettle 1.7L", "Home & Kitchen", 54.50, 89, 0),
    ("Bamboo Cutting Board", "Home & Kitchen", 27.25, 176, 0),
    ("Ceramic Dinnerware Set", "Home & Kitchen", 112.00, 31, 0),
    ("The Pragmatic Programmer", "Books", 44.99, 58, 0),
    ("Designing Data-Intensive Applications", "Books", 52.00, 44, 0),
    ("SQL Performance Explained", "Books", 38.50, 27, 0),
    ("A Short History of Nearly Everything", "Books", 19.99, 133, 0),
    ("The Left Hand of Darkness", "Books", 15.75, 91, 0),
    ("Yoga Mat Pro 6mm", "Sports & Outdoors", 48.00, 102, 0),
    ("Adjustable Dumbbell Pair", "Sports & Outdoors", 249.00, 22, 0),
    ("Trail Backpack 40L", "Sports & Outdoors", 134.50, 47, 0),
    ("Two-Person Tent Ridge", "Sports & Outdoors", 218.00, 18, 0),
    ("Cycling Helmet Aero", "Sports & Outdoors", 96.00, 63, 0),
    ("Insulated Water Bottle 1L", "Sports & Outdoors", 29.95, 245, 0),
    ("Strategy Board Game: Meridian", "Toys & Games", 54.99, 73, 0),
    ("1000-Piece Puzzle: Harbour", "Toys & Games", 22.50, 118, 0),
    ("Wooden Building Blocks", "Toys & Games", 36.00, 84, 0),
    ("Remote Control Rover", "Toys & Games", 78.25, 39, 0),
    ("Notebook A5 Dotted", "Office Supplies", 12.99, 312, 0),
    ("Fountain Pen Meridian", "Office Supplies", 68.00, 41, 0),
    ("Desk Organiser Oak", "Office Supplies", 45.50, 76, 0),
    ("Whiteboard 90x60cm", "Office Supplies", 82.00, 24, 0),
    ("Printer Paper 500ct", "Office Supplies", 9.75, 480, 0),
    ("Vitamin D3 Supplement", "Health & Beauty", 16.50, 205, 0),
    ("Electric Toothbrush Sonic", "Health & Beauty", 94.00, 58, 0),
    ("Shea Butter Hand Cream", "Health & Beauty", 14.25, 167, 0),
    ("Sunscreen SPF50 200ml", "Health & Beauty", 21.00, 0, 1),
    ("Single-Origin Coffee 1kg", "Grocery", 28.50, 96, 0),
    ("Sencha Green Tea 200g", "Grocery", 18.75, 74, 0),
    ("Olive Oil Extra Virgin 1L", "Grocery", 24.00, 111, 0),
    ("Dark Chocolate 85% (6-pack)", "Grocery", 19.50, 148, 0),
]

# (first, last, title, department, manager_id, hire_date, salary)
EMPLOYEES = [
    ("Dana", "Whitfield", "Chief Executive Officer", "Executive", None, "2018-03-05", 195000.0),
    ("Marcus", "Lindqvist", "Sales Manager", "Sales", 1, "2021-06-01", 118000.0),
    ("Priya", "Raman", "Support Manager", "Support", 1, "2022-01-15", 112000.0),
    ("Tomas", "Berger", "Warehouse Manager", "Warehouse", 1, "2020-02-24", 98000.0),
    ("Aisha", "Kone", "Sales Representative", "Sales", 2, "2021-01-11", 72000.0),
    ("Liam", "O'Donnell", "Sales Representative", "Sales", 2, "2021-08-30", 69500.0),
    ("Sofia", "Marchetti", "Sales Representative", "Sales", 2, "2022-04-18", 67000.0),
    ("Noah", "Feldman", "Sales Representative", "Sales", 2, "2023-09-25", 61000.0),
    ("Yuki", "Tanaka", "Support Specialist", "Support", 3, "2021-05-10", 64000.0),
    ("Grace", "Mbeki", "Support Specialist", "Support", 3, "2022-11-14", 60500.0),
    ("Ravi", "Chandra", "Warehouse Associate", "Warehouse", 4, "2022-02-07", 52000.0),
    ("Elena", "Petrova", "Warehouse Associate", "Warehouse", 4, "2024-06-03", 49500.0),
]

# Employees who can be credited with an order: the reps plus their manager.
SALES_STAFF = [2, 5, 6, 7, 8]

# (first, last, city, country)
CUSTOMERS = [
    ("Helena", "Vargas", "Madrid", "Spain"),
    ("Oscar", "Lindgren", "Stockholm", "Sweden"),
    ("Amara", "Okafor", "Lagos", "Nigeria"),
    ("Peter", "Novak", "Prague", "Czechia"),
    ("Mei", "Chen", "Singapore", "Singapore"),
    ("Julian", "Brandt", "Hamburg", "Germany"),
    ("Rosa", "Iglesias", "Buenos Aires", "Argentina"),
    ("Callum", "Fraser", "Glasgow", "United Kingdom"),
    ("Ingrid", "Solberg", "Bergen", "Norway"),
    ("Diego", "Moreno", "Mexico City", "Mexico"),
    ("Fatima", "Al-Rashid", "Dubai", "United Arab Emirates"),
    ("Henry", "Whitmore", "Toronto", "Canada"),
    ("Sanne", "de Vries", "Utrecht", "Netherlands"),
    ("Kwame", "Asante", "Accra", "Ghana"),
    ("Beatrice", "Conti", "Bologna", "Italy"),
    ("Andrei", "Popescu", "Bucharest", "Romania"),
    ("Nora", "Haugen", "Oslo", "Norway"),
    ("Tariq", "Hassan", "Cairo", "Egypt"),
    ("Lucia", "Fernandez", "Valencia", "Spain"),
    ("Jasper", "Kwan", "Vancouver", "Canada"),
    ("Maya", "Sundaram", "Chennai", "India"),
    ("Felix", "Bergmann", "Vienna", "Austria"),
    ("Chloe", "Dubois", "Lyon", "France"),
    ("Ravi", "Menon", "Bangalore", "India"),
    ("Astrid", "Nilsen", "Copenhagen", "Denmark"),
    ("Marcus", "Reid", "Melbourne", "Australia"),
    ("Yara", "Haddad", "Beirut", "Lebanon"),
    ("Tobias", "Frank", "Zurich", "Switzerland"),
    ("Priscilla", "Adeyemi", "Abuja", "Nigeria"),
    ("Sean", "Gallagher", "Dublin", "Ireland"),
]

PAYMENT_METHODS = ["card", "paypal", "bank transfer", "gift card"]

COMMENTS = [
    "Exactly what I needed, arrived quickly.",
    "Good quality for the price.",
    "Works well but the manual is useless.",
    "Better than I expected. Would buy again.",
    "Does the job, nothing special.",
    "Arrived damaged, support sorted it out fast.",
    "Feels cheap, would not repurchase.",
    "Excellent build quality.",
    "Fine, though shipping took a while.",
    "Not as described -- smaller than the photos suggest.",
    "Perfect gift, very happy with it.",
    "Third one I've bought. Reliable.",
]


def _email(first, last, taken):
    base = f"{first}.{last}".lower()
    for ch in " '-":
        base = base.replace(ch, "")
    candidate = f"{base}@example.com"
    n = 2
    while candidate in taken:
        candidate = f"{base}{n}@example.com"
        n += 1
    taken.add(candidate)
    return candidate


def _random_date(rng, start, end):
    return start + timedelta(days=rng.randint(0, (end - start).days))


def seed():
    rng = random.Random(SEED)

    # Drop and recreate rather than DELETE: the schema gains columns over time,
    # and clearing rows would leave the old table shape in place.
    conn = db.connect()
    try:
        with conn:
            conn.execute("DROP TABLE IF EXISTS note")
            for table in reversed(TABLES):
                conn.execute(f"DROP TABLE IF EXISTS {table}")
    finally:
        conn.close()
    db.init_db()

    conn = db.connect()
    try:
        with conn:

            # --- categories -------------------------------------------------
            conn.executemany(
                "INSERT INTO categories (category_id, name, description) VALUES (?, ?, ?)",
                [(i, name, desc) for i, (name, desc) in enumerate(CATEGORIES, 1)],
            )
            cat_id = {name: i for i, (name, _) in enumerate(CATEGORIES, 1)}

            # --- suppliers --------------------------------------------------
            conn.executemany(
                "INSERT INTO suppliers (supplier_id, name, country, contact_email) VALUES (?, ?, ?, ?)",
                [(i, *row) for i, row in enumerate(SUPPLIERS, 1)],
            )

            # --- products ---------------------------------------------------
            product_rows = []
            for i, (name, cat, price, stock, disc) in enumerate(PRODUCTS, 1):
                supplier = rng.randint(1, len(SUPPLIERS))
                # ~1 in 6 items has never been weighed: NULL, not zero
                weight = None if rng.random() < 0.16 else rng.randrange(50, 8000, 5)
                product_rows.append((i, name, cat_id[cat], supplier, price, stock, disc, weight))
            conn.executemany(
                "INSERT INTO products (product_id, name, category_id, supplier_id,"
                " unit_price, units_in_stock, discontinued, weight_grams)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                product_rows,
            )
            product_price = {row[0]: row[4] for row in product_rows}

            # --- employees --------------------------------------------------
            employee_rows = []
            for i, (first, last, title, dept, mgr, hired, salary) in enumerate(EMPLOYEES, 1):
                # NULL means "not on a commission scheme" -- distinct from 0.0,
                # which would mean "on a scheme paying nothing"
                rate = round(rng.uniform(0.02, 0.08), 3) if dept == "Sales" else None
                employee_rows.append((i, first, last, title, dept, mgr, hired, salary, rate))
            conn.executemany(
                "INSERT INTO employees (employee_id, first_name, last_name, title,"
                " department, manager_id, hire_date, salary, commission_rate)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                employee_rows,
            )

            # --- customers --------------------------------------------------
            taken, customer_rows = set(), []
            for i, (first, last, city, country) in enumerate(CUSTOMERS, 1):
                signup = _random_date(rng, date(2024, 2, 1), date(2026, 5, 1))
                customer_rows.append(
                    (i, first, last, _email(first, last, taken), city, country, signup.isoformat())
                )
            conn.executemany(
                "INSERT INTO customers (customer_id, first_name, last_name, email,"
                " city, country, signup_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                customer_rows,
            )

            # --- orders and order_items -------------------------------------
            # The last 4 customers never order, so LEFT JOIN / NOT EXISTS
            # exercises have something to find.
            buyers = list(range(1, len(CUSTOMERS) - 3))
            # A few customers are heavy repeat buyers; weighting makes the
            # per-customer aggregates more interesting than a flat spread.
            weights = [4 if c % 7 == 0 else (3 if c % 3 == 0 else 1) for c in buyers]

            # The last 3 products are never ordered, for the same reason.
            sellable = list(range(1, len(PRODUCTS) - 2))

            pending_cutoff = RANGE_END - timedelta(days=18)
            order_rows, item_rows = [], []
            order_id = 0

            for _ in range(165):
                order_id += 1
                customer = rng.choices(buyers, weights=weights, k=1)[0]
                employee = rng.choice(SALES_STAFF)
                ordered = _random_date(rng, RANGE_START, RANGE_END)

                if ordered >= pending_cutoff:
                    status, shipped = "pending", None
                elif rng.random() < 0.09:
                    status, shipped = "cancelled", None
                else:
                    status = "shipped"
                    shipped = (ordered + timedelta(days=rng.randint(1, 9))).isoformat()

                order_rows.append(
                    (order_id, customer, employee, ordered.isoformat(), shipped, status)
                )

                for product in rng.sample(sellable, rng.randint(1, 5)):
                    # Historical price wobbles around the current list price.
                    price = round(product_price[product] * rng.uniform(0.9, 1.08), 2)
                    discount = rng.choice([0.0, 0.0, 0.0, 0.05, 0.10, 0.15, 0.20])
                    item_rows.append(
                        (order_id, product, rng.randint(1, 6), price, discount)
                    )

            conn.executemany(
                "INSERT INTO orders (order_id, customer_id, employee_id, order_date,"
                " ship_date, status) VALUES (?, ?, ?, ?, ?, ?)",
                order_rows,
            )
            conn.executemany(
                "INSERT INTO order_items (order_id, product_id, quantity, unit_price,"
                " discount) VALUES (?, ?, ?, ?, ?)",
                item_rows,
            )

            # --- reviews ----------------------------------------------------
            # Only for things people actually received, and only once per
            # customer/product pair.
            shipped_orders = {
                row[0]: (row[1], row[3]) for row in order_rows if row[5] == "shipped"
            }
            review_rows, seen = [], set()
            review_id = 0
            for oid, product, *_ in item_rows:
                if oid not in shipped_orders or rng.random() > 0.38:
                    continue
                customer, ordered = shipped_orders[oid]
                if (customer, product) in seen:
                    continue
                seen.add((customer, product))
                review_id += 1
                # Ratings skew positive, as they do in the wild.
                rating = rng.choices([1, 2, 3, 4, 5], weights=[4, 6, 14, 34, 42], k=1)[0]
                comment = rng.choice(COMMENTS) if rng.random() < 0.62 else None
                when = date.fromisoformat(ordered) + timedelta(days=rng.randint(5, 45))
                # NULL = nobody has voted yet, which is not the same as zero votes
                votes = None if rng.random() < 0.3 else rng.randint(0, 40)
                review_rows.append(
                    (review_id, product, customer, rating, comment, when.isoformat(), votes)
                )

            conn.executemany(
                "INSERT INTO reviews (review_id, product_id, customer_id, rating,"
                " comment, review_date, helpful_votes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                review_rows,
            )

            # --- payments ---------------------------------------------------
            # An optional child of orders: roughly one order in ten has no
            # payment row at all, so LEFT JOIN and COUNT(*) have a trap to set.
            totals = {}
            for oid, product, qty, price, disc in item_rows:
                totals[oid] = totals.get(oid, 0.0) + qty * price * (1 - disc)

            payment_rows = []
            payment_id = 0
            for oid, _cust, _emp, ordered, _shipped, status in order_rows:
                if rng.random() < 0.10:
                    continue  # no payment row at all
                payment_id += 1
                if status == "shipped":
                    pay_status = "REFUNDED" if rng.random() < 0.08 else "PAID"
                elif status == "pending":
                    pay_status = "PENDING"
                else:
                    pay_status = "FAILED"
                # paid_at is set only where money actually moved
                if pay_status in ("PAID", "REFUNDED"):
                    settled = (date.fromisoformat(ordered)
                               + timedelta(days=rng.randint(0, 3))).isoformat()
                else:
                    settled = None
                payment_rows.append((
                    payment_id, oid, round(totals.get(oid, 0.0), 2),
                    pay_status, settled, rng.choice(PAYMENT_METHODS),
                ))

            conn.executemany(
                "INSERT INTO payments (payment_id, order_id, amount, status,"
                " paid_at, method) VALUES (?, ?, ?, ?, ?, ?)",
                payment_rows,
            )
    finally:
        conn.close()

    return {t: n for t, n in _counts().items()}


def _counts():
    conn = db.connect()
    try:
        return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABLES}
    finally:
        conn.close()


if __name__ == "__main__":
    for table, n in seed().items():
        print(f"{table:>12}: {n:>5}")
    print(f"\nseeded {db.DB_PATH}")
