-- Schema for testdb: a small group of hotels.
-- Applied by db.init_db(); every statement is safe to re-run.
--
-- The eighth schema in this repo, after a college, a field-service workshop,
-- a railway, a district hospital, a public library, a city bike-hire scheme
-- and a parcel courier. A hotel keeps the shapes the courier taught -- MONEY
-- in cents, a parent with a trail of child rows, a NULL that is a category,
-- one site that closes part-way through -- and adds the DATE RANGE that must
-- not overlap: a room is sold by the night, and two bookings for one room
-- collide when their ranges do.
--
--   bookings              check_in .. check_out, both dates. check_out is the
--                         morning the guest leaves, so the range is half-open:
--                         nights = check_out - check_in, and a guest is in the
--                         house on night d when check_in <= d < check_out.
--                         status says what became of it: 'booked' (not yet
--                         arrived when the data ends), 'stayed' (arrived,
--                         including guests still in the house), 'cancelled'
--                         or 'no_show'
--   rooms                 belong to a hotel; rack_cents is the LIST price per
--                         night, bookings.rate_cents the price actually agreed
--   charges               extras put on the room during a stay: breakfast, the
--                         bar, the restaurant, the spa, parking, laundry
--   payments              money against a booking: a deposit when it was made,
--                         the balance at check-out, and a NEGATIVE amount for
--                         a refund
--   reviews               at most one per booking, a score from 1 to 5 and
--                         perhaps a headline
--   guests                a person; tier is NULL for the many who are not in
--                         the loyalty scheme, and email NULL for those who
--                         never gave one
--
-- Carried over on purpose, so familiar questions have a home:
--
--   hotels.closed_on      NULL while trading; one hotel closes during the data
--                         and another opens during it
--   guests.tier           the NULL that is a category, not a gap
--   bookings.cancelled_at NULL unless the booking was cancelled, tied to
--                         status by a CHECK
--   kind, channel, status categories with a fixed list of values
--
-- Dates are TEXT 'YYYY-MM-DD' and timestamps TEXT 'YYYY-MM-DD HH:MM'. Both
-- compare correctly as text. The data ends at 2026-06-30 23:59.

CREATE TABLE IF NOT EXISTS hotels (
    hotel_id   INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL UNIQUE,
    town       TEXT    NOT NULL,
    stars      INTEGER NOT NULL CHECK (stars BETWEEN 2 AND 5),
    opened_on  TEXT    NOT NULL,
    -- NULL while the hotel is trading
    closed_on  TEXT
);

CREATE TABLE IF NOT EXISTS rooms (
    room_id    INTEGER PRIMARY KEY,
    hotel_id   INTEGER NOT NULL REFERENCES hotels(hotel_id),
    -- as written on the door: '204' is floor 2, room 4
    room_no    TEXT    NOT NULL,
    floor      INTEGER NOT NULL CHECK (floor >= 1),
    kind       TEXT    NOT NULL CHECK (kind IN ('single', 'twin', 'double', 'family', 'suite')),
    sleeps     INTEGER NOT NULL CHECK (sleeps BETWEEN 1 AND 6),
    -- the list price for one night, in whole cents
    rack_cents INTEGER NOT NULL CHECK (rack_cents > 0),
    UNIQUE (hotel_id, room_no)
);

CREATE TABLE IF NOT EXISTS guests (
    guest_id   INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL,
    -- two-letter country code
    country    TEXT    NOT NULL,
    -- NULL for a guest who never gave one
    email      TEXT,
    -- NULL for a guest who is not in the loyalty scheme
    tier       TEXT    CHECK (tier IN ('silver', 'gold')),
    -- the day the group first had this person on its books
    joined_on  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS bookings (
    booking_id   INTEGER PRIMARY KEY,
    guest_id     INTEGER NOT NULL REFERENCES guests(guest_id),
    room_id      INTEGER NOT NULL REFERENCES rooms(room_id),
    booked_at    TEXT    NOT NULL,
    -- the first night
    check_in     TEXT    NOT NULL,
    -- the morning of departure: nights = check_out - check_in
    check_out    TEXT    NOT NULL,
    adults       INTEGER NOT NULL CHECK (adults >= 1),
    children     INTEGER NOT NULL DEFAULT 0 CHECK (children >= 0),
    channel      TEXT    NOT NULL CHECK (channel IN ('web', 'phone', 'agent', 'walk_in')),
    -- the price agreed for one night, in whole cents
    rate_cents   INTEGER NOT NULL CHECK (rate_cents > 0),
    status       TEXT    NOT NULL CHECK (status IN ('booked', 'stayed', 'cancelled', 'no_show')),
    -- NULL unless the booking was cancelled
    cancelled_at TEXT,
    CHECK (check_out > check_in),
    CHECK ((status = 'cancelled') = (cancelled_at IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS charges (
    charge_id    INTEGER PRIMARY KEY,
    booking_id   INTEGER NOT NULL REFERENCES bookings(booking_id),
    kind         TEXT    NOT NULL CHECK (kind IN ('breakfast', 'bar', 'restaurant', 'spa', 'parking', 'laundry')),
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    charged_on   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id   INTEGER PRIMARY KEY,
    booking_id   INTEGER NOT NULL REFERENCES bookings(booking_id),
    paid_at      TEXT    NOT NULL,
    -- whole cents; a negative amount is a refund
    amount_cents INTEGER NOT NULL CHECK (amount_cents <> 0),
    method       TEXT    NOT NULL CHECK (method IN ('card', 'cash', 'transfer'))
);

CREATE TABLE IF NOT EXISTS reviews (
    review_id   INTEGER PRIMARY KEY,
    booking_id  INTEGER NOT NULL UNIQUE REFERENCES bookings(booking_id),
    score       INTEGER NOT NULL CHECK (score BETWEEN 1 AND 5),
    posted_on   TEXT    NOT NULL,
    -- NULL for a score left with no words
    headline    TEXT
);

CREATE INDEX IF NOT EXISTS idx_rooms_hotel      ON rooms(hotel_id);
CREATE INDEX IF NOT EXISTS idx_bookings_guest   ON bookings(guest_id);
CREATE INDEX IF NOT EXISTS idx_bookings_room    ON bookings(room_id, check_in);
CREATE INDEX IF NOT EXISTS idx_bookings_checkin ON bookings(check_in);
CREATE INDEX IF NOT EXISTS idx_charges_booking  ON charges(booking_id);
CREATE INDEX IF NOT EXISTS idx_payments_booking ON payments(booking_id);
CREATE INDEX IF NOT EXISTS idx_hotels_name      ON hotels(name COLLATE NOCASE);
