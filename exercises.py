"""Practice exercises: fifteen questions on the parcel-courier schema.

The seventh set on the courier scheme (SEED 1241), nine questions that
read and six that change the data, the last three of them procedures. The
tiers are named by task, the tools are ones the first six courier sets
left out, and the prompts name the tool but do not write the statement.
Joins and lookups -- hires beside leavers by FULL OUTER JOIN, two totals
side by side by aggregating before the join, each depot's newest courier
by a correlated ORDER BY ... LIMIT 1. Calendar buckets -- quarters by
integer division, weeks labelled by their Monday with the 'weekday'
modifier, senders by the month of their first parcel. Whole groups -- a
row against its own group's average by a window AVG, customers with every
invoice paid by COUNT(*) against COUNT(column), customers who always paid
the same way by MIN = MAX.

Changing rows, three single statements:

  * an INSERT ... SELECT that copies a row with two values replaced
  * an UPDATE whose rows are chosen by a window function in a subquery
  * a DELETE matching (customer, period) pairs as row values

Procedures, three scripts of several steps. SQLite has no CREATE
PROCEDURE; what it has is a transaction, whose steps stand or fall
together, and a trigger body, which is stored and runs when called:

  * two depots swap rosters, with a TEMP table to remember who was where
  * two customer records merged: children moved, a date kept, then the
    duplicate deleted
  * a summary table created, filled, and kept current by a trigger

Each writable question runs in a private in-memory copy of the database,
so nothing you write can reach the real file. The copy persists across
Runs of one question -- run an UPDATE, then a SELECT to see what it did --
and is discarded by Reset or by moving to another question, so no question
can depend on what another one wrote. Check answer always grades a FRESH
copy. The question's `probe_sql` then reads the result, and that is what
is compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script.
"""

import sqlite3

EXERCISES = [
    # ==================================================== 1 Joins and lookups
    dict(
        id=1, ledger="Q1312", concept="FULL", tier="1 - Joins and lookups",
        title="Hires and leavers, depot by depot",
        prompt=(
            "For each depot, by name: how many couriers it has hired"
            " since 2025-01-01, and how many of its couriers have left."
            " Some depots hired and lost nobody, some lost and hired"
            " nobody; a depot with neither is not listed, and a missing"
            " count is 0. Two grouped subqueries, and the join that"
            " keeps the unmatched rows of BOTH sides.\n\n"
            "Return: depot, hired, left"
        ),
        solution=("SELECT d.name, COALESCE(h.n, 0), COALESCE(l.n, 0) FROM"
                  " (SELECT depot_id, COUNT(*) AS n FROM couriers WHERE hired_on >= '2025-01-01' GROUP BY depot_id) h"
                  " FULL OUTER JOIN"
                  " (SELECT depot_id, COUNT(*) AS n FROM couriers WHERE left_on IS NOT NULL GROUP BY depot_id) l"
                  " ON l.depot_id = h.depot_id"
                  " JOIN depots d ON d.depot_id = COALESCE(h.depot_id, l.depot_id)"),
        trap_sql=("SELECT d.name, COALESCE(h.n, 0), COALESCE(l.n, 0) FROM"
                  " (SELECT depot_id, COUNT(*) AS n FROM couriers WHERE hired_on >= '2025-01-01' GROUP BY depot_id) h"
                  " LEFT JOIN"
                  " (SELECT depot_id, COUNT(*) AS n FROM couriers WHERE left_on IS NOT NULL GROUP BY depot_id) l"
                  " ON l.depot_id = h.depot_id"
                  " JOIN depots d ON d.depot_id = h.depot_id"),
        note="A FULL OUTER JOIN keeps every row of both inputs and"
             " fills the side with no match with NULLs, so a depot"
             " appears if it is in EITHER list. The LEFT JOIN of the"
             " trap starts from the hires and loses Millbank, which"
             " hired nobody and lost one. After a full join either"
             " side's key may be the NULL one, which is why the depot"
             " is looked up through COALESCE of the two. SQLite has had"
             " FULL and RIGHT joins since 3.39.",
        claims=[("nine depots, Millbank with no hires and one leaver",
                 lambda rows, c: len(rows) == 9 and ("Millbank", 0, 1) in rows),
                ("Docklands hired two and lost none",
                 lambda rows, c: ("Docklands", 2, 0) in rows)],
    ),
    dict(
        id=2, ledger="Q1313", concept="FANOUT", tier="1 - Joins and lookups",
        title="Postage and invoices, side by side",
        prompt=(
            "For each depot, by name, and its BUSINESS customers only:"
            " the postage on all their parcels, and the amount on all"
            " their invoices. A customer has many parcels and many"
            " invoices, so joining both tables to the customer at once"
            " pairs every parcel with every invoice. Add each one up on"
            " its own first, then join the totals.\n\n"
            "Return: depot, postage_cents, invoiced_cents"
        ),
        solution=("WITH post AS (SELECT c.depot_id, SUM(p.postage_cents) AS cents FROM parcels p"
                  " JOIN customers c ON c.customer_id = p.customer_id WHERE c.kind = 'business' GROUP BY c.depot_id),"
                  " inv AS (SELECT c.depot_id, SUM(i.amount_cents) AS cents FROM invoices i"
                  " JOIN customers c ON c.customer_id = i.customer_id WHERE c.kind = 'business' GROUP BY c.depot_id)"
                  " SELECT d.name, post.cents, inv.cents FROM depots d"
                  " JOIN post ON post.depot_id = d.depot_id JOIN inv ON inv.depot_id = d.depot_id"),
        trap_sql=("SELECT d.name, SUM(p.postage_cents), SUM(i.amount_cents) FROM depots d"
                  " JOIN customers c ON c.depot_id = d.depot_id AND c.kind = 'business'"
                  " JOIN parcels p ON p.customer_id = c.customer_id"
                  " JOIN invoices i ON i.customer_id = c.customer_id GROUP BY d.name"),
        note="Two one-to-many joins from the same parent multiply: a"
             " customer with 100 parcels and 15 invoices becomes 1,500"
             " rows, and each SUM counts its values many times over."
             " The trap's totals come out more than ten times too big,"
             " and nothing errors. Aggregating each child table down to"
             " one row per depot BEFORE joining makes both joins"
             " one-to-one. The postage is the larger of the two"
             " because June has not been invoiced yet.",
        claims=[("ten depots, Central Hub 902,320 posted and 857,470 invoiced",
                 lambda rows, c: len(rows) == 10 and ("Central Hub", 902320, 857470) in rows),
                ("invoiced is always the smaller",
                 lambda rows, c: all(r[2] < r[1] for r in rows))],
    ),
    dict(
        id=3, ledger="Q1314", concept="LATEST", tier="1 - Joins and lookups",
        title="Each depot's newest courier",
        prompt=(
            "For each depot, by name: the courier it hired most"
            " recently, and the date. Couriers who have since left"
            " count. The name and the date must belong to the SAME"
            " courier: a correlated subquery that sorts that depot's"
            " couriers and takes one.\n\n"
            "Return: depot, courier, hired_on"
        ),
        solution=("SELECT d.name, c.name, c.hired_on FROM depots d JOIN couriers c ON c.courier_id ="
                  " (SELECT c2.courier_id FROM couriers c2 WHERE c2.depot_id = d.depot_id"
                  " ORDER BY c2.hired_on DESC LIMIT 1)"),
        trap_sql=("SELECT d.name, MAX(c.name), MAX(c.hired_on) FROM depots d"
                  " JOIN couriers c ON c.depot_id = d.depot_id GROUP BY d.depot_id"),
        note="ORDER BY ... LIMIT 1 inside a correlated subquery returns"
             " one whole row's key for each outer row, so everything"
             " read through it comes from the same courier. Two MAXes,"
             " the trap, are computed independently: the latest date"
             " in the depot beside the name that sorts last in the"
             " alphabet, usually two different people. Central Hub's"
             " newest hire is Quentin Mbeki; MAX(name) says Tamsin"
             " Chowdhury.",
        claims=[("ten depots, Central Hub's newest is Quentin Mbeki",
                 lambda rows, c: len(rows) == 10 and ("Central Hub", "Quentin Mbeki", "2020-01-23") in rows),
                ("Docklands hired Aisha Chowdhury last, in November 2025",
                 lambda rows, c: ("Docklands", "Aisha Chowdhury", "2025-11-20") in rows)],
    ),
    # ===================================================== 2 Calendar buckets
    dict(
        id=4, ledger="Q1315", concept="QTR", tier="2 - Calendar buckets",
        title="Parcels and postage by quarter",
        prompt=(
            "For each calendar quarter of collection, labelled like"
            " '2025-Q1': the parcels collected and their postage."
            " January to March is Q1. strftime has no code for the"
            " quarter; it comes from the month number by integer"
            " arithmetic, and the label is put together with ||.\n\n"
            "Return: quarter, parcels, postage_cents"
        ),
        solution=("SELECT strftime('%Y', collected_at) || '-Q' ||"
                  " ((CAST(strftime('%m', collected_at) AS INTEGER) + 2) / 3) AS quarter,"
                  " COUNT(*), SUM(postage_cents) FROM parcels GROUP BY quarter"),
        trap_sql=("SELECT strftime('%Y', collected_at) || '-Q' ||"
                  " (CAST(strftime('%m', collected_at) AS INTEGER) / 3) AS quarter,"
                  " COUNT(*), SUM(postage_cents) FROM parcels GROUP BY quarter"),
        note="Integer division throws the remainder away, so (month +"
             " 2) / 3 sends 1, 2, 3 to 1 and 4, 5, 6 to 2: the + 2"
             " moves each quarter's last month up to a multiple of"
             " three. Plain month / 3, the trap, puts January and"
             " February in a 'Q0' and March with April and May."
             " strftime returns text, and text / 3 would still work in"
             " SQLite by silent conversion; the CAST says what is"
             " meant. || joins text and turns the number back into it.",
        claims=[("six quarters, 2026-Q2 the busiest with 4,455",
                 lambda rows, c: len(rows) == 6 and max(rows, key=lambda r: r[1]) == ("2026-Q2", 4455, 3326850)),
                ("2025-Q1 the quietest",
                 lambda rows, c: min(rows, key=lambda r: r[1])[0] == "2025-Q1")],
    ),
    dict(
        id=5, ledger="Q1316", concept="WEEK", tier="2 - Calendar buckets",
        title="June, week by week",
        prompt=(
            "Parcels collected in June 2026, counted by week. A week"
            " runs Monday to Sunday and is labelled with the DATE of"
            " its Monday. The 'weekday N' date modifier only ever"
            " moves a date forward, to the next such weekday or not"
            " at all, so reaching the Monday behind you takes a second"
            " modifier after it.\n\n"
            "Return: week_starting, parcels"
        ),
        solution=("SELECT date(collected_at, 'weekday 0', '-6 days') AS week_starting, COUNT(*) FROM parcels"
                  " WHERE collected_at >= '2026-06-01' AND collected_at < '2026-07-01' GROUP BY week_starting"),
        trap_sql=("SELECT date(collected_at, 'weekday 1') AS week_starting, COUNT(*) FROM parcels"
                  " WHERE collected_at >= '2026-06-01' AND collected_at < '2026-07-01' GROUP BY week_starting"),
        note="'weekday 0' moves forward to Sunday, the END of the"
             " week, staying put if the date is already a Sunday; '-6"
             " days' then steps back to that week's Monday. Every day"
             " from Monday to Sunday lands on the same date. 'weekday"
             " 1' alone, the trap, sends Tuesday to the FOLLOWING"
             " Monday: only Mondays stay in their own week, and a row"
             " for 6 July appears in a count of June. 1 June 2026 was"
             " a Monday, so the first week is a full one.",
        claims=[("five weeks, the first starting 2026-06-01 with 319",
                 lambda rows, c: len(rows) == 5 and ("2026-06-01", 319) in rows),
                ("the last week has only two days in June: 101 parcels",
                 lambda rows, c: ("2026-06-29", 101) in rows)],
    ),
    dict(
        id=6, ledger="Q1317", concept="COHORT", tier="2 - Calendar buckets",
        title="The month each sender first sent",
        prompt=(
            "For each month, as 'YYYY-MM': how many customers sent"
            " their FIRST parcel in it. A customer is counted once, in"
            " the month of their earliest collection; walk-ins are"
            " left out. An aggregate per customer, then a second"
            " grouping on what it found.\n\n"
            "Return: month, new_senders"
        ),
        solution=("SELECT first_month, COUNT(*) FROM (SELECT customer_id, strftime('%Y-%m', MIN(collected_at)) AS first_month"
                  " FROM parcels WHERE customer_id IS NOT NULL GROUP BY customer_id) GROUP BY first_month"),
        trap_sql=("SELECT strftime('%Y-%m', collected_at) AS m, COUNT(DISTINCT customer_id)"
                  " FROM parcels WHERE customer_id IS NOT NULL GROUP BY m"),
        note="The inner query reduces each customer to one row, the"
             " month of their MIN(collected_at); the outer one counts"
             " customers per month. That is a cohort: everyone is in"
             " exactly one bucket, and the buckets add up to the 620"
             " customers who have ever sent. Counting the distinct"
             " customers active in each month, the trap, counts a"
             " regular sender eighteen times. Nearly half the senders,"
             " 283, were there in the first month of the data.",
        claims=[("eighteen months, 283 first sent in January 2025",
                 lambda rows, c: len(rows) == 18 and ("2025-01", 283) in rows),
                ("the cohorts add up to 620",
                 lambda rows, c: sum(r[1] for r in rows) == 620)],
    ),
    # ========================================================= 3 Whole groups
    dict(
        id=7, ledger="Q1318", concept="WAVG", tier="3 - Whole groups",
        title="Parcels that cost twice their service's average",
        prompt=(
            "For each service: how many parcels paid MORE THAN DOUBLE"
            " the average postage of their own service. A window AVG"
            " puts the group's average beside every row; the"
            " comparison then needs an outer query.\n\n"
            "Return: service, parcels"
        ),
        solution=("SELECT service, COUNT(*) FROM (SELECT service, postage_cents,"
                  " AVG(postage_cents) OVER (PARTITION BY service) AS avg_cents FROM parcels)"
                  " WHERE postage_cents > 2 * avg_cents GROUP BY service"),
        trap_sql=("SELECT service, COUNT(*) FROM (SELECT service, postage_cents,"
                  " AVG(postage_cents) OVER () AS avg_cents FROM parcels)"
                  " WHERE postage_cents > 2 * avg_cents GROUP BY service"),
        note="AVG(x) OVER (PARTITION BY service) is the service's"
             " average repeated on each of its rows, with every row"
             " still there to be compared with it -- GROUP BY would"
             " have collapsed them. The trap's empty OVER () is the"
             " average of ALL parcels, about 740 cents: against that,"
             " more than a thousand express parcels look expensive"
             " simply for being express, and almost no economy ones"
             " do. A window function cannot be tested in WHERE at its"
             " own level, hence the subquery.",
        claims=[("three services, 153 economy parcels",
                 lambda rows, c: len(rows) == 3 and ("economy", 153) in rows),
                ("59 express and 95 standard",
                 lambda rows, c: ("express", 59) in rows and ("standard", 95) in rows)],
    ),
    dict(
        id=8, ledger="Q1319", concept="CNTCOL", tier="3 - Whole groups",
        title="Customers with nothing outstanding",
        prompt=(
            "For each depot, by name: how many of its customers have"
            " been invoiced and have paid EVERY invoice. A depot with"
            " no such customer is not listed. COUNT(*) counts rows and"
            " COUNT(column) counts the rows where the column is not"
            " NULL; HAVING can compare the two.\n\n"
            "Return: depot, customers"
        ),
        solution=("SELECT d.name, COUNT(*) FROM (SELECT customer_id FROM invoices GROUP BY customer_id"
                  " HAVING COUNT(*) = COUNT(paid_on)) x JOIN customers c ON c.customer_id = x.customer_id"
                  " JOIN depots d ON d.depot_id = c.depot_id GROUP BY d.name"),
        trap_sql=("SELECT d.name, COUNT(DISTINCT i.customer_id) FROM invoices i"
                  " JOIN customers c ON c.customer_id = i.customer_id"
                  " JOIN depots d ON d.depot_id = c.depot_id WHERE i.paid_on IS NOT NULL GROUP BY d.name"),
        note="'Every invoice is paid' is a statement about the whole"
             " group, so it is tested in HAVING: the group's row count"
             " equals its count of non-NULL paid_on exactly when no"
             " invoice is unpaid. A WHERE paid_on IS NOT NULL, the"
             " trap, throws the unpaid invoices away before grouping"
             " and so finds customers with ANY paid invoice, 221 of"
             " them instead of 49. Old Foundry has none: every one of"
             " its invoiced customers owes something.",
        claims=[("nine depots, 49 customers in all",
                 lambda rows, c: len(rows) == 9 and sum(r[1] for r in rows) == 49),
                ("Old Foundry is not listed",
                 lambda rows, c: all(r[0] != "Old Foundry" for r in rows))],
    ),
    dict(
        id=9, ledger="Q1320", concept="MINMAX", tier="3 - Whole groups",
        title="Customers who always pay the same way",
        prompt=(
            "Some customers have paid every invoice they have paid by"
            " the same method. For each method: how many customers"
            " have only ever used that one. Unpaid invoices have no"
            " method and do not count either way. A group holds a"
            " single value exactly when its smallest and its largest"
            " are the same.\n\n"
            "Return: method, customers"
        ),
        solution=("SELECT only_method, COUNT(*) FROM (SELECT customer_id, MIN(method) AS only_method FROM invoices"
                  " GROUP BY customer_id HAVING MIN(method) = MAX(method)) GROUP BY only_method"),
        trap_sql=("SELECT method, COUNT(DISTINCT customer_id) FROM invoices WHERE method IS NOT NULL GROUP BY method"),
        note="MIN and MAX work on text as well as numbers, and if the"
             " first and the last value in alphabetical order are the"
             " same there is only one value in the group. Both skip"
             " NULLs, so unpaid invoices drop out on their own, and a"
             " customer who has paid nothing has NULL = NULL, which is"
             " not true, and drops out too. The trap counts everyone"
             " who has EVER used a method, most customers twice."
             " HAVING COUNT(DISTINCT method) = 1 says the same thing"
             " the long way.",
        claims=[("two methods: 20 customers only by transfer, 2 only by card",
                 lambda rows, c: sorted(rows) == [("card", 2), ("transfer", 20)])],
    ),
    # ======================================================== 4 Changing rows
    dict(
        id=10, ledger="Q1321", concept="CLONE", tier="4 - Changing rows",
        kind="script",
        title="A second depot, copied from the first",
        prompt=(
            "A new depot opens on 2026-07-01, called 'Harbour Point"
            " East'. It is in the same region as Harbour Point and has"
            " the same number of bays, whatever those are -- read"
            " them, do not type them in. One INSERT ... SELECT whose"
            " SELECT reads the row being copied and supplies the new"
            " name and date itself.\n\n"
            "Checked: name, region, bays, opening and closing dates of"
            " every depot whose name starts 'Harbour Point'"
        ),
        solution=("INSERT INTO depots (name, region, bays, opened_on)\n"
                  "SELECT 'Harbour Point East', region, bays, '2026-07-01'\n"
                  "FROM depots WHERE name = 'Harbour Point';"),
        trap_sql=("INSERT INTO depots (name, region, bays, opened_on)\n"
                  "SELECT 'Harbour Point East', region, bays, opened_on\n"
                  "FROM depots WHERE name = 'Harbour Point';"),
        probe_sql="SELECT name, region, bays, opened_on, closed_on FROM depots WHERE name LIKE 'Harbour Point%'",
        note="A SELECT list can mix columns with literals, so INSERT"
             " ... SELECT copies a row while replacing the values that"
             " should differ: the literals go where the new name and"
             " date belong, the column names where the old values"
             " carry over. depot_id is left out of the column list and"
             " the table assigns the next one. The trap copies"
             " opened_on along with the rest, and the new depot has"
             " been open since 2021. A WHERE that matched two rows"
             " would insert two depots, and the UNIQUE name would"
             " refuse the second.",
        claims=[("two Harbour Points, the new one east, 14 bays, opened in July",
                 lambda rows, c: sorted(rows) == [("Harbour Point", "east", 14, "2021-02-01", None),
                                                  ("Harbour Point East", "east", 14, "2026-07-01", None)])],
    ),
    dict(
        id=11, ledger="Q1322", concept="UPWIN", tier="4 - Changing rows",
        kind="script",
        title="The longest-serving bike courier gets a van",
        prompt=(
            "At each depot, the bike courier who has been there"
            " longest and is STILL EMPLOYED moves up to a van. A depot"
            " with no such courier promotes nobody. One UPDATE; which"
            " couriers is decided by a subquery that numbers the"
            " candidates within their depot with a window function.\n\n"
            "Checked: for each vehicle, the couriers listed and how"
            " many of them are still employed"
        ),
        solution=("UPDATE couriers SET vehicle = 'van'\n"
                  "WHERE courier_id IN (\n"
                  "  SELECT courier_id FROM (\n"
                  "    SELECT courier_id, ROW_NUMBER() OVER (PARTITION BY depot_id ORDER BY hired_on) AS rn\n"
                  "    FROM couriers WHERE vehicle = 'bike' AND left_on IS NULL)\n"
                  "  WHERE rn = 1);"),
        trap_sql=("UPDATE couriers SET vehicle = 'van'\n"
                  "WHERE courier_id IN (\n"
                  "  SELECT courier_id FROM (\n"
                  "    SELECT courier_id, vehicle, left_on,\n"
                  "           ROW_NUMBER() OVER (PARTITION BY depot_id ORDER BY hired_on) AS rn\n"
                  "    FROM couriers)\n"
                  "  WHERE rn = 1 AND vehicle = 'bike' AND left_on IS NULL);"),
        probe_sql="SELECT vehicle, COUNT(*), SUM(left_on IS NULL) FROM couriers GROUP BY vehicle",
        note="An UPDATE cannot hold a window function itself, but its"
             " WHERE can read a subquery that does: number the"
             " candidates, keep number 1, update those ids. Where the"
             " filter goes decides who is a candidate. Inside, before"
             " the numbering, number 1 is the longest-serving current"
             " bike courier: eight depots have one. Outside, after it,"
             " as in the trap, number 1 is the depot's longest-serving"
             " courier of any kind, promoted only if that happens to"
             " be a current bike courier: four depots.",
        claims=[("eight promoted: eleven bikes left, seven of them current",
                 lambda rows, c: ("bike", 11, 7) in rows),
                ("forty vans, lorries untouched",
                 lambda rows, c: ("van", 40, 31) in rows and ("lorry", 9, 7) in rows)],
    ),
    dict(
        id=12, ledger="Q1323", concept="DELROW", tier="4 - Changing rows",
        kind="script",
        title="Invoices not worth chasing",
        prompt=(
            "An invoice for a single parcel is not worth chasing."
            " Cancel -- delete -- every UNPAID invoice whose period"
            " saw that customer send exactly ONE parcel. An invoice's"
            " period is the 'YYYY-MM' in which its parcels were"
            " collected. A DELETE whose WHERE matches (customer,"
            " period) PAIRS, as a row value, against a grouped"
            " subquery.\n\n"
            "Checked: invoices left, their cents added up, how many"
            " are unpaid"
        ),
        solution=("DELETE FROM invoices\n"
                  "WHERE paid_on IS NULL\n"
                  "  AND (customer_id, period) IN (\n"
                  "    SELECT customer_id, strftime('%Y-%m', collected_at) FROM parcels\n"
                  "    GROUP BY 1, 2 HAVING COUNT(*) = 1);"),
        trap_sql=("DELETE FROM invoices\n"
                  "WHERE paid_on IS NULL\n"
                  "  AND customer_id IN (\n"
                  "    SELECT customer_id FROM parcels\n"
                  "    GROUP BY customer_id, strftime('%Y-%m', collected_at) HAVING COUNT(*) = 1);"),
        probe_sql="SELECT COUNT(*), SUM(amount_cents), SUM(paid_on IS NULL) FROM invoices",
        note="(customer_id, period) IN (SELECT a, b ...) is true only"
             " when BOTH parts match the same row of the subquery, so"
             " an invoice is tied to its own month. Matching on the"
             " customer alone, the trap, deletes every unpaid invoice"
             " of anyone who EVER had a one-parcel month, big invoices"
             " included: 270 gone instead of 156. Before row values"
             " this needed a correlated EXISTS; both are worth"
             " recognising. Paid invoices for single parcels stay --"
             " they are history, not debts.",
        claims=[("156 cancelled: 2,142 invoices left, 176 unpaid",
                 lambda rows, c: rows[0][0] == 2142 and rows[0][2] == 176)],
    ),
    # =========================================================== 5 Procedures
    dict(
        id=13, ledger="Q1324", concept="SWAP", tier="5 - Procedures",
        kind="script",
        title="Two depots swap their couriers",
        prompt=(
            "Northgate (depot 3) and Moorside (depot 4) exchange their"
            " entire courier lists: everyone listed at one becomes"
            " listed at the other, leavers included. Two plain UPDATEs"
            " in a row will not do it -- after the first, the two"
            " groups cannot be told apart -- and the foreign key will"
            " not let anyone be parked at a depot that does not exist."
            " Remember who was where before moving anyone; a TEMP"
            " table is one place to keep it. One transaction.\n\n"
            "Checked: for depots 3 and 4: couriers listed, and the"
            " lowest courier_id among them"
        ),
        solution=("BEGIN;\n"
                  "CREATE TEMP TABLE was_northgate AS\n"
                  "  SELECT courier_id FROM couriers WHERE depot_id = 3;\n"
                  "UPDATE couriers SET depot_id = 3 WHERE depot_id = 4;\n"
                  "UPDATE couriers SET depot_id = 4\n"
                  "WHERE courier_id IN (SELECT courier_id FROM was_northgate);\n"
                  "COMMIT;"),
        trap_sql=("BEGIN;\n"
                  "UPDATE couriers SET depot_id = 4 WHERE depot_id = 3;\n"
                  "UPDATE couriers SET depot_id = 3 WHERE depot_id = 4;\n"
                  "COMMIT;"),
        probe_sql="SELECT depot_id, COUNT(*), MIN(courier_id) FROM couriers WHERE depot_id IN (3, 4) GROUP BY depot_id",
        note="A swap needs somewhere to hold one side, like swapping"
             " two glasses of water. The TEMP table is the third"
             " glass: it records Northgate's couriers before anything"
             " moves, so the last UPDATE can still find them once they"
             " share a depot_id with everyone else. The trap moves all"
             " eleven to Moorside and then all eleven back to"
             " Northgate. A single UPDATE with a CASE also works,"
             " because every row is decided from its OLD value; the"
             " steps are for when one statement will not do.",
        claims=[("six at Northgate now and five at Moorside",
                 lambda rows, c: sorted(rows) == [(3, 6, 2), (4, 5, 5)])],
    ),
    dict(
        id=14, ledger="Q1325", concept="MERGE", tier="5 - Procedures",
        kind="script",
        title="One customer, registered twice",
        prompt=(
            "Customers 67 and 201 are the same person, Dmitri Sowerby,"
            " registered twice at depot 5. (A third customer of that"
            " name, at another depot, is someone else.) Merge them into 67,"
            " in one transaction: 201's parcels become 67's; 67 takes"
            " whichever joined_on of the two is EARLIER; then 201 is"
            " deleted. The order is part of the answer -- foreign keys"
            " are on, and a deleted row can no longer be read. The"
            " question then issues a ROLLBACK: committed work"
            " survives it.\n\n"
            "Checked: customers of that name at depot 5, 67's"
            " joined_on, 67's parcels, and parcels with no customer"
        ),
        solution=("BEGIN;\n"
                  "UPDATE parcels SET customer_id = 67 WHERE customer_id = 201;\n"
                  "UPDATE customers\n"
                  "SET joined_on = (SELECT MIN(joined_on) FROM customers WHERE customer_id IN (67, 201))\n"
                  "WHERE customer_id = 67;\n"
                  "DELETE FROM customers WHERE customer_id = 201;\n"
                  "COMMIT;"),
        trap_sql=("BEGIN;\n"
                  "UPDATE parcels SET customer_id = 67 WHERE customer_id = 201;\n"
                  "DELETE FROM customers WHERE customer_id = 201;\n"
                  "UPDATE customers\n"
                  "SET joined_on = (SELECT MIN(joined_on) FROM customers WHERE customer_id IN (67, 201))\n"
                  "WHERE customer_id = 67;\n"
                  "COMMIT;"),
        driver_sql="ROLLBACK;",
        probe_sql=("SELECT (SELECT COUNT(*) FROM customers WHERE name = 'Dmitri Sowerby' AND depot_id = 5),"
                   " (SELECT joined_on FROM customers WHERE customer_id = 67),"
                   " (SELECT COUNT(*) FROM parcels WHERE customer_id = 67),"
                   " (SELECT COUNT(*) FROM parcels WHERE customer_id IS NULL)"),
        note="Children first: while a parcel still points at 201 the"
             " foreign key refuses the DELETE, so the parcels are"
             " repointed before anything else. Read before you delete:"
             " the earlier joined_on is 201's, and the trap looks for"
             " it after 201 has gone, finds only 67's own date and"
             " keeps it -- no error, just a customer who is suddenly"
             " ten months newer. Setting the parcels' customer_id to"
             " NULL would also have let the DELETE through, and turned"
             " a customer's history into walk-ins.",
        claims=[("one Dmitri Sowerby, joined 2025-01-24, with 25 parcels",
                 lambda rows, c: rows == [(1, "2025-01-24", 25, 5954)])],
    ),
    dict(
        id=15, ledger="Q1326", concept="TALLY", tier="5 - Procedures",
        kind="script",
        title="A running tally the database keeps itself",
        prompt=(
            "Counting 24,000 parcels every time someone asks is"
            " wasteful. Set up a tally in three steps: create a table"
            " depot_load with depot_id as its primary key and a"
            " required whole number parcels; fill it with the number"
            " of parcels each depot has COLLECTED so far; then create"
            " an AFTER INSERT trigger on parcels that adds one to the"
            " origin depot's row. The question then collects three"
            " new parcels, two at depot 3 and one at depot 10.\n\n"
            "Checked: every row of depot_load"
        ),
        solution=("CREATE TABLE depot_load (\n"
                  "  depot_id INTEGER PRIMARY KEY,\n"
                  "  parcels  INTEGER NOT NULL\n"
                  ");\n"
                  "INSERT INTO depot_load (depot_id, parcels)\n"
                  "SELECT origin_depot_id, COUNT(*) FROM parcels GROUP BY origin_depot_id;\n"
                  "CREATE TRIGGER tally_parcel AFTER INSERT ON parcels\n"
                  "BEGIN\n"
                  "  UPDATE depot_load SET parcels = parcels + 1 WHERE depot_id = NEW.origin_depot_id;\n"
                  "END;"),
        trap_sql=("CREATE TABLE depot_load (\n"
                  "  depot_id INTEGER PRIMARY KEY,\n"
                  "  parcels  INTEGER NOT NULL\n"
                  ");\n"
                  "INSERT INTO depot_load (depot_id, parcels)\n"
                  "SELECT origin_depot_id, COUNT(*) FROM parcels GROUP BY origin_depot_id;"),
        driver_sql=("INSERT INTO parcels (customer_id, origin_depot_id, dest_depot_id, service, weight_g, collected_at, postage_cents)"
                    " VALUES (NULL, 3, 5, 'economy', 500, '2026-07-01 09:00', 410);\n"
                    "INSERT INTO parcels (customer_id, origin_depot_id, dest_depot_id, service, weight_g, collected_at, postage_cents)"
                    " VALUES (4, 3, 3, 'express', 1200, '2026-07-01 09:20', 1200);\n"
                    "INSERT INTO parcels (customer_id, origin_depot_id, dest_depot_id, service, weight_g, collected_at, postage_cents)"
                    " VALUES (NULL, 10, 1, 'standard', 2500, '2026-07-01 10:05', 770);"),
        probe_sql="SELECT depot_id, parcels FROM depot_load",
        note="A trigger only sees what happens after it exists, so a"
             " summary table needs both halves: a one-off fill from"
             " the history, and a trigger for everything from now on."
             " The trap does the fill and stops: its numbers are right"
             " for one moment and wrong from the next parcel on, with"
             " nothing to say so. Skipping the fill instead leaves an"
             " empty table that the trigger can never start, because"
             " an UPDATE that matches no row is not an error. The"
             " tally is cheap to read and costs one small UPDATE per"
             " new parcel.",
        claims=[("ten depots, Northgate up two to 1,902",
                 lambda rows, c: len(rows) == 10 and (3, 1902) in rows),
                ("Hillcrest up one to 2,083, Central Hub unchanged at 3,365",
                 lambda rows, c: (10, 2083) in rows and (1, 3365) in rows)],
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
