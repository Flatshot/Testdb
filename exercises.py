"""Practice exercises: fifteen questions on the parcel-courier schema.

The fifth set on the courier scheme (SEED 1241), two tools per question,
the tiers named by task, on tools the first four courier sets left out,
with prompts that name the tool but do not write the statement. Sets and
ties -- customers who have used both ends of the price list by INTERSECT,
couriers who delivered last year and not this by EXCEPT, depots ranked by
staff with ties kept by DENSE_RANK. Dates, precisely -- June's deliveries
by a half-open range where BETWEEN loses a day, parcels collected on the
last day of a month by chained date modifiers, days employed inside the
data period by the two-argument MAX and MIN. Text, types and lists --
words in a customer's name by LENGTH and REPLACE, what postcode_area
holds by typeof, parcels for a JSON list of depots by json_each. Flags
and totals -- depots above the average depot by HAVING against a nested
aggregate, a lorry-driver flag by EXISTS as a column, June postage at
every depot by TOTAL where SUM gives NULL. And three WRITABLE questions:

  * a partial UNIQUE INDEX that allows one delivery scan per parcel
  * an UPDATE whose SET holds a CASE on region
  * an AFTER DELETE trigger that logs written-off invoices

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script.
"""

import sqlite3

EXERCISES = [
    # ======================================================== 1 Sets and ties
    dict(
        id=1, ledger="Q1282", concept="INTERSECT", tier="1 - Sets and ties",
        title="Customers who have used both ends of the price list",
        prompt=(
            "For each kind of customer: how many have sent at least one"
            " EXPRESS parcel and at least one ECONOMY parcel. Two lists"
            " of customer ids, one per service, combined with the set"
            " operator that keeps only what is in both.\n\n"
            "Return: kind, both_services"
        ),
        solution=("SELECT kind, COUNT(*) FROM customers WHERE customer_id IN"
                  " (SELECT customer_id FROM parcels WHERE service = 'express'"
                  " INTERSECT SELECT customer_id FROM parcels WHERE service = 'economy') GROUP BY kind"),
        trap_sql=("SELECT kind, COUNT(*) FROM customers WHERE customer_id IN"
                  " (SELECT customer_id FROM parcels WHERE service = 'express'"
                  " UNION SELECT customer_id FROM parcels WHERE service = 'economy') GROUP BY kind"),
        note="INTERSECT keeps the rows that appear in BOTH queries and"
             " removes duplicates, so each customer is listed once"
             " however many parcels they sent. UNION, the trap, is"
             " 'either': everyone who has sent an express OR an economy"
             " parcel, which is nearly every sender. The walk-ins' NULL"
             " customer_id is in both lists too, but no customer row has"
             " a NULL id for IN to match.",
        claims=[("two kinds, 223 businesses",
                 lambda rows, c: len(rows) == 2 and ("business", 223) in rows),
                ("605 customers in all",
                 lambda rows, c: sum(r[1] for r in rows) == 605)],
    ),
    dict(
        id=2, ledger="Q1283", concept="EXCEPT", tier="1 - Sets and ties",
        title="Couriers who delivered last year and not this",
        prompt=(
            "The couriers who delivered at least one parcel in 2025 and"
            " none in 2026: name and vehicle. Two lists of courier ids"
            " by delivery year, subtracted with the set operator whose"
            " order of operands matters.\n\n"
            "Return: name, vehicle"
        ),
        solution=("SELECT name, vehicle FROM couriers WHERE courier_id IN"
                  " (SELECT courier_id FROM parcels WHERE delivered_at < '2026-01-01'"
                  " EXCEPT SELECT courier_id FROM parcels WHERE delivered_at >= '2026-01-01')"),
        trap_sql=("SELECT name, vehicle FROM couriers WHERE courier_id IN"
                  " (SELECT courier_id FROM parcels WHERE delivered_at >= '2026-01-01'"
                  " EXCEPT SELECT courier_id FROM parcels WHERE delivered_at < '2026-01-01')"),
        note="EXCEPT keeps the rows of the first query that are not in"
             " the second, so the order of the two is the question: 2025"
             " EXCEPT 2026 is 'stopped delivering', and the trap's 2026"
             " EXCEPT 2025 is 'started this year', which is nobody."
             " Thirteen couriers stopped, and every one of them has a"
             " left_on date in 2025 -- the set arithmetic finds them"
             " without looking at that column.",
        claims=[("thirteen couriers",
                 lambda rows, c: len(rows) == 13),
                ("every one of them has left",
                 lambda rows, c: all(c.execute("SELECT COUNT(*) FROM couriers WHERE name = ? AND vehicle = ? AND left_on IS NOT NULL", r).fetchone()[0] >= 1 for r in rows))],
    ),
    dict(
        id=3, ledger="Q1284", concept="DRK", tier="1 - Sets and ties",
        title="Depots ranked by staff, ties sharing a place",
        prompt=(
            "Every depot with the number of couriers based there, and"
            " its rank by that number, most couriers first -- depots"
            " with the same number share a rank, and the next rank"
            " follows straight on with no gap. Count per depot in a CTE,"
            " then the ranking window function that does not skip.\n\n"
            "Return: name, couriers, rank"
        ),
        solution=("WITH per AS (SELECT d.name, COUNT(c.courier_id) AS n FROM depots d LEFT JOIN couriers c ON c.depot_id = d.depot_id GROUP BY d.depot_id)"
                  " SELECT name, n, DENSE_RANK() OVER (ORDER BY n DESC) FROM per"),
        trap_sql=("WITH per AS (SELECT d.name, COUNT(c.courier_id) AS n FROM depots d LEFT JOIN couriers c ON c.depot_id = d.depot_id GROUP BY d.depot_id)"
                  " SELECT name, n, RANK() OVER (ORDER BY n DESC) FROM per"),
        note="RANK and DENSE_RANK both give ties the same number; they"
             " differ in what comes next. RANK counts the rows ahead --"
             " 1, 2, 3, 4, 4, 4, 4, 8 -- so after four depots tied in"
             " fourth place the next is eighth, which is the trap."
             " DENSE_RANK counts the distinct VALUES ahead: 4, 4, 4, 4,"
             " then 5. Ten depots, six different staff sizes, six ranks.",
        claims=[("ten depots, six ranks with no gap",
                 lambda rows, c: len(rows) == 10 and {r[2] for r in rows} == {1, 2, 3, 4, 5, 6}),
                ("four depots tie on six couriers",
                 lambda rows, c: sum(r[1] == 6 for r in rows) == 4 and len({r[2] for r in rows if r[1] == 6}) == 1)],
    ),
    # ==================================================== 2 Dates, precisely
    dict(
        id=4, ledger="Q1285", concept="BTW", tier="2 - Dates, precisely",
        title="June's deliveries, and the day BETWEEN loses",
        prompt=(
            "For each vehicle type: the parcels its couriers delivered"
            " in June 2026. delivered_at carries a time of day, so a"
            " range that ends at '2026-06-30' stops at midnight on the"
            " 30th; use a half-open range, up to but not including the"
            " first of July.\n\n"
            "Return: vehicle, deliveries"
        ),
        solution=("SELECT c.vehicle, COUNT(*) FROM parcels p JOIN couriers c ON c.courier_id = p.courier_id"
                  " WHERE p.delivered_at >= '2026-06-01' AND p.delivered_at < '2026-07-01' GROUP BY c.vehicle"),
        trap_sql=("SELECT c.vehicle, COUNT(*) FROM parcels p JOIN couriers c ON c.courier_id = p.courier_id"
                  " WHERE p.delivered_at BETWEEN '2026-06-01' AND '2026-06-30' GROUP BY c.vehicle"),
        note="BETWEEN is inclusive, but '2026-06-30' as text is the very"
             " start of that day, so every delivery later on the 30th is"
             " above the upper bound: the trap loses sixty deliveries."
             " >= the first day and < the day AFTER the last is right"
             " for dates, timestamps and anything finer than the bound,"
             " and needs no knowledge of how long the month is.",
        claims=[("three vehicles, 885 by van",
                 lambda rows, c: len(rows) == 3 and ("van", 885) in rows),
                ("1492 June deliveries in all",
                 lambda rows, c: sum(r[1] for r in rows) == 1492)],
    ),
    dict(
        id=5, ledger="Q1286", concept="EOM", tier="2 - Dates, precisely",
        title="Handed in on the last day of the month",
        prompt=(
            "For each service: its parcels, and how many were collected"
            " on the LAST day of a calendar month -- the 31st of"
            " January, the 28th of February 2025, the 30th of April."
            " The last day of any date's month comes from chaining date"
            " modifiers: back to the start of the month, forward a"
            " month, back a day.\n\n"
            "Return: service, parcels, month_end"
        ),
        solution=("SELECT service, COUNT(*), SUM(date(collected_at) = date(collected_at, 'start of month', '+1 month', '-1 day'))"
                  " FROM parcels GROUP BY service"),
        trap_sql=("SELECT service, COUNT(*), SUM(strftime('%d', collected_at) = '31')"
                  " FROM parcels GROUP BY service"),
        note="'start of month', '+1 month', '-1 day' walks to the first"
             " of the month, on to the first of the next, and back one"
             " day: the last day, whatever the month's length. Testing"
             " for day 31, the trap, finds the last day of seven months"
             " and misses the other five. date(collected_at) on the left"
             " cuts the timestamp to its day so the two sides compare"
             " like with like.",
        claims=[("three services, about one parcel in thirty",
                 lambda rows, c: len(rows) == 3 and all(0.02 <= r[2] / r[1] <= 0.05 for r in rows)),
                ("the count matches the eighteen month-ends",
                 lambda rows, c: sum(r[2] for r in rows) == c.execute("SELECT COUNT(*) FROM parcels WHERE date(collected_at) IN ('2025-01-31','2025-02-28','2025-03-31','2025-04-30','2025-05-31','2025-06-30','2025-07-31','2025-08-31','2025-09-30','2025-10-31','2025-11-30','2025-12-31','2026-01-31','2026-02-28','2026-03-31','2026-04-30','2026-05-31','2026-06-30')").fetchone()[0])],
    ),
    dict(
        id=6, ledger="Q1287", concept="CLAMP", tier="2 - Dates, precisely",
        title="Days on the payroll inside the data",
        prompt=(
            "For each vehicle type: its couriers, and the average"
            " number of days they were employed INSIDE the data period,"
            " 2025-01-01 to 2026-06-30, to one decimal. A courier hired"
            " in 2019 counts from the period's start; one who left counts"
            " to their leaving date. The two-argument MAX and MIN pick"
            " the later of two dates and the earlier.\n\n"
            "Return: vehicle, couriers, avg_days"
        ),
        solution=("SELECT vehicle, COUNT(*), ROUND(AVG(julianday(MIN(COALESCE(left_on, '2026-06-30'), '2026-06-30'))"
                  " - julianday(MAX(hired_on, '2025-01-01'))), 1) FROM couriers GROUP BY vehicle"),
        trap_sql=("SELECT vehicle, COUNT(*), ROUND(AVG(julianday(COALESCE(left_on, '2026-06-30'))"
                  " - julianday(hired_on)), 1) FROM couriers GROUP BY vehicle"),
        note="MAX(a, b) with two arguments is a scalar function, not the"
             " aggregate: it compares two values in one row, and it is"
             " how a date is clamped to a range. Most couriers were hired"
             " years before the data begins, so without the clamp the"
             " trap counts service the data cannot see and the averages"
             " run to four and five years. Inside the period's 545 days,"
             " bike couriers were on the payroll for 490 on average.",
        claims=[("three vehicles, sixty couriers",
                 lambda rows, c: len(rows) == 3 and sum(r[1] for r in rows) == 60),
                ("no average longer than the period",
                 lambda rows, c: all(r[2] <= 546 for r in rows))],
    ),
    # ============================================== 3 Text, types and lists
    dict(
        id=7, ledger="Q1288", concept="WRD", tier="3 - Text, types and lists",
        title="How many words in a customer's name",
        prompt=(
            "For each kind of customer and each number of words a name"
            " has: how many customers. Words are spaces plus one, and"
            " the spaces are counted by measuring the name with and"
            " without them -- LENGTH and REPLACE.\n\n"
            "Return: kind, words, customers"
        ),
        solution=("SELECT kind, LENGTH(name) - LENGTH(REPLACE(name, ' ', '')) + 1, COUNT(*)"
                  " FROM customers GROUP BY kind, LENGTH(name) - LENGTH(REPLACE(name, ' ', '')) + 1"),
        trap_sql=("SELECT kind, LENGTH(name) - LENGTH(REPLACE(name, ' ', '')), COUNT(*)"
                  " FROM customers GROUP BY kind, LENGTH(name) - LENGTH(REPLACE(name, ' ', ''))"),
        note="SQLite has no function that counts occurrences, but REPLACE"
             " removes them all and LENGTH measures what is left, so the"
             " difference is the number of spaces -- and words are one"
             " more than that, which the trap forgets. Every person has"
             " two words; businesses run from three ('Achebe Bakery"
             " Ltd') to five ('Iqbal Garden Supplies & Sons').",
        claims=[("four rows, every person two words",
                 lambda rows, c: len(rows) == 4 and ("personal", 2, 453) in rows),
                ("700 customers in all",
                 lambda rows, c: sum(r[2] for r in rows) == 700)],
    ),
    dict(
        id=8, ledger="Q1289", concept="TYP", tier="3 - Text, types and lists",
        title="What the postcode area column actually holds",
        prompt=(
            "For each kind of customer: the storage types found in"
            " postcode_area and how many customers have each. typeof()"
            " names a value's type, and NULL is one of them.\n\n"
            "Return: kind, storage_type, customers"
        ),
        solution="SELECT kind, typeof(postcode_area), COUNT(*) FROM customers GROUP BY kind, typeof(postcode_area)",
        trap_sql="SELECT kind, typeof(postcode_area), COUNT(postcode_area) FROM customers GROUP BY kind, typeof(postcode_area)",
        note="SQLite stores each VALUE with its own type -- integer,"
             " real, text, blob or null -- whatever the column was"
             " declared as, and typeof() reports it; grouping on it"
             " shows at a glance how much of a column is missing."
             " COUNT(postcode_area) skips NULLs, so the trap reports"
             " zero customers of type null. One customer in ten has no"
             " area recorded, businesses and people alike.",
        claims=[("four rows, 31 businesses with no area",
                 lambda rows, c: len(rows) == 4 and ("business", "null", 31) in rows),
                ("73 NULLs in all",
                 lambda rows, c: sum(r[2] for r in rows if r[1] == "null") == 73)],
    ),
    dict(
        id=9, ledger="Q1290", concept="JSE", tier="3 - Text, types and lists",
        title="Parcels bound for the depots on a list",
        prompt=(
            "A caller hands you depot ids as a JSON array, '[3, 6, 10,"
            " 42]'. For each depot on the list that exists: its name and"
            " how many parcels were addressed to it. json_each() turns"
            " the array into rows you can join on.\n\n"
            "Return: name, parcels"
        ),
        solution=("SELECT d.name, COUNT(p.parcel_id) FROM json_each('[3, 6, 10, 42]') j"
                  " JOIN depots d ON d.depot_id = j.value"
                  " LEFT JOIN parcels p ON p.dest_depot_id = d.depot_id GROUP BY d.name"),
        trap_sql=("SELECT d.name, COUNT(p.parcel_id) FROM depots d"
                  " LEFT JOIN parcels p ON p.dest_depot_id = d.depot_id"
                  " WHERE d.depot_id IN ('[3, 6, 10, 42]') GROUP BY d.name"),
        note="json_each is a table-valued function: given JSON text it"
             " returns one row per element, in a column called value,"
             " and FROM can read it like a table. That is how a list"
             " arrives from an application without building SQL text."
             " IN ('[3, 6, 10, 42]'), the trap, compares each id with"
             " one string and matches nothing. Depot 42 does not exist"
             " and the inner join drops it.",
        claims=[("three depots, Northgate with 2357",
                 lambda rows, c: len(rows) == 3 and ("Northgate", 2357) in rows),
                ("depot 42 not among them",
                 lambda rows, c: {r[0] for r in rows} == {"Northgate", "Harbour Point", "Hillcrest"})],
    ),
    # ==================================================== 4 Flags and totals
    dict(
        id=10, ledger="Q1291", concept="HAV", tier="4 - Flags and totals",
        title="Depots busier than the average depot",
        prompt=(
            "The depots where more parcels have been collected than at"
            " the AVERAGE depot, with their count. The average is an"
            " aggregate of an aggregate -- the mean of the per-depot"
            " counts, the closed depot included -- compared with in"
            " HAVING.\n\n"
            "Return: name, parcels"
        ),
        solution=("SELECT d.name, COUNT(*) FROM parcels p JOIN depots d ON d.depot_id = p.origin_depot_id"
                  " GROUP BY d.name HAVING COUNT(*) > (SELECT AVG(n) FROM (SELECT COUNT(*) AS n FROM parcels GROUP BY origin_depot_id))"),
        trap_sql=("SELECT d.name, COUNT(*) FROM parcels p JOIN depots d ON d.depot_id = p.origin_depot_id"
                  " GROUP BY d.name HAVING COUNT(*) > (SELECT COUNT(*) FROM parcels) / (SELECT COUNT(*) FROM depots WHERE closed_on IS NULL)"),
        note="HAVING can compare a group's aggregate with a scalar"
             " subquery, and that subquery can itself average a grouped"
             " result: 24,000 parcels over ten depots is 2,400. The trap"
             " divides by the nine OPEN depots, but Old Foundry's parcels"
             " are in the total, so its bar is 2,666 and Westway, at"
             " 2,621, drops off the list. Four depots are above average.",
        claims=[("four depots, Westway among them",
                 lambda rows, c: len(rows) == 4 and any(r[0] == "Westway" for r in rows)),
                ("every count above 2400",
                 lambda rows, c: all(r[1] > 2400 for r in rows))],
    ),
    dict(
        id=11, ledger="Q1292", concept="EXS", tier="4 - Flags and totals",
        title="Which depots can take a lorry load",
        prompt=(
            "For every depot: a 1 or 0 saying whether it has a lorry"
            " driver still working there, and how many. EXISTS is an"
            " expression, so it can sit in the SELECT list as a column;"
            " a scalar subquery gives the count.\n\n"
            "Return: name, has_lorry, lorry_drivers"
        ),
        solution=("SELECT d.name,"
                  " EXISTS (SELECT 1 FROM couriers c WHERE c.depot_id = d.depot_id AND c.vehicle = 'lorry' AND c.left_on IS NULL),"
                  " (SELECT COUNT(*) FROM couriers c WHERE c.depot_id = d.depot_id AND c.vehicle = 'lorry' AND c.left_on IS NULL)"
                  " FROM depots d"),
        trap_sql=("SELECT d.name, COUNT(*) > 0, COUNT(*)"
                  " FROM depots d LEFT JOIN couriers c ON c.depot_id = d.depot_id AND c.vehicle = 'lorry' AND c.left_on IS NULL"
                  " GROUP BY d.name"),
        note="EXISTS returns 1 or 0 and can be used wherever an"
             " expression can: as a flag column it answers 'is there"
             " any?' without a join. The trap's LEFT JOIN keeps a row for"
             " every depot even when nothing matched, and COUNT(*) counts"
             " that row, so every depot shows 1 and one driver. Five"
             " depots have no lorry driver, Central Hub among them.",
        claims=[("ten depots, five with a lorry driver",
                 lambda rows, c: len(rows) == 10 and sum(r[1] for r in rows) == 5),
                ("the flag agrees with the count",
                 lambda rows, c: all((r[1] == 1) == (r[2] > 0) for r in rows))],
    ),
    dict(
        id=12, ledger="Q1293", concept="TTL", tier="4 - Flags and totals",
        title="June's postage at every depot, zero included",
        prompt=(
            "For every depot, the closed one included: the postage of"
            " the parcels collected there in June 2026, in dollars. A"
            " LEFT JOIN from depots with the June condition in ON, and"
            " TOTAL rather than SUM: SUM of no rows is NULL, TOTAL of no"
            " rows is 0.0.\n\n"
            "Return: name, june_postage"
        ),
        solution=("SELECT d.name, TOTAL(p.postage_cents) / 100.0 FROM depots d"
                  " LEFT JOIN parcels p ON p.origin_depot_id = d.depot_id AND p.collected_at >= '2026-06-01' GROUP BY d.name"),
        trap_sql=("SELECT d.name, SUM(p.postage_cents) / 100.0 FROM depots d"
                  " LEFT JOIN parcels p ON p.origin_depot_id = d.depot_id AND p.collected_at >= '2026-06-01' GROUP BY d.name"),
        note="TOTAL is SQLite's SUM that always returns a real number:"
             " 0.0 for an empty group, where SUM returns NULL. Old"
             " Foundry closed in February and collected nothing in June,"
             " so the LEFT JOIN keeps its row with nothing attached and"
             " the trap's SUM leaves a blank where a report should read"
             " zero. The June condition has to be in ON: in WHERE, Old"
             " Foundry's row would be gone before TOTAL saw it.",
        claims=[("ten depots, Old Foundry at zero",
                 lambda rows, c: len(rows) == 10 and ("Old Foundry", 0.0) in rows),
                ("Central Hub took the most",
                 lambda rows, c: max(rows, key=lambda r: r[1])[0] == "Central Hub")],
    ),
    # =================================================== 5 Changing the data
    dict(
        id=13, ledger="Q1294", concept="UNQ", tier="5 - Changing the data",
        kind="script",
        title="One delivery scan per parcel, enforced",
        prompt=(
            "A parcel may have many scans but only ONE with status"
            " 'delivered'. Create a UNIQUE index on scans that enforces"
            " exactly that and nothing more -- a partial index, with a"
            " WHERE of its own. The question then inserts a second"
            " 'delivered' scan for parcel 1, a first one for parcel 40,"
            " and a 'failed' scan for parcel 1.\n\n"
            "Checked: how many scans dated July got in, and how many of"
            " them are deliveries"
        ),
        solution="CREATE UNIQUE INDEX one_delivery ON scans(parcel_id) WHERE status = 'delivered';",
        trap_sql="CREATE INDEX one_delivery ON scans(parcel_id) WHERE status = 'delivered';",
        driver_sql=("INSERT INTO scans (parcel_id, depot_id, courier_id, scanned_at, status) VALUES (1, 1, 1, '2026-07-01 10:00', 'delivered');\n"
                    "INSERT INTO scans (parcel_id, depot_id, courier_id, scanned_at, status) VALUES (40, 5, 7, '2026-07-01 10:00', 'delivered');\n"
                    "INSERT INTO scans (parcel_id, depot_id, courier_id, scanned_at, status) VALUES (1, 1, 1, '2026-07-01 11:00', 'failed');"),
        probe_sql="SELECT COUNT(*), SUM(status = 'delivered') FROM scans WHERE scanned_at >= '2026-07-01'",
        note="A UNIQUE index is a constraint, and a WHERE on the index"
             " makes it partial: only the rows that match are indexed,"
             " so only they must be unique. Without the WHERE the index"
             " could not even be created -- every parcel has several"
             " scans -- and without UNIQUE, the trap, it speeds up"
             " lookups and refuses nothing. The refusal is reported in"
             " the status bar, not treated as an error.",
        claims=[("two scans in, one of them a delivery",
                 lambda rows, c: rows == [(2, 1)])],
    ),
    dict(
        id=14, ledger="Q1295", concept="UPC", tier="5 - Changing the data",
        kind="script",
        title="More loading bays, more in the centre",
        prompt=(
            "Every depot still open gets more loading bays: ten more in"
            " the central region, four more elsewhere. ONE UPDATE whose"
            " SET adds a CASE on region, with a WHERE that leaves the"
            " closed depot alone.\n\n"
            "Checked: each region's bays added up"
        ),
        solution="UPDATE depots SET bays = bays + CASE region WHEN 'central' THEN 10 ELSE 4 END WHERE closed_on IS NULL;",
        trap_sql="UPDATE depots SET bays = bays + CASE region WHEN 'central' THEN 10 ELSE 4 END;",
        probe_sql="SELECT region, SUM(bays) FROM depots GROUP BY region",
        note="A SET expression can read the row's other columns, and a"
             " CASE inside it makes one statement do what would otherwise"
             " be two UPDATEs with different WHEREs. The ELSE matters:"
             " without it a depot in no listed region would get NULL,"
             " and bays is NOT NULL. The trap forgets the WHERE and gives"
             " Old Foundry, closed since February, ten bays it will"
             " never use.",
        claims=[("the centre up ten, the other regions up eight",
                 lambda rows, c: sorted(rows) == [("central", 70), ("east", 52), ("north", 48), ("south", 46), ("west", 44)])],
    ),
    dict(
        id=15, ledger="Q1296", concept="AUD", tier="5 - Changing the data",
        kind="script",
        title="A record of every invoice written off",
        prompt=(
            "No invoice should vanish without a trace. Create a table"
            " written_off with invoice_id as its primary key, customer_id"
            " and amount_cents, all required; then an AFTER DELETE"
            " trigger on invoices that copies the removed row's three"
            " values into it. The question then deletes every unpaid"
            " invoice issued before July 2025.\n\n"
            "Checked: how many rows the log has, the cents added up, and"
            " its lowest invoice_id"
        ),
        solution=("CREATE TABLE written_off (\n"
                  "  invoice_id   INTEGER PRIMARY KEY,\n"
                  "  customer_id  INTEGER NOT NULL,\n"
                  "  amount_cents INTEGER NOT NULL\n"
                  ");\n"
                  "CREATE TRIGGER log_write_off AFTER DELETE ON invoices\n"
                  "BEGIN\n"
                  "  INSERT INTO written_off (invoice_id, customer_id, amount_cents)\n"
                  "  VALUES (OLD.invoice_id, OLD.customer_id, OLD.amount_cents);\n"
                  "END;"),
        trap_sql=("CREATE TABLE written_off (\n"
                  "  invoice_id   INTEGER PRIMARY KEY,\n"
                  "  customer_id  INTEGER NOT NULL,\n"
                  "  amount_cents INTEGER NOT NULL\n"
                  ");"),
        driver_sql="DELETE FROM invoices WHERE paid_on IS NULL AND issued_on < '2025-07-01';",
        probe_sql="SELECT COUNT(*), SUM(amount_cents), MIN(invoice_id) FROM written_off",
        note="In a DELETE trigger, OLD is the row being removed, and an"
             " AFTER trigger fires once per row, so a single DELETE that"
             " takes out 84 invoices logs all 84. The trap builds the"
             " log table and never writes to it. This is the audit-table"
             " pattern: the application deletes as it always did, and"
             " the database keeps the history on its own.",
        claims=[("84 invoices logged, 280,410 cents",
                 lambda rows, c: rows == [(84, 280410, 3)])],
    ),
]

BY_ID = {ex["id"]: ex for ex in EXERCISES}
TIERS = list(dict.fromkeys(ex["tier"] for ex in EXERCISES))

def query_plan(conn, sql):
    """The rows of EXPLAIN QUERY PLAN, joined into one searchable string.

    SQLite's plan output is a small tree; the `detail` column carries the text
    everyone actually reads -- "SCAN enrolments", "SEARCH ... USING INDEX ...",
    "USE TEMP B-TREE FOR ORDER BY". Joining them gives one string that a
    question can make assertions about.
    """
    return " | ".join(
        r[3] for r in conn.execute("EXPLAIN QUERY PLAN " + sql).fetchall())


def plan_ok(exercise, plan):
    """(passed, message) for an exercise's plan assertions.

    Efficiency questions cannot be graded on their result, because the slow
    way and the fast way return exactly the same rows -- that is what makes
    them worth asking. So they carry `plan_requires` and/or `plan_forbids`,
    checked against EXPLAIN QUERY PLAN, and a right answer has to be BOTH
    correct and taken by the intended route.

    Matching is case-insensitive substring, which is coarse on purpose: it
    should accept any query that reaches the plan the question is about, not
    just the reference wording.
    """
    up = plan.upper()
    for needle in exercise.get("plan_requires", ()):
        if needle.upper() not in up:
            return False, (f"Right rows, but the query plan does not contain"
                           f" {needle!r}.\n  Plan: {plan}")
    for needle in exercise.get("plan_forbids", ()):
        if needle.upper() in up:
            return False, (f"Right rows, but the query plan contains"
                           f" {needle!r}, which this question asks you to"
                           f" avoid.\n  Plan: {plan}")
    return True, ""


def is_script(exercise):
    """True for a writable question: graded on the database AFTER the script.

    A query question is graded on what its SELECT returns. A script question
    runs the editor's contents -- any number of statements, DML or DDL -- in
    a throwaway copy of the database, then runs the question's `probe_sql`
    against the result and grades THAT. So the answer is a state, not a
    result set, and the reference solution is whatever script produces the
    same state.
    """
    return exercise.get("kind") == "script"


def script_result(exercise, script, db_path=None):
    """(rows, error, info) from running `script` and then the probe.

    The pipeline every grader path shares, so the GUI and check_questions.py
    cannot drift:

      1. a fresh sandbox copy of the database
      2. the script, statement by statement, time-limited
      3. `driver_sql`, if the question has one: statements the question itself
         runs afterwards to EXERCISE what the script built -- an INSERT that
         should fire a trigger, or one that a CHECK or trigger should reject.
         Each runs separately and a rejection is recorded, not fatal, because
         "this row must be refused" is a legitimate thing to test.
      4. `probe_sql`, whose rows are the answer

    info carries statement/change counts and any driver rejections, for the
    status bar. error is a string if the script itself failed.
    """
    import db
    conn = db.sandbox(db_path)
    info = {"statements": 0, "changes": 0, "rejected": []}
    try:
        try:
            n, changed, _, _ = db.run_script(conn, script)
            info["statements"], info["changes"] = n, changed
        except (db.QueryTimeout, db.TooManyRows) as exc:
            return None, str(exc), info
        except sqlite3.Error as exc:
            return None, f"SQL error: {exc}", info
        for stmt in db.split_statements(exercise.get("driver_sql", "")):
            try:
                with db.time_limit(conn):
                    conn.execute(stmt)
            except sqlite3.Error as exc:
                info["rejected"].append((stmt, str(exc)))
        try:
            with db.time_limit(conn):
                cur = conn.execute(exercise["probe_sql"])
                info["headers"] = [d[0] for d in cur.description]
                rows = db.fetch_capped(cur)
        except (db.QueryTimeout, db.TooManyRows, sqlite3.Error) as exc:
            return None, f"probe failed: {exc}", info
        return [tuple(r) for r in rows], None, info
    finally:
        conn.close()


def normalise(rows):
    """Canonical form for comparison: floats rounded, rows sorted, order ignored."""
    out = []
    for row in rows:
        out.append(tuple(
            round(v, 2) if isinstance(v, float) else v
            for v in row
        ))
    # Sort by a string key so mixed types and None never blow up the comparison.
    return sorted(out, key=lambda r: [(v is None, str(v)) for v in r])


CELL_CHARS = 70          # per value in a sample row
SAMPLE_CHARS = 300       # per sample row, after the per-value trim


def brief(row):
    """One sample row, short enough to sit in a one-line status bar.

    A wrong GROUP_CONCAT can hold every value in the table -- 300,000
    characters in a single cell -- so the feedback has to be trimmed at the
    point it is built, not left to whatever displays it.
    """
    parts = []
    for v in row:
        s = repr(v)
        if len(s) > CELL_CHARS:
            s = s[:CELL_CHARS - 4] + "..." + s[-1]
        parts.append(s)
    out = "(" + ", ".join(parts) + ")"
    if len(out) > SAMPLE_CHARS:
        out = out[:SAMPLE_CHARS - 3] + "..."
    return out


def compare(user_rows, expected_rows):
    """Return (passed, message) describing how the two result sets line up."""
    got, want = normalise(user_rows), normalise(expected_rows)

    if got == want:
        return True, f"Correct - {len(want)} row(s) matched."

    if not user_rows:
        return False, f"Your query returned no rows; expected {len(want)}."

    got_cols = len(got[0]) if got else 0
    want_cols = len(want[0]) if want else 0
    if got_cols != want_cols:
        return False, (f"Wrong number of columns: you returned {got_cols}, "
                       f"expected {want_cols}. Check the 'Return:' line in the question.")

    if len(got) != len(want):
        extra = len(got) - len(want)
        direction = f"{extra} too many" if extra > 0 else f"{-extra} too few"
        return False, (f"Wrong number of rows: you returned {len(got)}, "
                       f"expected {len(want)} ({direction}).")

    missing = [r for r in want if r not in got]
    unexpected = [r for r in got if r not in want]
    detail = ""
    if missing:
        detail += f"\n  Expected but missing:  {brief(missing[0])}"
    if unexpected:
        detail += f"\n  Returned but wrong:    {brief(unexpected[0])}"
    return False, (f"Right row count ({len(got)}), but the values differ "
                   f"in {len(missing)} row(s).{detail}")
