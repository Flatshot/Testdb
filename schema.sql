-- Schema for testdb: a field-service repair depot.
-- Applied by db.init_db(); every statement is safe to re-run.
--
-- The shape is chosen to punish specific mistakes, not just to model a depot.
-- The central one is GRAIN: a work order has THREE independent children, so
-- almost every interesting question is a trap if you join more than one of
-- them in a single query block.
--
--   work_orders 1--0..n parts_used     parts cost, one row per part
--   work_orders 1--0..n labor_entries  labour cost, one row per visit
--   work_orders 1--0..n inspections    QA, one row per inspection
--
--        joining parts_used AND labor_entries multiplies BOTH:
--        4 parts x 3 visits = 12 rows, so SUM(parts) is 3x too big and
--        SUM(labour) is 4x too big. Each branch must be aggregated to one
--        row per work order BEFORE the two meet.
--
--   customers 1--n sites 1--n machines 1--n work_orders
--                                      a deep chain; counting customers after
--                                      joining down it needs DISTINCT
--   customers 1--0..n contracts        second child of customers, so joining
--                                      contracts and work_orders fans out too
--   technicians --> technicians        self-join; supervisor_id NULL at the top
--   depots *--* parts via part_stock   composite key, nullable policy columns
--   work_orders 1--0..1 invoices       optional child -> LEFT JOIN traps
--   nullable numeric columns           AVG skips NULLs; NULL eats arithmetic
--   INTEGER measures                   integer division truncates in SQLite
--
-- Deliberate gaps: some machines are never worked on, some work orders have no
-- parts, some have no labour, some have neither, some are never inspected,
-- some are still open, some are never invoiced. Anti-joins and NULL handling
-- need something real to find.

CREATE TABLE IF NOT EXISTS regions (
    region_id INTEGER PRIMARY KEY,
    name      TEXT NOT NULL UNIQUE,
    country   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id  INTEGER PRIMARY KEY,
    name         TEXT    NOT NULL,
    region_id    INTEGER NOT NULL REFERENCES regions(region_id),
    signed_on    TEXT    NOT NULL,
    -- 'bronze' | 'silver' | 'gold'; NULL where the account was never graded
    account_tier TEXT CHECK (account_tier IS NULL
                             OR account_tier IN ('bronze', 'silver', 'gold'))
);

-- A customer can have several sites. Rolling a per-site figure up to the
-- customer means aggregating twice, or being careful about DISTINCT.
CREATE TABLE IF NOT EXISTS sites (
    site_id     INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    name        TEXT    NOT NULL,
    city        TEXT    NOT NULL,
    region_id   INTEGER NOT NULL REFERENCES regions(region_id)
);

CREATE TABLE IF NOT EXISTS machines (
    machine_id     INTEGER PRIMARY KEY,
    site_id        INTEGER NOT NULL REFERENCES sites(site_id),
    model          TEXT    NOT NULL,
    serial         TEXT    NOT NULL UNIQUE,
    installed_on   TEXT    NOT NULL,
    -- NULL where the machine was never registered for warranty cover.
    -- Not the same as an expired warranty, which has a past date.
    warranty_until TEXT
);

CREATE TABLE IF NOT EXISTS depots (
    depot_id       INTEGER PRIMARY KEY,
    name           TEXT    NOT NULL,
    region_id      INTEGER NOT NULL REFERENCES regions(region_id),
    capacity_units INTEGER NOT NULL CHECK (capacity_units > 0),
    opened_on      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS technicians (
    technician_id INTEGER PRIMARY KEY,
    name          TEXT    NOT NULL,
    depot_id      INTEGER NOT NULL REFERENCES depots(depot_id),
    hired_on      TEXT    NOT NULL,
    -- NULL for the depot manager, who reports to nobody
    supervisor_id INTEGER REFERENCES technicians(technician_id),
    hourly_rate   REAL    NOT NULL CHECK (hourly_rate > 0),
    -- NULL where the technician has not sat the certification yet.
    -- An unknown level is not level 0.
    cert_level    INTEGER CHECK (cert_level IS NULL
                                 OR cert_level BETWEEN 1 AND 5)
);

-- Second child of customers, so joining contracts and work_orders in one
-- block fans out exactly the way parts and labour do.
CREATE TABLE IF NOT EXISTS contracts (
    contract_id    INTEGER PRIMARY KEY,
    customer_id    INTEGER NOT NULL REFERENCES customers(customer_id),
    start_date     TEXT    NOT NULL,
    -- NULL means open-ended, NOT expired
    end_date       TEXT,
    monthly_fee    REAL    NOT NULL CHECK (monthly_fee >= 0),
    -- NULL where no response time was ever agreed. An unknown SLA is not a
    -- slow one, so it must not be swept up by a > comparison.
    response_hours INTEGER CHECK (response_hours IS NULL OR response_hours > 0)
);

CREATE TABLE IF NOT EXISTS parts (
    part_id      INTEGER PRIMARY KEY,
    name         TEXT    NOT NULL,
    category     TEXT    NOT NULL,
    unit_cost    REAL    NOT NULL CHECK (unit_cost >= 0),
    -- nullable INTEGER measure: unweighed parts are NULL, not 0
    weight_grams INTEGER CHECK (weight_grams IS NULL OR weight_grams > 0)
);

CREATE TABLE IF NOT EXISTS work_orders (
    work_order_id INTEGER PRIMARY KEY,
    machine_id    INTEGER NOT NULL REFERENCES machines(machine_id),
    -- NULL while the job sits unassigned in the queue
    technician_id INTEGER REFERENCES technicians(technician_id),
    opened_at     TEXT    NOT NULL,
    -- NULL while the job is still open. Not the same as cancelled.
    closed_at     TEXT,
    priority      TEXT    NOT NULL CHECK (priority IN ('low', 'normal',
                                                       'high', 'critical')),
    status        TEXT    NOT NULL CHECK (status IN ('open', 'closed',
                                                     'cancelled'))
);

-- Child A of work_orders. unit_price is the price charged at the time, which
-- drifts from parts.unit_cost. discount is a RATE (0.05 = 5%), not a percent.
CREATE TABLE IF NOT EXISTS parts_used (
    work_order_id INTEGER NOT NULL REFERENCES work_orders(work_order_id),
    part_id       INTEGER NOT NULL REFERENCES parts(part_id),
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    unit_price    REAL    NOT NULL CHECK (unit_price >= 0),
    discount      REAL    NOT NULL DEFAULT 0 CHECK (discount >= 0
                                                    AND discount < 1),
    PRIMARY KEY (work_order_id, part_id)
);

-- Child B of work_orders, and the one that makes parts_used dangerous.
-- A job can take several visits, each logged separately.
CREATE TABLE IF NOT EXISTS labor_entries (
    entry_id      INTEGER PRIMARY KEY,
    work_order_id INTEGER NOT NULL REFERENCES work_orders(work_order_id),
    technician_id INTEGER NOT NULL REFERENCES technicians(technician_id),
    work_date     TEXT    NOT NULL,
    hours         REAL    NOT NULL CHECK (hours > 0),
    rate          REAL    NOT NULL CHECK (rate > 0)
);

-- Child C of work_orders. A third branch, so three-way fan-out is available.
CREATE TABLE IF NOT EXISTS inspections (
    inspection_id INTEGER PRIMARY KEY,
    work_order_id INTEGER NOT NULL REFERENCES work_orders(work_order_id),
    inspected_at  TEXT    NOT NULL,
    result        TEXT    NOT NULL CHECK (result IN ('pass', 'fail',
                                                     'conditional')),
    -- NULL where the inspector recorded a verdict but no numeric score
    score         INTEGER CHECK (score IS NULL OR score BETWEEN 0 AND 100)
);

-- Composite-key many-to-many. A part is stocked in several depots, so
-- SUM(quantity_on_hand) across a join is easy to double-count.
CREATE TABLE IF NOT EXISTS part_stock (
    depot_id         INTEGER NOT NULL REFERENCES depots(depot_id),
    part_id          INTEGER NOT NULL REFERENCES parts(part_id),
    quantity_on_hand INTEGER NOT NULL CHECK (quantity_on_hand >= 0),
    -- NULL where no reorder policy has been set for this line
    reorder_level    INTEGER CHECK (reorder_level IS NULL
                                    OR reorder_level >= 0),
    -- NULL where the line has never been physically counted
    last_counted_at  TEXT,
    PRIMARY KEY (depot_id, part_id)
);

-- Optional child of work_orders: not every job gets invoiced, and status is
-- stored UPPERCASE. Both facts matter.
CREATE TABLE IF NOT EXISTS invoices (
    invoice_id    INTEGER PRIMARY KEY,
    work_order_id INTEGER NOT NULL UNIQUE REFERENCES work_orders(work_order_id),
    issued_on     TEXT    NOT NULL,
    amount        REAL    NOT NULL CHECK (amount >= 0),
    status        TEXT    NOT NULL CHECK (status IN ('PAID', 'PENDING',
                                                     'OVERDUE', 'VOID')),
    -- NULL unless the invoice actually settled
    paid_on       TEXT
);

CREATE INDEX IF NOT EXISTS idx_sites_customer   ON sites(customer_id);
CREATE INDEX IF NOT EXISTS idx_machines_site    ON machines(site_id);
CREATE INDEX IF NOT EXISTS idx_tech_supervisor  ON technicians(supervisor_id);
CREATE INDEX IF NOT EXISTS idx_tech_depot       ON technicians(depot_id);
CREATE INDEX IF NOT EXISTS idx_contracts_cust   ON contracts(customer_id);
CREATE INDEX IF NOT EXISTS idx_wo_machine       ON work_orders(machine_id);
CREATE INDEX IF NOT EXISTS idx_wo_tech          ON work_orders(technician_id);
CREATE INDEX IF NOT EXISTS idx_wo_opened        ON work_orders(opened_at);
CREATE INDEX IF NOT EXISTS idx_parts_used_part  ON parts_used(part_id);
CREATE INDEX IF NOT EXISTS idx_labor_wo         ON labor_entries(work_order_id);
CREATE INDEX IF NOT EXISTS idx_labor_tech       ON labor_entries(technician_id);
CREATE INDEX IF NOT EXISTS idx_insp_wo          ON inspections(work_order_id);
CREATE INDEX IF NOT EXISTS idx_stock_part       ON part_stock(part_id);
CREATE INDEX IF NOT EXISTS idx_invoices_wo      ON invoices(work_order_id);
