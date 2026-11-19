"""Populate testdb with practice data for a small group of hotels.

Deterministic: the RNG is seeded and no wall-clock dates are used, so running
this twice produces byte-identical data. Safe to re-run -- it drops every table
first, so a schema change is picked up.

    python seed.py

The gaps below are deliberate. Questions about anti-joins, NULL handling,
date ranges, overlaps and COUNT need something real to find:

  * guests who have never booked, guests with no email, and guests who are
    not in the loyalty scheme (tier NULL)
  * a hotel that closes part-way through the data and one that opens during it
  * a room that is out of service and has never been booked
  * bookings that were cancelled, some of whose nights were then sold to
    someone else, so two bookings for one room can overlap -- but never two
    live ones
  * guests who booked and did not turn up
  * bookings for dates after the data ends, and guests still in the house
    on the last day
  * stays with no extras, stays whose balance was never paid, deposits
    refunded (a negative payment) and deposits kept
  * stays that were reviewed and many that were not, and reviews with a score
    and no headline
"""

import random
from datetime import date, datetime, timedelta

import db

SEED = 1356

# Stays are generated across this window and a little beyond it, because
# people book ahead. The data ends at SNAPSHOT: a booking not yet made by
# then does not exist, a stay not yet finished has no balance payment, and a
# guest who arrives after it is still 'booked'.
RANGE_START = date(2025, 1, 1)
RANGE_END = date(2026, 6, 30)
SNAPSHOT = datetime(2026, 6, 30, 23, 59)
HORIZON = RANGE_END + timedelta(days=240)

TABLES = ["hotels", "rooms", "guests", "bookings", "charges", "payments", "reviews"]

# name, town, stars, opened_on, rooms per floor on each floor, how busy it is
HOTELS = [
    ("Castle View",     "York",      4, "2012-04-01", [10, 10, 10], 0.30),
    ("The Old Mill",    "York",      3, "2015-06-15", [9, 9],       0.24),
    ("Harbour Lights",  "Whitby",    3, "2010-03-20", [8, 8, 8],    0.27),
    ("Abbey Steps",     "Whitby",    2, "2018-05-01", [6, 6],       0.17),
    ("Spa Gardens",     "Harrogate", 5, "2009-09-10", [12, 12, 12], 0.26),
    ("Station House",   "Harrogate", 3, "2019-02-11", [10, 10],     0.22),
    ("Lakeside Lodge",  "Keswick",   4, "2014-07-04", [11, 11],     0.29),
    ("Fellfoot Inn",    "Keswick",   2, "2025-09-01", [7, 7],       0.20),
]
CLOSED_HOTEL = 4                   # Abbey Steps closes part-way through
CLOSED_ON = date(2026, 3, 1)
OUT_OF_SERVICE = (5, "312")        # a suite at Spa Gardens, never let

RACK = {"single": 6500, "twin": 8000, "double": 8500, "family": 11000, "suite": 16000}
STAR_FACTOR = {2: 0.70, 3: 0.85, 4: 1.10, 5: 1.50}
SLEEPS = {"single": [1], "twin": [2], "double": [2], "family": [4, 4, 5], "suite": [2, 2, 3, 4]}
KIND_MIX = ["double"] * 9 + ["twin"] * 4 + ["single"] * 3 + ["family"] * 3 + ["suite"] * 1

BREAKFAST = {2: 900, 3: 1200, 4: 1500, 5: 2200}          # cents per adult
PARKING = [1200, 900, 700, 500, 1800, 1000, 800, 400]    # cents per night, by hotel
SPA_PRICES = [4500, 6000, 7500, 9500, 12000]

CHANNELS = ["web"] * 50 + ["phone"] * 22 + ["agent"] * 18 + ["walk_in"] * 10
CHANNEL_FACTOR = {"web": 0.95, "phone": 1.00, "agent": 0.88, "walk_in": 1.00}
SEASON = {1: 0.85, 2: 0.85, 3: 0.95, 4: 1.00, 5: 1.00, 6: 1.05,
          7: 1.20, 8: 1.20, 9: 1.00, 10: 0.95, 11: 0.90, 12: 1.10}
BUSY = {1: 0.70, 2: 0.75, 3: 0.90, 4: 1.00, 5: 1.05, 6: 1.10,
        7: 1.30, 8: 1.30, 9: 1.05, 10: 0.95, 11: 0.80, 12: 1.00}
NIGHTS = [1] * 7 + [2] * 9 + [3] * 6 + [4] * 3 + [5] * 2 + [7] * 2 + [10, 14]

FIRST = ["Agnes", "Benedict", "Callum", "Deepa", "Edmund", "Fatima", "Gwen",
         "Hugo", "Ingrid", "Jamal", "Kirsty", "Lorenzo", "Mei", "Niall",
         "Ottilie", "Pavel", "Rhiannon", "Sanjay", "Tabitha", "Ulrich",
         "Valentina", "Winston", "Yasmin", "Zeno"]
LAST = ["Ainsworth", "Bianchi", "Castellanos", "Devlin", "Eriksen", "Fofanah",
        "Gallagher", "Hargreaves", "Ivanova", "Jorgensen", "Kowalczyk",
        "Lambert", "Mwangi", "Nightingale", "O'Rourke", "Pemberton", "Qureshi",
        "Rosenthal", "Shrestha", "Thackeray", "Underhill", "Vasquez",
        "Wetherby", "Yamamoto", "Zubair"]
COUNTRIES = ["GB"] * 68 + ["IE"] * 7 + ["DE"] * 6 + ["FR"] * 5 + ["NL"] * 4 + ["US"] * 5 + ["ES"] * 3 + ["IT"] * 2
MAIL = ["example.com", "example.org", "example.net", "mail.example"]
HEADLINES = {
    1: ["Never again", "Dirty room, rude staff", "Not as advertised", "Avoid"],
    2: ["Disappointing", "Tired and noisy", "Expected better", "Cold room"],
    3: ["Fine for one night", "Average", "Good location, dated rooms", "Does the job"],
    4: ["Very comfortable", "Friendly staff", "Good value", "Would stay again", "Lovely breakfast"],
    5: ["Perfect weekend", "Could not fault it", "Outstanding", "A real treat", "Best stay this year"],
}
SCORES = {5: [1, 2, 5, 22, 70], 4: [2, 4, 12, 40, 42], 3: [4, 8, 22, 40, 26], 2: [8, 14, 30, 32, 16]}

N_GUESTS = 1600
NEVER_BOOKED = 95                  # the last so many guests have no booking
REGULARS = 260                     # the first so many guests come back often


def _d(d):
    return d.isoformat()


def _t(t):
    return t.strftime("%Y-%m-%d %H:%M")


def _round(x, to):
    return max(to, int(round(x / to)) * to)


def seed():
    rng = random.Random(SEED)
    conn = db.connect()
    try:
        with conn:
            conn.execute("PRAGMA foreign_keys=OFF")
            for t in [r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                    " AND name NOT LIKE 'sqlite_%'")]:
                conn.execute(f'DROP TABLE IF EXISTS "{t}"')
        conn.executescript(db.SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.execute("PRAGMA foreign_keys=ON")

        # ---- hotels: eight, one closes and one opens -----------------------
        with conn:
            conn.executemany(
                "INSERT INTO hotels (hotel_id, name, town, stars, opened_on, closed_on)"
                " VALUES (?,?,?,?,?,?)",
                [(i + 1, n, town, stars, opened, _d(CLOSED_ON) if i + 1 == CLOSED_HOTEL else None)
                 for i, (n, town, stars, opened, _, _) in enumerate(HOTELS)])

        # ---- rooms: a list price by kind, stars and floor ------------------
        rooms = []                 # (hotel_id, room_no, floor, kind, sleeps, rack)
        for h, (_, _, stars, _, floors, _) in enumerate(HOTELS, 1):
            for floor, count in enumerate(floors, 1):
                for n in range(1, count + 1):
                    kind = rng.choice(KIND_MIX)
                    if stars == 2 and kind == "suite":
                        kind = "double"
                    if (h, f"{floor}{n:02d}") == OUT_OF_SERVICE:
                        kind = "suite"
                    rack = _round(RACK[kind] * STAR_FACTOR[stars] + 250 * (floor - 1)
                                  + rng.choice([0, 0, 250, 500]), 50)
                    rooms.append((h, f"{floor}{n:02d}", floor, kind,
                                  rng.choice(SLEEPS[kind]), rack))
        with conn:
            conn.executemany(
                "INSERT INTO rooms (hotel_id, room_no, floor, kind, sleeps, rack_cents)"
                " VALUES (?,?,?,?,?,?)", rooms)

        # ---- guests: joined_on is filled in once their bookings are known ---
        guests = []                # [name, country, email, tier]
        for _ in range(N_GUESTS):
            first, last = rng.choice(FIRST), rng.choice(LAST)
            email = None
            if rng.random() > 0.18:
                local = f"{first}.{last}".lower().replace("'", "")
                email = f"{local}{rng.randint(1, 99)}@{rng.choice(MAIL)}"
            r = rng.random()
            tier = "gold" if r < 0.06 else "silver" if r < 0.22 else None
            guests.append([f"{first} {last}", rng.choice(COUNTRIES), email, tier])
        bookable = N_GUESTS - NEVER_BOOKED

        def pick_guest():
            if rng.random() < 0.35:
                return rng.randint(1, REGULARS)
            return rng.randint(1, bookable)

        # ---- bookings: each room's calendar, walked night by night ---------
        raw = []                   # dicts, given ids once sorted by booked_at

        def make(room_id, room, hotel, check_in, check_out, earliest=None):
            """One booking for the slot, or None if nobody has made it yet."""
            h, _, _, kind, sleeps, rack = room
            stars = HOTELS[h - 1][2]
            future = check_in > RANGE_END
            channel = rng.choice(CHANNELS)
            if future and channel == "walk_in":
                channel = "web"
            if channel == "walk_in":
                lead = 0
            elif channel == "web":
                lead = int(rng.triangular(0, 150, 8))
            elif channel == "phone":
                lead = int(rng.triangular(0, 60, 4))
            else:
                lead = int(rng.triangular(7, 240, 45))
            booked = datetime.combine(check_in - timedelta(days=lead), datetime.min.time()) \
                + timedelta(hours=rng.randint(7, 21), minutes=rng.randint(0, 59))
            if channel == "walk_in":
                booked = booked.replace(hour=rng.randint(13, 21))
            if earliest is not None and booked <= earliest:
                booked = earliest + timedelta(hours=rng.randint(1, 40), minutes=rng.randint(0, 59))
                if booked.date() > check_in:
                    return None
            if booked > SNAPSHOT:
                return None
            guest = pick_guest()
            if kind == "single":
                adults, children = 1, 0
            elif kind in ("twin", "double"):
                adults, children = (1 if rng.random() < 0.27 else 2), 0
            elif kind == "family":
                adults, children = 2, rng.randint(1, sleeps - 2)
            else:
                adults = 2
                children = rng.randint(0, sleeps - 2) if rng.random() < 0.3 else 0
            tier = guests[guest - 1][3]
            rate = _round(rack * CHANNEL_FACTOR[channel] * SEASON[check_in.month]
                          * {"gold": 0.90, "silver": 0.95, None: 1.0}[tier], 50)
            return dict(guest=guest, room_id=room_id, hotel=h, stars=stars, booked=booked,
                        check_in=check_in, check_out=check_out, adults=adults,
                        children=children, channel=channel, rate=rate,
                        status=None, cancelled=None)

        for room_id, room in enumerate(rooms, 1):
            h = room[0]
            if (h, room[1]) == OUT_OF_SERVICE:
                continue
            name, _, stars, opened, _, busy = HOTELS[h - 1]
            day = max(RANGE_START, date.fromisoformat(opened))
            last_night = HORIZON
            if h == CLOSED_HOTEL:
                last_night = CLOSED_ON
            while day < last_night:
                p = busy * BUSY[day.month] * (1.15 if day.weekday() in (4, 5) else 1.0)
                if rng.random() > p:
                    day += timedelta(days=1)
                    continue
                out = min(day + timedelta(days=rng.choice(NIGHTS)), last_night)
                b = make(room_id, room, h, day, out)
                if b is None:
                    day += timedelta(days=1)
                    continue
                # some bookings are cancelled, and some of those nights re-let
                if rng.random() < 0.11:
                    latest = min(datetime.combine(day, datetime.min.time()) + timedelta(hours=12), SNAPSHOT)
                    span = int((latest - b["booked"]).total_seconds() // 60)
                    if span > 90:
                        b["status"] = "cancelled"
                        b["cancelled"] = b["booked"] + timedelta(minutes=rng.randint(60, span))
                        raw.append(b)
                        if rng.random() < 0.6:
                            # the new guest takes some or all of the freed nights
                            start = day
                            if rng.random() < 0.5:
                                start += timedelta(days=rng.randint(0, (out - day).days - 1))
                            end = min(start + timedelta(days=rng.choice(NIGHTS)), out)
                            again = make(room_id, room, h, start, end, earliest=b["cancelled"])
                            if again is not None:
                                b = again
                            else:
                                day = out
                                continue
                        else:
                            day = out
                            continue
                if b["check_in"] > RANGE_END:
                    b["status"] = "booked"
                elif b["channel"] != "walk_in" and rng.random() < 0.03:
                    b["status"] = "no_show"
                else:
                    b["status"] = "stayed"
                raw.append(b)
                day = out

        raw.sort(key=lambda b: (b["booked"], b["room_id"], b["check_in"]))
        for i, b in enumerate(raw, 1):
            b["id"] = i

        # a guest joins the day they first book, or was known some time before
        first_seen = {}
        for b in raw:
            first_seen.setdefault(b["guest"], b["booked"].date())
        for g, row in enumerate(guests, 1):
            if g in first_seen:
                joined = first_seen[g]
                if rng.random() < 0.2:
                    joined -= timedelta(days=rng.randint(30, 1800))
            else:
                joined = date(2021, 1, 1) + timedelta(days=rng.randint(0, 2000))
            row.append(_d(joined))
        with conn:
            conn.executemany(
                "INSERT INTO guests (name, country, email, tier, joined_on) VALUES (?,?,?,?,?)",
                guests)
            conn.executemany(
                "INSERT INTO bookings (booking_id, guest_id, room_id, booked_at, check_in, check_out,"
                " adults, children, channel, rate_cents, status, cancelled_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                [(b["id"], b["guest"], b["room_id"], _t(b["booked"]), _d(b["check_in"]),
                  _d(b["check_out"]), b["adults"], b["children"], b["channel"], b["rate"],
                  b["status"], _t(b["cancelled"]) if b["cancelled"] else None) for b in raw])

        # ---- charges, payments and reviews ---------------------------------
        charges, payments, reviews = [], [], []
        for b in raw:
            h, stars = b["hotel"], b["stars"]
            nights = (b["check_out"] - b["check_in"]).days
            room_total = nights * b["rate"]

            # a deposit when the booking was made
            deposit, method = 0, None
            if b["channel"] == "web":
                deposit, method = b["rate"], "card"
                when = b["booked"] + timedelta(minutes=rng.randint(2, 9))
            elif b["channel"] == "agent" and rng.random() < 0.6:
                deposit, method = _round(room_total * 0.2, 100), "transfer"
                when = b["booked"] + timedelta(days=rng.randint(1, 5), minutes=rng.randint(0, 300))
            elif b["channel"] == "phone" and rng.random() < 0.3:
                deposit, method = b["rate"], "card"
                when = b["booked"] + timedelta(minutes=rng.randint(3, 25))
            if deposit and (when > SNAPSHOT or when.date() > b["check_in"]):
                deposit = 0
            if deposit:
                payments.append((b["id"], when, deposit, method))
                # cancelled a week or more ahead: the deposit goes back
                if b["status"] == "cancelled" and (b["check_in"] - b["cancelled"].date()).days >= 7:
                    back = b["cancelled"] + timedelta(minutes=rng.randint(5, 600))
                    if back <= SNAPSHOT:
                        payments.append((b["id"], back, -deposit, method))

            if b["status"] != "stayed":
                continue

            extras = 0
            takes_breakfast = rng.random() < 0.55
            has_car = rng.random() < 0.30
            for n in range(nights):
                night = b["check_in"] + timedelta(days=n)
                if night > RANGE_END:
                    break
                todays = []
                if has_car:
                    todays.append(("parking", PARKING[h - 1], night))
                if rng.random() < 0.22:
                    todays.append(("bar", _round(rng.randint(450, 4200), 10), night))
                if rng.random() < 0.15:
                    todays.append(("restaurant", _round(rng.randint(1800, 9500), 10), night))
                if stars >= 4 and rng.random() < 0.07:
                    todays.append(("spa", rng.choice(SPA_PRICES), night))
                if rng.random() < 0.03:
                    todays.append(("laundry", _round(rng.randint(800, 2600), 10), night))
                if takes_breakfast and night + timedelta(days=1) <= RANGE_END:
                    todays.append(("breakfast", BREAKFAST[stars] * b["adults"], night + timedelta(days=1)))
                for kind, cents, on in todays:
                    charges.append((b["id"], kind, cents, on))
                    extras += cents

            if b["check_out"] > RANGE_END:
                continue                                    # still in the house

            # the balance, at the desk on the way out
            balance = room_total + extras - deposit
            unpaid = rng.random() < (0.15 if b["channel"] == "agent" else 0.045)
            if balance > 0 and not unpaid:
                at = datetime.combine(b["check_out"], datetime.min.time()) \
                    + timedelta(hours=rng.randint(7, 11), minutes=rng.randint(0, 59))
                how = rng.choice(["card"] * 15 + ["cash"] * 3 + ["transfer"] * 2)
                if rng.random() < 0.05 and balance > 4000:
                    part = _round(balance * rng.uniform(0.2, 0.6), 100)
                    payments.append((b["id"], at, part, "cash"))
                    payments.append((b["id"], at + timedelta(minutes=1), balance - part, "card"))
                else:
                    payments.append((b["id"], at, balance, how))

            if rng.random() < 0.27:
                posted = b["check_out"] + timedelta(days=rng.randint(1, 21))
                if posted <= RANGE_END:
                    score = rng.choices([1, 2, 3, 4, 5], weights=SCORES[stars])[0]
                    headline = None if rng.random() < 0.35 else rng.choice(HEADLINES[score])
                    reviews.append((b["id"], score, posted, headline))

        charges.sort(key=lambda c: (c[3], c[0]))
        payments.sort(key=lambda p: (p[1], p[0]))
        reviews.sort(key=lambda r: (r[2], r[0]))
        with conn:
            conn.executemany(
                "INSERT INTO charges (booking_id, kind, amount_cents, charged_on) VALUES (?,?,?,?)",
                [(b, k, c, _d(on)) for b, k, c, on in charges])
            conn.executemany(
                "INSERT INTO payments (booking_id, paid_at, amount_cents, method) VALUES (?,?,?,?)",
                [(b, _t(at), c, m) for b, at, c, m in payments])
            conn.executemany(
                "INSERT INTO reviews (booking_id, score, posted_on, headline) VALUES (?,?,?,?)",
                [(b, s, _d(on), h) for b, s, on, h in reviews])
        # the sandbox copies this file into memory for every writable question,
        # so give back the space a re-seed leaves behind
        conn.execute("VACUUM")
    finally:
        conn.close()


def _counts():
    conn = db.connect()
    try:
        return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in TABLES}
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
    for t, n in _counts().items():
        print(f"  {t:>12}: {n:>7}")
    print(f"\nseeded {db.DB_PATH}")
