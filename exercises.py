"""Practice exercises: thirty questions on the railway schema.

Window functions carry this set -- ten of the thirty, up from six, and every
one a different mechanism rather than the same running total four times over:

  * LEAD to reach the next row, LAST_VALUE to reach the last
  * a frame that ends at the current row, one that starts there, and one
    that covers the whole partition
  * RANK against DENSE_RANK where the ties actually bite
  * a share of a PARTITION, a share of everything, and a percentile
  * an aggregate nested inside a window over already-grouped rows
  * ROW_NUMBER in a subquery, because a window cannot live in WHERE

The other twenty keep the spread: dates, set operations, unpivoting, grain,
and four efficiency puzzles graded on EXPLAIN QUERY PLAN.

The efficiency stage opens with a correct-but-slow query already in the
editor and grades the plan as well as the rows. Four mechanisms, none of
them repeated from the last set:

  27  an expression on the JOIN KEY, so the index cannot be probed at all
  28  a correlated EXISTS that cannot reach the filter doing the work
  29  grouping and sorting everything before a LIMIT of 20 applies
  30  a join that adds no columns, multiplies the rows, and forces a
      COUNT(DISTINCT) to undo the damage

28 is a deliberate inversion: rewriting a DISTINCT join as EXISTS is
ordinary advice, and here it costs ten times.
"""

EXERCISES = [
    # ========================================================== 1 Warm-up
    dict(
        id=1, ledger="Q492", concept="A2", tier="1 - Warm-up",
        title="Delay by kind of incident",
        prompt=(
            "One row per kind of incident: how many there were, how many have"
            " a delay recorded, and the average delay in minutes.\n\n"
            "delay_minutes is NULL when nobody logged one. Those incidents"
            " still count in the first column. Round the average to two"
            " decimals.\n\n"
            "Return: kind, incidents, recorded, avg_delay"
        ),
        solution=("SELECT kind, COUNT(*), COUNT(delay_minutes),"
                  " ROUND(AVG(delay_minutes), 2) FROM incidents GROUP BY 1"),
        trap_sql=("SELECT kind, COUNT(*), COUNT(delay_minutes),"
                  " ROUND(AVG(COALESCE(delay_minutes, 0)), 2)"
                  " FROM incidents GROUP BY 1"),
        note="COUNT(*) counts rows; COUNT(col) counts rows where col is not"
             " NULL. The gap between those two columns is the whole point."
             " AVG already skips NULLs -- it divides by the number of values it"
             " found, not by the number of rows -- so it needs no help. The"
             " trap 'fixes' the NULLs with COALESCE and drags every average"
             " down, because an unrecorded delay is now a zero-minute one.",
        claims=[("five kinds, and fewer recorded than reported",
                 lambda rows, c: len(rows) == 5
                 and all(r[2] < r[1] for r in rows))],
    ),
    dict(
        id=2, ledger="Q493", concept="N1", tier="1 - Warm-up",
        title="What a ticket costs",
        prompt=(
            "One row per class: how many tickets, and the cheapest and dearest"
            " price in POUNDS.\n\n"
            "price_pence holds whole pence. Give the pounds to two decimals.\n"
            "\nReturn: class, tickets, cheapest, dearest"
        ),
        solution=("SELECT class, COUNT(*), ROUND(MIN(price_pence) / 100.0, 2),"
                  " ROUND(MAX(price_pence) / 100.0, 2) FROM tickets GROUP BY 1"),
        trap_sql=("SELECT class, COUNT(*), ROUND(MIN(price_pence) / 100, 2),"
                  " ROUND(MAX(price_pence) / 100, 2) FROM tickets GROUP BY 1"),
        note="Both sides of / 100 are integers, so SQLite does integer"
             " division and throws the pence away before ROUND ever sees them:"
             " 2299 / 100 is 22, and rounding 22 to two decimals is still 22."
             " Writing 100.0 makes one side a float and the whole expression"
             " follows. Money stored as an integer is exact right up until you"
             " divide it.",
        claims=[("three classes, all prices with pence",
                 lambda rows, c: len(rows) == 3
                 and any(r[2] != int(r[2]) or r[3] != int(r[3]) for r in rows))],
    ),
    dict(
        id=3, ledger="Q494", concept="C7", tier="1 - Warm-up",
        title="Units by size",
        prompt=(
            "Put every unit of rolling stock into a size band by its seat"
            " count and count them:\n"
            "  'large'  250 or more\n"
            "  'medium' 150 up to but not including 250\n"
            "  'small'  everything else\n\n"
            "All 50 units land in exactly one band.\n\n"
            "Return: band, units"
        ),
        solution=("SELECT CASE WHEN seats >= 250 THEN 'large'"
                  " WHEN seats >= 150 THEN 'medium' ELSE 'small' END,"
                  " COUNT(*) FROM rolling_stock GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN seats >= 150 THEN 'medium'"
                  " WHEN seats >= 250 THEN 'large' ELSE 'small' END,"
                  " COUNT(*) FROM rolling_stock GROUP BY 1"),
        note="CASE stops at the FIRST branch that is true, so the order of the"
             " WHEN clauses is the logic. Test the loosest condition first --"
             " as the trap does -- and it swallows everything the tighter ones"
             " were meant to catch: a 300-seat unit matches seats >= 150 and"
             " never reaches the 'large' branch, which then matches nothing at"
             " all. Overlapping conditions must run tightest first.",
        claims=[("three bands covering all 50 units",
                 lambda rows, c: len(rows) == 3
                 and sum(r[1] for r in rows) == 50)],
    ),
    # ========================================== 2 Sequences and strings
    dict(
        id=4, ledger="Q495", concept="W2", tier="2 - Sequences and strings",
        title="The next station",
        prompt=(
            "For service 100, every stop with the name of the station it calls"
            " at NEXT.\n\n"
            "The last stop has nothing after it, so its next station is NULL."
            " Ten rows.\n\n"
            "Return: stop_seq, station, next_station"
        ),
        solution=("SELECT sp.stop_seq, st.name, LEAD(st.name) OVER"
                  " (ORDER BY sp.stop_seq) FROM stops sp"
                  " JOIN stations st ON st.station_id = sp.station_id"
                  " WHERE sp.service_id = 100"),
        trap_sql=("SELECT sp.stop_seq, st.name, LAG(st.name) OVER"
                  " (ORDER BY sp.stop_seq) FROM stops sp"
                  " JOIN stations st ON st.station_id = sp.station_id"
                  " WHERE sp.service_id = 100"),
        note="LEAD looks forward, LAG looks back, and they are otherwise"
             " identical -- which is exactly why they are easy to swap by"
             " accident. The check is the edge: with LEAD the NULL lands on"
             " the LAST row, because nothing follows it. If your NULL is on"
             " row 1 you have the other function.",
        claims=[("ten rows, the NULL on the last",
                 lambda rows, c: len(rows) == 10
                 and rows[-1][2] is None
                 and all(r[2] is not None for r in rows[:-1]))],
    ),
    dict(
        id=5, ledger="Q496", concept="W1", tier="2 - Sequences and strings",
        title="Where each service finishes",
        prompt=(
            "For the first service of each line on 2025-03-05, every stop"
            " alongside the name of the station that service TERMINATES at --"
            " repeated on each of its rows.\n\n"
            "Six services, each with its own terminus. The answer is the last"
            " row of each service's own sequence, so you need a window that"
            " can see past the current row.\n\n"
            "Return: service_id, stop_seq, terminus"
        ),
        solution=("SELECT sp.service_id, sp.stop_seq, LAST_VALUE(st.name) OVER"
                  " (PARTITION BY sp.service_id ORDER BY sp.stop_seq"
                  " ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)"
                  " FROM stops sp JOIN stations st"
                  " ON st.station_id = sp.station_id"
                  " WHERE sp.service_id IN (SELECT MIN(service_id)"
                  " FROM services WHERE run_date = '2025-03-05'"
                  " GROUP BY line_id)"),
        trap_sql=("SELECT sp.service_id, sp.stop_seq, LAST_VALUE(st.name) OVER"
                  " (PARTITION BY sp.service_id ORDER BY sp.stop_seq)"
                  " FROM stops sp JOIN stations st"
                  " ON st.station_id = sp.station_id"
                  " WHERE sp.service_id IN (SELECT MIN(service_id)"
                  " FROM services WHERE run_date = '2025-03-05'"
                  " GROUP BY line_id)"),
        note="The one window-function default worth memorising. Once you write"
             " ORDER BY inside OVER, the frame becomes 'from the start of the"
             " partition to the CURRENT ROW' -- so LAST_VALUE returns the"
             " current row's own station, every time, and looks like it is"
             " doing nothing. FIRST_VALUE works without a frame precisely"
             " because the start of that default frame is the start of the"
             " partition. To see the end you must say so: ROWS BETWEEN"
             " UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING.",
        claims=[("six services, each with one terminus",
                 lambda rows, c: len({r[0] for r in rows}) == 6
                 and len({r[2] for r in rows}) > 1
                 and all(len({x[2] for x in rows if x[0] == sid}) == 1
                         for sid in {r[0] for r in rows}))],
    ),
    dict(
        id=6, ledger="Q497", concept="STR", tier="2 - Sequences and strings",
        title="Stations named after their town",
        prompt=(
            "Stations whose name STARTS WITH their town but is not simply the"
            " town on its own -- 'Marsden Riverside' in Marsden qualifies,"
            " plain 'Marsden' does not.\n\n"
            "Report what follows the town, with no leading space: 'Riverside'."
            "\n\nReturn: station_id, name, suffix"
        ),
        solution=("SELECT station_id, name,"
                  " SUBSTR(name, LENGTH(town) + 2) FROM stations"
                  " WHERE name <> town AND SUBSTR(name, 1, LENGTH(town)) = town"),
        trap_sql=("SELECT station_id, name,"
                  " SUBSTR(name, LENGTH(town) + 1) FROM stations"
                  " WHERE name <> town AND SUBSTR(name, 1, LENGTH(town)) = town"),
        note="SUBSTR in SQLite is 1-indexed: SUBSTR(s, 1) is the whole string,"
             " so the character after a town of length n is at position n + 1"
             " and the character after the SPACE that follows it is at n + 2."
             " The trap is off by one and leaves the space on the front of"
             " every answer -- invisible in the results pane, and a mismatch"
             " the moment anything compares the strings.",
        claims=[("no suffix starts with a space",
                 lambda rows, c: len(rows) > 5
                 and all(not r[2].startswith(" ") for r in rows))],
    ),
    dict(
        id=7, ledger="Q498", concept="E2", tier="2 - Sequences and strings",
        title="Origin and destination",
        prompt=(
            "For the first service of each line, the station it starts from"
            " and the station it ends at.\n\n"
            "Both come from `stops`, at opposite ends of the same sequence."
            " Six rows.\n\n"
            "Return: service_id, origin, destination"
        ),
        solution=("SELECT sp.service_id,"
                  " (SELECT st.name FROM stops x JOIN stations st"
                  " ON st.station_id = x.station_id"
                  " WHERE x.service_id = sp.service_id"
                  " ORDER BY x.stop_seq LIMIT 1),"
                  " (SELECT st.name FROM stops x JOIN stations st"
                  " ON st.station_id = x.station_id"
                  " WHERE x.service_id = sp.service_id"
                  " ORDER BY x.stop_seq DESC LIMIT 1)"
                  " FROM stops sp WHERE sp.service_id IN"
                  " (SELECT MIN(service_id) FROM services GROUP BY line_id)"
                  " GROUP BY sp.service_id"),
        trap_sql=("SELECT sp.service_id, MIN(st.name), MAX(st.name)"
                  " FROM stops sp JOIN stations st"
                  " ON st.station_id = sp.station_id"
                  " WHERE sp.service_id IN"
                  " (SELECT MIN(service_id) FROM services GROUP BY line_id)"
                  " GROUP BY sp.service_id"),
        note="MIN and MAX over the station NAME give you the alphabetically"
             " first and last station, which has nothing to do with the order"
             " the service calls at them. You want the name belonging to the"
             " lowest and highest stop_seq -- a different question, and one"
             " MIN cannot answer, because the value you want to compare on and"
             " the value you want back are different columns. FIRST_VALUE and"
             " LAST_VALUE do this too; so does a correlated subquery.",
        claims=[("six services, origin never equal to destination",
                 lambda rows, c: len(rows) == 6
                 and all(r[1] != r[2] for r in rows))],
    ),
    # ============================================ 3 Unpivot and set ops
    dict(
        id=8, ledger="Q499", concept="UNP", tier="3 - Unpivot and set ops",
        title="Each station's busiest quarter",
        prompt=(
            "For 2025, which quarter each station was busiest in, and the"
            " figure.\n\n"
            "station_footfall stores q1..q4 as four COLUMNS of one row, so"
            " they have to become four rows before you can compare them."
            " Report the quarter as 'q1'..'q4'. Sixty rows.\n\n"
            "Return: station_id, quarter, footfall"
        ),
        solution=("WITH u AS ("
                  " SELECT station_id, 'q1' q, q1 v FROM station_footfall"
                  " WHERE year = 2025 UNION ALL"
                  " SELECT station_id, 'q2', q2 FROM station_footfall"
                  " WHERE year = 2025 UNION ALL"
                  " SELECT station_id, 'q3', q3 FROM station_footfall"
                  " WHERE year = 2025 UNION ALL"
                  " SELECT station_id, 'q4', q4 FROM station_footfall"
                  " WHERE year = 2025)"
                  " SELECT station_id, q, v FROM u a WHERE v ="
                  " (SELECT MAX(v) FROM u b WHERE b.station_id = a.station_id)"),
        trap_sql=("SELECT station_id, 'q1',"
                  " MAX(q1, q2, q3, q4) FROM station_footfall"
                  " WHERE year = 2025"),
        note="MAX(a, b, c, d) with several arguments is the scalar MAX -- it"
             " gives you the biggest of four values on one row, which is the"
             " right NUMBER but tells you nothing about which column it came"
             " from. Getting the label back means turning the columns into"
             " rows first, so that 'which quarter' becomes an ordinary value"
             " you can select. Four SELECTs joined by UNION ALL is the manual"
             " unpivot; use UNION ALL, not UNION, or two stations with equal"
             " footfall collapse into one.",
        claims=[("every station once, and the figure is its own maximum",
                 lambda rows, c: len(rows) == 60
                 and len({r[0] for r in rows}) == 60)],
    ),
    dict(
        id=9, ledger="Q500", concept="S1", tier="3 - Unpivot and set ops",
        title="Travelled from, never travelled to",
        prompt=(
            "Stations that appear as a ticket's origin but never as any"
            " ticket's destination.\n\n"
            "to_station is NULL on open tickets. Five stations qualify -- if"
            " you get none, that is why.\n\n"
            "Return: station_id"
        ),
        solution=("SELECT DISTINCT from_station FROM tickets"
                  " EXCEPT SELECT to_station FROM tickets"
                  " WHERE to_station IS NOT NULL"),
        trap_sql=("SELECT DISTINCT from_station FROM tickets"
                  " WHERE from_station NOT IN"
                  " (SELECT to_station FROM tickets)"),
        note="NOT IN over a list containing NULL returns nothing at all. The"
             " engine answers 'is x absent?' by testing x <> each entry, and"
             " x <> NULL is NULL rather than true, so it can never conclude"
             " the station is missing. EXCEPT compares values instead and"
             " treats NULL as an ordinary one that simply never matches a"
             " station id, so it is safe either way. NOT EXISTS is safe for"
             " the same reason.",
        claims=[("five stations, none of them a destination",
                 lambda rows, c: len(rows) == 5
                 and not c.execute(
                     "SELECT 1 FROM tickets WHERE to_station IN (%s) LIMIT 1"
                     % ",".join(str(int(r[0])) for r in rows)).fetchall())],
    ),
    dict(
        id=10, ledger="Q501", concept="A3", tier="3 - Unpivot and set ops",
        title="Models that do not get everywhere",
        prompt=(
            "Models of rolling stock that have worked on some lines but not"
            " all six, with how many lines they have worked.\n\n"
            "A model that has worked all six does not qualify. Do not hard"
            " code the six.\n\n"
            "Return: model, lines"
        ),
        solution=("SELECT r.model, COUNT(DISTINCT s.line_id) FROM service_units"
                  " su JOIN rolling_stock r ON r.unit_id = su.unit_id"
                  " JOIN services s ON s.service_id = su.service_id"
                  " GROUP BY r.model"
                  " HAVING COUNT(DISTINCT s.line_id) < (SELECT COUNT(*)"
                  " FROM lines)"),
        trap_sql=("SELECT r.model, COUNT(s.line_id) FROM service_units su"
                  " JOIN rolling_stock r ON r.unit_id = su.unit_id"
                  " JOIN services s ON s.service_id = su.service_id"
                  " GROUP BY r.model"
                  " HAVING COUNT(s.line_id) < (SELECT COUNT(*) FROM lines)"),
        note="COUNT(s.line_id) counts ROWS -- one per working -- so a model"
             " that has run three thousand times on two lines scores 3000, not"
             " 2. The DISTINCT is what turns a count of workings into a count"
             " of lines. Note also that the subquery in HAVING runs once, not"
             " per group, because it mentions nothing from the outer query.",
        claims=[("every model listed is short of six lines",
                 lambda rows, c: len(rows) > 1
                 and all(1 <= r[1] < 6 for r in rows))],
    ),
    # ================================================= 4 Dates and times
    dict(
        id=11, ledger="Q502", concept="D1", tier="4 - Dates and times",
        title="The week's shape",
        prompt=(
            "How many services ran on each day of the week, Monday first.\n\n"
            "Label the days 'Mon' through 'Sun'. The timetable is thinner at"
            " weekends, so the numbers should fall away at the end.\n\n"
            "Return: day, services"
        ),
        solution=("SELECT CASE strftime('%w', run_date)"
                  " WHEN '1' THEN 'Mon' WHEN '2' THEN 'Tue' WHEN '3' THEN 'Wed'"
                  " WHEN '4' THEN 'Thu' WHEN '5' THEN 'Fri' WHEN '6' THEN 'Sat'"
                  " ELSE 'Sun' END, COUNT(*) FROM services"
                  " GROUP BY strftime('%w', run_date)"
                  " ORDER BY (strftime('%w', run_date) + 6) % 7"),
        trap_sql=("SELECT CASE strftime('%W', run_date)"
                  " WHEN '1' THEN 'Mon' WHEN '2' THEN 'Tue' WHEN '3' THEN 'Wed'"
                  " WHEN '4' THEN 'Thu' WHEN '5' THEN 'Fri' WHEN '6' THEN 'Sat'"
                  " ELSE 'Sun' END, COUNT(*) FROM services"
                  " GROUP BY strftime('%W', run_date)"
                  " ORDER BY (strftime('%W', run_date) + 6) % 7"),
        note="%w is the day of the week, 0 for Sunday through 6 for Saturday."
             " %W -- same letter, different case -- is the WEEK OF THE YEAR,"
             " 00 to 53. The trap swaps them and gets no error, just fifty-odd"
             " groups most of which fall into the ELSE branch. Note too that"
             " Monday-first ordering is arithmetic on the number, not"
             " alphabetical on the label: sort by the name and you get Fri,"
             " Mon, Sat, Sun, Thu, Tue, Wed.",
        claims=[("seven days, Monday first, weekend quietest",
                 lambda rows, c: len(rows) == 7 and rows[0][0] == 'Mon'
                 and rows[6][0] == 'Sun' and rows[6][1] < rows[0][1])],
    ),
    dict(
        id=12, ledger="Q503", concept="D2", tier="4 - Dates and times",
        title="The last Friday of each month",
        prompt=(
            "How many services ran on the last FRIDAY of each month.\n\n"
            "Build that date with modifiers rather than assuming which day it"
            " falls on. One row per month.\n\n"
            "Return: month, services"
        ),
        solution=("SELECT strftime('%Y-%m', run_date), COUNT(*) FROM services"
                  " WHERE run_date = date(run_date, 'start of month',"
                  " '+1 month', '-1 day', 'weekday 5', '-7 days') GROUP BY 1"),
        trap_sql=("SELECT strftime('%Y-%m', run_date), COUNT(*) FROM services"
                  " WHERE run_date = date(run_date, 'start of month',"
                  " '+1 month', '-1 day', 'weekday 5') GROUP BY 1"),
        note="Modifiers apply left to right. 'start of month', '+1 month',"
             " '-1 day' lands on the last day of the month -- there is no 'end"
             " of month' modifier, and an unrecognised one returns NULL rather"
             " than complaining. From there 'weekday 5' moves FORWARD to the"
             " next Friday, which is usually in the following month, so you"
             " step back a week. The catch the trap falls into: 'weekday 5'"
             " leaves the date alone when it is ALREADY a Friday, so the two"
             " versions agree in exactly those months and differ in the rest.",
        claims=[("one row per month, and all of them Fridays",
                 lambda rows, c: len(rows) == 18)],
    ),
    dict(
        id=13, ledger="Q504", concept="D1", tier="4 - Dates and times",
        title="The longest-serving staff",
        prompt=(
            "The five longest-serving members of staff as at 2026-06-30, in"
            " whole years.\n\n"
            "Longest first; break ties by staff_id.\n\n"
            "Return: staff_id, name, years"
        ),
        solution=("SELECT staff_id, name, CAST((julianday('2026-06-30')"
                  " - julianday(hired_on)) / 365.25 AS INTEGER) y FROM staff"
                  " ORDER BY y DESC, staff_id LIMIT 5"),
        trap_sql=("SELECT staff_id, name,"
                  " strftime('%Y', '2026-06-30') - strftime('%Y', hired_on) y"
                  " FROM staff ORDER BY y DESC, staff_id LIMIT 5"),
        note="Subtracting one year number from another counts CALENDAR years,"
             " not elapsed ones: somebody hired on the 31st of December 2005"
             " scores the same as somebody hired on the 1st of January 2005,"
             " though a year separates them. julianday() turns each date into"
             " a day count first, so the arithmetic is real. CAST truncates"
             " rather than rounds, which is what a completed year means -- 20.9"
             " years of service is 20.",
        claims=[("five rows, descending, all plausible tenures",
                 lambda rows, c: len(rows) == 5
                 and all(0 < r[2] < 30 for r in rows)
                 and rows[0][2] >= rows[-1][2])],
    ),
    dict(
        id=14, ledger="Q505", concept="D1", tier="4 - Dates and times",
        title="When services depart",
        prompt=(
            "How many services depart in each hour of the day.\n\n"
            "depart_time is TEXT in 'HH:MM'. Report the hour as a two-digit"
            " string, in order.\n\n"
            "Return: hour, services"
        ),
        solution=("SELECT SUBSTR(depart_time, 1, 2), COUNT(*) FROM services"
                  " GROUP BY 1 ORDER BY 1"),
        trap_sql=("SELECT strftime('%h', depart_time), COUNT(*)"
                  " FROM services GROUP BY 1 ORDER BY 1"),
        note="strftime('%H', ...) would also work here -- SQLite parses a bare"
             " 'HH:MM' as a time -- but the format characters are"
             " case-sensitive and there is no %h. An unrecognised one is not"
             " an error: strftime returns NULL, every row lands in the same"
             " group, and you get a single row that looks like a legitimate"
             " total. The wider point is that when a column is already a"
             " fixed-width string, SUBSTR needs no parsing and cannot be"
             " misspelt into silence. Reach for a date function when you need"
             " date ARITHMETIC, not the first two characters.",
        claims=[("several hours, no NULL, in ascending order",
                 lambda rows, c: len(rows) > 3
                 and all(r[0] is not None for r in rows)
                 and [r[0] for r in rows] == sorted(r[0] for r in rows))],
    ),
    # ================================================= 5 Joins and grain
    dict(
        id=15, ledger="Q506", concept="C2", tier="5 - Joins and grain",
        title="Tickets and incidents per line",
        prompt=(
            "One row per line: how many tickets it sold and how many incidents"
            " it had.\n\n"
            "Both hang off `services`, so a service with tickets AND incidents"
            " produces a row for every combination. The counts must survive"
            " that.\n\n"
            "Return: line_name, tickets, incidents"
        ),
        solution=("SELECT l.name, COUNT(DISTINCT t.ticket_id),"
                  " COUNT(DISTINCT i.incident_id) FROM lines l"
                  " JOIN services s ON s.line_id = l.line_id"
                  " LEFT JOIN tickets t ON t.service_id = s.service_id"
                  " LEFT JOIN incidents i ON i.service_id = s.service_id"
                  " GROUP BY l.name"),
        trap_sql=("SELECT l.name, COUNT(t.ticket_id), COUNT(i.incident_id)"
                  " FROM lines l JOIN services s ON s.line_id = l.line_id"
                  " LEFT JOIN tickets t ON t.service_id = s.service_id"
                  " LEFT JOIN incidents i ON i.service_id = s.service_id"
                  " GROUP BY l.name"),
        note="Two children of one parent multiply. A service with 20 tickets"
             " and 2 incidents yields 40 rows, so every ticket is counted"
             " twice and every incident twenty times. COUNT(DISTINCT id)"
             " rescues a COUNT because the duplicates carry the same id -- but"
             " nothing rescues a SUM, since the duplicated amounts are"
             " genuinely different rows. When you need a sum across two"
             " children, aggregate each separately and join the results.",
        claims=[("six lines, totals matching the tables",
                 lambda rows, c: len(rows) == 6
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM tickets").fetchone()[0]
                 and sum(r[2] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM incidents").fetchone()[0])],
    ),
    dict(
        id=16, ledger="Q507", concept="J2", tier="5 - Joins and grain",
        title="Stations nobody travels from",
        prompt=(
            "Stations that are not the origin of a single ticket.\n\n"
            "Write it as an outer join that keeps the non-matches rather than"
            " as a subquery.\n\n"
            "Return: station_id, name"
        ),
        solution=("SELECT st.station_id, st.name FROM stations st"
                  " LEFT JOIN tickets t ON t.from_station = st.station_id"
                  " WHERE t.ticket_id IS NULL"),
        trap_sql=("SELECT st.station_id, st.name FROM stations st"
                  " LEFT JOIN tickets t ON t.from_station = st.station_id"
                  " WHERE t.ticket_id IS NULL OR t.class = 'first'"),
        note="The anti-join: keep every row of the left table, then keep only"
             " those where the join found nothing. The test must be IS NULL on"
             " a column of the RIGHT table -- and it has to be a column that is"
             " never NULL in a real match, or you cannot tell 'no row' from 'a"
             " row with a blank in it'. A primary key is the safe choice. Note"
             " that any OTHER condition on the right table belongs in ON, not"
             " WHERE: put it in WHERE and the non-matching rows, which hold"
             " NULL in every right-hand column, fail it and vanish -- turning"
             " the outer join back into an inner one.",
        claims=[("none of them is a ticket origin",
                 lambda rows, c: len(rows) > 5
                 and not c.execute(
                     "SELECT 1 FROM tickets WHERE from_station IN (%s) LIMIT 1"
                     % ",".join(str(int(r[0])) for r in rows)).fetchall())],
    ),
    dict(
        id=17, ledger="Q508", concept="C2", tier="5 - Joins and grain",
        title="Seats each line has run",
        prompt=(
            "One row per line: the total seats it has run, counting every unit"
            " on every service.\n\n"
            "A service may be formed of more than one unit and each unit has"
            " its own seat count. Four tables, and no fan-out to undo.\n\n"
            "Return: line_name, seats"
        ),
        solution=("SELECT l.name, SUM(r.seats) FROM lines l"
                  " JOIN services s ON s.line_id = l.line_id"
                  " JOIN service_units su ON su.service_id = s.service_id"
                  " JOIN rolling_stock r ON r.unit_id = su.unit_id"
                  " GROUP BY l.name"),
        trap_sql=("SELECT l.name, COUNT(*) FROM lines l"
                  " JOIN services s ON s.line_id = l.line_id"
                  " JOIN service_units su ON su.service_id = s.service_id"
                  " JOIN rolling_stock r ON r.unit_id = su.unit_id"
                  " GROUP BY l.name"),
        note="The opposite case to question 15, and worth seeing next to it."
             " Here the chain is one-to-many all the way down a single path,"
             " so each row is one genuine unit on one genuine service and"
             " adding them up is honest -- no DISTINCT required. The tell that"
             " something is missing in the trap: it joins rolling_stock and"
             " then never selects a column from it. A join that contributes"
             " nothing is either redundant or forgotten.",
        claims=[("six lines, seats far exceeding the workings",
                 lambda rows, c: len(rows) == 6
                 and all(r[1] > 100000 for r in rows))],
    ),
    dict(
        id=18, ledger="Q509", concept="J1", tier="5 - Joins and grain",
        title="Staff at step-free stations",
        prompt=(
            "Staff whose base station is recorded as step-free, with the"
            " station's name.\n\n"
            "Return: staff_id, name, station"
        ),
        solution=("SELECT s.staff_id, s.name, st.name FROM staff s"
                  " JOIN stations st ON st.station_id = s.base_station"
                  " WHERE st.step_free = 1"),
        trap_sql=("SELECT s.staff_id, s.name, st.name FROM staff s"
                  " JOIN stations st ON st.station_id = s.base_station"
                  " WHERE st.step_free IS NOT 0"),
        note="step_free is 1, 0, or NULL at the four stations where nobody"
             " recorded it, and the three ways of saying 'not zero' disagree"
             " about those. <> 0 drops them, because NULL <> 0 is NULL rather"
             " than true -- so = 1 and <> 0 happen to agree here. IS NOT 0 is"
             " the odd one out: IS and IS NOT compare NULL as an ordinary"
             " value, so unrecorded counts as not-zero and two extra staff"
             " appear. Neither operator is wrong; they answer different"
             " questions. Say = 1 for known-yes, and IS NOT 1 for 'anything"
             " except yes, unknown included'.",
        claims=[("every station returned is step-free",
                 lambda rows, c: len(rows) > 5
                 and not c.execute(
                     "SELECT 1 FROM staff s JOIN stations st"
                     " ON st.station_id = s.base_station"
                     " WHERE st.step_free IS NOT 1 AND s.staff_id IN (%s)"
                     " LIMIT 1"
                     % ",".join(str(int(r[0])) for r in rows)).fetchall())],
    ),
    # ================================================= 6 Window functions
    dict(
        id=19, ledger="Q510", concept="W1", tier="6 - Window functions",
        title="Revenue accumulating",
        prompt=(
            "Ticket revenue by month, with a running total alongside.\n\n"
            "The running total on the last row should equal every ticket ever"
            " sold. Eighteen rows.\n\n"
            "Return: month, revenue, running_total"
        ),
        solution=("SELECT strftime('%Y-%m', sold_at) m, SUM(price_pence),"
                  " SUM(SUM(price_pence)) OVER (ORDER BY strftime('%Y-%m',"
                  " sold_at) ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)"
                  " FROM tickets GROUP BY m"),
        trap_sql=("SELECT strftime('%Y-%m', sold_at) m, SUM(price_pence),"
                  " SUM(SUM(price_pence)) OVER ()"
                  " FROM tickets GROUP BY m"),
        note="Two things are happening at once. The nesting -- SUM(SUM(x)) --"
             " is legal because the window runs AFTER the GROUP BY: the inner"
             " SUM makes the monthly total, the outer one accumulates across"
             " the rows those totals produced. And the frame is what makes it"
             " a running total rather than a grand one: an OVER () with no"
             " ORDER BY sees the whole partition on every row, so the trap"
             " prints the same number eighteen times.",
        claims=[("the last running total is every ticket",
                 lambda rows, c: max(r[2] for r in rows) == c.execute(
                     "SELECT SUM(price_pence) FROM tickets").fetchone()[0]
                 and len({r[2] for r in rows}) == len(rows))],
    ),
    dict(
        id=20, ledger="Q511", concept="W1", tier="6 - Window functions",
        title="A three-month view of incidents",
        prompt=(
            "Incidents by month, with the average over that month and the two"
            " before it.\n\n"
            "The first month averages just itself, the second averages two."
            " Round to two decimals.\n\n"
            "Return: month, incidents, rolling_avg"
        ),
        solution=("SELECT strftime('%Y-%m', reported_at) m, COUNT(*),"
                  " ROUND(AVG(COUNT(*)) OVER (ORDER BY strftime('%Y-%m',"
                  " reported_at) ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2)"
                  " FROM incidents GROUP BY m"),
        trap_sql=("SELECT strftime('%Y-%m', reported_at) m, COUNT(*),"
                  " ROUND(AVG(COUNT(*)) OVER (ORDER BY strftime('%Y-%m',"
                  " reported_at) ROWS BETWEEN 3 PRECEDING AND CURRENT ROW), 2)"
                  " FROM incidents GROUP BY m"),
        note="'2 PRECEDING AND CURRENT ROW' is three rows, not two -- the"
             " current row is one of them. Off-by-one here is silent: every"
             " value stays plausible, just smoothed over the wrong span. The"
             " frame also shrinks at the start rather than returning NULL,"
             " which is usually what you want for a rolling average but does"
             " mean the first rows are averaging fewer months than the rest.",
        claims=[("the first row's average equals its own count",
                 lambda rows, c: len(rows) == 18
                 and abs(rows[0][2] - rows[0][1]) < 0.005
                 and abs(rows[1][2] - (rows[0][1] + rows[1][1]) / 2) < 0.01)],
    ),
    dict(
        id=21, ledger="Q512", concept="W2", tier="6 - Window functions",
        title="Two ways to rank a tie",
        prompt=(
            "The twenty units with the most seats, each with its position by"
            " both RANK and DENSE_RANK.\n\n"
            "Several units share a seat count, which is the entire point --"
            " the two columns must differ somewhere. Most seats first, ties"
            " broken by unit_id.\n\n"
            "Return: unit_id, seats, rank, dense_rank"
        ),
        solution=("SELECT unit_id, seats, RANK() OVER (ORDER BY seats DESC),"
                  " DENSE_RANK() OVER (ORDER BY seats DESC)"
                  " FROM rolling_stock ORDER BY seats DESC, unit_id LIMIT 20"),
        trap_sql=("SELECT unit_id, seats,"
                  " ROW_NUMBER() OVER (ORDER BY seats DESC),"
                  " DENSE_RANK() OVER (ORDER BY seats DESC)"
                  " FROM rolling_stock ORDER BY seats DESC, unit_id LIMIT 20"),
        note="All three number the rows; they differ only in how they treat"
             " ties. ROW_NUMBER ignores them and counts 1, 2, 3, 4 -- so two"
             " units with identical seats get different numbers, decided by"
             " nothing you asked for. RANK gives tied rows the same number and"
             " then SKIPS: 1, 1, 3. DENSE_RANK gives them the same number and"
             " carries on: 1, 1, 2. Use ROW_NUMBER only when you genuinely"
             " want an arbitrary tiebreak, as in question 25.",
        claims=[("rank and dense_rank actually diverge",
                 lambda rows, c: len(rows) == 20
                 and any(r[2] != r[3] for r in rows)
                 and any(r[2] == r2[2] for r in rows for r2 in rows
                         if r[0] != r2[0]))],
    ),
    dict(
        id=22, ledger="Q513", concept="W3", tier="6 - Window functions",
        title="Each unit's share of its model",
        prompt=(
            "For every unit, how many services it has worked and what"
            " percentage that is of its MODEL's total workings.\n\n"
            "Within each model the percentages add to 100. Round to two"
            " decimals.\n\n"
            "Return: unit_id, model, workings, pct_of_model"
        ),
        solution=("SELECT su.unit_id, r.model, COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER"
                  " (PARTITION BY r.model), 2) FROM service_units su"
                  " JOIN rolling_stock r ON r.unit_id = su.unit_id"
                  " GROUP BY su.unit_id, r.model"),
        trap_sql=("SELECT su.unit_id, r.model, COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)"
                  " FROM service_units su"
                  " JOIN rolling_stock r ON r.unit_id = su.unit_id"
                  " GROUP BY su.unit_id, r.model"),
        note="PARTITION BY is what decides the denominator. With it, the"
             " window restarts for each model and every unit is measured"
             " against its own kind; without it there is one partition holding"
             " everything, and you get each unit's share of the WHOLE fleet --"
             " numbers that look reasonable and sum to 100 across the entire"
             " result rather than within each model. PARTITION BY divides the"
             " rows up; ORDER BY, which this question does not want, decides"
             " how much of a partition each row can see.",
        claims=[("every model's shares add to 100",
                 lambda rows, c: len(rows) > 20 and all(
                     abs(sum(r[3] for r in rows if r[1] == m) - 100) < 0.5
                     for m in {r[1] for r in rows}))],
    ),
    dict(
        id=23, ledger="Q514", concept="W2", tier="6 - Window functions",
        title="Where a station sits in the network",
        prompt=(
            "Every station's total 2025 footfall, with the fraction of"
            " stations at or below it -- quietest first, so the busiest"
            " station scores 1.0.\n\n"
            "Round to three decimals. Sixty rows.\n\n"
            "Return: station_id, footfall, cume_dist"
        ),
        solution=("SELECT station_id, q1 + q2 + q3 + q4 f,"
                  " ROUND(CUME_DIST() OVER (ORDER BY q1 + q2 + q3 + q4), 3)"
                  " FROM station_footfall WHERE year = 2025"),
        trap_sql=("SELECT station_id, q1 + q2 + q3 + q4 f,"
                  " ROUND(PERCENT_RANK() OVER (ORDER BY q1 + q2 + q3 + q4), 3)"
                  " FROM station_footfall WHERE year = 2025"),
        note="The two percentile functions look interchangeable and are not."
             " CUME_DIST is the proportion of rows at or below this one, so it"
             " runs from 1/n up to exactly 1.0. PERCENT_RANK is (rank - 1) /"
             " (n - 1), so it runs from exactly 0.0 up to 1.0 -- the first row"
             " scores zero rather than 1/60. Both end at 1.0, which is why the"
             " swap is easy to miss; check the FIRST row to tell them apart.",
        claims=[("sixty rows, the last exactly 1.0 and the first not zero",
                 lambda rows, c: len(rows) == 60
                 and abs(max(r[2] for r in rows) - 1.0) < 1e-9
                 and min(r[2] for r in rows) > 0)],
    ),
    dict(
        id=24, ledger="Q515", concept="W3", tier="6 - Window functions",
        title="Each line's share of the timetable",
        prompt=(
            "One row per line: how many services it ran, and what percentage"
            " of all services that is.\n\n"
            "The percentages add to 100. Round to two decimals.\n\n"
            "Return: line_name, services, pct"
        ),
        solution=("SELECT l.name, COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)"
                  " FROM services s JOIN lines l ON l.line_id = s.line_id"
                  " GROUP BY l.name"),
        trap_sql=("SELECT l.name, COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM lines), 2)"
                  " FROM services s JOIN lines l ON l.line_id = s.line_id"
                  " GROUP BY l.name"),
        note="The total you need is the sum of the numbers you just computed,"
             " and a window over the grouped rows reaches it without a second"
             " pass over the table: SUM(COUNT(*)) OVER () adds up the six"
             " counts. The alternative is a scalar subquery counting services"
             " again, which works but reads the table twice -- and, as the"
             " trap shows, is easy to point at the wrong table entirely. If"
             " the percentages do not sum to 100, the denominator is wrong.",
        claims=[("six lines summing to 100 percent",
                 lambda rows, c: len(rows) == 6
                 and abs(sum(r[2] for r in rows) - 100) < 0.05
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM services").fetchone()[0])],
    ),
    dict(
        id=25, ledger="Q516", concept="W2", tier="6 - Window functions",
        title="The two best days each line had",
        prompt=(
            "For each line, its two highest-earning services by ticket"
            " revenue.\n\n"
            "Twelve rows. Break ties by the lower service_id. A window"
            " function cannot go in WHERE, which shapes the whole query.\n\n"
            "Return: line_id, service_id, revenue"
        ),
        solution=("SELECT line_id, service_id, rev FROM"
                  " (SELECT s.line_id, s.service_id, SUM(t.price_pence) rev,"
                  " ROW_NUMBER() OVER (PARTITION BY s.line_id"
                  " ORDER BY SUM(t.price_pence) DESC, s.service_id) rn"
                  " FROM services s JOIN tickets t"
                  " ON t.service_id = s.service_id GROUP BY s.service_id)"
                  " WHERE rn <= 2"),
        trap_sql=("SELECT s.line_id, s.service_id, SUM(t.price_pence) rev"
                  " FROM services s JOIN tickets t"
                  " ON t.service_id = s.service_id GROUP BY s.service_id"
                  " ORDER BY rev DESC LIMIT 12"),
        note="Top-N per group, the standard shape. WHERE runs before the"
             " window function does, so `WHERE ROW_NUMBER() OVER (...) <= 2`"
             " is not merely disallowed, it is meaningless -- the numbering"
             " does not exist yet. Compute it in a subquery and filter"
             " outside. The trap reaches for ORDER BY ... LIMIT 12 instead,"
             " which gives the twelve best services overall: the busiest line"
             " can take every slot and a quiet line appear not at all.",
        claims=[("two rows for each of the six lines",
                 lambda rows, c: len(rows) == 12
                 and all(sum(1 for r in rows if r[0] == lid) == 2
                         for lid in {r[0] for r in rows})
                 and len({r[0] for r in rows}) == 6)],
    ),
    dict(
        id=26, ledger="Q517", concept="W1", tier="6 - Window functions",
        title="Stops still to come",
        prompt=(
            "For service 100, each stop and how many stops remain after it.\n"
            "\nThe last stop has 0 remaining. This needs a frame that looks"
            " FORWARD, which is not what ORDER BY gives you by default.\n\n"
            "Return: stop_seq, remaining"
        ),
        solution=("SELECT stop_seq, COUNT(*) OVER (ORDER BY stop_seq"
                  " ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING) - 1"
                  " FROM stops WHERE service_id = 100"),
        trap_sql=("SELECT stop_seq, COUNT(*) OVER (ORDER BY stop_seq"
                  " ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) - 1"
                  " FROM stops WHERE service_id = 100"),
        note="Frames run in both directions, and the default only goes one."
             " UNBOUNDED PRECEDING to CURRENT ROW counts what you have already"
             " passed; CURRENT ROW to UNBOUNDED FOLLOWING counts what is"
             " ahead, including the current row -- hence the - 1. The trap's"
             " frame is the default one, so it counts stops COMPLETED, which"
             " is a mirror image: right at neither end, and plausible in the"
             " middle. Sanity-check the first and last rows of any frame.",
        claims=[("ten stops, counting down to nought",
                 lambda rows, c: len(rows) == 10
                 and rows[-1][1] == 0 and rows[0][1] == 9)],
    ),
    # ================================================== 7 Query efficiency
    # Each starter joins two or three tables, so the plan runs to four or five
    # lines and the first job is finding which one is costing you. Graded on
    # the plan as well as the rows; Reset restores the starter.
    dict(
        id=27, ledger="Q518", concept="X1", tier="7 - Query efficiency",
        title="A guard that costs four seconds",
        prompt=(
            "How many tickets were sold on lines 3 and 4, one row per line.\n\n"
            "The editor's query wraps the ticket side of the JOIN in COALESCE"
            " -- defensive, harmless-looking, and it takes about four SECONDS."
            " tickets.service_id is indexed. Your plan must not contain"
            " 'SCAN'.\n\n"
            "Return: line_id, tickets"
        ),
        solution=("SELECT s.line_id, COUNT(*) FROM services s"
                  " JOIN tickets t ON s.service_id = t.service_id"
                  " WHERE s.line_id IN (3, 4) GROUP BY 1"),
        trap_sql=("SELECT s.line_id, COUNT(*) FROM services s"
                  " JOIN tickets t ON s.service_id = COALESCE(t.service_id, -1)"
                  " WHERE s.line_id IN (3, 4) GROUP BY 1"),
        starter_sql=("SELECT s.line_id, COUNT(*) FROM services s"
                     " JOIN tickets t"
                     " ON s.service_id = COALESCE(t.service_id, -1)"
                     " WHERE s.line_id IN (3, 4) GROUP BY 1"),
        plan_forbids=("SCAN",),
        note="Everyone learns that a function on a filtered column blocks the"
             " index. The same is true of a JOIN KEY, and it costs far more --"
             " a filter is evaluated once per row, but a join key is probed"
             " once per row OF THE OTHER TABLE. With COALESCE wrapped round"
             " it, SQLite cannot look a ticket up by service_id at all, so for"
             " every one of the 3,600 services on those two lines it reads the"
             " entire ticket table: 3,600 x 34,622 comparisons. Remove the"
             " guard and the same query is four thousand times faster. The"
             " guard was never needed -- a NULL service_id would not match"
             " anything anyway, which is what an inner join already means.",
        claims=[("two lines, totals matching the unguarded join",
                 lambda rows, c: len(rows) == 2
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM tickets t JOIN services s"
                     " ON s.service_id = t.service_id"
                     " WHERE s.line_id IN (3, 4)").fetchone()[0])],
    ),
    dict(
        id=28, ledger="Q519", concept="X7", tier="7 - Query efficiency",
        title="When EXISTS is the slow one",
        prompt=(
            "The stations that line 2 calls at.\n\n"
            "The editor's query uses a correlated EXISTS, which is normally"
            " the tidy way to write this. Here it is ten times slower than the"
            " join it replaced. Your plan must not contain 'CORRELATED SCALAR"
            " SUBQUERY'.\n\n"
            "Return: station_id, name"
        ),
        solution=("SELECT DISTINCT st.station_id, st.name FROM stations st"
                  " JOIN stops sp ON sp.station_id = st.station_id"
                  " JOIN services s ON s.service_id = sp.service_id"
                  " WHERE s.line_id = 2"),
        trap_sql=("SELECT st.station_id, st.name FROM stations st"
                  " WHERE EXISTS (SELECT 1 FROM stops sp"
                  " JOIN services s ON s.service_id = sp.service_id"
                  " WHERE sp.station_id = st.station_id AND s.line_id = 2)"),
        starter_sql=("SELECT st.station_id, st.name FROM stations st"
                     " WHERE EXISTS (SELECT 1 FROM stops sp"
                     " JOIN services s ON s.service_id = sp.service_id"
                     " WHERE sp.station_id = st.station_id AND s.line_id = 2)"),
        plan_forbids=("CORRELATED SCALAR SUBQUERY",),
        note="A correlated subquery runs once per outer row, and it can only"
             " start from the correlation you gave it. Here that is"
             " station_id, so all 60 stations are walked and each one's ~1,600"
             " stops are read and checked against services -- 96,000 rows"
             " touched to answer a question about one line. The join is free"
             " to choose its own driving table, and idx_services_line takes it"
             " straight to line 2's 1,800 services. The lesson is not 'joins"
             " beat EXISTS' -- it is that a correlated subquery is LOCKED to"
             " the correlation, so when the selective condition lives"
             " somewhere else, it cannot get at it.",
        claims=[("ten stations, all of them on line 2",
                 lambda rows, c: len(rows) == 10
                 and not c.execute(
                     "SELECT 1 FROM stations st WHERE st.station_id IN (%s)"
                     " AND NOT EXISTS (SELECT 1 FROM stops sp JOIN services s"
                     " ON s.service_id = sp.service_id"
                     " WHERE sp.station_id = st.station_id AND s.line_id = 2)"
                     " LIMIT 1"
                     % ",".join(str(int(r[0])) for r in rows)).fetchall())],
    ),
    dict(
        id=29, ledger="Q520", concept="X2", tier="7 - Query efficiency",
        title="Fifty rows after grouping eleven thousand",
        prompt=(
            "The 50 most recent services with a count of the tickets each"
            " sold. Most recent first, ties broken by service_id.\n\n"
            "The editor's query groups all 11,107 services and sorts the lot"
            " to hand back 50. services.run_date is indexed. Your plan must"
            " not contain 'B-TREE FOR ORDER BY'.\n\n"
            "Return: service_id, run_date, tickets"
        ),
        solution=("SELECT s.service_id, s.run_date, (SELECT COUNT(*)"
                  " FROM tickets t WHERE t.service_id = s.service_id)"
                  " FROM services s ORDER BY s.run_date DESC, s.service_id"
                  " LIMIT 50"),
        trap_sql=("SELECT s.service_id, s.run_date, COUNT(t.ticket_id)"
                  " FROM services s LEFT JOIN tickets t"
                  " ON t.service_id = s.service_id"
                  " GROUP BY s.service_id, s.run_date"
                  " ORDER BY s.run_date DESC, s.service_id LIMIT 50"),
        starter_sql=("SELECT s.service_id, s.run_date, COUNT(t.ticket_id)"
                     " FROM services s LEFT JOIN tickets t"
                     " ON t.service_id = s.service_id"
                     " GROUP BY s.service_id, s.run_date"
                     " ORDER BY s.run_date DESC, s.service_id LIMIT 50"),
        plan_forbids=("B-TREE FOR ORDER BY",),
        note="A LIMIT can only stop early if the rows arrive in the right"
             " order already. GROUP BY builds its result before anything is"
             " sorted, so the whole grouped set exists before the ORDER BY can"
             " run and the LIMIT saves nothing. Moving the count into a"
             " correlated subquery removes the GROUP BY entirely: services can"
             " then be walked backwards along idx_services_date, and the query"
             " stops after fifty -- so the subquery runs fifty times, not"
             " eleven thousand. This is the mirror of question 28. There the"
             " correlated form was locked to the wrong table; here it is the"
             " thing that lets the index do the ordering.",
        claims=[("fifty rows, newest first",
                 lambda rows, c: len(rows) == 50
                 and rows[0][1] == c.execute(
                     "SELECT MAX(run_date) FROM services").fetchone()[0])],
    ),
    dict(
        id=30, ledger="Q521", concept="C2", tier="7 - Query efficiency",
        title="The join that pays for itself twice",
        prompt=(
            "Tickets sold per line, one row per line.\n\n"
            "The editor's query joins `stops` as well -- it adds no column to"
            " the result, but it multiplies every service by its seven or"
            " eight stops, and the COUNT(DISTINCT) then exists only to undo"
            " that. Your plan must not contain 'count(DISTINCT)'.\n\n"
            "Return: line_name, tickets"
        ),
        solution=("SELECT l.name, COUNT(t.ticket_id) FROM lines l"
                  " JOIN services s ON s.line_id = l.line_id"
                  " LEFT JOIN tickets t ON t.service_id = s.service_id"
                  " GROUP BY l.name"),
        trap_sql=("SELECT l.name, COUNT(DISTINCT t.ticket_id) FROM lines l"
                  " JOIN services s ON s.line_id = l.line_id"
                  " JOIN stops sp ON sp.service_id = s.service_id"
                  " LEFT JOIN tickets t ON t.service_id = s.service_id"
                  " GROUP BY l.name"),
        starter_sql=("SELECT l.name, COUNT(DISTINCT t.ticket_id) FROM lines l"
                     " JOIN services s ON s.line_id = l.line_id"
                     " JOIN stops sp ON sp.service_id = s.service_id"
                     " LEFT JOIN tickets t ON t.service_id = s.service_id"
                     " GROUP BY l.name"),
        plan_forbids=("count(DISTINCT)",),
        note="COUNT(DISTINCT) in a plan is worth treating as a question rather"
             " than a feature: it means rows are arriving more than once, and"
             " something has to hold them all in a temp b-tree to work out"
             " which are duplicates. Usually the cause is a join that fans the"
             " result out. Here `stops` contributes no column at all -- it"
             " multiplies each service by its number of calls, roughly eight"
             " times the rows, purely so the DISTINCT can take them away"
             " again. Drop the join and the DISTINCT becomes unnecessary"
             " together with it. Fifteen times faster, same six numbers.",
        claims=[("six lines, totalling every ticket",
                 lambda rows, c: len(rows) == 6
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM tickets").fetchone()[0])],
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
