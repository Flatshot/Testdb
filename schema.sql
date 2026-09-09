-- Schema for testdb: a regional railway.
-- Applied by db.init_db(); every statement is safe to re-run.
--
-- Chosen to be shaped DIFFERENTLY from the five sets that came before, not
-- merely to be a different subject. The central fact is an ORDERED SEQUENCE
-- inside a parent, which none of the earlier schemas had:
--
--   services 1--n stops   (service_id, stop_seq) is the primary key, so every
--                         stop knows where it sits in its own journey. That
--                         makes "the next station", "the first and last stop",
--                         "the whole route as one string" and "minutes since
--                         the previous stop" natural questions rather than
--                         contrived ones -- and they need LAG/LEAD, frame
--                         clauses, FIRST_VALUE/LAST_VALUE and GROUP_CONCAT.
--
-- Other shapes deliberately new to this repo:
--
--   station_footfall      a WIDE table: one row per station-year with four
--                         quarter columns. Turning it long again is an
--                         unpivot, which SQL has no operator for -- it is
--                         UNION ALL or nothing.
--   tickets.price_pence   money as INTEGER, so averages and shares hit
--                         integer division rather than floating point
--   tickets.class         a category whose natural order is NOT alphabetical
--                         ('first' < 'standard' < 'advance' by price), so
--                         sorting it needs CASE inside ORDER BY
--   services.run_date     a real calendar of daily runs, for date modifiers
--                         ('start of month', 'weekday 0', '+1 day')
--   service_units         many-to-many WITH a payload (position in the train)
--   staff.reports_to      a hierarchy, kept small -- recursion has had eight
--                         questions in three sets and is deliberately light
--                         here
--
-- Deliberate gaps: services that were cancelled and so have no stops, stations
-- no service calls at, staff who manage nobody, tickets with no recorded
-- destination, incidents with no delay, units never assigned to a service.

CREATE TABLE IF NOT EXISTS operators (
    operator_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,
    since_year  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS lines (
    line_id INTEGER PRIMARY KEY,
    name    TEXT NOT NULL UNIQUE,
    colour  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stations (
    station_id INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL UNIQUE,
    town       TEXT    NOT NULL,
    opened_on  TEXT    NOT NULL,
    -- 1 or 0; NULL where nobody has surveyed the station yet
    step_free  INTEGER CHECK (step_free IS NULL OR step_free IN (0, 1))
);

-- One row per station per year, with the four quarters side by side. Wide on
-- purpose: making it long again is the unpivot question.
CREATE TABLE IF NOT EXISTS station_footfall (
    station_id INTEGER NOT NULL REFERENCES stations(station_id),
    year       INTEGER NOT NULL,
    q1         INTEGER NOT NULL CHECK (q1 >= 0),
    q2         INTEGER NOT NULL CHECK (q2 >= 0),
    q3         INTEGER NOT NULL CHECK (q3 >= 0),
    q4         INTEGER NOT NULL CHECK (q4 >= 0),
    PRIMARY KEY (station_id, year)
);

CREATE TABLE IF NOT EXISTS staff (
    staff_id      INTEGER PRIMARY KEY,
    name          TEXT    NOT NULL,
    base_station  INTEGER NOT NULL REFERENCES stations(station_id),
    role          TEXT    NOT NULL CHECK (role IN ('driver', 'guard',
                                                   'dispatcher', 'manager')),
    hired_on      TEXT    NOT NULL,
    -- NULL for the one person at the top
    reports_to    INTEGER REFERENCES staff(staff_id),
    -- annual salary in whole pounds
    salary        INTEGER NOT NULL CHECK (salary > 0)
);

CREATE TABLE IF NOT EXISTS rolling_stock (
    unit_id    INTEGER PRIMARY KEY,
    model      TEXT    NOT NULL,
    seats      INTEGER NOT NULL CHECK (seats > 0),
    built_year INTEGER NOT NULL,
    -- NULL where the unit has never been refurbished
    refurbished_year INTEGER
);

CREATE TABLE IF NOT EXISTS services (
    service_id  INTEGER PRIMARY KEY,
    line_id     INTEGER NOT NULL REFERENCES lines(line_id),
    operator_id INTEGER NOT NULL REFERENCES operators(operator_id),
    run_date    TEXT    NOT NULL,
    -- scheduled departure from the first stop, 'HH:MM'
    depart_time TEXT    NOT NULL,
    cancelled   INTEGER NOT NULL DEFAULT 0 CHECK (cancelled IN (0, 1))
);

-- The ordered sequence. stop_seq counts from 1 within each service.
CREATE TABLE IF NOT EXISTS stops (
    service_id   INTEGER NOT NULL REFERENCES services(service_id),
    stop_seq     INTEGER NOT NULL CHECK (stop_seq > 0),
    station_id   INTEGER NOT NULL REFERENCES stations(station_id),
    sched_arrive TEXT    NOT NULL,
    -- NULL where the stop was skipped or nothing was recorded
    actual_arrive TEXT,
    PRIMARY KEY (service_id, stop_seq)
);

CREATE TABLE IF NOT EXISTS service_units (
    service_id INTEGER NOT NULL REFERENCES services(service_id),
    unit_id    INTEGER NOT NULL REFERENCES rolling_stock(unit_id),
    -- 1 is the front of the train
    position   INTEGER NOT NULL CHECK (position > 0),
    PRIMARY KEY (service_id, unit_id)
);

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id    INTEGER PRIMARY KEY,
    service_id   INTEGER NOT NULL REFERENCES services(service_id),
    from_station INTEGER NOT NULL REFERENCES stations(station_id),
    -- NULL for open returns with no destination recorded
    to_station   INTEGER REFERENCES stations(station_id),
    class        TEXT    NOT NULL CHECK (class IN ('first', 'standard',
                                                   'advance')),
    -- whole pence, so arithmetic on it is integer arithmetic
    price_pence  INTEGER NOT NULL CHECK (price_pence >= 0),
    sold_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS incidents (
    incident_id   INTEGER PRIMARY KEY,
    service_id    INTEGER NOT NULL REFERENCES services(service_id),
    reported_at   TEXT    NOT NULL,
    kind          TEXT    NOT NULL CHECK (kind IN ('signal', 'weather',
                                                   'fault', 'trespass',
                                                   'staffing')),
    -- NULL where the delay was never quantified
    delay_minutes INTEGER CHECK (delay_minutes IS NULL OR delay_minutes >= 0)
);

CREATE INDEX IF NOT EXISTS idx_stops_station   ON stops(station_id);
CREATE INDEX IF NOT EXISTS idx_services_date   ON services(run_date);
CREATE INDEX IF NOT EXISTS idx_services_line   ON services(line_id, run_date);
CREATE INDEX IF NOT EXISTS idx_tickets_service ON tickets(service_id);
CREATE INDEX IF NOT EXISTS idx_tickets_class   ON tickets(class, price_pence);
CREATE INDEX IF NOT EXISTS idx_tickets_sold    ON tickets(sold_at);
CREATE INDEX IF NOT EXISTS idx_incidents_svc   ON incidents(service_id);
CREATE INDEX IF NOT EXISTS idx_staff_reports   ON staff(reports_to);
CREATE INDEX IF NOT EXISTS idx_staff_name      ON staff(name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_units_unit      ON service_units(unit_id);
