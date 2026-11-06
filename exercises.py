"""Practice exercises: fifteen questions on the bike-hire schema.

The ninth set on the bike scheme (SEED 1206), two tools per question, the
tiers named by task, on tools no bike set has used, with prompts that name
the tool but do not write the statement. Finding the rows -- the busiest
route's rides by a row-value equality with a subquery, rides at the
stations in a JSON list by json_each, June's rides by a half-open date
range where BETWEEN loses a day. Patterns and parts -- four-letter first
names by LIKE's underscore, subscription payments by day of the month,
members who joined in the first week of a year by 'start of year'.
Ordered by time -- the longest ride each month by unixepoch, the record
distance to date by a running MAX, the station two rides back by LAG with
an offset and a default. Branches, distinct and difference -- fare bands
by a CASE whose order matters, June's riders against all riders by COUNT
of a DISTINCT CASE, the routes Old Mill's closure took away by EXCEPT on
two columns. And three WRITABLE questions:

  * an AFTER DELETE trigger that logs what was removed
  * a STRICT table that refuses text in an integer column
  * a WITHOUT ROWID table keyed by two columns

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
    # ==================================================== 1 Finding the rows
    dict(
        id=1, ledger="Q1192", concept="ROWEQ", tier="1 - Finding the rows",
        title="The busiest route, month by month",
        prompt=(
            "For each month: how many rides took the single busiest"
            " route, the (start, end) pair with the most finished rides"
            " overall. Compare the two columns as one ROW VALUE against"
            " a subquery that returns that pair, rather than testing"
            " start and end separately.\n\n"
            "Return: month, rides"
        ),
        solution=("SELECT strftime('%Y-%m', started_at), COUNT(*) FROM rides"
                  " WHERE (start_station_id, end_station_id) = (SELECT start_station_id, end_station_id FROM rides"
                  " WHERE end_station_id IS NOT NULL GROUP BY start_station_id, end_station_id ORDER BY COUNT(*) DESC LIMIT 1)"
                  " GROUP BY strftime('%Y-%m', started_at)"),
        trap_sql=("SELECT strftime('%Y-%m', started_at), COUNT(*) FROM rides"
                  " WHERE start_station_id = (SELECT start_station_id FROM rides"
                  " WHERE end_station_id IS NOT NULL GROUP BY start_station_id, end_station_id ORDER BY COUNT(*) DESC LIMIT 1)"
                  " GROUP BY strftime('%Y-%m', started_at)"),
        note="(a, b) = (SELECT x, y ...) compares both columns at once"
             " with a subquery that returns one row of two columns, so"
             " the route is matched as a pair. The trap keeps only the"
             " start and counts every ride out of that station. The"
             " busiest route turns out to be Market Square back to"
             " Market Square, a round trip, and its rides doubled from"
             " March 2026 -- the month Old Mill closed.",
        claims=[("eighteen months, 58 rides in March 2026",
                 lambda rows, c: len(rows) == 18 and ("2026-03", 58) in rows),
                ("592 rides in all",
                 lambda rows, c: sum(r[1] for r in rows) == 592)],
    ),
    dict(
        id=2, ledger="Q1193", concept="JSE", tier="1 - Finding the rows",
        title="Rides at the stations on a list",
        prompt=(
            "A caller hands you station ids as a JSON array, '[2, 5,"
            " 7, 99]'. For each station on the list that exists: its"
            " name and how many rides started there. json_each() turns"
            " the array into rows you can join on.\n\n"
            "Return: name, rides"
        ),
        solution=("SELECT s.name, COUNT(r.ride_id) FROM json_each('[2, 5, 7, 99]') j"
                  " JOIN stations s ON s.station_id = j.value"
                  " LEFT JOIN rides r ON r.start_station_id = s.station_id GROUP BY s.name"),
        trap_sql=("SELECT s.name, COUNT(r.ride_id) FROM stations s"
                  " LEFT JOIN rides r ON r.start_station_id = s.station_id"
                  " WHERE s.station_id IN ('[2, 5, 7, 99]') GROUP BY s.name"),
        note="json_each is a table-valued function: given JSON text it"
             " returns one row per element, with the element in a column"
             " called value, and a FROM clause can read it like a table."
             " That is how a list arrives from outside -- an app's"
             " parameter, a config value -- without building SQL text."
             " IN ('[2, 5, 7, 99]'), the trap, compares ids with one"
             " string and matches nothing. Station 99 does not exist and"
             " the inner join simply drops it.",
        claims=[("three stations, Cathedral with 3313",
                 lambda rows, c: len(rows) == 3 and ("Cathedral", 3313) in rows),
                ("station 99 not among them",
                 lambda rows, c: {r[0] for r in rows} == {"Cathedral", "Botanic Gardens", "Harbour"})],
    ),
    dict(
        id=3, ledger="Q1194", concept="BTW", tier="1 - Finding the rows",
        title="June's rides, and the day BETWEEN loses",
        prompt=(
            "For each zone, of the start station: the rides that"
            " started in June 2026. Timestamps carry a time of day, so"
            " a range that ends at '2026-06-30' stops at midnight on"
            " the 30th; use a half-open range instead, up to but not"
            " including the first of July.\n\n"
            "Return: zone, rides"
        ),
        solution=("SELECT s.zone, COUNT(*) FROM rides r JOIN stations s ON s.station_id = r.start_station_id"
                  " WHERE r.started_at >= '2026-06-01' AND r.started_at < '2026-07-01' GROUP BY s.zone"),
        trap_sql=("SELECT s.zone, COUNT(*) FROM rides r JOIN stations s ON s.station_id = r.start_station_id"
                  " WHERE r.started_at BETWEEN '2026-06-01' AND '2026-06-30' GROUP BY s.zone"),
        note="BETWEEN is inclusive, but '2026-06-30' as text is"
             " '2026-06-30 00:00', so every ride later that day is"
             " above the upper bound: the trap loses the hundred rides"
             " of 30 June. >= the first day and < the day AFTER the"
             " last is the shape that is right for dates, timestamps"
             " and anything else with a finer grain than the bound --"
             " and it has no last-day arithmetic to get wrong.",
        claims=[("five zones, 684 in the centre",
                 lambda rows, c: len(rows) == 5 and ("centre", 684) in rows),
                ("2071 June rides in all",
                 lambda rows, c: sum(r[1] for r in rows) == 2071)],
    ),
    # ================================================== 2 Patterns and parts
    dict(
        id=4, ledger="Q1195", concept="LIK_", tier="2 - Patterns and parts",
        title="Four-letter first names",
        prompt=(
            "For each plan: its members, and how many have a first"
            " name of exactly four letters. LIKE's other wildcard, _,"
            " matches exactly one character; the first name ends at"
            " the first space.\n\n"
            "Return: plan, members, four_letter"
        ),
        solution="SELECT plan, COUNT(*), SUM(name LIKE '____ %') FROM members GROUP BY plan",
        trap_sql="SELECT plan, COUNT(*), SUM(name LIKE '%___ %') FROM members GROUP BY plan",
        note="% matches any run of characters, including none; _"
             " matches exactly one. Four underscores and a space pin the"
             " first word to four letters. Lead with a %, the trap, and"
             " any first name of three letters or more qualifies, which"
             " is everyone. Rosa, Zara and Umar are the scheme's"
             " four-letter names; between them, an eighth of the"
             " members.",
        claims=[("three plans, 42 annual members",
                 lambda rows, c: len(rows) == 3 and ("annual", 324, 42) in rows),
                ("122 in all",
                 lambda rows, c: sum(r[2] for r in rows) == 122)],
    ),
    dict(
        id=5, ledger="Q1196", concept="DOM", tier="2 - Patterns and parts",
        title="Which day of the month subscriptions are paid",
        prompt=(
            "For each day of the month, '01' to '31': how many"
            " SUBSCRIPTION payments fell on it. A subscription payment"
            " names a member; strftime has a format code for the day"
            " of the month.\n\n"
            "Return: day, payments"
        ),
        solution="SELECT strftime('%d', paid_at), COUNT(*) FROM payments WHERE member_id IS NOT NULL GROUP BY strftime('%d', paid_at)",
        trap_sql="SELECT strftime('%d', paid_at), COUNT(*) FROM payments GROUP BY strftime('%d', paid_at)",
        note="%d is the day of the month, zero-padded, as text. The"
             " trap counts every payment, fares included, and the"
             " pattern of 'when subscriptions renew' is drowned in"
             " 22,000 ride fares. The 31st is lightest because only"
             " seven months have one; otherwise renewals are spread"
             " across the month, with a dip in the second week.",
        claims=[("31 days, the 31st the lightest",
                 lambda rows, c: len(rows) == 31 and min(rows, key=lambda r: r[1])[0] == "31"),
                ("5801 subscription payments in all",
                 lambda rows, c: sum(r[1] for r in rows) == 5801)],
    ),
    dict(
        id=6, ledger="Q1197", concept="SOY", tier="2 - Patterns and parts",
        title="Joined in the first week of the year",
        prompt=(
            "For each year members joined in: how many joined, and how"
            " many of them within the first seven days of that year."
            " A date modifier walks any date back to the start of its"
            " year; a second one moves forward from there.\n\n"
            "Return: year, joined, first_week"
        ),
        solution=("SELECT strftime('%Y', joined_on), COUNT(*), SUM(joined_on < date(joined_on, 'start of year', '+7 days'))"
                  " FROM members GROUP BY strftime('%Y', joined_on)"),
        trap_sql=("SELECT strftime('%Y', joined_on), COUNT(*), SUM(joined_on < date(joined_on, 'start of month', '+7 days'))"
                  " FROM members GROUP BY strftime('%Y', joined_on)"),
        note="'start of year' sets the date to 1 January and the"
             " modifiers chain, so '+7 days' from there is the 8th, and"
             " < that is the first week. 'start of month', the trap,"
             " finds the first week of EVERY month and counts about a"
             " quarter of the members. Few people join in the first"
             " week of a year: thirteen in four years.",
        claims=[("four years, five first-week joiners in 2026",
                 lambda rows, c: len(rows) == 4 and ("2026", 118, 5) in rows),
                ("thirteen in all",
                 lambda rows, c: sum(r[2] for r in rows) == 13)],
    ),
    # ====================================================== 3 Ordered by time
    dict(
        id=7, ledger="Q1198", concept="UNX", tier="3 - Ordered by time",
        title="The longest ride of each month, in minutes",
        prompt=(
            "For each month: the length in whole minutes of its"
            " longest finished ride. unixepoch() turns a timestamp into"
            " seconds, and seconds subtract cleanly.\n\n"
            "Return: month, longest_minutes"
        ),
        solution=("SELECT strftime('%Y-%m', started_at), MAX((unixepoch(ended_at) - unixepoch(started_at)) / 60)"
                  " FROM rides WHERE ended_at IS NOT NULL GROUP BY strftime('%Y-%m', started_at)"),
        trap_sql=("SELECT strftime('%Y-%m', started_at), MAX(unixepoch(ended_at) - unixepoch(started_at))"
                  " FROM rides WHERE ended_at IS NOT NULL GROUP BY strftime('%Y-%m', started_at)"),
        note="unixepoch() (SQLite 3.38 and later) is seconds since 1970"
             " as an integer, the alternative to julianday's fractional"
             " days: no 1440 to remember, and integer division by 60"
             " gives whole minutes directly. The trap forgets the"
             " division and reports seconds, 14,400 for January's"
             " four-hour ride. The longest ride in every month is two"
             " to four hours.",
        claims=[("eighteen months, January 2025's longest 240 minutes",
                 lambda rows, c: len(rows) == 18 and ("2025-01", 240) in rows),
                ("every month's longest between 120 and 240",
                 lambda rows, c: all(120 <= r[1] <= 240 for r in rows))],
    ),
    dict(
        id=8, ledger="Q1199", concept="RMAX", tier="3 - Ordered by time",
        title="The record ride, month by month",
        prompt=(
            "For each month: the longest distance ridden that month,"
            " and the longest ridden in ANY month up to and including"
            " it -- the record to date. A monthly MAX in a CTE, then a"
            " window MAX ordered by month over it.\n\n"
            "Return: month, longest_m, record_m"
        ),
        solution=("WITH m AS (SELECT strftime('%Y-%m', started_at) AS mo, MAX(distance_m) AS longest FROM rides GROUP BY mo)"
                  " SELECT mo, longest, MAX(longest) OVER (ORDER BY mo) FROM m"),
        trap_sql=("WITH m AS (SELECT strftime('%Y-%m', started_at) AS mo, MAX(distance_m) AS longest FROM rides GROUP BY mo)"
                  " SELECT mo, longest, MAX(longest) OVER () FROM m"),
        note="A window MAX with an ORDER BY runs from the first row to"
             " the current one, the same default frame that makes SUM a"
             " running total, so it is the record SO FAR. Without the"
             " ORDER BY, the trap, the frame is the whole partition and"
             " every month shows the all-time record. The record was"
             " broken four times, the last in October 2025 at just"
             " under 66 kilometres.",
        claims=[("eighteen months, the record 65956 from October 2025",
                 lambda rows, c: len(rows) == 18 and ("2025-10", 65956, 65956) in rows and ("2025-09", 40001, 49458) in rows),
                ("the record never falls",
                 lambda rows, c: [r[2] for r in sorted(rows)] == sorted(r[2] for r in rows))],
    ),
    dict(
        id=9, ledger="Q1200", concept="LAG2", tier="3 - Ordered by time",
        title="Where bike 7 was two rides ago",
        prompt=(
            "For each ride bike 7 started in June 2026: where it"
            " started, and where it started TWO rides earlier, with 0"
            " when there is no such ride. LAG takes an offset and a"
            " default as its second and third arguments; compute over"
            " all of bike 7's rides and filter to June afterwards.\n\n"
            "Return: ride_id, started_at, start_station_id, two_back"
        ),
        solution=("WITH w AS (SELECT ride_id, started_at, start_station_id,"
                  " LAG(start_station_id, 2, 0) OVER (ORDER BY started_at) AS two_back FROM rides WHERE bike_id = 7)"
                  " SELECT ride_id, started_at, start_station_id, two_back FROM w WHERE started_at >= '2026-06-01'"),
        trap_sql=("WITH w AS (SELECT ride_id, started_at, start_station_id,"
                  " LAG(start_station_id, 1, 0) OVER (ORDER BY started_at) AS two_back FROM rides WHERE bike_id = 7)"
                  " SELECT ride_id, started_at, start_station_id, two_back FROM w WHERE started_at >= '2026-06-01'"),
        note="LAG(x) is LAG(x, 1, NULL): the offset says how many rows"
             " back, the default is what the first rows get instead of"
             " NULL. The trap looks one ride back, which is a different"
             " question. The June filter has to come after the window,"
             " or the first two June rides would have nothing behind"
             " them and show the default.",
        claims=[("nine June rides, the sixth's two-back station 1",
                 lambda rows, c: len(rows) == 9 and (744, "2026-06-06 11:05", 3, 1) in rows),
                ("no ride shows the default",
                 lambda rows, c: all(r[3] != 0 for r in rows))],
    ),
    # ================================= 4 Branches, distinct and difference
    dict(
        id=10, ledger="Q1201", concept="CASEORD", tier="4 - Branches, distinct and difference",
        title="Fares in four bands",
        prompt=(
            "Every ride in one of four bands: 'free', 'under $2',"
            " 'under $5' and '$5 and up' -- with how many rides and"
            " the fares added up in dollars. One CASE; its WHEN tests"
            " are checked in order and the first true one wins, so"
            " think about which band has to be tested first.\n\n"
            "Return: band, rides, fares"
        ),
        solution=("SELECT CASE WHEN fare_cents = 0 THEN 'free' WHEN fare_cents < 200 THEN 'under $2'"
                  " WHEN fare_cents < 500 THEN 'under $5' ELSE '$5 and up' END, COUNT(*), SUM(fare_cents) / 100.0"
                  " FROM rides GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN fare_cents < 500 THEN 'under $5' WHEN fare_cents < 200 THEN 'under $2'"
                  " WHEN fare_cents = 0 THEN 'free' ELSE '$5 and up' END, COUNT(*), SUM(fare_cents) / 100.0"
                  " FROM rides GROUP BY 1"),
        note="CASE stops at the first WHEN that is true, which lets each"
             " test assume the earlier ones failed: 'under $2' need not"
             " say 'and not free'. Put the widest test first, the trap,"
             " and it swallows the narrower bands: 'under $5' takes the"
             " free rides and the under-$2 rides with it, and two of the"
             " four bands never appear. Bands have to be tested from the"
             " narrowest out, or from the lowest up with the ELSE as the"
             " top.",
        claims=[("four bands, 15873 free rides",
                 lambda rows, c: len(rows) == 4 and ("free", 15873, 0.0) in rows),
                ("rides add up to every ride",
                 lambda rows, c: sum(r[1] for r in rows) == 38605)],
    ),
    dict(
        id=11, ledger="Q1202", concept="CDC", tier="4 - Branches, distinct and difference",
        title="June's riders against all riders, per station",
        prompt=(
            "For every station: how many different members have ever"
            " started a ride there, and how many different members did"
            " so in June 2026. Both from one pass over rides: the"
            " second count is a COUNT of DISTINCT over a CASE that"
            " yields the member only for June rows.\n\n"
            "Return: name, riders_ever, riders_june"
        ),
        solution=("SELECT s.name, COUNT(DISTINCT r.member_id),"
                  " COUNT(DISTINCT CASE WHEN r.started_at >= '2026-06-01' THEN r.member_id END)"
                  " FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.name"),
        trap_sql=("SELECT s.name, COUNT(DISTINCT r.member_id),"
                  " COUNT(CASE WHEN r.started_at >= '2026-06-01' THEN r.member_id END)"
                  " FROM rides r JOIN stations s ON s.station_id = r.start_station_id GROUP BY s.name"),
        note="A CASE with no ELSE yields NULL for the rows that fail"
             " its test, COUNT skips NULLs, and DISTINCT counts each"
             " member once: the three together count June's distinct"
             " riders without a second query or a FILTER. Drop the"
             " DISTINCT, the trap, and it counts June's member RIDES."
             " Old Mill has no June riders at all; Market Square has"
             " the most, 163.",
        claims=[("twelve stations, Old Mill with none in June",
                 lambda rows, c: len(rows) == 12 and ("Old Mill", 648, 0) in rows),
                ("Market Square's 163 the most in June",
                 lambda rows, c: max(rows, key=lambda r: r[2]) == ("Market Square", 730, 163))],
    ),
    dict(
        id=12, ledger="Q1203", concept="EXC2", tier="4 - Branches, distinct and difference",
        title="The routes that Old Mill's closure took away",
        prompt=(
            "Every route -- a start station and an end station, by"
            " name -- that was ridden in June 2025 but not in June"
            " 2026. EXCEPT works on rows of two columns as well as"
            " one; join to stations for the names afterwards.\n\n"
            "Return: from_station, to_station"
        ),
        solution=("SELECT a.name, b.name FROM"
                  " (SELECT start_station_id AS s, end_station_id AS e FROM rides WHERE started_at LIKE '2025-06%' AND end_station_id IS NOT NULL"
                  " EXCEPT SELECT start_station_id, end_station_id FROM rides WHERE started_at LIKE '2026-06%' AND end_station_id IS NOT NULL) x"
                  " JOIN stations a ON a.station_id = x.s JOIN stations b ON b.station_id = x.e"),
        trap_sql=("SELECT a.name, b.name FROM"
                  " (SELECT start_station_id AS s, end_station_id AS e FROM rides WHERE started_at LIKE '2026-06%' AND end_station_id IS NOT NULL"
                  " EXCEPT SELECT start_station_id, end_station_id FROM rides WHERE started_at LIKE '2025-06%' AND end_station_id IS NOT NULL) x"
                  " JOIN stations a ON a.station_id = x.s JOIN stations b ON b.station_id = x.e"),
        note="EXCEPT keeps the rows of the first SELECT that do not"
             " appear in the second, comparing whole rows, so a (start,"
             " end) pair is a single thing to subtract -- and it removes"
             " duplicates, so each lost route appears once. The order"
             " of the operands is the question: the trap asks for the"
             " routes new in 2026, and there are none. All 23 routes"
             " lost touch Old Mill, closed since March.",
        claims=[("23 routes, every one touching Old Mill",
                 lambda rows, c: len(rows) == 23 and all("Old Mill" in r for r in rows)),
                ("the round trip from Old Mill among them",
                 lambda rows, c: ("Old Mill", "Old Mill") in rows)],
    ),
    # =================================================== 5 Changing the data
    dict(
        id=13, ledger="Q1204", concept="AUD", tier="5 - Changing the data",
        kind="script",
        title="A log of every deleted job",
        prompt=(
            "Nothing should vanish from maintenance without a trace."
            " Create a table deleted_jobs with job_id (the primary key),"
            " bike_id, kind and cost_cents, all required, plus a"
            " deleted_on text column defaulting to '2026-07-01'; then an"
            " AFTER DELETE trigger on maintenance that copies the"
            " removed row's four values into it. The question then"
            " deletes jobs 9 and 19, and every open battery job.\n\n"
            "Checked: how many rows the log has, its lowest and highest"
            " job_id, and how many are battery jobs"
        ),
        solution=("CREATE TABLE deleted_jobs (\n"
                  "  job_id     INTEGER PRIMARY KEY,\n"
                  "  bike_id    INTEGER NOT NULL,\n"
                  "  kind       TEXT    NOT NULL,\n"
                  "  cost_cents INTEGER NOT NULL,\n"
                  "  deleted_on TEXT    NOT NULL DEFAULT '2026-07-01'\n"
                  ");\n"
                  "CREATE TRIGGER log_deleted_job AFTER DELETE ON maintenance\n"
                  "BEGIN\n"
                  "  INSERT INTO deleted_jobs (job_id, bike_id, kind, cost_cents)\n"
                  "  VALUES (OLD.job_id, OLD.bike_id, OLD.kind, OLD.cost_cents);\n"
                  "END;"),
        trap_sql=("CREATE TABLE deleted_jobs (\n"
                  "  job_id     INTEGER PRIMARY KEY,\n"
                  "  bike_id    INTEGER NOT NULL,\n"
                  "  kind       TEXT    NOT NULL,\n"
                  "  cost_cents INTEGER NOT NULL,\n"
                  "  deleted_on TEXT    NOT NULL DEFAULT '2026-07-01'\n"
                  ");"),
        driver_sql=("DELETE FROM maintenance WHERE job_id IN (9, 19);\n"
                    "DELETE FROM maintenance WHERE kind = 'battery' AND fixed_at IS NULL;"),
        probe_sql="SELECT COUNT(*), MIN(job_id), MAX(job_id), SUM(kind = 'battery') FROM deleted_jobs",
        note="In a DELETE trigger, OLD is the row being removed, and an"
             " AFTER trigger fires once per row after the removal -- so"
             " a DELETE that takes out several rows logs each of them."
             " The trap builds the log and never writes to it. This is"
             " the audit-table pattern: the application deletes as it"
             " always did, and the database keeps the history on its"
             " own. Only one battery job was open.",
        claims=[("three jobs logged, one of them a battery job",
                 lambda rows, c: rows == [(3, 9, 376, 1)])],
    ),
    dict(
        id=14, ledger="Q1205", concept="STRICT", tier="5 - Changing the data",
        kind="script",
        title="A table that insists on its types",
        prompt=(
            "Create dock_counts with count_id as the integer primary"
            " key, station_id (integer, required), counted_on (text,"
            " required) and bikes (integer, required) -- as a STRICT"
            " table, so that a value of the wrong type is refused"
            " rather than stored as given. The question then inserts"
            " three counts: 17, the word 'twelve', and the text '9'.\n\n"
            "Checked: each row's station_id, bikes and typeof(bikes)"
        ),
        solution=("CREATE TABLE dock_counts (\n"
                  "  count_id   INTEGER PRIMARY KEY,\n"
                  "  station_id INTEGER NOT NULL,\n"
                  "  counted_on TEXT    NOT NULL,\n"
                  "  bikes      INTEGER NOT NULL\n"
                  ") STRICT;"),
        trap_sql=("CREATE TABLE dock_counts (\n"
                  "  count_id   INTEGER PRIMARY KEY,\n"
                  "  station_id INTEGER NOT NULL,\n"
                  "  counted_on TEXT    NOT NULL,\n"
                  "  bikes      INTEGER NOT NULL\n"
                  ");"),
        driver_sql=("INSERT INTO dock_counts (station_id, counted_on, bikes) VALUES (1, '2026-07-01', 17);\n"
                    "INSERT INTO dock_counts (station_id, counted_on, bikes) VALUES (2, '2026-07-01', 'twelve');\n"
                    "INSERT INTO dock_counts (station_id, counted_on, bikes) VALUES (3, '2026-07-01', '9');"),
        probe_sql="SELECT station_id, bikes, typeof(bikes) FROM dock_counts ORDER BY station_id",
        note="An ordinary SQLite column has a type AFFINITY, not a type:"
             " 'twelve' goes into an INTEGER column as text and stays"
             " text, which the trap shows. STRICT (SQLite 3.37 and"
             " later) makes the declared types binding -- a value that"
             " cannot be converted is refused, and the status bar"
             " reports it. The text '9' is accepted either way because"
             " it converts to the integer 9 cleanly, and typeof then says"
             " integer.",
        claims=[("two rows in, 'twelve' refused, '9' stored as an integer",
                 lambda rows, c: rows == [(1, 17, "integer"), (3, 9, "integer")])],
    ),
    dict(
        id=15, ledger="Q1206", concept="WOR", tier="5 - Changing the data",
        kind="script",
        title="One row per bike per day, keyed by both",
        prompt=(
            "Create daily_use with bike_id (referencing bikes), day"
            " (text) and rides (integer), all required, whose PRIMARY"
            " KEY is the pair (bike_id, day) -- a composite key -- and"
            " declared WITHOUT ROWID, as a table keyed by its own"
            " columns can be. The question then inserts three rows,"
            " the third repeating a bike-and-day.\n\n"
            "Checked: the rows that got in"
        ),
        solution=("CREATE TABLE daily_use (\n"
                  "  bike_id INTEGER NOT NULL REFERENCES bikes(bike_id),\n"
                  "  day     TEXT    NOT NULL,\n"
                  "  rides   INTEGER NOT NULL,\n"
                  "  PRIMARY KEY (bike_id, day)\n"
                  ") WITHOUT ROWID;"),
        trap_sql=("CREATE TABLE daily_use (\n"
                  "  bike_id INTEGER NOT NULL REFERENCES bikes(bike_id),\n"
                  "  day     TEXT    NOT NULL,\n"
                  "  rides   INTEGER NOT NULL\n"
                  ");"),
        driver_sql=("INSERT INTO daily_use VALUES (7, '2026-07-01', 3);\n"
                    "INSERT INTO daily_use VALUES (7, '2026-07-02', 1);\n"
                    "INSERT INTO daily_use VALUES (7, '2026-07-01', 5);"),
        probe_sql="SELECT bike_id, day, rides FROM daily_use ORDER BY day",
        note="A PRIMARY KEY can be several columns, written as a table"
             " constraint after the columns, and it is then the"
             " combination that must be unique: the same bike on another"
             " day is fine, the same bike on the same day is refused."
             " WITHOUT ROWID stores the table in primary-key order"
             " rather than by a hidden rowid, which suits a table that"
             " is always looked up by its key. The trap has no key at"
             " all and takes the duplicate.",
        claims=[("two rows in, the repeated day refused",
                 lambda rows, c: rows == [(7, "2026-07-01", 3), (7, "2026-07-02", 1)])],
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
