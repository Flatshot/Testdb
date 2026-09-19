"""Practice exercises: thirty questions on the railway schema.

Twenty-two are SELECT questions across the usual tiers, graded on the rows
they return. The last eight are WRITABLE questions, graded on the state of the
database after your script runs. They cover what SQLite has in place of a
procedural language, and this set takes constructs neither earlier set did --

  * DELETE in foreign-key order, with RETURNING
  * UPDATE ... FROM a grouped subquery
  * a CTE in front of an INSERT, into a table with real constraints
  * two transactions: one committed, one rolled back
  * a trigger that maintains a summary table, gated by WHEN on OLD and NEW
  * a BEFORE UPDATE trigger that enforces a policy with RAISE()
  * an unpivot saved as a view
  * a recursive CTE feeding an INSERT

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script -- the updates your trigger should
count, or refuse.
"""

import sqlite3

EXERCISES = [
    # ========================================================== 1 Warm-up
    dict(
        id=1, ledger="Q612", concept="C7", tier="1 - Warm-up",
        title="The fleet by decade",
        prompt=(
            "How many units were built in each decade, with their average"
            " seats to the nearest seat. Label the decade by its first year:"
            " 1990, 2000, 2010.\n\n"
            "Return: decade, units, avg_seats"
        ),
        solution=("SELECT built_year / 10 * 10, COUNT(*), ROUND(AVG(seats))"
                  " FROM rolling_stock GROUP BY 1"),
        trap_sql=("SELECT built_year / 10, COUNT(*), ROUND(AVG(seats))"
                  " FROM rolling_stock GROUP BY 1"),
        note="Integer division is the tool here, on purpose: 1997 / 10 is"
             " 199, and multiplying back by 10 gives 1990. The trap stops"
             " halfway and labels the decades 199 and 200 -- the grouping is"
             " right and the labels are not, which is the usual way a"
             " banding slips. Grouping by the expression is fine in SQLite;"
             " GROUP BY 1 refers to the first output column.",
        claims=[("a handful of decades, each a multiple of ten",
                 lambda rows, c: 3 <= len(rows) <= 6
                 and all(r[0] % 10 == 0 for r in rows))],
    ),
    dict(
        id=2, ledger="Q613", concept="A2", tier="1 - Warm-up",
        title="Delay by line",
        prompt=(
            "One row per line: how many incidents, how many of them have a"
            " quantified delay, and the average delay of those to one"
            " decimal.\n\n"
            "Incidents whose delay was never quantified must not pull the"
            " average down.\n\n"
            "Return: line_id, incidents, quantified, avg_delay"
        ),
        solution=("SELECT s.line_id, COUNT(*), COUNT(i.delay_minutes),"
                  " ROUND(AVG(i.delay_minutes), 1) FROM incidents i"
                  " JOIN services s ON s.service_id = i.service_id"
                  " GROUP BY 1"),
        trap_sql=("SELECT s.line_id, COUNT(*), COUNT(i.delay_minutes),"
                  " ROUND(AVG(COALESCE(i.delay_minutes, 0)), 1) FROM incidents i"
                  " JOIN services s ON s.service_id = i.service_id"
                  " GROUP BY 1"),
        note="COUNT(*) counts rows; COUNT(column) counts rows where the"
             " column is not NULL -- that difference IS the quantified"
             " count. AVG skips NULLs the same way, so the untouched column"
             " gives the right average. The trap turns every unknown delay"
             " into a delay of zero, and every line's average drops"
             " by six to nine minutes.",
        claims=[("six lines, quantified fewer than incidents on each",
                 lambda rows, c: len(rows) == 6
                 and all(r[2] < r[1] for r in rows))],
    ),
    dict(
        id=3, ledger="Q614", concept="A3", tier="1 - Warm-up",
        title="Well-served towns",
        prompt=(
            "Towns with three or more stations, at least one of which is"
            " step-free, with the station count and the step-free count.\n\n"
            "Both conditions describe the town.\n\n"
            "Return: town, stations, step_free_stations"
        ),
        solution=("SELECT town, COUNT(*), SUM(step_free = 1) FROM stations"
                  " GROUP BY town HAVING COUNT(*) >= 3 AND SUM(step_free = 1) >= 1"),
        trap_sql=("SELECT town, COUNT(*), SUM(step_free = 1) FROM stations"
                  " WHERE step_free = 1 GROUP BY town HAVING COUNT(*) >= 3"),
        note="'At least one step-free' sounds like a WHERE, but putting it"
             " there filters the STATIONS, and then the count of three is a"
             " count of step-free stations only -- the trap keeps two towns"
             " where thirteen qualify. SUM of a comparison counts the rows"
             " where it holds, NULL surveys contributing nothing, and both"
             " tests then sit in HAVING where they see the whole town.",
        claims=[("every town returned meets both conditions",
                 lambda rows, c: len(rows) > 5
                 and all(r[1] >= 3 and r[2] >= 1 for r in rows))],
    ),
    # ========================================== 2 Sequences and strings
    dict(
        id=4, ledger="Q615", concept="W2", tier="2 - Sequences and strings",
        title="Where each service lost the most time",
        prompt=(
            "For every service that ran on 2025-04-07: the stop at which it"
            " was latest -- actual arrival minus scheduled, in minutes -- and"
            " by how much. One row per service; when two stops tie, the"
            " earlier one.\n\n"
            "Unrecorded arrivals do not count.\n\n"
            "Return: service_id, stop_seq, late_minutes"
        ),
        solution=("SELECT service_id, stop_seq, late FROM (SELECT sp.service_id,"
                  " sp.stop_seq, (strftime('%s', sp.actual_arrive)"
                  " - strftime('%s', sp.sched_arrive)) / 60 late, ROW_NUMBER()"
                  " OVER (PARTITION BY sp.service_id ORDER BY"
                  " strftime('%s', sp.actual_arrive) - strftime('%s',"
                  " sp.sched_arrive) DESC, sp.stop_seq) rn FROM stops sp"
                  " JOIN services s ON s.service_id = sp.service_id"
                  " WHERE s.run_date = '2025-04-07'"
                  " AND sp.actual_arrive IS NOT NULL) WHERE rn = 1"),
        trap_sql=("SELECT service_id, stop_seq, late FROM (SELECT sp.service_id,"
                  " sp.stop_seq, (strftime('%s', sp.actual_arrive)"
                  " - strftime('%s', sp.sched_arrive)) / 60 late, RANK()"
                  " OVER (PARTITION BY sp.service_id ORDER BY"
                  " strftime('%s', sp.actual_arrive) - strftime('%s',"
                  " sp.sched_arrive) DESC) rn FROM stops sp"
                  " JOIN services s ON s.service_id = sp.service_id"
                  " WHERE s.run_date = '2025-04-07'"
                  " AND sp.actual_arrive IS NOT NULL) WHERE rn = 1"),
        note="Top-1 per group with ties resolved: ROW_NUMBER with a second"
             " sort key. RANK hands the same number to tied stops and the"
             " trap returns thirty-five rows for twenty-two services -- ties"
             " at eight minutes are common when lateness is a small"
             " integer. 'The earlier one' in the prompt is the tiebreak,"
             " and it belongs inside the OVER.",
        claims=[("one row per running service that day",
                 lambda rows, c: len(rows) == len({r[0] for r in rows})
                 and len(rows) == c.execute(
                     "SELECT COUNT(*) FROM services WHERE run_date"
                     " = '2025-04-07' AND cancelled = 0").fetchone()[0])],
    ),
    dict(
        id=5, ledger="Q616", concept="STR", tier="2 - Sequences and strings",
        title="Counting the words in a name",
        prompt=(
            "Every station with the length of its name in characters and in"
            " words. There is no split function: count the spaces.\n\n"
            "Return: station_id, chars, words"
        ),
        solution=("SELECT station_id, LENGTH(name),"
                  " LENGTH(name) - LENGTH(REPLACE(name, ' ', '')) + 1"
                  " FROM stations"),
        trap_sql=("SELECT station_id, LENGTH(name),"
                  " LENGTH(name) - LENGTH(REPLACE(name, ' ', ''))"
                  " FROM stations"),
        note="The idiom: the length of the string minus its length with the"
             " separator removed is the number of separators, and words are"
             " one more than that. The trap counts the spaces and calls it"
             " words, so every single-word station has none. It works"
             " because station names have single spaces and no leading or"
             " trailing ones; TRIM first when that is not guaranteed.",
        claims=[("sixty stations, one or two words each",
                 lambda rows, c: len(rows) == 60
                 and {r[2] for r in rows} == {1, 2})],
    ),
    dict(
        id=6, ledger="Q617", concept="W2", tier="2 - Sequences and strings",
        title="Until the next departure",
        prompt=(
            "Line 2's services on 2025-04-07 in departure order, each with"
            " the NEXT one's departure time and the minutes until it. The"
            " last service of the day has neither.\n\n"
            "Return: service_id, depart_time, next_depart, minutes_until"
        ),
        solution=("SELECT service_id, depart_time, LEAD(depart_time) OVER w,"
                  " (strftime('%s', LEAD(depart_time) OVER w)"
                  " - strftime('%s', depart_time)) / 60 FROM services"
                  " WHERE line_id = 2 AND run_date = '2025-04-07'"
                  " WINDOW w AS (ORDER BY depart_time)"),
        trap_sql=("SELECT service_id, depart_time, LAG(depart_time) OVER w,"
                  " (strftime('%s', depart_time) - strftime('%s',"
                  " LAG(depart_time) OVER w)) / 60 FROM services"
                  " WHERE line_id = 2 AND run_date = '2025-04-07'"
                  " WINDOW w AS (ORDER BY depart_time)"),
        note="LEAD looks forward, LAG back. The trap is consistent with"
             " itself -- previous departure, minutes since -- and answers"
             " the mirror question, with the NULL on the first row instead"
             " of the last. A named WINDOW saves writing the same OVER"
             " twice; SQLite supports it. strftime('%s') on a bare 'HH:MM'"
             " gives seconds from midnight, which is all a same-day gap"
             " needs.",
        claims=[("the last row has no next, the others a positive gap",
                 lambda rows, c: len(rows) >= 3 and rows[-1][2] is None
                 and all(r[3] > 0 for r in rows[:-1]))],
    ),
    dict(
        id=7, ledger="Q618", concept="S1", tier="2 - Sequences and strings",
        title="Everyone with authority",
        prompt=(
            "Staff who are managers by role OR who have someone reporting"
            " to them -- each person once, whichever way they qualify."
            " Ordered by staff_id.\n\n"
            "Some managers also have reports; they must not appear"
            " twice.\n\n"
            "Return: staff_id, name"
        ),
        solution=("SELECT staff_id, name FROM staff WHERE role = 'manager'"
                  " UNION SELECT s.staff_id, s.name FROM staff s WHERE EXISTS"
                  " (SELECT 1 FROM staff r WHERE r.reports_to = s.staff_id)"
                  " ORDER BY 1"),
        trap_sql=("SELECT staff_id, name FROM staff WHERE role = 'manager'"
                  " UNION ALL SELECT s.staff_id, s.name FROM staff s WHERE EXISTS"
                  " (SELECT 1 FROM staff r WHERE r.reports_to = s.staff_id)"
                  " ORDER BY 1"),
        note="UNION removes duplicates; UNION ALL keeps them. Every manager"
             " here also manages someone, so the trap lists all five of them"
             " twice. UNION ALL is the right default when the two sides"
             " cannot overlap, because deduplicating costs a sort -- but"
             " when they can, 'each person once' is a UNION. The same"
             " result is a single SELECT with OR in the WHERE; the set"
             " form is what generalises to two different tables.",
        claims=[("no staff_id twice, and every manager included",
                 lambda rows, c: len(rows) == len({r[0] for r in rows})
                 and {r[0] for r in rows} >= {r[0] for r in c.execute(
                     "SELECT staff_id FROM staff WHERE role = 'manager'")})],
    ),
    # ============================================ 3 Unpivot and set ops
    dict(
        id=8, ledger="Q619", concept="UNP", tier="3 - Unpivot and set ops",
        title="Each quarter's share of its year",
        prompt=(
            "Network-wide footfall for each quarter of each year as ROWS,"
            " with the percentage of that YEAR's total it is, to two"
            " decimals. Twelve rows, labelled q1 to q4.\n\n"
            "Return: year, quarter, footfall, pct_of_year"
        ),
        solution=("SELECT year, quarter, footfall, ROUND(100.0 * footfall"
                  " / SUM(footfall) OVER (PARTITION BY year), 2) FROM"
                  " (SELECT year, 'q1' quarter, SUM(q1) footfall"
                  " FROM station_footfall GROUP BY year UNION ALL"
                  " SELECT year, 'q2', SUM(q2) FROM station_footfall GROUP BY year"
                  " UNION ALL SELECT year, 'q3', SUM(q3) FROM station_footfall"
                  " GROUP BY year UNION ALL SELECT year, 'q4', SUM(q4)"
                  " FROM station_footfall GROUP BY year)"),
        trap_sql=("SELECT year, quarter, footfall, ROUND(100.0 * footfall"
                  " / SUM(footfall) OVER (), 2) FROM"
                  " (SELECT year, 'q1' quarter, SUM(q1) footfall"
                  " FROM station_footfall GROUP BY year UNION ALL"
                  " SELECT year, 'q2', SUM(q2) FROM station_footfall GROUP BY year"
                  " UNION ALL SELECT year, 'q3', SUM(q3) FROM station_footfall"
                  " GROUP BY year UNION ALL SELECT year, 'q4', SUM(q4)"
                  " FROM station_footfall GROUP BY year)"),
        note="Unpivot first, then window. Once the four columns are rows,"
             " 'share of the year' is an ordinary partitioned SUM over"
             " them; on the wide table it would take four expressions"
             " each dividing by the sum of all four. The trap divides by"
             " the grand total across three years, so its twelve shares"
             " add to 100 once rather than three times.",
        claims=[("twelve rows, each year's shares summing to 100",
                 lambda rows, c: len(rows) == 12 and all(
                     abs(sum(r[3] for r in rows if r[0] == y) - 100) < 0.05
                     for y in {r[0] for r in rows}))],
    ),
    dict(
        id=9, ledger="Q620", concept="J1", tier="3 - Unpivot and set ops",
        title="Pairs of stations in the same town",
        prompt=(
            "For every town with at least two stations, how many PAIRS of"
            " stations it has -- a town with three stations has three pairs,"
            " one with four has six.\n\n"
            "Return: town, pairs"
        ),
        solution=("SELECT a.town, COUNT(*) FROM stations a JOIN stations b"
                  " ON b.town = a.town AND b.station_id > a.station_id"
                  " GROUP BY a.town"),
        trap_sql=("SELECT a.town, COUNT(*) FROM stations a JOIN stations b"
                  " ON b.town = a.town AND b.station_id <> a.station_id"
                  " GROUP BY a.town"),
        note="A self-join on a plain column, then a count. b > a keeps each"
             " unordered pair once; <> keeps both orders and the trap"
             " doubles every count. The towns with one station drop out"
             " on their own, because an inner join with no partner"
             " produces no row -- the same fact that makes an outer join"
             " necessary when you DO want them.",
        claims=[("only towns with two or more stations, pairs matching n(n-1)/2",
                 lambda rows, c: len(rows) > 10 and all(
                     r[1] == n * (n - 1) // 2 for r, n in (
                         (r, c.execute("SELECT COUNT(*) FROM stations"
                                       " WHERE town = ?", (r[0],)).fetchone()[0])
                         for r in rows)))],
    ),
    dict(
        id=10, ledger="Q621", concept="S1", tier="3 - Unpivot and set ops",
        title="On two lines, never on a third",
        prompt=(
            "Units that have worked on BOTH line 2 and line 3 but have"
            " never worked on line 1.\n\n"
            "Return: unit_id"
        ),
        solution=("SELECT su.unit_id FROM service_units su JOIN services s"
                  " ON s.service_id = su.service_id WHERE s.line_id = 2"
                  " INTERSECT SELECT su.unit_id FROM service_units su"
                  " JOIN services s ON s.service_id = su.service_id"
                  " WHERE s.line_id = 3 EXCEPT SELECT su.unit_id"
                  " FROM service_units su JOIN services s"
                  " ON s.service_id = su.service_id WHERE s.line_id = 1"),
        trap_sql=("SELECT DISTINCT su.unit_id FROM service_units su"
                  " JOIN services s ON s.service_id = su.service_id"
                  " WHERE s.line_id IN (2, 3) AND s.line_id <> 1"),
        note="Three sets and two operators: (line 2 INTERSECT line 3)"
             " EXCEPT line 1, evaluated left to right, which is what the"
             " question says in order. The trap reasons row by row -- a"
             " workingIS on line 2 or 3, and a working on line 2 is trivially"
             " not on line 1 -- so it returns every unit that has touched"
             " either line, three times too many. 'Both' and 'never' are"
             " statements about a unit's whole history, and only sets see"
             " that.",
        claims=[("several units, each on lines 2 and 3 and never on 1",
                 lambda rows, c: len(rows) > 3 and all(
                     c.execute("SELECT COUNT(DISTINCT s.line_id) FILTER"
                               " (WHERE s.line_id IN (2, 3)) = 2 AND"
                               " COUNT(*) FILTER (WHERE s.line_id = 1) = 0"
                               " FROM service_units su JOIN services s"
                               " ON s.service_id = su.service_id"
                               " WHERE su.unit_id = ?", (r[0],)).fetchone()[0]
                     for r in rows))],
    ),
    # ================================================= 4 Dates and times
    dict(
        id=11, ledger="Q622", concept="D1", tier="4 - Dates and times",
        title="Cancellation rate by month",
        prompt=(
            "For each month of the timetable: services scheduled, services"
            " cancelled, and the cancellation rate as a percentage to one"
            " decimal. Eighteen rows -- January 2025 and January 2026 are"
            " different months.\n\n"
            "Return: month, services, cancelled, pct"
        ),
        solution=("SELECT strftime('%Y-%m', run_date), COUNT(*), SUM(cancelled),"
                  " ROUND(100.0 * SUM(cancelled) / COUNT(*), 1) FROM services"
                  " GROUP BY 1"),
        trap_sql=("SELECT strftime('%m', run_date), COUNT(*), SUM(cancelled),"
                  " ROUND(100.0 * SUM(cancelled) / COUNT(*), 1) FROM services"
                  " GROUP BY 1"),
        note="'%m' is the month number and nothing else, so the trap folds"
             " the two Januaries into one row and returns twelve months for"
             " eighteen. Group by '%Y-%m' whenever the range crosses a year"
             " -- and it nearly always will, eventually. SUM of a 0/1"
             " column is a count of the ones; 100.0 keeps the division"
             " real.",
        claims=[("eighteen months, rates a few percent",
                 lambda rows, c: len(rows) == 18
                 and all(0 < r[3] < 10 for r in rows))],
    ),
    dict(
        id=12, ledger="Q623", concept="D1", tier="4 - Dates and times",
        title="Departures by time of day",
        prompt=(
            "How many services depart in the morning (before 10:00), at"
            " midday (10:00 up to but not including 14:00) and later.\n\n"
            "Three rows, labelled 'morning', 'midday', 'later'.\n\n"
            "Return: band, services"
        ),
        solution=("SELECT CASE WHEN depart_time < '10:00' THEN 'morning'"
                  " WHEN depart_time < '14:00' THEN 'midday' ELSE 'later' END,"
                  " COUNT(*) FROM services GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN strftime('%H', depart_time) < 10"
                  " THEN 'morning' WHEN strftime('%H', depart_time) < 14"
                  " THEN 'midday' ELSE 'later' END, COUNT(*) FROM services"
                  " GROUP BY 1"),
        note="'HH:MM' is fixed-width and zero-padded, so comparing it as"
             " text IS comparing it as time. The trap compares the TEXT"
             " '06' with the INTEGER 10, and in SQLite every number sorts"
             " before every string -- '06' < 10 is false, as is '13' < 14,"
             " so all eleven thousand services land in 'later'. Compare"
             " text with text, or CAST the hour.",
        claims=[("three bands, morning the largest",
                 lambda rows, c: len(rows) == 3
                 and max(rows, key=lambda r: r[1])[0] == 'morning')],
    ),
    dict(
        id=13, ledger="Q624", concept="D1", tier="4 - Dates and times",
        title="Days since the previous opening",
        prompt=(
            "Every station in the order it opened, with the number of days"
            " since the previous station opened. The first has none. Two"
            " stations opened on the same day; order those by station_id,"
            " and the second shows 0.\n\n"
            "Return: station_id, opened_on, days_since_previous"
        ),
        solution=("SELECT station_id, opened_on, julianday(opened_on)"
                  " - julianday(LAG(opened_on) OVER (ORDER BY opened_on,"
                  " station_id)) FROM stations ORDER BY opened_on, station_id"),
        trap_sql=("SELECT station_id, opened_on, opened_on"
                  " - LAG(opened_on) OVER (ORDER BY opened_on, station_id)"
                  " FROM stations ORDER BY opened_on, station_id"),
        note="Two dates cannot be subtracted as text. SQLite reads the"
             " leading digits of each -- the year -- and the trap returns"
             " the difference in YEARS, mostly 0 and 1, with no error."
             " julianday turns a date into a day count, and the difference"
             " of two is days. The LAG's ORDER BY carries the tiebreak so"
             " that 'previous' is well defined on the day two stations"
             " share.",
        claims=[("sixty rows, the first blank, the rest non-negative and one zero",
                 lambda rows, c: len(rows) == 60 and rows[0][2] is None
                 and all(r[2] >= 0 for r in rows[1:])
                 and sum(1 for r in rows[1:] if r[2] == 0) == 1)],
    ),
    dict(
        id=14, ledger="Q625", concept="D2", tier="4 - Dates and times",
        title="The first full week of each month",
        prompt=(
            "How many services ran in the first full week of each month:"
            " the first Monday through the Sunday after it. Eighteen"
            " months.\n\n"
            "Modifiers: 'start of month', then 'weekday 1' for the Monday,"
            " which stays put if the 1st already is one.\n\n"
            "Return: month, services"
        ),
        solution=("SELECT strftime('%Y-%m', run_date), COUNT(*) FROM services"
                  " WHERE run_date BETWEEN date(run_date, 'start of month',"
                  " 'weekday 1') AND date(run_date, 'start of month',"
                  " 'weekday 1', '+6 days') GROUP BY 1"),
        trap_sql=("SELECT strftime('%Y-%m', run_date), COUNT(*) FROM services"
                  " WHERE run_date BETWEEN date(run_date, 'start of month',"
                  " 'weekday 1') AND date(run_date, 'start of month',"
                  " 'weekday 1', '+7 days') GROUP BY 1"),
        note="Monday plus six days is Sunday; BETWEEN is inclusive at both"
             " ends, so '+7 days' takes the following Monday too and every"
             " month is one weekday heavy. Off-by-one on an inclusive"
             " range is the commonest date bug there is. Both bounds are"
             " computed from the row's own date, so no month needs to be"
             " named.",
        claims=[("eighteen months, each a week's worth of services",
                 lambda rows, c: len(rows) == 18
                 and all(50 < r[1] < 250 for r in rows))],
    ),
    # ================================================= 5 Joins and grain
    dict(
        id=15, ledger="Q626", concept="J2", tier="5 - Joins and grain",
        title="Every unit's June 2025",
        prompt=(
            "Every unit of rolling stock with the number of services it"
            " worked in June 2025. Units that worked none -- and the five"
            " that have never worked at all -- must appear with 0, so all"
            " 50 rows come back.\n\n"
            "Return: unit_id, workings"
        ),
        solution=("SELECT r.unit_id, COUNT(s.service_id) FROM rolling_stock r"
                  " LEFT JOIN service_units su ON su.unit_id = r.unit_id"
                  " LEFT JOIN services s ON s.service_id = su.service_id"
                  " AND s.run_date BETWEEN '2025-06-01' AND '2025-06-30'"
                  " GROUP BY r.unit_id"),
        trap_sql=("SELECT r.unit_id, COUNT(s.service_id) FROM rolling_stock r"
                  " LEFT JOIN service_units su ON su.unit_id = r.unit_id"
                  " LEFT JOIN services s ON s.service_id = su.service_id"
                  " WHERE s.run_date BETWEEN '2025-06-01' AND '2025-06-30'"
                  " GROUP BY r.unit_id"),
        note="Two outer joins in a chain, and the date filter has to sit in"
             " the ON of the second one. In WHERE it runs after both joins,"
             " and a unit with no June working has s.run_date NULL there,"
             " which fails the BETWEEN and drops the row -- the trap"
             " returns 45 units. COUNT(s.service_id) counts only real"
             " matches, so the kept rows read 0.",
        claims=[("fifty units, some with none",
                 lambda rows, c: len(rows) == 50
                 and any(r[1] == 0 for r in rows)
                 and any(r[1] > 0 for r in rows))],
    ),
    dict(
        id=16, ledger="Q627", concept="C2", tier="5 - Joins and grain",
        title="Seats offered and tickets sold, per line",
        prompt=(
            "For each line: the total seats it has run -- every unit on"
            " every service -- and the total tickets sold on it.\n\n"
            "Units and tickets both hang off `services`, at different"
            " grains. Joined together they multiply.\n\n"
            "Return: line_id, seats, tickets"
        ),
        solution=("WITH seats AS (SELECT s.line_id, SUM(r.seats) k"
                  " FROM services s JOIN service_units su"
                  " ON su.service_id = s.service_id JOIN rolling_stock r"
                  " ON r.unit_id = su.unit_id GROUP BY 1), tk AS"
                  " (SELECT s.line_id, COUNT(*) n FROM services s"
                  " JOIN tickets t ON t.service_id = s.service_id GROUP BY 1)"
                  " SELECT seats.line_id, seats.k, tk.n FROM seats"
                  " JOIN tk ON tk.line_id = seats.line_id"),
        trap_sql=("SELECT s.line_id, SUM(r.seats), COUNT(t.ticket_id)"
                  " FROM services s JOIN service_units su"
                  " ON su.service_id = s.service_id JOIN rolling_stock r"
                  " ON r.unit_id = su.unit_id JOIN tickets t"
                  " ON t.service_id = s.service_id GROUP BY 1"),
        note="A service with two units and five tickets is ten rows in the"
             " trap: the seats counted five times and the tickets twice."
             " Neither aggregate survives -- COUNT(DISTINCT ticket_id) would"
             " repair the count but nothing repairs the SUM. Aggregate each"
             " child to the line separately and join the two small"
             " results; the CTEs are the same shape as question 16 of the"
             " last set.",
        claims=[("six lines, tickets matching the ticket table",
                 lambda rows, c: len(rows) == 6
                 and sum(r[2] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM tickets").fetchone()[0])],
    ),
    dict(
        id=17, ledger="Q628", concept="J2", tier="5 - Joins and grain",
        title="Services that sold nothing",
        prompt=(
            "Services scheduled on 2025-05-08 that sold no tickets at all."
            " Write it with an outer join.\n\n"
            "Return: service_id, line_id"
        ),
        solution=("SELECT s.service_id, s.line_id FROM services s"
                  " LEFT JOIN tickets t ON t.service_id = s.service_id"
                  " WHERE s.run_date = '2025-05-08' AND t.ticket_id IS NULL"),
        trap_sql=("SELECT s.service_id, s.line_id FROM services s"
                  " JOIN tickets t ON t.service_id = s.service_id"
                  " WHERE s.run_date = '2025-05-08' GROUP BY s.service_id"
                  " HAVING COUNT(t.ticket_id) = 0"),
        note="An inner join cannot find an absence: a service with no"
             " tickets produces no joined row, so there is nothing to count"
             " and the trap's HAVING COUNT = 0 is never true -- zero rows,"
             " no error. The anti-join keeps every service and tests the"
             " right side for NULL; the same HAVING would work on a LEFT"
             " JOIN, because then the service is present with a NULL"
             " ticket.",
        claims=[("a handful of services, none with a ticket",
                 lambda rows, c: 2 < len(rows) < 10 and not c.execute(
                     "SELECT 1 FROM tickets WHERE service_id IN (%s) LIMIT 1"
                     % ",".join(str(int(r[0])) for r in rows)).fetchall())],
    ),
    dict(
        id=18, ledger="Q629", concept="E1", tier="5 - Joins and grain",
        title="Sold only one class",
        prompt=(
            "Services in January 2025 that sold at least four tickets, all"
            " of the same class -- with the ticket count and that class.\n\n"
            "Return: service_id, tickets, class"
        ),
        solution=("SELECT s.service_id, COUNT(*), MIN(t.class) FROM services s"
                  " JOIN tickets t ON t.service_id = s.service_id"
                  " WHERE s.run_date BETWEEN '2025-01-01' AND '2025-01-31'"
                  " GROUP BY s.service_id HAVING COUNT(*) >= 4"
                  " AND COUNT(DISTINCT t.class) = 1"),
        trap_sql=("SELECT s.service_id, COUNT(*), t.class FROM services s"
                  " JOIN tickets t ON t.service_id = s.service_id"
                  " WHERE s.run_date BETWEEN '2025-01-01' AND '2025-01-31'"
                  " GROUP BY s.service_id, t.class HAVING COUNT(*) >= 4"),
        note="'All the same class' is COUNT(DISTINCT class) = 1 -- a"
             " statement about the group. The trap groups by service AND"
             " class, so it finds services that sold four of SOME class,"
             " whatever else they sold, and returns fifty rows for six."
             " MIN(class) is the idiom for 'the value, which is the same"
             " on every row': a bare column would do in SQLite but is not"
             " portable.",
        claims=[("a few services, each with one class only",
                 lambda rows, c: 2 < len(rows) < 20 and all(
                     c.execute("SELECT COUNT(DISTINCT class) FROM tickets"
                               " WHERE service_id = ?", (r[0],)).fetchone()[0]
                     == 1 for r in rows))],
    ),
    # ================================================= 6 Window functions
    dict(
        id=19, ledger="Q630", concept="W1", tier="6 - Window functions",
        title="A centred three-month average",
        prompt=(
            "Tickets sold per month, each with the average of that month,"
            " the one before and the one after, to one decimal. At the two"
            " ends, average what is there.\n\n"
            "Return: month, tickets, centred_avg"
        ),
        solution=("SELECT m, n, ROUND(AVG(n) OVER (ORDER BY m ROWS BETWEEN"
                  " 1 PRECEDING AND 1 FOLLOWING), 1) FROM (SELECT"
                  " strftime('%Y-%m', sold_at) m, COUNT(*) n FROM tickets"
                  " GROUP BY 1)"),
        trap_sql=("SELECT m, n, ROUND(AVG(n) OVER (ORDER BY m ROWS BETWEEN"
                  " 2 PRECEDING AND CURRENT ROW), 1) FROM (SELECT"
                  " strftime('%Y-%m', sold_at) m, COUNT(*) n FROM tickets"
                  " GROUP BY 1)"),
        note="A frame can reach forward: 1 PRECEDING AND 1 FOLLOWING is"
             " three rows centred on the current one. The trap is a"
             " TRAILING three-month average -- the same width, shifted one"
             " month late -- which is a fine thing to compute and not what"
             " was asked. AVG over a frame that runs off the end averages"
             " the rows that exist, which is what the prompt wants at the"
             " edges.",
        claims=[("eighteen months, the middle rows a three-month mean",
                 lambda rows, c: len(rows) == 18 and all(
                     abs(rows[i][2] - (rows[i-1][1] + rows[i][1]
                                       + rows[i+1][1]) / 3) < 0.06
                     for i in range(1, 17)))],
    ),
    dict(
        id=20, ledger="Q631", concept="W2", tier="6 - Window functions",
        title="The two hardest-working units of each model",
        prompt=(
            "For each model, its two units with the most workings -- rows"
            " in service_units -- and the count. Fourteen rows; ties by the"
            " lower unit_id.\n\n"
            "Return: model, unit_id, workings"
        ),
        solution=("SELECT model, unit_id, w FROM (SELECT r.model, r.unit_id,"
                  " COUNT(*) w, ROW_NUMBER() OVER (PARTITION BY r.model"
                  " ORDER BY COUNT(*) DESC, r.unit_id) rn FROM rolling_stock r"
                  " JOIN service_units su ON su.unit_id = r.unit_id"
                  " GROUP BY r.unit_id) WHERE rn <= 2"),
        trap_sql=("SELECT model, unit_id, w FROM (SELECT r.model, r.unit_id,"
                  " COUNT(*) w, ROW_NUMBER() OVER ("
                  " ORDER BY COUNT(*) DESC, r.unit_id) rn FROM rolling_stock r"
                  " JOIN service_units su ON su.unit_id = r.unit_id"
                  " GROUP BY r.unit_id) WHERE rn <= 2"),
        note="Without PARTITION BY model the numbering runs across the"
             " whole fleet, and rn <= 2 is the two busiest units anywhere"
             " -- two rows, not fourteen. The window's ORDER BY uses the"
             " aggregate directly, because windows are evaluated after"
             " GROUP BY; the tiebreak on unit_id makes the answer"
             " deterministic, which any top-N question needs.",
        claims=[("two per model",
                 lambda rows, c: len(rows) == 14 and all(
                     sum(1 for r in rows if r[0] == m) == 2
                     for m in {r[0] for r in rows}))],
    ),
    dict(
        id=21, ledger="Q632", concept="W3", tier="6 - Window functions",
        title="Each station's share of its town",
        prompt=(
            "Every station's 2025 footfall and what percentage of its"
            " TOWN's 2025 footfall that is, to two decimals. A town with"
            " one station reads 100.\n\n"
            "Return: station_id, town, footfall, pct_of_town"
        ),
        solution=("SELECT st.station_id, st.town, f.q1 + f.q2 + f.q3 + f.q4,"
                  " ROUND(100.0 * (f.q1 + f.q2 + f.q3 + f.q4)"
                  " / SUM(f.q1 + f.q2 + f.q3 + f.q4) OVER (PARTITION BY st.town),"
                  " 2) FROM stations st JOIN station_footfall f"
                  " ON f.station_id = st.station_id AND f.year = 2025"),
        trap_sql=("SELECT st.station_id, st.town, f.q1 + f.q2 + f.q3 + f.q4,"
                  " ROUND(100.0 * (f.q1 + f.q2 + f.q3 + f.q4)"
                  " / SUM(f.q1 + f.q2 + f.q3 + f.q4) OVER (), 2)"
                  " FROM stations st JOIN station_footfall f"
                  " ON f.station_id = st.station_id AND f.year = 2025"),
        note="No GROUP BY at all: one row per station, and the window"
             " supplies the town's total beside each. The trap's OVER ()"
             " is the network total, so the shares are all small and the"
             " single-station towns do not read 100 -- the check the prompt"
             " hands you. The year condition sits in the ON so the join"
             " itself is one row per station.",
        claims=[("sixty stations, every town summing to 100",
                 lambda rows, c: len(rows) == 60 and all(
                     abs(sum(r[3] for r in rows if r[1] == t) - 100) < 0.05
                     for t in {r[1] for r in rows}))],
    ),
    dict(
        id=22, ledger="Q633", concept="W2", tier="6 - Window functions",
        title="Running order for the day",
        prompt=(
            "Every service scheduled on 2025-04-07, cancelled or not,"
            " numbered in departure order from 1. Two pairs depart at the"
            " same minute; number those by service_id, so the numbers run"
            " 1 to 24 with no gaps or repeats.\n\n"
            "Return: position, service_id, depart_time"
        ),
        solution=("SELECT ROW_NUMBER() OVER (ORDER BY depart_time, service_id),"
                  " service_id, depart_time FROM services"
                  " WHERE run_date = '2025-04-07'"),
        trap_sql=("SELECT RANK() OVER (ORDER BY depart_time),"
                  " service_id, depart_time FROM services"
                  " WHERE run_date = '2025-04-07'"),
        note="ROW_NUMBER never repeats; RANK repeats on a tie and then"
             " skips, so the trap numbers two services 5 and none 6. Which"
             " function is right depends on what the number is FOR: a"
             " running order wants every slot filled, a league table wants"
             " ties shared. The tiebreak in the ORDER BY is what makes"
             " ROW_NUMBER's answer reproducible.",
        claims=[("positions 1 to 24 exactly once each",
                 lambda rows, c: sorted(r[0] for r in rows)
                 == list(range(1, 25)))],
    ),
    # ================================================ 7 Changing the data
    # Writable questions. The editor's script runs in a sandbox copy of the
    # database, then probe_sql reads the result and THAT is compared with the
    # reference. driver_sql, where present, is run by the question after the
    # script -- to fire a trigger, or to be refused by one.
    dict(
        id=23, ledger="Q634", concept="DML", tier="7 - Changing the data",
        kind="script",
        title="Scrap a unit that has worked",
        prompt=(
            "Unit 12 is being scrapped. Delete it from `rolling_stock` --"
            " but it has hundreds of rows in `service_units`, and with"
            " foreign keys on, a referenced row cannot go. Remove those"
            " first, then the unit.\n\n"
            "Add RETURNING unit_id, model to the second DELETE so the results"
            " pane shows what went.\n\n"
            "Checked: how many units remain, and how many service_units rows"
            " still name unit 12"
        ),
        solution=("DELETE FROM service_units WHERE unit_id = 12;\n"
                  "DELETE FROM rolling_stock WHERE unit_id = 12\n"
                  "RETURNING unit_id, model;"),
        trap_sql=("DELETE FROM rolling_stock WHERE unit_id = 12\n"
                  "RETURNING unit_id, model;\n"
                  "DELETE FROM service_units WHERE unit_id = 12;"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM rolling_stock),"
                   " (SELECT COUNT(*) FROM service_units WHERE unit_id = 12)"),
        note="Children before parents. With PRAGMA foreign_keys=ON the"
             " trap's first statement fails -- FOREIGN KEY constraint"
             " failed -- and the script stops there. SQLite ships with"
             " foreign keys OFF, in which case the same DELETE succeeds and"
             " leaves orphaned rows, which is worse. RETURNING (3.35+)"
             " makes a DELETE, UPDATE or INSERT hand back rows, so the"
             " results pane shows the unit that went; it changes nothing"
             " about what the statement does.",
        claims=[("one unit fewer, and nothing left pointing at it",
                 lambda rows, c: rows == [(49, 0)])],
    ),
    dict(
        id=24, ledger="Q635", concept="DML", tier="7 - Changing the data",
        kind="script",
        title="Borrow a delay from the timetable",
        prompt=(
            "163 incidents have no delay_minutes. For each, use the worst"
            " lateness recorded at any stop of its service -- actual arrival"
            " minus scheduled, in whole minutes -- as the delay. Incidents"
            " that already have a delay keep it.\n\n"
            "One UPDATE ... FROM, with the per-service worst lateness as a"
            " grouped subquery in the FROM.\n\n"
            "Checked: incidents, how many are quantified, the delay total,"
            " and how many delays are under ten minutes"
        ),
        solution=("UPDATE incidents\n"
                  "SET delay_minutes = x.worst\n"
                  "FROM (SELECT service_id,\n"
                  "             MAX((strftime('%s', actual_arrive)"
                  " - strftime('%s', sched_arrive)) / 60) AS worst\n"
                  "      FROM stops GROUP BY service_id) AS x\n"
                  "WHERE x.service_id = incidents.service_id\n"
                  "  AND incidents.delay_minutes IS NULL;"),
        trap_sql=("UPDATE incidents\n"
                  "SET delay_minutes = x.worst\n"
                  "FROM (SELECT service_id,\n"
                  "             MAX((strftime('%s', actual_arrive)"
                  " - strftime('%s', sched_arrive)) / 60) AS worst\n"
                  "      FROM stops GROUP BY service_id) AS x\n"
                  "WHERE x.service_id = incidents.service_id;"),
        probe_sql=("SELECT COUNT(*), COUNT(delay_minutes), SUM(delay_minutes),"
                   " SUM(delay_minutes < 10) FROM incidents"),
        note="UPDATE ... FROM (3.33+) joins the target to another table or"
             " subquery and takes the new value from the join -- SQLite's"
             " form of the T-SQL UPDATE ... FROM and the Postgres one. The"
             " subquery is grouped to one row per service, so each"
             " incident meets exactly one match; the trap drops the IS NULL"
             " guard and overwrites all 971 delays with single-digit"
             " numbers. 'Rows changed: 971' against 163 is the tell.",
        claims=[("every incident quantified, and only the blanks filled",
                 lambda rows, c: rows[0][1] == rows[0][0]
                 and rows[0][2] > 38000)],
    ),
    dict(
        id=25, ledger="Q636", concept="INS", tier="7 - Changing the data",
        kind="script",
        title="A summary table, built from a CTE",
        prompt=(
            "Create `line_summary (line_id INTEGER PRIMARY KEY, services,"
            " tickets, revenue_pence)`, all NOT NULL, and fill it: per line,"
            " how many services it scheduled, how many tickets it sold and"
            " the revenue. Every line has all three.\n\n"
            "Use a WITH clause in front of the INSERT to compute the rows,"
            " and mind the grain: services with no tickets still count as"
            " services.\n\n"
            "Checked: SELECT * FROM line_summary"
        ),
        solution=("CREATE TABLE line_summary (line_id INTEGER PRIMARY KEY,"
                  " services INTEGER NOT NULL,\n"
                  "                           tickets INTEGER NOT NULL,"
                  " revenue_pence INTEGER NOT NULL);\n"
                  "WITH totals AS (\n"
                  "  SELECT s.line_id, COUNT(DISTINCT s.service_id) AS services,\n"
                  "         COUNT(t.ticket_id) AS tickets,"
                  " COALESCE(SUM(t.price_pence), 0) AS revenue_pence\n"
                  "  FROM services s LEFT JOIN tickets t ON t.service_id = s.service_id\n"
                  "  GROUP BY s.line_id)\n"
                  "INSERT INTO line_summary SELECT * FROM totals;"),
        trap_sql=("CREATE TABLE line_summary (line_id INTEGER PRIMARY KEY,"
                  " services INTEGER NOT NULL,\n"
                  "                           tickets INTEGER NOT NULL,"
                  " revenue_pence INTEGER NOT NULL);\n"
                  "WITH totals AS (\n"
                  "  SELECT s.line_id, COUNT(s.service_id) AS services,\n"
                  "         COUNT(t.ticket_id) AS tickets,"
                  " COALESCE(SUM(t.price_pence), 0) AS revenue_pence\n"
                  "  FROM services s LEFT JOIN tickets t ON t.service_id = s.service_id\n"
                  "  GROUP BY s.line_id)\n"
                  "INSERT INTO line_summary SELECT * FROM totals;"),
        probe_sql="SELECT * FROM line_summary ORDER BY 1",
        note="A CTE can front an INSERT, UPDATE or DELETE, not only a"
             " SELECT; the INSERT then reads it like a table. The join is"
             " one row per TICKET, so COUNT(s.service_id) counts a service"
             " once per ticket -- the trap reports six thousand services"
             " per line for nineteen hundred. COUNT(DISTINCT) repairs it,"
             " and the LEFT JOIN keeps ticketless services in that count."
             " Unlike CREATE TABLE AS, this way the table has a primary"
             " key and NOT NULLs.",
        claims=[("six lines, services summing to the timetable",
                 lambda rows, c: len(rows) == 6
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM services").fetchone()[0]
                 and sum(r[2] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM tickets").fetchone()[0])],
    ),
    dict(
        id=26, ledger="Q637", concept="TXN", tier="7 - Changing the data",
        kind="script",
        title="Commit one, roll back the other",
        prompt=(
            "Two separate transactions. In the first, give every driver a 5%"
            " raise and COMMIT. In the second, give every guard 5% -- then"
            " think better of it and ROLLBACK.\n\n"
            "Whole pounds: CAST(ROUND(salary * 1.05) AS INTEGER). Each"
            " transaction needs its own BEGIN; there is no such thing as"
            " rolling back a statement that was never inside one.\n\n"
            "Checked: total salary by role"
        ),
        solution=("BEGIN;\n"
                  "UPDATE staff SET salary = CAST(ROUND(salary * 1.05) AS INTEGER)"
                  " WHERE role = 'driver';\n"
                  "COMMIT;\n"
                  "BEGIN;\n"
                  "UPDATE staff SET salary = CAST(ROUND(salary * 1.05) AS INTEGER)"
                  " WHERE role = 'guard';\n"
                  "ROLLBACK;"),
        trap_sql=("BEGIN;\n"
                  "UPDATE staff SET salary = CAST(ROUND(salary * 1.05) AS INTEGER)"
                  " WHERE role = 'driver';\n"
                  "COMMIT;\n"
                  "UPDATE staff SET salary = CAST(ROUND(salary * 1.05) AS INTEGER)"
                  " WHERE role = 'guard';\n"
                  "ROLLBACK;"),
        probe_sql="SELECT role, SUM(salary) FROM staff GROUP BY 1",
        note="COMMIT ends the transaction. Anything after it runs in"
             " autocommit -- each statement its own transaction, committed"
             " the instant it finishes -- so the trap's guards' raise is"
             " permanent before the ROLLBACK is reached, and the ROLLBACK"
             " itself fails: 'no transaction is active'. A second BEGIN is"
             " what makes the second change undoable. T-SQL behaves the"
             " same way; only the keyword differs.",
        claims=[("drivers up five percent, guards unchanged",
                 lambda rows, c: dict(rows)['driver'] == 466776
                 and dict(rows)['guard'] == 732540)],
    ),
    dict(
        id=27, ledger="Q638", concept="TRG", tier="7 - Changing the data",
        kind="script",
        title="A count that keeps itself right",
        prompt=(
            "Create `line_cancellations (line_id INTEGER PRIMARY KEY,"
            " cancelled INTEGER NOT NULL)` filled with each line's current"
            " cancellation count, then a trigger that adds one whenever a"
            " service's cancelled flag goes from 0 to 1 -- and does nothing"
            " when a service already cancelled is 'cancelled' again.\n\n"
            "After your script, the question cancels services 5 and 6 (line"
            " 2), then re-cancels service 79 (line 3), which already was.\n\n"
            "Checked: the table, in line order"
        ),
        solution=("CREATE TABLE line_cancellations (line_id INTEGER PRIMARY KEY,"
                  " cancelled INTEGER NOT NULL);\n"
                  "INSERT INTO line_cancellations\n"
                  "SELECT line_id, SUM(cancelled) FROM services GROUP BY line_id;\n"
                  "CREATE TRIGGER count_cancellation\n"
                  "AFTER UPDATE OF cancelled ON services\n"
                  "WHEN NEW.cancelled = 1 AND OLD.cancelled = 0\n"
                  "BEGIN\n"
                  "  UPDATE line_cancellations SET cancelled = cancelled + 1\n"
                  "  WHERE line_id = NEW.line_id;\n"
                  "END;"),
        trap_sql=("CREATE TABLE line_cancellations (line_id INTEGER PRIMARY KEY,"
                  " cancelled INTEGER NOT NULL);\n"
                  "INSERT INTO line_cancellations\n"
                  "SELECT line_id, SUM(cancelled) FROM services GROUP BY line_id;\n"
                  "CREATE TRIGGER count_cancellation\n"
                  "AFTER UPDATE OF cancelled ON services\n"
                  "BEGIN\n"
                  "  UPDATE line_cancellations SET cancelled = cancelled + 1\n"
                  "  WHERE line_id = NEW.line_id;\n"
                  "END;"),
        driver_sql=("UPDATE services SET cancelled = 1 WHERE service_id IN (5, 6);\n"
                    "UPDATE services SET cancelled = 1 WHERE service_id = 79;"),
        probe_sql="SELECT line_id, cancelled FROM line_cancellations ORDER BY 1",
        note="A trigger maintaining a summary -- the pattern behind"
             " counters, balances and denormalised totals. The WHEN clause"
             " is the whole difficulty: UPDATE OF cancelled fires on any"
             " write to the column, including 1 -> 1, and only OLD versus"
             " NEW can tell a real cancellation from a repeat. The trap"
             " counts line 3 up for a service that was already cancelled."
             " The trigger runs once per row, so the two-service UPDATE"
             " adds two.",
        claims=[("line 2 up by two, line 3 unchanged",
                 lambda rows, c: dict(rows)[2] == 54 and dict(rows)[3] == 50)],
    ),
    dict(
        id=28, ledger="Q639", concept="TRG", tier="7 - Changing the data",
        kind="script",
        title="No pay cuts",
        prompt=(
            "Write a trigger that refuses any UPDATE that would LOWER a"
            " member of staff's salary. Raises go through; so does setting"
            " a salary to the value it already has.\n\n"
            "After your script, the question runs three updates: staff 2 to"
            " 50000 (a raise), staff 3 to 30000 (a cut), staff 4 to its"
            " current 40713. Exactly one should be refused.\n\n"
            "Checked: the three salaries"
        ),
        solution=("CREATE TRIGGER no_pay_cuts\n"
                  "BEFORE UPDATE OF salary ON staff\n"
                  "WHEN NEW.salary < OLD.salary\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'salaries may not be cut');\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER no_pay_cuts\n"
                  "BEFORE UPDATE OF salary ON staff\n"
                  "WHEN NEW.salary > OLD.salary\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'salaries may not be cut');\n"
                  "END;"),
        driver_sql=("UPDATE staff SET salary = 50000 WHERE staff_id = 2;\n"
                    "UPDATE staff SET salary = 30000 WHERE staff_id = 3;\n"
                    "UPDATE staff SET salary = 40713 WHERE staff_id = 4;"),
        probe_sql=("SELECT staff_id, salary FROM staff"
                   " WHERE staff_id IN (2, 3, 4) ORDER BY 1"),
        note="An UPDATE trigger has both rows: OLD is the salary now, NEW"
             " the one being written, and the rule is a comparison of the"
             " two. The trap has them the wrong way round and refuses the"
             " raise while waving the cut through -- a trigger that"
             " enforces the opposite of its policy, with a message that"
             " says otherwise. The unchanged salary passes either way,"
             " because neither < nor > holds when they are equal.",
        claims=[("the raise landed, the cut did not",
                 lambda rows, c: rows == [(2, 50000), (3, 39212), (4, 40713)])],
    ),
    dict(
        id=29, ledger="Q640", concept="VIEW", tier="7 - Changing the data",
        kind="script",
        title="The footfall table, long",
        prompt=(
            "Create a view `footfall_long (station_id, year, quarter,"
            " footfall)` that presents station_footfall one row per quarter,"
            " with quarter as the number 1 to 4. 720 rows when selected.\n\n"
            "Checked: COUNT(*), SUM(footfall) and COUNT(DISTINCT quarter)"
            " over the view"
        ),
        solution=("CREATE VIEW footfall_long AS\n"
                  "SELECT station_id, year, 1 AS quarter, q1 AS footfall"
                  " FROM station_footfall\n"
                  "UNION ALL SELECT station_id, year, 2, q2 FROM station_footfall\n"
                  "UNION ALL SELECT station_id, year, 3, q3 FROM station_footfall\n"
                  "UNION ALL SELECT station_id, year, 4, q4 FROM station_footfall;"),
        trap_sql=("CREATE VIEW footfall_long AS\n"
                  "SELECT station_id, year, 1 AS quarter, q1 AS footfall"
                  " FROM station_footfall\n"
                  "UNION ALL SELECT station_id, year, 2, q2 FROM station_footfall\n"
                  "UNION ALL SELECT station_id, year, 3, q2 FROM station_footfall\n"
                  "UNION ALL SELECT station_id, year, 4, q4 FROM station_footfall;"),
        probe_sql=("SELECT COUNT(*), SUM(footfall), COUNT(DISTINCT quarter)"
                   " FROM footfall_long"),
        note="An unpivot saved as a view: every quarterly question from"
             " here on is a plain GROUP BY over it instead of four UNION"
             " branches. A compound SELECT takes its column names from"
             " the FIRST branch, so only that one needs the aliases. The"
             " trap is the copy-and-paste slip again -- the q3 branch"
             " reads q2 -- and a view hides it more thoroughly than a"
             " query does, because nobody re-reads a view.",
        claims=[("720 rows, four quarters, the table's total",
                 lambda rows, c: rows[0][0] == 720 and rows[0][2] == 4
                 and rows[0][1] == c.execute(
                     "SELECT SUM(q1 + q2 + q3 + q4) FROM station_footfall"
                 ).fetchone()[0])],
    ),
    dict(
        id=30, ledger="Q641", concept="R1", tier="7 - Changing the data",
        kind="script",
        title="A calendar table for July",
        prompt=(
            "Create a table `days (day TEXT PRIMARY KEY)` and fill it with"
            " every date in July 2025, generated -- not typed -- by a"
            " recursive CTE feeding an INSERT. 31 rows.\n\n"
            "Checked: how many rows, the first and the last"
        ),
        solution=("CREATE TABLE days (day TEXT PRIMARY KEY);\n"
                  "WITH RECURSIVE d(day) AS (\n"
                  "  SELECT '2025-07-01'\n"
                  "  UNION ALL\n"
                  "  SELECT date(day, '+1 day') FROM d WHERE day < '2025-07-31')\n"
                  "INSERT INTO days SELECT day FROM d;"),
        trap_sql=("CREATE TABLE days (day TEXT PRIMARY KEY);\n"
                  "WITH RECURSIVE d(day) AS (\n"
                  "  SELECT '2025-07-01'\n"
                  "  UNION ALL\n"
                  "  SELECT date(day, '+1 day') FROM d WHERE day < '2025-07-30')\n"
                  "INSERT INTO days SELECT day FROM d;"),
        probe_sql="SELECT COUNT(*), MIN(day), MAX(day) FROM days",
        note="A date spine, made permanent. The recursive step produces the"
             " NEXT day from the current one, so the stop condition is on"
             " the day being read, not the day being produced: WHERE day <"
             " '2025-07-31' still emits the 31st, and the trap's 30th stops"
             " one short. The WITH goes before the INSERT, exactly as it"
             " would before a SELECT. Left-join anything to this table and"
             " quiet days appear as zeros instead of vanishing.",
        claims=[("thirty-one days, the first and last of July",
                 lambda rows, c: rows == [(31, '2025-07-01', '2025-07-31')])],
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
