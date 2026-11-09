"""Practice exercises: fifteen questions on the parcel-courier schema.

The first set on the courier scheme (SEED 1241), two tools per question,
the tiers named by task, with prompts that name the tool but do not write
the statement. The parcel's trail -- each scan's place in its parcel's
story by ROW_NUMBER partitioned, transit times by julianday with a share
inside 48 hours, parcels that suffered a failed attempt by EXISTS where a
join would count attempts. Depots and routes -- the busiest routes by a
two-column GROUP BY with two aliases of depots, parcels in against out by
scalar subqueries, Old Foundry's customers rerouted by conditional sums
across its closure. Customers and money -- walk-in parcels as a NULL
category, the customers owing most by HAVING-free aggregation over a
filtered join, the postage table recovered by integer arithmetic on
weight. People and time -- deliveries per working day by COUNT DISTINCT
of a date, collections by weekday name through CASE on strftime, month on
month by LAG. And three WRITABLE questions:

  * a trigger with a WHEN clause that completes a parcel on its delivery scan
  * an UPDATE adding a surcharge to a slice of the parcels
  * a DELETE of the customers who never sent, where NOT IN meets a NULL

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
    # =================================================== 1 The parcel's trail
    dict(
        id=1, ledger="Q1222", concept="SEQ", tier="1 - The parcel's trail",
        title="Each parcel's trail, step by step",
        prompt=(
            "For parcels 1 to 5: every scan, numbered from 1 within its"
            " own parcel in time order, with the status and the time."
            " A window numbering function partitioned by parcel.\n\n"
            "Return: parcel_id, step, status, scanned_at"
        ),
        solution=("SELECT parcel_id, ROW_NUMBER() OVER (PARTITION BY parcel_id ORDER BY scanned_at), status, scanned_at"
                  " FROM scans WHERE parcel_id <= 5"),
        trap_sql=("SELECT parcel_id, ROW_NUMBER() OVER (ORDER BY scanned_at), status, scanned_at"
                  " FROM scans WHERE parcel_id <= 5"),
        note="PARTITION BY restarts the numbering for each parcel, so"
             " every trail begins at step 1; without it the trap numbers"
             " all 23 scans in one run and parcel 2's trail starts at"
             " step 6. The trail is the schema's ordered sequence inside"
             " a parent: collected, departed, arrived, out for delivery,"
             " delivered -- and a local parcel, which never departs, has"
             " three steps instead of five.",
        claims=[("23 scans, every trail starting at 1",
                 lambda rows, c: len(rows) == 23 and all(any(r[0] == p and r[1] == 1 for r in rows) for p in range(1, 6))),
                ("parcel 3's trail is three steps",
                 lambda rows, c: max(r[1] for r in rows if r[0] == 3) == 3)],
    ),
    dict(
        id=2, ledger="Q1223", concept="TRANSIT", tier="1 - The parcel's trail",
        title="How long each service really takes",
        prompt=(
            "For each service: the delivered parcels, the average hours"
            " from collection to delivery to one decimal, and the share"
            " delivered within 48 hours as a percentage to one decimal."
            " julianday differences are in DAYS; the average of a"
            " true-or-false comparison is a share.\n\n"
            "Return: service, delivered, avg_hours, within_48h_pct"
        ),
        solution=("SELECT service, COUNT(*), ROUND(AVG((julianday(delivered_at) - julianday(collected_at)) * 24), 1),"
                  " ROUND(100.0 * AVG((julianday(delivered_at) - julianday(collected_at)) * 24 <= 48), 1)"
                  " FROM parcels WHERE delivered_at IS NOT NULL GROUP BY service"),
        trap_sql=("SELECT service, COUNT(*), ROUND(AVG((julianday(delivered_at) - julianday(collected_at)) * 24), 1),"
                  " ROUND(100.0 * AVG(julianday(delivered_at) - julianday(collected_at) <= 48), 1)"
                  " FROM parcels WHERE delivered_at IS NOT NULL GROUP BY service"),
        note="julianday(b) - julianday(a) is a number of days, so hours"
             " need * 24 on both sides of the question: the trap compares"
             " DAYS with 48 and finds every parcel inside it. AVG of a"
             " comparison is the share of rows where it holds, because"
             " true is 1 and false is 0. Express is the only service that"
             " gets more than half its parcels there within two days, and"
             " its average is still just under 44 hours.",
        claims=[("three services, express the fastest",
                 lambda rows, c: len(rows) == 3 and min(rows, key=lambda r: r[2])[0] == "express"),
                ("only express mostly within 48 hours",
                 lambda rows, c: all((r[3] > 50) == (r[0] == "express") for r in rows))],
    ),
    dict(
        id=3, ledger="Q1224", concept="FAILED", tier="1 - The parcel's trail",
        title="Parcels that came back to the depot",
        prompt=(
            "For each service: its parcels, how many of them have a"
            " failed delivery attempt somewhere in their trail, and that"
            " as a percentage to one decimal. A parcel with two failed"
            " attempts counts once, which a join to scans would not"
            " do; EXISTS does.\n\n"
            "Return: service, parcels, with_failure, pct"
        ),
        solution=("SELECT p.service, COUNT(*),"
                  " SUM(EXISTS (SELECT 1 FROM scans s WHERE s.parcel_id = p.parcel_id AND s.status = 'failed')),"
                  " ROUND(100.0 * SUM(EXISTS (SELECT 1 FROM scans s WHERE s.parcel_id = p.parcel_id AND s.status = 'failed')) / COUNT(*), 1)"
                  " FROM parcels p GROUP BY p.service"),
        trap_sql=("SELECT p.service, COUNT(DISTINCT p.parcel_id), COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / COUNT(DISTINCT p.parcel_id), 1)"
                  " FROM parcels p JOIN scans s ON s.parcel_id = p.parcel_id AND s.status = 'failed' GROUP BY p.service"),
        note="EXISTS asks a yes-or-no question per parcel and is 1 or 0,"
             " so SUM of it counts parcels, however many failed scans"
             " each has. The trap joins the failed scans and counts rows:"
             " 72 parcels failed twice, so it reports attempts, not"
             " parcels, and its first column is only the parcels that"
             " failed at all. One parcel in seven comes back to the"
             " depot at least once, on every service alike.",
        claims=[("three services, each near 14 per cent",
                 lambda rows, c: len(rows) == 3 and all(13 <= r[3] <= 15 for r in rows)),
                ("3345 parcels with a failure",
                 lambda rows, c: sum(r[2] for r in rows) == 3345)],
    ),
    # =================================================== 2 Depots and routes
    dict(
        id=4, ledger="Q1225", concept="ROUTES", tier="2 - Depots and routes",
        title="The ten busiest routes between depots",
        prompt=(
            "The ten depot-to-depot routes with the most parcels, by"
            " name, leaving out the local parcels that stay at one"
            " depot. Join depots twice, once for each end; group by"
            " the pair; order by the count, then by the two names so a"
            " tie cannot shuffle the list.\n\n"
            "Return: from_depot, to_depot, parcels"
        ),
        solution=("SELECT a.name, b.name, COUNT(*) FROM parcels p"
                  " JOIN depots a ON a.depot_id = p.origin_depot_id JOIN depots b ON b.depot_id = p.dest_depot_id"
                  " WHERE p.origin_depot_id <> p.dest_depot_id GROUP BY a.name, b.name"
                  " ORDER BY COUNT(*) DESC, a.name, b.name LIMIT 10"),
        trap_sql=("SELECT a.name, b.name, COUNT(*) FROM parcels p"
                  " JOIN depots a ON a.depot_id = p.origin_depot_id JOIN depots b ON b.depot_id = p.dest_depot_id"
                  " GROUP BY a.name, b.name ORDER BY COUNT(*) DESC, a.name, b.name LIMIT 10"),
        note="Joining the same table twice with two aliases is how one"
             " row's two foreign keys to depots both get a name. Local"
             " parcels -- the same depot at both ends -- are a fifth of"
             " the traffic, and the trap's top ten is nine of them;"
             " WHERE origin <> dest keeps the routes that actually move."
             " Millbank sends a lot: six of the ten busiest routes start"
             " there.",
        claims=[("ten routes, Millbank to Central Hub the busiest",
                 lambda rows, c: len(rows) == 10 and max(rows, key=lambda r: r[2]) == ("Millbank", "Central Hub", 327)),
                ("no local route among them",
                 lambda rows, c: all(r[0] != r[1] for r in rows))],
    ),
    dict(
        id=5, ledger="Q1226", concept="FLOW", tier="2 - Depots and routes",
        title="Parcels in against parcels out, at every depot",
        prompt=(
            "For every depot: the parcels collected there, the parcels"
            " delivered to it, and the difference (in minus out). Two"
            " counts of the same table on two different keys -- scalar"
            " subqueries, or two conditional sums; joining parcels"
            " twice would multiply.\n\n"
            "Return: name, sent, received, net"
        ),
        solution=("SELECT d.name, (SELECT COUNT(*) FROM parcels WHERE origin_depot_id = d.depot_id),"
                  " (SELECT COUNT(*) FROM parcels WHERE dest_depot_id = d.depot_id),"
                  " (SELECT COUNT(*) FROM parcels WHERE dest_depot_id = d.depot_id) - (SELECT COUNT(*) FROM parcels WHERE origin_depot_id = d.depot_id)"
                  " FROM depots d"),
        trap_sql=("SELECT d.name, COUNT(o.parcel_id), COUNT(i.parcel_id), COUNT(i.parcel_id) - COUNT(o.parcel_id)"
                  " FROM depots d LEFT JOIN parcels o ON o.origin_depot_id = d.depot_id LEFT JOIN parcels i ON i.dest_depot_id = d.depot_id"
                  " GROUP BY d.name"),
        note="A depot is referenced by two columns of parcels, and"
             " counting each is a separate question. Two scalar"
             " subqueries ask them separately; the trap joins parcels"
             " twice onto depots and every sent parcel meets every"
             " received one, so the counts come out in the millions. The"
             " depots that send more than they receive -- Millbank,"
             " Southfield, Central Hub -- are the ones with the business"
             " customers.",
        claims=[("ten depots, Millbank down 827",
                 lambda rows, c: len(rows) == 10 and ("Millbank", 3461, 2634, -827) in rows),
                ("the nets add up to zero",
                 lambda rows, c: sum(r[3] for r in rows) == 0)],
    ),
    dict(
        id=6, ledger="Q1227", concept="RER", tier="2 - Depots and routes",
        title="Where Old Foundry's customers went",
        prompt=(
            "Old Foundry closed on 2026-02-01. For each month from"
            " October 2025: how many parcels its customers (the ones"
            " whose home depot it is) handed in at Old Foundry, and how"
            " many at Central Hub. One GROUP BY on the month with two"
            " conditional sums on the origin.\n\n"
            "Return: month, at_old_foundry, at_central_hub"
        ),
        solution=("SELECT strftime('%Y-%m', p.collected_at), SUM(p.origin_depot_id = 2), SUM(p.origin_depot_id = 1)"
                  " FROM parcels p JOIN customers c ON c.customer_id = p.customer_id"
                  " WHERE c.depot_id = 2 AND p.collected_at >= '2025-10-01' GROUP BY strftime('%Y-%m', p.collected_at)"),
        trap_sql=("SELECT strftime('%Y-%m', p.collected_at), COUNT(*), 0"
                  " FROM parcels p JOIN customers c ON c.customer_id = p.customer_id"
                  " WHERE c.depot_id = 2 AND p.origin_depot_id = 2 AND p.collected_at >= '2025-10-01' GROUP BY strftime('%Y-%m', p.collected_at)"),
        note="A customer's home depot and a parcel's origin depot are"
             " two different foreign keys to depots, and the question"
             " lives in the gap between them: the customers stay, the"
             " origin moves. Filtering parcels to origin = Old Foundry,"
             " the trap, loses every month after the closure. From"
             " February every one of those customers' parcels was handed"
             " in at the hub.",
        claims=[("nine months, the switch in February 2026",
                 lambda rows, c: len(rows) == 9 and ("2026-01", 83, 0) in rows and ("2026-02", 0, 89) in rows),
                ("never both in one month",
                 lambda rows, c: all(r[1] == 0 or r[2] == 0 for r in rows))],
    ),
    # ================================================ 3 Customers and money
    dict(
        id=7, ledger="Q1228", concept="WALKIN", tier="3 - Customers and money",
        title="Walk-ins at the counter",
        prompt=(
            "For each service: its parcels, how many were handed in by"
            " someone with no customer account, and that as a"
            " percentage to one decimal. A parcel's customer_id is NULL"
            " for a walk-in: a NULL that means something, so it is"
            " counted, not skipped.\n\n"
            "Return: service, parcels, walk_ins, pct"
        ),
        solution=("SELECT service, COUNT(*), SUM(customer_id IS NULL), ROUND(100.0 * SUM(customer_id IS NULL) / COUNT(*), 1)"
                  " FROM parcels GROUP BY service"),
        trap_sql=("SELECT service, COUNT(*), COUNT(customer_id), ROUND(100.0 * COUNT(customer_id) / COUNT(*), 1)"
                  " FROM parcels GROUP BY service"),
        note="COUNT(customer_id) counts the rows where it is NOT NULL,"
             " so the trap reports the account customers' parcels and"
             " calls them walk-ins. SUM(customer_id IS NULL) counts the"
             " NULLs themselves, which here are a category -- a stranger"
             " at the counter -- rather than missing data. A quarter of"
             " parcels on every service are walk-ins, and they pay the"
             " same postage.",
        claims=[("three services, each about a quarter walk-ins",
                 lambda rows, c: len(rows) == 3 and all(24 <= r[3] <= 26 for r in rows)),
                ("5954 walk-in parcels",
                 lambda rows, c: sum(r[2] for r in rows) == 5954)],
    ),
    dict(
        id=8, ledger="Q1229", concept="UNPAID", tier="3 - Customers and money",
        title="The ten customers who owe the most",
        prompt=(
            "The ten business customers with the most unpaid invoice"
            " money outstanding: their name, how many invoices are"
            " unpaid, the total owed in cents, and the issue date of"
            " the oldest. An unpaid invoice has no paid_on. Order by the"
            " total, then by customer_id to settle a tie.\n\n"
            "Return: name, unpaid_invoices, owed_cents, oldest_issued"
        ),
        solution=("SELECT c.name, COUNT(*), SUM(i.amount_cents), MIN(i.issued_on)"
                  " FROM invoices i JOIN customers c ON c.customer_id = i.customer_id"
                  " WHERE i.paid_on IS NULL GROUP BY c.customer_id ORDER BY SUM(i.amount_cents) DESC, c.customer_id LIMIT 10"),
        trap_sql=("SELECT c.name, COUNT(*), SUM(i.amount_cents), MIN(i.issued_on)"
                  " FROM invoices i JOIN customers c ON c.customer_id = i.customer_id"
                  " GROUP BY c.customer_id ORDER BY SUM(i.amount_cents) DESC, c.customer_id LIMIT 10"),
        note="The WHERE on paid_on IS NULL comes before the grouping, so"
             " every aggregate -- the count, the sum, the oldest date --"
             " is over the unpaid invoices only; the trap totals every"
             " invoice and ranks the biggest customers, paid up or not."
             " 174 customers owe something; the top ten owe between 286"
             " and 550 dollars each, some of it since early 2025.",
        claims=[("ten customers, Papadopoulos Garden Supplies first",
                 lambda rows, c: len(rows) == 10 and max(rows, key=lambda r: r[2])[0] == "Papadopoulos Garden Supplies & Co"),
                ("every one owes more than 280 dollars",
                 lambda rows, c: all(r[2] > 28000 for r in rows))],
    ),
    dict(
        id=9, ledger="Q1230", concept="KG", tier="3 - Customers and money",
        title="The postage table, recovered from the parcels",
        prompt=(
            "Postage is a base per service plus a rate per STARTED"
            " kilogram. For each service and each started-kilogram band"
            " from 1 to 5: how many parcels, and the postage they paid"
            " (one value per band). The band is integer arithmetic on"
            " weight_g such that 1 to 1000 grams is band 1 and 1001 to"
            " 2000 is band 2.\n\n"
            "Return: service, kg_band, parcels, postage_cents"
        ),
        solution=("SELECT service, (weight_g - 1) / 1000 + 1, COUNT(*), MIN(postage_cents)"
                  " FROM parcels WHERE weight_g <= 5000 GROUP BY service, (weight_g - 1) / 1000 + 1"),
        trap_sql=("SELECT service, weight_g / 1000, COUNT(*), MIN(postage_cents)"
                  " FROM parcels WHERE weight_g <= 5000 GROUP BY service, weight_g / 1000"),
        note="'Started kilogram' is a ceiling: (weight - 1) / 1000 + 1 in"
             " integer arithmetic puts 1000 g in band 1 and 1001 g in"
             " band 2. Plain weight / 1000, the trap, is a floor -- 999 g"
             " lands in band 0 and 1000 g in band 1 -- and the bands no"
             " longer match the postage, so MIN and MAX disagree inside"
             " them. Recovered: economy 350 + 60 a kilo, standard 500 +"
             " 90, express 900 + 150.",
        claims=[("fifteen bands, economy's first kilo 410 cents",
                 lambda rows, c: len(rows) == 15 and ("economy", 1, 3734, 410) in rows),
                ("each band one price",
                 lambda rows, c: all(r[3] == c.execute("SELECT MAX(postage_cents) FROM parcels WHERE service = ? AND (weight_g - 1) / 1000 + 1 = ?", (r[0], r[1])).fetchone()[0] for r in rows))],
    ),
    # ===================================================== 4 People and time
    dict(
        id=10, ledger="Q1231", concept="COURIER", tier="4 - People and time",
        title="How many drops a bike courier makes in a day",
        prompt=(
            "For each courier on a bike: their deliveries, the number"
            " of DAYS on which they delivered something, and the"
            " deliveries per such day to two decimals. The days are a"
            " COUNT of DISTINCT dates; the span from first to last"
            " delivery would count the days off.\n\n"
            "Return: name, deliveries, days, per_day"
        ),
        solution=("SELECT c.name, COUNT(*), COUNT(DISTINCT date(p.delivered_at)), ROUND(1.0 * COUNT(*) / COUNT(DISTINCT date(p.delivered_at)), 2)"
                  " FROM parcels p JOIN couriers c ON c.courier_id = p.courier_id WHERE c.vehicle = 'bike' GROUP BY c.courier_id"),
        trap_sql=("SELECT c.name, COUNT(*), COUNT(DISTINCT date(p.delivered_at)),"
                  " ROUND(COUNT(*) / (julianday(MAX(p.delivered_at)) - julianday(MIN(p.delivered_at))), 2)"
                  " FROM parcels p JOIN couriers c ON c.courier_id = p.courier_id WHERE c.vehicle = 'bike' GROUP BY c.courier_id"),
        note="date() cuts a timestamp to its day and COUNT(DISTINCT)"
             " counts the different days, which is 'days worked' as far"
             " as the data knows. The span between first and last"
             " delivery, the trap, includes every day the courier was"
             " off and halves the rate. Bike couriers make one or two"
             " drops on a working day; the vans do the volume.",
        claims=[("nineteen bike couriers, each between 1 and 2 a day",
                 lambda rows, c: len(rows) == 19 and all(1 <= r[3] <= 2 for r in rows)),
                ("Samir Chowdhury the busiest with 643",
                 lambda rows, c: max(rows, key=lambda r: r[1])[0] == "Samir Chowdhury")],
    ),
    dict(
        id=11, ledger="Q1232", concept="WEEKDAY", tier="4 - People and time",
        title="Which day of the week people post things",
        prompt=(
            "Parcels collected on each day of the week, with the day"
            " NAMED -- 'Monday', not '1'. strftime gives the weekday as"
            " a digit from '0' for Sunday; a CASE turns it into a word."
            "\n\n"
            "Return: weekday, parcels"
        ),
        solution=("SELECT CASE strftime('%w', collected_at) WHEN '0' THEN 'Sunday' WHEN '1' THEN 'Monday' WHEN '2' THEN 'Tuesday'"
                  " WHEN '3' THEN 'Wednesday' WHEN '4' THEN 'Thursday' WHEN '5' THEN 'Friday' ELSE 'Saturday' END, COUNT(*)"
                  " FROM parcels GROUP BY strftime('%w', collected_at)"),
        trap_sql=("SELECT CASE strftime('%w', collected_at) WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday' WHEN 2 THEN 'Tuesday'"
                  " WHEN 3 THEN 'Wednesday' WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday' ELSE 'Saturday' END, COUNT(*)"
                  " FROM parcels GROUP BY strftime('%w', collected_at)"),
        note="strftime returns TEXT, so the CASE must compare with '0',"
             " not 0: the trap's integer WHENs never match a text '1'"
             " and every day falls through to the ELSE, Saturday, seven"
             " times over. The simple form of CASE -- CASE x WHEN a THEN"
             " ... -- is for exactly this kind of lookup. Collections are"
             " flat across the week, Sunday included: counters are open"
             " seven days.",
        claims=[("seven days, Monday the busiest",
                 lambda rows, c: len(rows) == 7 and max(rows, key=lambda r: r[1])[0] == "Monday"),
                ("every day between 3200 and 3600",
                 lambda rows, c: all(3200 <= r[1] <= 3600 for r in rows))],
    ),
    dict(
        id=12, ledger="Q1233", concept="MOM", tier="4 - People and time",
        title="Month on month",
        prompt=(
            "For each month: the parcels collected, and the change from"
            " the month before -- NULL for the first month, since there"
            " is nothing before it. A CTE of parcels per month, then a"
            " window function that looks one row back.\n\n"
            "Return: month, parcels, change"
        ),
        solution=("WITH m AS (SELECT strftime('%Y-%m', collected_at) AS mo, COUNT(*) AS n FROM parcels GROUP BY mo)"
                  " SELECT mo, n, n - LAG(n) OVER (ORDER BY mo) FROM m"),
        trap_sql=("WITH m AS (SELECT strftime('%Y-%m', collected_at) AS mo, COUNT(*) AS n FROM parcels GROUP BY mo)"
                  " SELECT mo, n, n - LAG(n, 1, 0) OVER (ORDER BY mo) FROM m"),
        note="LAG(n) is the previous row's n in the window's order, and"
             " on the first row there is none, so the difference is NULL"
             " -- which is the honest answer. Giving LAG a default of 0,"
             " the trap, reports January 2025 as a rise of 1,099 parcels"
             " from nothing. The volume grew through 2025 as customers"
             " joined, from 1,100 a month to over 1,500.",
        claims=[("eighteen months, the first with no change",
                 lambda rows, c: len(rows) == 18 and ("2025-01", 1099, None) in rows),
                ("changes sum to the growth over the period",
                 lambda rows, c: sum(r[2] for r in rows if r[2] is not None) == 1523 - 1099)],
    ),
    # =================================================== 5 Changing the data
    dict(
        id=13, ledger="Q1234", concept="TRG", tier="5 - Changing the data",
        kind="script",
        title="A delivery scan completes the parcel",
        prompt=(
            "When a scan with status 'delivered' is inserted, the"
            " parcel should be marked delivered: its delivered_at set"
            " to the scan's time and its courier_id to the scan's"
            " courier. Write an AFTER INSERT trigger on scans with a"
            " WHEN clause so that only delivery scans do this. The"
            " question then inserts a 'delivered' scan for parcel 40"
            " and a 'failed' scan for parcel 122.\n\n"
            "Checked: parcel 40's delivered_at and courier_id, parcel"
            " 122's delivered_at, and how many parcels are delivered"
        ),
        solution=("CREATE TRIGGER complete_on_delivery AFTER INSERT ON scans\n"
                  "WHEN NEW.status = 'delivered'\n"
                  "BEGIN\n"
                  "  UPDATE parcels SET delivered_at = NEW.scanned_at, courier_id = NEW.courier_id\n"
                  "  WHERE parcel_id = NEW.parcel_id;\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER complete_on_delivery AFTER INSERT ON scans\n"
                  "BEGIN\n"
                  "  UPDATE parcels SET delivered_at = NEW.scanned_at, courier_id = NEW.courier_id\n"
                  "  WHERE parcel_id = NEW.parcel_id;\n"
                  "END;"),
        driver_sql=("INSERT INTO scans (parcel_id, depot_id, courier_id, scanned_at, status) VALUES (40, 5, 7, '2026-07-01 10:00', 'delivered');\n"
                    "INSERT INTO scans (parcel_id, depot_id, courier_id, scanned_at, status) VALUES (122, 1, 3, '2026-07-01 11:00', 'failed');"),
        probe_sql=("SELECT (SELECT delivered_at FROM parcels WHERE parcel_id = 40), (SELECT courier_id FROM parcels WHERE parcel_id = 40),"
                   " (SELECT delivered_at FROM parcels WHERE parcel_id = 122), (SELECT COUNT(*) FROM parcels WHERE delivered_at IS NOT NULL)"),
        note="A trigger's WHEN clause decides whether the body runs at"
             " all, and NEW is the row just inserted, so the trigger can"
             " read the scan's status, time and courier. Without the"
             " WHEN, the trap fires on every scan and marks parcel 122"
             " delivered on the strength of a FAILED attempt. Parcels 40"
             " and 122 are two of the lost ones; the driver's delivery"
             " brings 40 home.",
        claims=[("parcel 40 delivered, parcel 122 still not",
                 lambda rows, c: rows == [("2026-07-01 10:00", 7, None, 23730)])],
    ),
    dict(
        id=14, ledger="Q1235", concept="UPD", tier="5 - Changing the data",
        kind="script",
        title="A surcharge on June's heavy parcels",
        prompt=(
            "From June 2026 a parcel over ten kilograms carries a"
            " surcharge of 500 cents. Add it, in one UPDATE, to the"
            " postage of every parcel collected in June 2026 that"
            " weighs more than 10,000 grams -- and to no other.\n\n"
            "Checked: how many parcels were collected in June, and"
            " their postage added up"
        ),
        solution=("UPDATE parcels SET postage_cents = postage_cents + 500"
                  " WHERE collected_at >= '2026-06-01' AND weight_g > 10000;"),
        trap_sql=("UPDATE parcels SET postage_cents = postage_cents + 500"
                  " WHERE collected_at >= '2026-06-01';"),
        probe_sql="SELECT COUNT(*), SUM(postage_cents) FROM parcels WHERE collected_at >= '2026-06-01'",
        note="An UPDATE's WHERE is the whole of its policy, and two"
             " conditions joined by AND narrow it to the rows that meet"
             " both. The trap forgets the weight and charges all 1,523"
             " June parcels, 761,500 cents instead of the 15,500 that 31"
             " heavy parcels owe. SET postage_cents = postage_cents + 500"
             " reads the old value and writes the new one in a single"
             " step.",
        claims=[("31 parcels surcharged, 15,500 cents",
                 lambda rows, c: rows == [(1523, 1134020 + 31 * 500)])],
    ),
    dict(
        id=15, ledger="Q1236", concept="DEL", tier="5 - Changing the data",
        kind="script",
        title="Clearing out the customers who never sent anything",
        prompt=(
            "Delete every customer who has never sent a parcel and has"
            " no invoice. Test 'never sent' with NOT EXISTS, not NOT IN:"
            " parcels.customer_id is NULL on every walk-in row, and a"
            " NOT IN over a list that holds a NULL is never true.\n\n"
            "Checked: how many customers remain, and how many of them"
            " have never sent a parcel"
        ),
        solution=("DELETE FROM customers WHERE NOT EXISTS (SELECT 1 FROM parcels p WHERE p.customer_id = customers.customer_id)"
                  " AND NOT EXISTS (SELECT 1 FROM invoices i WHERE i.customer_id = customers.customer_id);"),
        trap_sql=("DELETE FROM customers WHERE customer_id NOT IN (SELECT customer_id FROM parcels)"
                  " AND NOT EXISTS (SELECT 1 FROM invoices i WHERE i.customer_id = customers.customer_id);"),
        probe_sql=("SELECT COUNT(*), SUM(NOT EXISTS (SELECT 1 FROM parcels p WHERE p.customer_id = c.customer_id)) FROM customers c"),
        note="x NOT IN (list) is x <> every item, and x <> NULL is NULL,"
             " so a NULL anywhere in the list makes NOT IN NULL -- never"
             " true -- for every x: the trap deletes nobody and reports"
             " success. 5,954 walk-in parcels put a NULL in that list."
             " NOT EXISTS has no such problem, because it asks whether a"
             " matching row exists rather than comparing values. The 80"
             " customers go; foreign keys would have stopped the DELETE"
             " if any of them had a parcel or an invoice.",
        claims=[("80 customers gone, none left who never sent",
                 lambda rows, c: rows == [(620, 0)])],
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
