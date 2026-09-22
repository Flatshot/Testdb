"""Populate testdb with practice data for a regional railway.

Deterministic: the RNG is seeded and no wall-clock dates are used, so running
this twice produces byte-identical data. Safe to re-run -- it drops every table
first, so a schema change is picked up.

    python seed.py

The gaps below are deliberate. Questions about anti-joins, NULL handling and
COUNT need something real to find:

  * cancelled services, which have no stops at all
  * stations no service calls at
  * stops that were skipped, so actual_arrive is NULL
  * tickets with no destination recorded (open returns)
  * incidents whose delay was never quantified
  * units that have never been assigned to a service
  * a five-deep reporting tree, with staff who manage nobody
  * stations nobody has surveyed for step-free access
"""

import random
from datetime import date, timedelta

import db

SEED = 701

# Services are generated per line per day across this window. stops is the big
# table -- roughly eight per service -- and it is what the efficiency questions
# are asked against, so it needs to be large enough that a scan is felt.
RANGE_START = date(2025, 1, 1)
RANGE_END = date(2026, 6, 30)
# A flat timetable makes a whole class of question ungradeable: with the same
# number of services every day, "the last day of the month" and "the 15th" give
# identical counts, so a wrong query still matches. Runs per line vary by day of
# the week and by season instead.
RUNS_WEEKDAY = 4
RUNS_SATURDAY = 3
RUNS_SUNDAY = 2
SUMMER = (6, 7, 8)          # an extra working on the busier lines
WINTER = (1, 2)             # and one fewer in the quiet months

TABLES = [
    "operators", "lines", "stations", "station_footfall", "staff",
    "rolling_stock", "services", "stops", "service_units", "tickets",
    "incidents",
]

OPERATORS = [("Northern Rail", 1997), ("Coastway", 2004),
             ("Vale Connect", 2012), ("Pennine Express", 1988)]

LINES = [("Coast Line", "blue"), ("Vale Line", "green"),
         ("Moor Line", "purple"), ("City Loop", "red"),
         ("Estuary Line", "orange"), ("Dales Line", "brown")]

TOWNS = ["Ashford", "Brindley", "Carrow", "Dunmere", "Eastgate", "Fenwick",
         "Garsdale", "Holbeck", "Ilkeston", "Jarrow", "Kirkstall", "Langton",
         "Marsden", "Netherby", "Oakworth", "Pentre", "Quarrydale", "Rosthorne",
         "Southwell", "Trentham"]
SUFFIXES = ["Central", "Parkway", "Bridge", "North", "South", "Halt",
            "Junction", "Riverside"]

FIRST = ["Alan", "Bernice", "Callum", "Dilys", "Eamon", "Freya", "Gareth",
         "Heulwen", "Ivan", "Joyce", "Kenan", "Lowri", "Martyn", "Nerys",
         "Osian", "Petra", "Rhodri", "Sian", "Tomos", "Verity"]
LAST = ["Ackroyd", "Broadbent", "Cadwallader", "Dewhurst", "Eccleston",
        "Fothergill", "Greenhalgh", "Hetherington", "Illingworth", "Jepson",
        "Kirkbride", "Lightfoot", "Micklethwait", "Nuttall", "Ormerod",
        "Pemberton", "Ravenscroft", "Sedgwick", "Thistlethwaite", "Wainwright"]

ROLES = ["driver", "guard", "dispatcher", "manager"]
MODELS = ["Class 150", "Class 156", "Class 158", "Class 170", "Class 195",
          "Class 331", "Class 802"]
CLASSES = ["first", "standard", "advance"]
KINDS = ["signal", "weather", "fault", "trespass", "staffing"]


def _iso(d):
    return d.isoformat()


def _hhmm(minutes):
    return f"{minutes // 60 % 24:02d}:{minutes % 60:02d}"


def seed():
    rng = random.Random(SEED)
    conn = db.connect()
    try:
        with conn:
            conn.execute("PRAGMA foreign_keys=OFF")
            for t in [r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                    " AND name NOT LIKE 'sqlite_%'")]:
                conn.execute(f'DROP TABLE IF EXISTS "{t}"')
        conn.executescript(db.SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.execute("PRAGMA foreign_keys=ON")

        with conn:
            conn.executemany(
                "INSERT INTO operators (operator_id, name, since_year)"
                " VALUES (?, ?, ?)",
                [(i, n, y) for i, (n, y) in enumerate(OPERATORS, 1)])
            conn.executemany(
                "INSERT INTO lines (line_id, name, colour) VALUES (?, ?, ?)",
                [(i, n, c) for i, (n, c) in enumerate(LINES, 1)])

            # ------------------------------------------------------- stations
            station_rows, used = [], set()
            for sid in range(1, 61):
                while True:
                    town = TOWNS[rng.randrange(len(TOWNS))]
                    name = (town if rng.random() < 0.35
                            else f"{town} {SUFFIXES[rng.randrange(len(SUFFIXES))]}")
                    if name not in used:
                        used.add(name)
                        break
                opened = date(1840, 1, 1) + timedelta(
                    days=rng.randrange(0, 60000))
                # A tenth have never been surveyed for step-free access.
                step = None if rng.random() < 0.10 else rng.choice([0, 1])
                station_rows.append((sid, name, town, _iso(opened), step))
            conn.executemany(
                "INSERT INTO stations (station_id, name, town, opened_on,"
                " step_free) VALUES (?, ?, ?, ?, ?)", station_rows)

            # ----------------------------------------------- station_footfall
            foot = []
            for sid in range(1, 61):
                base = rng.randrange(20_000, 400_000)
                for year in (2023, 2024, 2025):
                    qs = [max(0, int(base * rng.uniform(0.18, 0.32)))
                          for _ in range(4)]
                    foot.append((sid, year, *qs))
            conn.executemany(
                "INSERT INTO station_footfall (station_id, year, q1, q2, q3,"
                " q4) VALUES (?, ?, ?, ?, ?, ?)", foot)

            # ---------------------------------------------------------- staff
            staff_rows = []
            for stid in range(1, 41):
                name = (FIRST[rng.randrange(len(FIRST))] + " "
                        + LAST[rng.randrange(len(LAST))])
                role = "manager" if stid <= 5 else ROLES[rng.randrange(3)]
                if stid == 1:
                    boss = None
                elif stid <= 5:
                    boss = 1
                else:
                    # One draw whatever the level, so the rest of the seed
                    # stream is untouched; the offsets just deepen the tree.
                    pick = rng.randrange(2, 6)
                    if stid <= 15:
                        boss = pick
                    elif stid <= 25:
                        boss = pick + 4
                    else:
                        boss = pick + 14
                hired = date(2005, 1, 1) + timedelta(days=rng.randrange(7000))
                salary = rng.randrange(26_000, 71_000)
                staff_rows.append((stid, name, rng.randrange(1, 61), role,
                                   _iso(hired), boss, salary))
            conn.executemany(
                "INSERT INTO staff (staff_id, name, base_station, role,"
                " hired_on, reports_to, salary) VALUES (?, ?, ?, ?, ?, ?, ?)",
                staff_rows)

            # -------------------------------------------------- rolling stock
            stock = []
            for uid in range(1, 51):
                built = rng.randrange(1988, 2023)
                # Older units may have been refurbished; newer ones have not.
                refurb = (built + rng.randrange(12, 25)
                          if built < 2005 and rng.random() < 0.7 else None)
                stock.append((uid, MODELS[rng.randrange(len(MODELS))],
                              rng.choice([120, 148, 176, 200, 242, 300]),
                              built, refurb))
            conn.executemany(
                "INSERT INTO rolling_stock (unit_id, model, seats, built_year,"
                " refurbished_year) VALUES (?, ?, ?, ?, ?)", stock)

            # ------------------------------------------- a route per line ----
            # Each line calls at a fixed ordered list of stations. Five
            # stations are on no line at all.
            pool = list(range(1, 56))
            rng.shuffle(pool)
            routes, at = {}, 0
            for lid in range(1, len(LINES) + 1):
                n = rng.randrange(6, 11)
                routes[lid] = pool[at:at + n]
                at += n
                if at + 10 > len(pool):
                    at = 0

            # Each line draws its trains from a pool of units. Pools overlap
            # but no unit works every line, so "used on all six" is a real
            # question rather than a description of everything.
            pools = {}
            for lid in range(1, len(LINES) + 1):
                start = (lid - 1) * 7
                pools[lid] = [((start + k) % 45) + 1 for k in range(14)]

            # ------------------------------------------------------- services
            svc_rows, stop_rows, unit_rows = [], [], []
            svc = 0
            day = RANGE_START
            while day <= RANGE_END:
                weekday = day.weekday()          # 0 Monday .. 6 Sunday
                for lid in range(1, len(LINES) + 1):
                    if weekday == 6:
                        runs = RUNS_SUNDAY
                    elif weekday == 5:
                        runs = RUNS_SATURDAY
                    else:
                        runs = RUNS_WEEKDAY
                    if day.month in SUMMER and lid % 2 == 1:
                        runs += 1
                    elif day.month in WINTER and runs > 1:
                        runs -= 1
                    # A line drops the odd working at short notice.
                    if runs > 1 and rng.random() < 0.08:
                        runs -= 1
                    for run in range(runs):
                        svc += 1
                        dep = 6 * 60 + run * 210 + rng.randrange(0, 40)
                        cancelled = 1 if rng.random() < 0.03 else 0
                        svc_rows.append((svc, lid,
                                         rng.randrange(1, len(OPERATORS) + 1),
                                         _iso(day), _hhmm(dep), cancelled))
                        if cancelled:
                            continue          # cancelled services have no stops
                        t = dep
                        for seq, st in enumerate(routes[lid], 1):
                            t += rng.randrange(4, 15)
                            # One stop in twenty was skipped or not recorded.
                            actual = (None if rng.random() < 0.05
                                      else _hhmm(t + rng.randrange(-1, 9)))
                            stop_rows.append((svc, seq, st, _hhmm(t), actual))
                        for pos in range(1, rng.randrange(2, 4)):
                            unit_rows.append(
                                (svc, pools[lid][rng.randrange(
                                    len(pools[lid]))], pos))
                day += timedelta(days=1)
            conn.executemany(
                "INSERT INTO services (service_id, line_id, operator_id,"
                " run_date, depart_time, cancelled) VALUES (?, ?, ?, ?, ?, ?)",
                svc_rows)
            conn.executemany(
                "INSERT INTO stops (service_id, stop_seq, station_id,"
                " sched_arrive, actual_arrive) VALUES (?, ?, ?, ?, ?)",
                stop_rows)
            conn.executemany(
                "INSERT OR IGNORE INTO service_units (service_id, unit_id,"
                " position) VALUES (?, ?, ?)", unit_rows)

            running = [s[0] for s in svc_rows if not s[5]]

            # -------------------------------------------------------- tickets
            tick, tid = [], 0
            for s in rng.sample(running, k=int(len(running) * 0.8)):
                # A ticket is for a journey this service actually makes, so
                # from_station and to_station are stations on its own route.
                route = routes[svc_rows[s - 1][1]]
                for _ in range(rng.randrange(1, 8)):
                    tid += 1
                    cls = CLASSES[rng.randrange(3)]
                    base = {"first": 2200, "standard": 900,
                            "advance": 450}[cls]
                    a = rng.randrange(0, len(route) - 1)
                    # A twentieth are open returns with no destination.
                    to = (None if rng.random() < 0.05
                          else route[rng.randrange(a + 1, len(route))])
                    tick.append((tid, s, route[a], to, cls,
                                 base + rng.randrange(0, 900),
                                 svc_rows[s - 1][3]))
            conn.executemany(
                "INSERT INTO tickets (ticket_id, service_id, from_station,"
                " to_station, class, price_pence, sold_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)", tick)

            # ------------------------------------------------------ incidents
            inc, iid = [], 0
            for s in rng.sample(running, k=int(len(running) * 0.09)):
                iid += 1
                # A sixth of incidents were never quantified.
                delay = (None if rng.random() < 0.17
                         else rng.randrange(1, 95))
                inc.append((iid, s, svc_rows[s - 1][3],
                            KINDS[rng.randrange(len(KINDS))], delay))
            conn.executemany(
                "INSERT INTO incidents (incident_id, service_id, reported_at,"
                " kind, delay_minutes) VALUES (?, ?, ?, ?, ?)", inc)
    finally:
        conn.close()
    return _counts()


def _counts():
    conn = db.connect()
    try:
        return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in TABLES}
    finally:
        conn.close()


if __name__ == "__main__":
    for table, n in seed().items():
        print(f"{table:>18}: {n:>7}")
    print(f"\nseeded {db.DB_PATH}")
