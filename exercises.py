"""Practice exercises: fifteen questions on the bike-hire schema.

The seventh set on the bike scheme (SEED 1206), two tools per question,
the tiers named by task, on tools no bike set has used. Ties, pages and
matches -- the busiest bikes with their ties kept by DENSE_RANK, the next
page of rides by a row-value comparison, members who have ridden a cargo
bike by EXISTS where a join would count rides. Counting what's distinct
-- riders against rides by COUNT(DISTINCT), each month against the
average month by one CTE used twice, June fares at every station by
TOTAL where SUM gives NULL. Shaping the output -- a JSON object per
station by json_group_object, fleet labels by printf and UPPER, the
districts of each station's members by GROUP_CONCAT(DISTINCT ... ORDER
BY). The calendar, differently -- the last three days of a month by the
'start of month' modifier, the rush hour by comparing 'HH:MM' text, each
rider's active span by MAX minus MIN inside a CTE. And three WRITABLE
questions:

  * a DELETE with a WITH clause in front of it
  * an INSERT OR IGNORE that skips the names already there
  * an ALTER TABLE that renames one column and drops another

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
    # ============================================= 1 Ties, pages and matches
    dict(
        id=1, ledger="Q1162", concept="DRK", tier="1 - Ties, pages and matches",
        title="The busiest bikes, ties and all",
        prompt=(
            "The bikes with the three highest ride counts -- every bike"
            " that shares one of those counts, not just three bikes. A"
            " CTE of rides per bike, DENSE_RANK() OVER (ORDER BY rides"
            " DESC) in a second CTE, then the rows ranked 3 or better."
            " DENSE_RANK gives tied bikes the same rank and does not"
            " skip numbers after a tie.\n\n"
            "Return: bike_id, rides, rank"
        ),
        solution=("WITH per AS (SELECT bike_id, COUNT(*) AS rides FROM rides GROUP BY bike_id),"
                  " ranked AS (SELECT bike_id, rides, DENSE_RANK() OVER (ORDER BY rides DESC) AS rk FROM per)"
                  " SELECT bike_id, rides, rk FROM ranked WHERE rk <= 3"),
        trap_sql=("WITH per AS (SELECT bike_id, COUNT(*) AS rides FROM rides GROUP BY bike_id),"
                  " ranked AS (SELECT bike_id, rides, ROW_NUMBER() OVER (ORDER BY rides DESC) AS rk FROM per)"
                  " SELECT bike_id, rides, rk FROM ranked WHERE rk <= 3"),
        note="ROW_NUMBER numbers every row differently, so 'the top"
             " three' is three bikes and a tie is broken by whatever"
             " order the rows happened to arrive in. RANK gives ties the"
             " same number but then skips -- 1, 2, 2, 4 -- so 'rank <="
             " 3' would still miss the third distinct count. DENSE_RANK"
             " is 1, 2, 2, 3: the three highest COUNTS, five bikes.",
        claims=[("five bikes across three ranks",
                 lambda rows, c: len(rows) == 5 and {r[2] for r in rows} == {1, 2, 3}),
                ("bike 315 alone at the top with 159",
                 lambda rows, c: (315, 159, 1) in rows)],
    ),
    dict(
        id=2, ledger="Q1163", concept="ROWV", tier="1 - Ties, pages and matches",
        title="The next page of rides, keyset style",
        prompt=(
            "The ten rides that come after ride 1095 in start order,"
            " started_at then ride_id. Not OFFSET: compare ROW VALUES,"
            " WHERE (started_at, ride_id) > (SELECT started_at, ride_id"
            " FROM rides WHERE ride_id = 1095), ORDER BY the same two"
            " columns, LIMIT 10. Three other rides started in the same"
            " minute as 1095 and have higher ids, so they are the"
            " page's first three rows.\n\n"
            "Return: ride_id, started_at"
        ),
        solution=("SELECT ride_id, started_at FROM rides"
                  " WHERE (started_at, ride_id) > (SELECT started_at, ride_id FROM rides WHERE ride_id = 1095)"
                  " ORDER BY started_at, ride_id LIMIT 10"),
        trap_sql=("SELECT ride_id, started_at FROM rides"
                  " WHERE started_at > (SELECT started_at FROM rides WHERE ride_id = 1095)"
                  " ORDER BY started_at, ride_id LIMIT 10"),
        note="A row-value comparison works like a dictionary: (a, b) >"
             " (x, y) is true when a > x, or a = x and b > y. That is"
             " exactly 'after this row in the ORDER BY', ties included,"
             " and it is how a page is fetched from where the last one"
             " ended without counting rows to skip. Comparing started_at"
             " alone steps over the three rides that share 1095's"
             " minute, which the trap never shows on any page.",
        claims=[("ten rides, three in 1095's minute",
                 lambda rows, c: len(rows) == 10 and sum(r[1] == "2025-12-15 06:01" for r in rows) == 3),
                ("every id but 1095 itself",
                 lambda rows, c: all(r[0] != 1095 for r in rows))],
    ),
    dict(
        id=3, ledger="Q1164", concept="SEMI", tier="1 - Ties, pages and matches",
        title="Members who have tried a cargo bike",
        prompt=(
            "For each plan: how many of its members have ridden a cargo"
            " bike at least once. An EXISTS against rides joined to"
            " bikes, correlated on member_id -- a join from members"
            " would count every cargo RIDE, once per ride, not the"
            " members.\n\n"
            "Return: plan, members"
        ),
        solution=("SELECT m.plan, COUNT(*) FROM members m WHERE EXISTS"
                  " (SELECT 1 FROM rides r JOIN bikes b ON b.bike_id = r.bike_id"
                  " WHERE r.member_id = m.member_id AND b.model = 'cargo') GROUP BY m.plan"),
        trap_sql=("SELECT m.plan, COUNT(*) FROM members m"
                  " JOIN rides r ON r.member_id = m.member_id JOIN bikes b ON b.bike_id = r.bike_id"
                  " WHERE b.model = 'cargo' GROUP BY m.plan"),
        note="A join multiplies: a member with four cargo rides becomes"
             " four rows, and COUNT(*) counts rows. EXISTS asks a"
             " yes-or-no question per member and never produces more"
             " than one row for them, which is the semi-join: filter by"
             " another table without joining it. COUNT(DISTINCT"
             " m.member_id) over the join gives the same numbers at"
             " more cost. Four members in five have tried a cargo bike.",
        claims=[("three plans, 261 annual members",
                 lambda rows, c: len(rows) == 3 and ("annual", 261) in rows),
                ("734 members in all",
                 lambda rows, c: sum(r[1] for r in rows) == 734)],
    ),
    # ============================================= 2 Counting what's distinct
    dict(
        id=4, ledger="Q1165", concept="CDV", tier="2 - Counting what's distinct",
        title="Riders against rides at each station",
        prompt=(
            "For every station: the rides that started there, how many"
            " DIFFERENT members started a ride there, and the member"
            " rides per member to two decimals. COUNT(*) against"
            " COUNT(DISTINCT member_id); the casual rides, whose"
            " member_id is NULL, are in the first count and in neither"
            " of the others, so the ratio is COUNT(member_id) over the"
            " distinct count.\n\n"
            "Return: name, rides, riders, per_rider"
        ),
        solution=("SELECT s.name, COUNT(*), COUNT(DISTINCT r.member_id), ROUND(1.0 * COUNT(r.member_id) / COUNT(DISTINCT r.member_id), 2)"
                  " FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.name"),
        trap_sql=("SELECT s.name, COUNT(*), COUNT(DISTINCT r.member_id), ROUND(1.0 * COUNT(*) / COUNT(DISTINCT r.member_id), 2)"
                  " FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.name"),
        note="Three different counts of one column: COUNT(*) is rows,"
             " COUNT(member_id) is rows where it is not NULL, and"
             " COUNT(DISTINCT member_id) is how many different values"
             " there are. The trap divides every ride, casual ones"
             " included, by the members, and the per-rider figure comes"
             " out a third too high. About 700 members have started at"
             " each station, three or four times each.",
        claims=[("twelve stations, Market Square the most riders",
                 lambda rows, c: len(rows) == 12 and max(rows, key=lambda r: r[2])[0] == "Market Square"),
                ("every per-rider figure between 2.5 and 4",
                 lambda rows, c: all(2.5 <= r[3] <= 4 for r in rows))],
    ),
    dict(
        id=5, ledger="Q1166", concept="CTE2", tier="2 - Counting what's distinct",
        title="Each month against the average month",
        prompt=(
            "For every month in the data: its rides, and how far above"
            " or below the average month it is, as a percentage to one"
            " decimal. ONE CTE of rides per month, used twice: in FROM"
            " for the rows, and in a scalar subquery (SELECT AVG(n)"
            " FROM m) for the average -- 100.0 * n / avg - 100.\n\n"
            "Return: month, rides, vs_avg"
        ),
        solution=("WITH m AS (SELECT strftime('%Y-%m', started_at) AS mo, COUNT(*) AS n FROM rides GROUP BY mo)"
                  " SELECT mo, n, ROUND(100.0 * n / (SELECT AVG(n) FROM m) - 100, 1) FROM m"),
        trap_sql=("WITH m AS (SELECT strftime('%Y-%m', started_at) AS mo, COUNT(*) AS n FROM rides GROUP BY mo)"
                  " SELECT mo, n, ROUND(100.0 * n / (SELECT COUNT(*) FROM rides) - 100, 1) FROM m"),
        note="A CTE is a named result you can refer to as often as you"
             " like in the query that follows, and reading it once for"
             " the rows and once for a figure about the whole is the"
             " commonest reason to have one. The trap divides by the"
             " total rides rather than the average month and reports"
             " every month as 95 per cent below average. The months"
             " sit within ten per cent of each other; January 2025 and"
             " February 2026 are the quietest.",
        claims=[("eighteen months, January 2025 the furthest below",
                 lambda rows, c: len(rows) == 18 and min(rows, key=lambda r: r[2])[0] == "2025-01"),
                ("every month within ten per cent of the average",
                 lambda rows, c: all(abs(r[2]) < 10 for r in rows))],
    ),
    dict(
        id=6, ledger="Q1167", concept="TTL", tier="2 - Counting what's distinct",
        title="June's fares at every station, zero included",
        prompt=(
            "For every station, the closed one included: the fares of"
            " the rides that started there in June 2026, in dollars."
            " A LEFT JOIN from stations with the June condition in ON,"
            " and TOTAL(fare_cents) rather than SUM: SUM of no rows is"
            " NULL, TOTAL of no rows is 0.0.\n\n"
            "Return: name, june_fares"
        ),
        solution=("SELECT s.name, TOTAL(r.fare_cents) / 100.0 FROM stations s"
                  " LEFT JOIN rides r ON r.start_station_id = s.station_id AND r.started_at >= '2026-06-01'"
                  " GROUP BY s.name"),
        trap_sql=("SELECT s.name, SUM(r.fare_cents) / 100.0 FROM stations s"
                  " LEFT JOIN rides r ON r.start_station_id = s.station_id AND r.started_at >= '2026-06-01'"
                  " GROUP BY s.name"),
        note="TOTAL is SQLite's SUM that always returns a real number:"
             " 0.0 for an empty group, where SUM returns NULL. Old Mill"
             " closed in March and has no June rides, so the LEFT JOIN"
             " keeps its row with nothing attached, and the trap's SUM"
             " leaves its fares as NULL -- a blank in a report that"
             " should read zero. The June condition has to be in ON: in"
             " WHERE, Old Mill's row would be gone before TOTAL saw it.",
        claims=[("twelve stations, Old Mill at zero",
                 lambda rows, c: len(rows) == 12 and ("Old Mill", 0.0) in rows),
                ("Market Square took the most",
                 lambda rows, c: max(rows, key=lambda r: r[1])[0] == "Market Square")],
    ),
    # ================================================== 3 Shaping the output
    dict(
        id=7, ledger="Q1168", concept="JGO", tier="3 - Shaping the output",
        title="Each station's jobs, as one JSON object",
        prompt=(
            "For every station: a JSON object whose keys are the kinds"
            " of job reported there and whose values are the counts,"
            " keys in alphabetical order -- {\"battery\":2,\"brakes\":14,"
            "...}. A subquery of counts per station and kind, then"
            " json_group_object(kind, cnt ORDER BY kind) per station.\n\n"
            "Return: name, jobs"
        ),
        solution=("SELECT s.name, json_group_object(j.kind, j.cnt ORDER BY j.kind)"
                  " FROM (SELECT station_id, kind, COUNT(*) AS cnt FROM maintenance GROUP BY station_id, kind) j"
                  " JOIN stations s ON s.station_id = j.station_id GROUP BY s.name"),
        trap_sql=("SELECT s.name, json_group_array(json_object(j.kind, j.cnt) ORDER BY j.kind)"
                  " FROM (SELECT station_id, kind, COUNT(*) AS cnt FROM maintenance GROUP BY station_id, kind) j"
                  " JOIN stations s ON s.station_id = j.station_id GROUP BY s.name"),
        note="json_group_object takes a key and a value per row and"
             " builds one object for the group, the right shape for a"
             " lookup; json_group_array of one-key objects, the trap,"
             " builds a list of tiny objects that a program has to walk."
             " The ORDER BY inside the aggregate fixes the key order,"
             " which is what makes the text comparable. Three stations"
             " have never reported a battery job, so their objects have"
             " four keys.",
        claims=[("twelve objects, three without a battery key",
                 lambda rows, c: len(rows) == 12 and sum('"battery"' not in r[1] for r in rows) == 3),
                ("every object starts with a brace and a key",
                 lambda rows, c: all(r[1].startswith('{"') for r in rows))],
    ),
    dict(
        id=8, ledger="Q1169", concept="CONC", tier="3 - Shaping the output",
        title="Fleet labels for the cargo bikes",
        prompt=(
            "A label for every cargo bike: the model in capitals, a"
            " hyphen, and the bike_id padded with zeros to four digits"
            " -- CARGO-0010. printf('%s-%04d', UPPER(model), bike_id),"
            " or UPPER(model) || '-' || printf('%04d', bike_id).\n\n"
            "Return: bike_id, label"
        ),
        solution="SELECT bike_id, printf('%s-%04d', UPPER(model), bike_id) FROM bikes WHERE model = 'cargo'",
        trap_sql="SELECT bike_id, UPPER(model) || '-' || bike_id FROM bikes WHERE model = 'cargo'",
        note="printf is C's formatting in SQL: %s a string, %d an"
             " integer, and %04d an integer padded with zeros to four"
             " places. || concatenates, and converts a number to text"
             " as it goes, but it cannot pad -- the trap's labels are"
             " CARGO-10 and CARGO-123, which no longer sort or line up."
             " FORMAT is a synonym for printf.",
        claims=[("31 cargo bikes, every label ten characters",
                 lambda rows, c: len(rows) == 31 and all(len(r[1]) == 10 for r in rows)),
                ("bike 10 labelled CARGO-0010",
                 lambda rows, c: (10, "CARGO-0010") in rows)],
    ),
    dict(
        id=9, ledger="Q1170", concept="GCD", tier="3 - Shaping the output",
        title="What has gone wrong with each bike",
        prompt=(
            "For bikes 1 to 12 that have had a job: the kinds of job"
            " reported on the bike, each once, alphabetical, in one"
            " comma-separated cell. GROUP_CONCAT(DISTINCT kind ORDER BY"
            " kind) over maintenance, grouped by bike.\n\n"
            "Return: bike_id, kinds"
        ),
        solution=("SELECT bike_id, GROUP_CONCAT(DISTINCT kind ORDER BY kind)"
                  " FROM maintenance WHERE bike_id <= 12 GROUP BY bike_id"),
        trap_sql=("SELECT bike_id, GROUP_CONCAT(kind ORDER BY kind)"
                  " FROM maintenance WHERE bike_id <= 12 GROUP BY bike_id"),
        note="DISTINCT inside an aggregate removes the duplicates before"
             " they are combined, and the ORDER BY inside it fixes the"
             " order of what is left. Without DISTINCT the trap lists"
             " every job, 'puncture,puncture,puncture' for a bike that"
             " has had three. The same two keywords work in COUNT and"
             " in json_group_array; SUM(DISTINCT) exists too, and is"
             " almost never what anyone means.",
        claims=[("every cell alphabetical, nothing listed twice",
                 lambda rows, c: 6 <= len(rows) <= 12 and all(r[1].split(",") == sorted(set(r[1].split(","))) for r in rows)),
                ("the bikes do not all share one list",
                 lambda rows, c: len({r[1] for r in rows}) >= 3)],
    ),
    # ========================================== 4 The calendar, differently
    dict(
        id=10, ledger="Q1171", concept="SOM", tier="4 - The calendar, differently",
        title="Joined in the last three days of a month",
        prompt=(
            "For each plan: its members, and how many joined in the"
            " last three days of a month -- the 29th to the 31st of"
            " January, the 26th to the 28th of a February. The last"
            " day of a month is date(d, 'start of month', '+1 month',"
            " '-1 day'), so the window opens at '-3 days' from the"
            " start of the next month; a SUM of joined_on >= that.\n\n"
            "Return: plan, members, month_end"
        ),
        solution=("SELECT plan, COUNT(*), SUM(joined_on >= date(joined_on, 'start of month', '+1 month', '-3 days'))"
                  " FROM members GROUP BY plan"),
        trap_sql=("SELECT plan, COUNT(*), SUM(strftime('%d', joined_on) >= '28')"
                  " FROM members GROUP BY plan"),
        note="'start of month' is a date modifier that walks back to the"
             " first of the month, and the modifiers chain left to"
             " right, so '+1 month', '-3 days' from there is three days"
             " before the next month. Testing the day number against"
             " '28', the trap, is right only in February: it counts"
             " four days of a 31-day month and misses nothing in"
             " February, so monthly comes out at 55 instead of 45.",
        claims=[("three plans, 45 monthly members",
                 lambda rows, c: len(rows) == 3 and ("monthly", 371, 45) in rows),
                ("about a tenth of each plan",
                 lambda rows, c: all(0.08 <= r[2] / r[1] <= 0.14 for r in rows))],
    ),
    dict(
        id=11, ledger="Q1172", concept="RSH", tier="4 - The calendar, differently",
        title="The morning rush, zone by zone",
        prompt=(
            "For each zone, of the start station: its rides, those that"
            " started between 07:30 and 09:00 inclusive, and that as a"
            " percentage to one decimal. strftime('%H:%M', started_at)"
            " is the time of day as text, and 'HH:MM' text compares"
            " correctly, so BETWEEN '07:30' AND '09:00' is the test.\n\n"
            "Return: zone, rides, rush, rush_pct"
        ),
        solution=("SELECT s.zone, COUNT(*), SUM(strftime('%H:%M', r.started_at) BETWEEN '07:30' AND '09:00'),"
                  " ROUND(100.0 * SUM(strftime('%H:%M', r.started_at) BETWEEN '07:30' AND '09:00') / COUNT(*), 1)"
                  " FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.zone"),
        trap_sql=("SELECT s.zone, COUNT(*), SUM(strftime('%H', r.started_at) BETWEEN '07' AND '09'),"
                  " ROUND(100.0 * SUM(strftime('%H', r.started_at) BETWEEN '07' AND '09') / COUNT(*), 1)"
                  " FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.zone"),
        note="Zero-padded clock text sorts in time order, so a window"
             " of the day is a BETWEEN on five characters. The hour"
             " alone, the trap, is '07' to '09' -- 07:00 to 09:59, three"
             " full hours instead of ninety minutes -- and the share"
             " doubles. A sixth of rides start in the ninety-minute rush,"
             " the same in every zone.",
        claims=[("five zones, the centre's 1792 rush rides",
                 lambda rows, c: len(rows) == 5 and ("centre", 10361, 1792, 17.3) in rows),
                ("between 16 and 18 per cent everywhere",
                 lambda rows, c: all(16 <= r[3] <= 18 for r in rows))],
    ),
    dict(
        id=12, ledger="Q1173", concept="SPN", tier="4 - The calendar, differently",
        title="How long each rider has been riding",
        prompt=(
            "For each plan: the members who have ridden, and the"
            " average days between their first ride and their latest,"
            " to one decimal. A CTE per member of julianday(MAX("
            "started_at)) - julianday(MIN(started_at)) over their"
            " rides, then joined to members and averaged by plan. The"
            " span is measured from the first RIDE, not from joining.\n\n"
            "Return: plan, riders, avg_span"
        ),
        solution=("WITH x AS (SELECT member_id, julianday(MAX(started_at)) - julianday(MIN(started_at)) AS span"
                  " FROM rides WHERE member_id IS NOT NULL GROUP BY member_id)"
                  " SELECT m.plan, COUNT(*), ROUND(AVG(x.span), 1) FROM x JOIN members m ON m.member_id = x.member_id GROUP BY m.plan"),
        trap_sql=("WITH x AS (SELECT member_id, MAX(started_at) AS last FROM rides WHERE member_id IS NOT NULL GROUP BY member_id)"
                  " SELECT m.plan, COUNT(*), ROUND(AVG(julianday(x.last) - julianday(m.joined_on)), 1)"
                  " FROM x JOIN members m ON m.member_id = x.member_id GROUP BY m.plan"),
        note="MAX and MIN of the same column in one GROUP BY give the"
             " two ends of each member's riding, and the difference of"
             " their juliandays is the span; a second level of grouping"
             " averages those per plan. Measured from joined_on, the"
             " trap, the span includes the years before the data starts"
             " for the 530 members who joined before 2025, and comes"
             " out a hundred days longer. Riders on every plan have"
             " spanned about 500 of the data's 546 days.",
        claims=[("three plans, 289 annual riders",
                 lambda rows, c: len(rows) == 3 and any(r[0] == "annual" and r[1] == 289 for r in rows)),
                ("every span between 490 and 510 days",
                 lambda rows, c: all(490 <= r[2] <= 510 for r in rows))],
    ),
    # =================================================== 5 Changing the data
    dict(
        id=13, ledger="Q1174", concept="WDEL", tier="5 - Changing the data",
        kind="script",
        title="Refund the rides that never really happened",
        prompt=(
            "A ride under five minutes is a false start, and its fare"
            " is refunded by deleting its payment. A CTE in front of"
            " the DELETE: WITH short AS (SELECT ride_id FROM rides WHERE"
            " (julianday(ended_at) - julianday(started_at)) * 1440 < 5)"
            " DELETE FROM payments WHERE ride_id IN (SELECT ride_id FROM"
            " short). Minutes, not days: julianday differences are in"
            " days.\n\n"
            "Checked: how many payments remain, and how many name a ride"
        ),
        solution=("WITH short AS (SELECT ride_id FROM rides WHERE (julianday(ended_at) - julianday(started_at)) * 1440 < 5)"
                  " DELETE FROM payments WHERE ride_id IN (SELECT ride_id FROM short);"),
        trap_sql=("WITH short AS (SELECT ride_id FROM rides WHERE julianday(ended_at) - julianday(started_at) < 5)"
                  " DELETE FROM payments WHERE ride_id IN (SELECT ride_id FROM short);"),
        probe_sql="SELECT COUNT(*), COUNT(ride_id) FROM payments",
        note="WITH can precede DELETE, UPDATE and INSERT as well as"
             " SELECT, so a complicated 'which rows' can be named first"
             " and the statement kept short. julianday returns days, and"
             " every ride is under five DAYS, so the trap's CTE holds"
             " every finished ride and the DELETE removes all 22,732"
             " fare payments instead of 2,791. The subscription payments,"
             " whose ride_id is NULL, are never in the IN list.",
        claims=[("2,791 refunds, the subscriptions untouched",
                 lambda rows, c: rows == [(28533 - 2791, 22732 - 2791)])],
    ),
    dict(
        id=14, ledger="Q1175", concept="IGN", tier="5 - Changing the data",
        kind="script",
        title="New stations from a list, skipping the ones we have",
        prompt=(
            "A list of three stations to add, two of which already"
            " exist: Harbour (east, 20 docks), Canal Basin (west, 18)"
            " and Cathedral (centre, 24), all opening 2026-07-01. ONE"
            " INSERT OR IGNORE INTO stations (name, zone, docks,"
            " opened_on) VALUES (...), (...), (...): the name is UNIQUE,"
            " and OR IGNORE skips the rows that would break that"
            " instead of failing.\n\n"
            "Checked: how many stations there are, the highest"
            " station_id, and whether Canal Basin is among them"
        ),
        solution=("INSERT OR IGNORE INTO stations (name, zone, docks, opened_on) VALUES"
                  " ('Harbour', 'east', 20, '2026-07-01'), ('Canal Basin', 'west', 18, '2026-07-01'), ('Cathedral', 'centre', 24, '2026-07-01');"),
        trap_sql=("INSERT INTO stations (name, zone, docks, opened_on) VALUES"
                  " ('Harbour', 'east', 20, '2026-07-01'), ('Canal Basin', 'west', 18, '2026-07-01'), ('Cathedral', 'centre', 24, '2026-07-01');"),
        probe_sql="SELECT COUNT(*), MAX(station_id), SUM(name = 'Canal Basin') FROM stations",
        note="OR IGNORE is a conflict clause: a row that would violate a"
             " UNIQUE or PRIMARY KEY constraint is skipped and the rest"
             " of the statement carries on. A plain INSERT, the trap,"
             " stops at the first duplicate with an error and inserts"
             " nothing at all, not even Canal Basin. OR REPLACE would"
             " delete the old Harbour and insert the new one, which is"
             " a different and more dangerous thing.",
        claims=[("thirteen stations, Canal Basin number 13",
                 lambda rows, c: rows == [(13, 13, 1)])],
    ),
    dict(
        id=15, ledger="Q1176", concept="ALT2", tier="5 - Changing the data",
        kind="script",
        title="A column renamed and a column dropped",
        prompt=(
            "The members table is being tidied: district is to be"
            " called area, and born_on is no longer kept. Two"
            " statements: ALTER TABLE members RENAME COLUMN district TO"
            " area, then ALTER TABLE members DROP COLUMN born_on."
            " SQLite's ALTER TABLE does these two things and ADD COLUMN,"
            " and little else.\n\n"
            "Checked: the table's column names, in order"
        ),
        solution=("ALTER TABLE members RENAME COLUMN district TO area;\n"
                  "ALTER TABLE members DROP COLUMN born_on;"),
        trap_sql="ALTER TABLE members RENAME COLUMN district TO area;",
        probe_sql="SELECT GROUP_CONCAT(name, ',') FROM pragma_table_info('members')",
        note="pragma_table_info is a table-valued function that lists a"
             " table's columns, and the probe reads it, so the check is"
             " on the schema itself rather than on any row. DROP COLUMN"
             " (SQLite 3.35 and later) refuses a column that an index,"
             " a constraint or a view depends on; born_on has none, so"
             " it goes. The trap renames and forgets to drop. There is"
             " no ALTER COLUMN at all -- changing a column's type means"
             " making a new table.",
        claims=[("six columns, area last and born_on gone",
                 lambda rows, c: rows == [("member_id,name,joined_on,plan,home_station_id,area",)])],
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
