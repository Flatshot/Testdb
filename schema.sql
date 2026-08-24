-- Schema for testdb: a small retail / e-commerce dataset for practicing SQL.
-- Applied by db.init_db(); every statement is safe to re-run.
--
-- The shape is chosen to punish specific mistakes, not just to model a shop:
--
--   employees --> employees (manager_id)   self-join; manager_id NULL for the CEO
--   orders *--* products via order_items   many-to-many; revenue is per LINE
--   orders 1--0..n payments                optional child -> LEFT JOIN traps
--   nullable numeric columns               AVG skips NULLs; NULL eats arithmetic
--   INTEGER measures                       integer division truncates in SQLite
--
-- Deliberate gaps: some customers never order, some products never sell, some
-- orders have no payment row. Anti-joins and outer joins need something to find.

CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS suppliers (
    supplier_id   INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    country       TEXT NOT NULL,
    contact_email TEXT
);

CREATE TABLE IF NOT EXISTS products (
    product_id     INTEGER PRIMARY KEY,
    name           TEXT    NOT NULL,
    category_id    INTEGER NOT NULL REFERENCES categories(category_id),
    supplier_id    INTEGER NOT NULL REFERENCES suppliers(supplier_id),
    unit_price     REAL    NOT NULL CHECK (unit_price >= 0),
    units_in_stock INTEGER NOT NULL DEFAULT 0 CHECK (units_in_stock >= 0),
    discontinued   INTEGER NOT NULL DEFAULT 0 CHECK (discontinued IN (0, 1)),
    -- nullable INTEGER measure: unweighed items are NULL, not 0
    weight_grams   INTEGER CHECK (weight_grams IS NULL OR weight_grams > 0)
);

CREATE TABLE IF NOT EXISTS employees (
    employee_id     INTEGER PRIMARY KEY,
    first_name      TEXT    NOT NULL,
    last_name       TEXT    NOT NULL,
    title           TEXT    NOT NULL,
    department      TEXT    NOT NULL,
    -- NULL for the CEO, who reports to nobody
    manager_id      INTEGER REFERENCES employees(employee_id),
    hire_date       TEXT    NOT NULL,
    salary          REAL    NOT NULL CHECK (salary > 0),
    -- NULL for staff on no commission scheme -- not the same as 0.0
    commission_rate REAL    CHECK (commission_rate IS NULL OR commission_rate >= 0)
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    first_name  TEXT NOT NULL,
    last_name   TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    city        TEXT NOT NULL,
    country     TEXT NOT NULL,
    signup_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id    INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    employee_id INTEGER NOT NULL REFERENCES employees(employee_id),
    order_date  TEXT    NOT NULL,
    -- NULL while an order is still pending, and for cancelled orders
    ship_date   TEXT,
    status      TEXT    NOT NULL CHECK (status IN ('shipped', 'pending', 'cancelled'))
);

-- Junction table resolving the many-to-many between orders and products.
-- unit_price is the price *at time of sale*, which drifts from
-- products.unit_price. discount is a RATE (0.05 = 5%), not a percentage.
CREATE TABLE IF NOT EXISTS order_items (
    order_id   INTEGER NOT NULL REFERENCES orders(order_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity   INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL    NOT NULL CHECK (unit_price >= 0),
    discount   REAL    NOT NULL DEFAULT 0 CHECK (discount >= 0 AND discount < 1),
    PRIMARY KEY (order_id, product_id)
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id     INTEGER PRIMARY KEY,
    product_id    INTEGER NOT NULL REFERENCES products(product_id),
    customer_id   INTEGER NOT NULL REFERENCES customers(customer_id),
    rating        INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    -- often NULL: plenty of people rate without writing anything
    comment       TEXT,
    review_date   TEXT NOT NULL,
    -- NULL means "nobody has voted yet", which is not the same as zero votes
    helpful_votes INTEGER CHECK (helpful_votes IS NULL OR helpful_votes >= 0)
);

-- Optional child of orders: not every order has a payment row, and status is
-- stored UPPERCASE. Both facts matter.
CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY,
    order_id   INTEGER NOT NULL REFERENCES orders(order_id),
    amount     REAL    NOT NULL CHECK (amount >= 0),
    status     TEXT    NOT NULL CHECK (status IN ('PAID', 'PENDING', 'FAILED', 'REFUNDED')),
    -- NULL unless the payment actually settled
    paid_at    TEXT,
    method     TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_products_category  ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_supplier  ON products(supplier_id);
CREATE INDEX IF NOT EXISTS idx_employees_manager  ON employees(manager_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer    ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_employee    ON orders(employee_id);
CREATE INDEX IF NOT EXISTS idx_orders_date        ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_order_items_prod   ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_product    ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_payments_order     ON payments(order_id);
