"""Practice exercises: fifteen questions on the parcel-courier schema.

The second set on the courier scheme (SEED 1241), two tools per question,
the tiers named by task, on tools the first courier set left out, with
prompts that name the tool but do not write the statement. Trails and
gaps -- the parcels whose latest scan is a failure by a correlated MAX,
how many scans a trail has by an aggregate of an aggregate, the longest
quiet spell at each depot by LAG partitioned. Depots and regions -- a
depot-by-month grid with its zeros by CROSS JOIN and LEFT JOIN, each
depot's share of its region by a window partitioned, the busiest hour at
each depot by ROW_NUMBER with a tiebreak. Customers and money -- two
aggregates in one HAVING, days to pay by method over the paid invoices,
June's postage not yet billed by NOT EXISTS on two columns. People and
vehicles -- tenure with COALESCE for the couriers still here, a new
courier's first thirty days with the condition in ON, the busiest courier
at each depot by SQLite's bare column beside MAX. And three WRITABLE
questions:

  * a view of the lost parcels
  * an UPSERT that corrects one invoice and creates another
  * a column added and then filled by an UPDATE

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference.
"""

import sqlite3

EXERCISES = [
    # ====================================================== 1 Trails and gaps
    dict(
        id=1, ledger="Q1237", concept="LASTFAIL", tier="1 - Trails and gaps",
        title="The parcels that were never heard of again",
        prompt=(
            "For each service: how many parcels have a FAILED attempt as"
            " the latest scan in their trail -- lost, as far as the data"
            " knows. The latest scan is the one whose time equals the"
            " parcel's maximum, found by a correlated subquery; a"
            " parcel that failed once and was delivered later does not"
            " count.\n\n"
            "Return: service, lost"
        ),
        solution=("SELECT p.service, COUNT(*) FROM parcels p JOIN scans s ON s.parcel_id = p.parcel_id"
                  " WHERE s.scanned_at = (SELECT MAX(x.scanned_at) FROM scans x WHERE x.parcel_id = p.parcel_id)"
                  " AND s.status = 'failed' GROUP BY p.service"),
        trap_sql=("SELECT p.service, COUNT(*) FROM parcels p"
                  " WHERE EXISTS (SELECT 1 FROM scans s WHERE s.parcel_id = p.parcel_id AND s.status = 'failed')"
                  " GROUP BY p.service"),
        note="'The latest scan' is the greatest-n-per-group problem: a"
             " subquery finds each parcel's last time, and the join keeps"
             " the scan that has it. Asking whether a failure exists"
             " ANYWHERE in the trail, the trap, counts the 3,345 parcels"
             " that came back to the depot and were mostly delivered the"
             " next day. 113 parcels end on a failure, and those are the"
             " ones to chase.",
        claims=[("three services, 113 lost parcels in all",
                 lambda rows, c: len(rows) == 3 and sum(r[1] for r in rows) == 113),
                ("economy loses the most",
                 lambda rows, c: max(rows, key=lambda r: r[1])[0] == "economy")],
    ),
    dict(
        id=2, ledger="Q1238", concept="HIST", tier="1 - Trails and gaps",
        title="How long a trail is",
        prompt=(
            "How many parcels have a trail of 1 scan, of 2, of 3, and"
            " so on: one row per trail length. Count the scans per"
            " parcel first, then count the parcels per count -- an"
            " aggregate of an aggregate, in two layers.\n\n"
            "Return: scans, parcels"
        ),
        solution="SELECT n, COUNT(*) FROM (SELECT COUNT(*) AS n FROM scans GROUP BY parcel_id) GROUP BY n",
        trap_sql="SELECT n, SUM(n) FROM (SELECT COUNT(*) AS n FROM scans GROUP BY parcel_id) GROUP BY n",
        note="The inner query turns 112,000 scans into 24,000 counts,"
             " one per parcel; the outer query groups THOSE. SUM(n) in"
             " the outer layer, the trap, adds the scans back up and"
             " reports 17,961 for the three-scan parcels instead of"
             " 5,987. Three scans is a local parcel, five is a plain"
             " journey, seven is one failed attempt, nine is two; the"
             " trails of one or two are parcels the data's end cut"
             " short.",
        claims=[("six lengths, 15592 five-scan trails",
                 lambda rows, c: len(rows) == 6 and (5, 15592) in rows),
                ("parcels add up to 24000",
                 lambda rows, c: sum(r[1] for r in rows) == 24000)],
    ),
    dict(
        id=3, ledger="Q1239", concept="QUIET", tier="1 - Trails and gaps",
        title="The longest quiet spell at each depot",
        prompt=(
            "For every depot: the longest gap in hours between two"
            " consecutive collections there, to one decimal, and the"
            " average gap. The previous collection at the SAME depot"
            " comes from a window function that looks one row back,"
            " partitioned by depot and ordered by time, in a CTE.\n\n"
            "Return: name, longest_gap_h, avg_gap_h"
        ),
        solution=("WITH w AS (SELECT origin_depot_id AS d, collected_at,"
                  " LAG(collected_at) OVER (PARTITION BY origin_depot_id ORDER BY collected_at) AS prev FROM parcels)"
                  " SELECT dp.name, ROUND(MAX((julianday(collected_at) - julianday(prev)) * 24), 1),"
                  " ROUND(AVG((julianday(collected_at) - julianday(prev)) * 24), 1)"
                  " FROM w JOIN depots dp ON dp.depot_id = w.d GROUP BY dp.name"),
        trap_sql=("WITH w AS (SELECT origin_depot_id AS d, collected_at,"
                  " LAG(collected_at) OVER (ORDER BY collected_at) AS prev FROM parcels)"
                  " SELECT dp.name, ROUND(MAX((julianday(collected_at) - julianday(prev)) * 24), 1),"
                  " ROUND(AVG((julianday(collected_at) - julianday(prev)) * 24), 1)"
                  " FROM w JOIN depots dp ON dp.depot_id = w.d GROUP BY dp.name"),
        note="PARTITION BY makes LAG look back within the depot; without"
             " it, the trap's previous row is the previous collection"
             " ANYWHERE in the network, usually minutes earlier, and"
             " every gap shrinks. The first collection at each depot has"
             " no predecessor, so its NULL gap is skipped by MAX and AVG."
             " Nowhere goes quiet for three days; the small depots"
             " average six or seven hours between parcels.",
        claims=[("ten depots, every longest gap between 40 and 70 hours",
                 lambda rows, c: len(rows) == 10 and all(40 <= r[1] <= 70 for r in rows)),
                ("Millbank the steadiest",
                 lambda rows, c: min(rows, key=lambda r: r[2])[0] == "Millbank")],
    ),
    # ================================================== 2 Depots and regions
    dict(
        id=4, ledger="Q1240", concept="GRID", tier="2 - Depots and regions",
        title="Every depot, every month of 2026, zeros included",
        prompt=(
            "For every depot and every month of 2026 in the data: how"
            " many parcels were collected there, with 0 where there"
            " were none. A CROSS JOIN of the depots and the distinct"
            " months builds the full grid of sixty; a LEFT JOIN of"
            " parcels fills it, and a count of a parcels column gives"
            " the zeros.\n\n"
            "Return: name, month, parcels"
        ),
        solution=("SELECT d.name, m.mo, COUNT(p.parcel_id) FROM depots d"
                  " CROSS JOIN (SELECT DISTINCT strftime('%Y-%m', collected_at) AS mo FROM parcels WHERE collected_at >= '2026-01-01') m"
                  " LEFT JOIN parcels p ON p.origin_depot_id = d.depot_id AND strftime('%Y-%m', p.collected_at) = m.mo"
                  " GROUP BY d.name, m.mo"),
        trap_sql=("SELECT d.name, strftime('%Y-%m', p.collected_at), COUNT(*) FROM parcels p JOIN depots d ON d.depot_id = p.origin_depot_id"
                  " WHERE p.collected_at >= '2026-01-01' GROUP BY d.name, strftime('%Y-%m', p.collected_at)"),
        note="A GROUP BY can only report the combinations that occur, so"
             " Old Foundry's months after its closure simply are not"
             " there: the trap returns 55 rows and a chart would draw the"
             " depot as if it had never closed. The CROSS JOIN makes all"
             " sixty cells first, the LEFT JOIN finds the parcels for the"
             " ones that have them, and COUNT(p.parcel_id) -- not"
             " COUNT(*) -- is 0 where nothing matched.",
        claims=[("sixty cells, five of them zero",
                 lambda rows, c: len(rows) == 60 and sum(r[2] == 0 for r in rows) == 5),
                ("every zero is Old Foundry after January",
                 lambda rows, c: all(r[0] == "Old Foundry" and r[1] >= "2026-02" for r in rows if r[2] == 0))],
    ),
    dict(
        id=5, ledger="Q1241", concept="PART", tier="2 - Depots and regions",
        title="Each depot's share of its region",
        prompt=(
            "For every depot: its region, its collections, and its"
            " share of its REGION's collections as a percentage to one"
            " decimal. Count per depot in a CTE, then a window SUM"
            " partitioned by region for the denominator.\n\n"
            "Return: region, name, parcels, region_pct"
        ),
        solution=("WITH per AS (SELECT d.region, d.name, COUNT(*) AS n FROM parcels p JOIN depots d ON d.depot_id = p.origin_depot_id GROUP BY d.depot_id)"
                  " SELECT region, name, n, ROUND(100.0 * n / SUM(n) OVER (PARTITION BY region), 1) FROM per"),
        trap_sql=("WITH per AS (SELECT d.region, d.name, COUNT(*) AS n FROM parcels p JOIN depots d ON d.depot_id = p.origin_depot_id GROUP BY d.depot_id)"
                  " SELECT region, name, n, ROUND(100.0 * n / SUM(n) OVER (), 1) FROM per"),
        note="SUM(n) OVER (PARTITION BY region) is the region's total on"
             " every row of that region, so each depot's share is one"
             " division with no second query. The trap's empty OVER ()"
             " totals the whole network and every share drops to ten or"
             " fifteen per cent. Central Hub takes seven tenths of the"
             " centre; the other regions split roughly in half.",
        claims=[("ten depots, Central Hub 69.3 of the centre",
                 lambda rows, c: len(rows) == 10 and ("central", "Central Hub", 3365, 69.3) in rows),
                ("each region's shares add to a hundred",
                 lambda rows, c: all(abs(sum(r[3] for r in rows if r[0] == z) - 100) < 0.2 for z in {r[0] for r in rows}))],
    ),
    dict(
        id=6, ledger="Q1242", concept="TOP1", tier="2 - Depots and regions",
        title="The busiest hour at each depot's counter",
        prompt=(
            "For every depot: the hour of the day ('08' to '17') in"
            " which the most parcels were handed in, and how many. A"
            " CTE of parcels per depot and hour, then ROW_NUMBER"
            " partitioned by depot, ordered by the count descending with"
            " the hour as a tiebreak, keeping number 1.\n\n"
            "Return: name, hour, parcels"
        ),
        solution=("WITH h AS (SELECT origin_depot_id AS d, strftime('%H', collected_at) AS hr, COUNT(*) AS n FROM parcels GROUP BY origin_depot_id, strftime('%H', collected_at)),"
                  " r AS (SELECT d, hr, n, ROW_NUMBER() OVER (PARTITION BY d ORDER BY n DESC, hr) AS rn FROM h)"
                  " SELECT dp.name, r.hr, r.n FROM r JOIN depots dp ON dp.depot_id = r.d WHERE r.rn = 1"),
        trap_sql=("WITH h AS (SELECT origin_depot_id AS d, strftime('%H', collected_at) AS hr, COUNT(*) AS n FROM parcels GROUP BY origin_depot_id, strftime('%H', collected_at)),"
                  " r AS (SELECT d, hr, n, ROW_NUMBER() OVER (ORDER BY n DESC, hr) AS rn FROM h)"
                  " SELECT dp.name, r.hr, r.n FROM r JOIN depots dp ON dp.depot_id = r.d WHERE r.rn = 1"),
        note="Top-one-per-group is the window pattern: number the rows"
             " within each group in the order you care about and keep"
             " number 1. Without PARTITION BY the numbering runs across"
             " all depots and the trap returns a single row, the busiest"
             " hour anywhere. The tiebreak on the hour makes the answer"
             " reproducible if two hours ever tie. Counters are busiest"
             " mid-morning or late afternoon; nowhere peaks at lunch.",
        claims=[("ten depots, Millbank's five o'clock the biggest",
                 lambda rows, c: len(rows) == 10 and max(rows, key=lambda r: r[2]) == ("Millbank", "17", 364)),
                ("no depot peaks at noon",
                 lambda rows, c: all(r[1] != "12" for r in rows))],
    ),
    # ================================================ 3 Customers and money
    dict(
        id=7, ledger="Q1243", concept="HAV", tier="3 - Customers and money",
        title="Big senders who pay well",
        prompt=(
            "The customers who have sent more than 60 parcels AND whose"
            " average postage is above 700 cents: name, parcels, average"
            " postage in whole cents. Both conditions are on aggregates,"
            " so both belong in one HAVING, joined by AND.\n\n"
            "Return: name, parcels, avg_postage"
        ),
        solution=("SELECT c.name, COUNT(*), ROUND(AVG(p.postage_cents)) FROM parcels p JOIN customers c ON c.customer_id = p.customer_id"
                  " GROUP BY c.customer_id HAVING COUNT(*) > 60 AND AVG(p.postage_cents) > 700"),
        trap_sql=("SELECT c.name, COUNT(*), ROUND(AVG(p.postage_cents)) FROM parcels p JOIN customers c ON c.customer_id = p.customer_id"
                  " GROUP BY c.customer_id HAVING COUNT(*) > 60 OR AVG(p.postage_cents) > 700"),
        note="HAVING takes any expression over the group's aggregates,"
             " so two tests combine there just as two tests combine in"
             " WHERE. OR instead of AND, the trap, admits anyone who"
             " passes EITHER test -- 435 customers, most of them small"
             " senders who happened to post something heavy. Twenty-five"
             " customers pass both: all of them businesses, each with"
             " hundreds of parcels.",
        claims=[("25 customers, every one a big sender",
                 lambda rows, c: len(rows) == 25 and all(r[1] > 200 for r in rows)),
                ("every average above 700",
                 lambda rows, c: all(r[2] > 700 for r in rows))],
    ),
    dict(
        id=8, ledger="Q1244", concept="PAYLAG", tier="3 - Customers and money",
        title="How quickly invoices get paid, by method",
        prompt=(
            "For each payment method: the invoices paid that way, the"
            " average days from issue to payment to one decimal, and"
            " how many took more than 30 days. Paid invoices only --"
            " the unpaid ones have NULL in both the method and the"
            " date, and would make a group of their own.\n\n"
            "Return: method, paid, avg_days, over_30"
        ),
        solution=("SELECT method, COUNT(*), ROUND(AVG(julianday(paid_on) - julianday(issued_on)), 1),"
                  " SUM(julianday(paid_on) - julianday(issued_on) > 30)"
                  " FROM invoices WHERE paid_on IS NOT NULL GROUP BY method"),
        trap_sql=("SELECT method, COUNT(*), ROUND(AVG(julianday(paid_on) - julianday(issued_on)), 1),"
                  " SUM(julianday(paid_on) - julianday(issued_on) > 30)"
                  " FROM invoices GROUP BY method"),
        note="GROUP BY puts every NULL into one group, so without the"
             " WHERE the trap returns a third row, method NULL, 332"
             " invoices, average NULL: the unpaid ones, which have no"
             " days to count. The WHERE on paid_on IS NOT NULL is the"
             " question's 'paid invoices only' in SQL. Cards and"
             " transfers are paid at the same pace, a little over three"
             " weeks, and a third of each take more than thirty days.",
        claims=[("two methods, no NULL row",
                 lambda rows, c: len(rows) == 2 and all(r[0] is not None for r in rows)),
                ("1966 paid invoices",
                 lambda rows, c: sum(r[1] for r in rows) == 1966)],
    ),
    dict(
        id=9, ledger="Q1245", concept="NOTBILLED", tier="3 - Customers and money",
        title="June's postage, not yet on a bill",
        prompt=(
            "June 2026's invoices are not out yet. For the ten business"
            " customers with the most June postage outstanding: name,"
            " June parcels, and the postage in cents -- counting only"
            " customers who do NOT already have an invoice for the"
            " period '2026-06'. A NOT EXISTS on two columns, customer"
            " and period; order by the postage, then by customer_id.\n\n"
            "Return: name, june_parcels, postage_cents"
        ),
        solution=("SELECT c.name, COUNT(*), SUM(p.postage_cents) FROM parcels p JOIN customers c ON c.customer_id = p.customer_id"
                  " WHERE c.kind = 'business' AND p.collected_at >= '2026-06-01'"
                  " AND NOT EXISTS (SELECT 1 FROM invoices i WHERE i.customer_id = c.customer_id AND i.period = '2026-06')"
                  " GROUP BY c.customer_id ORDER BY SUM(p.postage_cents) DESC, c.customer_id LIMIT 10"),
        trap_sql=("SELECT c.name, COUNT(*), SUM(p.postage_cents) FROM parcels p JOIN customers c ON c.customer_id = p.customer_id"
                  " WHERE p.collected_at >= '2026-06-01'"
                  " AND NOT EXISTS (SELECT 1 FROM invoices i WHERE i.customer_id = c.customer_id AND i.period = '2026-06')"
                  " GROUP BY c.customer_id ORDER BY SUM(p.postage_cents) DESC, c.customer_id LIMIT 10"),
        note="NOT EXISTS can correlate on as many columns as the"
             " question needs -- here the customer AND the month -- which"
             " is how 'no invoice for this period' is asked. The trap"
             " forgets that only businesses are invoiced and lists"
             " personal customers, who pay at the counter and will never"
             " get a bill. No June invoice exists yet, so every business"
             " that sent in June is outstanding; the biggest owe about"
             " 140 dollars.",
        claims=[("ten customers, every one a business",
                 lambda rows, c: len(rows) == 10 and all(c.execute("SELECT kind FROM customers WHERE name = ?", (r[0],)).fetchone()[0] == "business" for r in rows)),
                ("Papadopoulos Bicycles first with 14820",
                 lambda rows, c: max(rows, key=lambda r: r[2]) == ("Papadopoulos Bicycles & Co", 18, 14820))],
    ),
    # ================================================= 4 People and vehicles
    dict(
        id=10, ledger="Q1246", concept="COAL", tier="4 - People and vehicles",
        title="How long couriers stay",
        prompt=(
            "For each vehicle type: its couriers, how many have left,"
            " and the average days of service to the nearest whole day"
            " -- to the day they left, or to 2026-06-30 for those still"
            " here. A fallback for the NULL leaving date, inside"
            " julianday.\n\n"
            "Return: vehicle, couriers, left, avg_days"
        ),
        solution=("SELECT vehicle, COUNT(*), SUM(left_on IS NOT NULL),"
                  " ROUND(AVG(julianday(COALESCE(left_on, '2026-06-30')) - julianday(hired_on)))"
                  " FROM couriers GROUP BY vehicle"),
        trap_sql=("SELECT vehicle, COUNT(*), SUM(left_on IS NOT NULL),"
                  " ROUND(AVG(julianday(left_on) - julianday(hired_on)))"
                  " FROM couriers GROUP BY vehicle"),
        note="julianday(NULL) is NULL and AVG skips NULLs, so the trap"
             " averages only the couriers who have LEFT -- the shortest"
             " careers -- and calls that everyone's service. COALESCE"
             " supplies the data's end date for the rest, and the"
             " average covers all sixty. Bike couriers have been here"
             " longest, over five years on average.",
        claims=[("three vehicles, sixty couriers, fifteen gone",
                 lambda rows, c: len(rows) == 3 and sum(r[1] for r in rows) == 60 and sum(r[2] for r in rows) == 15),
                ("bike couriers the longest serving",
                 lambda rows, c: max(rows, key=lambda r: r[3])[0] == "bike")],
    ),
    dict(
        id=11, ledger="Q1247", concept="FIRST30", tier="4 - People and vehicles",
        title="A new courier's first month",
        prompt=(
            "For each courier hired since the data began (2025 on):"
            " their name, hire date, and how many parcels they"
            " delivered in their first 30 days. The 30-day test uses a"
            " date modifier on the hire date, and it belongs in the"
            " LEFT JOIN's ON clause so that a courier with no such"
            " delivery still appears with 0.\n\n"
            "Return: name, hired_on, first_month_deliveries"
        ),
        solution=("SELECT c.name, c.hired_on, COUNT(p.parcel_id) FROM couriers c"
                  " LEFT JOIN parcels p ON p.courier_id = c.courier_id AND p.delivered_at < date(c.hired_on, '+30 days')"
                  " WHERE c.hired_on >= '2025-01-01' GROUP BY c.courier_id"),
        trap_sql=("SELECT c.name, c.hired_on, COUNT(p.parcel_id) FROM couriers c"
                  " LEFT JOIN parcels p ON p.courier_id = c.courier_id AND p.delivered_at < c.hired_on + 30"
                  " WHERE c.hired_on >= '2025-01-01' GROUP BY c.courier_id"),
        note="date(x, '+30 days') is date arithmetic; '2025-11-20' + 30"
             " is NOT -- SQLite turns the text into the number 2025, adds"
             " 30, and compares a timestamp with 2055, which is true for"
             " every delivery, so the trap counts the courier's whole"
             " career. The condition sits in ON rather than WHERE so"
             " that the LEFT JOIN keeps a courier who delivered nothing"
             " in the first month; as it happens, all nine did.",
        claims=[("nine couriers, each with 13 to 30 first-month deliveries",
                 lambda rows, c: len(rows) == 9 and all(13 <= r[2] <= 30 for r in rows)),
                ("Leila Dalgleish the quickest start",
                 lambda rows, c: max(rows, key=lambda r: r[2])[0] == "Leila Dalgleish")],
    ),
    dict(
        id=12, ledger="Q1248", concept="BARE", tier="4 - People and vehicles",
        title="The top courier at each depot",
        prompt=(
            "For every depot: the courier based there with the most"
            " deliveries, and the count. SQLite has a shortcut here: in"
            " a query that groups by depot and takes MAX of the count,"
            " a bare column such as the courier's name is taken from"
            " the row that held the maximum. Count per courier in a"
            " CTE first.\n\n"
            "Return: depot, courier, deliveries"
        ),
        solution=("WITH per AS (SELECT c.depot_id, c.name, COUNT(p.parcel_id) AS n FROM couriers c LEFT JOIN parcels p ON p.courier_id = c.courier_id GROUP BY c.courier_id)"
                  " SELECT d.name, per.name, MAX(per.n) FROM per JOIN depots d ON d.depot_id = per.depot_id GROUP BY per.depot_id"),
        trap_sql=("WITH per AS (SELECT c.depot_id, c.name, COUNT(p.parcel_id) AS n FROM couriers c LEFT JOIN parcels p ON p.courier_id = c.courier_id GROUP BY c.courier_id)"
                  " SELECT d.name, per.name, per.n FROM per JOIN depots d ON d.depot_id = per.depot_id GROUP BY per.depot_id"),
        note="When a SELECT has exactly one MIN or MAX aggregate, SQLite"
             " takes any bare column from the row where that extreme was"
             " found -- a documented shortcut, and not portable. With no"
             " MAX at all, the trap's bare columns come from whichever"
             " row SQLite happened to visit last, which is some courier,"
             " not the busiest. The portable answer is ROW_NUMBER"
             " partitioned by depot, as in question 6.",
        claims=[("ten depots, each courier's count the depot's maximum",
                 lambda rows, c: len(rows) == 10 and all(r[2] == c.execute("SELECT MAX(n) FROM (SELECT COUNT(p.parcel_id) n FROM couriers c LEFT JOIN parcels p ON p.courier_id = c.courier_id WHERE c.depot_id = (SELECT depot_id FROM depots WHERE name = ?) GROUP BY c.courier_id)", (r[0],)).fetchone()[0] for r in rows)),
                ("the busiest of all delivers over a thousand",
                 lambda rows, c: max(r[2] for r in rows) > 1000)],
    ),
    # =================================================== 5 Changing the data
    dict(
        id=13, ledger="Q1249", concept="VIEW", tier="5 - Changing the data",
        kind="script",
        title="A view of the lost parcels",
        prompt=(
            "Create a view named lost_parcels holding every column of"
            " parcels for the parcels that are not delivered AND whose"
            " latest scan is a failed attempt -- the same 'latest scan'"
            " test as question 1, inside the view's definition.\n\n"
            "Checked: how many rows the view has, and how many of them"
            " are economy"
        ),
        solution=("CREATE VIEW lost_parcels AS\n"
                  "SELECT p.* FROM parcels p\n"
                  "WHERE p.delivered_at IS NULL\n"
                  "  AND (SELECT s.status FROM scans s WHERE s.parcel_id = p.parcel_id ORDER BY s.scanned_at DESC LIMIT 1) = 'failed';"),
        trap_sql=("CREATE VIEW lost_parcels AS\n"
                  "SELECT p.* FROM parcels p\n"
                  "WHERE EXISTS (SELECT 1 FROM scans s WHERE s.parcel_id = p.parcel_id AND s.status = 'failed');"),
        probe_sql="SELECT COUNT(*), SUM(service = 'economy') FROM lost_parcels",
        note="A view is a saved query: it costs nothing to create, runs"
             " its SELECT whenever it is read, and gives a name to a"
             " definition that would otherwise be copied into every"
             " report. The trap's view holds every parcel that ever"
             " failed an attempt, 3,345 of them, delivered or not. A"
             " correlated subquery with ORDER BY and LIMIT 1 is another"
             " way to reach 'the latest scan'.",
        claims=[("113 lost parcels, 64 of them economy",
                 lambda rows, c: rows == [(113, 64)])],
    ),
    dict(
        id=14, ledger="Q1250", concept="UPSERT", tier="5 - Changing the data",
        kind="script",
        title="One invoice corrected, one created, in one statement",
        prompt=(
            "Two invoices for the period '2026-05', both issued on"
            " 2026-06-01: customer 4's, which exists and must be"
            " corrected to 2500 cents, and customer 8's, which does"
            " not exist and must be created at 1200 cents. ONE INSERT"
            " with two rows and an ON CONFLICT clause on the"
            " (customer_id, period) key that updates the amount instead"
            " of failing -- an upsert.\n\n"
            "Checked: the two amounts, how many invoices there are, and"
            " the highest invoice_id"
        ),
        solution=("INSERT INTO invoices (customer_id, period, amount_cents, issued_on)"
                  " VALUES (4, '2026-05', 2500, '2026-06-01'), (8, '2026-05', 1200, '2026-06-01')"
                  " ON CONFLICT (customer_id, period) DO UPDATE SET amount_cents = excluded.amount_cents;"),
        trap_sql=("INSERT OR REPLACE INTO invoices (customer_id, period, amount_cents, issued_on)"
                  " VALUES (4, '2026-05', 2500, '2026-06-01'), (8, '2026-05', 1200, '2026-06-01');"),
        probe_sql=("SELECT (SELECT amount_cents FROM invoices WHERE customer_id = 4 AND period = '2026-05'),"
                   " (SELECT amount_cents FROM invoices WHERE customer_id = 8 AND period = '2026-05'),"
                   " (SELECT COUNT(*) FROM invoices), (SELECT MAX(invoice_id) FROM invoices)"),
        note="ON CONFLICT (...) DO UPDATE is the upsert: the row is"
             " inserted if its key is new and updated in place if the"
             " key exists, and `excluded` names the row that could not"
             " be inserted. INSERT OR REPLACE, the trap, DELETES the"
             " existing invoice and inserts a new one, so customer 4's"
             " invoice gets a new id -- the highest id ends at 2300"
             " instead of 2299 -- and would lose any paid_on it had. The"
             " UNIQUE (customer_id, period) constraint is what the"
             " conflict target names.",
        claims=[("4 corrected in place, 8 created",
                 lambda rows, c: rows == [(2500, 1200, 2299, 2299)])],
    ),
    dict(
        id=15, ledger="Q1251", concept="ADDCOL", tier="5 - Changing the data",
        kind="script",
        title="A flag column, added and filled",
        prompt=(
            "Add an integer column is_local to parcels, NOT NULL with a"
            " default of 0, then set it to 1 for every parcel whose"
            " origin and destination depots are the same. Two"
            " statements: an ALTER TABLE and an UPDATE.\n\n"
            "Checked: how many parcels are flagged, and how many there"
            " are"
        ),
        solution=("ALTER TABLE parcels ADD COLUMN is_local INTEGER NOT NULL DEFAULT 0;\n"
                  "UPDATE parcels SET is_local = 1 WHERE origin_depot_id = dest_depot_id;"),
        trap_sql="ALTER TABLE parcels ADD COLUMN is_local INTEGER NOT NULL DEFAULT 0;",
        probe_sql="SELECT SUM(is_local), COUNT(*) FROM parcels",
        note="ADD COLUMN with a DEFAULT fills every existing row at"
             " once, which is why NOT NULL is allowed; the UPDATE then"
             " overwrites the default where the rule says so. The trap"
             " adds the column and stops, leaving every flag at 0. A"
             " generated column -- GENERATED ALWAYS AS (origin_depot_id"
             " = dest_depot_id) -- would keep itself right as rows"
             " change, which a filled column will not.",
        claims=[("6900 local parcels flagged",
                 lambda rows, c: rows == [(6900, 24000)])],
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
