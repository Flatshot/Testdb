-- Schema for testdb: a regional parcel courier.
-- Applied by db.init_db(); every statement is safe to re-run.
--
-- The seventh schema in this repo, after a college, a field-service workshop,
-- a railway, a district hospital, a public library and a city bike-hire
-- scheme. A courier keeps the shapes the bike scheme taught -- INTERVALS
-- with open ends, MONEY in cents, two foreign keys to one table, a NULL
-- that is a category -- and adds an ORDERED SEQUENCE inside a parent: every
-- parcel leaves a trail of scans, and the trail is the story.
--
--   parcels               collected_at .. delivered_at between two depots: a
--                         parcel still moving has NULL delivered_at and NULL
--                         courier_id; the postage depends on service and weight
--   scans                 the parcel's trail, one row per event, in time order:
--                         collected, departed, arrived, out_for_delivery,
--                         failed, delivered -- a failed attempt is followed by
--                         another out_for_delivery the next day
--   invoices              a business customer's month of postage, issued on the
--                         first of the next month, perhaps not yet paid
--   customers             a business or a person with a home depot; a parcel
--                         handed in at a counter by a stranger has NO customer
--
-- Carried over on purpose, so familiar questions have a home:
--
--   parcels.origin_depot_id, parcels.dest_depot_id, customers.depot_id
--                         three foreign keys to depots
--   parcels.customer_id   NULL for a walk-in sender: the NULL that is a
--                         category, not a gap
--   service               a category with a natural order: 'economy' <
--                         'standard' < 'express', not alphabetical
--   dates and times are text: 'YYYY-MM-DD' for dates, 'YYYY-MM-DD HH:MM' for
--                         timestamps. julianday() turns either into a number.
--
-- Deliberate gaps: customers who have never sent a parcel, couriers who have
-- left, a depot closed part-way through, parcels still in transit, parcels
-- lost after a failed attempt, walk-in parcels with no customer, customers
-- with no postcode area, invoices unpaid.

CREATE TABLE IF NOT EXISTS depots (
    depot_id  INTEGER PRIMARY KEY,
    name      TEXT    NOT NULL UNIQUE,
    region    TEXT    NOT NULL CHECK (region IN ('central', 'north', 'south', 'east', 'west')),
    bays      INTEGER NOT NULL CHECK (bays > 0),
    opened_on TEXT    NOT NULL,
    -- NULL while the depot is in service
    closed_on TEXT
);

CREATE TABLE IF NOT EXISTS couriers (
    courier_id INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL,
    depot_id   INTEGER NOT NULL REFERENCES depots(depot_id),
    vehicle    TEXT    NOT NULL CHECK (vehicle IN ('bike', 'van', 'lorry')),
    hired_on   TEXT    NOT NULL,
    -- NULL while the courier still works here
    left_on    TEXT
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id   INTEGER PRIMARY KEY,
    name          TEXT    NOT NULL,
    kind          TEXT    NOT NULL CHECK (kind IN ('business', 'personal')),
    depot_id      INTEGER NOT NULL REFERENCES depots(depot_id),
    joined_on     TEXT    NOT NULL,
    -- NULL where never recorded
    postcode_area TEXT
);

CREATE TABLE IF NOT EXISTS parcels (
    parcel_id       INTEGER PRIMARY KEY,
    -- NULL for a walk-in sender who paid at the counter
    customer_id     INTEGER REFERENCES customers(customer_id),
    origin_depot_id INTEGER NOT NULL REFERENCES depots(depot_id),
    dest_depot_id   INTEGER NOT NULL REFERENCES depots(depot_id),
    service         TEXT    NOT NULL CHECK (service IN ('economy', 'standard', 'express')),
    weight_g        INTEGER NOT NULL CHECK (weight_g > 0),
    collected_at    TEXT    NOT NULL,
    -- NULL while the parcel is still moving (or lost)
    delivered_at    TEXT,
    -- the courier who delivered it; NULL until then
    courier_id      INTEGER REFERENCES couriers(courier_id),
    -- whole cents, decided by service and weight when collected
    postage_cents   INTEGER NOT NULL CHECK (postage_cents > 0),
    CHECK ((delivered_at IS NULL) = (courier_id IS NULL))
);

CREATE TABLE IF NOT EXISTS scans (
    scan_id    INTEGER PRIMARY KEY,
    parcel_id  INTEGER NOT NULL REFERENCES parcels(parcel_id),
    depot_id   INTEGER NOT NULL REFERENCES depots(depot_id),
    -- the courier holding the parcel; NULL for a scan inside a depot
    courier_id INTEGER REFERENCES couriers(courier_id),
    scanned_at TEXT    NOT NULL,
    status     TEXT    NOT NULL CHECK (status IN ('collected', 'departed', 'arrived',
                                                  'out_for_delivery', 'failed', 'delivered'))
);

CREATE TABLE IF NOT EXISTS invoices (
    invoice_id   INTEGER PRIMARY KEY,
    customer_id  INTEGER NOT NULL REFERENCES customers(customer_id),
    -- the month billed, 'YYYY-MM'
    period       TEXT    NOT NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    issued_on    TEXT    NOT NULL,
    -- NULL while unpaid
    paid_on      TEXT,
    method       TEXT    CHECK (method IN ('card', 'transfer')),
    UNIQUE (customer_id, period),
    CHECK ((paid_on IS NULL) = (method IS NULL))
);

CREATE INDEX IF NOT EXISTS idx_customers_depot   ON customers(depot_id);
CREATE INDEX IF NOT EXISTS idx_parcels_customer  ON parcels(customer_id);
CREATE INDEX IF NOT EXISTS idx_parcels_origin    ON parcels(origin_depot_id, collected_at);
CREATE INDEX IF NOT EXISTS idx_parcels_dest      ON parcels(dest_depot_id);
CREATE INDEX IF NOT EXISTS idx_parcels_courier   ON parcels(courier_id);
CREATE INDEX IF NOT EXISTS idx_scans_parcel      ON scans(parcel_id, scanned_at);
CREATE INDEX IF NOT EXISTS idx_scans_depot       ON scans(depot_id, scanned_at);
CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_id);
CREATE INDEX IF NOT EXISTS idx_depots_name       ON depots(name COLLATE NOCASE);
