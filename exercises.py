"""Practice exercises: fifteen questions on the bike-hire schema.

The tenth set on the bike scheme (SEED 1206), two tools per question, the
tiers named by task, on tools no bike set has used, with prompts that name
the tool but do not write the statement. Who, exactly -- an EXISTS used as
a column, a FULL OUTER JOIN of payers and riders, IS NOT where <> would
drop the open rides. Rank and share -- PERCENT_RANK among a bike's
model-mates, two window sums with two different partitions in one query,
a one-in-a-hundred sample by the modulo operator. The clock and the
calendar -- rides by week number, rides that began on the hour, an exact
age with the birthday-not-yet adjustment. Capacity and balance -- rides
per dock per active day, stations out of balance by ABS, the first casual
and first member ride by MIN of a CASE. And three WRITABLE questions:

  * a REPLACE INTO that re-records a payment
  * a table renamed, with a view keeping the old name alive
  * a STORED generated column, told from VIRTUAL by pragma_table_xinfo

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
    # ========================================================= 1 Who, exactly
    dict(
        id=1, ledger="Q1207", concept="EXS", tier="1 - Who, exactly",
        title="Has this station ever seen a battery job?",
        prompt=(
            "For every station: a 1 or 0 saying whether a battery job"
            " has ever been reported there, and how many have. EXISTS"
            " is an expression, so it can sit in the SELECT list as a"
            " column; a scalar subquery gives the count.\n\n"
            "Return: name, had_battery_job, battery_jobs"
        ),
        solution=("SELECT s.name,"
                  " EXISTS (SELECT 1 FROM maintenance m WHERE m.station_id = s.station_id AND m.kind = 'battery'),"
                  " (SELECT COUNT(*) FROM maintenance m WHERE m.station_id = s.station_id AND m.kind = 'battery')"
                  " FROM stations s"),
        trap_sql=("SELECT s.name, COUNT(*) > 0, COUNT(*)"
                  " FROM stations s LEFT JOIN maintenance m ON m.station_id = s.station_id AND m.kind = 'battery'"
                  " GROUP BY s.name"),
        note="EXISTS returns 1 or 0 and can be used anywhere an"
             " expression can, not only in WHERE: as a flag column it"
             " answers 'is there any?' without a join. The trap's LEFT"
             " JOIN keeps a row for every station even when nothing"
             " matched, and COUNT(*) counts that row, so every station"
             " shows 1 and one job. Three stations have never had a"
             " battery job reported.",
        claims=[("twelve stations, three without",
                 lambda rows, c: len(rows) == 12 and sum(r[1] == 0 for r in rows) == 3),
                ("the flag agrees with the count",
                 lambda rows, c: all((r[1] == 1) == (r[2] > 0) for r in rows))],
    ),
    dict(
        id=2, ledger="Q1208", concept="FOJ", tier="1 - Who, exactly",
        title="Paid, rode, or both",
        prompt=(
            "For each plan: members who have paid a subscription but"
            " never ridden, members who have ridden but never paid one,"
            " and members who have done both. A FULL OUTER JOIN between"
            " the distinct paying members and the distinct riding"
            " members keeps the members on either side alone; COALESCE"
            " the two ids to reach the plan.\n\n"
            "Return: plan, paid_never_rode, rode_never_paid, both"
        ),
        solution=("WITH p AS (SELECT DISTINCT member_id FROM payments WHERE member_id IS NOT NULL),"
                  " r AS (SELECT DISTINCT member_id FROM rides WHERE member_id IS NOT NULL)"
                  " SELECT m.plan, SUM(r.member_id IS NULL), SUM(p.member_id IS NULL), SUM(p.member_id IS NOT NULL AND r.member_id IS NOT NULL)"
                  " FROM p FULL OUTER JOIN r ON r.member_id = p.member_id"
                  " JOIN members m ON m.member_id = COALESCE(p.member_id, r.member_id) GROUP BY m.plan"),
        trap_sql=("WITH p AS (SELECT DISTINCT member_id FROM payments WHERE member_id IS NOT NULL),"
                  " r AS (SELECT DISTINCT member_id FROM rides WHERE member_id IS NOT NULL)"
                  " SELECT m.plan, SUM(r.member_id IS NULL), SUM(p.member_id IS NULL), SUM(p.member_id IS NOT NULL AND r.member_id IS NOT NULL)"
                  " FROM p LEFT JOIN r ON r.member_id = p.member_id"
                  " JOIN members m ON m.member_id = COALESCE(p.member_id, r.member_id) GROUP BY m.plan"),
        note="FULL OUTER JOIN (SQLite 3.39 and later) keeps the"
             " unmatched rows of BOTH sides, so one query sees the"
             " payers without rides and the riders without payments; a"
             " LEFT JOIN, the trap, keeps only the left side's strays"
             " and never meets the 196 riders who were never named on a"
             " payment -- the pay-as-you-go plan vanishes entirely. The"
             " two NULL tests tell the three groups apart.",
        claims=[("three plans, every pay-as-you-go rider unnamed on a payment",
                 lambda rows, c: len(rows) == 3 and ("pay-as-you-go", 0, 186, 0) in rows),
                ("81 subscribers paid and never rode",
                 lambda rows, c: sum(r[1] for r in rows) == 81)],
    ),
    dict(
        id=3, ledger="Q1209", concept="ISNOT", tier="1 - Who, exactly",
        title="Rides that went somewhere else, open ones included",
        prompt=(
            "For each zone, of the start station: its rides, and how"
            " many did NOT end where they began -- counting a ride"
            " still out, whose end station is NULL, as not a round"
            " trip. The NULL-safe comparison is IS NOT, which <> is"
            " not.\n\n"
            "Return: zone, rides, not_round_trips"
        ),
        solution=("SELECT s.zone, COUNT(*), SUM(r.end_station_id IS NOT r.start_station_id)"
                  " FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.zone"),
        trap_sql=("SELECT s.zone, COUNT(*), SUM(r.end_station_id <> r.start_station_id)"
                  " FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.zone"),
        note="NULL <> 5 is NULL, not true, and SUM skips it, so the trap"
             " leaves the 35 open rides out of every count. IS and IS NOT"
             " treat NULL as a value: NULL IS NOT 5 is true, and NULL IS"
             " NULL is true. The difference is small here -- 35 rides in"
             " 38,605 -- which is exactly how this kind of error hides.",
        claims=[("five zones, the centre's 8701",
                 lambda rows, c: len(rows) == 5 and ("centre", 10361, 8701) in rows),
                ("35 more than the <> version in all",
                 lambda rows, c: sum(r[2] for r in rows) == 32522)],
    ),
    # ======================================================= 2 Rank and share
    dict(
        id=4, ledger="Q1210", concept="PRK", tier="2 - Rank and share",
        title="Where each bike stands among its model",
        prompt=(
            "For bikes 1 to 10: the model, the bike's rides, and the"
            " share of its model-mates that have FEWER rides, as a"
            " fraction from 0 to 1 to three decimals. PERCENT_RANK"
            " over the model's bikes, computed over every bike in a"
            " CTE and filtered afterwards; bikes never ridden count as"
            " 0 rides.\n\n"
            "Return: bike_id, model, rides, pct_rank"
        ),
        solution=("WITH per AS (SELECT b.bike_id, b.model, COUNT(r.ride_id) AS n FROM bikes b LEFT JOIN rides r ON r.bike_id = b.bike_id GROUP BY b.bike_id),"
                  " w AS (SELECT bike_id, model, n, ROUND(PERCENT_RANK() OVER (PARTITION BY model ORDER BY n), 3) AS pr FROM per)"
                  " SELECT bike_id, model, n, pr FROM w WHERE bike_id <= 10"),
        trap_sql=("WITH per AS (SELECT b.bike_id, b.model, COUNT(r.ride_id) AS n FROM bikes b LEFT JOIN rides r ON r.bike_id = b.bike_id GROUP BY b.bike_id),"
                  " w AS (SELECT bike_id, model, n, ROUND(CUME_DIST() OVER (PARTITION BY model ORDER BY n), 3) AS pr FROM per)"
                  " SELECT bike_id, model, n, pr FROM w WHERE bike_id <= 10"),
        note="PERCENT_RANK is (rank - 1) / (rows - 1): the share of the"
             " partition strictly BELOW the row, 0 for the lowest and 1"
             " for the highest. CUME_DIST, the trap, is the share at or"
             " below, which counts the row itself and its ties, so the"
             " lowest bike gets a small positive number instead of 0."
             " Bike 2, with 43 rides, is below 96 per cent of the"
             " classics.",
        claims=[("ten bikes, bike 2 at 0.039",
                 lambda rows, c: len(rows) == 10 and (2, "classic", 43, 0.039) in rows),
                ("bikes 3 and 4 tie",
                 lambda rows, c: [r[3] for r in rows if r[0] in (3, 4)] == [0.311, 0.311])],
    ),
    dict(
        id=5, ledger="Q1211", concept="TWOWIN", tier="2 - Rank and share",
        title="Each station's share of its zone, and of everything",
        prompt=(
            "For every station: its zone, its rides, its share of the"
            " ZONE's rides and its share of ALL rides, both as"
            " percentages to one decimal. Two window SUMs over a CTE of"
            " rides per station: one partitioned by zone, one over the"
            " whole result.\n\n"
            "Return: name, zone, rides, zone_pct, all_pct"
        ),
        solution=("WITH per AS (SELECT s.zone, s.name, COUNT(*) AS n FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.station_id)"
                  " SELECT name, zone, n, ROUND(100.0 * n / SUM(n) OVER (PARTITION BY zone), 1), ROUND(100.0 * n / SUM(n) OVER (), 1) FROM per"),
        trap_sql=("WITH per AS (SELECT s.zone, s.name, COUNT(*) AS n FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.station_id)"
                  " SELECT name, zone, n, ROUND(100.0 * n / SUM(n) OVER (), 1), ROUND(100.0 * n / SUM(n) OVER (), 1) FROM per"),
        note="Each window has its own OVER clause, so one query can"
             " total by zone and overall at once: the same SUM(n) with"
             " two different partitions. The trap uses the whole-result"
             " window twice and the zone share is just the overall share"
             " again. The two-station zones split roughly in half; in"
             " the centre, Market Square takes 37 per cent.",
        claims=[("twelve stations, Market Square 37.0 of its zone and 9.9 of all",
                 lambda rows, c: len(rows) == 12 and ("Market Square", "centre", 3834, 37.0, 9.9) in rows),
                ("each zone's shares add to a hundred",
                 lambda rows, c: all(abs(sum(r[3] for r in rows if r[1] == z) - 100) < 0.2 for z in {r[1] for r in rows}))],
    ),
    dict(
        id=6, ledger="Q1212", concept="MOD", tier="2 - Rank and share",
        title="A one-in-a-hundred sample",
        prompt=(
            "For each model: how many rides fall in a one-in-a-hundred"
            " sample -- the rides whose ride_id is a multiple of 100 --"
            " the sample's average distance in whole metres, and the"
            " average over every ride of the model. The modulo operator"
            " % picks the sample; a CASE inside AVG keeps the other"
            " rides out of it.\n\n"
            "Return: model, sampled, sample_avg_m, all_avg_m"
        ),
        solution=("SELECT b.model, SUM(r.ride_id % 100 = 0), ROUND(AVG(CASE WHEN r.ride_id % 100 = 0 THEN r.distance_m END)), ROUND(AVG(r.distance_m))"
                  " FROM rides r JOIN bikes b ON b.bike_id = r.bike_id GROUP BY b.model"),
        trap_sql=("SELECT b.model, SUM(r.ride_id % 100 = 0), ROUND(AVG(CASE WHEN r.ride_id % 100 = 0 THEN r.distance_m ELSE 0 END)), ROUND(AVG(r.distance_m))"
                  " FROM rides r JOIN bikes b ON b.bike_id = r.bike_id GROUP BY b.model"),
        note="x % 100 = 0 is true for one id in a hundred, and since"
             " ids are handed out in order it is a fair sample of the"
             " table -- 386 rides. A CASE with no ELSE gives NULL for"
             " the rest and AVG skips NULLs; with ELSE 0, the trap, the"
             " non-sample rides are averaged in as zero-metre rides and"
             " the sample average collapses. The classic and electric"
             " samples land within a few per cent of the truth; the"
             " cargo sample, 36 rides, is off by a sixth.",
        claims=[("three models, 253 classic rides sampled",
                 lambda rows, c: len(rows) == 3 and any(r[0] == "classic" and r[1] == 253 for r in rows)),
                ("386 sampled in all",
                 lambda rows, c: sum(r[1] for r in rows) == 386)],
    ),
    # ============================================ 3 The clock and the calendar
    dict(
        id=7, ledger="Q1213", concept="WK", tier="3 - The clock and the calendar",
        title="Rides by week of the year, 2026",
        prompt=(
            "For 2026: rides per week number, weeks starting on Monday,"
            " '00' for the days before the first Monday. strftime has"
            " two week-number codes; one counts Monday-led weeks and"
            " the other Sunday-led.\n\n"
            "Return: week, rides"
        ),
        solution="SELECT strftime('%W', started_at), COUNT(*) FROM rides WHERE started_at >= '2026-01-01' GROUP BY strftime('%W', started_at)",
        trap_sql="SELECT strftime('%U', started_at), COUNT(*) FROM rides WHERE started_at >= '2026-01-01' GROUP BY strftime('%U', started_at)",
        note="%W numbers the weeks from the first Monday of the year,"
             " %U from the first Sunday; both call the days before that"
             " week 00, which is why week 00 is short. The trap's %U"
             " shifts every boundary by a day and most counts with it."
             " Week 26 is short too: the data stops on a Tuesday.",
        claims=[("27 weeks, week 01 with 510 rides",
                 lambda rows, c: len(rows) == 27 and ("01", 510) in rows),
                ("weeks 00 and 26 the short ones",
                 lambda rows, c: sorted(rows, key=lambda r: r[1])[:2] == [("26", 160), ("00", 291)])],
    ),
    dict(
        id=8, ledger="Q1214", concept="MIN00", tier="3 - The clock and the calendar",
        title="Rides that began on the hour",
        prompt=(
            "For each zone, of the start station: its rides, how many"
            " started at exactly zero minutes past an hour, and that as"
            " a percentage to two decimals. strftime has a code for the"
            " minute of the hour.\n\n"
            "Return: zone, rides, on_the_hour, pct"
        ),
        solution=("SELECT s.zone, COUNT(*), SUM(strftime('%M', r.started_at) = '00'),"
                  " ROUND(100.0 * SUM(strftime('%M', r.started_at) = '00') / COUNT(*), 2)"
                  " FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.zone"),
        trap_sql=("SELECT s.zone, COUNT(*), SUM(strftime('%S', r.started_at) = '00'),"
                  " ROUND(100.0 * SUM(strftime('%S', r.started_at) = '00') / COUNT(*), 2)"
                  " FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.zone"),
        note="%M is the minute, %S the second -- and since the data"
             " records minutes only, every ride's seconds are 00, so the"
             " trap counts all of them. One ride in sixty would start on"
             " the hour by chance, 1.67 per cent, and the zones sit"
             " close to that: the start times are random to the minute.",
        claims=[("five zones, each between 1.5 and 2 per cent",
                 lambda rows, c: len(rows) == 5 and all(1.5 <= r[3] <= 2 for r in rows)),
                ("the centre's 188 on the hour",
                 lambda rows, c: ("centre", 10361, 188, 1.81) in rows)],
    ),
    dict(
        id=9, ledger="Q1215", concept="AGEX", tier="3 - The clock and the calendar",
        title="Members who were 65 or over when the data ends",
        prompt=(
            "For each plan: its members, and how many were 65 or"
            " older on 2026-06-30 -- an EXACT age, so a member whose"
            " 65th birthday fell in July 2026 is not counted. Take the"
            " difference of the years, then subtract one if the"
            " birthday's month-and-day had not yet come round.\n\n"
            "Return: plan, members, seniors"
        ),
        solution=("SELECT plan, COUNT(*),"
                  " SUM((strftime('%Y', '2026-06-30') - strftime('%Y', born_on))"
                  " - (strftime('%m-%d', '2026-06-30') < strftime('%m-%d', born_on)) >= 65)"
                  " FROM members GROUP BY plan"),
        trap_sql=("SELECT plan, COUNT(*),"
                  " SUM(strftime('%Y', '2026-06-30') - strftime('%Y', born_on) >= 65)"
                  " FROM members GROUP BY plan"),
        note="Subtracting years gives the age a person turns THIS year,"
             " which is one too many for anyone whose birthday is still"
             " ahead; comparing 'MM-DD' text, which sorts correctly,"
             " says whether it is, and subtracting that true-or-false"
             " (1 or 0) corrects it. The trap counts ten members who"
             " were still 64 on 30 June. A quarter of the members are"
             " 65 or over.",
        claims=[("three plans, 87 annual seniors",
                 lambda rows, c: len(rows) == 3 and ("annual", 324, 87) in rows),
                ("256 seniors in all",
                 lambda rows, c: sum(r[2] for r in rows) == 256)],
    ),
    # ================================================ 4 Capacity and balance
    dict(
        id=10, ledger="Q1216", concept="UTIL", tier="4 - Capacity and balance",
        title="How hard each dock works",
        prompt=(
            "For every station: its docks, its rides, the number of"
            " DAYS on which a ride started there, and the rides per"
            " dock per active day to three decimals. The active days"
            " are a COUNT of DISTINCT dates; Old Mill's are fewer, and"
            " dividing by the data's 546 days instead would understate"
            " it.\n\n"
            "Return: name, docks, rides, active_days, per_dock_day"
        ),
        solution=("SELECT s.name, s.docks, COUNT(*), COUNT(DISTINCT date(r.started_at)),"
                  " ROUND(1.0 * COUNT(*) / s.docks / COUNT(DISTINCT date(r.started_at)), 3)"
                  " FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.station_id"),
        trap_sql=("SELECT s.name, s.docks, COUNT(*), COUNT(DISTINCT date(r.started_at)),"
                  " ROUND(1.0 * COUNT(*) / s.docks / 546, 3)"
                  " FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.station_id"),
        note="A rate per day needs the right number of days, and"
             " COUNT(DISTINCT date(...)) counts the days the station was"
             " actually in use: Old Mill closed in March and has 422,"
             " not 546. The trap divides every station by the full span"
             " and makes the closed station look idle when, per dock"
             " per day, it was the busiest of all. Big stations have"
             " spare docks; Hilltop's sixteen are the busiest among the"
             " open ones.",
        claims=[("twelve stations, Old Mill's 422 active days",
                 lambda rows, c: len(rows) == 12 and ("Old Mill", 14, 2500, 422, 0.423) in rows),
                ("Old Mill the busiest per dock",
                 lambda rows, c: max(rows, key=lambda r: r[4])[0] == "Old Mill")],
    ),
    dict(
        id=11, ledger="Q1217", concept="ABS", tier="4 - Capacity and balance",
        title="Stations out of balance",
        prompt=(
            "The stations where rides ending and rides starting differ"
            " by MORE than a hundred, in either direction: the starts,"
            " the ends, and the net gain (ends minus starts, negative"
            " for a drain). Two scalar subqueries per station, and ABS"
            " in the WHERE.\n\n"
            "Return: name, starts, ends, net"
        ),
        solution=("WITH t AS (SELECT s.name, (SELECT COUNT(*) FROM rides WHERE start_station_id = s.station_id) AS starts,"
                  " (SELECT COUNT(*) FROM rides WHERE end_station_id = s.station_id) AS ends FROM stations s)"
                  " SELECT name, starts, ends, ends - starts FROM t WHERE ABS(ends - starts) > 100"),
        trap_sql=("WITH t AS (SELECT s.name, (SELECT COUNT(*) FROM rides WHERE start_station_id = s.station_id) AS starts,"
                  " (SELECT COUNT(*) FROM rides WHERE end_station_id = s.station_id) AS ends FROM stations s)"
                  " SELECT name, starts, ends, ends - starts FROM t WHERE ends - starts > 100"),
        note="'Differ by more than a hundred' is a condition on the"
             " size of the difference, whatever its sign, and ABS is"
             " how a WHERE says so. Without it the trap keeps only the"
             " stations that GAIN bikes and misses the two that drain."
             " Station Approach gains nearly 800 bikes over the data and"
             " Market Square loses nearly 600, which is what the crew's"
             " van is for.",
        claims=[("three stations, two draining and one filling",
                 lambda rows, c: len(rows) == 3 and sum(r[3] < 0 for r in rows) == 2),
                ("Station Approach up 794",
                 lambda rows, c: ("Station Approach", 3214, 4008, 794) in rows)],
    ),
    dict(
        id=12, ledger="Q1218", concept="MINC", tier="4 - Capacity and balance",
        title="The first casual ride and the first member ride",
        prompt=(
            "For every station: when its first ride by a casual rider"
            " started, and when its first ride by a member did. One"
            " pass over rides: MIN of a CASE that yields the timestamp"
            " only for the rows of each kind, and nothing -- NULL --"
            " for the others.\n\n"
            "Return: name, first_casual, first_member"
        ),
        solution=("SELECT s.name, MIN(CASE WHEN r.member_id IS NULL THEN r.started_at END),"
                  " MIN(CASE WHEN r.member_id IS NOT NULL THEN r.started_at END)"
                  " FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.name"),
        trap_sql=("SELECT s.name, MIN(CASE WHEN r.member_id IS NULL THEN r.started_at ELSE '' END),"
                  " MIN(CASE WHEN r.member_id IS NOT NULL THEN r.started_at ELSE '' END)"
                  " FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.name"),
        note="MIN skips NULLs, so a CASE with no ELSE hands it only the"
             " rows that qualify, and two such CASEs give two"
             " conditional minimums from one scan. Give the CASE an"
             " ELSE '' and the empty string, which sorts before every"
             " timestamp, becomes the minimum everywhere: the trap"
             " returns blanks. Every station had both kinds of rider"
             " within its first week.",
        claims=[("twelve stations, every first ride in the first week of 2025",
                 lambda rows, c: len(rows) == 12 and all(r[1] < "2025-01-08" and r[2] < "2025-01-08" for r in rows)),
                ("Old Mill's first ride was casual",
                 lambda rows, c: any(r[0] == "Old Mill" and r[1] < r[2] for r in rows))],
    ),
    # =================================================== 5 Changing the data
    dict(
        id=13, ledger="Q1219", concept="RPL", tier="5 - Changing the data",
        kind="script",
        title="A payment re-recorded",
        prompt=(
            "Payment 1 was keyed in wrong: it was 350 cents by card,"
            " not 300 by app. Re-record it in ONE statement, keeping"
            " payment_id 1, ride 12152 and the time '2025-01-01 02:42':"
            " REPLACE INTO writes the row as given, removing the old"
            " row with that id first.\n\n"
            "Checked: payment 1's amount and method, how many payments"
            " there are, and the highest payment_id"
        ),
        solution=("REPLACE INTO payments (payment_id, ride_id, amount_cents, paid_at, method)"
                  " VALUES (1, 12152, 350, '2025-01-01 02:42', 'card');"),
        trap_sql=("INSERT OR IGNORE INTO payments (payment_id, ride_id, amount_cents, paid_at, method)"
                  " VALUES (1, 12152, 350, '2025-01-01 02:42', 'card');"),
        probe_sql=("SELECT (SELECT amount_cents FROM payments WHERE payment_id = 1),"
                   " (SELECT method FROM payments WHERE payment_id = 1),"
                   " (SELECT COUNT(*) FROM payments), (SELECT MAX(payment_id) FROM payments)"),
        note="REPLACE INTO is INSERT OR REPLACE: a row that would break"
             " the primary key is DELETED and the new row inserted, so"
             " the count stays at 28,533 and payment 1 now says 350 by"
             " card. It is a blunt tool -- every column must be given"
             " again, and a DELETE trigger would fire -- where an UPDATE"
             " changes only what is named. OR IGNORE, the trap, keeps"
             " the old row and drops the new one in silence.",
        claims=[("payment 1 now 350 by card, nothing added",
                 lambda rows, c: rows == [(350, "card", 28533, 28533)])],
    ),
    dict(
        id=14, ledger="Q1220", concept="RNT", tier="5 - Changing the data",
        kind="script",
        title="A table renamed, without breaking the old name",
        prompt=(
            "The maintenance table is to be called jobs from now on,"
            " but old reports still query maintenance. Rename the table"
            " with ALTER TABLE, then create a VIEW called maintenance"
            " that selects everything from jobs, so both names work.\n\n"
            "Checked: what sqlite_master says the names jobs and"
            " maintenance are"
        ),
        solution=("ALTER TABLE maintenance RENAME TO jobs;\n"
                  "CREATE VIEW maintenance AS SELECT * FROM jobs;"),
        trap_sql="ALTER TABLE maintenance RENAME TO jobs;",
        probe_sql="SELECT name, type FROM sqlite_master WHERE name IN ('jobs', 'maintenance') ORDER BY name",
        note="ALTER TABLE ... RENAME TO changes the table's name and"
             " fixes up the indexes and triggers that belong to it; it"
             " does not fix the queries written against the old name,"
             " which is what the view is for -- a compatibility shim"
             " that can be dropped once the reports catch up. sqlite_master"
             " lists every object with its type, which is how the probe"
             " can tell a table from a view of the same name.",
        claims=[("jobs a table, maintenance a view",
                 lambda rows, c: rows == [("jobs", "table"), ("maintenance", "view")])],
    ),
    dict(
        id=15, ledger="Q1221", concept="GEN2", tier="5 - Changing the data",
        kind="script",
        title="A total that is computed and kept",
        prompt=(
            "Create invoice_lines with line_id as the integer primary"
            " key, job_id (required, referencing maintenance), qty and"
            " unit_cents (integers, required), and total_cents as a"
            " GENERATED column equal to qty times unit_cents that is"
            " STORED -- written to disk when the row is, not recomputed"
            " on every read. The question then inserts two lines.\n\n"
            "Checked: the totals added up, and the 'hidden' code"
            " pragma_table_xinfo gives the total_cents column (3 for"
            " stored, 2 for virtual)"
        ),
        solution=("CREATE TABLE invoice_lines (\n"
                  "  line_id     INTEGER PRIMARY KEY,\n"
                  "  job_id      INTEGER NOT NULL REFERENCES maintenance(job_id),\n"
                  "  qty         INTEGER NOT NULL,\n"
                  "  unit_cents  INTEGER NOT NULL,\n"
                  "  total_cents INTEGER GENERATED ALWAYS AS (qty * unit_cents) STORED\n"
                  ");"),
        trap_sql=("CREATE TABLE invoice_lines (\n"
                  "  line_id     INTEGER PRIMARY KEY,\n"
                  "  job_id      INTEGER NOT NULL REFERENCES maintenance(job_id),\n"
                  "  qty         INTEGER NOT NULL,\n"
                  "  unit_cents  INTEGER NOT NULL,\n"
                  "  total_cents INTEGER GENERATED ALWAYS AS (qty * unit_cents)\n"
                  ");"),
        driver_sql=("INSERT INTO invoice_lines (job_id, qty, unit_cents) VALUES (1, 2, 1500);\n"
                    "INSERT INTO invoice_lines (job_id, qty, unit_cents) VALUES (1, 1, 700);"),
        probe_sql=("SELECT (SELECT SUM(total_cents) FROM invoice_lines),"
                   " (SELECT hidden FROM pragma_table_xinfo('invoice_lines') WHERE name = 'total_cents')"),
        note="A generated column is VIRTUAL unless you say STORED:"
             " virtual is computed each time it is read and costs no"
             " space, stored is computed on write and can be indexed."
             " Both give the same totals, which is why the probe also"
             " reads pragma_table_xinfo, whose hidden column is 2 for a"
             " virtual generated column and 3 for a stored one; the"
             " trap leaves the keyword off and gets 2. STORED columns"
             " cannot be added by ALTER TABLE, only in CREATE TABLE.",
        claims=[("3700 cents, stored",
                 lambda rows, c: rows == [(3700, 3)])],
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
