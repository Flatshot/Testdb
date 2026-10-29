"""Practice exercises: fifteen questions on the bike-hire schema.

The fourth set on the bike scheme (SEED 1206), two tools per question, the
tiers named by task, on tools no bike set has used. Streaks and spells --
each bike's longest run of consecutive days by the gaps-and-islands trick,
a seven-day moving average by a ROWS frame, the first and last ride of
every month by FIRST_VALUE and LAST_VALUE with the frame opened. Labels
and text -- station names packed by GROUP_CONCAT with an ORDER BY, a
district with a zone as fallback by COALESCE, fares printed as dollars by
FORMAT. Counting with conditions -- a casual share by FILTER, the members
never named on a payment by NOT EXISTS where NOT IN would return nothing,
the ride count at the ninetieth percentile by CUME_DIST. The fleet's
calendar -- cargo bikes in order of arrival through a named WINDOW, weeks
that start on Monday by date modifiers, bike ages with COALESCE for the
bikes still in service. And three WRITABLE questions in two steps each:

  * a VIRTUAL generated column of minutes added to rides
  * a new table whose CHECK and REFERENCES turn bad rows away
  * a TEMP table of retired bikes, then a DELETE through it

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
    # ================================================= 1 Streaks and spells
    dict(
        id=1, ledger="Q1117", concept="GAP", tier="1 - Streaks and spells",
        title="Each bike's longest run of days in use",
        prompt=(
            "For bikes 1 to 10: the most CONSECUTIVE days on which the"
            " bike started at least one ride. The gaps-and-islands trick:"
            " a CTE of DISTINCT bike-and-day pairs, then date(day, '-' ||"
            " ROW_NUMBER() OVER (PARTITION BY bike_id ORDER BY day) || '"
            " days') as a group key that is the same for every day of a"
            " run, COUNT per group, MAX per bike.\n\n"
            "Return: bike_id, longest_run"
        ),
        solution=("WITH d AS (SELECT DISTINCT bike_id, date(started_at) AS day FROM rides WHERE bike_id <= 10),"
                  " g AS (SELECT bike_id, date(day, '-' || ROW_NUMBER() OVER (PARTITION BY bike_id ORDER BY day) || ' days') AS grp FROM d),"
                  " s AS (SELECT bike_id, COUNT(*) AS len FROM g GROUP BY bike_id, grp)"
                  " SELECT bike_id, MAX(len) FROM s GROUP BY bike_id"),
        trap_sql=("WITH d AS (SELECT bike_id, date(started_at) AS day FROM rides WHERE bike_id <= 10),"
                  " g AS (SELECT bike_id, date(day, '-' || ROW_NUMBER() OVER (PARTITION BY bike_id ORDER BY day) || ' days') AS grp FROM d),"
                  " s AS (SELECT bike_id, COUNT(*) AS len FROM g GROUP BY bike_id, grp)"
                  " SELECT bike_id, MAX(len) FROM s GROUP BY bike_id"),
        note="The trick needs ONE row per day: a day minus its row number"
             " is constant along a run only when the numbers step with"
             " the days. Two rides on one day give it two numbers, the"
             " key drifts, and every run breaks into pieces -- hence the"
             " DISTINCT. None of these ten manages more than five days"
             " running; the fleet's record is eight.",
        claims=[("ten bikes, the best run five days",
                 lambda rows, c: len(rows) == 10 and max(r[1] for r in rows) == 5
                 and min(r[1] for r in rows) == 2)],
    ),
    dict(
        id=2, ledger="Q1118", concept="W1", tier="1 - Streaks and spells",
        title="A week's average, rolling",
        prompt=(
            "For each day of June 2026: the rides started that day and the"
            " average over that day and the six before it, to one decimal."
            " A CTE of rides per day over ALL days, AVG with ROWS BETWEEN"
            " 6 PRECEDING AND CURRENT ROW, and the filter to June applied"
            " OUTSIDE, so that June 1st can see the end of May.\n\n"
            "Return: day, rides, avg_7d"
        ),
        solution=("WITH d AS (SELECT date(started_at) AS day, COUNT(*) AS n FROM rides GROUP BY day),"
                  " w AS (SELECT day, n, ROUND(AVG(n) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 1) AS a FROM d)"
                  " SELECT day, n, a FROM w WHERE day >= '2026-06-01'"),
        trap_sql=("WITH d AS (SELECT date(started_at) AS day, COUNT(*) AS n FROM rides WHERE started_at >= '2026-06-01' GROUP BY day)"
                  " SELECT day, n, ROUND(AVG(n) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING AND CURRENT ROW), 1) FROM d"),
        note="A window sees only the rows that reach it. Filter to June"
             " first and the first six days average over a shortened"
             " week -- June 1st over itself alone. Compute the window"
             " over every day and filter afterwards, in an outer query,"
             " since a WHERE on the same level runs before the window.",
        claims=[("thirty days, June 1st already a full week's average",
                 lambda rows, c: len(rows) == 30 and rows[0][0] == '2026-06-01'
                 and rows[0][2] != rows[0][1] and all(50 < r[2] < 80 for r in rows))],
    ),
    dict(
        id=3, ledger="Q1119", concept="W1", tier="1 - Streaks and spells",
        title="The first and last ride of every month",
        prompt=(
            "For each month: the ride_id of the first ride started in it"
            " and of the last. FIRST_VALUE and LAST_VALUE over a window"
            " partitioned by month and ordered by started_at, with the"
            " frame opened to ROWS BETWEEN UNBOUNDED PRECEDING AND"
            " UNBOUNDED FOLLOWING, and DISTINCT.\n\n"
            "Return: month, first_ride, last_ride"
        ),
        solution=("SELECT DISTINCT strftime('%Y-%m', started_at) AS m,"
                  " FIRST_VALUE(ride_id) OVER (PARTITION BY strftime('%Y-%m', started_at) ORDER BY started_at"
                  " ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING),"
                  " LAST_VALUE(ride_id) OVER (PARTITION BY strftime('%Y-%m', started_at) ORDER BY started_at"
                  " ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) FROM rides"),
        trap_sql=("SELECT DISTINCT strftime('%Y-%m', started_at) AS m,"
                  " FIRST_VALUE(ride_id) OVER (PARTITION BY strftime('%Y-%m', started_at) ORDER BY started_at),"
                  " LAST_VALUE(ride_id) OVER (PARTITION BY strftime('%Y-%m', started_at) ORDER BY started_at) FROM rides"),
        note="With an ORDER BY and no frame, a window runs from the start"
             " of the partition to the CURRENT row, so LAST_VALUE is"
             " always the row itself and DISTINCT leaves 38,000 rows."
             " UNBOUNDED FOLLOWING opens the frame to the whole month."
             " Ride ids are issued per bike, not in time order, so the"
             " first ride of January is number 34,693.",
        claims=[("eighteen months, January starting with ride 34693",
                 lambda rows, c: len(rows) == 18 and ('2025-01', 34693, 6117) in rows)],
    ),
    # ==================================================== 2 Labels and text
    dict(
        id=4, ledger="Q1120", concept="G1", tier="2 - Labels and text",
        title="The stations of each zone, in one cell",
        prompt=(
            "For each zone: how many stations, and their names in one"
            " text, alphabetical, separated by ', '. GROUP_CONCAT with a"
            " separator and an ORDER BY inside the brackets.\n\n"
            "Return: zone, stations, names"
        ),
        solution="SELECT zone, COUNT(*), GROUP_CONCAT(name, ', ' ORDER BY name) FROM stations GROUP BY zone",
        trap_sql="SELECT zone, COUNT(*), GROUP_CONCAT(name, ', ') FROM stations GROUP BY zone",
        note="GROUP_CONCAT packs a group into one string, and since SQLite"
             " 3.44 takes its own ORDER BY; without it the names come in"
             " whatever order the rows arrived, here by station_id, so"
             " the centre reads 'Market Square, Cathedral, Station"
             " Approach'. The text is compared exactly.",
        claims=[("five zones, the centre alphabetical",
                 lambda rows, c: len(rows) == 5
                 and ('centre', 3, 'Cathedral, Market Square, Station Approach') in rows)],
    ),
    dict(
        id=5, ledger="Q1121", concept="N1", tier="2 - Labels and text",
        title="Where the members live, with a fallback",
        prompt=(
            "Members counted by district, except that a member with no"
            " district is counted under 'zone ' followed by the zone of"
            " their home station. COALESCE over the district and the"
            " concatenation, with a join to stations.\n\n"
            "Return: place, members"
        ),
        solution=("SELECT COALESCE(m.district, 'zone ' || s.zone) AS place, COUNT(*) FROM members m"
                  " JOIN stations s ON s.station_id = m.home_station_id GROUP BY place"),
        trap_sql=("SELECT IFNULL(m.district, 'zone ' || s.zone) AS place, COUNT(*) FROM members m"
                  " JOIN stations s ON s.station_id = m.home_station_id GROUP BY m.district"),
        note="The GROUP BY has to be on the COALESCEd value, not the raw"
             " district: grouping by the district puts all eighty-six"
             " NULLs in one group and labels it with whichever zone comes"
             " first. Ten districts and five zone fallbacks make fifteen"
             " rows. IFNULL and COALESCE are the same thing for two"
             " arguments.",
        claims=[("fifteen places, five of them zone fallbacks",
                 lambda rows, c: len(rows) == 15 and sum(r[0].startswith('zone ') for r in rows) == 5
                 and sum(r[1] for r in rows) == 900)],
    ),
    dict(
        id=6, ledger="Q1122", concept="FMT", tier="2 - Labels and text",
        title="Fares by plan, in dollars",
        prompt=(
            "For each plan: the members' fares in all, as TEXT like"
            " '$12345.50' -- FORMAT('$%.2f', ...) over the cents divided"
            " by 100.0. A join from rides to members for the plan.\n\n"
            "Return: plan, fares"
        ),
        solution=("SELECT m.plan, FORMAT('$%.2f', SUM(r.fare_cents) / 100.0) FROM rides r"
                  " JOIN members m ON m.member_id = r.member_id GROUP BY m.plan"),
        trap_sql=("SELECT m.plan, FORMAT('$%.2f', SUM(r.fare_cents) / 100) FROM rides r"
                  " JOIN members m ON m.member_id = r.member_id GROUP BY m.plan"),
        note="FORMAT is SQLite's printf: %.2f prints two decimals of"
             " whatever it is given. Given SUM / 100 it is given an"
             " integer -- the cents were already thrown away -- and"
             " prints '.00' on every plan. Divide by 100.0 so the"
             " decimals exist to be printed. Pay-as-you-go pays the most,"
             " having no free half hour.",
        claims=[("three plans, pay-as-you-go the biggest and not round",
                 lambda rows, c: len(rows) == 3
                 and max(rows, key=lambda r: float(r[1][1:]))[0] == 'pay-as-you-go'
                 and any(not r[1].endswith('.00') for r in rows))],
    ),
    # =========================================== 3 Counting with conditions
    dict(
        id=7, ledger="Q1123", concept="FIL", tier="3 - Counting with conditions",
        title="How casual each station is",
        prompt=(
            "For each start station: all rides started there, those by"
            " casual riders (member_id NULL), and the casual share as a"
            " percentage to one decimal. COUNT(*) FILTER (WHERE ...) for"
            " the casual count, in one pass over rides.\n\n"
            "Return: station_id, rides, casual, casual_pct"
        ),
        solution=("SELECT start_station_id, COUNT(*), COUNT(*) FILTER (WHERE member_id IS NULL),"
                  " ROUND(100.0 * COUNT(*) FILTER (WHERE member_id IS NULL) / COUNT(*), 1) FROM rides GROUP BY start_station_id"),
        trap_sql=("SELECT start_station_id, COUNT(*), COUNT(*) FILTER (WHERE member_id IS NULL),"
                  " ROUND(100.0 * COUNT(*) FILTER (WHERE member_id IS NULL) / COUNT(*), 1) FROM rides"
                  " WHERE member_id IS NULL GROUP BY start_station_id"),
        note="FILTER restricts one aggregate; WHERE restricts the whole"
             " query. Put the casual test in the WHERE as well and the"
             " denominator is casual too, so every station is 100 per"
             " cent casual. FILTER is the standard spelling of"
             " SUM(member_id IS NULL), and reads better with COUNT.",
        claims=[("twelve stations, each around thirty per cent casual",
                 lambda rows, c: len(rows) == 12 and all(28 < r[3] < 32 for r in rows))],
    ),
    dict(
        id=8, ledger="Q1124", concept="N1X", tier="3 - Counting with conditions",
        title="Members never named on a payment",
        prompt=(
            "Members with no payment carrying their member_id, counted by"
            " plan -- fare payments name the ride, not the rider, so"
            " pay-as-you-go members are mostly here. Use NOT EXISTS; a"
            " NOT IN over payments.member_id would meet the NULLs of the"
            " fare payments and return nothing.\n\n"
            "Return: plan, members"
        ),
        solution=("SELECT plan, COUNT(*) FROM members m"
                  " WHERE NOT EXISTS (SELECT 1 FROM payments p WHERE p.member_id = m.member_id) GROUP BY plan"),
        trap_sql=("SELECT plan, COUNT(*) FROM members"
                  " WHERE member_id NOT IN (SELECT member_id FROM payments) GROUP BY plan"),
        note="x NOT IN (list) is x <> each value, ANDed together; one NULL"
             " in the list makes the whole thing NULL, never true, and the"
             " query is empty with no warning. NOT EXISTS has no such"
             " hole. Nine annual and one monthly member have never been"
             " charged for their plan -- the ones every subscription"
             " payment missed.",
        claims=[("three plans, over two hundred pay-as-you-go",
                 lambda rows, c: len(rows) == 3 and dict(rows)['pay-as-you-go'] > 200
                 and dict(rows)['annual'] < 20)],
    ),
    dict(
        id=9, ledger="Q1125", concept="DST", tier="3 - Counting with conditions",
        title="What it takes to be a top-ten-per-cent rider",
        prompt=(
            "For each plan: the ride count that puts a member in the top"
            " ten per cent of that plan's riders, and the plan's maximum."
            " A CTE of rides per member, CUME_DIST() OVER (PARTITION BY"
            " plan ORDER BY rides), then the smallest count whose"
            " CUME_DIST is at least 0.9 -- MIN with a FILTER -- and"
            " MAX.\n\n"
            "Return: plan, top_decile_rides, max_rides"
        ),
        solution=("WITH per AS (SELECT m.plan, COUNT(*) AS n FROM members m JOIN rides r ON r.member_id = m.member_id GROUP BY m.member_id),"
                  " cd AS (SELECT plan, n, CUME_DIST() OVER (PARTITION BY plan ORDER BY n) AS c FROM per)"
                  " SELECT plan, MIN(n) FILTER (WHERE c >= 0.9), MAX(n) FROM cd GROUP BY plan"),
        trap_sql=("WITH per AS (SELECT m.plan, COUNT(*) AS n FROM members m JOIN rides r ON r.member_id = m.member_id GROUP BY m.member_id),"
                  " cd AS (SELECT plan, n, CUME_DIST() OVER (PARTITION BY plan ORDER BY n DESC) AS c FROM per)"
                  " SELECT plan, MIN(n) FILTER (WHERE c >= 0.9), MAX(n) FROM cd GROUP BY plan"),
        note="CUME_DIST is the share of the partition at or below the row"
             " in the window's order, so ascending puts the heavy riders"
             " at 0.9 and above. Ordered descending, 0.9 is reached by the"
             " LIGHTEST riders and the threshold collapses to ten rides."
             " Thirty-odd rides a year and a half gets you into the top"
             " tenth on any plan.",
        claims=[("three plans, the threshold in the thirties",
                 lambda rows, c: len(rows) == 3 and all(30 <= r[1] <= 35 and r[2] > 200 for r in rows))],
    ),
    # ================================================= 4 The fleet's calendar
    dict(
        id=10, ledger="Q1126", concept="WIN", tier="4 - The fleet's calendar",
        title="The cargo bikes, in order of arrival",
        prompt=(
            "The cargo bikes in the order they were acquired: bike_id,"
            " acquired_on, their place in that order, and the days since"
            " the previous cargo bike arrived (NULL for the first)."
            " ROW_NUMBER and LAG over ONE named window -- WINDOW w AS"
            " (ORDER BY acquired_on, bike_id) after the WHERE -- and"
            " julianday for the gap.\n\n"
            "Return: bike_id, acquired_on, nth, days_since_previous"
        ),
        solution=("SELECT bike_id, acquired_on, ROW_NUMBER() OVER w, julianday(acquired_on) - julianday(LAG(acquired_on) OVER w)"
                  " FROM bikes WHERE model = 'cargo' WINDOW w AS (ORDER BY acquired_on, bike_id)"),
        trap_sql=("SELECT bike_id, acquired_on, ROW_NUMBER() OVER w, julianday(acquired_on) - julianday(LAG(acquired_on) OVER (ORDER BY bike_id))"
                  " FROM bikes WHERE model = 'cargo' WINDOW w AS (ORDER BY acquired_on, bike_id)"),
        note="A named window is defined once and used by every function"
             " that says OVER w, so the numbering and the look-back agree."
             " A LAG with its own ORDER BY bike_id looks at the previous"
             " bike NUMBER, whose acquisition date has nothing to do with"
             " this one's, and the gaps go negative. Two cargo bikes"
             " arrived on the same day, which is why bike_id breaks the"
             " tie.",
        claims=[("thirty-one cargo bikes, one same-day pair",
                 lambda rows, c: len(rows) == 31 and sum(r[3] == 0 for r in rows) == 1
                 and all(r[3] is None or r[3] >= 0 for r in rows))],
    ),
    dict(
        id=11, ledger="Q1127", concept="D2", tier="4 - The fleet's calendar",
        title="Weeks that start on Monday",
        prompt=(
            "Rides per week for the weeks touching June 2026 -- rides"
            " started from 2026-05-25 up to but not including 2026-07-01"
            " -- labelled by the MONDAY the week began: date(started_at,"
            " 'weekday 0', '-6 days') moves forward to the Sunday and back"
            " six days. GROUP BY that.\n\n"
            "Return: week_of, rides"
        ),
        solution=("SELECT date(started_at, 'weekday 0', '-6 days') AS wk, COUNT(*) FROM rides"
                  " WHERE started_at >= '2026-05-25' AND started_at < '2026-07-01' GROUP BY wk"),
        trap_sql=("SELECT date(started_at, 'weekday 1') AS wk, COUNT(*) FROM rides"
                  " WHERE started_at >= '2026-05-25' AND started_at < '2026-07-01' GROUP BY wk"),
        note="'weekday N' moves FORWARD to the next day numbered N, or"
             " stays if already there -- so 'weekday 1' labels each week"
             " by the Monday AFTER it, a week late, and a Monday's rides"
             " land in their own week while Tuesday's go to the next."
             " Forward to Sunday and back six days is the standard way to"
             " the Monday that began the week.",
        claims=[("six weeks, all labelled with Mondays",
                 lambda rows, c: len(rows) == 6 and rows[0][0] == '2026-05-25'
                 and all(dict(rows).get(k) for k in ('2026-06-01', '2026-06-29')))],
    ),
    dict(
        id=12, ledger="Q1128", concept="D2N", tier="4 - The fleet's calendar",
        title="How old the fleet is",
        prompt=(
            "For each model: the bikes, how many are retired, and the"
            " average age in whole days -- a retired bike's age at"
            " retirement, an in-service bike's age at 2026-06-30."
            " COALESCE(retired_on, '2026-06-30') inside julianday.\n\n"
            "Return: model, bikes, retired, avg_age_days"
        ),
        solution=("SELECT model, COUNT(*), SUM(retired_on IS NOT NULL),"
                  " CAST(ROUND(AVG(julianday(COALESCE(retired_on, '2026-06-30')) - julianday(acquired_on))) AS INTEGER) FROM bikes GROUP BY model"),
        trap_sql=("SELECT model, COUNT(*), SUM(retired_on IS NOT NULL),"
                  " CAST(ROUND(AVG(julianday(retired_on) - julianday(acquired_on))) AS INTEGER) FROM bikes GROUP BY model"),
        note="julianday(NULL) is NULL, and AVG skips NULLs, so without"
             " the COALESCE the average is over the retired bikes only --"
             " eighteen of three hundred and twenty -- and says the fleet"
             " is younger than it is. The fallback date makes every bike"
             " count. The three models are all about three years old on"
             " average.",
        claims=[("three models, around a thousand days old",
                 lambda rows, c: len(rows) == 3 and all(1000 < r[3] < 1100 for r in rows)
                 and sum(r[2] for r in rows) == 18)],
    ),
    # ================================================= 5 Changing the data
    dict(
        id=13, ledger="Q1129", concept="GEN", tier="5 - Changing the data",
        kind="script",
        title="A minutes column that computes itself",
        prompt=(
            "Add to rides a column `minutes` that is GENERATED ALWAYS AS"
            " the ride's length in minutes -- (julianday(ended_at) -"
            " julianday(started_at)) * 1440 -- VIRTUAL, so ALTER TABLE"
            " can add it without rewriting the table. Open rides get"
            " NULL by themselves.\n\n"
            "Checked: the column's average to one decimal, its rounded"
            " maximum, and how many rows have it NULL"
        ),
        solution=("ALTER TABLE rides ADD COLUMN minutes REAL"
                  " GENERATED ALWAYS AS ((julianday(ended_at) - julianday(started_at)) * 1440) VIRTUAL;"),
        trap_sql=("ALTER TABLE rides ADD COLUMN minutes REAL"
                  " GENERATED ALWAYS AS ((julianday(ended_at) - julianday(started_at)) * 24) VIRTUAL;"),
        probe_sql="SELECT ROUND(AVG(minutes), 1), ROUND(MAX(minutes)), SUM(minutes IS NULL) FROM rides",
        note="A generated column is an expression that behaves as a"
             " column: queried, indexed, never stored for VIRTUAL. The"
             " trap multiplies by 24 and gets hours. ALTER TABLE can add"
             " a VIRTUAL generated column but not a STORED one, which"
             " would need every row rewritten. The thirty-five open rides"
             " are NULL because julianday(NULL) is.",
        claims=[("twenty-two minutes on average, four hours at most, thirty-five NULL",
                 lambda rows, c: rows == [(22.7, 240.0, 35)])],
    ),
    dict(
        id=14, ledger="Q1130", concept="DDL", tier="5 - Changing the data",
        kind="script",
        title="A table that turns bad rows away",
        prompt=(
            "Create a table `bike_moves (move_id INTEGER PRIMARY KEY,"
            " bike_id, from_station, to_station, moved_on)` for bikes"
            " trucked between stations: bike_id REFERENCES bikes,"
            " from_station and to_station REFERENCES stations, all NOT"
            " NULL, moved_on NOT NULL, and a CHECK that from_station <>"
            " to_station. The question then inserts four rows: a good"
            " one, one moving a bike to the station it is at, one for a"
            " bike 999, and one to a station 99.\n\n"
            "Checked: the move_ids that got in"
        ),
        solution=("CREATE TABLE bike_moves (\n"
                  "  move_id INTEGER PRIMARY KEY,\n"
                  "  bike_id INTEGER NOT NULL REFERENCES bikes(bike_id),\n"
                  "  from_station INTEGER NOT NULL REFERENCES stations(station_id),\n"
                  "  to_station INTEGER NOT NULL REFERENCES stations(station_id),\n"
                  "  moved_on TEXT NOT NULL,\n"
                  "  CHECK (from_station <> to_station)\n"
                  ");"),
        trap_sql=("CREATE TABLE bike_moves (\n"
                  "  move_id INTEGER PRIMARY KEY,\n"
                  "  bike_id INTEGER NOT NULL REFERENCES bikes(bike_id),\n"
                  "  from_station INTEGER NOT NULL REFERENCES stations(station_id),\n"
                  "  to_station INTEGER NOT NULL REFERENCES stations(station_id),\n"
                  "  moved_on TEXT NOT NULL\n"
                  ");"),
        driver_sql=("INSERT INTO bike_moves VALUES (1, 1, 3, 1, '2026-06-30');\n"
                    "INSERT INTO bike_moves VALUES (2, 1, 3, 3, '2026-06-30');\n"
                    "INSERT INTO bike_moves VALUES (3, 999, 3, 1, '2026-06-30');\n"
                    "INSERT INTO bike_moves VALUES (4, 1, 3, 99, '2026-06-30');"),
        probe_sql="SELECT move_id, bike_id, to_station FROM bike_moves ORDER BY move_id",
        note="A CHECK can compare two columns of the row, and REFERENCES"
             " makes the database refuse a bike or station that does not"
             " exist -- the sandbox has foreign keys ON, as the real app"
             " does. Without the CHECK, the move from station 3 to station"
             " 3 is accepted. Each refusal is reported in the status bar,"
             " not treated as an error.",
        claims=[("one move in, three turned away",
                 lambda rows, c: rows == [(1, 1, 1)])],
    ),
    dict(
        id=15, ledger="Q1131", concept="TMP", tier="5 - Changing the data",
        kind="script",
        title="Close the books on the retired bikes",
        prompt=(
            "Two steps: CREATE TEMP TABLE gone AS the bike_ids of the"
            " retired bikes, then DELETE the maintenance jobs that are"
            " still OPEN (fixed_at NULL) on those bikes -- WHERE bike_id"
            " IN (SELECT bike_id FROM gone). Fixed jobs on retired bikes"
            " are history and stay.\n\n"
            "Checked: how many jobs remain, and how many of them are open"
        ),
        solution=("CREATE TEMP TABLE gone AS SELECT bike_id FROM bikes WHERE retired_on IS NOT NULL;\n"
                  "DELETE FROM maintenance WHERE fixed_at IS NULL AND bike_id IN (SELECT bike_id FROM gone);"),
        trap_sql=("CREATE TEMP TABLE gone AS SELECT bike_id FROM bikes WHERE retired_on IS NOT NULL;\n"
                  "DELETE FROM maintenance WHERE bike_id IN (SELECT bike_id FROM gone);"),
        probe_sql="SELECT COUNT(*), SUM(fixed_at IS NULL) FROM maintenance",
        note="A TEMP table lives in the connection and vanishes with it,"
             " which makes it a scratch pad for a multi-step change: build"
             " the list once, use it in the DELETE. The trap forgets the"
             " 'still open' half and deletes the retired bikes' whole"
             " history, sixty-four jobs instead of seven.",
        claims=[("seven open jobs gone, the fixed ones kept",
                 lambda rows, c: rows == [(1100 - 7, 114 - 7)])],
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
