"""Practice exercises: thirty questions on the railway schema.

Twenty-two are SELECT questions across the usual tiers, graded on the rows
they return. The last eight are WRITABLE questions, graded on the state of the
database after your script runs. They cover what SQLite has in place of a
procedural language, and this set takes a different construct in each slot
from the last one --

  * DELETE and UPDATE driven by subqueries, one of them correlated
  * INSERT ... SELECT, and the type affinity that decides what gets stored
  * nested SAVEPOINTs, and what RELEASE does and does not do
  * an INSTEAD OF trigger that makes a view writable
  * an AFTER DELETE trigger, where only OLD exists
  * a view with a computed column and a filter its users must not forget
  * ALTER TABLE: rename, add with a default, drop

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script -- the insert that should go through
your view, or the delete your trigger should catch.
"""

import sqlite3

EXERCISES = [
    # ========================================================== 1 Warm-up
    dict(
        id=1, ledger="Q582", concept="A2", tier="1 - Warm-up",
        title="Seats by model",
        prompt=(
            "One row per model of rolling stock: how many units, the seats"
            " across all of them, and the average seats per unit to the"
            " nearest seat.\n\n"
            "Return: model, units, total_seats, avg_seats"
        ),
        solution=("SELECT model, COUNT(*), SUM(seats), ROUND(AVG(seats))"
                  " FROM rolling_stock GROUP BY 1"),
        trap_sql=("SELECT model, COUNT(*), SUM(seats),"
                  " ROUND(SUM(seats) / COUNT(*)) FROM rolling_stock"
                  " GROUP BY 1"),
        note="SUM(seats) / COUNT(*) is one integer divided by another, so it"
             " truncates BEFORE ROUND ever sees it: 2478 / 13 is 190, and"
             " ROUND(190) is 190, where the average is 190.6 and rounds to"
             " 191. AVG returns a REAL however integer its input, which is"
             " exactly why it exists as a separate function.",
        claims=[("seven models, every average a whole number",
                 lambda rows, c: len(rows) == 7
                 and all(r[3] == int(r[3]) for r in rows))],
    ),
    dict(
        id=2, ledger="Q583", concept="N1", tier="1 - Warm-up",
        title="Takings per operator, in pounds",
        prompt=(
            "One row per operator: how many tickets were sold on its"
            " services, and the revenue in POUNDS to two decimals.\n\n"
            "price_pence is an integer.\n\n"
            "Return: operator, tickets, revenue_pounds"
        ),
        solution=("SELECT o.name, COUNT(*), ROUND(SUM(t.price_pence) / 100.0, 2)"
                  " FROM operators o JOIN services s"
                  " ON s.operator_id = o.operator_id JOIN tickets t"
                  " ON t.service_id = s.service_id GROUP BY o.name"),
        trap_sql=("SELECT o.name, COUNT(*), ROUND(SUM(t.price_pence) / 100, 2)"
                  " FROM operators o JOIN services s"
                  " ON s.operator_id = o.operator_id JOIN tickets t"
                  " ON t.service_id = s.service_id GROUP BY o.name"),
        note="14871697 pence / 100 is 148716 -- integer division drops the"
             " 97p, and ROUND(148716, 2) has nothing to restore. Divide by"
             " 100.0 and the whole expression is REAL. The join runs"
             " operators -> services -> tickets; a ticket belongs to one"
             " service and a service to one operator, so nothing fans out.",
        claims=[("four operators, and the revenue carries pence",
                 lambda rows, c: len(rows) == 4
                 and any(r[2] != int(r[2]) for r in rows))],
    ),
    dict(
        id=3, ledger="Q584", concept="A3", tier="1 - Warm-up",
        title="Common, roomy models",
        prompt=(
            "Models with at least 5 units whose average seats per unit is"
            " above 200, with the unit count and that average to the nearest"
            " seat.\n\n"
            "Both conditions describe the model as a whole, not any one"
            " unit.\n\n"
            "Return: model, units, avg_seats"
        ),
        solution=("SELECT model, COUNT(*), ROUND(AVG(seats)) FROM rolling_stock"
                  " GROUP BY model HAVING COUNT(*) >= 5 AND AVG(seats) > 200"),
        trap_sql=("SELECT model, COUNT(*), ROUND(AVG(seats)) FROM rolling_stock"
                  " WHERE seats > 200 GROUP BY model HAVING COUNT(*) >= 5"),
        note="WHERE seats > 200 throws away the small units before the"
             " average is taken, so every model's average rises and the"
             " count is of big units only -- a different question with"
             " tidy-looking answers. A condition on an aggregate belongs in"
             " HAVING, which sees each group whole.",
        claims=[("every model returned satisfies both conditions",
                 lambda rows, c: len(rows) > 0
                 and all(r[1] >= 5 and r[2] > 200 for r in rows))],
    ),
    # ========================================== 2 Sequences and strings
    dict(
        id=4, ledger="Q585", concept="W3", tier="2 - Sequences and strings",
        title="The shortest leg of each service",
        prompt=(
            "For every service that ran on 2025-03-03: the fewest minutes"
            " between one scheduled call and the next.\n\n"
            "A leg belongs to one service. The gap must never be measured"
            " from the previous service's last stop to this one's first.\n\n"
            "Return: service_id, shortest_leg"
        ),
        solution=("SELECT service_id, MIN(gap) FROM (SELECT service_id,"
                  " (strftime('%s', sched_arrive) - strftime('%s',"
                  " LAG(sched_arrive) OVER (PARTITION BY service_id"
                  " ORDER BY stop_seq))) / 60 gap FROM stops"
                  " WHERE service_id IN (SELECT service_id FROM services"
                  " WHERE run_date = '2025-03-03')) GROUP BY service_id"),
        trap_sql=("SELECT service_id, MIN(gap) FROM (SELECT service_id,"
                  " (strftime('%s', sched_arrive) - strftime('%s',"
                  " LAG(sched_arrive) OVER (ORDER BY service_id, stop_seq)))"
                  " / 60 gap FROM stops"
                  " WHERE service_id IN (SELECT service_id FROM services"
                  " WHERE run_date = '2025-03-03')) GROUP BY service_id"),
        note="LAG needs a PARTITION BY as well as an ORDER BY when the"
             " sequence restarts. Ordered by (service_id, stop_seq) alone,"
             " the first stop of each service looks back at the previous"
             " service's last stop -- a gap of several hours, or negative"
             " when the next service departs earlier -- and MIN picks that"
             " up. The window function has to sit in a subquery because MIN"
             " runs after it.",
        claims=[("services that ran that day, every leg a few minutes",
                 lambda rows, c: len(rows) > 10
                 and all(0 < r[1] < 30 for r in rows))],
    ),
    dict(
        id=5, ledger="Q586", concept="STR", tier="2 - Sequences and strings",
        title="Surnames on the payroll",
        prompt=(
            "How many staff share each surname. Every name is exactly two"
            " words; the surname is the second.\n\n"
            "Most common first, ties by surname.\n\n"
            "Return: surname, staff"
        ),
        solution=("SELECT SUBSTR(name, INSTR(name, ' ') + 1), COUNT(*)"
                  " FROM staff GROUP BY 1 ORDER BY 2 DESC, 1"),
        trap_sql=("SELECT SUBSTR(name, INSTR(name, ' ')), COUNT(*)"
                  " FROM staff GROUP BY 1 ORDER BY 2 DESC, 1"),
        note="INSTR returns the position of the space, and SUBSTR from"
             " THERE keeps it: ' Jepson' with a leading blank. The counts"
             " are all right and the strings all wrong, which the grader"
             " notices and an eye does not. Start one character past the"
             " separator. This only works because every name has one space;"
             " question 5 of the last set had the idiom for the general case.",
        claims=[("forty staff counted, no surname starting with a space",
                 lambda rows, c: sum(r[1] for r in rows) == 40
                 and not any(r[0].startswith(' ') for r in rows))],
    ),
    dict(
        id=6, ledger="Q587", concept="W3", tier="2 - Sequences and strings",
        title="Lateness, stop by stop",
        prompt=(
            "For service 311, each stop's lateness in minutes -- actual"
            " arrival minus scheduled -- and how much that changed since the"
            " previous stop.\n\n"
            "A stop with no recorded arrival has NULL lateness and NULL"
            " change, and so does the stop after it. The first stop's change"
            " is NULL.\n\n"
            "Return: stop_seq, late_minutes, change"
        ),
        solution=("SELECT stop_seq, late, late - LAG(late) OVER"
                  " (ORDER BY stop_seq) FROM (SELECT stop_seq,"
                  " (strftime('%s', actual_arrive) - strftime('%s',"
                  " sched_arrive)) / 60 late FROM stops WHERE service_id = 311)"),
        trap_sql=("SELECT stop_seq, late, late - LAG(late) OVER"
                  " (ORDER BY stop_seq) FROM (SELECT stop_seq,"
                  " CAST(strftime('%M', actual_arrive) AS INTEGER)"
                  " - CAST(strftime('%M', sched_arrive) AS INTEGER) late"
                  " FROM stops WHERE service_id = 311)"),
        note="Subtracting the minute fields alone is right until an arrival"
             " crosses the hour: scheduled 07:58, actual 08:03, is 3 - 58 ="
             " -55 instead of 5. strftime('%s') turns either time into"
             " seconds since midnight and the difference is honest. NULL"
             " arithmetic does the rest for free -- NULL minus anything is"
             " NULL, so an unrecorded stop blanks its own change and the"
             " next stop's.",
        claims=[("first change NULL, exactly one unrecorded stop",
                 lambda rows, c: rows[0][2] is None
                 and sum(1 for r in rows if r[1] is None) == 1)],
    ),
    dict(
        id=7, ledger="Q588", concept="S1", tier="2 - Sequences and strings",
        title="Days with trouble but no cancellations",
        prompt=(
            "Dates on which at least one incident was reported but NO"
            " service was cancelled.\n\n"
            "Incidents are dated by reported_at, cancellations by run_date."
            " One column, one row per date.\n\n"
            "Return: day"
        ),
        solution=("SELECT reported_at FROM incidents EXCEPT SELECT run_date"
                  " FROM services WHERE cancelled = 1"),
        trap_sql=("SELECT DISTINCT s.run_date FROM services s JOIN incidents i"
                  " ON i.service_id = s.service_id WHERE s.cancelled = 0"),
        note="The trap asks whether the incident's OWN service was cancelled"
             " -- never, since a cancelled service runs nothing that can go"
             " wrong -- and so returns every date with an incident. 'No"
             " service was cancelled that day' is a statement about the"
             " whole day, which is a set of dates to take away: EXCEPT. It"
             " deduplicates as it goes, so DISTINCT is not needed.",
        claims=[("many days, none with a cancellation",
                 lambda rows, c: len(rows) > 100 and not c.execute(
                     "SELECT 1 FROM services WHERE cancelled = 1"
                     " AND run_date IN (%s) LIMIT 1"
                     % ",".join("'%s'" % r[0] for r in rows)).fetchall())],
    ),
    # ============================================ 3 Unpivot and set ops
    dict(
        id=8, ledger="Q589", concept="UNP", tier="3 - Unpivot and set ops",
        title="Station 5, quarter by quarter",
        prompt=(
            "Station 5's footfall as one ROW per quarter, across every year"
            " it has a row for, labelled like '2024-q3'. Twelve rows,"
            " earliest first.\n\n"
            "Return: period, footfall"
        ),
        solution=("SELECT year || '-q1', q1 FROM station_footfall"
                  " WHERE station_id = 5 UNION ALL SELECT year || '-q2', q2"
                  " FROM station_footfall WHERE station_id = 5"
                  " UNION ALL SELECT year || '-q3', q3 FROM station_footfall"
                  " WHERE station_id = 5 UNION ALL SELECT year || '-q4', q4"
                  " FROM station_footfall WHERE station_id = 5 ORDER BY 1"),
        trap_sql=("SELECT year || '-q1', q1 FROM station_footfall"
                  " WHERE station_id = 5 UNION ALL SELECT year || '-q2', q2"
                  " FROM station_footfall WHERE station_id = 5"
                  " UNION ALL SELECT year || '-q3', q2 FROM station_footfall"
                  " WHERE station_id = 5 UNION ALL SELECT year || '-q4', q4"
                  " FROM station_footfall WHERE station_id = 5 ORDER BY 1"),
        note="Three years times four quarters is twelve rows from four"
             " branches, because each branch returns one row per YEAR. The"
             " label is built from the year column so it comes out right for"
             " every year without being typed. The trap is the usual"
             " copy-and-paste slip: the q3 branch selects q2. An ORDER BY"
             " on a compound SELECT applies to the whole result and goes"
             " last.",
        claims=[("twelve distinct periods, totalling the station's footfall",
                 lambda rows, c: len(rows) == 12
                 and len({r[0] for r in rows}) == 12
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT SUM(q1 + q2 + q3 + q4) FROM station_footfall"
                     " WHERE station_id = 5").fetchone()[0])],
    ),
    dict(
        id=9, ledger="Q590", concept="J1", tier="3 - Unpivot and set ops",
        title="Opened in the same year",
        prompt=(
            "Pairs of stations that opened in the same calendar year, with"
            " the year. Each pair once, the lower station_id first.\n\n"
            "Return: station_a, station_b, year"
        ),
        solution=("SELECT a.station_id, b.station_id, strftime('%Y', a.opened_on)"
                  " FROM stations a JOIN stations b"
                  " ON strftime('%Y', b.opened_on) = strftime('%Y', a.opened_on)"
                  " AND b.station_id > a.station_id"),
        trap_sql=("SELECT a.station_id, b.station_id, strftime('%Y', a.opened_on)"
                  " FROM stations a JOIN stations b"
                  " ON strftime('%Y', b.opened_on) = strftime('%Y', a.opened_on)"
                  " AND b.station_id <> a.station_id"),
        note="A self-join on a derived value -- the year -- rather than a"
             " key. <> keeps a station from pairing with itself but still"
             " produces (2, 33) AND (33, 2), so the trap returns every pair"
             " twice. a < b is the standard way to get each unordered pair"
             " once. Three stations in one year give three pairs, which is"
             " right.",
        claims=[("more than ten pairs, each with the lower id first",
                 lambda rows, c: len(rows) > 10
                 and all(r[0] < r[1] for r in rows))],
    ),
    dict(
        id=10, ledger="Q591", concept="S1", tier="3 - Unpivot and set ops",
        title="Formations both lines have used",
        prompt=(
            "Two-unit formations -- the front unit and the rear unit, in"
            " that order -- that have run on both line 1 and line 2.\n\n"
            "A formation is ordered: unit 9 leading unit 8 is not the same"
            " as unit 8 leading unit 9. Position 1 is the front.\n\n"
            "Return: front_unit, rear_unit"
        ),
        solution=("SELECT f.unit_id, r.unit_id FROM service_units f"
                  " JOIN service_units r ON r.service_id = f.service_id"
                  " AND r.position = 2 JOIN services s"
                  " ON s.service_id = f.service_id WHERE f.position = 1"
                  " AND s.line_id = 1 INTERSECT SELECT f.unit_id, r.unit_id"
                  " FROM service_units f JOIN service_units r"
                  " ON r.service_id = f.service_id AND r.position = 2"
                  " JOIN services s ON s.service_id = f.service_id"
                  " WHERE f.position = 1 AND s.line_id = 2"),
        trap_sql=("SELECT a.unit_id, b.unit_id FROM service_units a"
                  " JOIN service_units b ON b.service_id = a.service_id"
                  " AND b.unit_id > a.unit_id JOIN services s"
                  " ON s.service_id = a.service_id WHERE s.line_id = 1"
                  " INTERSECT SELECT a.unit_id, b.unit_id FROM service_units a"
                  " JOIN service_units b ON b.service_id = a.service_id"
                  " AND b.unit_id > a.unit_id JOIN services s"
                  " ON s.service_id = a.service_id WHERE s.line_id = 2"),
        note="Two mechanisms at once. The self-join on service_units pairs"
             " the front row with the rear row of the same service; then"
             " INTERSECT keeps the (front, rear) pairs that appear in both"
             " lines' sets -- set operations compare whole rows, however"
             " many columns. The trap pairs by unit_id order, which folds"
             " (9, 8) into (8, 9) and halves the answer: the formation, not"
             " the pair of units, is what the question asked for.",
        claims=[("dozens of formations, no unit leading itself",
                 lambda rows, c: len(rows) > 10
                 and all(r[0] != r[1] for r in rows))],
    ),
    # ================================================= 4 Dates and times
    dict(
        id=11, ledger="Q592", concept="D1", tier="4 - Dates and times",
        title="Incidents by quarter",
        prompt=(
            "How many incidents were reported in each calendar quarter,"
            " labelled like '2025-Q3', earliest first. Six quarters.\n\n"
            "strftime has no quarter code: build it from the month.\n\n"
            "Return: quarter, incidents"
        ),
        solution=("SELECT strftime('%Y', reported_at) || '-Q'"
                  " || ((CAST(strftime('%m', reported_at) AS INTEGER) + 2) / 3),"
                  " COUNT(*) FROM incidents GROUP BY 1 ORDER BY 1"),
        trap_sql=("SELECT strftime('%Y', reported_at) || '-Q'"
                  " || (CAST(strftime('%m', reported_at) AS INTEGER) / 3),"
                  " COUNT(*) FROM incidents GROUP BY 1 ORDER BY 1"),
        note="Months 1-3 are quarter 1, so (month + 2) / 3 with integer"
             " division: 3/3 = 1, 5/3 = 1, 6/3 = 2. Plain month / 3 puts"
             " January and February in a 'Q0' and December in its own Q4,"
             " eight labels for six quarters. strftime returns TEXT, so"
             " CAST before doing arithmetic -- '03' + 2 does coerce in"
             " SQLite, but not everywhere.",
        claims=[("six quarters labelled Q1 to Q4, totalling every incident",
                 lambda rows, c: len(rows) == 6
                 and all(r[0][-2:] in ('Q1', 'Q2', 'Q3', 'Q4') for r in rows)
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM incidents").fetchone()[0])],
    ),
    dict(
        id=12, ledger="Q593", concept="D1", tier="4 - Dates and times",
        title="Journey time by line",
        prompt=(
            "For each line, the average scheduled journey in minutes, to one"
            " decimal: from the service's departure to its LAST scheduled"
            " call.\n\n"
            "The departure time is in `services`; the calls are in `stops`."
            " Cancelled services have no stops and must not count.\n\n"
            "Return: line_id, avg_minutes"
        ),
        solution=("SELECT s.line_id, ROUND(AVG((strftime('%s', x.last_call)"
                  " - strftime('%s', s.depart_time)) / 60.0), 1)"
                  " FROM services s JOIN (SELECT service_id,"
                  " MAX(sched_arrive) last_call FROM stops GROUP BY 1) x"
                  " ON x.service_id = s.service_id GROUP BY 1"),
        trap_sql=("SELECT s.line_id, ROUND(AVG((strftime('%s', x.last_call)"
                  " - strftime('%s', x.first_call)) / 60.0), 1)"
                  " FROM services s JOIN (SELECT service_id,"
                  " MAX(sched_arrive) last_call, MIN(sched_arrive) first_call"
                  " FROM stops GROUP BY 1) x"
                  " ON x.service_id = s.service_id GROUP BY 1"),
        note="The trap measures first call to last call, which leaves out"
             " the run from the origin -- nine minutes on average, every"
             " line about nine short. The departure is a column of"
             " `services`, so the journey has to reach both tables. MAX of"
             " an 'HH:MM' string is the latest time because the format is"
             " fixed-width; the inner join drops the cancelled services on"
             " its own, since they have no stops to aggregate.",
        claims=[("six lines, all between fifty and two hundred minutes",
                 lambda rows, c: len(rows) == 6
                 and all(50 < r[1] < 200 for r in rows))],
    ),
    dict(
        id=13, ledger="Q594", concept="D1", tier="4 - Dates and times",
        title="How old each station is",
        prompt=(
            "Every station's age in completed years on 2026-06-30.\n\n"
            "A station opened on 1952-11-18 is 73 that day, not 74: its"
            " anniversary has not come round yet.\n\n"
            "Return: station_id, age"
        ),
        solution=("SELECT station_id, strftime('%Y', '2026-06-30')"
                  " - strftime('%Y', opened_on) - (strftime('%m-%d', '2026-06-30')"
                  " < strftime('%m-%d', opened_on)) FROM stations"),
        trap_sql=("SELECT station_id, strftime('%Y', '2026-06-30')"
                  " - strftime('%Y', opened_on) FROM stations"),
        note="Year minus year is right only for stations whose anniversary"
             " has passed. The fix is to subtract one when the month-day of"
             " the opening is later in the year than today's -- and a"
             " comparison in SQLite is 0 or 1, so it can be subtracted"
             " directly. Dividing julianday differences by 365.25 gets"
             " within a day of this and is wrong on some of those days.",
        claims=[("sixty stations, and the naive year difference overstates some",
                 lambda rows, c: len(rows) == 60
                 and sum(r[1] for r in rows) < c.execute(
                     "SELECT SUM(strftime('%Y', '2026-06-30')"
                     " - strftime('%Y', opened_on)) FROM stations"
                 ).fetchone()[0])],
    ),
    dict(
        id=14, ledger="Q595", concept="D2", tier="4 - Dates and times",
        title="The last week of each month",
        prompt=(
            "How many services ran in the last seven days of each month --"
            " the 25th to the 31st of a 31-day month, the 22nd to the 28th"
            " of February 2026. Eighteen months.\n\n"
            "Build the window with date modifiers, not a day-of-month"
            " number.\n\n"
            "Return: month, services"
        ),
        solution=("SELECT strftime('%Y-%m', run_date), COUNT(*) FROM services"
                  " WHERE run_date >= date(run_date, 'start of month',"
                  " '+1 month', '-7 days') GROUP BY 1"),
        trap_sql=("SELECT strftime('%Y-%m', run_date), COUNT(*) FROM services"
                  " WHERE CAST(strftime('%d', run_date) AS INTEGER) >= 25"
                  " GROUP BY 1"),
        note="'start of month', '+1 month' is the first of NEXT month, and"
             " '-7 days' from there is the first of the last seven. The"
             " trap's >= 25 is right in every 31-day month and short by one"
             " or three days in the others, which is the kind of wrong that"
             " survives a glance at the output. Modifiers apply left to"
             " right, so the order matters.",
        claims=[("eighteen months with varying counts",
                 lambda rows, c: len(rows) == 18
                 and len({r[1] for r in rows}) > 5)],
    ),
    # ================================================= 5 Joins and grain
    dict(
        id=15, ledger="Q596", concept="J2", tier="5 - Joins and grain",
        title="Drivers based in each town",
        prompt=(
            "Every town with the number of DRIVERS based at its stations."
            " Towns with none must appear with 0, so all 20 towns come"
            " back.\n\n"
            "Return: town, drivers"
        ),
        solution=("SELECT st.town, COUNT(sf.staff_id) FROM stations st"
                  " LEFT JOIN staff sf ON sf.base_station = st.station_id"
                  " AND sf.role = 'driver' GROUP BY st.town"),
        trap_sql=("SELECT st.town, COUNT(sf.staff_id) FROM stations st"
                  " LEFT JOIN staff sf ON sf.base_station = st.station_id"
                  " WHERE sf.role = 'driver' GROUP BY st.town"),
        note="A condition on the RIGHT table of an outer join goes in ON,"
             " not WHERE. In WHERE it runs after the join, and a town with"
             " no drivers has sf.role NULL there -- which is not 'driver',"
             " so the row is dropped and the outer join has been turned"
             " back into an inner one. In ON, the condition decides what"
             " matches; unmatched towns are kept with NULLs, and COUNT of a"
             " right-table column counts them as 0.",
        claims=[("all twenty towns, some with none, totalling the drivers",
                 lambda rows, c: len(rows) == 20
                 and any(r[1] == 0 for r in rows)
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM staff WHERE role = 'driver'"
                 ).fetchone()[0])],
    ),
    dict(
        id=16, ledger="Q597", concept="C2", tier="5 - Joins and grain",
        title="Takings and delay per operator",
        prompt=(
            "For each operator: total ticket revenue in pence, and total"
            " quantified delay minutes, across its services.\n\n"
            "Tickets and incidents both hang off `services`. Joining both at"
            " once multiplies every ticket by the service's incidents, and"
            " the other way round.\n\n"
            "Return: operator, revenue, delay_minutes"
        ),
        solution=("WITH rev AS (SELECT s.operator_id, SUM(t.price_pence) r"
                  " FROM services s JOIN tickets t ON t.service_id = s.service_id"
                  " GROUP BY 1), dly AS (SELECT s.operator_id,"
                  " SUM(i.delay_minutes) d FROM services s JOIN incidents i"
                  " ON i.service_id = s.service_id GROUP BY 1)"
                  " SELECT o.name, rev.r, dly.d FROM operators o"
                  " JOIN rev ON rev.operator_id = o.operator_id"
                  " JOIN dly ON dly.operator_id = o.operator_id"),
        trap_sql=("SELECT o.name, SUM(t.price_pence), SUM(i.delay_minutes)"
                  " FROM operators o JOIN services s"
                  " ON s.operator_id = o.operator_id JOIN tickets t"
                  " ON t.service_id = s.service_id JOIN incidents i"
                  " ON i.service_id = s.service_id GROUP BY o.name"),
        note="Two sums over two children of the same parent. Joined"
             " together, a service with 4 tickets and 1 incident yields 4"
             " rows -- its delay counted four times -- and a service with"
             " tickets but no incident vanishes from the inner join"
             " altogether. Aggregate each child to the operator on its own,"
             " then join the two small results. COUNT(DISTINCT) rescues a"
             " count from this; nothing rescues a SUM.",
        claims=[("four operators, both totals matching their tables",
                 lambda rows, c: len(rows) == 4
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT SUM(price_pence) FROM tickets").fetchone()[0]
                 and sum(r[2] for r in rows) == c.execute(
                     "SELECT SUM(delay_minutes) FROM incidents").fetchone()[0])],
    ),
    dict(
        id=17, ledger="Q598", concept="N1", tier="5 - Joins and grain",
        title="Staff who manage nobody",
        prompt=(
            "Members of staff to whom nobody reports.\n\n"
            "The one person at the top reports to nobody -- reports_to is"
            " NULL there -- and that single row is enough to make one"
            " obvious phrasing return nothing at all.\n\n"
            "Return: staff_id, name"
        ),
        solution=("SELECT s.staff_id, s.name FROM staff s WHERE NOT EXISTS"
                  " (SELECT 1 FROM staff r WHERE r.reports_to = s.staff_id)"),
        trap_sql=("SELECT staff_id, name FROM staff WHERE staff_id NOT IN"
                  " (SELECT reports_to FROM staff)"),
        note="NOT IN (list) is 'not equal to every item', and 'not equal to"
             " NULL' is unknown -- so with one NULL in the list, no row can"
             " ever be true and the trap returns nothing. NOT EXISTS has no"
             " such hole: the subquery either finds a row or does not."
             " Filtering the NULL out of the subquery (WHERE reports_to IS"
             " NOT NULL) also works; the anti-join from question 17 of the"
             " last set is the third way.",
        claims=[("most of the staff, none of whom appears as a reports_to",
                 lambda rows, c: 20 < len(rows) < 40
                 and not c.execute(
                     "SELECT 1 FROM staff WHERE reports_to IN (%s) LIMIT 1"
                     % ",".join(str(int(r[0])) for r in rows)).fetchall())],
    ),
    dict(
        id=18, ledger="Q599", concept="E1", tier="5 - Joins and grain",
        title="Lost time at every stop",
        prompt=(
            "Services on 2025-01-10 that arrived later than scheduled at"
            " EVERY stop, with their number of stops.\n\n"
            "A stop with no recorded arrival is not a late one, so a"
            " service with an unrecorded stop does not qualify.\n\n"
            "Return: service_id, stops"
        ),
        solution=("SELECT sp.service_id, COUNT(*) FROM stops sp JOIN services s"
                  " ON s.service_id = sp.service_id"
                  " WHERE s.run_date = '2025-01-10' GROUP BY sp.service_id"
                  " HAVING COUNT(*) = SUM(sp.actual_arrive > sp.sched_arrive)"),
        trap_sql=("SELECT sp.service_id, COUNT(*) FROM stops sp JOIN services s"
                  " ON s.service_id = sp.service_id"
                  " WHERE s.run_date = '2025-01-10'"
                  " AND sp.actual_arrive > sp.sched_arrive"
                  " GROUP BY sp.service_id"),
        note="'Every stop' is a property of the group: the number of late"
             " stops equals the number of stops. The trap filters to late"
             " stops first and then counts them, which finds every service"
             " with at least ONE late stop -- and reports a stop count that"
             " is really a late-stop count. SUM of a comparison counts the"
             " rows where it is true; a NULL arrival compares as NULL and"
             " adds nothing, which is exactly the exclusion the question"
             " wants.",
        claims=[("a handful of services, each late at every stop",
                 lambda rows, c: 1 < len(rows) < 10 and all(
                     c.execute("SELECT COUNT(*) = SUM(actual_arrive"
                               " > sched_arrive) FROM stops WHERE service_id"
                               " = ?", (r[0],)).fetchone()[0] for r in rows))],
    ),
    # ================================================= 6 Window functions
    dict(
        id=19, ledger="Q600", concept="W1", tier="6 - Window functions",
        title="The week's tickets, rolling",
        prompt=(
            "For each day of January 2025: tickets sold that day, and the"
            " total over the seven days ending that day -- for the first"
            " six days, over as many days as there are.\n\n"
            "Return: day, tickets, seven_day_total"
        ),
        solution=("SELECT sold_at, COUNT(*), SUM(COUNT(*)) OVER (ORDER BY"
                  " sold_at ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)"
                  " FROM tickets WHERE sold_at < '2025-02-01' GROUP BY 1"),
        trap_sql=("SELECT sold_at, COUNT(*), SUM(COUNT(*)) OVER (ORDER BY"
                  " sold_at ROWS BETWEEN 7 PRECEDING AND CURRENT ROW)"
                  " FROM tickets WHERE sold_at < '2025-02-01' GROUP BY 1"),
        note="Seven days ending today is today plus the six before it, so"
             " the frame is 6 PRECEDING, not 7 -- an off-by-one that shows"
             " only from the eighth row on, where the trap's totals are one"
             " day too heavy. ROWS is safe here because every day sold"
             " tickets, so one row is one day; a day with no sales would"
             " need a RANGE frame or a date spine.",
        claims=[("31 days, the seventh total the sum of the first seven",
                 lambda rows, c: len(rows) == 31
                 and rows[6][2] == sum(r[1] for r in rows[:7])
                 and rows[7][2] == sum(r[1] for r in rows[1:8]))],
    ),
    dict(
        id=20, ledger="Q601", concept="W2", tier="6 - Window functions",
        title="Pay rank within the role",
        prompt=(
            "Every member of staff with their salary's rank within their"
            " ROLE -- 1 for the best paid -- and how many pounds behind that"
            " role's top salary they are.\n\n"
            "Return: staff_id, role, salary, rank_in_role, behind_top"
        ),
        solution=("SELECT staff_id, role, salary, RANK() OVER (PARTITION BY"
                  " role ORDER BY salary DESC), MAX(salary) OVER (PARTITION BY"
                  " role) - salary FROM staff"),
        trap_sql=("SELECT staff_id, role, salary, RANK() OVER (ORDER BY"
                  " salary DESC), MAX(salary) OVER () - salary FROM staff"),
        note="Two windows, both partitioned by role: a rank and an"
             " aggregate. Without PARTITION BY the rank runs across all"
             " forty people and the gap is to the best-paid person anywhere,"
             " so only one row in the company reads 1 and 0. An aggregate"
             " with OVER is not grouped -- every row keeps its own salary"
             " and gains the partition's maximum beside it.",
        claims=[("forty rows, one rank-1 per role, each 0 behind",
                 lambda rows, c: len(rows) == 40
                 and sum(1 for r in rows if r[3] == 1) == 4
                 and all(r[4] == 0 for r in rows if r[3] == 1))],
    ),
    dict(
        id=21, ledger="Q602", concept="W3", tier="6 - Window functions",
        title="Each kind's share of the line's delay",
        prompt=(
            "For every line and kind of incident: the quantified delay"
            " minutes, and what percentage of THAT LINE's delay minutes it"
            " is, to two decimals.\n\n"
            "Each line's five percentages add to 100.\n\n"
            "Return: line_id, kind, delay_minutes, pct_of_line"
        ),
        solution=("SELECT s.line_id, i.kind, SUM(i.delay_minutes),"
                  " ROUND(100.0 * SUM(i.delay_minutes) / SUM(SUM(i.delay_minutes))"
                  " OVER (PARTITION BY s.line_id), 2) FROM incidents i"
                  " JOIN services s ON s.service_id = i.service_id"
                  " GROUP BY 1, 2"),
        trap_sql=("SELECT s.line_id, i.kind, SUM(i.delay_minutes),"
                  " ROUND(100.0 * SUM(i.delay_minutes) / SUM(SUM(i.delay_minutes))"
                  " OVER (), 2) FROM incidents i"
                  " JOIN services s ON s.service_id = i.service_id"
                  " GROUP BY 1, 2"),
        note="SUM(SUM(x)) OVER (PARTITION BY line) adds up the grouped sums"
             " within one line, which is the denominator a share OF THE LINE"
             " needs. OVER () with no partition is the network total, and"
             " the trap's thirty percentages add to 100 once, across"
             " everything, instead of six times. Incidents with no quantified"
             " delay contribute nothing to either sum.",
        claims=[("thirty rows, each line's shares summing to 100",
                 lambda rows, c: len(rows) == 30 and all(
                     abs(sum(r[3] for r in rows if r[0] == lid) - 100) < 0.05
                     for lid in {r[0] for r in rows}))],
    ),
    dict(
        id=22, ledger="Q603", concept="W2", tier="6 - Window functions",
        title="The three latest incidents on each line",
        prompt=(
            "For each line, its three most recently reported incidents."
            " Eighteen rows. When two were reported on the same day, the"
            " higher incident_id is the more recent.\n\n"
            "Return: line_id, incident_id, reported_at"
        ),
        solution=("SELECT line_id, incident_id, reported_at FROM (SELECT"
                  " s.line_id, i.incident_id, i.reported_at, ROW_NUMBER() OVER"
                  " (PARTITION BY s.line_id ORDER BY i.reported_at DESC,"
                  " i.incident_id DESC) rn FROM incidents i JOIN services s"
                  " ON s.service_id = i.service_id) WHERE rn <= 3"),
        trap_sql=("SELECT line_id, incident_id, reported_at FROM (SELECT"
                  " s.line_id, i.incident_id, i.reported_at, ROW_NUMBER() OVER"
                  " (PARTITION BY s.line_id ORDER BY i.reported_at,"
                  " i.incident_id DESC) rn FROM incidents i JOIN services s"
                  " ON s.service_id = i.service_id) WHERE rn <= 3"),
        note="Top-N per group again, and the ORDER BY inside OVER decides"
             " which end 'top' is: DESC for the latest. The trap numbers"
             " from the oldest, so it returns the three EARLIEST incidents"
             " per line with perfect confidence. Two sort keys, both"
             " descending, because several incidents share a date and the"
             " tiebreak is part of the question.",
        claims=[("three per line, none older than the line's fourth-latest",
                 lambda rows, c: len(rows) == 18 and all(
                     sum(1 for r in rows if r[0] == lid) == 3
                     for lid in {r[0] for r in rows}))],
    ),
    # ================================================ 7 Changing the data
    # Writable questions. The editor's script runs in a sandbox copy of the
    # database, then probe_sql reads the result and THAT is compared with the
    # reference. driver_sql, where present, is run by the question after the
    # script -- to fire a trigger, or to be refused by one.
    dict(
        id=23, ledger="Q604", concept="DML", tier="7 - Changing the data",
        kind="script",
        title="Footfall for stations nobody calls at",
        prompt=(
            "Some stations are on no line's route, yet they have footfall"
            " rows. Delete the footfall rows of every station that no service"
            " has ever called at. 21 rows go, for 7 stations.\n\n"
            "One DELETE, with a subquery that finds the stations.\n\n"
            "Checked: how many footfall rows remain, and for how many"
            " stations"
        ),
        solution=("DELETE FROM station_footfall\n"
                  "WHERE station_id NOT IN (SELECT station_id FROM stops);"),
        trap_sql=("DELETE FROM station_footfall\n"
                  "WHERE station_id NOT IN\n"
                  "      (SELECT station_id FROM stops WHERE stop_seq = 1);"),
        probe_sql=("SELECT COUNT(*), COUNT(DISTINCT station_id)"
                   " FROM station_footfall"),
        note="A DELETE takes the same WHERE a SELECT would, so write the"
             " SELECT first and look at what it returns -- the trap's"
             " subquery finds stations no service STARTS at, which is nearly"
             " all of them, and 162 rows go. NOT IN is safe here because"
             " stops.station_id is NOT NULL; against a column that allows"
             " NULL it would delete nothing, silently, for the reason"
             " question 17 gives.",
        claims=[("three rows per remaining station, all of them called at",
                 lambda rows, c: rows[0][0] == 3 * rows[0][1]
                 and rows[0][1] == c.execute(
                     "SELECT COUNT(DISTINCT station_id) FROM stops"
                 ).fetchone()[0])],
    ),
    dict(
        id=24, ledger="Q605", concept="DML", tier="7 - Changing the data",
        kind="script",
        title="Fill in the unquantified delays",
        prompt=(
            "174 incidents have no delay_minutes. Fill each one in with the"
            " average delay of the quantified incidents of the SAME kind,"
            " rounded to a whole minute.\n\n"
            "One UPDATE, with a subquery that depends on the row being"
            " updated.\n\n"
            "Checked: total delay minutes and how many incidents are"
            " quantified, per kind"
        ),
        solution=("UPDATE incidents\n"
                  "SET delay_minutes = (SELECT ROUND(AVG(i2.delay_minutes))\n"
                  "                     FROM incidents i2\n"
                  "                     WHERE i2.kind = incidents.kind)\n"
                  "WHERE delay_minutes IS NULL;"),
        trap_sql=("UPDATE incidents\n"
                  "SET delay_minutes = (SELECT ROUND(AVG(delay_minutes))\n"
                  "                     FROM incidents)\n"
                  "WHERE delay_minutes IS NULL;"),
        probe_sql=("SELECT kind, SUM(delay_minutes), COUNT(delay_minutes)"
                   " FROM incidents GROUP BY 1 ORDER BY 1"),
        note="A correlated subquery in SET: the outer table is named without"
             " an alias, so `incidents.kind` inside refers to the row being"
             " updated. AVG skips NULLs, so the unquantified rows do not"
             " drag the average down. The trap fills every kind with one"
             " network-wide figure -- off by a minute or two per row, a"
             " hundred rows at a time. UPDATE ... FROM a grouped subquery"
             " says the same thing with the read done first; both give the"
             " same rows here.",
        claims=[("every kind fully quantified",
                 lambda rows, c: len(rows) == 5 and all(
                     r[2] == c.execute("SELECT COUNT(*) FROM incidents"
                                       " WHERE kind = ?", (r[0],)).fetchone()[0]
                     for r in rows))],
    ),
    dict(
        id=25, ledger="Q606", concept="INS", tier="7 - Changing the data",
        kind="script",
        title="Next year's budget",
        prompt=(
            "Give every station a 2026 footfall row in which each quarter is"
            " its 2025 figure up 10%, rounded to a whole number. Sixty new"
            " rows from one INSERT ... SELECT.\n\n"
            "The quarter columns are INTEGER. What you insert should be"
            " stored as integers, not as 25801.6.\n\n"
            "Checked: per year, the rows, the total footfall, and how many"
            " q1 values are stored as integers"
        ),
        solution=("INSERT INTO station_footfall (station_id, year, q1, q2, q3, q4)\n"
                  "SELECT station_id, 2026, ROUND(q1 * 1.1), ROUND(q2 * 1.1),\n"
                  "       ROUND(q3 * 1.1), ROUND(q4 * 1.1)\n"
                  "FROM station_footfall\n"
                  "WHERE year = 2025;"),
        trap_sql=("INSERT INTO station_footfall (station_id, year, q1, q2, q3, q4)\n"
                  "SELECT station_id, 2026, q1 * 1.1, q2 * 1.1, q3 * 1.1, q4 * 1.1\n"
                  "FROM station_footfall\n"
                  "WHERE year = 2025;"),
        probe_sql=("SELECT year, COUNT(*), SUM(q1 + q2 + q3 + q4),"
                   " SUM(typeof(q1) = 'integer') FROM station_footfall"
                   " GROUP BY 1 ORDER BY 1"),
        note="INSERT ... SELECT copies rows through a query, and the query"
             " may compute anything. The twist is type AFFINITY: an INTEGER"
             " column accepts a REAL, and stores it as a REAL unless the"
             " value happens to be whole. ROUND returns 25802.0, which is"
             " whole, so it lands as the integer 25802; the trap's 25801.6"
             " stays a REAL in an 'integer' column, and typeof() says so."
             " SQLite will not refuse it -- that is the lesson.",
        claims=[("sixty 2026 rows, all integers, ten percent up",
                 lambda rows, c: [r[0] for r in rows] == [2023, 2024, 2025, 2026]
                 and rows[3][1] == 60 and rows[3][3] == 60
                 and abs(rows[3][2] - 1.1 * rows[2][2]) < 60)],
    ),
    dict(
        id=26, ledger="Q607", concept="TXN", tier="7 - Changing the data",
        kind="script",
        title="Two savepoints, one raise",
        prompt=(
            "In one transaction: give every guard a 2% raise; set a"
            " savepoint; give every dispatcher 2%; set a second savepoint;"
            " give every manager 2%; RELEASE the second savepoint; roll back"
            " to the first; commit.\n\n"
            "Whole pounds: CAST(ROUND(salary * 1.02) AS INTEGER). Only the"
            " guards' raise should survive -- releasing a savepoint does not"
            " commit what came after it.\n\n"
            "Checked: total salary by role"
        ),
        solution=("BEGIN;\n"
                  "UPDATE staff SET salary = CAST(ROUND(salary * 1.02) AS INTEGER)"
                  " WHERE role = 'guard';\n"
                  "SAVEPOINT office;\n"
                  "UPDATE staff SET salary = CAST(ROUND(salary * 1.02) AS INTEGER)"
                  " WHERE role = 'dispatcher';\n"
                  "SAVEPOINT top;\n"
                  "UPDATE staff SET salary = CAST(ROUND(salary * 1.02) AS INTEGER)"
                  " WHERE role = 'manager';\n"
                  "RELEASE top;\n"
                  "ROLLBACK TO office;\n"
                  "COMMIT;"),
        trap_sql=("BEGIN;\n"
                  "UPDATE staff SET salary = CAST(ROUND(salary * 1.02) AS INTEGER)"
                  " WHERE role = 'guard';\n"
                  "SAVEPOINT office;\n"
                  "UPDATE staff SET salary = CAST(ROUND(salary * 1.02) AS INTEGER)"
                  " WHERE role = 'dispatcher';\n"
                  "SAVEPOINT top;\n"
                  "UPDATE staff SET salary = CAST(ROUND(salary * 1.02) AS INTEGER)"
                  " WHERE role = 'manager';\n"
                  "RELEASE top;\n"
                  "RELEASE office;\n"
                  "COMMIT;"),
        probe_sql="SELECT role, SUM(salary) FROM staff GROUP BY 1",
        note="Savepoints nest. RELEASE top merges the managers' raise into"
             " the enclosing savepoint -- it does not commit anything -- so"
             " ROLLBACK TO office then undoes the managers' raise along with"
             " the dispatchers'. The trap releases both, which keeps all"
             " three; only COMMIT makes anything permanent. This is the"
             " point where T-SQL's SAVE TRANSACTION differs least and"
             " confuses most: there, too, a savepoint is a mark, not a"
             " commit.",
        claims=[("guards up two percent, the other roles untouched",
                 lambda rows, c: dict(rows) == {'guard': 494428,
                                                'dispatcher': 767816,
                                                'driver': 556221,
                                                'manager': 274668})],
    ),
    dict(
        id=27, ledger="Q608", concept="TRG", tier="7 - Changing the data",
        kind="script",
        title="A view you can insert through",
        prompt=(
            "Create a view `open_returns` over `tickets` -- ticket_id,"
            " service_id, from_station, class, price_pence, sold_at -- for"
            " tickets with no destination. Then make it writable: a trigger"
            " so that an INSERT into the view lands in `tickets` with"
            " to_station NULL.\n\n"
            "After your script, the question inserts one ticket through the"
            " view: service 1, from station 25, 'standard', 1200 pence, sold"
            " 2025-01-01.\n\n"
            "Checked: how many open returns there are, and the newest"
            " ticket's destination, price and class"
        ),
        solution=("CREATE VIEW open_returns AS\n"
                  "SELECT ticket_id, service_id, from_station, class, price_pence, sold_at\n"
                  "FROM tickets\n"
                  "WHERE to_station IS NULL;\n"
                  "CREATE TRIGGER open_returns_insert\n"
                  "INSTEAD OF INSERT ON open_returns\n"
                  "BEGIN\n"
                  "  INSERT INTO tickets (service_id, from_station, to_station,"
                  " class, price_pence, sold_at)\n"
                  "  VALUES (NEW.service_id, NEW.from_station, NULL,"
                  " NEW.class, NEW.price_pence, NEW.sold_at);\n"
                  "END;"),
        trap_sql=("CREATE VIEW open_returns AS\n"
                  "SELECT ticket_id, service_id, from_station, class, price_pence, sold_at\n"
                  "FROM tickets\n"
                  "WHERE to_station IS NULL;\n"
                  "CREATE TRIGGER open_returns_insert\n"
                  "BEFORE INSERT ON open_returns\n"
                  "BEGIN\n"
                  "  INSERT INTO tickets (service_id, from_station, to_station,"
                  " class, price_pence, sold_at)\n"
                  "  VALUES (NEW.service_id, NEW.from_station, NULL,"
                  " NEW.class, NEW.price_pence, NEW.sold_at);\n"
                  "END;"),
        driver_sql=("INSERT INTO open_returns (service_id, from_station, class,"
                    " price_pence, sold_at)"
                    " VALUES (1, 25, 'standard', 1200, '2025-01-01');"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM open_returns), to_station,"
                   " price_pence, class FROM tickets"
                   " ORDER BY ticket_id DESC LIMIT 1"),
        note="A view has no rows of its own, so an INSERT into one has"
             " nowhere to go -- unless an INSTEAD OF trigger says where."
             " That is the only kind of trigger a view accepts: BEFORE and"
             " AFTER are for tables, and the trap is refused at CREATE"
             " TRIGGER. NEW holds the row as it was written to the view, so"
             " the trigger reshapes it for the base table; the column the"
             " view hides is supplied here. This is how an updatable view is"
             " built in SQLite, and in Postgres.",
        claims=[("one more open return, with no destination",
                 lambda rows, c: rows[0][1] is None and rows[0][2] == 1200
                 and rows[0][0] == c.execute(
                     "SELECT COUNT(*) FROM tickets WHERE to_station IS NULL"
                 ).fetchone()[0])],
    ),
    dict(
        id=28, ledger="Q609", concept="TRG", tier="7 - Changing the data",
        kind="script",
        title="A recycle bin for incidents",
        prompt=(
            "Create a table `incidents_bin` with the same five columns as"
            " `incidents`, and a trigger so that every incident deleted from"
            " `incidents` is copied into it first.\n\n"
            "After your script, the question deletes the three incidents"
            " reported on 2025-01-02.\n\n"
            "Checked: that none of those three remain, and what the bin"
            " holds"
        ),
        solution=("CREATE TABLE incidents_bin (incident_id INTEGER, service_id INTEGER,\n"
                  "                            reported_at TEXT, kind TEXT,"
                  " delay_minutes INTEGER);\n"
                  "CREATE TRIGGER bin_incident\n"
                  "AFTER DELETE ON incidents\n"
                  "BEGIN\n"
                  "  INSERT INTO incidents_bin\n"
                  "  VALUES (OLD.incident_id, OLD.service_id, OLD.reported_at,"
                  " OLD.kind, OLD.delay_minutes);\n"
                  "END;"),
        trap_sql=("CREATE TABLE incidents_bin (incident_id INTEGER, service_id INTEGER,\n"
                  "                            reported_at TEXT, kind TEXT,"
                  " delay_minutes INTEGER);\n"
                  "CREATE TRIGGER bin_incident\n"
                  "AFTER UPDATE ON incidents\n"
                  "BEGIN\n"
                  "  INSERT INTO incidents_bin\n"
                  "  VALUES (OLD.incident_id, OLD.service_id, OLD.reported_at,"
                  " OLD.kind, OLD.delay_minutes);\n"
                  "END;"),
        driver_sql="DELETE FROM incidents WHERE reported_at = '2025-01-02';",
        probe_sql=("SELECT (SELECT COUNT(*) FROM incidents"
                   " WHERE reported_at = '2025-01-02'), incident_id, kind,"
                   " delay_minutes FROM incidents_bin ORDER BY incident_id"),
        note="A DELETE trigger sees only OLD -- there is no NEW row, and"
             " naming one is an error. The trigger fires once per deleted"
             " row, so a DELETE of three rows makes three inserts. The trap"
             " watches the wrong event and never fires, so the bin stays"
             " empty and the rows are simply gone. A NULL delay_minutes"
             " copies across as NULL; the bin's columns allow it because"
             " nothing said otherwise.",
        claims=[("three incidents binned, none left in the table",
                 lambda rows, c: len(rows) == 3
                 and all(r[0] == 0 for r in rows))],
    ),
    dict(
        id=29, ledger="Q610", concept="VIEW", tier="7 - Changing the data",
        kind="script",
        title="A view of lateness",
        prompt=(
            "Create a view `late_stops (service_id, stop_seq, station_id,"
            " late_minutes)`: each recorded arrival's lateness in whole"
            " minutes, actual minus scheduled.\n\n"
            "Stops with no recorded arrival must not appear in it at all --"
            " a NULL lateness is not a lateness. Just under five thousand"
            " stops are like that.\n\n"
            "Checked: COUNT(*), SUM, MIN and MAX of late_minutes over the"
            " view"
        ),
        solution=("CREATE VIEW late_stops AS\n"
                  "SELECT service_id, stop_seq, station_id,\n"
                  "       (strftime('%s', actual_arrive) - strftime('%s', sched_arrive))"
                  " / 60 AS late_minutes\n"
                  "FROM stops\n"
                  "WHERE actual_arrive IS NOT NULL;"),
        trap_sql=("CREATE VIEW late_stops AS\n"
                  "SELECT service_id, stop_seq, station_id,\n"
                  "       (strftime('%s', actual_arrive) - strftime('%s', sched_arrive))"
                  " / 60 AS late_minutes\n"
                  "FROM stops;"),
        probe_sql=("SELECT COUNT(*), SUM(late_minutes), MIN(late_minutes),"
                   " MAX(late_minutes) FROM late_stops"),
        note="A view with a computed column: whoever selects from it gets"
             " the arithmetic done. The trap's SUM, MIN and MAX are"
             " identical -- aggregates skip NULL -- and only COUNT(*) gives"
             " it away, by counting 4,725 rows of NULL lateness as rows."
             " The filter belongs in the view, because every user of it"
             " would otherwise have to remember it. Name the column with AS"
             " or the view's callers get a formula for a heading.",
        claims=[("one row per recorded arrival, lateness a few minutes either way",
                 lambda rows, c: rows[0][0] == c.execute(
                     "SELECT COUNT(*) FROM stops WHERE actual_arrive"
                     " IS NOT NULL").fetchone()[0]
                 and -5 < rows[0][2] < 0 < rows[0][3] < 15)],
    ),
    dict(
        id=30, ledger="Q611", concept="ALT", tier="7 - Changing the data",
        kind="script",
        title="Reshape the fleet table",
        prompt=(
            "Three ALTER TABLE statements on `rolling_stock`: rename `seats`"
            " to `seat_count`; add `in_service INTEGER NOT NULL`, which must"
            " be 1 for every existing unit; drop `refurbished_year`.\n\n"
            "A NOT NULL column added to a table that already has rows needs"
            " something to put in them.\n\n"
            "Checked: unit_id, seat_count and in_service for units 1 to 3,"
            " and how many columns the table has"
        ),
        solution=("ALTER TABLE rolling_stock RENAME COLUMN seats TO seat_count;\n"
                  "ALTER TABLE rolling_stock ADD COLUMN in_service INTEGER"
                  " NOT NULL DEFAULT 1;\n"
                  "ALTER TABLE rolling_stock DROP COLUMN refurbished_year;"),
        trap_sql=("ALTER TABLE rolling_stock RENAME COLUMN seats TO seat_count;\n"
                  "ALTER TABLE rolling_stock ADD COLUMN in_service INTEGER"
                  " NOT NULL;\n"
                  "ALTER TABLE rolling_stock DROP COLUMN refurbished_year;"),
        probe_sql=("SELECT unit_id, seat_count, in_service,"
                   " (SELECT COUNT(*) FROM pragma_table_info('rolling_stock'))"
                   " FROM rolling_stock WHERE unit_id <= 3"),
        note="SQLite's ALTER TABLE does four things -- rename table, rename"
             " column, add column, drop column -- and nothing else; changing"
             " a type or a constraint means rebuilding the table. ADD COLUMN"
             " with NOT NULL is refused unless there is a non-NULL DEFAULT,"
             " because the existing rows would violate it at once; the trap"
             " stops at the second statement, with the rename already done."
             " DROP COLUMN (3.35+) refuses columns an index, constraint or"
             " generated column depends on -- none here.",
        claims=[("three units, all in service, five columns",
                 lambda rows, c: rows == [(1, 300, 1, 5), (2, 200, 1, 5),
                                          (3, 200, 1, 5)])],
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
