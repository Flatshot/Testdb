"""Practice exercises: fifteen questions on the bike-hire schema.

The second set on the bike scheme (SEED 1206), two tools per question,
with the tiers named by task and the tools the first bike set did not use
brought in. Stations and docks -- the biggest station per zone through a
bare column, rides per dock ranked, bikes shared by casual riders and open
jobs by INTERSECT. Members and plans -- quartiles by NTILE with an average
fare, a plan-by-zone pivot, surnames shared within a plan. Bikes on the
road -- a bike's rides found through its index and graded on the plan, the
bikes idle longest by MAX and julianday, each bike's busiest month by
ROW_NUMBER over a grouped CTE. Time of day -- hours with a cumulative
share, weekday against weekend by two CASEs, the longest quiet spell at
each station by LAG. And three WRITABLE questions in two steps each:

  * an AFTER UPDATE trigger that prices a ride when it ends
  * a DELETE of stale maintenance reports by date arithmetic and EXISTS
  * CREATE TABLE ... AS SELECT holding a window function

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script.

The query-plan question carries `plan_requires` / `plan_forbids`, checked
against EXPLAIN QUERY PLAN, and a `starter_sql` that opens in the editor:
correct, slow, and the thing to improve.
"""

import sqlite3

EXERCISES = [
    # ================================================= 1 Stations and docks
    dict(
        id=1, ledger="Q1087", concept="BARE", tier="1 - Stations and docks",
        title="The biggest station in each zone",
        prompt=(
            "For each zone: the name and dock count of its station with"
            " the most docks. MAX(docks) with name as a bare column --"
            " SQLite brings the name from the row the MAX came from. No"
            " zone has a tie.\n\n"
            "Return: zone, name, docks"
        ),
        solution="SELECT zone, name, MAX(docks) FROM stations GROUP BY zone",
        trap_sql="SELECT zone, name, MIN(docks) FROM stations GROUP BY zone",
        note="SQLite's bare-column rule: beside a single MAX or MIN, a"
             " column that is neither grouped nor aggregated comes from"
             " the row the extreme was found in. MIN gives the smallest"
             " station in each zone instead. Postgres would refuse the"
             " query outright.",
        claims=[("five zones, Market Square the biggest in the centre",
                 lambda rows, c: len(rows) == 5 and ('centre', 'Market Square', 40) in rows)],
    ),
    dict(
        id=2, ledger="Q1088", concept="W2", tier="1 - Stations and docks",
        title="Rides per dock, ranked",
        prompt=(
            "For each station: its docks, the rides that have started"
            " there, rides per dock to one decimal, and the station's"
            " place by that ratio, 1 for the hardest-worked. A scalar"
            " subquery for the starts, and DENSE_RANK over the ratio.\n\n"
            "Return: station_id, docks, starts, per_dock, place"
        ),
        solution=("SELECT station_id, docks, (SELECT COUNT(*) FROM rides r WHERE r.start_station_id = s.station_id),"
                  " ROUND((SELECT COUNT(*) FROM rides r WHERE r.start_station_id = s.station_id) * 1.0 / docks, 1),"
                  " DENSE_RANK() OVER (ORDER BY (SELECT COUNT(*) FROM rides r WHERE r.start_station_id = s.station_id) * 1.0 / docks DESC)"
                  " FROM stations s"),
        trap_sql=("SELECT station_id, docks, (SELECT COUNT(*) FROM rides r WHERE r.start_station_id = s.station_id),"
                  " ROUND((SELECT COUNT(*) FROM rides r WHERE r.start_station_id = s.station_id) * 1.0 / docks, 1),"
                  " DENSE_RANK() OVER (ORDER BY (SELECT COUNT(*) FROM rides r WHERE r.start_station_id = s.station_id) DESC)"
                  " FROM stations s"),
        note="A window can rank by any expression, including one built"
             " from a scalar subquery. Ranking by the raw count puts the"
             " forty-dock Market Square first; per dock it is nearly"
             " last, and little Hilltop with sixteen docks works hardest."
             " The * 1.0 keeps the ratio from being integer division.",
        claims=[("twelve stations, Hilltop first per dock, Market Square near last",
                 lambda rows, c: len(rows) == 12
                 and min(rows, key=lambda r: r[4])[0] == 6
                 and dict((r[0], r[4]) for r in rows)[1] >= 11)],
    ),
    dict(
        id=3, ledger="Q1089", concept="S1", tier="1 - Stations and docks",
        title="Bikes casual riders have used that also need fixing",
        prompt=(
            "Bikes that have been ridden by a CASUAL rider -- a ride with"
            " member_id NULL -- AND have a maintenance job still open:"
            " INTERSECT between a query over rides and one over"
            " maintenance, each bike once.\n\n"
            "Return: bike_id"
        ),
        solution=("SELECT bike_id FROM rides WHERE member_id IS NULL"
                  " INTERSECT SELECT bike_id FROM maintenance WHERE fixed_at IS NULL"),
        trap_sql=("SELECT bike_id FROM rides WHERE member_id IS NULL"
                  " UNION SELECT bike_id FROM maintenance WHERE fixed_at IS NULL"),
        note="INTERSECT keeps the bikes both queries name; UNION keeps the"
             " bikes either names, which is almost the whole fleet, since"
             " nearly every bike has carried a casual rider. Both remove"
             " duplicates, so a bike with a hundred casual rides is one"
             " row.",
        claims=[("a hundred or so bikes",
                 lambda rows, c: 80 < len(rows) < 115)],
    ),
    # ================================================== 2 Members and plans
    dict(
        id=4, ledger="Q1090", concept="W2", tier="2 - Members and plans",
        title="Riders in quartiles, and what they pay",
        prompt=(
            "Split the members who have completed rides into four equal"
            " groups by ride count, quartile 1 the LIGHTEST riders: for"
            " each quartile, the smallest and largest ride count in it"
            " and their average fare per ride in whole cents. A CTE per member with the count and the average,"
            " NTILE(4) over it, then a GROUP BY the tile.\n\n"
            "Return: quartile, min_rides, max_rides, avg_fare"
        ),
        solution=("WITH per AS (SELECT member_id, COUNT(*) AS n, AVG(fare_cents) AS f FROM rides"
                  " WHERE member_id IS NOT NULL AND ended_at IS NOT NULL GROUP BY member_id),"
                  " t AS (SELECT n, f, NTILE(4) OVER (ORDER BY n) AS q FROM per)"
                  " SELECT q, MIN(n), MAX(n), CAST(ROUND(AVG(f)) AS INTEGER) FROM t GROUP BY q"),
        trap_sql=("WITH per AS (SELECT member_id, COUNT(*) AS n, AVG(fare_cents) AS f FROM rides"
                  " WHERE member_id IS NOT NULL AND ended_at IS NOT NULL GROUP BY member_id),"
                  " t AS (SELECT n, f, NTILE(4) OVER (ORDER BY n DESC) AS q FROM per)"
                  " SELECT q, MIN(n), MAX(n), CAST(ROUND(AVG(f)) AS INTEGER) FROM t GROUP BY q"),
        note="NTILE(4) deals the ordered rows into four equal bands;"
             " ORDER BY n ascending makes band 1 the lightest riders,"
             " and DESC reverses the bands. The average fare is an"
             " average of per-member averages, which is what 'their"
             " average fare per ride' asks for -- the heaviest riders"
             " pay least per ride, because regulars keep inside the"
             " free half hour.",
        claims=[("four quartiles, the heaviest paying least per ride",
                 lambda rows, c: len(rows) == 4
                 and dict((r[0], r[3]) for r in rows)[1] > dict((r[0], r[3]) for r in rows)[4]
                 and dict((r[0], r[2]) for r in rows)[4] > 200)],
    ),
    dict(
        id=5, ledger="Q1091", concept="C7", tier="2 - Members and plans",
        title="Plans by home zone, as a pivot",
        prompt=(
            "For each plan, one row with the number of members whose home"
            " station is in each zone, as five columns: centre, north,"
            " south, east, west. A join to stations for the zone, and SUM"
            " over a comparison for each column.\n\n"
            "Return: plan, centre, north, south, east, west"
        ),
        solution=("SELECT m.plan, SUM(s.zone = 'centre'), SUM(s.zone = 'north'), SUM(s.zone = 'south'),"
                  " SUM(s.zone = 'east'), SUM(s.zone = 'west')"
                  " FROM members m JOIN stations s ON s.station_id = m.home_station_id GROUP BY m.plan"),
        trap_sql=("SELECT m.plan, COUNT(CASE WHEN s.zone = 'centre' THEN 1 ELSE 0 END),"
                  " COUNT(CASE WHEN s.zone = 'north' THEN 1 ELSE 0 END), COUNT(CASE WHEN s.zone = 'south' THEN 1 ELSE 0 END),"
                  " COUNT(CASE WHEN s.zone = 'east' THEN 1 ELSE 0 END), COUNT(CASE WHEN s.zone = 'west' THEN 1 ELSE 0 END)"
                  " FROM members m JOIN stations s ON s.station_id = m.home_station_id GROUP BY m.plan"),
        note="A pivot is one conditional SUM per column: SUM(zone ="
             " 'centre') adds a 1 for each match. COUNT with an ELSE 0"
             " counts the zeros too -- COUNT counts non-NULL values and 0"
             " is a value -- so every column equals the plan's total."
             " The zone lives on the station, hence the join.",
        claims=[("three plans, the five columns adding up to 900",
                 lambda rows, c: len(rows) == 3 and sum(sum(r[1:]) for r in rows) == 900
                 and all(len(set(r[1:])) > 1 for r in rows))],
    ),
    dict(
        id=6, ledger="Q1092", concept="STR", tier="2 - Members and plans",
        title="Surnames shared within a plan",
        prompt=(
            "Plan-and-surname pairs where MORE THAN ONE member on that"
            " plan has that surname -- the surname being the part of"
            " name after the space: plan, surname, how many members."
            " GROUP BY the plan and the SUBSTR together, HAVING COUNT(*)"
            " > 1.\n\n"
            "Return: plan, surname, members"
        ),
        solution=("SELECT plan, SUBSTR(name, INSTR(name, ' ') + 1) AS surname, COUNT(*) FROM members"
                  " GROUP BY plan, surname HAVING COUNT(*) > 1"),
        trap_sql=("SELECT plan, SUBSTR(name, INSTR(name, ' ') + 1) AS surname, COUNT(*) FROM members"
                  " GROUP BY surname HAVING COUNT(*) > 1"),
        note="Grouping by a plain column and a computed one together"
             " makes the group 'this plan, this surname'; grouping by the"
             " surname alone collapses the plans into twenty-five groups"
             " with an arbitrary plan each. With twenty-five surnames and"
             " nine hundred members, nearly every pair repeats.",
        claims=[("seventy-five pairs, every surname many times over",
                 lambda rows, c: len(rows) == 75 and all(r[2] > 1 for r in rows)
                 and len({r[0] for r in rows}) == 3)],
    ),
    # ==================================================== 3 Bikes on the road
    dict(
        id=7, ledger="Q1093", concept="X5", tier="3 - Bikes on the road",
        title="Bike 7's rides, through the index",
        prompt=(
            "Every ride of bike 7: ride_id and started_at. The query in"
            " the editor is correct and reads all 38,000 rides, because"
            " it wraps bike_id in arithmetic. There is an index on"
            " rides(bike_id, started_at); write the WHERE on the bare"
            " column so it is searched. Your plan must say SEARCH with"
            " idx_rides_bike.\n\n"
            "Return: ride_id, started_at"
        ),
        starter_sql="SELECT ride_id, started_at FROM rides WHERE bike_id + 0 = 7",
        solution="SELECT ride_id, started_at FROM rides WHERE bike_id = 7",
        trap_sql="SELECT ride_id, started_at FROM rides WHERE CAST(bike_id AS TEXT) = '7'",
        note="The index is on the column as stored; arithmetic or a CAST"
             " around it makes an expression the index cannot be searched"
             " for, and SQLite reads every row. The index holds"
             " started_at too, and ride_id is the rowid, so the plan says"
             " COVERING: the table is never opened.",
        plan_requires=("SEARCH rides USING COVERING INDEX idx_rides_bike",),
        plan_forbids=("SCAN",),
        claims=[("a hundred and forty-eight rides",
                 lambda rows, c: len(rows) == 148)],
    ),
    dict(
        id=8, ledger="Q1094", concept="D1", tier="3 - Bikes on the road",
        title="The bikes that have sat longest",
        prompt=(
            "The ten in-service bikes -- not retired, not out on a ride --"
            " that have waited longest since their last ride ended, as of"
            " 2026-06-30 23:59: bike_id and the days idle to one decimal,"
            " ties by lower bike_id. MAX(ended_at) per bike, julianday"
            " for the gap, a NOT EXISTS for 'not out', ORDER BY and"
            " LIMIT.\n\n"
            "Return: bike_id, days_idle"
        ),
        solution=("SELECT b.bike_id, ROUND(julianday('2026-06-30 23:59') - julianday(MAX(r.ended_at)), 1) AS d"
                  " FROM bikes b JOIN rides r ON r.bike_id = b.bike_id"
                  " WHERE b.retired_on IS NULL AND NOT EXISTS (SELECT 1 FROM rides o WHERE o.bike_id = b.bike_id AND o.ended_at IS NULL)"
                  " GROUP BY b.bike_id ORDER BY d DESC, b.bike_id LIMIT 10"),
        trap_sql=("SELECT b.bike_id, ROUND(julianday('2026-06-30 23:59') - julianday(MAX(r.started_at)), 1) AS d"
                  " FROM bikes b JOIN rides r ON r.bike_id = b.bike_id"
                  " WHERE b.retired_on IS NULL AND NOT EXISTS (SELECT 1 FROM rides o WHERE o.bike_id = b.bike_id AND o.ended_at IS NULL)"
                  " GROUP BY b.bike_id ORDER BY d DESC, b.bike_id LIMIT 10"),
        note="Idle time runs from the END of the last ride, so the MAX is"
             " of ended_at; measured from the last start the figures are"
             " a ride's length too big and the order shifts. The NOT"
             " EXISTS keeps the bikes currently out off the list -- their"
             " MAX(ended_at) ignores the open ride and would make them"
             " look idle.",
        claims=[("ten bikes, the top one idle over two weeks",
                 lambda rows, c: len(rows) == 10 and rows[0][1] > 14 and rows[0][0] == 156)],
    ),
    dict(
        id=9, ledger="Q1095", concept="W2", tier="3 - Bikes on the road",
        title="Each bike's busiest month",
        prompt=(
            "For bikes 1 to 10: the month in which each started the most"
            " rides, and how many -- ties to the earlier month. A CTE of"
            " rides per bike and month, ROW_NUMBER partitioned by bike"
            " ordered by rides descending then month, keep rank 1.\n\n"
            "Return: bike_id, month, rides"
        ),
        solution=("WITH m AS (SELECT bike_id, strftime('%Y-%m', started_at) AS ym, COUNT(*) AS n FROM rides"
                  " WHERE bike_id <= 10 GROUP BY bike_id, ym),"
                  " r AS (SELECT bike_id, ym, n, ROW_NUMBER() OVER (PARTITION BY bike_id ORDER BY n DESC, ym) AS rn FROM m)"
                  " SELECT bike_id, ym, n FROM r WHERE rn = 1"),
        trap_sql=("WITH m AS (SELECT bike_id, strftime('%Y-%m', started_at) AS ym, COUNT(*) AS n FROM rides"
                  " WHERE bike_id <= 10 GROUP BY bike_id, ym),"
                  " r AS (SELECT bike_id, ym, n, ROW_NUMBER() OVER (ORDER BY n DESC, ym) AS rn FROM m)"
                  " SELECT bike_id, ym, n FROM r WHERE rn = 1"),
        note="PARTITION BY bike_id restarts the numbering for each bike,"
             " so each has a rank 1; without it one month across all ten"
             " bikes is number 1 and the result is a single row. The"
             " month in the ORDER BY settles ties, which are common with"
             " counts around ten.",
        claims=[("ten bikes, one busiest month each",
                 lambda rows, c: len(rows) == 10 and len({r[0] for r in rows}) == 10
                 and all(r[2] >= 10 for r in rows))],
    ),
    # ======================================================== 4 Time of day
    dict(
        id=10, ledger="Q1096", concept="W1", tier="4 - Time of day",
        title="Rides by hour, and the share of the day so far",
        prompt=(
            "For each hour of the day -- strftime's %H -- how many rides"
            " started in it, and the cumulative percentage of all rides"
            " started by the end of that hour, to one decimal. A running"
            " window SUM over the grouped counts, divided by the total.\n\n"
            "Return: hour, rides, cum_pct"
        ),
        solution=("SELECT strftime('%H', started_at) AS h, COUNT(*),"
                  " ROUND(100.0 * SUM(COUNT(*)) OVER (ORDER BY strftime('%H', started_at)) / (SELECT COUNT(*) FROM rides), 1)"
                  " FROM rides GROUP BY h"),
        trap_sql=("SELECT strftime('%H', started_at) AS h, COUNT(*),"
                  " ROUND(100.0 * SUM(COUNT(*)) OVER () / (SELECT COUNT(*) FROM rides), 1)"
                  " FROM rides GROUP BY h"),
        note="The hour is text, '00' to '23', which sorts correctly as"
             " text because of the leading zero -- so the window can"
             " ORDER BY it. The ORDER BY is what makes the SUM cumulative;"
             " without it every hour shows 100. Almost nothing happens"
             " before six, and the morning hours carry the day.",
        claims=[("twenty-four hours, climbing to a hundred",
                 lambda rows, c: len(rows) == 24 and max(rows)[2] == 100.0
                 and dict((r[0], r[2]) for r in rows)['05'] < 1)],
    ),
    dict(
        id=11, ledger="Q1097", concept="C7", tier="4 - Time of day",
        title="Weekday or weekend, member or casual",
        prompt=(
            "Completed rides in four groups -- weekday or weekend by the"
            " start day, member or casual by member_id -- with the count"
            " and the average length in minutes to one decimal. Two"
            " CASEs, one on strftime('%w') tested against the TEXT"
            " values '0' and '6', one on member_id IS NULL.\n\n"
            "Return: day_type, rider, rides, avg_minutes"
        ),
        solution=("SELECT CASE WHEN strftime('%w', started_at) IN ('0', '6') THEN 'weekend' ELSE 'weekday' END,"
                  " CASE WHEN member_id IS NULL THEN 'casual' ELSE 'member' END, COUNT(*),"
                  " ROUND(AVG((julianday(ended_at) - julianday(started_at)) * 1440), 1)"
                  " FROM rides WHERE ended_at IS NOT NULL GROUP BY 1, 2"),
        trap_sql=("SELECT CASE WHEN strftime('%w', started_at) IN (0, 6) THEN 'weekend' ELSE 'weekday' END,"
                  " CASE WHEN member_id IS NULL THEN 'casual' ELSE 'member' END, COUNT(*),"
                  " ROUND(AVG((julianday(ended_at) - julianday(started_at)) * 1440), 1)"
                  " FROM rides WHERE ended_at IS NOT NULL GROUP BY 1, 2"),
        note="strftime returns text, and in SQLite '0' never equals the"
             " integer 0, so IN (0, 6) matches nothing and every ride is"
             " a weekday -- two groups instead of four, and no error."
             " Two CASEs in the GROUP BY cross the two splits into four"
             " cells.",
        claims=[("four cells, weekdays the busier",
                 lambda rows, c: len(rows) == 4 and sum(r[2] for r in rows) == 38570
                 and all(20 < r[3] < 25 for r in rows))],
    ),
    dict(
        id=12, ledger="Q1098", concept="W3", tier="4 - Time of day",
        title="The longest quiet spell at each station",
        prompt=(
            "For each station, the longest gap in hours between one ride"
            " starting there and the next, to one decimal. LAG over"
            " started_at partitioned by the start station in a CTE,"
            " julianday times 24 for hours, then MAX per station.\n\n"
            "Return: station_id, max_gap_hours"
        ),
        solution=("WITH g AS (SELECT start_station_id AS s, (julianday(started_at)"
                  " - julianday(LAG(started_at) OVER (PARTITION BY start_station_id ORDER BY started_at))) * 24 AS h FROM rides)"
                  " SELECT s, ROUND(MAX(h), 1) FROM g GROUP BY s"),
        trap_sql=("WITH g AS (SELECT start_station_id AS s, (julianday(started_at)"
                  " - julianday(LAG(started_at) OVER (ORDER BY started_at))) * 24 AS h FROM rides)"
                  " SELECT s, ROUND(MAX(h), 1) FROM g GROUP BY s"),
        note="The gap at a station is between consecutive starts AT THAT"
             " STATION, so the window is partitioned by it; unpartitioned,"
             " LAG reaches the previous ride anywhere in the city and the"
             " gaps shrink to minutes. The window runs in the CTE because"
             " MAX of a window needs two steps.",
        claims=[("twelve stations, every longest gap over a day",
                 lambda rows, c: len(rows) == 12 and all(24 < r[1] < 200 for r in rows))],
    ),
    # ================================================= 5 Changing the data
    dict(
        id=13, ledger="Q1099", concept="TRG", tier="5 - Changing the data",
        kind="script",
        title="Price the ride when it ends",
        prompt=(
            "Write an AFTER UPDATE OF ended_at trigger on rides that sets"
            " the ride's fare_cents when ended_at is set: minutes are"
            " (julianday(NEW.ended_at) - julianday(NEW.started_at)) *"
            " 1440; a CASUAL rider (member_id NULL) pays 200 plus 50 per"
            " started 10 minutes; a member pays 100 per started 15"
            " minutes beyond the first 30, else 0. 'Per started' means"
            " rounded UP: (minutes + 9) / 10 in integer arithmetic. The"
            " question then ends ride 1253 (casual) and ride 884 (a"
            " member), both 75 minutes long.\n\n"
            "Checked: the two rides' fares"
        ),
        solution=("CREATE TRIGGER price_on_end AFTER UPDATE OF ended_at ON rides\n"
                  "WHEN NEW.ended_at IS NOT NULL\n"
                  "BEGIN\n"
                  "  UPDATE rides SET fare_cents = CASE\n"
                  "    WHEN NEW.member_id IS NULL THEN 200 + 50 * ((CAST((julianday(NEW.ended_at) - julianday(NEW.started_at)) * 1440 AS INTEGER) + 9) / 10)\n"
                  "    ELSE 100 * ((MAX(CAST((julianday(NEW.ended_at) - julianday(NEW.started_at)) * 1440 AS INTEGER) - 30, 0) + 14) / 15)\n"
                  "  END WHERE ride_id = NEW.ride_id;\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER price_on_end AFTER UPDATE OF ended_at ON rides\n"
                  "WHEN NEW.ended_at IS NOT NULL\n"
                  "BEGIN\n"
                  "  UPDATE rides SET fare_cents = CASE\n"
                  "    WHEN NEW.member_id IS NULL THEN 200 + 50 * (CAST((julianday(NEW.ended_at) - julianday(NEW.started_at)) * 1440 AS INTEGER) / 10)\n"
                  "    ELSE 100 * (MAX(CAST((julianday(NEW.ended_at) - julianday(NEW.started_at)) * 1440 AS INTEGER) - 30, 0) / 15)\n"
                  "  END WHERE ride_id = NEW.ride_id;\n"
                  "END;"),
        driver_sql=("UPDATE rides SET ended_at = '2026-06-30 20:10', end_station_id = 5, distance_m = 3000 WHERE ride_id = 1253;\n"
                    "UPDATE rides SET ended_at = '2026-06-30 20:04', end_station_id = 5, distance_m = 3000 WHERE ride_id = 884;"),
        probe_sql="SELECT ride_id, fare_cents FROM rides WHERE ride_id IN (884, 1253) ORDER BY ride_id",
        note="An AFTER UPDATE trigger may UPDATE the row that fired it --"
             " by its key, from NEW -- and a CASE in the SET prices by"
             " who rode. 'Per started ten minutes' is a ceiling, and"
             " integer division floors: 75 / 10 is 7, where the eighth"
             " block has been started. Adding 9 before dividing is the"
             " integer way to round up.",
        claims=[("the casual ride 600 cents, the member's 300",
                 lambda rows, c: rows == [(884, 300), (1253, 600)])],
    ),
    dict(
        id=14, ledger="Q1100", concept="DML", tier="5 - Changing the data",
        kind="script",
        title="Clear the stale repair reports",
        prompt=(
            "Delete the maintenance jobs that are still OPEN, were"
            " reported more than 90 days before 2026-06-30 23:59, AND"
            " whose bike has started a ride since the report -- the"
            " problem evidently did not stop it. julianday for the age,"
            " a correlated EXISTS for the ride.\n\n"
            "Checked: how many jobs remain, and how many of them are open"
        ),
        solution=("DELETE FROM maintenance WHERE fixed_at IS NULL"
                  " AND julianday('2026-06-30 23:59') - julianday(reported_at) > 90"
                  " AND EXISTS (SELECT 1 FROM rides r WHERE r.bike_id = maintenance.bike_id AND r.started_at > maintenance.reported_at);"),
        trap_sql=("DELETE FROM maintenance WHERE fixed_at IS NULL"
                  " AND julianday('2026-06-30 23:59') - julianday(reported_at) > 90;"),
        probe_sql="SELECT COUNT(*), SUM(fixed_at IS NULL) FROM maintenance",
        note="Three conditions, and the EXISTS is the one that says"
             " 'stale' rather than merely 'old': an old open job on a"
             " bike that has not moved since is a bike waiting for a"
             " mechanic, and must stay. Inside the subquery the table"
             " being deleted from is referred to by its own name.",
        claims=[("seventy-seven stale reports gone, the rest kept",
                 lambda rows, c: rows == [(1100 - 77, 114 - 77)])],
    ),
    dict(
        id=15, ledger="Q1101", concept="DDL", tier="5 - Changing the data",
        kind="script",
        title="A league table of stations",
        prompt=(
            "Create a table `station_rank (station_id, starts, place)`"
            " with CREATE TABLE ... AS SELECT: every station's rides"
            " STARTED there and its place by that count, 1 for the most,"
            " RANK over the grouped counts. Rides are grouped by their"
            " start station.\n\n"
            "Checked: the table's rows"
        ),
        solution=("CREATE TABLE station_rank AS\n"
                  "  SELECT start_station_id AS station_id, COUNT(*) AS starts,\n"
                  "         RANK() OVER (ORDER BY COUNT(*) DESC) AS place\n"
                  "  FROM rides GROUP BY start_station_id;"),
        trap_sql=("CREATE TABLE station_rank AS\n"
                  "  SELECT end_station_id AS station_id, COUNT(*) AS starts,\n"
                  "         RANK() OVER (ORDER BY COUNT(*) DESC) AS place\n"
                  "  FROM rides WHERE end_station_id IS NOT NULL GROUP BY end_station_id;"),
        probe_sql="SELECT station_id, starts, place FROM station_rank ORDER BY place, station_id",
        note="CREATE TABLE AS SELECT can hold a window function, and the"
             " result is an ordinary table -- no view, no recomputation."
             " Starts and ends are different counts of the same rides:"
             " Market Square has the most starts, Station Approach the"
             " most ends, and the table has to say which it holds.",
        claims=[("twelve stations, Market Square first",
                 lambda rows, c: len(rows) == 12 and rows[0] == (1, 3834, 1))],
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
