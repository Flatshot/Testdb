"""Populate testdb with practice data for a regional parcel courier.

Deterministic: the RNG is seeded and no wall-clock dates are used, so running
this twice produces byte-identical data. Safe to re-run -- it drops every table
first, so a schema change is picked up.

    python seed.py

The gaps below are deliberate. Questions about anti-joins, NULL handling,
open intervals, sequences and COUNT need something real to find:

  * customers who have never sent a parcel, and customers with no postcode area
  * couriers who have left
  * a depot closed part-way through the data
  * parcels still in transit (delivered_at NULL), and parcels lost after a
    failed delivery attempt
  * walk-in parcels with no customer (customer_id NULL)
  * failed delivery attempts, each followed by another attempt
  * invoices not yet paid
"""

import random
from datetime import date, datetime, timedelta

import db

SEED = 1241

# Parcels are collected across this window. The data ends at SNAPSHOT: a
# parcel that would have been delivered after it is still in transit, and an
# invoice for June is issued on 1 July, after the end, so there is none.
RANGE_START = date(2025, 1, 1)
RANGE_END = date(2026, 6, 30)
SNAPSHOT = datetime(2026, 6, 30, 23, 59)

# Postage: a base per service plus a rate per started kilogram.
BASE = {"economy": 350, "standard": 500, "express": 900}      # cents
PER_KG = {"economy": 60, "standard": 90, "express": 150}      # cents per started kg
# How long the line haul takes, in days, by service (min, max); delivery is
# the next working morning after arrival.
TRANSIT = {"economy": (2, 5), "standard": (1, 2), "express": (0, 1)}

TABLES = ["depots", "couriers", "customers", "parcels", "scans", "invoices"]

DEPOTS = [("Central Hub", "central", 48, "2017-03-01"), ("Old Foundry", "central", 12, "2018-06-11"),
          ("Northgate", "north", 24, "2017-03-01"), ("Moorside", "north", 16, "2020-09-15"),
          ("Docklands", "east", 30, "2017-03-01"), ("Harbour Point", "east", 14, "2021-02-01"),
          ("Southfield", "south", 20, "2018-01-20"), ("Millbank", "south", 18, "2019-10-05"),
          ("Westway", "west", 26, "2017-03-01"), ("Hillcrest", "west", 10, "2022-05-30")]
CLOSED_DEPOT = 2             # Old Foundry closes part-way through
CLOSED_ON = date(2026, 2, 1)

FIRST = ["Aisha", "Bartholomew", "Cerys", "Dmitri", "Eleanor", "Farouk",
         "Grace", "Hamid", "Imogen", "Jonah", "Kwame", "Leila", "Marcus",
         "Nadia", "Oluwaseun", "Priya", "Quentin", "Rosa", "Samir", "Tamsin",
         "Umar", "Verity", "Wilfred", "Xiu", "Yusuf", "Zara"]
LAST = ["Achebe", "Baxter", "Chowdhury", "Dalgleish", "Ekwueme", "Fairweather",
        "Grzybowski", "Hollingsworth", "Iqbal", "Jankowski", "Khatri",
        "Lindqvist", "Mbeki", "Nakamura", "Okonjo", "Papadopoulos", "Quraishi",
        "Rasmussen", "Sowerby", "Tremblay", "Uddin", "Villanueva", "Whitcombe",
        "Yilmaz", "Zielinski"]
TRADES = ["Bakery", "Books", "Bicycles", "Pharmacy", "Florist", "Printers", "Textiles",
          "Hardware", "Ceramics", "Optics", "Coffee", "Garden Supplies", "Records", "Toys"]
SUFFIX = ["Ltd", "& Sons", "& Co", "Supplies", "Direct", "Studio"]
AREAS = ["NG1", "NG2", "NG3", "NG5", "NG7", "NG9", "DE1", "DE22", "LE1", "LE4", "S1", "S8"]
VEHICLES = ["van"] * 6 + ["bike"] * 3 + ["lorry"]
SERVICES = ["economy"] * 5 + ["standard"] * 3 + ["express"] * 2
KINDS = ["personal"] * 13 + ["business"] * 7


def _d(d):
    return d.isoformat()


def _t(t):
    return t.strftime("%Y-%m-%d %H:%M")


def _ceil_div(a, b):
    return -(-a // b)


def postage(service, weight_g):
    """Postage in cents: a base for the service plus a rate per started kg."""
    return BASE[service] + PER_KG[service] * _ceil_div(weight_g, 1000)


def _next_morning(rng, t, days=1):
    """A time in the morning `days` days after t's date."""
    day = t.date() + timedelta(days=days)
    return datetime.combine(day, datetime.min.time()) + timedelta(
        hours=rng.randint(7, 11), minutes=rng.randint(0, 59))


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

        # ---- depots: ten, one of which closes ------------------------------
        with conn:
            conn.executemany(
                "INSERT INTO depots (depot_id, name, region, bays, opened_on, closed_on)"
                " VALUES (?,?,?,?,?,?)",
                [(i + 1, n, r, b, o, _d(CLOSED_ON) if i + 1 == CLOSED_DEPOT else None)
                 for i, (n, r, b, o) in enumerate(DEPOTS)])
        depots = list(range(1, len(DEPOTS) + 1))
        open_depots = [d for d in depots if d != CLOSED_DEPOT]

        # ---- couriers: 60, a few who have left -----------------------------
        couriers = []
        for _ in range(60):
            depot = rng.choice(depots)
            hired = date(2018, 1, 1) + timedelta(days=rng.randint(0, 2900))
            left = None
            if rng.random() < 0.13:
                left = _d(RANGE_START + timedelta(days=rng.randint(60, 500)))
            couriers.append((f"{rng.choice(FIRST)} {rng.choice(LAST)}", depot,
                             rng.choice(VEHICLES), _d(hired), left))
        # the closed depot's couriers move to the hub when it shuts; in the
        # data that shows as their depot being the hub from the start, except
        # for two who left when it closed
        with conn:
            conn.executemany(
                "INSERT INTO couriers (name, depot_id, vehicle, hired_on, left_on)"
                " VALUES (?,?,?,?,?)", couriers)

        def courier_at(depot, when):
            """A courier working from `depot` on `when`, or from the hub."""
            pool = [i + 1 for i, c in enumerate(couriers)
                    if c[1] == depot and c[3] <= _d(when.date())
                    and (c[4] is None or c[4] > _d(when.date()))]
            if not pool:
                pool = [i + 1 for i, c in enumerate(couriers)
                        if c[1] == 1 and (c[4] is None or c[4] > _d(when.date()))]
            return rng.choice(pool)

        # ---- customers: 700, some who never send ---------------------------
        customers = []
        for _ in range(700):
            kind = rng.choice(KINDS)
            if kind == "business":
                name = f"{rng.choice(LAST)} {rng.choice(TRADES)} {rng.choice(SUFFIX)}"
            else:
                name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
            joined = date(2022, 1, 1) + timedelta(days=rng.randint(0, 1640))
            joined = min(joined, RANGE_END)
            area = None if rng.random() < 0.1 else rng.choice(AREAS)
            customers.append((name, kind, rng.choice(depots), _d(joined), area))
        with conn:
            conn.executemany(
                "INSERT INTO customers (name, kind, depot_id, joined_on, postcode_area)"
                " VALUES (?,?,?,?,?)", customers)
        never = set(rng.sample(range(1, 701), 80))
        senders = [c for c in range(1, 701) if c not in never]
        heavy = rng.sample([c for c in senders if customers[c - 1][1] == "business"], 25)

        # ---- parcels and their scans ---------------------------------------
        parcels, scans = [], []
        n_parcels = 24_000
        span_minutes = int((SNAPSHOT - datetime.combine(RANGE_START, datetime.min.time()))
                           .total_seconds() // 60)
        for _ in range(n_parcels):
            collected = datetime.combine(RANGE_START, datetime.min.time()) + timedelta(
                minutes=rng.randint(0, span_minutes))
            # counters open 8 to 18; nothing is handed in at night
            collected = collected.replace(hour=rng.randint(8, 17), minute=rng.randint(0, 59))
            if rng.random() < 0.25:
                cust, origin = None, rng.choice(depots)                    # walk-in
            else:
                cust = rng.choice(heavy) if rng.random() < 0.35 else rng.choice(senders)
                origin = customers[cust - 1][2]
                joined = date.fromisoformat(customers[cust - 1][3])
                if collected.date() < joined:
                    collected = collected.replace(year=joined.year, month=joined.month, day=joined.day)
            if origin == CLOSED_DEPOT and collected.date() >= CLOSED_ON:
                origin = 1
            dest = origin if rng.random() < 0.2 else rng.choice(depots)
            if dest == CLOSED_DEPOT and collected.date() >= CLOSED_ON - timedelta(days=7):
                dest = 1
            service = rng.choice(SERVICES)
            weight = min(int(rng.lognormvariate(7.3, 0.9)) + 50, 30_000)
            lo, hi = TRANSIT[service]
            pid = len(parcels) + 1
            trail = [(pid, origin, None, _t(collected), "collected")]
            if dest != origin:
                departed = collected + timedelta(hours=rng.randint(2, 9))
                arrived = departed + timedelta(days=rng.randint(lo, hi), hours=rng.randint(1, 12))
                trail.append((pid, origin, None, _t(departed), "departed"))
                trail.append((pid, dest, None, _t(arrived), "arrived"))
            else:
                arrived = collected
            out = _next_morning(rng, arrived) if dest != origin or rng.random() < 0.5 else arrived + timedelta(hours=2)
            lost = rng.random() < 0.005
            attempts = 1 + (rng.random() < 0.12) + (rng.random() < 0.02)
            courier = courier_at(dest, out)
            delivered = None
            for attempt in range(attempts):
                trail.append((pid, dest, courier, _t(out), "out_for_delivery"))
                if attempt < attempts - 1 or lost:
                    trail.append((pid, dest, courier, _t(out + timedelta(hours=rng.randint(1, 6))), "failed"))
                    out = _next_morning(rng, out)
                else:
                    delivered = out + timedelta(minutes=rng.randint(30, 420))
                    trail.append((pid, dest, courier, _t(delivered), "delivered"))
            # cut the trail at the snapshot: what has not happened yet is not there
            trail = [s for s in trail if s[3] <= _t(SNAPSHOT)]
            if delivered is None or delivered > SNAPSHOT or lost:
                delivered, courier = None, None
            parcels.append((cust, origin, dest, service, weight, _t(collected),
                            _t(delivered) if delivered else None, courier, postage(service, weight)))
            scans.extend(trail)
        with conn:
            conn.executemany(
                "INSERT INTO parcels (customer_id, origin_depot_id, dest_depot_id, service,"
                " weight_g, collected_at, delivered_at, courier_id, postage_cents)"
                " VALUES (?,?,?,?,?,?,?,?,?)", parcels)
            scans.sort(key=lambda s: (s[3], s[0]))
            conn.executemany(
                "INSERT INTO scans (parcel_id, depot_id, courier_id, scanned_at, status)"
                " VALUES (?,?,?,?,?)", scans)

        # ---- invoices: a business customer's month of postage ---------------
        totals = {}
        for cust, origin, dest, service, weight, collected, delivered, courier, cents in parcels:
            if cust is None or customers[cust - 1][1] != "business":
                continue
            totals[(cust, collected[:7])] = totals.get((cust, collected[:7]), 0) + cents
        invoices = []
        for (cust, period), cents in sorted(totals.items(), key=lambda kv: (kv[0][1], kv[0][0])):
            year, month = int(period[:4]), int(period[5:])
            issued = date(year + (month == 12), month % 12 + 1, 1)
            if issued > RANGE_END:
                continue                                        # June's bill is not out yet
            paid, method = None, None
            if rng.random() < 0.88:
                paid = _d(issued + timedelta(days=rng.randint(3, 45)))
                method = rng.choice(["transfer", "transfer", "card"])
                if paid > _d(RANGE_END):
                    paid, method = None, None
            invoices.append((cust, period, cents, _d(issued), paid, method))
        with conn:
            conn.executemany(
                "INSERT INTO invoices (customer_id, period, amount_cents, issued_on, paid_on, method)"
                " VALUES (?,?,?,?,?,?)", invoices)
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
