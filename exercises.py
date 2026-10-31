"""Practice exercises: fifteen questions on the bike-hire schema.

The fifth set on the bike scheme (SEED 1206), two tools per question, the
tiers named by task, on tools no bike set has used. Reach and traffic --
the members who have started from every station in their zone by
relational division, a month-by-kind grid with its zeros by CROSS JOIN
and LEFT JOIN, each station's starts and ends by UNION ALL. Averages,
done right -- a median by ROW_NUMBER against COUNT, kilometres divided
by 1000.0 rather than 1000, a tariff that exists only in a VALUES CTE.
Between events -- a seven-day RANGE frame over julianday, a correlated
scalar subquery for the next ride after a repair, LEAD for the next job
on the same bike. Names, pairs and first months -- SUBSTR with INSTR, a
self-join on opened_on with a strict inequality, a LEFT JOIN whose
condition belongs in ON. And three WRITABLE questions, one statement
each:

  * an UPDATE ... FROM that joins members into the rides it changes
  * an INSERT ... SELECT guarded by NOT EXISTS
  * a DELETE through ROW_NUMBER, numbering the open jobs only

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
    # =================================================== 1 Reach and traffic
    dict(
        id=1, ledger="Q1132", concept="DIV", tier="1 - Reach and traffic",
        title="Riders who know their whole zone",
        prompt=(
            "For each zone: how many members have a home station in it,"
            " and how many of THOSE have started a ride from EVERY station"
            " of the zone. Relational division: a CTE counting the"
            " stations per zone, a CTE of the (member, home zone) pairs"
            " whose COUNT(DISTINCT start station in that zone) equals the"
            " zone's count, then one row per zone.\n\n"
            "Return: zone, members, complete"
        ),
        solution=("WITH z AS (SELECT zone, COUNT(*) AS n FROM stations GROUP BY zone),"
                  " done AS (SELECT m.member_id, h.zone FROM members m"
                  " JOIN stations h ON h.station_id = m.home_station_id"
                  " JOIN rides r ON r.member_id = m.member_id"
                  " JOIN stations s ON s.station_id = r.start_station_id AND s.zone = h.zone"
                  " GROUP BY m.member_id, h.zone"
                  " HAVING COUNT(DISTINCT s.station_id) = (SELECT n FROM z WHERE z.zone = h.zone))"
                  " SELECT h.zone, COUNT(*), (SELECT COUNT(*) FROM done d WHERE d.zone = h.zone)"
                  " FROM members m JOIN stations h ON h.station_id = m.home_station_id GROUP BY h.zone"),
        trap_sql=("WITH done AS (SELECT m.member_id, h.zone FROM members m"
                  " JOIN stations h ON h.station_id = m.home_station_id"
                  " JOIN rides r ON r.member_id = m.member_id"
                  " JOIN stations s ON s.station_id = r.start_station_id AND s.zone = h.zone"
                  " GROUP BY m.member_id, h.zone)"
                  " SELECT h.zone, COUNT(*), (SELECT COUNT(*) FROM done d WHERE d.zone = h.zone)"
                  " FROM members m JOIN stations h ON h.station_id = m.home_station_id GROUP BY h.zone"),
        note="'Every station' is a count compared with a count: the"
             " distinct stations a member has started from in the zone"
             " against the stations the zone has. Any join finds the"
             " members who have started from SOME station in their zone,"
             " which the trap counts -- 204 in the centre instead of 147."
             " Only three of the 313 bikes that have been ridden have not"
             " ended at all twelve stations, so the same trick on bikes"
             " would have little to say.",
        claims=[("five zones, the centre's 147 of 237",
                 lambda rows, c: len(rows) == 5 and ("centre", 237, 147) in rows),
                ("no zone is complete",
                 lambda rows, c: all(r[2] < r[1] for r in rows))],
    ),
    dict(
        id=2, ledger="Q1133", concept="CRS", tier="1 - Reach and traffic",
        title="Every kind, every month, zeros included",
        prompt=(
            "For each month of 2026 and each of the five kinds of job:"
            " how many jobs were reported, with 0 where there were none."
            " A CROSS JOIN of the distinct months -- strftime('%Y-%m',"
            " reported_at) for 2026 -- and the distinct kinds makes the"
            " full grid of thirty; a LEFT JOIN of maintenance onto it and"
            " COUNT(job_id) fills it in.\n\n"
            "Return: month, kind, jobs"
        ),
        solution=("SELECT mo.m, k.kind, COUNT(j.job_id)"
                  " FROM (SELECT DISTINCT strftime('%Y-%m', reported_at) AS m FROM maintenance WHERE reported_at >= '2026-01-01') mo"
                  " CROSS JOIN (SELECT DISTINCT kind FROM maintenance) k"
                  " LEFT JOIN maintenance j ON j.kind = k.kind AND strftime('%Y-%m', j.reported_at) = mo.m"
                  " GROUP BY mo.m, k.kind"),
        trap_sql=("SELECT strftime('%Y-%m', reported_at), kind, COUNT(*) FROM maintenance"
                  " WHERE reported_at >= '2026-01-01' GROUP BY 1, 2"),
        note="A GROUP BY can only count what is there, so a month with no"
             " battery job has no battery row: the trap returns"
             " twenty-seven rows and the three zeros are missing, which a"
             " chart or a report would silently skip. The CROSS JOIN"
             " builds every combination first; the LEFT JOIN then finds"
             " jobs for the ones that have them, and COUNT(job_id) -- not"
             " COUNT(*) -- gives 0 where the join found nothing.",
        claims=[("thirty cells, three of them zero",
                 lambda rows, c: len(rows) == 30 and sum(r[2] == 0 for r in rows) == 3),
                ("every zero is a battery month",
                 lambda rows, c: all(r[1] == "battery" for r in rows if r[2] == 0))],
    ),
    dict(
        id=3, ledger="Q1134", concept="UNA", tier="1 - Reach and traffic",
        title="Each station's traffic, both ends counted",
        prompt=(
            "For every station: the rides that started there, the rides"
            " that ended there, and the two added together. A UNION ALL"
            " of (start_station_id, 1 AS starts, 0 AS ends) from every"
            " ride and (end_station_id, 0, 1) from the finished ones,"
            " then one GROUP BY over the stacked rows, joined to stations"
            " for the name.\n\n"
            "Return: name, starts, ends, traffic"
        ),
        solution=("SELECT s.name, SUM(t.starts), SUM(t.ends), SUM(t.starts + t.ends)"
                  " FROM (SELECT start_station_id AS sid, 1 AS starts, 0 AS ends FROM rides"
                  " UNION ALL SELECT end_station_id, 0, 1 FROM rides WHERE end_station_id IS NOT NULL) t"
                  " JOIN stations s ON s.station_id = t.sid GROUP BY s.name"),
        trap_sql=("SELECT s.name, SUM(t.starts), SUM(t.ends), SUM(t.starts + t.ends)"
                  " FROM (SELECT start_station_id AS sid, 1 AS starts, 0 AS ends FROM rides"
                  " UNION SELECT end_station_id, 0, 1 FROM rides WHERE end_station_id IS NOT NULL) t"
                  " JOIN stations s ON s.station_id = t.sid GROUP BY s.name"),
        note="UNION ALL keeps every row; UNION removes duplicates, and"
             " here every row is a duplicate of thousands of others --"
             " (3, 1, 0) is the same row whichever ride produced it -- so"
             " the trap collapses 77,000 rows to twenty-four and counts"
             " one start and one end per station. Stacking the two ends"
             " of a ride as separate rows is what lets one GROUP BY count"
             " both; the alternative is two subqueries joined on"
             " station_id.",
        claims=[("twelve stations, Station Approach the busiest",
                 lambda rows, c: len(rows) == 12 and max(rows, key=lambda r: r[3])[0] == "Station Approach"),
                ("starts add up to every ride",
                 lambda rows, c: sum(r[1] for r in rows) == c.execute("SELECT COUNT(*) FROM rides").fetchone()[0])],
    ),
    # ================================================= 2 Averages, done right
    dict(
        id=4, ledger="Q1135", concept="MED", tier="2 - Averages, done right",
        title="The middle ride of each model",
        prompt=(
            "For each model: the MEDIAN distance of its finished rides, in"
            " metres. SQLite has no MEDIAN: in a CTE give every ride"
            " ROW_NUMBER() OVER (PARTITION BY model ORDER BY distance_m)"
            " and COUNT(*) OVER (PARTITION BY model), keep the rows"
            " numbered (n + 1) / 2 and (n + 2) / 2 -- the same row when n"
            " is odd, the two middle ones when it is even -- and AVG them"
            " per model.\n\n"
            "Return: model, median_m"
        ),
        solution=("WITH r AS (SELECT b.model, distance_m,"
                  " ROW_NUMBER() OVER (PARTITION BY b.model ORDER BY distance_m) AS rn,"
                  " COUNT(*) OVER (PARTITION BY b.model) AS n"
                  " FROM rides JOIN bikes b ON b.bike_id = rides.bike_id WHERE distance_m IS NOT NULL)"
                  " SELECT model, AVG(distance_m) FROM r WHERE rn IN ((n + 1) / 2, (n + 2) / 2) GROUP BY model"),
        trap_sql=("SELECT b.model, AVG(distance_m) FROM rides JOIN bikes b ON b.bike_id = rides.bike_id"
                  " WHERE distance_m IS NOT NULL GROUP BY b.model"),
        note="The mean is pulled up by the long rides: a classic's mean"
             " is 3,317 metres but its median 2,322, so half of all"
             " classic rides are under 2.3 km. (n + 1) / 2 and (n + 2) / 2"
             " are integer divisions, which is what makes them land on"
             " the middle row for odd n and on the two middle rows for"
             " even n; AVG of one row is that row.",
        claims=[("three models, the classic's median 2322",
                 lambda rows, c: len(rows) == 3 and ("classic", 2322.0) in rows),
                ("every median below its mean",
                 lambda rows, c: all(r[1] < c.execute("SELECT AVG(distance_m) FROM rides JOIN bikes b ON b.bike_id = rides.bike_id WHERE model = ?", (r[0],)).fetchone()[0] for r in rows))],
    ),
    dict(
        id=5, ledger="Q1136", concept="CST", tier="2 - Averages, done right",
        title="Kilometres per ride, by zone",
        prompt=(
            "For each zone, of the start station: the average distance of"
            " its finished rides in KILOMETRES, to two decimals. Average"
            " the metres, then divide by 1000.0 -- distance_m / 1000"
            " inside the AVG is integer division, which throws away the"
            " fraction of every ride before the average is taken.\n\n"
            "Return: zone, avg_km"
        ),
        solution=("SELECT s.zone, ROUND(AVG(r.distance_m) / 1000.0, 2) FROM rides r"
                  " JOIN stations s ON s.station_id = r.start_station_id"
                  " WHERE r.distance_m IS NOT NULL GROUP BY s.zone"),
        trap_sql=("SELECT s.zone, ROUND(AVG(r.distance_m / 1000), 2) FROM rides r"
                  " JOIN stations s ON s.station_id = r.start_station_id"
                  " WHERE r.distance_m IS NOT NULL GROUP BY s.zone"),
        note="distance_m is an INTEGER and 1000 is an integer, so 2,322 /"
             " 1000 is 2, not 2.322: the trap loses about half a"
             " kilometre from every zone. One of the operands has to be a"
             " real -- 1000.0, or CAST(distance_m AS REAL) -- and it is"
             " cheapest to do the division once, on the average, rather"
             " than on every row.",
        claims=[("five zones, all between 4 and 4.4 km",
                 lambda rows, c: len(rows) == 5 and all(4 <= r[1] <= 4.4 for r in rows))],
    ),
    dict(
        id=6, ledger="Q1137", concept="VAL", tier="2 - Averages, done right",
        title="What distance pricing would have raised",
        prompt=(
            "A tariff that exists nowhere in the database: 40 cents per"
            " kilometre on a classic, 60 on an electric, 80 on a cargo"
            " bike. Write it as a CTE of literal rows -- WITH tariff(model,"
            " cents_per_km) AS (VALUES ('classic', 40), ('electric', 60),"
            " ('cargo', 80)) -- join it to bikes ON model, and for each"
            " model return what the tariff would have charged for the"
            " finished rides, in dollars to two decimals (distance_m /"
            " 1000.0 * cents_per_km, summed, / 100), beside what their"
            " fares actually came to.\n\n"
            "Return: model, by_distance, charged"
        ),
        solution=("WITH tariff(model, cents_per_km) AS (VALUES ('classic', 40), ('electric', 60), ('cargo', 80))"
                  " SELECT b.model, ROUND(SUM(r.distance_m / 1000.0 * t.cents_per_km) / 100, 2), SUM(r.fare_cents) / 100.0"
                  " FROM rides r JOIN bikes b ON b.bike_id = r.bike_id JOIN tariff t ON t.model = b.model"
                  " WHERE r.distance_m IS NOT NULL GROUP BY b.model"),
        trap_sql=("WITH tariff(model, cents_per_km) AS (VALUES ('classic', 40), ('electric', 60), ('cargo', 80))"
                  " SELECT b.model, ROUND(SUM(r.distance_m / 1000.0 * t.cents_per_km) / 100, 2), SUM(r.fare_cents) / 100.0"
                  " FROM rides r JOIN bikes b ON b.bike_id = r.bike_id, tariff t"
                  " WHERE r.distance_m IS NOT NULL GROUP BY b.model"),
        note="A VALUES CTE is a table you type: a lookup that is not worth"
             " a real table, or a what-if to join against. It joins like"
             " any other, and like any other it needs its ON -- the trap"
             " lists tariff after a comma with no condition, which is a"
             " CROSS JOIN, so every ride is priced at all three rates and"
             " every total triples. Distance pricing would have raised"
             " twice what the electric bikes earned and less than the"
             " classics did.",
        claims=[("three models, classics would raise less than they charged",
                 lambda rows, c: len(rows) == 3 and all(r[1] < r[2] for r in rows if r[0] == "classic")),
                ("electric and cargo would raise more",
                 lambda rows, c: all(r[1] > r[2] for r in rows if r[0] != "classic"))],
    ),
    # ====================================================== 3 Between events
    dict(
        id=7, ledger="Q1138", concept="RNG", tier="3 - Between events",
        title="A week's worth of rides, by the clock",
        prompt=(
            "For each ride bike 7 started in June 2026: how many rides"
            " the bike had started in the SEVEN DAYS before it. A RANGE"
            " frame over julianday(started_at): COUNT(*) OVER (ORDER BY"
            " julianday(started_at) RANGE BETWEEN 7 PRECEDING AND CURRENT"
            " ROW) - 1, computed over ALL of bike 7's rides in a CTE and"
            " filtered to June afterwards -- the ride of 6 June has one"
            " of 31 May in its week.\n\n"
            "Return: ride_id, started_at, prior_week"
        ),
        solution=("WITH w AS (SELECT ride_id, started_at,"
                  " COUNT(*) OVER (ORDER BY julianday(started_at) RANGE BETWEEN 7 PRECEDING AND CURRENT ROW) - 1 AS prior_week"
                  " FROM rides WHERE bike_id = 7)"
                  " SELECT ride_id, started_at, prior_week FROM w WHERE started_at >= '2026-06-01'"),
        trap_sql=("SELECT ride_id, started_at,"
                  " COUNT(*) OVER (ORDER BY julianday(started_at) RANGE BETWEEN 7 PRECEDING AND CURRENT ROW) - 1"
                  " FROM rides WHERE bike_id = 7 AND started_at >= '2026-06-01'"),
        note="ROWS counts rows back; RANGE counts VALUE back, so 7"
             " PRECEDING over julianday is seven days whether the bike"
             " went out once or ten times in them, and a RANGE frame"
             " needs a numeric ORDER BY, which is what julianday is for."
             " Window functions run after WHERE, so the trap's June"
             " filter is applied first and 31 May is gone before the"
             " frame looks for it: the ride of 6 June shows 0 instead of"
             " 1.",
        claims=[("nine June rides, the sixth's week holding one",
                 lambda rows, c: len(rows) == 9 and any(r[0] == 744 and r[2] == 1 for r in rows)),
                ("the busiest week ran to five",
                 lambda rows, c: max(r[2] for r in rows) == 5)],
    ),
    dict(
        id=8, ledger="Q1139", concept="SUB", tier="3 - Between events",
        title="How soon a mended bike goes out again",
        prompt=(
            "For each kind of job: how many have been fixed, and the"
            " average DAYS from the fix to the bike's next ride, to two"
            " decimals. A correlated scalar subquery in the SELECT list"
            " finds the next ride -- (SELECT MIN(started_at) FROM rides r"
            " WHERE r.bike_id = m.bike_id AND r.started_at > m.fixed_at)"
            " -- and julianday of that minus julianday(fixed_at) is the"
            " wait. The 64 fixes never followed by a ride give NULL,"
            " which AVG skips.\n\n"
            "Return: kind, fixed, avg_days"
        ),
        solution=("SELECT m.kind, COUNT(*),"
                  " ROUND(AVG(julianday((SELECT MIN(r.started_at) FROM rides r WHERE r.bike_id = m.bike_id AND r.started_at > m.fixed_at)) - julianday(m.fixed_at)), 2)"
                  " FROM maintenance m WHERE m.fixed_at IS NOT NULL GROUP BY m.kind"),
        trap_sql=("SELECT m.kind, COUNT(*),"
                  " ROUND(AVG(julianday((SELECT MIN(r.started_at) FROM rides r WHERE r.bike_id = m.bike_id)) - julianday(m.fixed_at)), 2)"
                  " FROM maintenance m WHERE m.fixed_at IS NOT NULL GROUP BY m.kind"),
        note="A correlated subquery runs once per outer row, with that"
             " row's bike_id and fixed_at in scope, and a scalar one"
             " returns a single value, so it can sit in the SELECT list"
             " like a column. Drop the 'after the fix' condition and MIN"
             " finds the bike's first ride ever, usually long before the"
             " job: the trap's averages are large and negative. A"
             " mended bike is out again in four to five days.",
        claims=[("five kinds, every wait between 3 and 6 days",
                 lambda rows, c: len(rows) == 5 and all(3 <= r[2] <= 6 for r in rows)),
                ("986 fixes in all",
                 lambda rows, c: sum(r[1] for r in rows) == 986)],
    ),
    dict(
        id=9, ledger="Q1140", concept="LEAD", tier="3 - Between events",
        title="Days until the bike is back in the shop",
        prompt=(
            "For each kind of job: how many jobs of that kind were"
            " followed by another job on the same bike, and the average"
            " days until that next job, to one decimal. LEAD(reported_at)"
            " OVER (PARTITION BY bike_id ORDER BY reported_at) in a CTE"
            " puts the next job's date on each row; COUNT of that column"
            " counts only the rows that have one, and the last job on"
            " every bike has none.\n\n"
            "Return: kind, followed, avg_days"
        ),
        solution=("WITH j AS (SELECT kind, reported_at,"
                  " LEAD(reported_at) OVER (PARTITION BY bike_id ORDER BY reported_at) AS nxt FROM maintenance)"
                  " SELECT kind, COUNT(nxt), ROUND(AVG(julianday(nxt) - julianday(reported_at)), 1) FROM j GROUP BY kind"),
        trap_sql=("WITH j AS (SELECT kind, reported_at,"
                  " LEAD(reported_at) OVER (PARTITION BY bike_id ORDER BY reported_at) AS nxt FROM maintenance)"
                  " SELECT kind, COUNT(*), ROUND(AVG(julianday(nxt) - julianday(reported_at)), 1) FROM j GROUP BY kind"),
        note="LEAD looks forward where LAG looks back, and on the last"
             " row of each partition it returns NULL. COUNT(*) counts"
             " rows, NULL or not; COUNT(nxt) counts the rows where nxt is"
             " not NULL, which is the 'followed by another job' the"
             " question asks for -- the trap reports every job as"
             " followed, 452 punctures instead of 328. Whatever the job,"
             " the bike is back in about three months.",
        claims=[("five kinds, 328 punctures followed",
                 lambda rows, c: len(rows) == 5 and any(r[0] == "puncture" and r[1] == 328 for r in rows)),
                ("every average between 85 and 120 days",
                 lambda rows, c: all(85 <= r[2] <= 120 for r in rows))],
    ),
    # ====================================== 4 Names, pairs and first months
    dict(
        id=10, ledger="Q1141", concept="STR", tier="4 - Names, pairs and first months",
        title="The first names the scheme is full of",
        prompt=(
            "The first names shared by 38 or more members, with the"
            " count. The first name is everything before the first"
            " space: SUBSTR(name, 1, INSTR(name, ' ') - 1), grouped on."
            "\n\n"
            "Return: first_name, members"
        ),
        solution=("SELECT SUBSTR(name, 1, INSTR(name, ' ') - 1) AS first_name, COUNT(*)"
                  " FROM members GROUP BY first_name HAVING COUNT(*) >= 38"),
        trap_sql=("SELECT SUBSTR(name, 1, 5) AS first_name, COUNT(*)"
                  " FROM members GROUP BY first_name HAVING COUNT(*) >= 38"),
        note="INSTR finds where the space is, SUBSTR takes everything"
             " before it, and the two together cut a first name of any"
             " length. A fixed SUBSTR(name, 1, 5) cuts 'Rosa ' with its"
             " space and 'Elean' without its -or, and loses Xiu altogether"
             " because 'Xiu U', 'Xiu S' and 'Xiu B' are three different"
             " groups. Eight first names each cover more than four per"
             " cent of the members.",
        claims=[("eight names, Xiu the most common",
                 lambda rows, c: len(rows) == 8 and max(rows, key=lambda r: r[1])[0] == "Xiu")],
    ),
    dict(
        id=11, ledger="Q1142", concept="SLF", tier="4 - Names, pairs and first months",
        title="Stations that opened together",
        prompt=(
            "Every pair of stations that opened on the same day, each"
            " pair once, by name. A self-join of stations on opened_on"
            " with a.station_id < b.station_id, so that a station is never"
            " paired with itself and (Market Square, Cathedral) does not"
            " come back again as (Cathedral, Market Square).\n\n"
            "Return: first, second"
        ),
        solution=("SELECT a.name, b.name FROM stations a JOIN stations b"
                  " ON b.opened_on = a.opened_on AND a.station_id < b.station_id"),
        trap_sql=("SELECT a.name, b.name FROM stations a JOIN stations b"
                  " ON b.opened_on = a.opened_on AND a.station_id <> b.station_id"),
        note="A self-join compares rows of one table with each other,"
             " and the join condition decides which comparisons count."
             " <> only stops a station meeting itself: every pair still"
             " appears twice, once each way round, and the trap returns"
             " twelve rows for six pairs. < keeps one ordering of each"
             " pair. Four stations opened on the scheme's first day, which"
             " is six pairs.",
        claims=[("six pairs",
                 lambda rows, c: len(rows) == 6),
                ("Market Square in three of them",
                 lambda rows, c: sum("Market Square" in r for r in rows) == 3)],
    ),
    dict(
        id=12, ledger="Q1143", concept="FST", tier="4 - Names, pairs and first months",
        title="The first month of membership",
        prompt=(
            "For each plan: its members, the rides they took in their"
            " first thirty days -- started_at before date(joined_on, '+30"
            " days') -- and the rides per member, to two decimals. The"
            " thirty-day condition belongs in the LEFT JOIN's ON clause:"
            " in WHERE it drops every member without such a ride, and"
            " the per-member figure is for the keen ones only.\n\n"
            "Return: plan, members, first_month_rides, per_member"
        ),
        solution=("SELECT m.plan, COUNT(DISTINCT m.member_id), COUNT(r.ride_id),"
                  " ROUND(1.0 * COUNT(r.ride_id) / COUNT(DISTINCT m.member_id), 2)"
                  " FROM members m LEFT JOIN rides r ON r.member_id = m.member_id"
                  " AND r.started_at < date(m.joined_on, '+30 days') GROUP BY m.plan"),
        trap_sql=("SELECT m.plan, COUNT(DISTINCT m.member_id), COUNT(r.ride_id),"
                  " ROUND(1.0 * COUNT(r.ride_id) / COUNT(DISTINCT m.member_id), 2)"
                  " FROM members m LEFT JOIN rides r ON r.member_id = m.member_id"
                  " WHERE r.started_at < date(m.joined_on, '+30 days') GROUP BY m.plan"),
        note="In a LEFT JOIN, ON decides which right-hand rows attach;"
             " WHERE runs afterwards on the joined rows, and a condition"
             " on the right-hand table there turns the LEFT JOIN into an"
             " inner one, because the NULLs of the unmatched members fail"
             " it. The trap keeps 138 annual members instead of 324 and"
             " reports 21.6 rides per member instead of 9.2. The rides"
             " begin in 2025 and many members joined before that, which"
             " is why the first-month figures are low.",
        claims=[("three plans, 324 annual members",
                 lambda rows, c: len(rows) == 3 and any(r[0] == "annual" and r[1] == 324 for r in rows)),
                ("members add up to 900",
                 lambda rows, c: sum(r[1] for r in rows) == 900)],
    ),
    # =================================================== 5 Changing the data
    dict(
        id=13, ledger="Q1144", concept="UPF", tier="5 - Changing the data",
        kind="script",
        title="Short rides go free for annual members",
        prompt=(
            "From June 2026 an annual member's ride under five"
            " kilometres is free. ONE statement: UPDATE rides SET"
            " fare_cents = 0 FROM members m WHERE the ride's member_id is"
            " m.member_id, m.plan is 'annual', distance_m < 5000,"
            " started_at >= '2026-06-01' and fare_cents > 0. The FROM"
            " clause joins another table into an UPDATE, so the plan can"
            " be tested without a subquery.\n\n"
            "Checked: the fares' total, and how many rides are free"
        ),
        solution=("UPDATE rides SET fare_cents = 0 FROM members m"
                  " WHERE rides.member_id = m.member_id AND m.plan = 'annual'"
                  " AND rides.distance_m < 5000 AND rides.started_at >= '2026-06-01' AND rides.fare_cents > 0;"),
        trap_sql=("UPDATE rides SET fare_cents = 0"
                  " WHERE member_id IS NOT NULL"
                  " AND distance_m < 5000 AND started_at >= '2026-06-01' AND fare_cents > 0;"),
        probe_sql="SELECT SUM(fare_cents), SUM(fare_cents = 0) FROM rides",
        note="UPDATE ... FROM (SQLite 3.33 and later) is a join inside an"
             " UPDATE: the FROM table's columns are available in WHERE and"
             " in the SET expressions. Without it the plan test needs a"
             " subquery -- WHERE member_id IN (SELECT member_id FROM"
             " members WHERE plan = 'annual') -- and the trap, which"
             " skips the test, gives every member's short June ride"
             " away: 264 rides and $567 instead of 22 rides and $24.",
        claims=[("22 rides freed, $24 forgone",
                 lambda rows, c: rows == [(6667950 - 2400, 38605 - 22732 + 22)])],
    ),
    dict(
        id=14, ledger="Q1145", concept="INS", tier="5 - Changing the data",
        kind="script",
        title="A brake check for every cargo bike without a job",
        prompt=(
            "Open a 'brakes' job on every cargo bike still in the fleet"
            " that has NO open job: INSERT INTO maintenance (bike_id,"
            " station_id, reported_at, kind, cost_cents) SELECT ... FROM"
            " bikes b WHERE the model is 'cargo', retired_on IS NULL and"
            " NOT EXISTS an open job for b.bike_id -- at station 1,"
            " reported '2026-07-01 09:00', cost 0. job_id numbers itself"
            " and fixed_at stays NULL, which is what makes the job open."
            "\n\n"
            "Checked: how many jobs there are, how many open brakes jobs,"
            " and how many bikes have more than one open job"
        ),
        solution=("INSERT INTO maintenance (bike_id, station_id, reported_at, kind, cost_cents)"
                  " SELECT b.bike_id, 1, '2026-07-01 09:00', 'brakes', 0 FROM bikes b"
                  " WHERE b.model = 'cargo' AND b.retired_on IS NULL"
                  " AND NOT EXISTS (SELECT 1 FROM maintenance m WHERE m.bike_id = b.bike_id AND m.fixed_at IS NULL);"),
        trap_sql=("INSERT INTO maintenance (bike_id, station_id, reported_at, kind, cost_cents)"
                  " SELECT b.bike_id, 1, '2026-07-01 09:00', 'brakes', 0 FROM bikes b"
                  " WHERE b.model = 'cargo' AND b.retired_on IS NULL;"),
        probe_sql=("SELECT COUNT(*), SUM(kind = 'brakes' AND fixed_at IS NULL),"
                   " (SELECT COUNT(*) FROM (SELECT 1 FROM maintenance WHERE fixed_at IS NULL GROUP BY bike_id HAVING COUNT(*) > 1))"
                   " FROM maintenance"),
        note="INSERT ... SELECT writes as many rows as the SELECT returns,"
             " so the SELECT's WHERE is the whole policy: literals for"
             " the columns that are the same on every row, a column for"
             " the one that is not, and NOT EXISTS for 'no open job"
             " already'. The trap drops the NOT EXISTS and opens a job on"
             " all 29 cargo bikes, ten of which were already in the"
             " queue, which leaves 24 bikes with two open jobs instead of"
             " 18.",
        claims=[("nineteen jobs opened, no bike queued twice over",
                 lambda rows, c: rows == [(1100 + 19, 23 + 19, 18)])],
    ),
    dict(
        id=15, ledger="Q1146", concept="DDP", tier="5 - Changing the data",
        kind="script",
        title="One open job per bike",
        prompt=(
            "Where a bike has more than one open job, keep the EARLIEST"
            " by reported_at and delete the rest. DELETE FROM maintenance"
            " WHERE job_id IN (...) with a subquery that numbers the OPEN"
            " jobs -- ROW_NUMBER() OVER (PARTITION BY bike_id ORDER BY"
            " reported_at), in a subquery whose WHERE keeps fixed_at IS"
            " NULL -- and returns the job_ids numbered above 1. The"
            " numbering must run over open jobs only: numbered over every"
            " job, a bike's only open job can be its third and go.\n\n"
            "Checked: how many jobs remain, how many are open, and how"
            " many bikes still have more than one open job"
        ),
        solution=("DELETE FROM maintenance WHERE job_id IN"
                  " (SELECT job_id FROM (SELECT job_id, ROW_NUMBER() OVER (PARTITION BY bike_id ORDER BY reported_at) AS rn"
                  " FROM maintenance WHERE fixed_at IS NULL) WHERE rn > 1);"),
        trap_sql=("DELETE FROM maintenance WHERE fixed_at IS NULL AND job_id IN"
                  " (SELECT job_id FROM (SELECT job_id, ROW_NUMBER() OVER (PARTITION BY bike_id ORDER BY reported_at) AS rn"
                  " FROM maintenance) WHERE rn > 1);"),
        probe_sql=("SELECT COUNT(*), SUM(fixed_at IS NULL),"
                   " (SELECT COUNT(*) FROM (SELECT 1 FROM maintenance WHERE fixed_at IS NULL GROUP BY bike_id HAVING COUNT(*) > 1))"
                   " FROM maintenance"),
        note="A window function cannot sit in a DELETE's WHERE, but it"
             " can number rows in a subquery, and the DELETE can pick the"
             " job_ids it produced. The numbering belongs to the rows the"
             " subquery sees: filter to open jobs INSIDE it and the"
             " second open job of a bike is number 2; filter outside and"
             " a bike's only open job is numbered after its fixed ones"
             " and deleted too. The trap removes 80 open jobs; the"
             " answer removes the 23 that were queued behind another.",
        claims=[("23 later open jobs gone, no bike queued twice",
                 lambda rows, c: rows == [(1100 - 23, 114 - 23, 0)])],
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
