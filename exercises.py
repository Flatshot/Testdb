"""Practice exercises: fifteen questions on the bike-hire schema.

A NEW schema -- a city bike-hire scheme, after the college, the workshop,
the railway, the hospital and the library -- with the library's shapes
carried over (intervals with open ends, money, three foreign keys to one
table, a NULL that means 'casual rider' rather than 'unknown') and a GRAPH
of its own: every ride is an edge from one station to another. SEED 1206.
Two tools per question, with the tiers named by task. Riding the network
-- the busiest station pairs, each station's inflow against its outflow,
a zone-to-zone matrix as JSON. Riders and fares -- the casual share by
month, casual fares banded by duration, the members who ride for free.
The fleet -- rides per bike by model with the never-ridden kept, open
maintenance jobs and whether the bike has moved since, maintenance cost
per thousand rides. Money -- missed subscription payments found by a
recursive calendar of due dates, monthly revenue split with a running
total, payment method by plan through two LEFT JOINs. And three WRITABLE
questions in two steps each:

  * a BEFORE INSERT trigger that refuses a ride on a bike already out
  * an UPDATE that closes the rides still out, with a CASE for the fare
  * a view on a view, minutes per ride then minutes per member

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
    # =================================================== 1 Riding the network
    dict(
        id=1, ledger="Q1072", concept="W2", tier="1 - Riding the network",
        title="The ten busiest routes",
        prompt=(
            "The ten most ridden station-to-station routes, counting"
            " completed rides whose start and end stations differ: start"
            " station, end station, rides -- ties by the lower start id,"
            " then end id. GROUP BY both stations, ROW_NUMBER over the"
            " counts, keep ten.\n\n"
            "Return: start_station_id, end_station_id, rides"
        ),
        solution=("SELECT start_station_id, end_station_id, n FROM ("
                  "SELECT start_station_id, end_station_id, COUNT(*) AS n,"
                  " ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC, start_station_id, end_station_id) AS rn"
                  " FROM rides WHERE end_station_id IS NOT NULL AND start_station_id <> end_station_id"
                  " GROUP BY start_station_id, end_station_id) WHERE rn <= 10"),
        trap_sql=("SELECT start_station_id, end_station_id, n FROM ("
                  "SELECT start_station_id, end_station_id, COUNT(*) AS n,"
                  " ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC, start_station_id, end_station_id) AS rn"
                  " FROM rides WHERE end_station_id IS NOT NULL"
                  " GROUP BY start_station_id, end_station_id) WHERE rn <= 10"),
        note="A route is a pair of columns, so the GROUP BY has two keys"
             " and the window ranks the pairs. The WHERE does two things:"
             " drops the rides still out, which have no end, and drops"
             " the round trips, which start and end at the same dock --"
             " a sixth of all rides, enough to push several into the top"
             " ten.",
        claims=[("ten routes, Market Square to Station Approach the busiest",
                 lambda rows, c: len(rows) == 10 and rows[0] == (1, 3, 417)
                 and all(r[0] != r[1] for r in rows))],
    ),
    dict(
        id=2, ledger="Q1073", concept="C2", tier="1 - Riding the network",
        title="Where the bikes pile up",
        prompt=(
            "For each station: rides that started there, rides that"
            " ended there, and the difference, ends minus starts -- a"
            " positive number means bikes accumulate. Rides reference"
            " stations twice, so count each direction with its own"
            " scalar subquery rather than joining rides to stations.\n\n"
            "Return: station_id, starts, ends, net"
        ),
        solution=("SELECT s.station_id, (SELECT COUNT(*) FROM rides r WHERE r.start_station_id = s.station_id),"
                  " (SELECT COUNT(*) FROM rides r WHERE r.end_station_id = s.station_id),"
                  " (SELECT COUNT(*) FROM rides r WHERE r.end_station_id = s.station_id)"
                  " - (SELECT COUNT(*) FROM rides r WHERE r.start_station_id = s.station_id) FROM stations s"),
        trap_sql=("SELECT s.station_id, COUNT(a.ride_id), COUNT(b.ride_id), COUNT(b.ride_id) - COUNT(a.ride_id)"
                  " FROM stations s LEFT JOIN rides a ON a.start_station_id = s.station_id"
                  " LEFT JOIN rides b ON b.end_station_id = s.station_id GROUP BY s.station_id"),
        note="Two foreign keys to one table are two different one-to-many"
             " relationships, and joining both multiplies them -- three"
             " thousand starts times three thousand ends is nine million"
             " rows per station. A scalar subquery per direction counts"
             " each on its own. Station Approach gains bikes; Market"
             " Square loses them.",
        claims=[("twelve stations, the nets adding up to the rides still out",
                 lambda rows, c: len(rows) == 12
                 and sum(r[3] for r in rows) == -c.execute("SELECT COUNT(*) FROM rides WHERE ended_at IS NULL").fetchone()[0])],
    ),
    dict(
        id=3, ledger="Q1074", concept="JSN", tier="1 - Riding the network",
        title="Zone to zone, as JSON",
        prompt=(
            "For each zone a ride can start in, a JSON object whose keys"
            " are the zones rides END in and whose values are the counts"
            " -- completed rides only. Join stations TWICE, under two"
            " aliases, for the start zone and the end zone; count per"
            " pair in a CTE; json_group_object grouped by the start"
            " zone.\n\n"
            "Return: start_zone, by_end_zone"
        ),
        solution=("WITH t AS (SELECT a.zone AS sz, b.zone AS ez, COUNT(*) AS n FROM rides r"
                  " JOIN stations a ON a.station_id = r.start_station_id"
                  " JOIN stations b ON b.station_id = r.end_station_id GROUP BY a.zone, b.zone)"
                  " SELECT sz, json_group_object(ez, n) FROM t GROUP BY sz"),
        trap_sql=("WITH t AS (SELECT a.zone AS sz, a.zone AS ez, COUNT(*) AS n FROM rides r"
                  " JOIN stations a ON a.station_id = r.start_station_id"
                  " JOIN stations b ON b.station_id = r.end_station_id GROUP BY a.zone, b.zone)"
                  " SELECT sz, json_group_object(ez, n) FROM t GROUP BY sz"),
        note="The same table joined twice needs two aliases, and every"
             " column must say which: a.zone is where the ride began,"
             " b.zone where it ended. Use a.zone for both and every"
             " 'end zone' is the start zone, so each JSON object has one"
             " key repeated. The inner join to b drops the rides still"
             " out, whose end station is NULL.",
        claims=[("five zones, each object naming all five",
                 lambda rows, c: len(rows) == 5
                 and all(sorted(__import__('json').loads(r[1])) == ['centre', 'east', 'north', 'south', 'west']
                         for r in rows))],
    ),
    # ==================================================== 2 Riders and fares
    dict(
        id=4, ledger="Q1075", concept="N1", tier="2 - Riders and fares",
        title="How much of each month is casual",
        prompt=(
            "For each month rides started: how many rides, and the"
            " percentage by CASUAL riders -- member_id NULL -- to one"
            " decimal. strftime for the month, AVG of member_id IS NULL"
            " for the share.\n\n"
            "Return: month, rides, pct_casual"
        ),
        solution=("SELECT strftime('%Y-%m', started_at), COUNT(*), ROUND(100.0 * AVG(member_id IS NULL), 1)"
                  " FROM rides GROUP BY 1"),
        trap_sql=("SELECT strftime('%Y-%m', started_at), COUNT(*), ROUND(100.0 * COUNT(member_id) / COUNT(*), 1)"
                  " FROM rides GROUP BY 1"),
        note="In this schema a NULL member_id is a CATEGORY -- a casual"
             " rider who paid at the dock -- not missing data, and"
             " member_id IS NULL is the test for it. COUNT(member_id)"
             " counts the rows that have one, so the trap reports the"
             " MEMBER share, around seventy, where the casual share is"
             " around thirty.",
        claims=[("eighteen months, casual share near thirty per cent",
                 lambda rows, c: len(rows) == 18 and all(25 < r[2] < 35 for r in rows))],
    ),
    dict(
        id=5, ledger="Q1076", concept="C7", tier="2 - Riders and fares",
        title="What a casual ride costs, by length",
        prompt=(
            "Completed CASUAL rides banded by length in minutes -- 'under"
            " 10', '10 to 30' (10 up to and including 30), 'over 30' --"
            " with the count and the average fare in whole cents. Minutes"
            " are (julianday(ended_at) - julianday(started_at)) * 1440;"
            " the band is a CASE with the shortest band first.\n\n"
            "Return: band, rides, avg_fare"
        ),
        solution=("SELECT CASE WHEN (julianday(ended_at) - julianday(started_at)) * 1440 < 10 THEN 'under 10'"
                  " WHEN (julianday(ended_at) - julianday(started_at)) * 1440 <= 30 THEN '10 to 30'"
                  " ELSE 'over 30' END, COUNT(*), CAST(ROUND(AVG(fare_cents)) AS INTEGER)"
                  " FROM rides WHERE member_id IS NULL AND ended_at IS NOT NULL GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN (julianday(ended_at) - julianday(started_at)) * 1440 < 10 THEN 'under 10'"
                  " WHEN (julianday(ended_at) - julianday(started_at)) * 1440 <= 30 THEN '10 to 30'"
                  " ELSE 'over 30' END, COUNT(*), CAST(ROUND(AVG(fare_cents)) AS INTEGER)"
                  " FROM rides WHERE ended_at IS NOT NULL GROUP BY 1"),
        note="julianday gives days, and 1440 minutes make a day, so the"
             " multiplication turns a timestamp difference into minutes."
             " The WHERE picks casual riders by their NULL member_id;"
             " without it the members' free half hours pull every"
             " average down by two-thirds.",
        claims=[("three bands with rising fares",
                 lambda rows, c: len(rows) == 3
                 and dict((r[0], r[2]) for r in rows)['under 10'] < dict((r[0], r[2]) for r in rows)['10 to 30']
                 < dict((r[0], r[2]) for r in rows)['over 30'])],
    ),
    dict(
        id=6, ledger="Q1077", concept="A3", tier="2 - Riders and fares",
        title="The members who ride for free",
        prompt=(
            "The ten members with the highest share of free rides -- fare"
            " 0 -- among members with at least 10 completed rides, ties by"
            " lower member_id: member_id, rides, and the free share as a"
            " percentage to one decimal. HAVING on the count, AVG of the"
            " comparison, ORDER BY and LIMIT.\n\n"
            "Return: member_id, rides, pct_free"
        ),
        solution=("SELECT member_id, COUNT(*), ROUND(100.0 * AVG(fare_cents = 0), 1) AS pct FROM rides"
                  " WHERE member_id IS NOT NULL AND ended_at IS NOT NULL GROUP BY member_id"
                  " HAVING COUNT(*) >= 10 ORDER BY pct DESC, member_id LIMIT 10"),
        trap_sql=("SELECT member_id, COUNT(*), ROUND(100 * SUM(fare_cents = 0) / COUNT(*), 1) AS pct FROM rides"
                  " WHERE member_id IS NOT NULL AND ended_at IS NOT NULL GROUP BY member_id"
                  " HAVING COUNT(*) >= 10 ORDER BY pct DESC, member_id LIMIT 10"),
        note="AVG of a comparison is the share of rows where it holds,"
             " and it is floating-point from the start. 100 * SUM / COUNT"
             " is integer arithmetic -- 100 * 9 / 10 is 90, but 100 * 9 /"
             " 11 is 81 rather than 81.8 -- and the rounding error reorders"
             " the top ten. Pay-as-you-go members never ride free, so the"
             " list is annual and monthly members.",
        claims=[("ten members, the top one entirely free",
                 lambda rows, c: len(rows) == 10 and rows[0][2] == 100.0 and all(r[1] >= 10 for r in rows))],
    ),
    # ============================================================ 3 The fleet
    dict(
        id=7, ledger="Q1078", concept="J2", tier="3 - The fleet",
        title="Rides per bike, by model",
        prompt=(
            "For each model: how many bikes, and the average rides per"
            " bike to one decimal, counting a bike that has never been"
            " ridden as 0. A LEFT JOIN from bikes to rides, COUNT of the"
            " ride id over COUNT(DISTINCT bike_id).\n\n"
            "Return: model, bikes, avg_rides"
        ),
        solution=("SELECT b.model, COUNT(DISTINCT b.bike_id), ROUND(1.0 * COUNT(r.ride_id) / COUNT(DISTINCT b.bike_id), 1)"
                  " FROM bikes b LEFT JOIN rides r ON r.bike_id = b.bike_id GROUP BY b.model"),
        trap_sql=("SELECT b.model, COUNT(DISTINCT b.bike_id), ROUND(1.0 * COUNT(r.ride_id) / COUNT(DISTINCT b.bike_id), 1)"
                  " FROM bikes b JOIN rides r ON r.bike_id = b.bike_id GROUP BY b.model"),
        note="A handful of bikes have never been ridden, and an inner join"
             " loses them, so both the bike count and the denominator"
             " come out short. The LEFT JOIN keeps each as one row with a"
             " NULL ride id, which COUNT(r.ride_id) ignores and"
             " COUNT(DISTINCT b.bike_id) does not.",
        claims=[("three models, 320 bikes, about 120 rides each",
                 lambda rows, c: len(rows) == 3 and sum(r[1] for r in rows) == 320
                 and all(110 < r[2] < 130 for r in rows))],
    ),
    dict(
        id=8, ledger="Q1079", concept="E1", tier="3 - The fleet",
        title="Jobs still open, and bikes that went out anyway",
        prompt=(
            "Every maintenance job still OPEN -- fixed_at NULL: job_id,"
            " bike_id, whole days since it was reported as of 2026-06-30"
            " 23:59, and 1 or 0 for whether the bike has started a ride"
            " SINCE the report. julianday for the days, an EXISTS over"
            " rides for the flag.\n\n"
            "Return: job_id, bike_id, days_open, ridden_since"
        ),
        solution=("SELECT job_id, bike_id, CAST(julianday('2026-06-30 23:59') - julianday(reported_at) AS INTEGER),"
                  " EXISTS (SELECT 1 FROM rides r WHERE r.bike_id = m.bike_id AND r.started_at > m.reported_at)"
                  " FROM maintenance m WHERE fixed_at IS NULL"),
        trap_sql=("SELECT job_id, bike_id, CAST(julianday('2026-06-30 23:59') - julianday(reported_at) AS INTEGER),"
                  " EXISTS (SELECT 1 FROM rides r WHERE r.bike_id = m.bike_id)"
                  " FROM maintenance m WHERE fixed_at IS NULL"),
        note="The EXISTS has to compare times: a ride that started AFTER"
             " the report is the one that matters, and every bike with"
             " an open job has been ridden at some point, so without the"
             " comparison the flag is 1 on every row. Text timestamps in"
             " this format compare correctly with >.",
        claims=[("a hundred or so open jobs, most of the bikes ridden since",
                 lambda rows, c: 100 < len(rows) < 130
                 and 0.7 < sum(r[3] for r in rows) / len(rows) < 0.95)],
    ),
    dict(
        id=9, ledger="Q1080", concept="C2", tier="3 - The fleet",
        title="Maintenance cost per thousand rides",
        prompt=(
            "For each model: the total maintenance cost of its bikes in"
            " cents, its total rides, and the cost per THOUSAND rides as"
            " a whole number. Jobs and rides are two children of a bike,"
            " so total each with its own scalar subquery over the"
            " model.\n\n"
            "Return: model, cost_cents, rides, cost_per_1000"
        ),
        solution=("SELECT b.model,"
                  " (SELECT SUM(m.cost_cents) FROM maintenance m JOIN bikes b2 ON b2.bike_id = m.bike_id WHERE b2.model = b.model),"
                  " (SELECT COUNT(*) FROM rides r JOIN bikes b2 ON b2.bike_id = r.bike_id WHERE b2.model = b.model),"
                  " CAST(ROUND(1000.0 * (SELECT SUM(m.cost_cents) FROM maintenance m JOIN bikes b2 ON b2.bike_id = m.bike_id WHERE b2.model = b.model)"
                  " / (SELECT COUNT(*) FROM rides r JOIN bikes b2 ON b2.bike_id = r.bike_id WHERE b2.model = b.model)) AS INTEGER)"
                  " FROM bikes b GROUP BY b.model"),
        trap_sql=("SELECT b.model, SUM(m.cost_cents), COUNT(r.ride_id),"
                  " CAST(ROUND(1000.0 * SUM(m.cost_cents) / COUNT(r.ride_id)) AS INTEGER)"
                  " FROM bikes b JOIN maintenance m ON m.bike_id = b.bike_id JOIN rides r ON r.bike_id = b.bike_id"
                  " GROUP BY b.model"),
        note="Joining both children to the bike repeats every job once"
             " per ride and every ride once per job, so the cost is"
             " inflated by a factor of a hundred and the ride count by"
             " the number of jobs. The grouped outer query only chooses"
             " the three models; the subqueries do the totals.",
        claims=[("three models, electrics the dearest to keep per ride",
                 lambda rows, c: len(rows) == 3
                 and max(rows, key=lambda r: r[3])[0] == 'electric'
                 and sum(r[2] for r in rows) == 38605)],
    ),
    # ================================================================ 4 Money
    dict(
        id=10, ledger="Q1081", concept="R1", tier="4 - Money",
        title="Monthly members who have missed a payment",
        prompt=(
            "A monthly member owes 1,200 cents every 30 days from the"
            " day they joined. For each monthly member who has MISSED at"
            " least one payment due between 2025-01-01 and 2026-06-30:"
            " member_id and how many due dates have no payment on that"
            " day. A recursive CTE generates each member's due dates,"
            " stepping date(d, '+30 days') from joined_on; a NOT EXISTS"
            " over payments with date(paid_at) = the due date finds the"
            " misses.\n\n"
            "Return: member_id, missed"
        ),
        solution=("WITH RECURSIVE due(member_id, d) AS (SELECT member_id, joined_on FROM members WHERE plan = 'monthly'"
                  " UNION ALL SELECT member_id, date(d, '+30 days') FROM due WHERE date(d, '+30 days') <= '2026-06-30')"
                  " SELECT member_id, SUM(NOT EXISTS (SELECT 1 FROM payments p WHERE p.member_id = due.member_id"
                  " AND date(p.paid_at) = due.d)) AS missed FROM due WHERE d >= '2025-01-01'"
                  " GROUP BY member_id HAVING missed > 0"),
        trap_sql=("WITH RECURSIVE due(member_id, d) AS (SELECT member_id, joined_on FROM members WHERE plan = 'monthly'"
                  " UNION ALL SELECT member_id, date(d, '+30 days') FROM due WHERE date(d, '+30 days') <= '2026-06-30')"
                  " SELECT member_id, SUM(NOT EXISTS (SELECT 1 FROM payments p WHERE p.member_id = due.member_id"
                  " AND p.paid_at = due.d)) AS missed FROM due WHERE d >= '2025-01-01'"
                  " GROUP BY member_id HAVING missed > 0"),
        note="A recursive CTE can carry a key along, so one recursion"
             " generates a calendar PER MEMBER: the anchor is every"
             " monthly member's joining date and the step adds thirty"
             " days until the end of the data. paid_at carries a time,"
             " so the NOT EXISTS has to compare date(paid_at) with the"
             " due date -- compared raw, no payment ever matches and"
             " every member has missed every payment.",
        claims=[("two hundred or so members, three hundred or so misses",
                 lambda rows, c: 200 < len(rows) < 240 and 300 < sum(r[1] for r in rows) < 350)],
    ),
    dict(
        id=11, ledger="Q1082", concept="W1", tier="4 - Money",
        title="Revenue by month, fares against subscriptions",
        prompt=(
            "For each month payments were made: the fare revenue --"
            " payments with a ride_id -- the subscription revenue --"
            " payments with a member_id -- and the running total of ALL"
            " revenue so far, all in cents. Two conditional SUMs and a"
            " window SUM over their total, ordered by month.\n\n"
            "Return: month, fares, subscriptions, running_total"
        ),
        solution=("SELECT strftime('%Y-%m', paid_at) AS m,"
                  " SUM(CASE WHEN ride_id IS NOT NULL THEN amount_cents ELSE 0 END),"
                  " SUM(CASE WHEN member_id IS NOT NULL THEN amount_cents ELSE 0 END),"
                  " SUM(SUM(amount_cents)) OVER (ORDER BY strftime('%Y-%m', paid_at))"
                  " FROM payments GROUP BY m"),
        trap_sql=("SELECT strftime('%Y-%m', paid_at) AS m,"
                  " SUM(CASE WHEN ride_id IS NOT NULL THEN amount_cents ELSE 0 END),"
                  " SUM(CASE WHEN member_id IS NOT NULL THEN amount_cents ELSE 0 END),"
                  " SUM(SUM(amount_cents)) OVER ()"
                  " FROM payments GROUP BY m"),
        note="Every payment names a ride or a member, never both, so the"
             " two conditional SUMs split the money cleanly and add up to"
             " the month's total. The window SUM over that total is"
             " cumulative only with its ORDER BY; OVER () is the grand"
             " total on every row.",
        claims=[("eighteen months, the last running total equal to all payments",
                 lambda rows, c: len(rows) == 18
                 and max(rows)[3] == c.execute("SELECT SUM(amount_cents) FROM payments").fetchone()[0]
                 and all(r[1] > 0 and r[2] > 0 for r in rows))],
    ),
    dict(
        id=12, ledger="Q1083", concept="J2", tier="4 - Money",
        title="Who pays by app",
        prompt=(
            "For each kind of payer -- 'annual', 'monthly',"
            " 'pay-as-you-go', or 'casual' for a fare paid by a rider with"
            " no membership: how many payments, and the percentage made by"
            " app to one decimal. A fare payment reaches its member"
            " through its ride, so LEFT JOIN rides, then LEFT JOIN members"
            " on COALESCE(payments.member_id, rides.member_id), and"
            " COALESCE(plan, 'casual') for the label.\n\n"
            "Return: payer, payments, pct_app"
        ),
        solution=("SELECT COALESCE(m.plan, 'casual'), COUNT(*), ROUND(100.0 * AVG(p.method = 'app'), 1)"
                  " FROM payments p LEFT JOIN rides r ON r.ride_id = p.ride_id"
                  " LEFT JOIN members m ON m.member_id = COALESCE(p.member_id, r.member_id) GROUP BY 1"),
        trap_sql=("SELECT COALESCE(m.plan, 'casual'), COUNT(*), ROUND(100.0 * AVG(p.method = 'app'), 1)"
                  " FROM payments p LEFT JOIN rides r ON r.ride_id = p.ride_id"
                  " LEFT JOIN members m ON m.member_id = p.member_id GROUP BY 1"),
        note="Two LEFT JOINs and two COALESCEs: the first COALESCE picks"
             " whichever of the payment's own member and the ride's"
             " member exists, the second turns a still-missing plan into"
             " the word 'casual'. Joining members on the payment's"
             " member alone labels every fare 'casual', pay-as-you-go"
             " members included.",
        claims=[("four payers, monthly members the keenest on the app",
                 lambda rows, c: len(rows) == 4 and max(rows, key=lambda r: r[2])[0] == 'monthly'
                 and dict((r[0], r[1]) for r in rows)['casual'] > 11000)],
    ),
    # ================================================= 5 Changing the data
    dict(
        id=13, ledger="Q1084", concept="TRG", tier="5 - Changing the data",
        kind="script",
        title="One rider per bike",
        prompt=(
            "Write a BEFORE INSERT trigger on rides that refuses --"
            " RAISE(ABORT, ...) -- a ride on a bike that is already OUT:"
            " a ride of the same bike with ended_at NULL exists. The"
            " question then starts a ride on bike 8, which is out, and on"
            " bike 1, which is docked.\n\n"
            "Checked: the bike_ids of any rides added"
        ),
        solution=("CREATE TRIGGER one_rider_per_bike BEFORE INSERT ON rides\n"
                  "WHEN EXISTS (SELECT 1 FROM rides r WHERE r.bike_id = NEW.bike_id AND r.ended_at IS NULL)\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'bike is already out');\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER one_rider_per_bike BEFORE INSERT ON rides\n"
                  "WHEN EXISTS (SELECT 1 FROM bikes b WHERE b.bike_id = NEW.bike_id AND b.retired_on IS NOT NULL)\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'bike is already out');\n"
                  "END;"),
        driver_sql=("INSERT INTO rides (bike_id, member_id, start_station_id, started_at) VALUES (8, NULL, 1, '2026-06-30 23:00');\n"
                    "INSERT INTO rides (bike_id, member_id, start_station_id, started_at) VALUES (1, NULL, 1, '2026-06-30 23:00');"),
        probe_sql="SELECT bike_id FROM rides WHERE ride_id > 38605 ORDER BY ride_id",
        note="The open end is the test: a ride with no ended_at is a bike"
             " still on the road, and the trigger looks for one on the"
             " same bike as NEW. Checking the bike's retirement instead"
             " is a different rule -- a sensible one, but it lets a"
             " second rider take bike 8 while the first is still riding.",
        claims=[("bike 8 refused, bike 1 lent",
                 lambda rows, c: rows == [(1,)])],
    ),
    dict(
        id=14, ledger="Q1085", concept="DML", tier="5 - Changing the data",
        kind="script",
        title="Close the rides still out at the end of the data",
        prompt=(
            "Every ride with ended_at NULL is closed at '2026-06-30"
            " 23:59', returned to its own start station, with"
            " distance_m 0 and a fare of 200 cents for a CASUAL rider"
            " (member_id NULL) or 0 for a member. One UPDATE whose SET"
            " uses the row's own start_station_id and a CASE on"
            " member_id.\n\n"
            "Checked: how many rides are still out, the fares the closed"
            " rides were charged, and how many of them end where they"
            " began"
        ),
        solution=("UPDATE rides SET ended_at = '2026-06-30 23:59', end_station_id = start_station_id, distance_m = 0,"
                  " fare_cents = CASE WHEN member_id IS NULL THEN 200 ELSE 0 END WHERE ended_at IS NULL;"),
        trap_sql=("UPDATE rides SET ended_at = '2026-06-30 23:59', end_station_id = start_station_id, distance_m = 0,"
                  " fare_cents = 200 WHERE ended_at IS NULL;"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM rides WHERE ended_at IS NULL),"
                   " (SELECT SUM(fare_cents) FROM rides WHERE ended_at = '2026-06-30 23:59'),"
                   " (SELECT COUNT(*) FROM rides WHERE ended_at = '2026-06-30 23:59' AND end_station_id = start_station_id)"),
        note="A SET can read the row it is changing -- end_station_id ="
             " start_station_id copies one column into another on each"
             " row -- and a CASE in the SET makes the fare depend on who"
             " rode. Charging 200 to everyone fines the members for a"
             " ride the scheme's own rules call free. The table's CHECK"
             " requires ended_at and end_station_id to be set together.",
        claims=[("thirty-five rides closed, eleven of them charged",
                 lambda rows, c: rows == [(0, 11 * 200, 35)])],
    ),
    dict(
        id=15, ledger="Q1086", concept="VIEW", tier="5 - Changing the data",
        kind="script",
        title="Minutes per ride, then minutes per member",
        prompt=(
            "Create a view `ride_minutes (ride_id, member_id, minutes)`"
            " of the COMPLETED rides with the ride's length in minutes --"
            " (julianday(ended_at) - julianday(started_at)) * 1440 -- then"
            " a second view `member_minutes (member_id, rides,"
            " total_minutes)` that reads ride_minutes, keeps the rows"
            " with a member, and sums per member with the total rounded"
            " to a whole number.\n\n"
            "Checked: how many members the second view holds, and member"
            " 608's rides and minutes"
        ),
        solution=("CREATE VIEW ride_minutes AS\n"
                  "  SELECT ride_id, member_id, (julianday(ended_at) - julianday(started_at)) * 1440 AS minutes\n"
                  "  FROM rides WHERE ended_at IS NOT NULL;\n"
                  "CREATE VIEW member_minutes AS\n"
                  "  SELECT member_id, COUNT(*) AS rides, CAST(ROUND(SUM(minutes)) AS INTEGER) AS total_minutes\n"
                  "  FROM ride_minutes WHERE member_id IS NOT NULL GROUP BY member_id;"),
        trap_sql=("CREATE VIEW ride_minutes AS\n"
                  "  SELECT ride_id, member_id, julianday(ended_at) - julianday(started_at) AS minutes\n"
                  "  FROM rides WHERE ended_at IS NOT NULL;\n"
                  "CREATE VIEW member_minutes AS\n"
                  "  SELECT member_id, COUNT(*) AS rides, CAST(ROUND(SUM(minutes)) AS INTEGER) AS total_minutes\n"
                  "  FROM ride_minutes WHERE member_id IS NOT NULL GROUP BY member_id;"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM member_minutes),"
                   " (SELECT rides FROM member_minutes WHERE member_id = 608),"
                   " (SELECT total_minutes FROM member_minutes WHERE member_id = 608)"),
        note="The first view fixes what a ride's length means, in"
             " minutes, and the second inherits it -- which is the point"
             " of a view on a view. Leave out the 1440 and the first view"
             " measures in DAYS: the second view's totals shrink by that"
             " factor and round to a handful, with nothing to say why.",
        claims=[("eight hundred members, 608 with 270 rides and 6,378 minutes",
                 lambda rows, c: rows == [(800, 270, 6378)])],
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
