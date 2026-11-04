"""Practice exercises: fifteen questions on the bike-hire schema.

The eighth set on the bike scheme (SEED 1206), two tools per question, the
tiers named by task, on tools no bike set has used -- and, from this set
on, prompts that name the tool but do not write the statement. Nearest
and next -- the runner-up station in each zone by NTH_VALUE, each bike
against its model-mates by a frame that EXCLUDEs the current row, each
member's latest ride by a correlated MAX. Text and type -- the first and
last names alphabetically by MIN and MAX on text, a surname matched
however it is typed by COLLATE NOCASE, what a column actually holds by
typeof. Per group, per station -- the three latest jobs at each station
by a correlated ORDER BY ... LIMIT, new riders by month with a running
total, surname-sharing pairs by a self-join on two columns. Ratios and
buckets -- cents per kilometre as a ratio of sums, a GROUP BY on a boolean
expression, quarters by integer arithmetic. And three WRITABLE questions:

  * a view with an INSTEAD OF DELETE trigger that closes a job instead
  * a CREATE TABLE ... AS SELECT snapshot
  * a table whose DEFAULTs fill in what an INSERT leaves out

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
    # ==================================================== 1 Nearest and next
    dict(
        id=1, ledger="Q1177", concept="NTH", tier="1 - Nearest and next",
        title="The runner-up station in each zone",
        prompt=(
            "For each zone: the station with the SECOND most rides"
            " started there, and that count. Count rides per station in"
            " a CTE, then NTH_VALUE over a window partitioned by zone;"
            " the frame has to be opened to the whole partition, or"
            " the first row of each zone cannot see its runner-up.\n\n"
            "Return: zone, runner_up, rides"
        ),
        solution=("WITH per AS (SELECT s.zone, s.name, COUNT(*) AS n FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.station_id)"
                  " SELECT DISTINCT zone,"
                  " NTH_VALUE(name, 2) OVER (PARTITION BY zone ORDER BY n DESC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING),"
                  " NTH_VALUE(n, 2) OVER (PARTITION BY zone ORDER BY n DESC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)"
                  " FROM per"),
        trap_sql=("WITH per AS (SELECT s.zone, s.name, COUNT(*) AS n FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.station_id)"
                  " SELECT DISTINCT zone,"
                  " NTH_VALUE(name, 2) OVER (PARTITION BY zone ORDER BY n DESC),"
                  " NTH_VALUE(n, 2) OVER (PARTITION BY zone ORDER BY n DESC)"
                  " FROM per"),
        note="NTH_VALUE(x, 2) is the second row's x within the frame,"
             " and with an ORDER BY the default frame ends at the"
             " current row: on the busiest station's row there is no"
             " second row yet, so the trap returns NULL for it and a"
             " zone shows up twice, once blank. ROWS BETWEEN UNBOUNDED"
             " PRECEDING AND UNBOUNDED FOLLOWING makes every row see the"
             " whole zone, and DISTINCT then collapses it to one line."
             " Old Mill is the south's runner-up even though it closed.",
        claims=[("five zones, Cathedral second in the centre",
                 lambda rows, c: len(rows) == 5 and ("centre", "Cathedral", 3313) in rows),
                ("no zone blank",
                 lambda rows, c: all(r[1] is not None for r in rows))],
    ),
    dict(
        id=2, ledger="Q1178", concept="EXC", tier="1 - Nearest and next",
        title="Each bike against its model-mates",
        prompt=(
            "For bikes 1 to 10: the model, the bike's rides, and the"
            " average rides of the OTHER bikes of that model, to one"
            " decimal. A window frame over the whole partition with"
            " EXCLUDE CURRENT ROW leaves the bike itself out of its own"
            " comparison. Count over every bike first, including the"
            " ones never ridden, and filter to 1 to 10 afterwards.\n\n"
            "Return: bike_id, model, rides, others_avg"
        ),
        solution=("WITH per AS (SELECT b.bike_id, b.model, COUNT(r.ride_id) AS n FROM bikes b LEFT JOIN rides r ON r.bike_id = b.bike_id GROUP BY b.bike_id),"
                  " w AS (SELECT bike_id, model, n, ROUND(AVG(n) OVER (PARTITION BY model ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING EXCLUDE CURRENT ROW), 1) AS others FROM per)"
                  " SELECT bike_id, model, n, others FROM w WHERE bike_id <= 10"),
        trap_sql=("WITH per AS (SELECT b.bike_id, b.model, COUNT(r.ride_id) AS n FROM bikes b LEFT JOIN rides r ON r.bike_id = b.bike_id GROUP BY b.bike_id),"
                  " w AS (SELECT bike_id, model, n, ROUND(AVG(n) OVER (PARTITION BY model), 1) AS others FROM per)"
                  " SELECT bike_id, model, n, others FROM w WHERE bike_id <= 10"),
        note="EXCLUDE CURRENT ROW is a frame option: the window still"
             " runs over the whole partition but the row being computed"
             " is left out of the aggregate, which is what 'compared"
             " with the others' means. The trap includes the bike in its"
             " own average, so a bike with 43 rides pulls its"
             " comparison down towards itself. The window must be"
             " computed over all 320 bikes in the CTE; filtered to ten"
             " first, the 'others' would be the other nine.",
        claims=[("ten bikes, bike 2 well below its model-mates",
                 lambda rows, c: len(rows) == 10 and any(r[0] == 2 and r[2] == 43 and r[3] > 120 for r in rows)),
                ("every comparison figure between 115 and 125",
                 lambda rows, c: all(115 <= r[3] <= 125 for r in rows))],
    ),
    dict(
        id=3, ledger="Q1179", concept="GNG", tier="1 - Nearest and next",
        title="Each member's latest ride",
        prompt=(
            "For members 1 to 10 who have ridden: the ride_id and"
            " start of their most recent ride. No window function:"
            " a correlated scalar subquery in WHERE that finds the"
            " member's latest started_at, matched against the row's"
            " own.\n\n"
            "Return: member_id, ride_id, started_at"
        ),
        solution=("SELECT r.member_id, r.ride_id, r.started_at FROM rides r WHERE r.member_id <= 10"
                  " AND r.started_at = (SELECT MAX(x.started_at) FROM rides x WHERE x.member_id = r.member_id)"),
        trap_sql=("SELECT r.member_id, r.ride_id, r.started_at FROM rides r WHERE r.member_id <= 10"
                  " AND r.started_at = (SELECT MAX(x.started_at) FROM rides x)"),
        note="'The latest row per group' is the greatest-n-per-group"
             " problem, and the oldest answer to it is a subquery that"
             " computes the group's maximum and a WHERE that keeps the"
             " row equal to it. The correlation -- x.member_id ="
             " r.member_id -- is what makes it per member; without it"
             " the trap compares every ride with the latest ride in the"
             " whole table and returns nothing. Seven of the first ten"
             " members have ridden; three never have.",
        claims=[("seven members, each once",
                 lambda rows, c: len(rows) == 7 and len({r[0] for r in rows}) == 7),
                ("member 2's latest ride is 14159",
                 lambda rows, c: any(r[0] == 2 and r[1] == 14159 for r in rows))],
    ),
    # ======================================================= 2 Text and type
    dict(
        id=4, ledger="Q1180", concept="TXTAGG", tier="2 - Text and type",
        title="First and last in the register, by plan",
        prompt=(
            "For each plan: the member whose name comes first"
            " alphabetically and the one whose name comes last. MIN"
            " and MAX work on text as well as numbers.\n\n"
            "Return: plan, first_name, last_name"
        ),
        solution="SELECT plan, MIN(name), MAX(name) FROM members GROUP BY plan",
        trap_sql="SELECT plan, MIN(member_id), MAX(member_id) FROM members GROUP BY plan",
        note="MIN and MAX compare text the way ORDER BY does, by"
             " collation -- BINARY unless the column says otherwise, so"
             " capitals before lower case -- and return the extreme"
             " value, not a row. The trap takes the smallest and largest"
             " ids, which is the first and last to JOIN, a different"
             " question. Every plan's register runs from an Aisha to a"
             " Zara.",
        claims=[("three plans, every register from Aisha to Zara",
                 lambda rows, c: len(rows) == 3 and all(r[1].startswith("Aisha") and r[2].startswith("Zara") for r in rows))],
    ),
    dict(
        id=5, ledger="Q1181", concept="COL", tier="2 - Text and type",
        title="The Uddins, however the name was typed",
        prompt=(
            "Every member whose surname is Uddin, found with the"
            " search term typed in lower case: 'uddin'. The surname is"
            " the text after the first space; compare it with COLLATE"
            " NOCASE so that case does not matter.\n\n"
            "Return: member_id, name"
        ),
        solution=("SELECT member_id, name FROM members"
                  " WHERE SUBSTR(name, INSTR(name, ' ') + 1) = 'uddin' COLLATE NOCASE"),
        trap_sql=("SELECT member_id, name FROM members"
                  " WHERE SUBSTR(name, INSTR(name, ' ') + 1) = 'uddin'"),
        note="= on text is exact by default, so 'Uddin' is not 'uddin'"
             " and the trap finds nobody. COLLATE NOCASE after the"
             " comparison makes it ignore ASCII case; a column can also"
             " be declared NOCASE, as stations.name's index is, and then"
             " every comparison on it behaves this way. LIKE is"
             " case-insensitive too, but matches patterns, which is"
             " more than needed here.",
        claims=[("45 Uddins",
                 lambda rows, c: len(rows) == 45 and all(r[1].endswith("Uddin") for r in rows))],
    ),
    dict(
        id=6, ledger="Q1182", concept="TYP", tier="2 - Text and type",
        title="What the rides table actually holds",
        prompt=(
            "For three columns of rides -- distance_m, member_id and"
            " fare_cents -- the storage types found in them and how"
            " many rows hold each. typeof() names a value's type, and"
            " NULL is one of them; one GROUP BY per column, stacked.\n\n"
            "Return: column_name, storage_type, rows"
        ),
        solution=("SELECT 'distance_m', typeof(distance_m), COUNT(*) FROM rides GROUP BY typeof(distance_m)"
                  " UNION ALL SELECT 'member_id', typeof(member_id), COUNT(*) FROM rides GROUP BY typeof(member_id)"
                  " UNION ALL SELECT 'fare_cents', typeof(fare_cents), COUNT(*) FROM rides GROUP BY typeof(fare_cents)"),
        trap_sql=("SELECT 'distance_m', typeof(distance_m), COUNT(distance_m) FROM rides GROUP BY typeof(distance_m)"
                  " UNION ALL SELECT 'member_id', typeof(member_id), COUNT(member_id) FROM rides GROUP BY typeof(member_id)"
                  " UNION ALL SELECT 'fare_cents', typeof(fare_cents), COUNT(fare_cents) FROM rides GROUP BY typeof(fare_cents)"),
        note="SQLite stores each VALUE with its own type -- integer,"
             " real, text, blob or null -- whatever the column was"
             " declared as, and typeof() reports it, so this is how to"
             " find a number stored as text or a column full of NULLs."
             " COUNT(column) skips NULLs, which is why the trap reports"
             " zero rows of type null. 35 rides have no distance, the"
             " ones still out; 11,513 have no member.",
        claims=[("five rows, 35 null distances",
                 lambda rows, c: len(rows) == 5 and ("distance_m", "null", 35) in rows),
                ("fare_cents is integer on every row",
                 lambda rows, c: ("fare_cents", "integer", 38605) in rows)],
    ),
    # ============================================= 3 Per group, per station
    dict(
        id=7, ledger="Q1183", concept="CLIM", tier="3 - Per group, per station",
        title="The three latest jobs at each station",
        prompt=(
            "For every station: its three most recently reported jobs."
            " No window function: a subquery correlated on station_id"
            " with its own ORDER BY and LIMIT 3, used as an IN list of"
            " job_ids.\n\n"
            "Return: station_id, job_id, reported_at"
        ),
        solution=("SELECT m.station_id, m.job_id, m.reported_at FROM maintenance m"
                  " WHERE m.job_id IN (SELECT x.job_id FROM maintenance x WHERE x.station_id = m.station_id ORDER BY x.reported_at DESC LIMIT 3)"),
        trap_sql=("SELECT m.station_id, m.job_id, m.reported_at FROM maintenance m"
                  " WHERE m.job_id IN (SELECT x.job_id FROM maintenance x ORDER BY x.reported_at DESC LIMIT 3)"),
        note="ORDER BY and LIMIT are allowed inside a subquery, and when"
             " the subquery is correlated it runs once per outer row"
             " with that row's station in scope: 'the three latest at"
             " THIS station'. Without the correlation the trap finds the"
             " three latest jobs anywhere and returns three rows. This"
             " is top-N-per-group without ROW_NUMBER, slower on a big"
             " table but often clearer. No station reported two jobs in"
             " the same minute, so the order is settled.",
        claims=[("36 rows, three per station",
                 lambda rows, c: len(rows) == 36 and all(sum(r[0] == s for r in rows) == 3 for s in range(1, 13))),
                ("station 1's latest is job 214",
                 lambda rows, c: (1, 214, "2026-06-30 22:14") in rows)],
    ),
    dict(
        id=8, ledger="Q1184", concept="NEWR", tier="3 - Per group, per station",
        title="New riders by month, and the running total",
        prompt=(
            "For each month in which some member took their FIRST"
            " ride: how many members did, and how many members had"
            " ridden by the end of that month. A CTE of each member's"
            " first ride month, a count per month, and a running SUM"
            " over the months.\n\n"
            "Return: month, new_riders, riders_so_far"
        ),
        solution=("WITH f AS (SELECT member_id, strftime('%Y-%m', MIN(started_at)) AS mo FROM rides WHERE member_id IS NOT NULL GROUP BY member_id),"
                  " m AS (SELECT mo, COUNT(*) AS n FROM f GROUP BY mo)"
                  " SELECT mo, n, SUM(n) OVER (ORDER BY mo) FROM m"),
        trap_sql=("SELECT strftime('%Y-%m', started_at), COUNT(DISTINCT member_id),"
                  " SUM(COUNT(DISTINCT member_id)) OVER (ORDER BY strftime('%Y-%m', started_at))"
                  " FROM rides WHERE member_id IS NOT NULL GROUP BY strftime('%Y-%m', started_at)"),
        note="'New' needs each member's first month, which is a MIN per"
             " member before anything is counted per month; the trap"
             " counts the distinct riders active in each month, who are"
             " mostly the same people every month, and its running total"
             " climbs past the 800 members who have ever ridden. Every"
             " rider's first ride falls in the first five months of the"
             " data, so there are five rows; the running SUM reaches 800"
             " in May 2025.",
        claims=[("five months, 584 riders in the first",
                 lambda rows, c: len(rows) == 5 and ("2025-01", 584, 584) in rows),
                ("the running total ends at 800",
                 lambda rows, c: max(r[2] for r in rows) == 800)],
    ),
    dict(
        id=9, ledger="Q1185", concept="SLF2", tier="3 - Per group, per station",
        title="Family at the same station",
        prompt=(
            "For every station: how many PAIRS of its members share a"
            " surname. A self-join of members on two conditions, the"
            " home station and the surname (the text after the first"
            " space), each pair counted once.\n\n"
            "Return: name, pairs"
        ),
        solution=("SELECT s.name, COUNT(*) FROM members a JOIN members b"
                  " ON b.home_station_id = a.home_station_id"
                  " AND SUBSTR(b.name, INSTR(b.name, ' ') + 1) = SUBSTR(a.name, INSTR(a.name, ' ') + 1)"
                  " AND a.member_id < b.member_id"
                  " JOIN stations s ON s.station_id = a.home_station_id GROUP BY s.name"),
        trap_sql=("SELECT s.name, COUNT(*) FROM members a JOIN members b"
                  " ON b.home_station_id = a.home_station_id"
                  " AND SUBSTR(b.name, INSTR(b.name, ' ') + 1) = SUBSTR(a.name, INSTR(a.name, ' ') + 1)"
                  " AND a.member_id <> b.member_id"
                  " JOIN stations s ON s.station_id = a.home_station_id GROUP BY s.name"),
        note="A self-join can match on as many columns as the question"
             " needs, and computed ones too. < on the ids keeps each"
             " pair once; <> keeps both orderings and the trap doubles"
             " every count. With 25 surnames across 900 members, sharing"
             " one is common: Botanic Gardens has 148 such pairs among"
             " its members.",
        claims=[("twelve stations, 148 pairs at Botanic Gardens",
                 lambda rows, c: len(rows) == 12 and ("Botanic Gardens", 148) in rows),
                ("1354 pairs in all",
                 lambda rows, c: sum(r[1] for r in rows) == 1354)],
    ),
    # ================================================== 4 Ratios and buckets
    dict(
        id=10, ledger="Q1186", concept="RSUM", tier="4 - Ratios and buckets",
        title="What a kilometre costs, by plan",
        prompt=(
            "For each plan, with the casual riders as a fourth group"
            " labelled 'casual': the fare per kilometre in cents, to"
            " two decimals, over the finished rides. A ratio of SUMS --"
            " all the fares over all the distance -- not an average of"
            " each ride's own ratio.\n\n"
            "Return: plan, cents_per_km"
        ),
        solution=("SELECT COALESCE(m.plan, 'casual'), ROUND(1000.0 * SUM(r.fare_cents) / SUM(r.distance_m), 2)"
                  " FROM rides r LEFT JOIN members m ON m.member_id = r.member_id"
                  " WHERE r.distance_m IS NOT NULL GROUP BY COALESCE(m.plan, 'casual')"),
        trap_sql=("SELECT COALESCE(m.plan, 'casual'), ROUND(AVG(1000.0 * r.fare_cents / r.distance_m), 2)"
                  " FROM rides r LEFT JOIN members m ON m.member_id = r.member_id"
                  " WHERE r.distance_m IS NOT NULL GROUP BY COALESCE(m.plan, 'casual')"),
        note="A rate over a group is total over total. The average of"
             " per-ride rates, the trap, weights a 200-metre ride the"
             " same as a 20-kilometre one, and short rides have wild"
             " rates -- a minimum fare over a few hundred metres -- so"
             " the casual figure comes out at 174 cents a kilometre"
             " instead of 79. Subscribers pay about 12 cents a"
             " kilometre, casual riders about six times that.",
        claims=[("four groups, casual riders at 79.21",
                 lambda rows, c: len(rows) == 4 and ("casual", 79.21) in rows),
                ("subscribers around 12 cents",
                 lambda rows, c: all(11 <= r[1] <= 13 for r in rows if r[0] in ("annual", "monthly")))],
    ),
    dict(
        id=11, ledger="Q1187", concept="GRPB", tier="4 - Ratios and buckets",
        title="Members and casuals, model by model",
        prompt=(
            "For each model and, within it, members against casual"
            " riders: the finished rides and their average length in"
            " minutes to one decimal. GROUP BY the model and a BOOLEAN"
            " expression -- whether member_id is NULL -- rather than"
            " a column; six rows.\n\n"
            "Return: model, casual, rides, avg_minutes"
        ),
        solution=("SELECT b.model, r.member_id IS NULL, COUNT(*), ROUND(AVG((julianday(r.ended_at) - julianday(r.started_at)) * 1440), 1)"
                  " FROM rides r JOIN bikes b ON b.bike_id = r.bike_id WHERE r.ended_at IS NOT NULL"
                  " GROUP BY b.model, r.member_id IS NULL"),
        trap_sql=("SELECT b.model, r.member_id IS NULL, COUNT(*), ROUND(AVG((julianday(r.ended_at) - julianday(r.started_at)) * 1440), 1)"
                  " FROM rides r JOIN bikes b ON b.bike_id = r.bike_id WHERE r.ended_at IS NOT NULL"
                  " GROUP BY b.model"),
        note="Any expression can be a grouping key, and a comparison is"
             " an expression that is 0 or 1, so GROUP BY member_id IS"
             " NULL splits each model in two without a CASE. The trap"
             " groups by model alone: SQLite then shows the IS NULL of"
             " an arbitrary row of each group, and three rows stand"
             " where six should. Casual riders and members ride for"
             " about the same time on every model.",
        claims=[("six rows, two per model",
                 lambda rows, c: len(rows) == 6 and {r[1] for r in rows} == {0, 1}),
                ("17,517 member rides on classics",
                 lambda rows, c: any(r[0] == "classic" and r[1] == 0 and r[2] == 17517 for r in rows))],
    ),
    dict(
        id=12, ledger="Q1188", concept="QTR", tier="4 - Ratios and buckets",
        title="Rides and fares by quarter",
        prompt=(
            "For each quarter in the data, labelled '2025-Q1' and so"
            " on: the rides, and the fares in dollars. The quarter"
            " number comes from the month by integer arithmetic -- think"
            " about what to add before dividing by three so that"
            " months 1 to 3 give 1 and 10 to 12 give 4.\n\n"
            "Return: quarter, rides, fares"
        ),
        solution=("SELECT strftime('%Y', started_at) || '-Q' || ((strftime('%m', started_at) + 2) / 3), COUNT(*), SUM(fare_cents) / 100.0"
                  " FROM rides GROUP BY 1"),
        trap_sql=("SELECT strftime('%Y', started_at) || '-Q' || (strftime('%m', started_at) / 3), COUNT(*), SUM(fare_cents) / 100.0"
                  " FROM rides GROUP BY 1"),
        note="(month + 2) / 3 in integer arithmetic maps 1, 2, 3 to 1"
             " and 10, 11, 12 to 4; month / 3 alone, the trap, gives a"
             " Q0 of January and February and puts December in a"
             " quarter of its own, eight groups instead of six. strftime"
             " returns text, and + turns '03' into 3 as SQLite does"
             " arithmetic on it. The quarters are within a tenth of one"
             " another.",
        claims=[("six quarters, 2025-Q2 the busiest",
                 lambda rows, c: len(rows) == 6 and max(rows, key=lambda r: r[1])[0] == "2025-Q2"),
                ("rides add up to every ride",
                 lambda rows, c: sum(r[1] for r in rows) == 38605)],
    ),
    # =================================================== 5 Changing the data
    dict(
        id=13, ledger="Q1189", concept="IOT", tier="5 - Changing the data",
        kind="script",
        title="Deleting from the open-jobs view closes the job",
        prompt=(
            "Create a view named open_jobs of the maintenance rows"
            " whose fixed_at is NULL, then a trigger INSTEAD OF DELETE"
            " on that view that, rather than deleting anything, sets"
            " the job's fixed_at to '2026-07-01 09:00'. The question"
            " then deletes jobs 9 and 19 from the view.\n\n"
            "Checked: job 9's fixed_at, how many jobs there are, and"
            " how many are open"
        ),
        solution=("CREATE VIEW open_jobs AS SELECT * FROM maintenance WHERE fixed_at IS NULL;\n"
                  "CREATE TRIGGER close_instead INSTEAD OF DELETE ON open_jobs\n"
                  "BEGIN\n"
                  "  UPDATE maintenance SET fixed_at = '2026-07-01 09:00' WHERE job_id = OLD.job_id;\n"
                  "END;"),
        trap_sql="CREATE VIEW open_jobs AS SELECT * FROM maintenance WHERE fixed_at IS NULL;",
        driver_sql=("DELETE FROM open_jobs WHERE job_id = 9;\n"
                    "DELETE FROM open_jobs WHERE job_id = 19;"),
        probe_sql=("SELECT (SELECT fixed_at FROM maintenance WHERE job_id = 9),"
                   " (SELECT COUNT(*) FROM maintenance),"
                   " (SELECT COUNT(*) FROM maintenance WHERE fixed_at IS NULL)"),
        note="A view cannot be written to, but an INSTEAD OF trigger"
             " on it catches the attempt and does something else -- here"
             " an UPDATE of the base table, with OLD.job_id naming the"
             " row the DELETE asked for. The row then drops out of the"
             " view because it no longer matches its WHERE, which is"
             " what a delete looks like from outside. Without the"
             " trigger the view refuses the DELETE, which the trap's"
             " status bar reports twice.",
        claims=[("two jobs closed, none deleted",
                 lambda rows, c: rows == [("2026-07-01 09:00", 1100, 112)])],
    ),
    dict(
        id=14, ledger="Q1190", concept="CTAS", tier="5 - Changing the data",
        kind="script",
        title="A snapshot table of every bike's record",
        prompt=(
            "Make a table named bike_stats from a query, in one"
            " statement: for every bike, including the ones never"
            " ridden or never repaired, its bike_id, model, how many"
            " rides it has had and how many maintenance jobs. The"
            " columns must be called bike_id, model, rides and jobs."
            " Two independent counts from two tables for one bike is a"
            " place where a single query with two joins goes wrong.\n\n"
            "Checked: how many rows the new table has, and the rides"
            " and jobs added up"
        ),
        solution=("CREATE TABLE bike_stats AS"
                  " SELECT b.bike_id, b.model,"
                  " (SELECT COUNT(*) FROM rides r WHERE r.bike_id = b.bike_id) AS rides,"
                  " (SELECT COUNT(*) FROM maintenance m WHERE m.bike_id = b.bike_id) AS jobs"
                  " FROM bikes b;"),
        trap_sql=("CREATE TABLE bike_stats AS"
                  " SELECT b.bike_id, b.model, COUNT(r.ride_id) AS rides, COUNT(m.job_id) AS jobs"
                  " FROM bikes b LEFT JOIN rides r ON r.bike_id = b.bike_id LEFT JOIN maintenance m ON m.bike_id = b.bike_id"
                  " GROUP BY b.bike_id;"),
        probe_sql="SELECT COUNT(*), SUM(rides), SUM(jobs) FROM bike_stats",
        note="CREATE TABLE ... AS SELECT builds the table from the"
             " query's result: the column names come from the aliases,"
             " the types from the values, and there is no primary key"
             " unless you add one afterwards. It is a snapshot, not a"
             " view. Joining rides AND maintenance to bikes in one query"
             " pairs every ride of a bike with every job of it -- the"
             " fan-out -- so the trap's rides are multiplied by the"
             " jobs and its jobs by the rides, about 130,000 of each."
             " Two scalar subqueries, or two pre-aggregated subqueries"
             " joined on bike_id, count each table on its own.",
        claims=[("320 bikes, 38,605 rides and 1,100 jobs",
                 lambda rows, c: rows == [(320, 38605, 1100)])],
    ),
    dict(
        id=15, ledger="Q1191", concept="DEF", tier="5 - Changing the data",
        kind="script",
        title="A table that fills in what you leave out",
        prompt=(
            "Create a table incidents with: incident_id as the integer"
            " primary key; bike_id, required and referencing bikes;"
            " reported_on, text, required, defaulting to '2026-07-01';"
            " status, text, required, defaulting to 'open' and allowed"
            " only 'open' or 'closed'; cost_cents, integer, required,"
            " defaulting to 0 and never negative. The question then"
            " inserts three rows: one giving only a bike_id, one giving"
            " every column, and one with a status of 'lost', which must"
            " be refused.\n\n"
            "Checked: the rows that got in, all five columns"
        ),
        solution=("CREATE TABLE incidents (\n"
                  "  incident_id INTEGER PRIMARY KEY,\n"
                  "  bike_id     INTEGER NOT NULL REFERENCES bikes(bike_id),\n"
                  "  reported_on TEXT    NOT NULL DEFAULT '2026-07-01',\n"
                  "  status      TEXT    NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),\n"
                  "  cost_cents  INTEGER NOT NULL DEFAULT 0 CHECK (cost_cents >= 0)\n"
                  ");"),
        trap_sql=("CREATE TABLE incidents (\n"
                  "  incident_id INTEGER PRIMARY KEY,\n"
                  "  bike_id     INTEGER NOT NULL REFERENCES bikes(bike_id),\n"
                  "  reported_on TEXT,\n"
                  "  status      TEXT CHECK (status IN ('open', 'closed')),\n"
                  "  cost_cents  INTEGER CHECK (cost_cents >= 0)\n"
                  ");"),
        driver_sql=("INSERT INTO incidents (bike_id) VALUES (5);\n"
                    "INSERT INTO incidents (bike_id, reported_on, status, cost_cents) VALUES (6, '2026-06-30', 'closed', 1250);\n"
                    "INSERT INTO incidents (bike_id, status) VALUES (7, 'lost');"),
        probe_sql="SELECT incident_id, bike_id, reported_on, status, cost_cents FROM incidents ORDER BY incident_id",
        note="A DEFAULT is used when an INSERT does not mention the"
             " column, so a row given only a bike_id comes out complete:"
             " today's date, 'open', nothing owed. NOT NULL without a"
             " DEFAULT would REFUSE that insert; nullable without one,"
             " the trap, accepts it with three NULLs. The CHECK on"
             " status is what turns 'lost' away, and the status bar"
             " reports it. DEFAULT CURRENT_DATE would be the usual"
             " choice for a real table, but the sandbox needs a fixed"
             " date to grade.",
        claims=[("two rows in, the first filled by defaults",
                 lambda rows, c: rows == [(1, 5, "2026-07-01", "open", 0), (2, 6, "2026-06-30", "closed", 1250)])],
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
