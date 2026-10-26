"""Populate testdb with practice data for a city bike-hire scheme.

Deterministic: the RNG is seeded and no wall-clock dates are used, so running
this twice produces byte-identical data. Safe to re-run -- it drops every table
first, so a schema change is picked up.

    python seed.py

The gaps below are deliberate. Questions about anti-joins, NULL handling,
open intervals and COUNT need something real to find:

  * members who have never ridden, and members with no district recorded
  * bikes never ridden, and bikes retired
  * a station closed part-way through the data
  * rides still out (ended_at NULL), and rides by casual riders (member_id NULL)
  * maintenance jobs still open
  * subscription payments that members have missed
"""

import random
from datetime import date, datetime, timedelta

import db

SEED = 1206

# Rides are spread across this window. The data ends at SNAPSHOT: a ride that
# would have ended after it is left out instead, and a job not yet fixed by
# then is left open.
RANGE_START = date(2025, 1, 1)
RANGE_END = date(2026, 6, 30)
SNAPSHOT = datetime(2026, 6, 30, 23, 59)

FREE_MINUTES = 30            # a member's ride inside this costs nothing
MEMBER_RATE = 100            # cents per started 15 minutes beyond the free half hour
CASUAL_BASE = 200            # cents to unlock, casual rider
CASUAL_RATE = 50             # cents per started 10 minutes, casual rider
PAYG_BASE = 150              # cents to unlock, pay-as-you-go member
PAYG_RATE = 50               # cents per started 10 minutes, pay-as-you-go member
MONTHLY_FEE = 1200           # cents
ANNUAL_FEE = 9900            # cents

TABLES = ["stations", "bikes", "members", "rides", "maintenance", "payments"]

STATIONS = [("Market Square", "centre", 40, "2019-04-01"), ("Cathedral", "centre", 24, "2019-04-01"),
            ("Station Approach", "centre", 36, "2019-04-01"), ("University", "north", 32, "2019-06-15"),
            ("Botanic Gardens", "north", 20, "2020-03-01"), ("Hilltop", "north", 16, "2021-05-20"),
            ("Harbour", "east", 28, "2019-09-10"), ("East Quay", "east", 18, "2022-07-01"),
            ("Stadium", "south", 30, "2020-08-14"), ("Old Mill", "south", 14, "2021-11-02"),
            ("Parkway", "west", 22, "2020-01-20"), ("Riverside", "west", 26, "2019-04-01")]
CLOSED_STATION = 10          # Old Mill closes part-way through
CLOSED_ON = date(2026, 3, 1)

FIRST = ["Aisha", "Bartholomew", "Cerys", "Dmitri", "Eleanor", "Farouk",
         "Grace", "Hamid", "Imogen", "Jonah", "Kwame", "Leila", "Marcus",
         "Nadia", "Oluwaseun", "Priya", "Quentin", "Rosa", "Samir", "Tamsin",
         "Umar", "Verity", "Wilfred", "Xiu", "Yusuf", "Zara"]
LAST = ["Achebe", "Baxter", "Chowdhury", "Dalgleish", "Ekwueme", "Fairweather",
        "Grzybowski", "Hollingsworth", "Iqbal", "Jankowski", "Khatri",
        "Lindqvist", "Mbeki", "Nakamura", "Okonjo", "Papadopoulos", "Quraishi",
        "Rasmussen", "Sowerby", "Tremblay", "Uddin", "Villanueva", "Whitcombe",
        "Yilmaz", "Zielinski"]
DISTRICTS = ["Old Town", "Docklands", "Northfield", "Southgate", "Westbrook",
             "Eastmoor", "Hillside", "Riverbank", "Millfield", "Greenway"]
MODELS = ["classic"] * 6 + ["electric"] * 3 + ["cargo"]
PLANS = ["annual"] * 4 + ["monthly"] * 4 + ["pay-as-you-go"] * 2
KINDS = ["puncture"] * 4 + ["brakes"] * 2 + ["battery", "chain", "chain", "other"]
COST = {"puncture": (800, 1500), "brakes": (1500, 4000), "battery": (6000, 15000),
        "chain": (1200, 3000), "other": (500, 8000)}

# Typical ride lengths by model, in minutes, and typical speed in metres a
# minute -- cargo bikes are hired for errands, electrics go further.
TYPICAL = {"classic": (18, 180), "electric": (24, 260), "cargo": (35, 150)}


def _d(d):
    return d.isoformat()


def _t(t):
    return t.strftime("%Y-%m-%d %H:%M")


def _ceil_div(a, b):
    return -(-a // b)


def fare(minutes, plan):
    """What a ride costs, in cents, for a rider on `plan` (None = casual)."""
    if plan is None:
        return CASUAL_BASE + CASUAL_RATE * _ceil_div(minutes, 10)
    if plan == "pay-as-you-go":
        return PAYG_BASE + PAYG_RATE * _ceil_div(minutes, 10)
    extra = max(minutes - FREE_MINUTES, 0)
    return MEMBER_RATE * _ceil_div(extra, 15) if extra else 0


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

        # ---- stations: twelve, one of which closes ------------------------
        with conn:
            conn.executemany(
                "INSERT INTO stations (station_id, name, zone, docks, opened_on, closed_on)"
                " VALUES (?,?,?,?,?,?)",
                [(i + 1, n, z, d, o, _d(CLOSED_ON) if i + 1 == CLOSED_STATION else None)
                 for i, (n, z, d, o) in enumerate(STATIONS)])
        open_stations = [s for s in range(1, len(STATIONS) + 1)]

        # ---- bikes: 320, some retired --------------------------------------
        bikes = []
        for _ in range(320):
            model = rng.choice(MODELS)
            acquired = date(2022, 1, 1) + timedelta(days=rng.randint(0, 1200))
            retired = None
            if rng.random() < 0.06:
                retired = _d(RANGE_START + timedelta(days=rng.randint(30, 500)))
            bikes.append((model, _d(acquired), retired))
        with conn:
            conn.executemany(
                "INSERT INTO bikes (model, acquired_on, retired_on) VALUES (?,?,?)", bikes)

        # ---- members: 900, some who never ride -----------------------------
        members = []
        for _ in range(900):
            born = date(1945, 1, 1) + timedelta(days=rng.randint(0, 22000))
            joined = date(2023, 1, 1) + timedelta(days=rng.randint(0, 1270))
            joined = min(joined, RANGE_END)
            district = None if rng.random() < 0.1 else rng.choice(DISTRICTS)
            members.append((f"{rng.choice(FIRST)} {rng.choice(LAST)}", _d(born), _d(joined),
                            rng.choice(PLANS), rng.randint(1, len(STATIONS)), district))
        with conn:
            conn.executemany(
                "INSERT INTO members (name, born_on, joined_on, plan, home_station_id, district)"
                " VALUES (?,?,?,?,?,?)", members)
        never = set(rng.sample(range(1, 901), 100))
        riders = [m for m in range(1, 901) if m not in never]
        commuters = rng.sample(riders, 40)          # a heavy tail of regulars

        # ---- rides: one bike at a time, with gaps between -----------------
        rides = []
        for bid, (model, acquired, retired) in enumerate(bikes, start=1):
            if rng.random() < 0.03:
                continue                                    # never ridden
            end = datetime.fromisoformat(retired) if retired else SNAPSHOT
            start_day = max(RANGE_START, date.fromisoformat(acquired))
            when = datetime.combine(start_day, datetime.min.time()) + timedelta(
                minutes=rng.randint(0, 14 * 24 * 60))
            typical_min, speed = TYPICAL[model]
            while when < end:
                if rng.random() < 0.3:
                    member, plan = None, None                # casual rider
                else:
                    member = rng.choice(commuters) if rng.random() < 0.3 else rng.choice(riders)
                    plan = members[member - 1][3]
                from_s = rng.choice(open_stations)
                if from_s == CLOSED_STATION and when.date() >= CLOSED_ON:
                    from_s = 1
                to_s = from_s if rng.random() < 0.08 else rng.choice(open_stations)
                minutes = max(2, int(rng.expovariate(1 / typical_min)) + 2)
                minutes = min(minutes, 240)
                ended = when + timedelta(minutes=minutes)
                if to_s == CLOSED_STATION and ended.date() >= CLOSED_ON:
                    to_s = 3
                if ended > end:
                    rides.append((bid, member, from_s, None, _t(when), None, None, 0))
                    break
                dist = int(minutes * speed * rng.uniform(0.6, 1.3))
                rides.append((bid, member, from_s, to_s, _t(when), _t(ended), dist,
                              fare(minutes, plan)))
                # the bike waits at the dock -- a few days on average, so a
                # bike sees about a hundred rides over the eighteen months
                gap = int(rng.expovariate(1 / 6000)) + 30
                when = ended + timedelta(minutes=min(gap, 20 * 24 * 60))
                # nobody unlocks a bike in the small hours: push to the morning
                if when.hour < 6:
                    when = when.replace(hour=rng.randint(6, 9), minute=rng.randint(0, 59))
                elif when.hour >= 23:
                    when = (when + timedelta(days=1)).replace(hour=rng.randint(6, 9),
                                                              minute=rng.randint(0, 59))
            # a few bikes are out on the road as the data ends
            if not retired and rng.random() < 0.12:
                out_from = SNAPSHOT - timedelta(minutes=rng.randint(5, 600))
                if not rides or rides[-1][0] != bid or rides[-1][5] is None or rides[-1][5] < _t(out_from):
                    rides.append((bid, rng.choice(riders) if rng.random() < 0.7 else None,
                                  rng.choice([s for s in open_stations if s != CLOSED_STATION]),
                                  None, _t(out_from), None, None, 0))
        with conn:
            conn.executemany(
                "INSERT INTO rides (bike_id, member_id, start_station_id, end_station_id,"
                " started_at, ended_at, distance_m, fare_cents) VALUES (?,?,?,?,?,?,?,?)", rides)

        # ---- maintenance: 1,100 jobs, some still open -----------------------
        jobs = []
        for _ in range(1100):
            bid = rng.randint(1, 320)
            model = bikes[bid - 1][0]
            kind = rng.choice(KINDS)
            if kind == "battery" and model != "electric":
                kind = "chain"
            reported = datetime.combine(RANGE_START, datetime.min.time()) + timedelta(
                minutes=rng.randint(0, 546 * 24 * 60))
            fixed = reported + timedelta(hours=rng.randint(2, 240))
            fixed_s = _t(fixed) if fixed <= SNAPSHOT and rng.random() < 0.92 else None
            lo, hi = COST[kind]
            jobs.append((bid, rng.randint(1, len(STATIONS)), _t(reported), fixed_s, kind,
                         rng.randint(lo, hi) // 10 * 10))
        with conn:
            conn.executemany(
                "INSERT INTO maintenance (bike_id, station_id, reported_at, fixed_at, kind,"
                " cost_cents) VALUES (?,?,?,?,?,?)", jobs)

        # ---- payments: fares per ride, subscriptions per member -------------
        payments = []
        for rid, (bid, member, from_s, to_s, started, ended, dist, cents) in enumerate(rides, start=1):
            if cents == 0 or ended is None:
                continue
            payments.append((None, rid, cents, ended, rng.choice(["card", "card", "app"])))
        for mid, (name, born, joined, plan, home, district) in enumerate(members, start=1):
            if plan == "pay-as-you-go":
                continue
            due = date.fromisoformat(joined)
            step = timedelta(days=365) if plan == "annual" else timedelta(days=30)
            amount = ANNUAL_FEE if plan == "annual" else MONTHLY_FEE
            while due <= RANGE_END:
                if due >= RANGE_START and rng.random() >= 0.06:      # a few missed payments
                    paid = datetime.combine(due, datetime.min.time()) + timedelta(
                        minutes=rng.randint(8 * 60, 22 * 60))
                    payments.append((mid, None, amount, _t(paid), rng.choice(["card", "app", "app"])))
                due = due + step
        payments.sort(key=lambda p: p[3])
        with conn:
            conn.executemany(
                "INSERT INTO payments (member_id, ride_id, amount_cents, paid_at, method)"
                " VALUES (?,?,?,?,?)", payments)
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
