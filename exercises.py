"""Practice exercises: fifteen questions on the bike-hire schema.

The third set on the bike scheme (SEED 1206), two tools per question, the
tiers named by task, on the tools the first two bike sets did not reach.
The fleet in motion -- speed from distance and julianday, the longest ride
per station by FIRST_VALUE, electric bikes never needing a battery by
EXCEPT. The calendar -- a recursive month spine LEFT JOINed to a closed
station's rides, month-on-month change by LAG, the week named by CASE on
strftime. Members -- riders who never start from home by two EXISTS, age
bands by CASE over julianday, each member's last three rides as JSON under
ROW_NUMBER. Money -- pay-as-you-go months dearer than a subscription by
HAVING, payment method shares by a partitioned window, subscriptions from
members who never ride by NOT EXISTS. And three WRITABLE questions in two
steps each:

  * a BEFORE UPDATE trigger that keeps a bike out on a ride in service
  * ALTER TABLE ADD COLUMN filled by a correlated UPDATE
  * an UPSERT that retires one bike and adds another in one statement

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
    # ================================================= 1 The fleet in motion
    dict(
        id=1, ledger="Q1102", concept="D1", tier="1 - The fleet in motion",
        title="How fast each model goes",
        prompt=(
            "For each bike model: completed rides, and the average speed"
            " in km/h to one decimal -- distance_m / 1000.0 over the hours"
            " from julianday, averaged per ride. A join to bikes for the"
            " model; every completed ride has a distance.\n\n"
            "Return: model, rides, avg_kmh"
        ),
        solution=("SELECT b.model, COUNT(*), ROUND(AVG(r.distance_m / 1000.0 / ((julianday(r.ended_at) - julianday(r.started_at)) * 24)), 1)"
                  " FROM rides r JOIN bikes b ON b.bike_id = r.bike_id WHERE r.ended_at IS NOT NULL GROUP BY b.model"),
        trap_sql=("SELECT b.model, COUNT(*), ROUND(AVG(r.distance_m / 1000 / ((julianday(r.ended_at) - julianday(r.started_at)) * 24)), 1)"
                  " FROM rides r JOIN bikes b ON b.bike_id = r.bike_id WHERE r.ended_at IS NOT NULL GROUP BY b.model"),
        note="distance_m is an integer, so distance_m / 1000 is integer"
             " division: a 2,850-metre ride becomes 2 km and every speed"
             " is pulled down. The 1000.0 makes the division real before"
             " it happens. Electric bikes are the quickest, cargo bikes"
             " the slowest, and the gap is wider than the trap shows.",
        claims=[("three models, electric fastest, cargo slowest",
                 lambda rows, c: len(rows) == 3
                 and max(rows, key=lambda r: r[2])[0] == 'electric'
                 and min(rows, key=lambda r: r[2])[0] == 'cargo')],
    ),
    dict(
        id=2, ledger="Q1103", concept="W1", tier="1 - The fleet in motion",
        title="The longest ride out of each station",
        prompt=(
            "For each start station, the ride_id and distance of the"
            " LONGEST ride that started there. FIRST_VALUE over a window"
            " partitioned by the start station and ordered by distance"
            " descending, with DISTINCT to keep one row per station. No"
            " station has a tie at the top.\n\n"
            "Return: station_id, ride_id, distance_m"
        ),
        solution=("SELECT DISTINCT start_station_id,"
                  " FIRST_VALUE(ride_id) OVER (PARTITION BY start_station_id ORDER BY distance_m DESC),"
                  " FIRST_VALUE(distance_m) OVER (PARTITION BY start_station_id ORDER BY distance_m DESC)"
                  " FROM rides WHERE distance_m IS NOT NULL"),
        trap_sql=("SELECT DISTINCT start_station_id,"
                  " FIRST_VALUE(ride_id) OVER (PARTITION BY start_station_id ORDER BY distance_m),"
                  " FIRST_VALUE(distance_m) OVER (PARTITION BY start_station_id ORDER BY distance_m)"
                  " FROM rides WHERE distance_m IS NOT NULL"),
        note="FIRST_VALUE returns the first row of the window as ordered,"
             " so the ORDER BY decides whether 'first' is longest or"
             " shortest -- ascending gives the shortest hop from each"
             " station. Two FIRST_VALUEs over the same window carry two"
             " columns of the same row, and DISTINCT collapses the 38,000"
             " identical copies to twelve.",
        claims=[("twelve stations, the longest from University",
                 lambda rows, c: len(rows) == 12 and max(rows, key=lambda r: r[2])[0] == 4
                 and all(r[2] > 30000 for r in rows))],
    ),
    dict(
        id=3, ledger="Q1104", concept="S1", tier="1 - The fleet in motion",
        title="Electric bikes that have never needed a battery",
        prompt=(
            "The electric bikes with no 'battery' maintenance job on"
            " record, ever: the electric bike_ids EXCEPT the bike_ids of"
            " battery jobs.\n\n"
            "Return: bike_id"
        ),
        solution=("SELECT bike_id FROM bikes WHERE model = 'electric'"
                  " EXCEPT SELECT bike_id FROM maintenance WHERE kind = 'battery'"),
        trap_sql=("SELECT bike_id FROM maintenance WHERE kind = 'battery'"
                  " EXCEPT SELECT bike_id FROM bikes WHERE model = 'electric'"),
        note="EXCEPT is not symmetric: A EXCEPT B is what is in A and not"
             " in B. Reversed, it asks for battery jobs on non-electric"
             " bikes, and there are none -- the data is consistent -- so"
             " the trap returns nothing. Fifty-nine of the eighty-two"
             " electric bikes have never had a battery fault.",
        claims=[("fifty-nine bikes",
                 lambda rows, c: len(rows) == 59)],
    ),
    # ======================================================= 2 The calendar
    dict(
        id=4, ledger="Q1105", concept="SPN", tier="2 - The calendar",
        title="Old Mill, month by month, to the end",
        prompt=(
            "Rides started at Old Mill (station 10) in EVERY month from"
            " 2025-01 to 2026-06, including the months after it closed,"
            " as 0. A recursive CTE that builds the eighteen months --"
            " strftime('%Y-%m', m || '-01', '+1 month') steps one on --"
            " LEFT JOINed to the rides, counting a ride column.\n\n"
            "Return: month, rides"
        ),
        solution=("WITH RECURSIVE cal(m) AS (SELECT '2025-01' UNION ALL SELECT strftime('%Y-%m', m || '-01', '+1 month') FROM cal WHERE m < '2026-06')"
                  " SELECT cal.m, COUNT(r.ride_id) FROM cal"
                  " LEFT JOIN rides r ON strftime('%Y-%m', r.started_at) = cal.m AND r.start_station_id = 10 GROUP BY cal.m"),
        trap_sql=("WITH RECURSIVE cal(m) AS (SELECT '2025-01' UNION ALL SELECT strftime('%Y-%m', m || '-01', '+1 month') FROM cal WHERE m < '2026-06')"
                  " SELECT cal.m, COUNT(r.ride_id) FROM cal"
                  " LEFT JOIN rides r ON strftime('%Y-%m', r.started_at) = cal.m WHERE r.start_station_id = 10 GROUP BY cal.m"),
        note="The station test belongs in the ON clause. In the WHERE it"
             " runs after the LEFT JOIN has kept the empty months with"
             " NULL rides, and NULL = 10 is not true, so those months"
             " vanish and the result is fourteen rows -- the inner join"
             " in disguise. The station closed on 2026-03-01 and its last"
             " ride is in February.",
        claims=[("eighteen months, the last four at zero",
                 lambda rows, c: len(rows) == 18 and sum(r[1] == 0 for r in rows) == 4
                 and dict(rows)['2026-02'] > 100)],
    ),
    dict(
        id=5, ledger="Q1106", concept="D1", tier="2 - The calendar",
        title="Month on month",
        prompt=(
            "For each month, the rides started, the change from the month"
            " before, and that change as a percentage of the month before"
            " to one decimal -- NULL for the first month. A grouped CTE,"
            " then LAG over it, used twice.\n\n"
            "Return: month, rides, change, pct"
        ),
        solution=("WITH m AS (SELECT strftime('%Y-%m', started_at) AS ym, COUNT(*) AS n FROM rides GROUP BY ym)"
                  " SELECT ym, n, n - LAG(n) OVER (ORDER BY ym),"
                  " ROUND(100.0 * (n - LAG(n) OVER (ORDER BY ym)) / LAG(n) OVER (ORDER BY ym), 1) FROM m"),
        trap_sql=("WITH m AS (SELECT strftime('%Y-%m', started_at) AS ym, COUNT(*) AS n FROM rides GROUP BY ym)"
                  " SELECT ym, n, n - LEAD(n) OVER (ORDER BY ym),"
                  " ROUND(100.0 * (n - LEAD(n) OVER (ORDER BY ym)) / LEAD(n) OVER (ORDER BY ym), 1) FROM m"),
        note="LAG looks back a row, LEAD looks forward: with LEAD the"
             " change is against the month AFTER and every sign flips,"
             " and the NULL lands on the last month instead of the first."
             " The percentage divides by the previous month, not the"
             " current one. February's dip and March's recovery are the"
             " biggest swings.",
        claims=[("eighteen months, the first with no change",
                 lambda rows, c: len(rows) == 18 and rows[0] == ('2025-01', 1943, None, None)
                 and min(r[3] for r in rows if r[3] is not None) < -9)],
    ),
    dict(
        id=6, ledger="Q1107", concept="C7", tier="2 - The calendar",
        title="The week, day by day",
        prompt=(
            "Rides by day of the week, with the day NAMED: strftime('%w')"
            " gives '0' for Sunday through '6' for Saturday as TEXT, and a"
            " CASE turns it into Sun, Mon, Tue, Wed, Thu, Fri, Sat. Count"
            " the rides and average the fare in whole cents.\n\n"
            "Return: dow, day, rides, avg_fare"
        ),
        solution=("SELECT strftime('%w', started_at) AS dow,"
                  " CASE strftime('%w', started_at) WHEN '0' THEN 'Sun' WHEN '1' THEN 'Mon' WHEN '2' THEN 'Tue'"
                  " WHEN '3' THEN 'Wed' WHEN '4' THEN 'Thu' WHEN '5' THEN 'Fri' ELSE 'Sat' END,"
                  " COUNT(*), CAST(ROUND(AVG(fare_cents)) AS INTEGER) FROM rides GROUP BY dow"),
        trap_sql=("SELECT strftime('%w', started_at) AS dow,"
                  " CASE strftime('%w', started_at) WHEN 0 THEN 'Sun' WHEN 1 THEN 'Mon' WHEN 2 THEN 'Tue'"
                  " WHEN 3 THEN 'Wed' WHEN 4 THEN 'Thu' WHEN 5 THEN 'Fri' ELSE 'Sat' END,"
                  " COUNT(*), CAST(ROUND(AVG(fare_cents)) AS INTEGER) FROM rides GROUP BY dow"),
        note="The simple CASE compares with =, and strftime's '0' is text"
             " that never equals the integer 0, so every WHEN misses and"
             " the ELSE names all seven days Saturday. Quote the"
             " constants. The week is flat -- commuters on weekdays,"
             " casuals at the weekend -- and Friday's fares run highest.",
        claims=[("seven days, each named once",
                 lambda rows, c: len(rows) == 7 and len({r[1] for r in rows}) == 7
                 and all(5300 < r[2] < 5700 for r in rows))],
    ),
    # ============================================================ 3 Members
    dict(
        id=7, ledger="Q1108", concept="E1", tier="3 - Members",
        title="Riders who never start from home",
        prompt=(
            "Members who HAVE ridden but have never started a ride at"
            " their own home station, counted by plan. An EXISTS for 'has"
            " ridden' and a NOT EXISTS that compares the ride's start"
            " station with the member's home station.\n\n"
            "Return: plan, members"
        ),
        solution=("SELECT plan, COUNT(*) FROM members m"
                  " WHERE EXISTS (SELECT 1 FROM rides r WHERE r.member_id = m.member_id)"
                  " AND NOT EXISTS (SELECT 1 FROM rides r WHERE r.member_id = m.member_id AND r.start_station_id = m.home_station_id)"
                  " GROUP BY plan"),
        trap_sql=("SELECT plan, COUNT(*) FROM members m"
                  " WHERE NOT EXISTS (SELECT 1 FROM rides r WHERE r.member_id = m.member_id AND r.start_station_id = m.home_station_id)"
                  " GROUP BY plan"),
        note="A member with no rides at all also has no ride from home,"
             " so the NOT EXISTS alone sweeps in the hundred who never"
             " ride and nearly doubles the counts. The EXISTS first says"
             " 'among riders'. Inside the subquery both tables are in"
             " scope, so the comparison crosses them.",
        claims=[("three plans, about a hundred members in all",
                 lambda rows, c: len(rows) == 3 and 95 < sum(r[1] for r in rows) < 115)],
    ),
    dict(
        id=8, ledger="Q1109", concept="C7", tier="3 - Members",
        title="Members by age, and how much they ride",
        prompt=(
            "Members in three age bands as of 2026-06-30 -- 'under 30',"
            " '30-49', '50+' -- with how many members and their average"
            " number of rides to one decimal. Age in years is the"
            " julianday difference divided by 365.25; CASE for the band;"
            " a scalar subquery for each member's ride count.\n\n"
            "Return: band, members, avg_rides"
        ),
        solution=("SELECT CASE WHEN (julianday('2026-06-30') - julianday(born_on)) / 365.25 < 30 THEN 'under 30'"
                  " WHEN (julianday('2026-06-30') - julianday(born_on)) / 365.25 < 50 THEN '30-49' ELSE '50+' END AS band,"
                  " COUNT(*), ROUND(AVG((SELECT COUNT(*) FROM rides r WHERE r.member_id = m.member_id)), 1)"
                  " FROM members m GROUP BY band"),
        trap_sql=("SELECT CASE WHEN 2026 - CAST(SUBSTR(born_on, 1, 4) AS INTEGER) < 30 THEN 'under 30'"
                  " WHEN 2026 - CAST(SUBSTR(born_on, 1, 4) AS INTEGER) < 50 THEN '30-49' ELSE '50+' END AS band,"
                  " COUNT(*), ROUND(AVG((SELECT COUNT(*) FROM rides r WHERE r.member_id = m.member_id)), 1)"
                  " FROM members m GROUP BY band"),
        note="Subtracting birth years counts a member born in December"
             " 1996 as 30 in June 2026, half a year early, and moves"
             " everyone with a later birthday up a band. julianday"
             " measures the actual elapsed time. The bands ride about the"
             " same -- age barely shows in this data.",
        claims=[("three bands, the over-fifties the largest",
                 lambda rows, c: len(rows) == 3 and max(rows, key=lambda r: r[1])[0] == '50+'
                 and all(28 < r[2] < 33 for r in rows))],
    ),
    dict(
        id=9, ledger="Q1110", concept="JSN", tier="3 - Members",
        title="Each member's last three rides, as JSON",
        prompt=(
            "For members 2 to 6 who have ridden: their member_id and a"
            " JSON array of the ride_ids of their three most recent rides,"
            " most recent first. ROW_NUMBER partitioned by member ordered"
            " by started_at descending in a CTE, then json_group_array"
            " with an ORDER BY of its own over the rows numbered 1 to"
            " 3.\n\n"
            "Return: member_id, last_three"
        ),
        solution=("WITH r AS (SELECT member_id, ride_id, started_at,"
                  " ROW_NUMBER() OVER (PARTITION BY member_id ORDER BY started_at DESC) AS rn"
                  " FROM rides WHERE member_id BETWEEN 2 AND 6)"
                  " SELECT member_id, json_group_array(ride_id ORDER BY started_at DESC) FROM r WHERE rn <= 3 GROUP BY member_id"),
        trap_sql=("WITH r AS (SELECT member_id, ride_id, started_at,"
                  " ROW_NUMBER() OVER (PARTITION BY member_id ORDER BY started_at DESC) AS rn"
                  " FROM rides WHERE member_id BETWEEN 2 AND 6)"
                  " SELECT member_id, json_group_array(ride_id ORDER BY started_at) FROM r WHERE rn <= 3 GROUP BY member_id"),
        note="The window's ORDER BY picks WHICH three rides; the"
             " aggregate's ORDER BY decides the order they are packed in,"
             " and JSON text is compared exactly, so oldest-first is a"
             " different answer. Members 1 and 4 have never ridden and"
             " are rightly absent.",
        claims=[("four members, three rides each",
                 lambda rows, c: len(rows) == 4 and all(r[1].count(',') == 2 for r in rows))],
    ),
    # ============================================================== 4 Money
    dict(
        id=10, ledger="Q1111", concept="A3", tier="4 - Money",
        title="Pay-as-you-go months that cost more than a subscription",
        prompt=(
            "Member-and-month pairs where a pay-as-you-go member's fares"
            " in one calendar month came to MORE than the 1200-cent"
            " monthly fee: member_id, the month, and the fares. A join to"
            " members for the plan, GROUP BY member and strftime month,"
            " HAVING on the SUM.\n\n"
            "Return: member_id, month, fares"
        ),
        solution=("SELECT m.member_id, strftime('%Y-%m', r.started_at) AS ym, SUM(r.fare_cents)"
                  " FROM rides r JOIN members m ON m.member_id = r.member_id WHERE m.plan = 'pay-as-you-go'"
                  " GROUP BY m.member_id, ym HAVING SUM(r.fare_cents) > 1200"),
        trap_sql=("SELECT m.member_id, strftime('%Y-%m', r.started_at) AS ym, SUM(r.fare_cents)"
                  " FROM rides r JOIN members m ON m.member_id = r.member_id WHERE m.plan = 'pay-as-you-go'"
                  " GROUP BY m.member_id, ym HAVING SUM(r.fare_cents) >= 1200"),
        note="'More than' is a strict >, and with fares in multiples of"
             " 50 a month of exactly 1200 is common: thirteen pairs sit"
             " on the line and >= lets them in. The plan filter is a"
             " WHERE, the total is a HAVING -- one before grouping, one"
             " after. Seventy-five members have at least one such month.",
        claims=[("two hundred and twenty-five pairs, all over 1200",
                 lambda rows, c: len(rows) == 225 and all(r[2] > 1200 for r in rows))],
    ),
    dict(
        id=11, ledger="Q1112", concept="C3", tier="4 - Money",
        title="Card or app, zone by zone",
        prompt=(
            "Members' payments by the zone of their home station and the"
            " payment method: the count and its share of that ZONE's"
            " payments as a percentage to one decimal. Two joins, GROUP"
            " BY zone and method, and a window SUM of COUNT(*)"
            " partitioned by zone for the denominator.\n\n"
            "Return: zone, method, payments, pct"
        ),
        solution=("SELECT s.zone, p.method, COUNT(*), ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY s.zone), 1)"
                  " FROM payments p JOIN members m ON m.member_id = p.member_id JOIN stations s ON s.station_id = m.home_station_id"
                  " GROUP BY s.zone, p.method"),
        trap_sql=("SELECT s.zone, p.method, COUNT(*), ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)"
                  " FROM payments p JOIN members m ON m.member_id = p.member_id JOIN stations s ON s.station_id = m.home_station_id"
                  " GROUP BY s.zone, p.method"),
        note="SUM(COUNT(*)) OVER (PARTITION BY zone) adds up the grouped"
             " counts within one zone, so each zone's two rows total 100."
             " Without the PARTITION the denominator is every payment in"
             " the city and the shares shrink to a tenth. Casual riders'"
             " payments have no member, so they drop out at the first"
             " join.",
        claims=[("ten rows, two thirds by app everywhere",
                 lambda rows, c: len(rows) == 10
                 and all(60 < r[3] < 72 for r in rows if r[1] == 'app'))],
    ),
    dict(
        id=12, ledger="Q1113", concept="X7", tier="4 - Money",
        title="Paying for nothing",
        prompt=(
            "Members who have paid a subscription but have never ridden:"
            " by plan, how many such members and the total they have"
            " paid. A join to payments, NOT EXISTS over rides, and COUNT"
            " DISTINCT of the members.\n\n"
            "Return: plan, members, paid_cents"
        ),
        solution=("SELECT m.plan, COUNT(DISTINCT m.member_id), SUM(p.amount_cents)"
                  " FROM members m JOIN payments p ON p.member_id = m.member_id"
                  " WHERE NOT EXISTS (SELECT 1 FROM rides r WHERE r.member_id = m.member_id) GROUP BY m.plan"),
        trap_sql=("SELECT m.plan, COUNT(*), SUM(p.amount_cents)"
                  " FROM members m JOIN payments p ON p.member_id = m.member_id"
                  " WHERE NOT EXISTS (SELECT 1 FROM rides r WHERE r.member_id = m.member_id) GROUP BY m.plan"),
        note="The join to payments makes one row per PAYMENT, so COUNT(*)"
             " counts monthly instalments, not people; COUNT(DISTINCT"
             " member_id) counts each member once while SUM still adds"
             " every payment. Pay-as-you-go members pay only per ride,"
             " so they cannot appear: two plans, not three.",
        claims=[("two plans, over twelve thousand dollars between them",
                 lambda rows, c: len(rows) == 2 and sum(r[2] for r in rows) > 1200000
                 and all(r[1] < 50 for r in rows))],
    ),
    # ================================================= 5 Changing the data
    dict(
        id=13, ledger="Q1114", concept="TRG", tier="5 - Changing the data",
        kind="script",
        title="A bike out on a ride cannot be retired",
        prompt=(
            "Write a BEFORE UPDATE OF retired_on trigger on bikes that"
            " refuses -- RAISE(ABORT, ...) -- when the bike has a ride"
            " still open (ended_at NULL) and the new retired_on is not"
            " NULL, and lets every other update through. The question"
            " then retires bikes 3 and 8 in one UPDATE each; bike 8 is"
            " out on a ride.\n\n"
            "Checked: bikes 3 and 8"
        ),
        solution=("CREATE TRIGGER no_retiring_out BEFORE UPDATE OF retired_on ON bikes\n"
                  "WHEN NEW.retired_on IS NOT NULL AND EXISTS (SELECT 1 FROM rides WHERE bike_id = OLD.bike_id AND ended_at IS NULL)\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'bike is out on a ride');\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER no_retiring_out BEFORE UPDATE OF retired_on ON bikes\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'bike is out on a ride');\n"
                  "END;"),
        driver_sql=("UPDATE bikes SET retired_on = '2026-06-30' WHERE bike_id = 3;\n"
                    "UPDATE bikes SET retired_on = '2026-06-30' WHERE bike_id = 8;"),
        probe_sql="SELECT bike_id, retired_on FROM bikes WHERE bike_id IN (3, 8) ORDER BY bike_id",
        note="In an UPDATE trigger OLD is the row as it was and NEW as it"
             " will be; the WHEN is what makes the refusal conditional."
             " Without it the trigger refuses every change to retired_on,"
             " and the docked bike 3 cannot be retired either. A refused"
             " statement is reported in the status bar, not treated as an"
             " error.",
        claims=[("bike 3 retired, bike 8 still in service",
                 lambda rows, c: rows == [(3, '2026-06-30'), (8, None)])],
    ),
    dict(
        id=14, ledger="Q1115", concept="ALT", tier="5 - Changing the data",
        kind="script",
        title="A ride count on every bike",
        prompt=(
            "Add an integer column `rides` to bikes with ALTER TABLE ADD"
            " COLUMN, DEFAULT 0, then fill it with each bike's number of"
            " rides by an UPDATE whose SET is a correlated subquery over"
            " rides. Bikes never ridden must end at 0.\n\n"
            "Checked: the total of the new column, how many bikes are at"
            " 0, and the largest value"
        ),
        solution=("ALTER TABLE bikes ADD COLUMN rides INTEGER NOT NULL DEFAULT 0;\n"
                  "UPDATE bikes SET rides = (SELECT COUNT(*) FROM rides r WHERE r.bike_id = bikes.bike_id);"),
        trap_sql=("ALTER TABLE bikes ADD COLUMN rides INTEGER NOT NULL DEFAULT 0;\n"
                  "UPDATE bikes SET rides = (SELECT COUNT(*) FROM rides);"),
        probe_sql="SELECT SUM(rides), SUM(rides = 0), MAX(rides) FROM bikes",
        note="The subquery has to name the outer row -- bikes.bike_id --"
             " or it is the same count for every bike: 38,605 on each of"
             " 320 rows. COUNT(*) of an empty correlated subquery is 0,"
             " which is what the seven never-ridden bikes need. ALTER"
             " TABLE ADD COLUMN is instant in SQLite; the rows are not"
             " rewritten.",
        claims=[("38,605 rides over 320 bikes, seven at zero",
                 lambda rows, c: rows == [(38605, 7, 159)])],
    ),
    dict(
        id=15, ledger="Q1116", concept="UPS", tier="5 - Changing the data",
        kind="script",
        title="Retire one bike and add another, in one statement",
        prompt=(
            "One INSERT with two VALUES rows -- (1, 'electric',"
            " '2026-06-30', '2026-06-30') and (321, 'electric',"
            " '2026-06-30', NULL) for (bike_id, model, acquired_on,"
            " retired_on) -- with ON CONFLICT (bike_id) DO UPDATE that"
            " sets ONLY retired_on from excluded. Bike 1 exists, so its"
            " row becomes an update that retires it; bike 1's own model"
            " and acquisition date must survive. Bike 321 is new.\n\n"
            "Checked: bikes 1 and 321"
        ),
        solution=("INSERT INTO bikes (bike_id, model, acquired_on, retired_on)\n"
                  "VALUES (1, 'electric', '2026-06-30', '2026-06-30'), (321, 'electric', '2026-06-30', NULL)\n"
                  "ON CONFLICT (bike_id) DO UPDATE SET retired_on = excluded.retired_on;"),
        trap_sql=("INSERT OR REPLACE INTO bikes (bike_id, model, acquired_on, retired_on)\n"
                  "VALUES (1, 'electric', '2026-06-30', '2026-06-30'), (321, 'electric', '2026-06-30', NULL);"),
        probe_sql="SELECT bike_id, model, acquired_on, retired_on FROM bikes WHERE bike_id IN (1, 321) ORDER BY bike_id",
        note="ON CONFLICT DO UPDATE touches only the columns it names, and"
             " `excluded` is the row that would have been inserted."
             " INSERT OR REPLACE deletes the old row and writes the new"
             " one whole, so bike 1 -- a classic from 2024 -- turns into"
             " an electric acquired on the day it retired.",
        claims=[("bike 1 retired as the classic it was, bike 321 new",
                 lambda rows, c: rows == [(1, 'classic', '2024-09-22', '2026-06-30'), (321, 'electric', '2026-06-30', None)])],
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
