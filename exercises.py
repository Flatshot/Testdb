"""Practice exercises: thirty questions on the railway schema.

Twenty of these are shapes you have worked before -- grain, frames, set
operations, dates, anti-joins -- against a re-seeded database. The other ten
are mechanisms that have not appeared in any previous set:

  * GAPS AND ISLANDS (16, 24) -- collapsing consecutive dates into runs by
    subtracting a row number, so a streak becomes a group you can aggregate
  * A DATE SPINE (11, 12) -- generating the calendar with a recursive CTE and
    joining data onto it, so days with nothing to report appear as 0 rather
    than going missing
  * PIVOT (8, 9) -- turning rows into columns with conditional aggregation,
    and the FILTER clause that does the same thing more legibly
  * NAMED WINDOWS (23) -- defining a window once in a WINDOW clause and using
    it from several functions
  * RANGE FRAMES (21) and EXCLUDE (22) -- frames measured in VALUES rather
    than rows, and the four ways to drop the current row's peers
  * A MEDIAN (25) -- SQLite has no median function, so it falls out of
    ROW_NUMBER and COUNT, including the even-sized case

The efficiency stage keeps its four multi-table plan puzzles, on four
mechanisms none of the previous sets used:

  27  an aggregate subquery correlated to the row, so it runs 30,000 times
  28  a correlation added to an IN subquery that did not need one
  29  a TEXT date compared as though it were a number
  30  a join that does not fan out, but does cost the covering index

27 deliberately reverses Q491, where pulling an aggregate into a CTE was the
mistake. What matters is whether the outer query can narrow it.
"""

EXERCISES = [
    # ========================================================== 1 Warm-up
    dict(
        id=1, ledger="Q522", concept="A2", tier="1 - Warm-up",
        title="How full the trains are",
        prompt=(
            "One row per model of rolling stock: how many units, the smallest"
            " and largest seat count, and the average.\n\n"
            "Round the average to one decimal.\n\n"
            "Return: model, units, fewest, most, avg_seats"
        ),
        solution=("SELECT model, COUNT(*), MIN(seats), MAX(seats),"
                  " ROUND(AVG(seats), 1) FROM rolling_stock GROUP BY 1"),
        trap_sql=("SELECT model, COUNT(*), MIN(seats), MAX(seats),"
                  " ROUND(AVG(seats)) FROM rolling_stock GROUP BY 1"),
        note="ROUND with one argument rounds to a whole number, which is not"
             " the same as rounding to one decimal and happens to look"
             " plausible either way. The second argument is the number of"
             " decimal places you want.",
        claims=[("several models, and at least one average with a decimal",
                 lambda rows, c: len(rows) > 3
                 and any(r[4] != int(r[4]) for r in rows))],
    ),
    dict(
        id=2, ledger="Q523", concept="C1", tier="1 - Warm-up",
        title="Busy roles",
        prompt=(
            "Roles with more than five staff, and their average salary to the"
            " nearest pound.\n\n"
            "The condition is about the role as a whole, not about any one"
            " person.\n\n"
            "Return: role, staff, avg_salary"
        ),
        solution=("SELECT role, COUNT(*), ROUND(AVG(salary)) FROM staff"
                  " GROUP BY role HAVING COUNT(*) > 5"),
        trap_sql=("SELECT role, COUNT(*), ROUND(AVG(salary)) FROM staff"
                  " WHERE salary > 5 GROUP BY role"),
        note="WHERE filters rows before they are grouped; HAVING filters the"
             " groups afterwards. A condition on COUNT(*) cannot go in WHERE"
             " because at that point there is no group to count -- each row is"
             " still just a row. The order to hold in your head is FROM,"
             " WHERE, GROUP BY, HAVING, SELECT, ORDER BY.",
        claims=[("every role returned has more than five staff",
                 lambda rows, c: len(rows) > 0 and all(r[1] > 5 for r in rows))],
    ),
    dict(
        id=3, ledger="Q524", concept="N1", tier="1 - Warm-up",
        title="Revenue by class in pounds",
        prompt=(
            "One row per class: how many tickets and the total revenue in"
            " POUNDS, to two decimals.\n\n"
            "price_pence holds whole pence.\n\n"
            "Return: class, tickets, revenue"
        ),
        solution=("SELECT class, COUNT(*), ROUND(SUM(price_pence) / 100.0, 2)"
                  " FROM tickets GROUP BY 1"),
        trap_sql=("SELECT class, COUNT(*), ROUND(SUM(price_pence) / 100, 2)"
                  " FROM tickets GROUP BY 1"),
        note="SUM(price_pence) is an integer and 100 is an integer, so / 100"
             " is integer division: the pence are discarded before ROUND ever"
             " sees them, and asking for two decimals of a whole number gives"
             " you the whole number back. Writing 100.0 makes one side a float"
             " and the rest follows. Money kept as an integer is exact right"
             " up to the moment you divide it.",
        claims=[("three classes, revenue in the thousands",
                 lambda rows, c: len(rows) == 3
                 and all(r[2] > 1000 for r in rows))],
    ),
    # ========================================== 2 Sequences and strings
    dict(
        id=4, ledger="Q525", concept="W3", tier="2 - Sequences and strings",
        title="How long between stops",
        prompt=(
            "For service 200, the gap in minutes between each stop's"
            " scheduled arrival and the one before it.\n\n"
            "Stop 1 has no predecessor, so report NULL for it.\n\n"
            "Return: stop_seq, gap_minutes"
        ),
        solution=("SELECT stop_seq, (strftime('%s', sched_arrive)"
                  " - strftime('%s', LAG(sched_arrive) OVER"
                  " (ORDER BY stop_seq))) / 60 FROM stops"
                  " WHERE service_id = 200"),
        trap_sql=("SELECT stop_seq, (strftime('%s', sched_arrive)"
                  " - strftime('%s', LAG(sched_arrive) OVER"
                  " (ORDER BY stop_seq))) / 3600 FROM stops"
                  " WHERE service_id = 200"),
        note="strftime('%s', x) gives seconds since 1970, so a difference of"
             " two of them is seconds: divide by 60 for minutes, not 3600."
             " Integer division makes the trap worse than a wrong unit -- every"
             " gap under an hour truncates to 0, so the column is all zeros"
             " rather than obviously-wrong numbers.",
        claims=[("the first gap is NULL and the rest are positive",
                 lambda rows, c: rows[0][1] is None
                 and all(r[1] > 0 for r in rows[1:]))],
    ),
    dict(
        id=5, ledger="Q526", concept="STR", tier="2 - Sequences and strings",
        title="The calling pattern, backwards",
        prompt=(
            "For service 200, its stations as one string in REVERSE calling"
            " order -- terminus first -- joined with ' > '.\n\n"
            "One row, one column.\n\n"
            "Return: pattern"
        ),
        solution=("SELECT GROUP_CONCAT(st.name, ' > '"
                  " ORDER BY sp.stop_seq DESC)"
                  " FROM stops sp JOIN stations st"
                  " ON st.station_id = sp.station_id"
                  " WHERE sp.service_id = 200"),
        trap_sql=("SELECT GROUP_CONCAT(st.name, ' > ')"
                  " FROM stops sp JOIN stations st"
                  " ON st.station_id = sp.station_id"
                  " WHERE sp.service_id = 200 ORDER BY sp.stop_seq"),
        note="GROUP_CONCAT promises nothing about the order it concatenates"
             " in, and a trailing ORDER BY cannot fix it -- that sorts the ONE"
             " row the aggregate returns, long after the string was built. The"
             " ordering goes inside the call, after the separator. Ask for"
             " forward order and the trap looks right, because the rows happen"
             " to arrive in stop_seq order; ask for reverse and the luck runs"
             " out. Relying on arrival order is relying on the current query"
             " plan.",
        claims=[("one row with the right number of separators",
                 lambda rows, c: len(rows) == 1
                 and rows[0][0].count(" > ") == c.execute(
                     "SELECT COUNT(*) - 1 FROM stops WHERE service_id = 200"
                 ).fetchone()[0])],
    ),
    dict(
        id=6, ledger="Q527", concept="W2", tier="2 - Sequences and strings",
        title="Where each service came from",
        prompt=(
            "Take the lowest-numbered service on each line -- six services."
            " For every stop of those six, give the station that service"
            " started from, repeated on each of its rows.\n\n"
            "Return: service_id, stop_seq, origin"
        ),
        solution=("SELECT sp.service_id, sp.stop_seq, FIRST_VALUE(st.name)"
                  " OVER (PARTITION BY sp.service_id ORDER BY sp.stop_seq)"
                  " FROM stops sp"
                  " JOIN stations st ON st.station_id = sp.station_id"
                  " WHERE sp.service_id IN (SELECT MIN(service_id)"
                  " FROM services GROUP BY line_id)"),
        trap_sql=("SELECT sp.service_id, sp.stop_seq, LAST_VALUE(st.name)"
                  " OVER (PARTITION BY sp.service_id ORDER BY sp.stop_seq)"
                  " FROM stops sp"
                  " JOIN stations st ON st.station_id = sp.station_id"
                  " WHERE sp.service_id IN (SELECT MIN(service_id)"
                  " FROM services GROUP BY line_id)"),
        note="FIRST_VALUE needs no frame, because the default frame starts at"
             " the beginning of the partition -- exactly where the first value"
             " lives. LAST_VALUE with the same default returns the CURRENT"
             " row, since the default frame ends there. That asymmetry is the"
             " whole reason LAST_VALUE has a reputation for being broken.",
        claims=[("six services, one origin each",
                 lambda rows, c: len({r[0] for r in rows}) == 6
                 and all(len({x[2] for x in rows if x[0] == sid}) == 1
                         for sid in {r[0] for r in rows}))],
    ),
    dict(
        id=7, ledger="Q528", concept="S1", tier="2 - Sequences and strings",
        title="Models both lines use",
        prompt=(
            "Models of rolling stock that have worked on line 1 AND on line 6."
            "\n\nFour of the seven models qualify.\n\n"
            "Return: model"
        ),
        solution=("SELECT r.model FROM service_units su"
                  " JOIN rolling_stock r ON r.unit_id = su.unit_id"
                  " JOIN services s ON s.service_id = su.service_id"
                  " WHERE s.line_id = 1"
                  " INTERSECT SELECT r.model FROM service_units su"
                  " JOIN rolling_stock r ON r.unit_id = su.unit_id"
                  " JOIN services s ON s.service_id = su.service_id"
                  " WHERE s.line_id = 6"),
        trap_sql=("SELECT DISTINCT r.model FROM service_units su"
                  " JOIN rolling_stock r ON r.unit_id = su.unit_id"
                  " JOIN services s ON s.service_id = su.service_id"
                  " WHERE s.line_id = 1 OR s.line_id = 6"),
        note="'Both' is not 'either'. A WHERE clause sees one row at a time"
             " and one row belongs to one line, so no row can satisfy both"
             " conditions -- OR quietly answers the other question and returns"
             " all seven of them. INTERSECT compares two whole result sets, which is"
             " the level 'both' operates at. GROUP BY model HAVING"
             " COUNT(DISTINCT line_id) = 2 says the same thing, and scales"
             " better to 'all six lines'.",
        claims=[("four models, fewer than the seven that exist",
                 lambda rows, c: len(rows) == 4
                 and len(rows) < c.execute(
                     "SELECT COUNT(DISTINCT model)"
                     " FROM rolling_stock").fetchone()[0])],
    ),
    # ================================================ 3 Pivot and set ops
    dict(
        id=8, ledger="Q529", concept="PIV", tier="3 - Pivot and set ops",
        title="Classes across the top",
        prompt=(
            "One row per line with THREE columns of counts -- advance, first"
            " and standard -- rather than three rows per line.\n\n"
            "This is the reverse of unpivoting: values that were rows in the"
            " `class` column become columns of their own. Six rows.\n\n"
            "Return: line_name, advance, first, standard"
        ),
        solution=("SELECT l.name,"
                  " SUM(CASE WHEN t.class = 'advance' THEN 1 ELSE 0 END),"
                  " SUM(CASE WHEN t.class = 'first' THEN 1 ELSE 0 END),"
                  " SUM(CASE WHEN t.class = 'standard' THEN 1 ELSE 0 END)"
                  " FROM lines l JOIN services s ON s.line_id = l.line_id"
                  " JOIN tickets t ON t.service_id = s.service_id"
                  " GROUP BY l.name"),
        trap_sql=("SELECT l.name,"
                  " COUNT(CASE WHEN t.class = 'advance' THEN 1 ELSE 0 END),"
                  " COUNT(CASE WHEN t.class = 'first' THEN 1 ELSE 0 END),"
                  " COUNT(CASE WHEN t.class = 'standard' THEN 1 ELSE 0 END)"
                  " FROM lines l JOIN services s ON s.line_id = l.line_id"
                  " JOIN tickets t ON t.service_id = s.service_id"
                  " GROUP BY l.name"),
        note="SQLite has no PIVOT keyword; you write it as one conditional"
             " aggregate per column. The pairing matters: SUM with"
             " 'THEN 1 ELSE 0' adds one for the matches and nothing for the"
             " rest, while COUNT with the same CASE counts every row -- because"
             " COUNT counts non-NULL values and 0 is not NULL, so all three"
             " columns come back identical. If you want COUNT, drop the ELSE"
             " so non-matches become NULL: COUNT(CASE WHEN c THEN 1 END).",
        claims=[("six lines, the three columns summing to every ticket",
                 lambda rows, c: len(rows) == 6
                 and sum(r[1] + r[2] + r[3] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM tickets").fetchone()[0]
                 and any(r[1] != r[2] for r in rows))],
    ),
    dict(
        id=9, ledger="Q530", concept="FIL", tier="3 - Pivot and set ops",
        title="Filtered aggregates",
        prompt=(
            "One row per line: how many DISTINCT services sold at least one"
            " first-class ticket, and how many sold any ticket at all.\n\n"
            "Both are counts of distinct services over the same joined rows,"
            " differing only in which rows each one is allowed to see. SQLite"
            " has a clause for exactly that.\n\n"
            "Return: line_name, services_with_first, services_selling"
        ),
        solution=("SELECT l.name,"
                  " COUNT(DISTINCT t.service_id) FILTER"
                  " (WHERE t.class = 'first'), COUNT(DISTINCT t.service_id)"
                  " FROM lines l JOIN services s ON s.line_id = l.line_id"
                  " JOIN tickets t ON t.service_id = s.service_id"
                  " GROUP BY l.name"),
        trap_sql=("SELECT l.name,"
                  " COUNT(DISTINCT t.service_id) FILTER"
                  " (WHERE t.class = 'first'), COUNT(t.service_id)"
                  " FROM lines l JOIN services s ON s.line_id = l.line_id"
                  " JOIN tickets t ON t.service_id = s.service_id"
                  " GROUP BY l.name"),
        note="FILTER (WHERE ...) restricts one aggregate to the rows matching"
             " its condition, leaving every other aggregate in the SELECT list"
             " untouched. It is the readable form of the CASE trick in"
             " question 8 -- and unlike CASE it composes with DISTINCT without"
             " nesting, which is why this question asks for a distinct count."
             " Postgres has it too; SQL Server does not, and there you are"
             " back to CASE.",
        claims=[("six lines, first-class services never exceeding the total",
                 lambda rows, c: len(rows) == 6
                 and all(0 < r[1] < r[2] for r in rows))],
    ),
    dict(
        id=10, ledger="Q531", concept="S1", tier="3 - Pivot and set ops",
        title="Units line 1 keeps to itself",
        prompt=(
            "Units that have worked on line 1 but never on line 2.\n\n"
            "Seven units qualify.\n\n"
            "Return: unit_id"
        ),
        solution=("SELECT su.unit_id FROM service_units su"
                  " JOIN services s ON s.service_id = su.service_id"
                  " WHERE s.line_id = 1"
                  " EXCEPT SELECT su.unit_id FROM service_units su"
                  " JOIN services s ON s.service_id = su.service_id"
                  " WHERE s.line_id = 2"),
        trap_sql=("SELECT su.unit_id FROM service_units su"
                  " JOIN services s ON s.service_id = su.service_id"
                  " WHERE s.line_id = 2"
                  " EXCEPT SELECT su.unit_id FROM service_units su"
                  " JOIN services s ON s.service_id = su.service_id"
                  " WHERE s.line_id = 1"),
        note="EXCEPT is directional: A EXCEPT B is what is in A and not in B,"
             " and swapping the operands asks a different question that is"
             " just as valid-looking. INTERSECT and UNION read the same both"
             " ways, so there is no habit to fall back on -- the check is to"
             " name which side you want KEPT before you write it. EXCEPT also"
             " removes duplicates for you, so a DISTINCT on either side is"
             " decoration.",
        claims=[("seven units, none of which has worked line 2",
                 lambda rows, c: len(rows) == 7
                 and not c.execute(
                     "SELECT 1 FROM service_units su JOIN services s"
                     " ON s.service_id = su.service_id WHERE s.line_id = 2"
                     " AND su.unit_id IN (%s) LIMIT 1"
                     % ",".join(str(int(r[0])) for r in rows)).fetchall())],
    ),
    # ================================================= 4 Dates and times
    dict(
        id=11, ledger="Q532", concept="SPN", tier="4 - Dates and times",
        title="Every day of March, including the quiet ones",
        prompt=(
            "Every date in March 2025 with the number of incidents reported"
            " that day -- including the days with none, which must appear as"
            " 0.\n\n"
            "Thirty-one rows. The days with no incidents are not in the"
            " incidents table at all, so grouping it can never produce them:"
            " you have to generate the calendar and hang the data off it.\n\n"
            "Return: day, incidents"
        ),
        solution=("WITH RECURSIVE d(x) AS (SELECT '2025-03-01'"
                  " UNION ALL SELECT date(x, '+1 day') FROM d"
                  " WHERE x < '2025-03-31')"
                  " SELECT d.x, COUNT(i.incident_id) FROM d"
                  " LEFT JOIN incidents i ON date(i.reported_at) = d.x"
                  " GROUP BY d.x"),
        trap_sql=("SELECT date(reported_at), COUNT(*) FROM incidents"
                  " WHERE date(reported_at) BETWEEN '2025-03-01'"
                  " AND '2025-03-31' GROUP BY 1"),
        note="A GROUP BY can only return groups the data contains. A day with"
             " no incidents has no row to group, so it cannot appear however"
             " the query is written -- the trap returns only the days that"
             " happened, and a chart built on it silently closes the gaps. The"
             " fix is a SPINE: generate the days you want with a recursive"
             " CTE, then LEFT JOIN the data onto it. COUNT(i.incident_id)"
             " rather than COUNT(*) is what makes the empty days 0, because"
             " COUNT(*) counts the spine row itself and would report 1.",
        claims=[("thirty-one days, some of them zero",
                 lambda rows, c: len(rows) == 31
                 and any(r[1] == 0 for r in rows)
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM incidents WHERE date(reported_at)"
                     " BETWEEN '2025-03-01' AND '2025-03-31'").fetchone()[0])],
    ),
    dict(
        id=12, ledger="Q533", concept="SPN", tier="4 - Dates and times",
        title="Every line, every kind, every quarter",
        prompt=(
            "For each line, each kind of incident and each quarter of 2025,"
            " how many incidents there were -- including the combinations that"
            " never happened, as 0.\n\n"
            "Label quarters '2025Q1' to '2025Q4'. Six lines x five kinds x"
            " four quarters, so 120 rows whatever the data does.\n\n"
            "Return: line_id, kind, quarter, incidents"
        ),
        solution=("WITH q(q) AS (VALUES ('2025Q1'), ('2025Q2'), ('2025Q3'),"
                  " ('2025Q4')), k AS (SELECT DISTINCT kind FROM incidents)"
                  " SELECT l.line_id, k.kind, q.q, COUNT(i.incident_id)"
                  " FROM lines l CROSS JOIN k CROSS JOIN q"
                  " LEFT JOIN services s ON s.line_id = l.line_id"
                  " LEFT JOIN incidents i ON i.service_id = s.service_id"
                  " AND i.kind = k.kind"
                  " AND strftime('%Y', i.reported_at) || 'Q'"
                  " || ((CAST(strftime('%m', i.reported_at) AS INTEGER) + 2)"
                  " / 3) = q.q"
                  " GROUP BY l.line_id, k.kind, q.q"),
        trap_sql=("SELECT s.line_id, i.kind,"
                  " strftime('%Y', i.reported_at) || 'Q'"
                  " || ((CAST(strftime('%m', i.reported_at) AS INTEGER) + 2)"
                  " / 3), COUNT(*) FROM incidents i"
                  " JOIN services s ON s.service_id = i.service_id"
                  " WHERE strftime('%Y', i.reported_at) = '2025'"
                  " GROUP BY 1, 2, 3"),
        note="The same lesson as question 11 in two dimensions instead of one."
             " CROSS JOIN builds every combination that SHOULD exist -- that is"
             " what a cross join is for, and one of the few times you want one"
             " on purpose -- and the LEFT JOIN attaches whatever data there is."
             " Note where the quarter test lives: in the ON clause, not WHERE."
             " In WHERE it would discard the unmatched spine rows, which are"
             " the entire point. VALUES works as an inline table here, saving"
             " a four-way UNION ALL.",
        claims=[("120 rows, and at least one of them zero",
                 lambda rows, c: len(rows) == 120
                 and any(r[3] == 0 for r in rows))],
    ),
    dict(
        id=13, ledger="Q534", concept="D2", tier="4 - Dates and times",
        title="The first Monday of each month",
        prompt=(
            "How many services ran on the first MONDAY of each month.\n\n"
            "Build that date with modifiers. One row per month, all eighteen."
            "\n\nReturn: month, services"
        ),
        solution=("SELECT strftime('%Y-%m', run_date), COUNT(*) FROM services"
                  " WHERE run_date = date(run_date, 'start of month',"
                  " 'weekday 1') GROUP BY 1"),
        trap_sql=("SELECT strftime('%Y-%m', run_date), COUNT(*) FROM services"
                  " WHERE run_date = date(run_date, 'start of month',"
                  " '-1 day', 'weekday 1') GROUP BY 1"),
        note="'weekday 1' moves forward to the next Monday and leaves the date"
             " ALONE when it is already one -- which is exactly what makes"
             " 'start of month' then 'weekday 1' correct: from the 1st it"
             " either stays (the 1st is a Monday) or advances to the first"
             " Monday after it. The trap steps back a day first, reasoning"
             " that it should force a move. It does, but from the last day of"
             " the PREVIOUS month -- and when that day is itself a Monday,"
             " 'weekday 1' stays put in the wrong month and that month"
             " disappears from the result. Two of the eighteen go missing.",
        claims=[("all eighteen months, each a Monday",
                 lambda rows, c: len(rows) == 18
                 and all(c.execute("SELECT strftime('%w', ?)",
                                   (r[0] + '-01',)).fetchone() is not None
                         for r in rows))],
    ),
    dict(
        id=14, ledger="Q535", concept="D1", tier="4 - Dates and times",
        title="How long staff have served",
        prompt=(
            "Staff bucketed by length of service as at 2026-06-30: 'under 5"
            " years', '5 to 15', 'over 15'.\n\n"
            "Return: band, staff"
        ),
        solution=("SELECT CASE WHEN (julianday('2026-06-30')"
                  " - julianday(hired_on)) / 365.25 < 5 THEN 'under 5 years'"
                  " WHEN (julianday('2026-06-30') - julianday(hired_on))"
                  " / 365.25 <= 15 THEN '5 to 15' ELSE 'over 15' END,"
                  " COUNT(*) FROM staff GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN strftime('%Y', '2026-06-30')"
                  " - strftime('%Y', hired_on) < 5 THEN 'under 5 years'"
                  " WHEN strftime('%Y', '2026-06-30') - strftime('%Y',"
                  " hired_on) <= 15 THEN '5 to 15' ELSE 'over 15' END,"
                  " COUNT(*) FROM staff GROUP BY 1"),
        note="Subtracting one year number from another counts calendar years,"
             " not elapsed ones: hired on the 31st of December 2021 scores the"
             " same as hired on the 1st of January 2021, though a year"
             " separates them. Near a band boundary that moves people between"
             " buckets. julianday() converts both dates to a day count first,"
             " so the arithmetic is real.",
        claims=[("the bands cover all forty staff",
                 lambda rows, c: sum(r[1] for r in rows) == 40)],
    ),
    # ================================================= 5 Joins and grain
    dict(
        id=15, ledger="Q536", concept="J2", tier="5 - Joins and grain",
        title="Every station, tickets or not",
        prompt=(
            "Every station with the number of tickets bought TO it. Stations"
            " nobody travels to must appear with 0, so all 60 come back.\n\n"
            "Return: station_id, name, tickets"
        ),
        solution=("SELECT st.station_id, st.name, COUNT(t.ticket_id)"
                  " FROM stations st LEFT JOIN tickets t"
                  " ON t.to_station = st.station_id GROUP BY 1, 2"),
        trap_sql=("SELECT st.station_id, st.name, COUNT(*)"
                  " FROM stations st LEFT JOIN tickets t"
                  " ON t.to_station = st.station_id GROUP BY 1, 2"),
        note="COUNT(*) counts rows, and an outer join that found nothing still"
             " produces one row -- with NULLs in every column of the right"
             " table. So the stations you were careful to keep come back with"
             " 1 instead of 0. COUNT of a column from the RIGHT table skips"
             " those NULLs and reports 0. Whenever you count over an outer"
             " join, name a column.",
        claims=[("all 60 stations, some with none, totalling the tickets",
                 lambda rows, c: len(rows) == 60
                 and any(r[2] == 0 for r in rows)
                 and sum(r[2] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM tickets"
                     " WHERE to_station IS NOT NULL").fetchone()[0])],
    ),
    dict(
        id=16, ledger="Q537", concept="GAP", tier="5 - Joins and grain",
        title="The longest quiet spell",
        prompt=(
            "The three longest runs of CONSECUTIVE days on which line 1 had no"
            " incident at all.\n\n"
            "Only count days the timetable actually ran. Longest first, then"
            " earliest.\n\n"
            "Return: days, started, ended"
        ),
        solution=("WITH d AS (SELECT DISTINCT run_date FROM services),"
                  " q AS (SELECT run_date, ROW_NUMBER() OVER"
                  " (ORDER BY run_date) rn FROM d"
                  " WHERE NOT EXISTS (SELECT 1 FROM incidents i"
                  " JOIN services s ON s.service_id = i.service_id"
                  " WHERE s.line_id = 1 AND s.run_date = d.run_date))"
                  " SELECT COUNT(*), MIN(run_date), MAX(run_date) FROM"
                  " (SELECT run_date, date(run_date, '-' || rn || ' days') g"
                  " FROM q) GROUP BY g ORDER BY 1 DESC, 2 LIMIT 3"),
        trap_sql=("WITH d AS (SELECT DISTINCT run_date FROM services)"
                  " SELECT COUNT(*), MIN(run_date), MAX(run_date) FROM d"
                  " WHERE NOT EXISTS (SELECT 1 FROM incidents i"
                  " JOIN services s ON s.service_id = i.service_id"
                  " WHERE s.line_id = 1 AND s.run_date = d.run_date)"),
        note="Gaps and islands, the standard trick and worth learning once."
             " Number the qualifying days 1, 2, 3... in date order. For days"
             " that are CONSECUTIVE, the date minus the row number is"
             " constant -- both advance in step -- and it changes exactly when"
             " a day is missing. So that difference is a group id for each"
             " unbroken run, and the rest is an ordinary GROUP BY. The trap"
             " counts all the quiet days as one lump, which is a different"
             " question with a much larger answer.",
        claims=[("three runs, none longer than the days available",
                 lambda rows, c: len(rows) == 3
                 and rows[0][0] >= rows[2][0]
                 and all(r[0] > 1 for r in rows))],
    ),
    dict(
        id=17, ledger="Q538", concept="C2", tier="5 - Joins and grain",
        title="Revenue and incidents together",
        prompt=(
            "One row per operator: total ticket revenue in pence and the"
            " number of incidents.\n\n"
            "Both hang off `services`. A SUM cannot be rescued by DISTINCT, so"
            " the fan-out has to be avoided rather than undone.\n\n"
            "Return: operator, revenue, incidents"
        ),
        solution=("SELECT o.name,"
                  " (SELECT COALESCE(SUM(t.price_pence), 0) FROM tickets t"
                  " JOIN services s ON s.service_id = t.service_id"
                  " WHERE s.operator_id = o.operator_id),"
                  " (SELECT COUNT(*) FROM incidents i"
                  " JOIN services s ON s.service_id = i.service_id"
                  " WHERE s.operator_id = o.operator_id)"
                  " FROM operators o"),
        trap_sql=("SELECT o.name, SUM(t.price_pence), COUNT(i.incident_id)"
                  " FROM operators o"
                  " JOIN services s ON s.operator_id = o.operator_id"
                  " LEFT JOIN tickets t ON t.service_id = s.service_id"
                  " LEFT JOIN incidents i ON i.service_id = s.service_id"
                  " GROUP BY o.name"),
        note="The case where COUNT(DISTINCT) cannot save you. Joining two"
             " children of one parent multiplies the rows, and while a count"
             " can be repaired -- the duplicates share an id -- a SUM cannot,"
             " because the repeated amounts are indistinguishable from"
             " genuinely separate tickets. A service with 20 tickets and 2"
             " incidents has its revenue counted twice. Aggregate each child"
             " on its own, as two subqueries or two CTEs joined to the parent.",
        claims=[("four operators, revenue matching the ticket table",
                 lambda rows, c: len(rows) == 4
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT SUM(price_pence) FROM tickets").fetchone()[0])],
    ),
    dict(
        id=18, ledger="Q539", concept="E1", tier="5 - Joins and grain",
        title="Units that only ever work one line",
        prompt=(
            "Units of rolling stock that have run, and have only ever run on a"
            " single line -- with that line.\n\n"
            "Return: unit_id, line_id"
        ),
        solution=("SELECT su.unit_id, MIN(s.line_id) FROM service_units su"
                  " JOIN services s ON s.service_id = su.service_id"
                  " GROUP BY su.unit_id"
                  " HAVING COUNT(DISTINCT s.line_id) = 1"),
        trap_sql=("SELECT DISTINCT su.unit_id, s.line_id FROM service_units su"
                  " JOIN services s ON s.service_id = su.service_id"),
        note="'Only ever' is a statement about all of a unit's rows at once,"
             " so it has to be tested after grouping -- COUNT(DISTINCT"
             " line_id) = 1 in HAVING. No row-level filter can express it,"
             " because each row only knows about one working. Once the group"
             " is down to a single line, MIN or MAX is a harmless way to fetch"
             " the value: they all agree.",
        claims=[("every unit returned has exactly one line",
                 lambda rows, c: len(rows) > 0
                 and all(r[0] not in {x[0] for x in rows if x[1] != r[1]}
                         for r in rows))],
    ),
    # ================================================= 6 Window functions
    dict(
        id=19, ledger="Q540", concept="W1", tier="6 - Window functions",
        title="Revenue month by month, accumulating",
        prompt=(
            "Ticket revenue by month with a running total.\n\n"
            "Return: month, revenue, running_total"
        ),
        solution=("SELECT strftime('%Y-%m', sold_at) m, SUM(price_pence),"
                  " SUM(SUM(price_pence)) OVER (ORDER BY"
                  " strftime('%Y-%m', sold_at) ROWS BETWEEN UNBOUNDED"
                  " PRECEDING AND CURRENT ROW) FROM tickets GROUP BY m"),
        trap_sql=("SELECT strftime('%Y-%m', sold_at) m, SUM(price_pence),"
                  " SUM(SUM(price_pence)) OVER (ORDER BY"
                  " strftime('%Y-%m', sold_at) ROWS BETWEEN CURRENT ROW"
                  " AND UNBOUNDED FOLLOWING) FROM tickets GROUP BY m"),
        note="The frame is the whole question. UNBOUNDED PRECEDING to CURRENT"
             " ROW accumulates from the start; CURRENT ROW to UNBOUNDED"
             " FOLLOWING counts down what is left. Both are running totals,"
             " both end plausibly, and only one is the one you asked for --"
             " check row 1, where the running total should equal the month.",
        claims=[("the running total rises to every ticket",
                 lambda rows, c: rows[0][1] == rows[0][2]
                 and max(r[2] for r in rows) == c.execute(
                     "SELECT SUM(price_pence) FROM tickets").fetchone()[0])],
    ),
    dict(
        id=20, ledger="Q541", concept="W2", tier="6 - Window functions",
        title="The best-earning service on each line",
        prompt=(
            "For each line, the single service that took the most money.\n\n"
            "Ties broken by the lower service_id. Six rows.\n\n"
            "Return: line_id, service_id, revenue"
        ),
        solution=("SELECT line_id, service_id, n FROM (SELECT s.line_id,"
                  " s.service_id, SUM(t.price_pence) n, ROW_NUMBER() OVER"
                  " (PARTITION BY s.line_id ORDER BY SUM(t.price_pence) DESC,"
                  " s.service_id) rn FROM services s JOIN tickets t"
                  " ON t.service_id = s.service_id GROUP BY s.service_id)"
                  " WHERE rn = 1"),
        trap_sql=("SELECT s.line_id, s.service_id, SUM(t.price_pence) n"
                  " FROM services s JOIN tickets t"
                  " ON t.service_id = s.service_id GROUP BY s.service_id"
                  " ORDER BY n DESC LIMIT 6"),
        note="Top-N per group. WHERE is evaluated before the window function"
             " exists, so the numbering has to happen in a subquery and be"
             " filtered outside it. The trap takes the six best services"
             " overall, which is a different question: one busy line can take"
             " every slot and a quiet line appear nowhere.",
        claims=[("one row for each of the six lines",
                 lambda rows, c: len(rows) == 6
                 and len({r[0] for r in rows}) == 6)],
    ),
    dict(
        id=21, ledger="Q542", concept="RNG", tier="6 - Window functions",
        title="Units of a similar size",
        prompt=(
            "For each unit, how many units in the whole fleet have a seat"
            " count within 20 of its own -- itself included.\n\n"
            "'Within 20' is about the VALUES, not about neighbouring rows, so"
            " the frame has to be measured in seats rather than in positions."
            " Fifty rows.\n\n"
            "Return: unit_id, seats, similar_units"
        ),
        solution=("SELECT unit_id, seats, COUNT(*) OVER (ORDER BY seats"
                  " RANGE BETWEEN 20 PRECEDING AND 20 FOLLOWING)"
                  " FROM rolling_stock"),
        trap_sql=("SELECT unit_id, seats, COUNT(*) OVER (ORDER BY seats"
                  " ROWS BETWEEN 20 PRECEDING AND 20 FOLLOWING)"
                  " FROM rolling_stock"),
        note="ROWS and RANGE both take a frame, and they count different"
             " things. ROWS BETWEEN 20 PRECEDING counts twenty ROWS back,"
             " whatever their values. RANGE BETWEEN 20 PRECEDING counts every"
             " row whose ORDER BY value is within 20 of this one -- so the"
             " frame grows and shrinks with the data, and every row of a tied"
             " group gets the same answer. RANGE needs exactly one ORDER BY"
             " column, and it must be numeric or a date for an offset to mean"
             " anything.",
        claims=[("fifty rows, and tied units always agree",
                 lambda rows, c: len(rows) == 50
                 and all(len({r[2] for r in rows if r[1] == s}) == 1
                         for s in {r[1] for r in rows}))],
    ),
    dict(
        id=22, ledger="Q543", concept="EXC", tier="6 - Window functions",
        title="Everyone but your equals",
        prompt=(
            "For each unit: its seat count, how many units its MODEL has, and"
            " how many of those are not on the same seat count as it.\n\n"
            "The last column is the model's fleet minus this unit's tied"
            " group. There is a frame clause for that -- no arithmetic"
            " needed.\n\nReturn: unit_id, seats, model_units, others"
        ),
        solution=("SELECT unit_id, seats,"
                  " COUNT(*) OVER (PARTITION BY model ORDER BY seats"
                  " RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED"
                  " FOLLOWING), COUNT(*) OVER (PARTITION BY model"
                  " ORDER BY seats RANGE BETWEEN UNBOUNDED PRECEDING"
                  " AND UNBOUNDED FOLLOWING EXCLUDE GROUP)"
                  " FROM rolling_stock"),
        trap_sql=("SELECT unit_id, seats,"
                  " COUNT(*) OVER (PARTITION BY model ORDER BY seats"
                  " RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED"
                  " FOLLOWING), COUNT(*) OVER (PARTITION BY model"
                  " ORDER BY seats RANGE BETWEEN UNBOUNDED PRECEDING"
                  " AND UNBOUNDED FOLLOWING EXCLUDE CURRENT ROW)"
                  " FROM rolling_stock"),
        note="EXCLUDE trims the frame after it has been worked out, and there"
             " are four settings. EXCLUDE CURRENT ROW drops just this row."
             " EXCLUDE GROUP drops this row AND every row tied with it under"
             " the ORDER BY. EXCLUDE TIES drops the peers but keeps this row."
             " EXCLUDE NO OTHERS is the default. The trap uses CURRENT ROW,"
             " which leaves the unit's equals in the count -- a precise answer"
             " to a question nobody asked. Note this only means anything"
             " because the frame is RANGE: under ROWS, 'tied' would not be a"
             " concept the frame knows about.",
        claims=[("the gap is always this unit's tied group inside its model",
                 lambda rows, c: len(rows) == 50
                 and len({r[2] for r in rows}) > 1)],
    ),
    dict(
        id=23, ledger="Q544", concept="WIN", tier="6 - Window functions",
        title="One window, three questions",
        prompt=(
            "Incidents by month, with a running total, a running average and"
            " the running maximum.\n\n"
            "All three use the same window. Define it ONCE in a WINDOW clause"
            " and refer to it by name rather than repeating it. Round the"
            " average to two decimals.\n\n"
            "Return: month, incidents, running_total, running_avg, running_max"
        ),
        solution=("SELECT strftime('%Y-%m', reported_at) m, COUNT(*),"
                  " SUM(COUNT(*)) OVER w, ROUND(AVG(COUNT(*)) OVER w, 2),"
                  " MAX(COUNT(*)) OVER w FROM incidents GROUP BY m"
                  " WINDOW w AS (ORDER BY strftime('%Y-%m', reported_at)"
                  " ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)"),
        trap_sql=("SELECT strftime('%Y-%m', reported_at) m, COUNT(*),"
                  " SUM(COUNT(*)) OVER w, ROUND(AVG(COUNT(*)) OVER w, 2),"
                  " MAX(COUNT(*)) OVER (ORDER BY"
                  " strftime('%Y-%m', reported_at) ROWS BETWEEN 2 PRECEDING"
                  " AND CURRENT ROW) FROM incidents GROUP BY m"
                  " WINDOW w AS (ORDER BY strftime('%Y-%m', reported_at)"
                  " ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)"),
        note="The WINDOW clause sits between HAVING and ORDER BY and names a"
             " window definition so several functions can share it. Three"
             " copies of the same OVER (...) is three chances to change one"
             " and not the others, which is exactly what the trap does -- its"
             " third window is spelled out again with a three-month frame, so"
             " the running maximum becomes a rolling one and can fall. Two of"
             " the five columns then disagree about what 'running' means, and"
             " nothing in the query looks wrong. You can also write"
             " OVER (w ORDER BY ...) to extend a named window rather than"
             " replace it.",
        claims=[("the running max never falls",
                 lambda rows, c: len(rows) == 18
                 and all(rows[i][4] >= rows[i - 1][4]
                         for i in range(1, len(rows)))
                 and rows[-1][2] == c.execute(
                     "SELECT COUNT(*) FROM incidents").fetchone()[0])],
    ),
    dict(
        id=24, ledger="Q545", concept="GAP", tier="6 - Window functions",
        title="Each line's best quiet streak",
        prompt=(
            "For every line, the length of its longest run of consecutive"
            " timetabled days with no incident.\n\n"
            "Six rows. Same island-finding as question 16, but partitioned --"
            " each line has to be numbered separately.\n\n"
            "Return: line_id, longest_streak"
        ),
        solution=("WITH d AS (SELECT DISTINCT run_date FROM services),"
                  " q AS (SELECT l.line_id, d.run_date, ROW_NUMBER() OVER"
                  " (PARTITION BY l.line_id ORDER BY d.run_date) rn"
                  " FROM lines l CROSS JOIN d WHERE NOT EXISTS"
                  " (SELECT 1 FROM incidents i JOIN services s"
                  " ON s.service_id = i.service_id"
                  " WHERE s.line_id = l.line_id AND s.run_date = d.run_date))"
                  " SELECT line_id, MAX(len) FROM (SELECT line_id, COUNT(*) len"
                  " FROM (SELECT line_id, run_date,"
                  " date(run_date, '-' || rn || ' days') g FROM q)"
                  " GROUP BY line_id, g) GROUP BY line_id"),
        trap_sql=("WITH d AS (SELECT DISTINCT run_date FROM services),"
                  " q AS (SELECT l.line_id, d.run_date, ROW_NUMBER() OVER"
                  " (ORDER BY d.run_date) rn"
                  " FROM lines l CROSS JOIN d WHERE NOT EXISTS"
                  " (SELECT 1 FROM incidents i JOIN services s"
                  " ON s.service_id = i.service_id"
                  " WHERE s.line_id = l.line_id AND s.run_date = d.run_date))"
                  " SELECT line_id, MAX(len) FROM (SELECT line_id, COUNT(*) len"
                  " FROM (SELECT line_id, run_date,"
                  " date(run_date, '-' || rn || ' days') g FROM q)"
                  " GROUP BY line_id, g) GROUP BY line_id"),
        note="The numbering has to restart for each line, or the row numbers"
             " run continuously across all six and the date-minus-rn trick"
             " compares days that belong to different lines. The trap omits"
             " PARTITION BY and produces streaks of 1 almost everywhere,"
             " because consecutive rows are usually different lines. Whenever"
             " you use this technique per-group, the PARTITION BY on"
             " ROW_NUMBER is the part that makes it per-group.",
        claims=[("six lines, streaks longer than a single day",
                 lambda rows, c: len(rows) == 6
                 and all(r[1] > 2 for r in rows))],
    ),
    dict(
        id=25, ledger="Q546", concept="MED", tier="6 - Window functions",
        title="The median unit",
        prompt=(
            "The MEDIAN seat count for each model of rolling stock.\n\n"
            "SQLite has no median function. Several models have an even number"
            " of units, and for those the median is the average of the two"
            " middle values -- not either one of them.\n\n"
            "Return: model, median_seats"
        ),
        solution=("WITH r AS (SELECT model, seats, ROW_NUMBER() OVER"
                  " (PARTITION BY model ORDER BY seats) rn,"
                  " COUNT(*) OVER (PARTITION BY model) n FROM rolling_stock)"
                  " SELECT model, AVG(seats) FROM r"
                  " WHERE rn IN ((n + 1) / 2, (n + 2) / 2) GROUP BY model"),
        trap_sql=("WITH r AS (SELECT model, seats, ROW_NUMBER() OVER"
                  " (PARTITION BY model ORDER BY seats) rn,"
                  " COUNT(*) OVER (PARTITION BY model) n FROM rolling_stock)"
                  " SELECT model, AVG(seats) FROM r"
                  " WHERE rn = (n + 1) / 2 GROUP BY model"),
        note="Number the rows within each model in seat order and count them"
             " in the same pass, then take the middle. The two expressions"
             " (n + 1) / 2 and (n + 2) / 2 are the trick: under integer"
             " division they pick the SAME row when n is odd and the two"
             " middle rows when n is even, so one formula covers both cases"
             " without a CASE. The trap keeps only the lower middle, which is"
             " right for the odd-sized models and wrong for every even one --"
             " a plausible number, off by half the gap. It is also why a"
             " median is not simply 'the middle row'.",
        claims=[("a median for every model, each inside its own range",
                 lambda rows, c: len(rows) == c.execute(
                     "SELECT COUNT(DISTINCT model)"
                     " FROM rolling_stock").fetchone()[0]
                 and all(c.execute(
                     "SELECT MIN(seats) <= ? AND MAX(seats) >= ?"
                     " FROM rolling_stock WHERE model = ?",
                     (r[1], r[1], r[0])).fetchone()[0] for r in rows))],
    ),
    dict(
        id=26, ledger="Q547", concept="W3", tier="6 - Window functions",
        title="Share of the line's revenue",
        prompt=(
            "For every service that sold tickets, its revenue and what"
            " percentage of its LINE's revenue that is.\n\n"
            "Within a line the percentages add to 100. Round to four decimals."
            "\n\nReturn: service_id, line_id, revenue, pct_of_line"
        ),
        solution=("SELECT s.service_id, s.line_id, SUM(t.price_pence),"
                  " ROUND(100.0 * SUM(t.price_pence) / SUM(SUM(t.price_pence))"
                  " OVER (PARTITION BY s.line_id), 4) FROM services s"
                  " JOIN tickets t ON t.service_id = s.service_id"
                  " GROUP BY s.service_id, s.line_id"),
        trap_sql=("SELECT s.service_id, s.line_id, SUM(t.price_pence),"
                  " ROUND(100.0 * SUM(t.price_pence) / SUM(SUM(t.price_pence))"
                  " OVER (), 4) FROM services s"
                  " JOIN tickets t ON t.service_id = s.service_id"
                  " GROUP BY s.service_id, s.line_id"),
        note="PARTITION BY chooses the denominator. Without it there is one"
             " partition holding every service, so each percentage is a share"
             " of the WHOLE network -- about a sixth of what it should be, and"
             " summing to 100 across the entire result rather than within each"
             " line. Both versions look reasonable; the check is to add up one"
             " line's percentages.",
        claims=[("each line's percentages sum to 100",
                 lambda rows, c: all(
                     abs(sum(r[3] for r in rows if r[1] == lid) - 100) < 0.5
                     for lid in {r[1] for r in rows}))],
    ),
    # ================================================== 7 Query efficiency
    dict(
        id=27, ledger="Q548", concept="X8", tier="7 - Query efficiency",
        title="An average recalculated thirty thousand times",
        prompt=(
            "How many tickets on lines 1 and 2 cost more than the average for"
            " their own class, one row per line.\n\n"
            "The editor's query asks for that average inside the WHERE clause,"
            " where it is correlated to the row -- so it is worked out again"
            " for every ticket, and the query takes about four SECONDS. Your"
            " plan must not contain 'CORRELATED'.\n\n"
            "Return: line_id, tickets"
        ),
        solution=("WITH a AS (SELECT class, AVG(price_pence) m FROM tickets"
                  " GROUP BY class) SELECT s.line_id, COUNT(*) FROM tickets t"
                  " JOIN services s ON s.service_id = t.service_id"
                  " JOIN a ON a.class = t.class"
                  " WHERE s.line_id IN (1, 2) AND t.price_pence > a.m"
                  " GROUP BY s.line_id"),
        trap_sql=("SELECT s.line_id, COUNT(*) FROM tickets t"
                  " JOIN services s ON s.service_id = t.service_id"
                  " WHERE s.line_id IN (1, 2) AND t.price_pence >"
                  " (SELECT AVG(price_pence) FROM tickets x"
                  " WHERE x.class = t.class) GROUP BY s.line_id"),
        starter_sql=("SELECT s.line_id, COUNT(*) FROM tickets t"
                     " JOIN services s ON s.service_id = t.service_id"
                     " WHERE s.line_id IN (1, 2) AND t.price_pence >"
                     " (SELECT AVG(price_pence) FROM tickets x"
                     " WHERE x.class = t.class) GROUP BY s.line_id"),
        plan_forbids=("CORRELATED",),
        note="There are only three class averages, and the query computes them"
             " about six thousand times each. CORRELATED in a plan means the"
             " subquery depends on the current row, so it cannot be worked out"
             " once -- and an aggregate over 11,000 rows, re-run per row, is"
             " what four seconds looks like. Lift it into a CTE and it runs"
             " once. This is the exact reverse of Q491, where materialising a"
             " CTE was the mistake. The distinction: there the CTE computed"
             " far more than the outer query needed, and here it computes"
             " three numbers that every row wants. Ask what the subquery costs"
             " and how often it runs -- not which syntax it is written in.",
        claims=[("two lines, matching the correlated version",
                 lambda rows, c: len(rows) == 2
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM tickets t JOIN services s"
                     " ON s.service_id = t.service_id"
                     " WHERE s.line_id IN (1, 2) AND t.price_pence >"
                     " (SELECT AVG(price_pence) FROM tickets x"
                     " WHERE x.class = t.class)").fetchone()[0])],
    ),
    dict(
        id=28, ledger="Q549", concept="X9", tier="7 - Query efficiency",
        title="A correlation that buys nothing",
        prompt=(
            "How many services have had at least one incident.\n\n"
            "The editor's query uses IN with a subquery, and has added a"
            " condition tying the subquery back to the outer row. It returns"
            " the right answer. Take the condition out -- IN already compares"
            " the value -- and the subquery can be evaluated once instead of"
            " per row. Your plan must not contain 'CORRELATED'.\n\n"
            "Return: one row, one column: the count"
        ),
        solution=("SELECT COUNT(*) FROM services s WHERE s.service_id IN"
                  " (SELECT i.service_id FROM incidents i)"),
        trap_sql=("SELECT COUNT(*) FROM services s WHERE s.service_id IN"
                  " (SELECT i.service_id FROM incidents i"
                  " WHERE i.service_id = s.service_id)"),
        starter_sql=("SELECT COUNT(*) FROM services s WHERE s.service_id IN"
                     " (SELECT i.service_id FROM incidents i"
                     " WHERE i.service_id = s.service_id)"),
        plan_forbids=("CORRELATED",),
        note="`x IN (SELECT y FROM t)` already means 'is x among the y values'."
             " Adding WHERE y = x inside restates it, and the restatement is"
             " what costs: the subquery now mentions the outer row, so SQLite"
             " must re-run it for each of 11,111 services instead of building"
             " the value list once. The plan says so -- CORRELATED LIST"
             " SUBQUERY against LIST SUBQUERY, and the uncorrelated form gets"
             " a bloom filter as well. It is an easy habit to pick up from"
             " EXISTS, where the correlation is required and there is no other"
             " way to link the two.",
        claims=[("the same count as a join",
                 lambda rows, c: rows[0][0] == c.execute(
                     "SELECT COUNT(DISTINCT service_id)"
                     " FROM incidents").fetchone()[0])],
    ),
    dict(
        id=29, ledger="Q550", concept="X1", tier="7 - Query efficiency",
        title="A date treated as a number",
        prompt=(
            "How many tickets were sold on services running in 2026 or later."
            "\n\nrun_date is TEXT in 'YYYY-MM-DD' and is indexed. The editor's"
            " query compares it as a number, which gets the right answer and"
            " loses the index. Your plan must not contain 'SCAN'.\n\n"
            "Return: one row, one column: the count"
        ),
        solution=("SELECT COUNT(*) FROM services s JOIN tickets t"
                  " ON t.service_id = s.service_id"
                  " WHERE s.run_date >= '2026-01-01'"),
        trap_sql=("SELECT COUNT(*) FROM services s JOIN tickets t"
                  " ON t.service_id = s.service_id"
                  " WHERE s.run_date + 0 >= 2026"),
        starter_sql=("SELECT COUNT(*) FROM services s JOIN tickets t"
                     " ON t.service_id = s.service_id"
                     " WHERE s.run_date + 0 >= 2026"),
        plan_forbids=("SCAN",),
        note="`run_date + 0` forces SQLite to read the leading digits of each"
             " date as a number -- '2026-03-14' becomes 2026 -- which happens"
             " to answer the question and destroys the index twice over. It is"
             " an expression, so no seek is possible; and the values it"
             " produces are not the values the index holds, so nothing could"
             " be seeked to anyway. The whole ticket table gets scanned and"
             " each service looked up. Compare the column against a string of"
             " the same shape and the index does the work.",
        claims=[("the count matches the string comparison",
                 lambda rows, c: rows[0][0] == c.execute(
                     "SELECT COUNT(*) FROM services s JOIN tickets t"
                     " ON t.service_id = s.service_id"
                     " WHERE s.run_date >= '2026-01-01'").fetchone()[0])],
    ),
    dict(
        id=30, ledger="Q551", concept="X5", tier="7 - Query efficiency",
        title="The join that costs a covering index",
        prompt=(
            "The class and price of every first-class ticket over 2900 pence,"
            " cheapest first, ties by ticket_id.\n\n"
            "The editor's query joins `services`. It adds no column, and"
            " because every ticket has a service it removes no row either --"
            " but idx_tickets_class holds only class and price_pence, so"
            " reaching service_id forces a lookup into the table for all 2,680"
            " matches. Your plan must contain 'COVERING INDEX'.\n\n"
            "Return: class, price_pence"
        ),
        solution=("SELECT t.class, t.price_pence FROM tickets t"
                  " WHERE t.class = 'first' AND t.price_pence > 2900"
                  " ORDER BY t.price_pence, t.ticket_id"),
        trap_sql=("SELECT t.class, t.price_pence FROM tickets t"
                  " JOIN services s ON s.service_id = t.service_id"
                  " WHERE t.class = 'first' AND t.price_pence > 2900"
                  " ORDER BY t.price_pence, t.ticket_id"),
        starter_sql=("SELECT t.class, t.price_pence FROM tickets t"
                     " JOIN services s ON s.service_id = t.service_id"
                     " WHERE t.class = 'first' AND t.price_pence > 2900"
                     " ORDER BY t.price_pence, t.ticket_id"),
        plan_requires=("COVERING INDEX",),
        note="A COVERING index is one that holds every column the query"
             " touches, so the table itself is never opened. Both versions say"
             " SEARCH t USING ... idx_tickets_class -- the difference is the"
             " word COVERING, and that one word is the whole cost. The join"
             " needs t.service_id, which the index does not carry, so every"
             " matching row requires a second read. Note this is NOT the"
             " fan-out of question 17: the row count is identical, nothing is"
             " double-counted, and the only damage is to how the rows are"
             " fetched. A join that contributes no column is worth deleting"
             " even when it changes no answer.",
        claims=[("every row first class and over 2900",
                 lambda rows, c: len(rows) > 100
                 and all(r[0] == 'first' and r[1] > 2900 for r in rows))],
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
