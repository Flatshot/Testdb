"""Populate testdb with practice data for a field-service repair depot.

Deterministic: the RNG is seeded and no wall-clock dates are used, so running
this twice produces byte-identical data. Safe to re-run -- it drops and
recreates the tables first, so a schema change is picked up.

    python seed.py

The gaps below are deliberate, not sloppiness. Questions about anti-joins,
NULL handling and COUNT need something real to find:

  * work orders with parts but no labour, labour but no parts, and neither
  * work orders never inspected, and a few inspected twice
  * open work orders (closed_at NULL) alongside cancelled ones
  * technicians who have not certified (cert_level NULL)
  * contracts with no agreed response time, and open-ended contracts
  * parts stocked in no depot at all
  * machines never worked on, customers with no work orders
"""

import random
from datetime import date, timedelta

import db

SEED = 41

# Work orders span this window. Fixed, not derived from today, so the data set
# does not drift as time passes.
RANGE_START = date(2025, 2, 3)
RANGE_END = date(2026, 7, 20)

# Tables in dependency order; dropped in reverse so foreign keys stay satisfied.
TABLES = [
    "regions",
    "customers",
    "sites",
    "machines",
    "depots",
    "technicians",
    "contracts",
    "parts",
    "work_orders",
    "parts_used",
    "labor_entries",
    "inspections",
    "part_stock",
    "invoices",
]

REGIONS = [
    ("North", "United Kingdom"),
    ("Midlands", "United Kingdom"),
    ("South West", "United Kingdom"),
    ("Scotland", "United Kingdom"),
    ("Leinster", "Ireland"),
]

CUSTOMER_NAMES = [
    "Ashfield Dairy", "Brightwater Foods", "Calder Print", "Dunmore Packaging",
    "Eastgate Brewing", "Fenwick Textiles", "Girvan Aggregates", "Harlow Plastics",
    "Ironbridge Castings", "Jesmond Bakery", "Kelvin Engineering",
    "Lomond Distillery", "Marlow Glassworks", "Newforge Metals",
    "Oakhampton Mills", "Penrith Cold Store", "Quarrywood Stone",
    "Ravensbourne Labs", "Selkirk Joinery", "Thornbury Farms",
    "Ulverston Chemicals", "Vale Composites", "Westmoor Recycling",
    "Xavier Precision", "Yardley Bottling", "Zetland Marine",
    "Aldridge Coatings", "Bridgnorth Tooling",
]

CITIES = {
    "North": ["Leeds", "York", "Durham", "Carlisle"],
    "Midlands": ["Derby", "Coventry", "Stoke", "Lincoln"],
    "South West": ["Bristol", "Exeter", "Taunton", "Truro"],
    "Scotland": ["Glasgow", "Dundee", "Perth", "Ayr"],
    "Leinster": ["Dublin", "Drogheda", "Naas", "Wexford"],
}

SITE_SUFFIX = ["Works", "Plant", "Depot", "Unit 4", "North Site", "Yard",
               "Mill", "Annexe"]

MACHINE_MODELS = [
    "AX-200 Filler", "AX-450 Filler", "BR-90 Conveyor", "BR-140 Conveyor",
    "CH-12 Chiller", "CH-30 Chiller", "DL-7 Labeller", "DL-15 Labeller",
    "EP-3 Press", "EP-8 Press", "FS-22 Sorter", "GT-60 Dryer",
]

DEPOTS = [
    ("Leeds Central", "North", 4200),
    ("Coventry Hub", "Midlands", 5100),
    ("Bristol West", "South West", 3300),
    ("Glasgow North", "Scotland", 2800),
]

TECH_NAMES = [
    "Priya Raman", "Tom Alderton", "Grace Okonkwo", "Ben Halliday",
    "Nadia Kaur", "Rory MacLeod", "Iris Chen", "Owen Pritchard",
    "Salma Haddad", "Dmitri Volkov", "Fiona Byrne", "Karl Jensen",
    "Lena Fischer", "Marcus Bell",
]

PART_NAMES = [
    ("Drive belt", "Transmission"), ("Bearing housing", "Transmission"),
    ("Timing chain", "Transmission"), ("Gearbox seal", "Transmission"),
    ("Coupling sleeve", "Transmission"), ("Servo motor", "Electrical"),
    ("Contactor 40A", "Electrical"), ("Relay board", "Electrical"),
    ("Wiring loom", "Electrical"), ("Encoder disc", "Electrical"),
    ("Control PCB", "Electrical"), ("Proximity sensor", "Sensors"),
    ("Load cell", "Sensors"), ("Thermocouple", "Sensors"),
    ("Pressure switch", "Sensors"), ("Optical gate", "Sensors"),
    ("Hydraulic hose", "Hydraulics"), ("Pump cartridge", "Hydraulics"),
    ("Solenoid valve", "Hydraulics"), ("Accumulator", "Hydraulics"),
    ("O-ring set", "Hydraulics"), ("Filter element", "Filtration"),
    ("Strainer basket", "Filtration"), ("Membrane pack", "Filtration"),
    ("Carbon cartridge", "Filtration"), ("Guard panel", "Chassis"),
    ("Castor wheel", "Chassis"), ("Levelling foot", "Chassis"),
    ("Hinge assembly", "Chassis"), ("Access hatch", "Chassis"),
    ("Compressor head", "Refrigeration"), ("Expansion valve", "Refrigeration"),
    ("Condenser fan", "Refrigeration"), ("Evaporator coil", "Refrigeration"),
    ("Heating element", "Thermal"), ("Insulation jacket", "Thermal"),
    ("Fan blade", "Thermal"), ("Nozzle tip", "Consumables"),
    ("Squeegee blade", "Consumables"), ("Ink cup", "Consumables"),
]

PRIORITIES = ["low", "normal", "high", "critical"]
INSPECTION_RESULTS = ["pass", "fail", "conditional"]
TIERS = ["bronze", "silver", "gold"]


def _random_date(rng, start, end):
    return start + timedelta(days=rng.randrange((end - start).days + 1))


def _iso(d):
    return d.isoformat()


def seed():
    rng = random.Random(SEED)

    conn = db.connect()
    try:
        with conn:
            # Drop rather than DELETE so schema changes are picked up.
            conn.execute("PRAGMA foreign_keys=OFF")
            for table in reversed(TABLES):
                conn.execute(f"DROP TABLE IF EXISTS {table}")
        conn.executescript(db.SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.execute("PRAGMA foreign_keys=ON")

        with conn:
            # ---------------------------------------------------------- regions
            region_rows = [(i, name, country)
                           for i, (name, country) in enumerate(REGIONS, 1)]
            conn.executemany(
                "INSERT INTO regions (region_id, name, country) VALUES (?, ?, ?)",
                region_rows,
            )
            region_by_name = {name: i for i, name, _ in region_rows}

            # -------------------------------------------------------- customers
            customer_rows = []
            for cid, name in enumerate(CUSTOMER_NAMES, 1):
                region = REGIONS[rng.randrange(len(REGIONS))][0]
                signed = _random_date(rng, date(2019, 1, 1), date(2025, 1, 20))
                # A fifth of accounts were never graded -- NULL, not 'bronze'.
                tier = None if rng.random() < 0.20 else TIERS[rng.randrange(3)]
                customer_rows.append((cid, name, region_by_name[region],
                                      _iso(signed), tier))
            conn.executemany(
                "INSERT INTO customers (customer_id, name, region_id, signed_on,"
                " account_tier) VALUES (?, ?, ?, ?, ?)",
                customer_rows,
            )

            # ------------------------------------------------------------ sites
            site_rows = []
            sid = 0
            sites_by_customer = {}
            for cid, _name, region_id, _signed, _tier in customer_rows:
                region_name = REGIONS[region_id - 1][0]
                # Most customers have one or two sites; a few have three, which
                # is what makes rolling site figures up to the customer a trap.
                n_sites = rng.choices([1, 2, 3], weights=[5, 3, 2])[0]
                sites_by_customer[cid] = []
                for k in range(n_sites):
                    sid += 1
                    city = CITIES[region_name][rng.randrange(4)]
                    suffix = SITE_SUFFIX[rng.randrange(len(SITE_SUFFIX))]
                    site_rows.append((sid, cid, f"{city} {suffix}", city,
                                      region_id))
                    sites_by_customer[cid].append(sid)
            conn.executemany(
                "INSERT INTO sites (site_id, customer_id, name, city, region_id)"
                " VALUES (?, ?, ?, ?, ?)",
                site_rows,
            )

            # --------------------------------------------------------- machines
            machine_rows = []
            mid = 0
            for site in site_rows:
                s_id = site[0]
                for _ in range(rng.choices([1, 2, 3], weights=[4, 4, 2])[0]):
                    mid += 1
                    model = MACHINE_MODELS[rng.randrange(len(MACHINE_MODELS))]
                    installed = _random_date(rng, date(2018, 3, 1),
                                             date(2025, 6, 1))
                    # A quarter were never registered for warranty: NULL.
                    # The rest have a real date, some already in the past.
                    if rng.random() < 0.25:
                        warranty = None
                    else:
                        warranty = _iso(installed + timedelta(
                            days=rng.choice([365, 730, 1095, 1460])))
                    machine_rows.append((mid, s_id, model, f"SN{100000 + mid}",
                                         _iso(installed), warranty))
            conn.executemany(
                "INSERT INTO machines (machine_id, site_id, model, serial,"
                " installed_on, warranty_until) VALUES (?, ?, ?, ?, ?, ?)",
                machine_rows,
            )

            # ----------------------------------------------------------- depots
            depot_rows = [
                (i, name, region_by_name[region], cap,
                 _iso(date(2016 + i, 4, 1)))
                for i, (name, region, cap) in enumerate(DEPOTS, 1)
            ]
            conn.executemany(
                "INSERT INTO depots (depot_id, name, region_id, capacity_units,"
                " opened_on) VALUES (?, ?, ?, ?, ?)",
                depot_rows,
            )

            # ------------------------------------------------------ technicians
            # Technician 1 is the depot manager: supervisor_id NULL.
            tech_rows = []
            for tid, name in enumerate(TECH_NAMES, 1):
                depot = 1 if tid == 1 else rng.randrange(1, len(DEPOTS) + 1)
                hired = _random_date(rng, date(2015, 1, 5), date(2024, 11, 1))
                supervisor = None if tid == 1 else (
                    1 if tid <= 4 else rng.randrange(2, 5))
                rate = round(rng.uniform(38, 82), 2)
                # Four technicians have not sat the certification yet.
                cert = None if tid in (6, 9, 12, 14) else rng.randint(1, 5)
                tech_rows.append((tid, name, depot, _iso(hired), supervisor,
                                  rate, cert))
            conn.executemany(
                "INSERT INTO technicians (technician_id, name, depot_id,"
                " hired_on, supervisor_id, hourly_rate, cert_level)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                tech_rows,
            )

            # -------------------------------------------------------- contracts
            contract_rows = []
            ctr = 0
            for cid, *_ in customer_rows:
                # Some customers have no contract; a few have two, which makes
                # contracts a second child of customers and so a fan-out risk.
                n = rng.choices([0, 1, 2], weights=[2, 6, 3])[0]
                for _ in range(n):
                    ctr += 1
                    start = _random_date(rng, date(2022, 1, 1),
                                         date(2025, 9, 1))
                    # A third are open-ended: end_date NULL, not expired.
                    end = None if rng.random() < 0.33 else _iso(
                        start + timedelta(days=rng.choice([365, 730, 1095])))
                    fee = round(rng.uniform(180, 2400), 2)
                    # A quarter never agreed a response time.
                    resp = None if rng.random() < 0.25 else rng.choice(
                        [4, 8, 12, 24, 48, 72])
                    contract_rows.append((ctr, cid, _iso(start), end, fee, resp))
            conn.executemany(
                "INSERT INTO contracts (contract_id, customer_id, start_date,"
                " end_date, monthly_fee, response_hours)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                contract_rows,
            )

            # ------------------------------------------------------------ parts
            part_rows = []
            for pid, (name, category) in enumerate(PART_NAMES, 1):
                cost = round(rng.uniform(4, 480), 2)
                # A sixth of parts have never been weighed: NULL, not 0.
                weight = None if rng.random() < 0.17 else rng.randrange(
                    20, 9000, 10)
                part_rows.append((pid, name, category, cost, weight))
            conn.executemany(
                "INSERT INTO parts (part_id, name, category, unit_cost,"
                " weight_grams) VALUES (?, ?, ?, ?, ?)",
                part_rows,
            )

            # ------------------------------------------------------ work_orders
            # Machines are picked from a subset so some are never worked on,
            # and customers 7 and 19 are excluded entirely so an anti-join can
            # find customers who have never raised a work order.
            quiet_sites = {s[0] for s in site_rows if s[1] in (7, 19)}
            workable = [m[0] for m in machine_rows
                        if m[0] % 7 != 0 and m[1] not in quiet_sites]
            wo_rows = []
            for wid in range(1, 181):
                machine = workable[rng.randrange(len(workable))]
                opened = _random_date(rng, RANGE_START, RANGE_END)
                status = rng.choices(["closed", "open", "cancelled"],
                                     weights=[72, 19, 9])[0]
                if status == "closed":
                    closed = _iso(opened + timedelta(
                        days=rng.choices([1, 2, 3, 5, 8, 13, 21],
                                         weights=[6, 6, 5, 4, 3, 2, 1])[0]))
                else:
                    # Open and cancelled jobs both have closed_at NULL, so
                    # "still open" needs the status, not just the NULL.
                    closed = None
                # A tenth of jobs sit unassigned in the queue.
                tech = None if rng.random() < 0.10 else rng.randrange(
                    1, len(TECH_NAMES) + 1)
                priority = rng.choices(PRIORITIES, weights=[3, 6, 4, 2])[0]
                wo_rows.append((wid, machine, tech, _iso(opened), closed,
                                priority, status))
            conn.executemany(
                "INSERT INTO work_orders (work_order_id, machine_id,"
                " technician_id, opened_at, closed_at, priority, status)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                wo_rows,
            )

            # ------------------------------------------------------- parts_used
            # Parts 39 and 40 are never fitted, so an anti-join finds them.
            usable_parts = list(range(1, len(PART_NAMES) - 1))
            parts_used_rows = []
            for wid, _m, _t, _o, _c, _p, status in wo_rows:
                if status == "cancelled" or rng.random() < 0.14:
                    continue  # no parts on this job
                n = rng.choices([1, 2, 3, 4, 5], weights=[5, 6, 5, 3, 2])[0]
                chosen = rng.sample(usable_parts, n)
                for pid in chosen:
                    qty = rng.choices([1, 2, 3, 4, 6, 8],
                                      weights=[8, 6, 4, 3, 2, 1])[0]
                    base = part_rows[pid - 1][3]
                    price = round(base * rng.uniform(1.25, 1.9), 2)
                    disc = rng.choices([0.0, 0.05, 0.10, 0.15],
                                       weights=[12, 4, 3, 1])[0]
                    parts_used_rows.append((wid, pid, qty, price, disc))
            conn.executemany(
                "INSERT INTO parts_used (work_order_id, part_id, quantity,"
                " unit_price, discount) VALUES (?, ?, ?, ?, ?)",
                parts_used_rows,
            )

            # ---------------------------------------------------- labor_entries
            # Multiple visits per job is the whole point: this is what makes
            # joining parts_used and labor_entries in one block multiply.
            labor_rows = []
            entry = 0
            for wid, _m, tech, opened, _c, _p, status in wo_rows:
                if status == "cancelled" or rng.random() < 0.11:
                    continue  # no labour logged
                n = rng.choices([1, 2, 3, 4], weights=[7, 6, 3, 1])[0]
                start = date.fromisoformat(opened)
                offset = 0
                for k in range(n):
                    entry += 1
                    # Usually the assigned technician, but a fifth of visits are
                    # covered by somebody else. So the technician who logged a
                    # visit is NOT reliably the one the job is assigned to.
                    if tech is None or rng.random() < 0.20:
                        who = rng.randrange(1, len(TECH_NAMES) + 1)
                    else:
                        who = tech
                    # Consecutive visits sometimes land on the same day, so
                    # ordering by work_date alone leaves genuine ties.
                    day = start + timedelta(days=offset)
                    offset += rng.choice([0, 1, 1, 2, 3])
                    hours = round(rng.choice([0.5, 1.0, 1.5, 2.0, 2.5, 3.0,
                                              4.0, 5.5, 7.0]), 2)
                    rate = tech_rows[who - 1][5]
                    labor_rows.append((entry, wid, who, _iso(day), hours, rate))
            conn.executemany(
                "INSERT INTO labor_entries (entry_id, work_order_id,"
                " technician_id, work_date, hours, rate)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                labor_rows,
            )

            # ------------------------------------------------------ inspections
            insp_rows = []
            insp = 0
            for wid, _m, _t, opened, closed, _p, status in wo_rows:
                if status != "closed":
                    continue
                # Most closed jobs are inspected once, some twice, some not at
                # all -- so COUNT(*) and COUNT(inspection_id) diverge.
                n = rng.choices([0, 1, 2], weights=[2, 7, 2])[0]
                base = date.fromisoformat(closed)
                for k in range(n):
                    insp += 1
                    when = base + timedelta(days=k + rng.randint(0, 4))
                    result = rng.choices(INSPECTION_RESULTS,
                                         weights=[7, 2, 3])[0]
                    # A fifth carry a verdict but no numeric score.
                    score = None if rng.random() < 0.20 else rng.randint(41, 99)
                    insp_rows.append((insp, wid, _iso(when), result, score))
            conn.executemany(
                "INSERT INTO inspections (inspection_id, work_order_id,"
                " inspected_at, result, score) VALUES (?, ?, ?, ?, ?)",
                insp_rows,
            )

            # ------------------------------------------------------- part_stock
            # The last three parts are stocked in no depot at all.
            stocked = list(range(1, len(PART_NAMES) - 2))
            stock_rows = []
            for pid in stocked:
                for did in range(1, len(DEPOTS) + 1):
                    if rng.random() < 0.32:
                        continue  # not carried at this depot
                    qty = rng.randrange(0, 260)
                    # A quarter of lines have no agreed reorder policy.
                    reorder = None if rng.random() < 0.25 else rng.choice(
                        [10, 20, 25, 40, 60])
                    counted = None if rng.random() < 0.30 else _iso(
                        _random_date(rng, date(2025, 6, 1), RANGE_END))
                    stock_rows.append((did, pid, qty, reorder, counted))
            conn.executemany(
                "INSERT INTO part_stock (depot_id, part_id, quantity_on_hand,"
                " reorder_level, last_counted_at) VALUES (?, ?, ?, ?, ?)",
                stock_rows,
            )

            # --------------------------------------------------------- invoices
            # Only closed jobs are invoiced, and not even all of those.
            parts_total = {}
            for wid, pid, qty, price, disc in parts_used_rows:
                parts_total[wid] = parts_total.get(wid, 0.0) + \
                    qty * price * (1 - disc)
            labor_total = {}
            for _e, wid, _t, _d, hours, rate in labor_rows:
                labor_total[wid] = labor_total.get(wid, 0.0) + hours * rate

            inv_rows = []
            inv = 0
            for wid, _m, _t, _o, closed, _p, status in wo_rows:
                if status != "closed" or rng.random() < 0.14:
                    continue
                inv += 1
                amount = round(parts_total.get(wid, 0.0)
                               + labor_total.get(wid, 0.0), 2)
                issued = date.fromisoformat(closed) + timedelta(
                    days=rng.randint(1, 10))
                st = rng.choices(["PAID", "PENDING", "OVERDUE", "VOID"],
                                 weights=[11, 4, 3, 1])[0]
                paid = _iso(issued + timedelta(days=rng.randint(3, 45))) \
                    if st == "PAID" else None
                inv_rows.append((inv, wid, _iso(issued), amount, st, paid))
            conn.executemany(
                "INSERT INTO invoices (invoice_id, work_order_id, issued_on,"
                " amount, status, paid_on) VALUES (?, ?, ?, ?, ?, ?)",
                inv_rows,
            )
    finally:
        conn.close()

    return {t: n for t, n in _counts().items()}


def _counts():
    conn = db.connect()
    try:
        return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in TABLES}
    finally:
        conn.close()


if __name__ == "__main__":
    for table, n in seed().items():
        print(f"{table:>14}: {n:>5}")
    print(f"\nseeded {db.DB_PATH}")
