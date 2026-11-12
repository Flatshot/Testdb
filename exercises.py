"""Practice exercises: fifteen questions on the parcel-courier schema.

The fourth set on the courier scheme (SEED 1241), two tools per question,
the tiers named by task, on tools the first three courier sets left out,
with prompts that name the tool but do not write the statement. Trails and
runs -- each bike courier's longest run of consecutive delivery days by the
gaps-and-islands trick, a seven-day moving average by a ROWS frame
computed before the filter, a trail packed into one cell by GROUP_CONCAT
with ORDER BY. Depots and regions -- customers who have sent to every
region by relational division, same-region depot pairs by a self-join,
Old Foundry's months with zeros after its closure by a recursive date
spine. Customers and money -- business customers never invoiced by a LEFT
JOIN anti-join, the spend at the ninetieth percentile by CUME_DIST,
money as text by printf with a thousands separator. Weights and days -- a
median by ROW_NUMBER against COUNT, weekend deliveries by AVG of a
comparison on strftime, the couriers with the lowest failure rate by a
ratio with a tiebreak. And three WRITABLE questions:

  * an UPDATE ... FROM that moves a closed depot's customers to the hub
  * an AFTER UPDATE OF trigger that writes a scan when a parcel is delivered
  * an INSERT ... SELECT that bills June

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
    # ====================================================== 1 Trails and runs
    dict(
        id=1, ledger="Q1267", concept="STREAK", tier="1 - Trails and runs",
        title="Each bike courier's longest unbroken run of days",
        prompt=(
            "For each courier on a bike: the most CONSECUTIVE days on"
            " which they delivered at least one parcel. The"
            " gaps-and-islands trick: a CTE of DISTINCT courier-and-day"
            " pairs, a group key made by subtracting each day's row"
            " number (within the courier) from the day, so a run of"
            " consecutive days shares one key; count per key, MAX per"
            " courier.\n\n"
            "Return: name, longest_run"
        ),
        solution=("WITH d AS (SELECT DISTINCT courier_id, date(delivered_at) AS day FROM parcels WHERE courier_id IS NOT NULL),"
                  " g AS (SELECT courier_id, date(day, '-' || ROW_NUMBER() OVER (PARTITION BY courier_id ORDER BY day) || ' days') AS grp FROM d),"
                  " s AS (SELECT courier_id, COUNT(*) AS len FROM g GROUP BY courier_id, grp)"
                  " SELECT c.name, MAX(s.len) FROM s JOIN couriers c ON c.courier_id = s.courier_id WHERE c.vehicle = 'bike' GROUP BY c.courier_id"),
        trap_sql=("WITH d AS (SELECT courier_id, date(delivered_at) AS day FROM parcels WHERE courier_id IS NOT NULL),"
                  " g AS (SELECT courier_id, date(day, '-' || ROW_NUMBER() OVER (PARTITION BY courier_id ORDER BY day) || ' days') AS grp FROM d),"
                  " s AS (SELECT courier_id, COUNT(*) AS len FROM g GROUP BY courier_id, grp)"
                  " SELECT c.name, MAX(s.len) FROM s JOIN couriers c ON c.courier_id = s.courier_id WHERE c.vehicle = 'bike' GROUP BY c.courier_id"),
        note="Subtract a row number from a run of consecutive dates and"
             " every date in the run gives the same result -- that shared"
             " value is the island's key. It only works on one row per"
             " day: with two deliveries on one day the row numbers jump"
             " twice while the date does not, the keys drift, and the"
             " trap's runs come out too long. DISTINCT in the first CTE"
             " is the whole difference. The best bike courier managed"
             " twenty days in a row.",
        claims=[("nineteen bike couriers, the best run twenty days",
                 lambda rows, c: len(rows) == 19 and max(r[1] for r in rows) == 20),
                ("Farouk Baxter holds it",
                 lambda rows, c: ("Farouk Baxter", 20) in rows)],
    ),
    dict(
        id=2, ledger="Q1268", concept="MA7", tier="1 - Trails and runs",
        title="A week's collections, rolling",
        prompt=(
            "For each day of June 2026: the parcels collected that day,"
            " and the average over that day and the six before it, to"
            " one decimal. Count per day in a CTE, a window AVG with a"
            " ROWS frame reaching six rows back, and the June filter"
            " applied AFTER the window -- 1 June's week reaches into"
            " May.\n\n"
            "Return: day, parcels, rolling_avg"
        ),
        solution=("WITH d AS (SELECT date(collected_at) AS day, COUNT(*) AS n FROM parcels GROUP BY day),"
                  " w AS (SELECT day, n, ROUND(AVG(n) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 1) AS ma FROM d)"
                  " SELECT day, n, ma FROM w WHERE day >= '2026-06-01'"),
        trap_sql=("WITH d AS (SELECT date(collected_at) AS day, COUNT(*) AS n FROM parcels WHERE collected_at >= '2026-06-01' GROUP BY day)"
                  " SELECT day, n, ROUND(AVG(n) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 1) FROM d"),
        note="ROWS BETWEEN 6 PRECEDING AND CURRENT ROW is a frame of"
             " seven rows, and since every day has a collection, seven"
             " rows is seven days. Window functions run after WHERE, so"
             " the trap's filter removes May before the window looks"
             " for it and the first six averages are over too few days"
             " -- 1 June averages only itself. Filter in the outer query"
             " and the frame can see back into May.",
        claims=[("thirty days, 1 June's average 46.4",
                 lambda rows, c: len(rows) == 30 and ("2026-06-01", 41, 46.4) in rows),
                ("every rolling average between 40 and 60",
                 lambda rows, c: all(40 <= r[2] <= 60 for r in rows))],
    ),
    dict(
        id=3, ledger="Q1269", concept="GC", tier="1 - Trails and runs",
        title="A troubled trail in one line",
        prompt=(
            "For parcels 40, 44, 67, 71 and 72 -- the first five that"
            " failed an attempt: the whole trail as ONE text cell, the"
            " statuses in time order joined by ' > '. GROUP_CONCAT with"
            " its own separator and its own ORDER BY; a status that"
            " appears twice must appear twice.\n\n"
            "Return: parcel_id, trail"
        ),
        solution=("SELECT parcel_id, GROUP_CONCAT(status, ' > ' ORDER BY scanned_at) FROM scans"
                  " WHERE parcel_id IN (40, 44, 67, 71, 72) GROUP BY parcel_id"),
        trap_sql=("SELECT parcel_id, GROUP_CONCAT(DISTINCT status) FROM scans"
                  " WHERE parcel_id IN (40, 44, 67, 71, 72) GROUP BY parcel_id"),
        note="GROUP_CONCAT builds one string from a group, with the"
             " separator between items, and since SQLite 3.44 it takes"
             " an ORDER BY inside the brackets so the order is fixed. The"
             " trap's DISTINCT removes the repeats -- parcel 44's two"
             " failed attempts become one -- and loses the separator too."
             " Parcel 40 is a lost one: its trail ends on the failure.",
        claims=[("five trails, parcel 40 ending on a failure",
                 lambda rows, c: len(rows) == 5 and any(r[0] == 40 and r[1].endswith("failed") for r in rows)),
                ("parcel 44 failed twice",
                 lambda rows, c: any(r[0] == 44 and r[1].count("failed") == 2 for r in rows))],
    ),
    # =================================================== 2 Depots and regions
    dict(
        id=4, ledger="Q1270", concept="DIV", tier="2 - Depots and regions",
        title="Customers who have sent to every region",
        prompt=(
            "For each kind of customer: how many have sent parcels to"
            " EVERY one of the five regions. Relational division: per"
            " customer, the number of DIFFERENT destination regions,"
            " compared with the number of regions there are; then a"
            " count per kind.\n\n"
            "Return: kind, everywhere"
        ),
        solution=("SELECT c.kind, COUNT(*) FROM customers c"
                  " WHERE (SELECT COUNT(DISTINCT d.region) FROM parcels p JOIN depots d ON d.depot_id = p.dest_depot_id WHERE p.customer_id = c.customer_id)"
                  " = (SELECT COUNT(DISTINCT region) FROM depots) GROUP BY c.kind"),
        trap_sql=("SELECT c.kind, COUNT(*) FROM customers c"
                  " WHERE (SELECT COUNT(DISTINCT d.region) FROM parcels p JOIN depots d ON d.depot_id = p.dest_depot_id WHERE p.customer_id = c.customer_id)"
                  " >= 1 GROUP BY c.kind"),
        note="'Every region' is a count compared with a count: the"
             " distinct regions a customer has reached against the"
             " regions that exist. 'Some region', the trap, is anyone who"
             " has sent anything -- 620 customers. Five regions is not"
             " many to cover: 509 customers have, and only nine have"
             " stuck to three.",
        claims=[("two kinds, 509 customers in all",
                 lambda rows, c: len(rows) == 2 and sum(r[1] for r in rows) == 509),
                ("196 of them businesses",
                 lambda rows, c: ("business", 196) in rows)],
    ),
    dict(
        id=5, ledger="Q1271", concept="SELF", tier="2 - Depots and regions",
        title="Neighbours in the same region",
        prompt=(
            "Every pair of depots that share a region, each pair once"
            " with the lower depot_id first, and the parcels that"
            " travelled between them in EITHER direction. A self-join of"
            " depots on region with a strict inequality on the ids, and"
            " a count of the parcels whose two depots are the pair,"
            " either way round.\n\n"
            "Return: depot_a, depot_b, between"
        ),
        solution=("SELECT a.name, b.name,"
                  " (SELECT COUNT(*) FROM parcels p WHERE (p.origin_depot_id = a.depot_id AND p.dest_depot_id = b.depot_id)"
                  " OR (p.origin_depot_id = b.depot_id AND p.dest_depot_id = a.depot_id))"
                  " FROM depots a JOIN depots b ON b.region = a.region AND a.depot_id < b.depot_id"),
        trap_sql=("SELECT a.name, b.name,"
                  " (SELECT COUNT(*) FROM parcels p WHERE (p.origin_depot_id = a.depot_id AND p.dest_depot_id = b.depot_id)"
                  " OR (p.origin_depot_id = b.depot_id AND p.dest_depot_id = a.depot_id))"
                  " FROM depots a JOIN depots b ON b.region = a.region AND a.depot_id <> b.depot_id"),
        note="A self-join on region pairs each depot with the others in"
             " its region; < keeps each pair once, <> keeps both"
             " orderings and the trap returns ten rows for five pairs."
             " The subquery counts the pair's traffic in both directions"
             " with an OR of the two orderings. Every region has exactly"
             " two depots, so there are exactly five pairs; Southfield"
             " and Millbank exchange the most.",
        claims=[("five pairs, Southfield and Millbank the busiest",
                 lambda rows, c: len(rows) == 5 and max(rows, key=lambda r: r[2]) == ("Southfield", "Millbank", 547)),
                ("lower id first in every pair",
                 lambda rows, c: all(c.execute("SELECT depot_id FROM depots WHERE name = ?", (r[0],)).fetchone()[0] < c.execute("SELECT depot_id FROM depots WHERE name = ?", (r[1],)).fetchone()[0] for r in rows))],
    ),
    dict(
        id=6, ledger="Q1272", concept="SPINE", tier="2 - Depots and regions",
        title="Old Foundry, month by month, to the end",
        prompt=(
            "Old Foundry's collections for every month from January"
            " 2025 to June 2026 -- eighteen rows, with 0 for the months"
            " after it closed. Generate the months with a recursive CTE"
            " that adds a month each step, then LEFT JOIN the depot's"
            " parcels onto them.\n\n"
            "Return: month, parcels"
        ),
        solution=("WITH RECURSIVE m(mo) AS (SELECT '2025-01' UNION ALL SELECT strftime('%Y-%m', date(mo || '-01', '+1 month')) FROM m WHERE mo < '2026-06')"
                  " SELECT m.mo, COUNT(p.parcel_id) FROM m LEFT JOIN parcels p ON p.origin_depot_id = 2 AND strftime('%Y-%m', p.collected_at) = m.mo GROUP BY m.mo"),
        trap_sql=("SELECT strftime('%Y-%m', collected_at), COUNT(*) FROM parcels WHERE origin_depot_id = 2 GROUP BY 1"),
        note="A GROUP BY over the parcels can only report the months"
             " that have parcels, so the trap stops at January 2026 with"
             " thirteen rows and the closure is invisible. The recursive"
             " CTE manufactures the eighteen months from nothing -- an"
             " anchor row and a step that adds a month until the stop --"
             " and the LEFT JOIN hangs the parcels on them, leaving the"
             " five closed months at zero. Note the depot condition sits"
             " in ON, not WHERE.",
        claims=[("eighteen months, five of them zero",
                 lambda rows, c: len(rows) == 18 and sum(r[1] == 0 for r in rows) == 5),
                ("the zeros are February 2026 onwards",
                 lambda rows, c: all(r[0] >= "2026-02" for r in rows if r[1] == 0))],
    ),
    # ================================================ 3 Customers and money
    dict(
        id=7, ledger="Q1273", concept="ANTI", tier="3 - Customers and money",
        title="Businesses that have never been billed",
        prompt=(
            "Every business customer with no invoice at all: name, date"
            " joined, and how many parcels they have sent. An anti-join"
            " with LEFT JOIN: join invoices and keep the customers whose"
            " side of the join came back empty. The parcel count is a"
            " separate scalar subquery.\n\n"
            "Return: name, joined_on, parcels"
        ),
        solution=("SELECT c.name, c.joined_on, (SELECT COUNT(*) FROM parcels p WHERE p.customer_id = c.customer_id)"
                  " FROM customers c LEFT JOIN invoices i ON i.customer_id = c.customer_id"
                  " WHERE c.kind = 'business' AND i.invoice_id IS NULL"),
        trap_sql=("SELECT c.name, c.joined_on, (SELECT COUNT(*) FROM parcels p WHERE p.customer_id = c.customer_id)"
                  " FROM customers c LEFT JOIN invoices i ON i.customer_id = c.customer_id AND i.invoice_id IS NULL"
                  " WHERE c.kind = 'business'"),
        note="A LEFT JOIN with WHERE right-side IS NULL keeps exactly the"
             " rows that found no match -- the anti-join. Put the IS NULL"
             " in ON instead, the trap, and it is a join condition that"
             " no invoice can meet, so every business comes back"
             " unmatched and all 247 appear. Twenty-four businesses have"
             " never been billed: twenty-two never sent, and two joined"
             " in June 2026, whose first bill is not out yet.",
        claims=[("24 businesses, 22 of them never sent",
                 lambda rows, c: len(rows) == 24 and sum(r[2] == 0 for r in rows) == 22),
                ("the two who did send joined in June 2026",
                 lambda rows, c: all(r[1] >= "2026-06-01" for r in rows if r[2] > 0))],
    ),
    dict(
        id=8, ledger="Q1274", concept="DST", tier="3 - Customers and money",
        title="What it takes to be a top-ten-per-cent sender",
        prompt=(
            "For each kind of customer: the senders, the postage total"
            " that puts a customer in the top ten per cent of that"
            " kind's senders, and the kind's maximum. A CTE of postage"
            " per customer, CUME_DIST over it partitioned by kind in"
            " ascending order, then the smallest total whose CUME_DIST"
            " is at least 0.9 -- MIN with a FILTER -- and MAX.\n\n"
            "Return: kind, senders, top_decile_cents, max_cents"
        ),
        solution=("WITH s AS (SELECT c.kind, c.customer_id, SUM(p.postage_cents) AS spent FROM parcels p JOIN customers c ON c.customer_id = p.customer_id GROUP BY c.customer_id),"
                  " d AS (SELECT kind, spent, CUME_DIST() OVER (PARTITION BY kind ORDER BY spent) AS cd FROM s)"
                  " SELECT kind, COUNT(*), MIN(spent) FILTER (WHERE cd >= 0.9), MAX(spent) FROM d GROUP BY kind"),
        trap_sql=("WITH s AS (SELECT c.kind, c.customer_id, SUM(p.postage_cents) AS spent FROM parcels p JOIN customers c ON c.customer_id = p.customer_id GROUP BY c.customer_id),"
                  " d AS (SELECT kind, spent, CUME_DIST() OVER (PARTITION BY kind ORDER BY spent DESC) AS cd FROM s)"
                  " SELECT kind, COUNT(*), MIN(spent) FILTER (WHERE cd >= 0.9), MAX(spent) FROM d GROUP BY kind"),
        note="CUME_DIST is the share of the partition at or below the"
             " row in the window's order, so ascending puts the big"
             " spenders at 0.9 and above. Ordered descending, the trap,"
             " 0.9 is reached by the SMALLEST spenders and the threshold"
             " collapses to a few dollars. A business needs about 1,876"
             " dollars of postage to be in its top tenth; a person about"
             " 183.",
        claims=[("two kinds, 225 business senders",
                 lambda rows, c: len(rows) == 2 and ("business", 225, 187570, 230910) in rows),
                ("the threshold below the maximum on both",
                 lambda rows, c: all(r[2] < r[3] for r in rows))],
    ),
    dict(
        id=9, ledger="Q1275", concept="FMT", tier="3 - Customers and money",
        title="Invoiced money, printed as money",
        prompt=(
            "For every depot, of the customer's home: the invoice money"
            " issued, as TEXT the way an accountant writes it -- a"
            " dollar sign, thousands separated by commas, two decimals:"
            " '$8,574.70'. printf has a flag for the separator.\n\n"
            "Return: name, invoiced"
        ),
        solution=("SELECT d.name, printf('$%,.2f', SUM(i.amount_cents) / 100.0)"
                  " FROM invoices i JOIN customers c ON c.customer_id = i.customer_id JOIN depots d ON d.depot_id = c.depot_id GROUP BY d.name"),
        trap_sql=("SELECT d.name, printf('$%.2f', SUM(i.amount_cents) / 100.0)"
                  " FROM invoices i JOIN customers c ON c.customer_id = i.customer_id JOIN depots d ON d.depot_id = c.depot_id GROUP BY d.name"),
        note="printf('%,.2f') is a floating-point conversion with the"
             " comma flag, which groups the thousands; without the flag,"
             " the trap, the number is right but reads '$8574.70'. The"
             " division by 100.0 has to be real, or the cents are lost"
             " before printf sees them. Formatting belongs at the edge:"
             " the sums stay as cents everywhere else.",
        claims=[("ten depots, Central Hub at $8,574.70",
                 lambda rows, c: len(rows) == 10 and ("Central Hub", "$8,574.70") in rows),
                ("every value starts with a dollar sign and has a comma",
                 lambda rows, c: all(r[1].startswith("$") and "," in r[1] for r in rows))],
    ),
    # ==================================================== 4 Weights and days
    dict(
        id=10, ledger="Q1276", concept="MED", tier="4 - Weights and days",
        title="The middle parcel of each service",
        prompt=(
            "For each service: the MEDIAN weight in grams. No MEDIAN"
            " function: number each service's parcels by weight with"
            " ROW_NUMBER and count them with COUNT(*) OVER, both"
            " partitioned by service, in a CTE; keep the rows numbered"
            " (n + 1) / 2 and (n + 2) / 2 -- one row when n is odd, the"
            " two middle rows when it is even -- and AVG them.\n\n"
            "Return: service, median_g"
        ),
        solution=("WITH r AS (SELECT service, weight_g, ROW_NUMBER() OVER (PARTITION BY service ORDER BY weight_g) AS rn,"
                  " COUNT(*) OVER (PARTITION BY service) AS n FROM parcels)"
                  " SELECT service, AVG(weight_g) FROM r WHERE rn IN ((n + 1) / 2, (n + 2) / 2) GROUP BY service"),
        trap_sql="SELECT service, AVG(weight_g) FROM parcels GROUP BY service",
        note="The mean is pulled up by the heavy tail: economy's mean is"
             " 2,243 grams but its median 1,532, so half of all economy"
             " parcels weigh under a kilo and a half. (n + 1) / 2 and"
             " (n + 2) / 2 are integer divisions, which is what lands them"
             " on the middle row for odd n and the two middle rows for"
             " even n. The three services weigh much the same; people"
             " choose speed, not size.",
        claims=[("three services, economy's median 1532",
                 lambda rows, c: len(rows) == 3 and ("economy", 1532.0) in rows),
                ("every median below its mean",
                 lambda rows, c: all(r[1] < c.execute("SELECT AVG(weight_g) FROM parcels WHERE service = ?", (r[0],)).fetchone()[0] for r in rows))],
    ),
    dict(
        id=11, ledger="Q1277", concept="WKND", tier="4 - Weights and days",
        title="Weekend deliveries, by vehicle",
        prompt=(
            "For each vehicle type: its deliveries, how many were made"
            " on a Saturday or Sunday, and that as a percentage to one"
            " decimal. The day of the week comes from strftime on the"
            " DELIVERY timestamp, '0' for Sunday to '6' for Saturday;"
            " the average of a true-or-false test is a share.\n\n"
            "Return: vehicle, deliveries, weekend, weekend_pct"
        ),
        solution=("SELECT c.vehicle, COUNT(*), SUM(strftime('%w', p.delivered_at) IN ('0', '6')),"
                  " ROUND(100.0 * AVG(strftime('%w', p.delivered_at) IN ('0', '6')), 1)"
                  " FROM parcels p JOIN couriers c ON c.courier_id = p.courier_id GROUP BY c.vehicle"),
        trap_sql=("SELECT c.vehicle, COUNT(*), SUM(strftime('%w', p.collected_at) IN ('0', '6')),"
                  " ROUND(100.0 * AVG(strftime('%w', p.collected_at) IN ('0', '6')), 1)"
                  " FROM parcels p JOIN couriers c ON c.courier_id = p.courier_id GROUP BY c.vehicle"),
        note="%w gives the weekday as a text digit, Sunday first, so the"
             " weekend is IN ('0', '6') -- quoted, because it is text."
             " The trap asks the question of the COLLECTION date, which"
             " is the customer's weekend, not the courier's. Two days in"
             " seven is 28.6 per cent, and deliveries land within a point"
             " of it: the depots work seven days.",
        claims=[("three vehicles, each between 27 and 30 per cent",
                 lambda rows, c: len(rows) == 3 and all(27 <= r[3] <= 30 for r in rows)),
                ("23729 deliveries in all",
                 lambda rows, c: sum(r[1] for r in rows) == 23729)],
    ),
    dict(
        id=12, ledger="Q1278", concept="RATE", tier="4 - Weights and days",
        title="The couriers whose attempts most often succeed",
        prompt=(
            "The five couriers with the LOWEST failure rate: name,"
            " vehicle, attempts ('out_for_delivery' scans), failures"
            " ('failed' scans), and the failures as a percentage of the"
            " attempts to one decimal. Two conditional sums per courier,"
            " a ratio of them, ORDER BY the rate then courier_id, LIMIT"
            " 5.\n\n"
            "Return: name, vehicle, attempts, failures, fail_pct"
        ),
        solution=("SELECT c.name, c.vehicle, SUM(s.status = 'out_for_delivery'), SUM(s.status = 'failed'),"
                  " ROUND(100.0 * SUM(s.status = 'failed') / SUM(s.status = 'out_for_delivery'), 1)"
                  " FROM scans s JOIN couriers c ON c.courier_id = s.courier_id GROUP BY c.courier_id"
                  " ORDER BY ROUND(100.0 * SUM(s.status = 'failed') / SUM(s.status = 'out_for_delivery'), 1), c.courier_id LIMIT 5"),
        trap_sql=("SELECT c.name, c.vehicle, SUM(s.status = 'out_for_delivery'), SUM(s.status = 'failed'),"
                  " ROUND(100.0 * SUM(s.status = 'failed') / SUM(s.status = 'delivered'), 1)"
                  " FROM scans s JOIN couriers c ON c.courier_id = s.courier_id GROUP BY c.courier_id"
                  " ORDER BY ROUND(100.0 * SUM(s.status = 'failed') / SUM(s.status = 'delivered'), 1), c.courier_id LIMIT 5"),
        note="A rate needs the right denominator: failures over ATTEMPTS"
             " is the share of attempts that failed, which is what the"
             " question asks. Failures over deliveries, the trap, is a"
             " different ratio -- bigger, since a courier has fewer"
             " deliveries than attempts -- and it reorders the list. Two"
             " conditional sums from one scan of the scans table give"
             " both counts at once. Every courier fails about one"
             " attempt in ten; the best fail one in eleven or twelve.",
        claims=[("five couriers, Kwame Tremblay first at 8.7",
                 lambda rows, c: len(rows) == 5 and ("Kwame Tremblay", "van", 173, 15, 8.7) in rows),
                ("every rate under 10.1 per cent",
                 lambda rows, c: all(r[4] <= 10.0 for r in rows))],
    ),
    # =================================================== 5 Changing the data
    dict(
        id=13, ledger="Q1279", concept="UPDFROM", tier="5 - Changing the data",
        kind="script",
        title="A closed depot's customers move to the hub",
        prompt=(
            "Every customer whose home depot has closed should now"
            " belong to Central Hub, depot 1. ONE UPDATE of customers"
            " that joins depots into it -- UPDATE ... FROM -- so that"
            " the test on closed_on can be written against the depot"
            " row rather than a subquery.\n\n"
            "Checked: how many customers belong to depot 1, how many to"
            " depot 2, and how many there are"
        ),
        solution=("UPDATE customers SET depot_id = 1 FROM depots d"
                  " WHERE customers.depot_id = d.depot_id AND d.closed_on IS NOT NULL;"),
        trap_sql=("UPDATE customers SET depot_id = 1 FROM depots d"
                  " WHERE customers.depot_id = d.depot_id;"),
        probe_sql="SELECT SUM(depot_id = 1), SUM(depot_id = 2), COUNT(*) FROM customers",
        note="UPDATE ... FROM (SQLite 3.33 and later) is a join inside an"
             " UPDATE: the FROM table's columns are available in WHERE and"
             " in SET. The trap joins the depots and forgets to ask"
             " whether they are closed, so every customer in the city"
             " moves to the hub. Old Foundry's 53 customers join Central"
             " Hub's 73; the depot itself stays in the table, with its"
             " history.",
        claims=[("126 customers at the hub, none left at Old Foundry",
                 lambda rows, c: rows == [(126, 0, 700)])],
    ),
    dict(
        id=14, ledger="Q1280", concept="UPDTRG", tier="5 - Changing the data",
        kind="script",
        title="Marking a parcel delivered writes its last scan",
        prompt=(
            "When a parcel's delivered_at is set -- changed from NULL to"
            " a time -- a 'delivered' scan should appear in its trail:"
            " at the destination depot, by the parcel's courier, at"
            " that time. Write an AFTER UPDATE trigger on parcels that"
            " fires only for that column and only for that change (a"
            " WHEN clause with OLD and NEW). The question then marks"
            " parcel 40 delivered and changes parcel 41's postage.\n\n"
            "Checked: parcel 40's delivered scans, any scan for parcel"
            " 41 dated July, and the total number of scans"
        ),
        solution=("CREATE TRIGGER scan_on_delivery AFTER UPDATE OF delivered_at ON parcels\n"
                  "WHEN NEW.delivered_at IS NOT NULL AND OLD.delivered_at IS NULL\n"
                  "BEGIN\n"
                  "  INSERT INTO scans (parcel_id, depot_id, courier_id, scanned_at, status)\n"
                  "  VALUES (NEW.parcel_id, NEW.dest_depot_id, NEW.courier_id, NEW.delivered_at, 'delivered');\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER scan_on_delivery AFTER UPDATE ON parcels\n"
                  "BEGIN\n"
                  "  INSERT INTO scans (parcel_id, depot_id, courier_id, scanned_at, status)\n"
                  "  VALUES (NEW.parcel_id, NEW.dest_depot_id, NEW.courier_id, COALESCE(NEW.delivered_at, '2026-07-01 00:00'), 'delivered');\n"
                  "END;"),
        driver_sql=("UPDATE parcels SET delivered_at = '2026-07-01 10:00', courier_id = 7 WHERE parcel_id = 40;\n"
                    "UPDATE parcels SET postage_cents = postage_cents + 100 WHERE parcel_id = 41;"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM scans WHERE parcel_id = 40 AND status = 'delivered'),"
                   " (SELECT COUNT(*) FROM scans WHERE parcel_id = 41 AND scanned_at >= '2026-07-01'),"
                   " (SELECT COUNT(*) FROM scans)"),
        note="AFTER UPDATE OF column narrows a trigger to changes of one"
             " column, and the WHEN clause narrows it further: OLD and"
             " NEW are the row before and after, so 'NULL became a time'"
             " is a condition the trigger can test. The trap fires on"
             " every update of any column and writes a bogus delivered"
             " scan when parcel 41's postage changes. This is the mirror"
             " of the first set's trigger, which went from scan to"
             " parcel.",
        claims=[("one scan for 40, none for 41",
                 lambda rows, c: rows == [(1, 0, 112379)])],
    ),
    dict(
        id=15, ledger="Q1281", concept="INSSEL", tier="5 - Changing the data",
        kind="script",
        title="Billing June",
        prompt=(
            "Issue June 2026's invoices: one per BUSINESS customer who"
            " sent a parcel in June, for the period '2026-06', issued"
            " on 2026-07-01, for the sum of their June postage. ONE"
            " INSERT whose rows come from a SELECT with a GROUP BY.\n\n"
            "Checked: how many June invoices there are, their amounts"
            " added up, and the earliest issue date"
        ),
        solution=("INSERT INTO invoices (customer_id, period, amount_cents, issued_on)"
                  " SELECT c.customer_id, '2026-06', SUM(p.postage_cents), '2026-07-01'"
                  " FROM parcels p JOIN customers c ON c.customer_id = p.customer_id"
                  " WHERE c.kind = 'business' AND p.collected_at >= '2026-06-01' GROUP BY c.customer_id;"),
        trap_sql=("INSERT INTO invoices (customer_id, period, amount_cents, issued_on)"
                  " SELECT c.customer_id, '2026-06', SUM(p.postage_cents), '2026-07-01'"
                  " FROM parcels p JOIN customers c ON c.customer_id = p.customer_id"
                  " WHERE p.collected_at >= '2026-06-01' GROUP BY c.customer_id;"),
        probe_sql="SELECT COUNT(*), SUM(amount_cents), MIN(issued_on) FROM invoices WHERE period = '2026-06'",
        note="INSERT ... SELECT writes one row per row the SELECT"
             " returns, and a GROUP BY makes that one per customer with"
             " the month's postage summed; literals supply the columns"
             " that are the same on every row. The trap bills everyone"
             " who sent in June, 424 customers, when only businesses are"
             " invoiced -- people pay at the counter. The UNIQUE"
             " (customer_id, period) constraint would refuse a second"
             " run.",
        claims=[("163 invoices for 458,560 cents",
                 lambda rows, c: rows == [(163, 458560, "2026-07-01")])],
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
