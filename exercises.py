"""Practice exercises: fifteen questions on the parcel-courier schema.

The third set on the courier scheme (SEED 1241), two tools per question,
the tiers named by task, on tools the first two courier sets left out,
with prompts that name the tool but do not write the statement. Along the
trail -- what follows an attempt by LEAD, the state of the moving parcels
by LAST_VALUE with the frame opened, scan statuses as columns by a
conditional-sum pivot. Regions and routes -- a region-to-region matrix as
JSON objects, parcels leaving and entering each region by UNION ALL,
customers who use more than one depot by COUNT(DISTINCT) in HAVING.
Weight and money -- weight quartiles by NTILE, cents per kilogram as a
ratio of sums, paid against unpaid by FILTER. Couriers and time -- idle
days as a span minus the active days, a running total by month, tenure
bands by a CASE with ranges. And three WRITABLE questions:

  * a BEFORE INSERT trigger that RAISEs on a second delivery
  * a VIRTUAL generated column of kilograms
  * a TEMP table of the lost parcels feeding an INSERT ... SELECT

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
    # ====================================================== 1 Along the trail
    dict(
        id=1, ledger="Q1252", concept="LEADT", tier="1 - Along the trail",
        title="What happens after the van leaves",
        prompt=(
            "For each vehicle type: how many 'out_for_delivery' scans"
            " its couriers made that were followed by another scan, the"
            " average minutes from that scan to the next one, and how"
            " many of those next scans were a failure. A window"
            " function that looks one row FORWARD within the parcel's"
            " trail, in a CTE; then group by the courier's vehicle.\n\n"
            "Return: vehicle, attempts, avg_minutes, failed"
        ),
        solution=("WITH w AS (SELECT courier_id, status, scanned_at,"
                  " LEAD(status) OVER (PARTITION BY parcel_id ORDER BY scanned_at) AS nxt,"
                  " LEAD(scanned_at) OVER (PARTITION BY parcel_id ORDER BY scanned_at) AS nxt_at FROM scans)"
                  " SELECT c.vehicle, COUNT(*), ROUND(AVG((julianday(w.nxt_at) - julianday(w.scanned_at)) * 1440)), SUM(w.nxt = 'failed')"
                  " FROM w JOIN couriers c ON c.courier_id = w.courier_id"
                  " WHERE w.status = 'out_for_delivery' AND w.nxt IS NOT NULL GROUP BY c.vehicle"),
        trap_sql=("WITH w AS (SELECT courier_id, status, scanned_at,"
                  " LAG(status) OVER (PARTITION BY parcel_id ORDER BY scanned_at) AS nxt,"
                  " LAG(scanned_at) OVER (PARTITION BY parcel_id ORDER BY scanned_at) AS nxt_at FROM scans)"
                  " SELECT c.vehicle, COUNT(*), ROUND(AVG((julianday(w.nxt_at) - julianday(w.scanned_at)) * 1440)), SUM(w.nxt = 'failed')"
                  " FROM w JOIN couriers c ON c.courier_id = w.courier_id"
                  " WHERE w.status = 'out_for_delivery' AND w.nxt IS NOT NULL GROUP BY c.vehicle"),
        note="LEAD fetches the NEXT row's value within the partition, so"
             " an attempt can be paired with its outcome -- delivered or"
             " failed -- and timed. LAG, the trap, looks back and pairs"
             " the attempt with the arrival before it, so the minutes come"
             " out negative and the 'failures' are the previous attempt's."
             " On every vehicle an attempt takes about three and three"
             " quarter hours and one in eight ends in a failure.",
        claims=[("three vehicles, each attempt about 220 minutes",
                 lambda rows, c: len(rows) == 3 and all(215 <= r[2] <= 230 for r in rows)),
                ("27146 attempts in all",
                 lambda rows, c: sum(r[1] for r in rows) == 27146)],
    ),
    dict(
        id=2, ledger="Q1253", concept="LASTV", tier="1 - Along the trail",
        title="Where the moving parcels are",
        prompt=(
            "For the parcels not yet delivered: how many are at each"
            " stage, by the status of their LATEST scan. LAST_VALUE over"
            " the parcel's trail gives it on every row once the frame"
            " is opened to the whole partition -- the default frame"
            " stops at the current row -- and DISTINCT then collapses"
            " each parcel to one row.\n\n"
            "Return: last_status, parcels"
        ),
        solution=("WITH w AS (SELECT DISTINCT s.parcel_id,"
                  " LAST_VALUE(s.status) OVER (PARTITION BY s.parcel_id ORDER BY s.scanned_at ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) AS last_status"
                  " FROM scans s JOIN parcels p ON p.parcel_id = s.parcel_id WHERE p.delivered_at IS NULL)"
                  " SELECT last_status, COUNT(*) FROM w GROUP BY last_status"),
        trap_sql=("WITH w AS (SELECT DISTINCT s.parcel_id,"
                  " LAST_VALUE(s.status) OVER (PARTITION BY s.parcel_id ORDER BY s.scanned_at) AS last_status"
                  " FROM scans s JOIN parcels p ON p.parcel_id = s.parcel_id WHERE p.delivered_at IS NULL)"
                  " SELECT last_status, COUNT(*) FROM w GROUP BY last_status"),
        note="With an ORDER BY, a window's default frame runs from the"
             " start of the partition to the CURRENT row, so LAST_VALUE"
             " is just the current row's value and every scan of a"
             " parcel reports itself as 'last'; the trap counts the same"
             " parcel under several statuses and gets 855 rows for 271"
             " parcels. ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED"
             " FOLLOWING makes the frame the whole trail. 113 of the"
             " moving parcels are not moving at all: their last word is"
             " a failure.",
        claims=[("four stages, 113 ending on a failure",
                 lambda rows, c: len(rows) == 4 and ("failed", 113) in rows),
                ("271 parcels in all",
                 lambda rows, c: sum(r[1] for r in rows) == 271)],
    ),
    dict(
        id=3, ledger="Q1254", concept="PIVOT", tier="1 - Along the trail",
        title="Attempts, failures and deliveries, vehicle by vehicle",
        prompt=(
            "For each vehicle type, three counts side by side as"
            " columns: its couriers' 'out_for_delivery' scans, 'failed'"
            " scans and 'delivered' scans. One GROUP BY and three"
            " conditional sums -- a pivot by hand.\n\n"
            "Return: vehicle, attempts, failures, deliveries"
        ),
        solution=("SELECT c.vehicle, SUM(s.status = 'out_for_delivery'), SUM(s.status = 'failed'), SUM(s.status = 'delivered')"
                  " FROM scans s JOIN couriers c ON c.courier_id = s.courier_id GROUP BY c.vehicle"),
        trap_sql=("SELECT c.vehicle, COUNT(CASE WHEN s.status = 'out_for_delivery' THEN 1 ELSE 0 END),"
                  " COUNT(CASE WHEN s.status = 'failed' THEN 1 ELSE 0 END), COUNT(CASE WHEN s.status = 'delivered' THEN 1 ELSE 0 END)"
                  " FROM scans s JOIN couriers c ON c.courier_id = s.courier_id GROUP BY c.vehicle"),
        note="SUM of a comparison counts the rows where it is true,"
             " which turns a status column into one column per status."
             " COUNT of a CASE with an ELSE 0, the trap, counts every"
             " row, because 0 is a value and COUNT skips only NULL -- so"
             " all three columns show the vehicle's total. Vans do the"
             " volume, bikes a third of it, lorries a tenth; the failure"
             " rate is one in eight everywhere.",
        claims=[("three vehicles, vans with 13271 deliveries",
                 lambda rows, c: len(rows) == 3 and ("van", 15155, 1884, 13271) in rows),
                ("every column different on every row",
                 lambda rows, c: all(r[1] > r[3] > r[2] for r in rows))],
    ),
    # =================================================== 2 Regions and routes
    dict(
        id=4, ledger="Q1255", concept="JSON", tier="2 - Regions and routes",
        title="Where each region's parcels go, as one JSON object",
        prompt=(
            "For each origin region: a JSON object whose keys are the"
            " five destination regions and whose values are the parcel"
            " counts, keys in alphabetical order. Count by region pair"
            " first -- not by depot pair -- then json_group_object per"
            " origin region.\n\n"
            "Return: region, destinations"
        ),
        solution=("WITH pairs AS (SELECT a.region AS o, b.region AS d, COUNT(*) AS n FROM parcels p"
                  " JOIN depots a ON a.depot_id = p.origin_depot_id JOIN depots b ON b.depot_id = p.dest_depot_id GROUP BY a.region, b.region)"
                  " SELECT o, json_group_object(d, n ORDER BY d) FROM pairs GROUP BY o"),
        trap_sql=("WITH pairs AS (SELECT a.region AS o, b.region AS d, COUNT(*) AS n FROM parcels p"
                  " JOIN depots a ON a.depot_id = p.origin_depot_id JOIN depots b ON b.depot_id = p.dest_depot_id GROUP BY p.origin_depot_id, p.dest_depot_id)"
                  " SELECT o, json_group_object(d, n ORDER BY d) FROM pairs GROUP BY o"),
        note="json_group_object adds one key per row it is given, and"
             " it does not merge duplicates: grouped by depot pair, the"
             " trap feeds it twenty rows per region and the object has"
             " 'central' four times with four different counts. The"
             " grouping has to be at the grain of the keys -- region"
             " pairs -- before the JSON is built. Every region sends"
             " most of its parcels to itself.",
        claims=[("five regions, five keys each",
                 lambda rows, c: len(rows) == 5 and all(r[1].count('":') == 5 for r in rows)),
                ("the south sends 2401 to itself",
                 lambda rows, c: any(r[0] == "south" and '"south":2401' in r[1] for r in rows))],
    ),
    dict(
        id=5, ledger="Q1256", concept="UNIONALL", tier="2 - Regions and routes",
        title="Parcels leaving each region, and arriving",
        prompt=(
            "For each region: the parcels collected there, the parcels"
            " delivered to it, and the difference (in minus out). Stack"
            " the two ends of every parcel with UNION ALL -- a row"
            " tagged 'out' for the origin, one tagged 'in' for the"
            " destination -- and total the stack in one GROUP BY.\n\n"
            "Return: region, out, in_, net"
        ),
        solution=("SELECT region, SUM(o), SUM(i), SUM(i) - SUM(o) FROM"
                  " (SELECT d.region, 1 AS o, 0 AS i FROM parcels p JOIN depots d ON d.depot_id = p.origin_depot_id"
                  " UNION ALL SELECT d.region, 0, 1 FROM parcels p JOIN depots d ON d.depot_id = p.dest_depot_id)"
                  " GROUP BY region"),
        trap_sql=("SELECT region, SUM(o), SUM(i), SUM(i) - SUM(o) FROM"
                  " (SELECT d.region, 1 AS o, 0 AS i FROM parcels p JOIN depots d ON d.depot_id = p.origin_depot_id"
                  " UNION SELECT d.region, 0, 1 FROM parcels p JOIN depots d ON d.depot_id = p.dest_depot_id)"
                  " GROUP BY region"),
        note="UNION ALL keeps every row; UNION removes duplicates, and"
             " here every row is a duplicate of thousands of others --"
             " ('south', 1, 0) is the same row whichever parcel made it"
             " -- so the trap collapses 48,000 rows to ten and every"
             " region sends one parcel and receives one. The south"
             " sends 1,136 more than it receives: Millbank's business"
             " customers post to the whole city.",
        claims=[("five regions, the south down 1136",
                 lambda rows, c: len(rows) == 5 and ("south", 6386, 5250, -1136) in rows),
                ("the nets add up to zero",
                 lambda rows, c: sum(r[3] for r in rows) == 0)],
    ),
    dict(
        id=6, ledger="Q1257", concept="MULTI", tier="2 - Regions and routes",
        title="Customers who use more than one depot",
        prompt=(
            "For each kind of customer: how many of its senders have"
            " handed parcels in at MORE THAN ONE depot. Per customer,"
            " the number of DIFFERENT origin depots, tested in HAVING;"
            " then a count per kind.\n\n"
            "Return: kind, multi_depot"
        ),
        solution=("SELECT c.kind, COUNT(*) FROM"
                  " (SELECT customer_id FROM parcels WHERE customer_id IS NOT NULL GROUP BY customer_id HAVING COUNT(DISTINCT origin_depot_id) > 1) x"
                  " JOIN customers c ON c.customer_id = x.customer_id GROUP BY c.kind"),
        trap_sql=("SELECT c.kind, COUNT(*) FROM"
                  " (SELECT customer_id FROM parcels WHERE customer_id IS NOT NULL GROUP BY customer_id HAVING COUNT(origin_depot_id) > 1) x"
                  " JOIN customers c ON c.customer_id = x.customer_id GROUP BY c.kind"),
        note="COUNT(column) counts rows; COUNT(DISTINCT column) counts"
             " different values, and 'more than one depot' is the"
             " second. The trap's HAVING keeps every customer with more"
             " than one PARCEL, which is nearly all of them. Only 40 of"
             " the 620 senders have used two depots -- the ones whose"
             " home depot was Old Foundry, mostly, after it closed and"
             " their parcels moved to the hub.",
        claims=[("two kinds, 40 customers in all",
                 lambda rows, c: len(rows) == 2 and sum(r[1] for r in rows) == 40),
                ("15 of them businesses",
                 lambda rows, c: ("business", 15) in rows)],
    ),
    # ==================================================== 3 Weight and money
    dict(
        id=7, ledger="Q1258", concept="NTILE", tier="3 - Weight and money",
        title="Parcels in four weight bands of equal size",
        prompt=(
            "Split the parcels into four equal groups by weight, the"
            " lightest quarter first: for each, the lightest and"
            " heaviest weight, and the average postage in"
            " whole cents. A window function that deals rows into"
            " numbered buckets, ordered by weight, in a CTE.\n\n"
            "Return: quartile, min_g, max_g, avg_postage"
        ),
        solution=("WITH q AS (SELECT weight_g, postage_cents, NTILE(4) OVER (ORDER BY weight_g) AS quartile FROM parcels)"
                  " SELECT quartile, MIN(weight_g), MAX(weight_g), ROUND(AVG(postage_cents)) FROM q GROUP BY quartile"),
        trap_sql=("WITH q AS (SELECT weight_g, postage_cents, NTILE(4) OVER (ORDER BY postage_cents) AS quartile FROM parcels)"
                  " SELECT quartile, MIN(weight_g), MAX(weight_g), ROUND(AVG(postage_cents)) FROM q GROUP BY quartile"),
        note="NTILE(4) numbers the rows 1 to 4 in the window's order so"
             " that each bucket has the same number of rows -- 6,000"
             " here -- which is a quartile by COUNT, not by value. The"
             " buckets are only weight bands if the ORDER BY is on"
             " weight; ordered by postage, the trap's bands run from 81"
             " grams to several kilograms every one. The heaviest"
             " quarter runs from 2.8 kg to 30 kg and pays nearly twice"
             " the lightest.",
        claims=[("four quartiles, the lightest from 81 grams",
                 lambda rows, c: len(rows) == 4 and any(r[0] == 1 and r[1] == 81 for r in rows)),
                ("the top quartile starts at 2759 grams and pays the most",
                 lambda rows, c: any(r[0] == 4 and r[1] == 2759 for r in rows) and max(rows, key=lambda r: r[3])[0] == 4)],
    ),
    dict(
        id=8, ledger="Q1259", concept="CPK", tier="3 - Weight and money",
        title="What a kilogram costs to send",
        prompt=(
            "For each service: the postage per kilogram in cents, to"
            " one decimal, as a RATIO OF SUMS -- all the postage over"
            " all the weight -- and not as an average of each parcel's"
            " own rate.\n\n"
            "Return: service, cents_per_kg"
        ),
        solution="SELECT service, ROUND(1000.0 * SUM(postage_cents) / SUM(weight_g), 1) FROM parcels GROUP BY service",
        trap_sql="SELECT service, ROUND(AVG(1000.0 * postage_cents / weight_g), 1) FROM parcels GROUP BY service",
        note="A rate over a group is total over total. The average of"
             " per-parcel rates, the trap, weights a 100-gram letter the"
             " same as a 20-kilogram box, and the letter's rate is"
             " enormous -- the base charge spread over a tenth of a kilo"
             " -- so the trap's figures are nearly double. Express costs"
             " two and a half times economy per kilogram.",
        claims=[("three services, express the dearest",
                 lambda rows, c: len(rows) == 3 and max(rows, key=lambda r: r[1])[0] == "express"),
                ("economy at 229.2",
                 lambda rows, c: ("economy", 229.2) in rows)],
    ),
    dict(
        id=9, ledger="Q1260", concept="FILTER", tier="3 - Weight and money",
        title="Paid and unpaid, side by side, by home depot",
        prompt=(
            "For each depot, of the customer's home: the invoice money"
            " paid, the invoice money unpaid, and the number of unpaid"
            " invoices -- all three from one GROUP BY. SQLite's FILTER"
            " clause puts a condition on one aggregate without touching"
            " the others.\n\n"
            "Return: name, paid_cents, unpaid_cents, unpaid_invoices"
        ),
        solution=("SELECT d.name, SUM(i.amount_cents) FILTER (WHERE i.paid_on IS NOT NULL),"
                  " SUM(i.amount_cents) FILTER (WHERE i.paid_on IS NULL), COUNT(*) FILTER (WHERE i.paid_on IS NULL)"
                  " FROM invoices i JOIN customers c ON c.customer_id = i.customer_id JOIN depots d ON d.depot_id = c.depot_id GROUP BY d.name"),
        trap_sql=("SELECT d.name, SUM(i.amount_cents), SUM(i.amount_cents), COUNT(*)"
                  " FROM invoices i JOIN customers c ON c.customer_id = i.customer_id JOIN depots d ON d.depot_id = c.depot_id"
                  " WHERE i.paid_on IS NULL GROUP BY d.name"),
        note="A WHERE filters the rows before every aggregate sees them,"
             " so one query cannot have both the paid total and the"
             " unpaid total that way; the trap filters to unpaid and"
             " reports the unpaid figure twice. FILTER (WHERE ...) after"
             " an aggregate filters that aggregate alone. Millbank's"
             " customers owe the most, but also pay the most.",
        claims=[("ten depots, Millbank's customers owing 193580",
                 lambda rows, c: len(rows) == 10 and ("Millbank", 1264730, 193580, 34) in rows),
                ("332 unpaid invoices in all",
                 lambda rows, c: sum(r[3] for r in rows) == 332)],
    ),
    # =================================================== 4 Couriers and time
    dict(
        id=10, ledger="Q1261", concept="IDLE", tier="4 - Couriers and time",
        title="Days without a delivery",
        prompt=(
            "For each vehicle type: its couriers who have delivered,"
            " and their average number of idle days -- the days inside"
            " the span from their first delivery to their last on which"
            " they delivered nothing, to one decimal. Per courier, the"
            " span in days (last minus first, plus one) minus the"
            " distinct delivery days; then average by vehicle.\n\n"
            "Return: vehicle, couriers, avg_idle_days"
        ),
        solution=("SELECT c.vehicle, COUNT(*), ROUND(AVG(x.span - x.active), 1) FROM"
                  " (SELECT courier_id, CAST(julianday(MAX(delivered_at)) - julianday(MIN(delivered_at)) AS INTEGER) + 1 AS span,"
                  " COUNT(DISTINCT date(delivered_at)) AS active FROM parcels WHERE courier_id IS NOT NULL GROUP BY courier_id) x"
                  " JOIN couriers c ON c.courier_id = x.courier_id GROUP BY c.vehicle"),
        trap_sql=("SELECT c.vehicle, COUNT(*), ROUND(AVG(x.span - x.active), 1) FROM"
                  " (SELECT courier_id, CAST(julianday(MAX(delivered_at)) - julianday(MIN(delivered_at)) AS INTEGER) + 1 AS span,"
                  " COUNT(date(delivered_at)) AS active FROM parcels WHERE courier_id IS NOT NULL GROUP BY courier_id) x"
                  " JOIN couriers c ON c.courier_id = x.courier_id GROUP BY c.vehicle"),
        note="Idle days are what is left of the span once the working"
             " days are taken out, and the working days are a COUNT of"
             " DISTINCT dates; the trap counts every delivery as a day,"
             " subtracts hundreds of 'days' from the span and reports"
             " negative idleness. Couriers are idle about a third of"
             " their span: weekends, holidays and the quiet start.",
        claims=[("three vehicles, every average between 150 and 220 days",
                 lambda rows, c: len(rows) == 3 and all(150 <= r[2] <= 220 for r in rows)),
                ("sixty couriers",
                 lambda rows, c: sum(r[1] for r in rows) == 60)],
    ),
    dict(
        id=11, ledger="Q1262", concept="RUN", tier="4 - Couriers and time",
        title="Parcels to date, month by month",
        prompt=(
            "For each month: the parcels collected, and the running"
            " total of parcels collected since the data began. A CTE of"
            " parcels per month, then a window SUM with an ORDER BY,"
            " whose default frame runs from the first row to the"
            " current one.\n\n"
            "Return: month, parcels, to_date"
        ),
        solution=("WITH m AS (SELECT strftime('%Y-%m', collected_at) AS mo, COUNT(*) AS n FROM parcels GROUP BY mo)"
                  " SELECT mo, n, SUM(n) OVER (ORDER BY mo) FROM m"),
        trap_sql=("WITH m AS (SELECT strftime('%Y-%m', collected_at) AS mo, COUNT(*) AS n FROM parcels GROUP BY mo)"
                  " SELECT mo, n, SUM(n) OVER () FROM m"),
        note="A window SUM with an ORDER BY accumulates: the frame is"
             " everything up to the current row, so each month sees the"
             " months before it added in. Without the ORDER BY the"
             " frame is the whole result and the trap shows 24,000 on"
             " every row. The running total crosses 12,000 in September"
             " 2025, nine months in, and the second nine months carry"
             " the other half: the volume grew.",
        claims=[("eighteen months, ending at 24000",
                 lambda rows, c: len(rows) == 18 and max(r[2] for r in rows) == 24000),
                ("the running total never falls",
                 lambda rows, c: [r[2] for r in sorted(rows)] == sorted(r[2] for r in rows))],
    ),
    dict(
        id=12, ledger="Q1263", concept="BANDS", tier="4 - Couriers and time",
        title="Couriers by how long they have been here",
        prompt=(
            "Couriers in three tenure bands as of 2026-06-30 -- 'under"
            " a year', '1 to 3 years', '3 years or more' -- and within"
            " each band by vehicle, with the count. A CASE with ranges"
            " on the days since hiring, tested from the shortest band"
            " up so that each WHEN can assume the earlier ones failed;"
            " couriers who have left still count by their hire date.\n\n"
            "Return: band, vehicle, couriers"
        ),
        solution=("SELECT CASE WHEN julianday('2026-06-30') - julianday(hired_on) < 365 THEN 'under a year'"
                  " WHEN julianday('2026-06-30') - julianday(hired_on) < 1095 THEN '1 to 3 years' ELSE '3 years or more' END,"
                  " vehicle, COUNT(*) FROM couriers GROUP BY 1, vehicle"),
        trap_sql=("SELECT CASE WHEN julianday('2026-06-30') - julianday(hired_on) < 1095 THEN '1 to 3 years'"
                  " WHEN julianday('2026-06-30') - julianday(hired_on) < 365 THEN 'under a year' ELSE '3 years or more' END,"
                  " vehicle, COUNT(*) FROM couriers GROUP BY 1, vehicle"),
        note="CASE takes the first WHEN that is true, so bands tested"
             " widest-first swallow the narrower ones: the trap's '< 1095'"
             " catches every courier under three years, including the"
             " five under a year, and the 'under a year' band never"
             " appears. From the narrowest up, each WHEN only has to"
             " state its upper edge. Most couriers have been here over"
             " three years; every bike courier has.",
        claims=[("eight band-and-vehicle rows, sixty couriers",
                 lambda rows, c: len(rows) == 8 and sum(r[2] for r in rows) == 60),
                ("five couriers under a year, none on a bike",
                 lambda rows, c: sum(r[2] for r in rows if r[0] == "under a year") == 5 and not any(r[0] == "under a year" and r[1] == "bike" for r in rows))],
    ),
    # =================================================== 5 Changing the data
    dict(
        id=13, ledger="Q1264", concept="RAISE", tier="5 - Changing the data",
        kind="script",
        title="A parcel cannot be delivered twice",
        prompt=(
            "Write a BEFORE INSERT trigger on scans that refuses a"
            " 'delivered' scan for a parcel that already has a"
            " delivered_at, by raising an error -- and lets every other"
            " scan through. The question then inserts a 'delivered'"
            " scan for parcel 1, which is delivered, and one for parcel"
            " 40, which is not.\n\n"
            "Checked: how many scans dated 2026-07-01 or later got in"
        ),
        solution=("CREATE TRIGGER no_double_delivery BEFORE INSERT ON scans\n"
                  "WHEN NEW.status = 'delivered'\n"
                  " AND (SELECT delivered_at FROM parcels WHERE parcel_id = NEW.parcel_id) IS NOT NULL\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'parcel already delivered');\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER no_double_delivery BEFORE INSERT ON scans\n"
                  "WHEN NEW.status = 'delivered'\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'parcel already delivered');\n"
                  "END;"),
        driver_sql=("INSERT INTO scans (parcel_id, depot_id, courier_id, scanned_at, status) VALUES (1, 1, 1, '2026-07-01 10:00', 'delivered');\n"
                    "INSERT INTO scans (parcel_id, depot_id, courier_id, scanned_at, status) VALUES (40, 5, 7, '2026-07-01 10:00', 'delivered');"),
        probe_sql="SELECT COUNT(*) FROM scans WHERE scanned_at >= '2026-07-01'",
        note="RAISE(ABORT, message) inside a trigger body cancels the"
             " statement that fired it and reports the message, which"
             " the status bar shows. The WHEN clause is where the rule"
             " lives: the trap's WHEN tests only the status and refuses"
             " EVERY delivery, parcel 40's included. A subquery in WHEN"
             " can look at other tables, which is how the trigger knows"
             " whether the parcel is already home.",
        claims=[("one scan in, the double delivery refused",
                 lambda rows, c: rows == [(1,)])],
    ),
    dict(
        id=14, ledger="Q1265", concept="GEN", tier="5 - Changing the data",
        kind="script",
        title="Kilograms, computed on the fly",
        prompt=(
            "Add a column weight_kg to parcels that is computed from"
            " weight_g rather than stored: a REAL generated column,"
            " VIRTUAL, holding the weight in kilograms with its"
            " fraction. Mind the division.\n\n"
            "Checked: the column's average to three decimals, its"
            " maximum, and the maximum's storage type"
        ),
        solution="ALTER TABLE parcels ADD COLUMN weight_kg REAL GENERATED ALWAYS AS (weight_g / 1000.0) VIRTUAL;",
        trap_sql="ALTER TABLE parcels ADD COLUMN weight_kg REAL GENERATED ALWAYS AS (weight_g / 1000) VIRTUAL;",
        probe_sql="SELECT ROUND(AVG(weight_kg), 3), MAX(weight_kg), typeof(MAX(weight_kg)) FROM parcels",
        note="A generated column is an expression that behaves like a"
             " column: queries read it, indexes can use it, and ALTER"
             " TABLE can add the VIRTUAL kind to an existing table."
             " Declaring it REAL does not make the arithmetic real:"
             " weight_g / 1000 is integer division before the value is"
             " stored, and the trap's kilograms are whole -- the average"
             " comes out at 1.755 instead of 2.260. Divide by 1000.0.",
        claims=[("an average of 2.26 kg, real",
                 lambda rows, c: rows == [(2.26, 30.0, "real")])],
    ),
    dict(
        id=15, ledger="Q1266", concept="TMP", tier="5 - Changing the data",
        kind="script",
        title="Refunds for the lost parcels",
        prompt=(
            "Three steps: create a table refunds with parcel_id as its"
            " primary key and a cents column; create a TEMP table of"
            " the lost parcels' ids -- not delivered, and the latest"
            " scan a failure, as in question 2; then INSERT into"
            " refunds, from a SELECT, each lost parcel's id and its"
            " postage.\n\n"
            "Checked: how many refunds there are, and the cents added up"
        ),
        solution=("CREATE TABLE refunds (parcel_id INTEGER PRIMARY KEY REFERENCES parcels(parcel_id), cents INTEGER NOT NULL);\n"
                  "CREATE TEMP TABLE lost AS SELECT parcel_id FROM parcels p WHERE p.delivered_at IS NULL\n"
                  "  AND (SELECT status FROM scans s WHERE s.parcel_id = p.parcel_id ORDER BY scanned_at DESC LIMIT 1) = 'failed';\n"
                  "INSERT INTO refunds (parcel_id, cents) SELECT parcel_id, postage_cents FROM parcels WHERE parcel_id IN (SELECT parcel_id FROM lost);"),
        trap_sql=("CREATE TABLE refunds (parcel_id INTEGER PRIMARY KEY REFERENCES parcels(parcel_id), cents INTEGER NOT NULL);\n"
                  "CREATE TEMP TABLE lost AS SELECT parcel_id FROM parcels WHERE delivered_at IS NULL;\n"
                  "INSERT INTO refunds (parcel_id, cents) SELECT parcel_id, postage_cents FROM parcels WHERE parcel_id IN (SELECT parcel_id FROM lost);"),
        probe_sql="SELECT COUNT(*), SUM(cents) FROM refunds",
        note="A TEMP table lives in the connection and vanishes with it,"
             " which makes it a scratch pad for a multi-step change:"
             " name the set once, use it in the INSERT. The trap's set"
             " is every undelivered parcel, 271, and refunds the 158"
             " that are simply still on their way. The parcels' own"
             " postage cannot be zeroed -- a CHECK insists it is"
             " positive -- which is why the refund is a row elsewhere.",
        claims=[("113 refunds, 79,650 cents",
                 lambda rows, c: rows == [(113, 79650)])],
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
