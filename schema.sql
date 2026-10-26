-- Schema for testdb: a city bike-hire scheme.
-- Applied by db.init_db(); every statement is safe to re-run.
--
-- The sixth schema in this repo, after a college, a field-service workshop,
-- a railway, a district hospital and a public library. A bike-hire scheme
-- keeps the shapes the library taught -- INTERVALS with open ends, MONEY,
-- two foreign keys to one table -- and adds a GRAPH: every ride is an edge
-- from one station to another.
--
--   rides                 started_at .. ended_at, each at a station: a ride
--                         still out has NULL ended_at and NULL end_station_id;
--                         the fare depends on who rode and for how long
--   maintenance           reported_at .. fixed_at, a bike off the road while
--                         the job is open
--   payments              money in whole cents: a per-ride fare paid by a
--                         casual rider or a pay-as-you-go member, or a
--                         subscription paid by a member -- one of ride_id and
--                         member_id is NULL on every row
--   bikes                 a model with a natural order ('classic' < 'electric'
--                         < 'cargo'), acquired on a date, perhaps retired
--
-- Carried over on purpose, so familiar questions have a home:
--
--   rides.start_station_id, rides.end_station_id, members.home_station_id
--                         three different foreign keys to stations
--   rides.member_id       NULL for a casual rider: the NULL that is a
--                         category, not a gap
--   dates and times are text: 'YYYY-MM-DD' for dates, 'YYYY-MM-DD HH:MM' for
--                         timestamps. julianday() turns either into a number.
--
-- Deliberate gaps: members who have never ridden, bikes never ridden, bikes
-- retired, a station closed, rides still out, maintenance still open, rides
-- by casual riders with no member, members with no recorded district.

CREATE TABLE IF NOT EXISTS stations (
    station_id INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL UNIQUE,
    zone       TEXT    NOT NULL CHECK (zone IN ('centre', 'north', 'south', 'east', 'west')),
    docks      INTEGER NOT NULL CHECK (docks > 0),
    opened_on  TEXT    NOT NULL,
    -- NULL while the station is in service
    closed_on  TEXT
);

CREATE TABLE IF NOT EXISTS bikes (
    bike_id     INTEGER PRIMARY KEY,
    model       TEXT    NOT NULL CHECK (model IN ('classic', 'electric', 'cargo')),
    acquired_on TEXT    NOT NULL,
    -- NULL while the bike is in the fleet
    retired_on  TEXT
);

CREATE TABLE IF NOT EXISTS members (
    member_id       INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL,
    born_on         TEXT    NOT NULL,
    joined_on       TEXT    NOT NULL,
    plan            TEXT    NOT NULL CHECK (plan IN ('annual', 'monthly', 'pay-as-you-go')),
    home_station_id INTEGER NOT NULL REFERENCES stations(station_id),
    -- NULL where never recorded
    district        TEXT
);

CREATE TABLE IF NOT EXISTS rides (
    ride_id          INTEGER PRIMARY KEY,
    bike_id          INTEGER NOT NULL REFERENCES bikes(bike_id),
    -- NULL for a casual rider who paid at the dock
    member_id        INTEGER REFERENCES members(member_id),
    start_station_id INTEGER NOT NULL REFERENCES stations(station_id),
    -- NULL while the ride is still out
    end_station_id   INTEGER REFERENCES stations(station_id),
    started_at       TEXT    NOT NULL,
    ended_at         TEXT,
    -- metres ridden, NULL while the ride is still out
    distance_m       INTEGER,
    -- whole cents; 0 for a member's ride inside their free half hour
    fare_cents       INTEGER NOT NULL DEFAULT 0 CHECK (fare_cents >= 0),
    CHECK ((ended_at IS NULL) = (end_station_id IS NULL))
);

CREATE TABLE IF NOT EXISTS maintenance (
    job_id      INTEGER PRIMARY KEY,
    bike_id     INTEGER NOT NULL REFERENCES bikes(bike_id),
    station_id  INTEGER NOT NULL REFERENCES stations(station_id),
    reported_at TEXT    NOT NULL,
    -- NULL while the job is open
    fixed_at    TEXT,
    kind        TEXT    NOT NULL CHECK (kind IN ('puncture', 'brakes', 'battery', 'chain', 'other')),
    cost_cents  INTEGER NOT NULL CHECK (cost_cents >= 0)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id   INTEGER PRIMARY KEY,
    -- a subscription payment names the member; a fare names the ride
    member_id    INTEGER REFERENCES members(member_id),
    ride_id      INTEGER REFERENCES rides(ride_id),
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    paid_at      TEXT    NOT NULL,
    method       TEXT    NOT NULL CHECK (method IN ('card', 'app')),
    CHECK (member_id IS NOT NULL OR ride_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_members_station   ON members(home_station_id);
CREATE INDEX IF NOT EXISTS idx_rides_bike        ON rides(bike_id, started_at);
CREATE INDEX IF NOT EXISTS idx_rides_member      ON rides(member_id);
CREATE INDEX IF NOT EXISTS idx_rides_start       ON rides(start_station_id, started_at);
CREATE INDEX IF NOT EXISTS idx_rides_end         ON rides(end_station_id);
CREATE INDEX IF NOT EXISTS idx_maint_bike        ON maintenance(bike_id);
CREATE INDEX IF NOT EXISTS idx_payments_member   ON payments(member_id);
CREATE INDEX IF NOT EXISTS idx_payments_ride     ON payments(ride_id);
CREATE INDEX IF NOT EXISTS idx_stations_name     ON stations(name COLLATE NOCASE);
