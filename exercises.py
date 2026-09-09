"""Practice exercises with reference solutions, used by the GUI to grade answers.

These 30 questions (ledger Q402-Q431) run on a NEW schema: a regional railway.
The college is retired. Six consecutive sets on one schema had made the
questions feel alike whatever they were about, so this one is shaped
differently rather than merely being about something else.

WHAT IS NEW ABOUT THE SHAPE
---------------------------
The central fact is an ORDERED SEQUENCE inside a parent. `stops` is keyed on
(service_id, stop_seq), so every stop knows where it sits in its own journey.
That makes a whole family of questions natural instead of contrived: the first
and last station, the next station, the gap since the previous one, the route
written out as a single string. Those need LAG, LEAD, frame clauses,
FIRST_VALUE and GROUP_CONCAT -- and none of the previous schemas gave them
anywhere honest to live.

Three more shapes chosen to reach concepts no earlier set covered:

  station_footfall   one row per station-year with FOUR QUARTER COLUMNS. Making
                     it long again is an unpivot, and SQL has no operator for
                     one -- it is UNION ALL or nothing.
  tickets.price_pence   money as INTEGER, so shares and averages meet integer
                     division rather than floating point
  tickets.class      a category whose natural order is not alphabetical, so
                     sorting it needs CASE inside ORDER BY

Recursion is deliberately light -- one question. It has had eight across the
last three sets.

THE EFFICIENCY STAGE NOW STARTS FILLED IN
-----------------------------------------
Each of the last six opens with a query already in the editor that returns the
RIGHT answer by a slow route. Nothing to work out about what to select; the
task is only to improve the plan. Press F6 to see what it is doing now, change
it, press F6 again. Grading checks the plan as well as the rows, so the query
you were given is by definition not yet a pass.

  concept   the mistake or technique it drills
  solution  one correct answer
  starter_sql  what the editor opens with (efficiency questions only)
  trap_sql  the tempting WRONG query -- check_questions.py asserts the grader
            rejects it
  note      the lesson, shown once you get it right
  claims    facts the prompt asserts, re-checked against the live database

Grading compares your result as an unordered multiset of rows, floats rounded
to 2 decimals. Row order never matters; column order does.

Spoiler warning: the reference SQL is in this file.
"""

# Each efficiency question's slow-but-correct form, written once and used both
# as the editor's starting point and as the trap the grader must reject.
SLOW_YEAR = ("SELECT COUNT(*) FROM services"
             " WHERE strftime('%Y', run_date) = '2025'")
SLOW_SORT = ("SELECT ticket_id FROM tickets"
             " ORDER BY class, price_pence + 0, ticket_id LIMIT 20")
SLOW_COVER = ("SELECT class, price_pence FROM tickets"
              " WHERE class = 'first' AND sold_at IS NOT NULL")
SLOW_LIKE = ("SELECT staff_id, name FROM staff"
             " WHERE substr(name, 1, 4) = 'Alan'")
SLOW_ANTI = ("SELECT COUNT(*) FROM stations st"
             " LEFT JOIN stops s ON s.station_id = st.station_id"
             " WHERE s.service_id IS NULL")
SLOW_GROUP = ("SELECT run_date, COUNT(*) FROM services"
              " GROUP BY run_date || ''")

EXERCISES = [
    # ============================================================ 1 Warm-up
    dict(
        id=1, ledger="Q402", concept="N1", tier="1 - Warm-up",
        title="Revenue in pounds",
        prompt=(
            "Total ticket revenue, in POUNDS, to two decimal places.\n\n"
            "price_pence is an INTEGER column holding whole pence. One table,"
            " no joins.\n\n"
            "Return: one row, one column: the total in pounds"
        ),
        solution="SELECT ROUND(SUM(price_pence) / 100.0, 2) FROM tickets",
        trap_sql="SELECT ROUND(SUM(price_pence) / 100, 2) FROM tickets",
        note="Both operands are integers, so / 100 is INTEGER division and the"
             " pence are discarded before ROUND ever sees the value -- rounding"
             " something that has already been truncated cannot put the"
             " decimals back. Writing 100.0 makes the whole expression float."
             " The tell is a 'two decimal place' answer that comes out whole.",
        claims=[("the pounds figure is not a whole number",
                 lambda rows, c: len(rows) == 1
                 and abs(rows[0][0] - round(rows[0][0])) > 0.001)],
    ),
    dict(
        id=2, ledger="Q403", concept="N2", tier="1 - Warm-up",
        title="Classes in price order",
        prompt=(
            "The three ticket classes with how many were sold, ordered from"
            " most expensive class to cheapest: first, then standard, then"
            " advance.\n\n"
            "That is not alphabetical order, and it is not the order of any"
            " column in the table. One table, no joins.\n\n"
            "Return: class, tickets, sort_order  (1, 2, 3 for first, standard,\n"
            "advance -- the grader ignores row order, so the ordering has to be a\n"
            "VALUE you return)"
        ),
        solution=("SELECT class, COUNT(*), CASE class WHEN 'first' THEN 1"
                  " WHEN 'standard' THEN 2 ELSE 3 END AS ord"
                  " FROM tickets GROUP BY class ORDER BY ord"),
        trap_sql=("SELECT class, COUNT(*), 1 FROM tickets GROUP BY class"
                  " ORDER BY class"),
        note="ORDER BY takes an expression, not just a column, so a CASE is how"
             " you impose an order the data does not contain. Alphabetically"
             " these sort advance, first, standard -- which is meaningless. The"
             " grader ignores row order, so this one is graded on the ORDER"
             " COLUMN being right: the CASE has to appear in the SELECT list as"
             " well, and the trap has no such column at all.",
        claims=[("three classes",
                 lambda rows, c: len(rows) == 3)],
    ),
    dict(
        id=3, ledger="Q404", concept="C7", tier="1 - Warm-up",
        title="Step-free access, surveyed and not",
        prompt=(
            "Classify every station by its step_free value and count them:\n"
            "  'step free'     step_free is 1\n"
            "  'not step free' step_free is 0\n"
            "  'not surveyed'  step_free is NULL\n\n"
            "All 60 stations land in exactly one bucket. One table, no"
            " joins.\n\n"
            "Return: access, stations"
        ),
        solution=("SELECT CASE WHEN step_free IS NULL THEN 'not surveyed'"
                  " WHEN step_free = 1 THEN 'step free'"
                  " ELSE 'not step free' END, COUNT(*)"
                  " FROM stations GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN step_free = 1 THEN 'step free'"
                  " ELSE 'not step free' END, COUNT(*)"
                  " FROM stations GROUP BY 1"),
        note="The trap has no branch for NULL, so the three unsurveyed stations"
             " fail the = 1 test and fall into ELSE, silently reported as"
             " step-free-less rather than unknown. NULL does not compare as"
             " unequal -- it does not compare at all, so it lands wherever ELSE"
             " points. Test IS NULL FIRST: it is the only branch that can catch"
             " it deliberately.",
        claims=[("three buckets covering all 60 stations",
                 lambda rows, c: len(rows) == 3
                 and sum(r[1] for r in rows) == 60)],
    ),
    dict(
        id=4, ledger="Q405", concept="N3", tier="1 - Warm-up",
        title="Stations named after their town",
        prompt=(
            "Stations whose name is the town name plus a suffix -- that is, the"
            " name starts with the town and is longer than it.\n\n"
            "A station whose name IS exactly its town does not qualify.\n\n"
            "Return: station_id, name, town, suffix  (the part after the town"
            " and the space)"
        ),
        solution=("SELECT station_id, name, town,"
                  " substr(name, length(town) + 2) FROM stations"
                  " WHERE name LIKE town || ' %'"),
        trap_sql=("SELECT station_id, name, town,"
                  " substr(name, length(town) + 2) FROM stations"
                  " WHERE name LIKE town || '%'"),
        note="Two string functions doing different jobs. LIKE builds its"
             " pattern by concatenation, so the town becomes the prefix -- and"
             " the space before % is what excludes a station whose name is"
             " exactly the town. substr(x, n) with no third argument returns"
             " everything from position n onward; length(town) + 2 skips the"
             " town and the space, because SQLite strings are 1-indexed.",
        claims=[("every row's name really is longer than its town",
                 lambda rows, c: len(rows) > 0
                 and all(len(r[1]) > len(r[2]) and r[3] for r in rows))],
    ),
    # ============================================== 2 Sequences and strings
    dict(
        id=5, ledger="Q406", concept="G1", tier="2 - Sequences and strings",
        title="The whole route on one line",
        prompt=(
            "For service 1, its route as a SINGLE string: every station it"
            " calls at, in stop order, joined with ' -> '.\n\n"
            "One row, one column.\n\n"
            "Return: route"
        ),
        solution=("SELECT group_concat(st.name, ' -> ') FROM"
                  " (SELECT station_id FROM stops WHERE service_id = 1"
                  " ORDER BY stop_seq) sp"
                  " JOIN stations st ON st.station_id = sp.station_id"),
        trap_sql=("SELECT group_concat(st.name) FROM stops sp"
                  " JOIN stations st ON st.station_id = sp.station_id"
                  " WHERE sp.service_id = 1"),
        note="GROUP_CONCAT collapses many rows into one string, and its second"
             " argument is the separator -- the default is a bare comma. Order"
             " is the subtle part: GROUP_CONCAT has no ORDER BY of its own in"
             " SQLite, so the rows must arrive already sorted, which is why the"
             " stops are ordered in a subquery before the join. Sort after the"
             " concatenation and it is far too late.",
        claims=[("one row containing the arrow separator",
                 lambda rows, c: len(rows) == 1 and ' -> ' in rows[0][0]),
                ("it names as many stations as the service has stops",
                 lambda rows, c: rows[0][0].count(' -> ') + 1 == c.execute(
                     "SELECT COUNT(*) FROM stops WHERE service_id = 1"
                 ).fetchone()[0])],
    ),
    dict(
        id=6, ledger="Q407", concept="W2", tier="2 - Sequences and strings",
        title="Where each line starts and ends",
        prompt=(
            "For each LINE, the station its services start from and the station"
            " they end at.\n\n"
            "Every service on a line calls at the same stations in the same"
            " order, so take any one service on it -- the lowest service_id --"
            " and report its first and last stop.\n\n"
            "Return: line_name, origin, destination"
        ),
        solution=("WITH pick AS (SELECT l.line_id, l.name AS line_name,"
                  " MIN(s.service_id) AS sid FROM lines l"
                  " JOIN services s ON s.line_id = l.line_id"
                  " WHERE s.cancelled = 0 GROUP BY 1, 2)"
                  " SELECT p.line_name,"
                  " (SELECT st.name FROM stops sp"
                  " JOIN stations st ON st.station_id = sp.station_id"
                  " WHERE sp.service_id = p.sid"
                  " ORDER BY sp.stop_seq LIMIT 1),"
                  " (SELECT st.name FROM stops sp"
                  " JOIN stations st ON st.station_id = sp.station_id"
                  " WHERE sp.service_id = p.sid"
                  " ORDER BY sp.stop_seq DESC LIMIT 1)"
                  " FROM pick p"),
        trap_sql=("WITH pick AS (SELECT l.line_id, l.name AS line_name,"
                  " MIN(s.service_id) AS sid FROM lines l"
                  " JOIN services s ON s.line_id = l.line_id"
                  " WHERE s.cancelled = 0 GROUP BY 1, 2)"
                  " SELECT p.line_name,"
                  " (SELECT MIN(st.name) FROM stops sp"
                  " JOIN stations st ON st.station_id = sp.station_id"
                  " WHERE sp.service_id = p.sid),"
                  " (SELECT MAX(st.name) FROM stops sp"
                  " JOIN stations st ON st.station_id = sp.station_id"
                  " WHERE sp.service_id = p.sid)"
                  " FROM pick p"),
        note="First and last mean first and last BY STOP_SEQ, not"
             " alphabetically. MIN(name) and MAX(name) give the"
             " alphabetically first and last station on the route, which is a"
             " different question with a plausible-looking answer. When a"
             " sequence column exists, order by it and take one row.",
        claims=[("six lines, origin and destination differing on each",
                 lambda rows, c: len(rows) == 6
                 and all(r[1] != r[2] for r in rows))],
    ),
    dict(
        id=7, ledger="Q408", concept="W3", tier="2 - Sequences and strings",
        title="Minutes between stops",
        prompt=(
            "For service 1, each stop with the number of scheduled minutes"
            " since the PREVIOUS stop on that journey.\n\n"
            "The first stop has nothing before it, so its gap is NULL. Times"
            " are 'HH:MM' and no service crosses midnight.\n\n"
            "Return: stop_seq, sched_arrive, minutes_since_previous"
        ),
        solution=("SELECT stop_seq, sched_arrive,"
                  " (CAST(substr(sched_arrive, 1, 2) AS INTEGER) * 60"
                  " + CAST(substr(sched_arrive, 4, 2) AS INTEGER))"
                  " - LAG(CAST(substr(sched_arrive, 1, 2) AS INTEGER) * 60"
                  " + CAST(substr(sched_arrive, 4, 2) AS INTEGER))"
                  " OVER (ORDER BY stop_seq)"
                  " FROM stops WHERE service_id = 1"),
        trap_sql=("SELECT stop_seq, sched_arrive,"
                  " sched_arrive - LAG(sched_arrive) OVER (ORDER BY stop_seq)"
                  " FROM stops WHERE service_id = 1"),
        note="'HH:MM' is text, and subtracting text coerces it to a number --"
             " '09:47' reads as 9 and stops at the colon, so you get a"
             " difference in whole hours, usually 0. Convert to minutes first:"
             " hours * 60 + minutes, pulled out with substr and CAST. Note the"
             " conversion has to be written twice, once inside LAG and once"
             " outside, because LAG takes the VALUE you want from the previous"
             " row -- it cannot reach back and transform it afterwards.",
        claims=[("one row per stop, exactly one NULL gap",
                 lambda rows, c: sum(1 for r in rows if r[2] is None) == 1),
                ("every other gap is positive",
                 lambda rows, c: all(r[2] > 0 for r in rows
                                     if r[2] is not None))],
    ),
    dict(
        id=8, ledger="Q409", concept="W3", tier="2 - Sequences and strings",
        title="The next station on the journey",
        prompt=(
            "For service 1, each stop with the name of the station it calls at"
            " NEXT.\n\n"
            "The final stop has nothing after it, so its next station is"
            " NULL.\n\n"
            "Return: stop_seq, station, next_station"
        ),
        solution=("SELECT sp.stop_seq, st.name,"
                  " LEAD(st.name) OVER (ORDER BY sp.stop_seq)"
                  " FROM stops sp JOIN stations st"
                  " ON st.station_id = sp.station_id WHERE sp.service_id = 1"),
        trap_sql=("SELECT sp.stop_seq, st.name,"
                  " LAG(st.name) OVER (ORDER BY sp.stop_seq)"
                  " FROM stops sp JOIN stations st"
                  " ON st.station_id = sp.station_id WHERE sp.service_id = 1"),
        note="LEAD looks forward, LAG looks back -- otherwise identical. Both"
             " return NULL where there is no neighbour, so the NULL moves from"
             " the last row to the first depending on which you used, and that"
             " is the quickest way to tell them apart when the answer looks"
             " almost right.",
        claims=[("the NULL is on the LAST stop, not the first",
                 lambda rows, c: max(rows, key=lambda r: r[0])[2] is None
                 and min(rows, key=lambda r: r[0])[2] is not None)],
    ),
    dict(
        id=9, ledger="Q410", concept="W1", tier="2 - Sequences and strings",
        title="How much of the journey is still to come",
        prompt=(
            "For service 1, each stop with the number of stops STILL AHEAD of"
            " it on that journey.\n\n"
            "The final stop has 0 ahead of it; the first has all the rest.\n\n"
            "Return: stop_seq, stops_ahead"
        ),
        solution=("SELECT stop_seq, COUNT(*) OVER (ORDER BY stop_seq"
                  " ROWS BETWEEN 1 FOLLOWING AND UNBOUNDED FOLLOWING)"
                  " FROM stops WHERE service_id = 1"),
        trap_sql=("SELECT stop_seq, COUNT(*) OVER (ORDER BY stop_seq)"
                  " FROM stops WHERE service_id = 1"),
        note="Frames can look FORWARD as well as back. ROWS BETWEEN 1"
             " FOLLOWING AND UNBOUNDED FOLLOWING is everything after the"
             " current row, which is a shape the trailing-window questions"
             " never needed. The trap uses the default frame -- start of"
             " partition to current row -- and counts what is BEHIND instead,"
             " which is the mirror image and looks entirely plausible.",
        claims=[("the last stop has 0 ahead and the first has the most",
                 lambda rows, c: max(rows, key=lambda r: r[0])[1] == 0
                 and min(rows, key=lambda r: r[0])[1] == len(rows) - 1)],
    ),
    dict(
        id=10, ledger="Q411", concept="W2", tier="2 - Sequences and strings",
        title="Every station's place in the line",
        prompt=(
            "For service 1, each stop with the name of the station the service"
            " STARTED from -- repeated on every row.\n\n"
            "Return: stop_seq, station, origin"
        ),
        solution=("SELECT sp.stop_seq, st.name,"
                  " FIRST_VALUE(st.name) OVER (ORDER BY sp.stop_seq)"
                  " FROM stops sp JOIN stations st"
                  " ON st.station_id = sp.station_id WHERE sp.service_id = 1"),
        trap_sql=("SELECT sp.stop_seq, st.name,"
                  " LAST_VALUE(st.name) OVER (ORDER BY sp.stop_seq)"
                  " FROM stops sp JOIN stations st"
                  " ON st.station_id = sp.station_id WHERE sp.service_id = 1"),
        note="FIRST_VALUE is safe with the default frame, because the start of"
             " the partition is always in view. LAST_VALUE is the notorious"
             " one: the default frame ends at the CURRENT ROW, so 'the last"
             " value' is the current row's own value on every line. To make"
             " LAST_VALUE mean what it says you must write the frame out --"
             " ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING.",
        claims=[("origin is the same on every row",
                 lambda rows, c: len({r[2] for r in rows}) == 1),
                ("and it equals the first stop's station",
                 lambda rows, c: min(rows, key=lambda r: r[0])[1]
                 == rows[0][2])],
    ),
    # ================================================ 3 Unpivot and set ops
    dict(
        id=11, ledger="Q412", concept="U1", tier="3 - Unpivot and set ops",
        title="Four columns into four rows",
        prompt=(
            "station_footfall holds one row per station-year with q1, q2, q3"
            " and q4 side by side. Turn 2025 long again: one row per station"
            " per quarter.\n\n"
            "Quarters are the integers 1 to 4.\n\n"
            "Return: station_id, quarter, footfall"
        ),
        solution=("SELECT station_id, 1, q1 FROM station_footfall"
                  " WHERE year = 2025 UNION ALL"
                  " SELECT station_id, 2, q2 FROM station_footfall"
                  " WHERE year = 2025 UNION ALL"
                  " SELECT station_id, 3, q3 FROM station_footfall"
                  " WHERE year = 2025 UNION ALL"
                  " SELECT station_id, 4, q4 FROM station_footfall"
                  " WHERE year = 2025"),
        trap_sql=("SELECT station_id, 1, q1 FROM station_footfall"
                  " WHERE year = 2025 UNION"
                  " SELECT station_id, 2, q2 FROM station_footfall"
                  " WHERE year = 2025 UNION"
                  " SELECT station_id, 3, q3 FROM station_footfall"
                  " WHERE year = 2025 UNION"
                  " SELECT station_id, 4, q4 FROM station_footfall"
                  " WHERE year = 2025"
                  " EXCEPT SELECT station_id, 4, q4 FROM station_footfall"
                  " WHERE year = 2025 AND q4 > 0"),
        note="SQL has no UNPIVOT operator -- turning columns into rows is one"
             " SELECT per column, stacked. The quarter number is a LITERAL in"
             " each branch, which is what carries the information that used to"
             " be in the column NAME. Use UNION ALL, not UNION: two stations"
             " with identical figures in the same quarter are different facts"
             " and UNION would silently merge them.",
        claims=[("four rows per station",
                 lambda rows, c: len(rows) == 4 * c.execute(
                     "SELECT COUNT(*) FROM station_footfall WHERE year = 2025"
                 ).fetchone()[0]),
                ("the total matches the wide table",
                 lambda rows, c: sum(r[2] for r in rows) == c.execute(
                     "SELECT SUM(q1 + q2 + q3 + q4) FROM station_footfall"
                     " WHERE year = 2025").fetchone()[0])],
    ),
    dict(
        id=12, ledger="Q413", concept="S1", tier="3 - Unpivot and set ops",
        title="Stations that grew two years running",
        prompt=(
            "Stations whose total footfall rose from 2023 to 2024 AND again"
            " from 2024 to 2025.\n\n"
            "Total footfall for a year is the four quarters added up.\n\n"
            "Return: station_id"
        ),
        solution=("WITH y AS (SELECT station_id, year, q1 + q2 + q3 + q4 AS t"
                  " FROM station_footfall)"
                  " SELECT a.station_id FROM y a JOIN y b"
                  " ON b.station_id = a.station_id AND b.year = a.year + 1"
                  " AND b.t > a.t WHERE a.year = 2023"
                  " INTERSECT"
                  " SELECT a.station_id FROM y a JOIN y b"
                  " ON b.station_id = a.station_id AND b.year = a.year + 1"
                  " AND b.t > a.t WHERE a.year = 2024"),
        trap_sql=("WITH y AS (SELECT station_id, year, q1 + q2 + q3 + q4 AS t"
                  " FROM station_footfall)"
                  " SELECT a.station_id FROM y a JOIN y b"
                  " ON b.station_id = a.station_id AND b.year = a.year + 1"
                  " AND b.t > a.t WHERE a.year = 2023"
                  " UNION"
                  " SELECT a.station_id FROM y a JOIN y b"
                  " ON b.station_id = a.station_id AND b.year = a.year + 1"
                  " AND b.t > a.t WHERE a.year = 2024"),
        note="Two conditions on the same station, so INTERSECT. UNION gives"
             " stations that grew in EITHER year, which is a much larger and"
             " entirely plausible set. Note the self-join on year = year + 1 --"
             " a table joined to itself one row along is the other way to"
             " compare consecutive periods when a window function is not"
             " convenient.",
        claims=[("every station returned really did grow twice",
                 lambda rows, c: all(c.execute(
                     "SELECT (SELECT q1+q2+q3+q4 FROM station_footfall WHERE"
                     " station_id = ? AND year = 2024) >"
                     " (SELECT q1+q2+q3+q4 FROM station_footfall WHERE"
                     " station_id = ? AND year = 2023)",
                     (r[0], r[0])).fetchone()[0] == 1 for r in rows))],
    ),
    dict(
        id=13, ledger="Q414", concept="S1", tier="3 - Unpivot and set ops",
        title="Bought from there, never bought to there",
        prompt=(
            "Station-and-class pairs that appear as the ORIGIN of a ticket but"
            " never as the destination of a ticket of that same class.\n\n"
            "Set operators compare WHOLE ROWS, so both sides here are two"
            " columns wide. Tickets with no destination recorded cannot"
            " contribute to the second list. There are 18 such pairs.\n\n"
            "Return: station_id, class"
        ),
        solution=("SELECT DISTINCT from_station, class FROM tickets"
                  " EXCEPT"
                  " SELECT DISTINCT to_station, class FROM tickets"
                  " WHERE to_station IS NOT NULL"),
        trap_sql=("SELECT DISTINCT from_station FROM tickets"
                  " EXCEPT"
                  " SELECT DISTINCT to_station FROM tickets"
                  " WHERE to_station IS NOT NULL"),
        note="A set operator matches on EVERY column, so (station, class) is"
             " subtracted as a PAIR -- a station that receives standard-class"
             " arrivals but never first-class ones still appears, for first."
             " Reduce it to one column and you ask a weaker question: stations"
             " nobody ever travels to at all, which is 6 rather than 18. Both"
             " run; only one answers what was asked.",
        claims=[("18 pairs, two columns wide",
                 lambda rows, c: len(rows) == 18 and len(rows[0]) == 2),
                ("the single-column version would give far fewer",
                 lambda rows, c: c.execute(
                     "SELECT COUNT(*) FROM (SELECT DISTINCT from_station FROM"
                     " tickets EXCEPT SELECT DISTINCT to_station FROM tickets"
                     " WHERE to_station IS NOT NULL)").fetchone()[0] < 18)],
    ),
    dict(
        id=14, ledger="Q415", concept="A1", tier="3 - Unpivot and set ops",
        title="And back to wide again",
        prompt=(
            "One row per line, with the number of its services in each of the"
            " three ticket classes as columns.\n\n"
            "A service with no tickets of a class counts 0.\n\n"
            "Return: line_name, first, standard, advance"
        ),
        solution=("SELECT l.name,"
                  " SUM(CASE WHEN t.class = 'first' THEN 1 ELSE 0 END),"
                  " SUM(CASE WHEN t.class = 'standard' THEN 1 ELSE 0 END),"
                  " SUM(CASE WHEN t.class = 'advance' THEN 1 ELSE 0 END)"
                  " FROM lines l JOIN services s ON s.line_id = l.line_id"
                  " JOIN tickets t ON t.service_id = s.service_id"
                  " GROUP BY l.name"),
        trap_sql=("SELECT l.name,"
                  " COUNT(CASE WHEN t.class = 'first' THEN 1 ELSE 0 END),"
                  " COUNT(CASE WHEN t.class = 'standard' THEN 1 ELSE 0 END),"
                  " COUNT(CASE WHEN t.class = 'advance' THEN 1 ELSE 0 END)"
                  " FROM lines l JOIN services s ON s.line_id = l.line_id"
                  " JOIN tickets t ON t.service_id = s.service_id"
                  " GROUP BY l.name"),
        note="The inverse of question 11: rows into columns is a pivot, and SQL"
             " has no operator for that either -- it is one conditional"
             " aggregate per column. Pick SUM(CASE ... THEN 1 ELSE 0 END) or"
             " COUNT(CASE ... THEN 1 END); the mixture in the trap counts every"
             " row, because 0 is a value and COUNT only skips NULL.",
        claims=[("six lines, columns totalling every ticket",
                 lambda rows, c: len(rows) == 6
                 and sum(r[1] + r[2] + r[3] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM tickets").fetchone()[0])],
    ),
    # ==================================================== 4 Dates and times
    dict(
        id=15, ledger="Q416", concept="D2", tier="4 - Dates and times",
        title="Services by calendar month",
        prompt=(
            "One row per calendar month, giving the FIRST DAY of that month as"
            " a date and how many services ran in it.\n\n"
            "Use a date modifier rather than string surgery -- the answer must"
            " be a real date like '2025-03-01', not '2025-03'.\n\n"
            "Return: month_start, services"
        ),
        solution=("SELECT date(run_date, 'start of month'), COUNT(*)"
                  " FROM services GROUP BY 1"),
        trap_sql=("SELECT strftime('%Y-%m', run_date), COUNT(*)"
                  " FROM services GROUP BY 1"),
        note="date() takes MODIFIERS after the value: 'start of month',"
             " 'start of year', '+1 day', '-3 months', 'weekday 0'. They chain"
             " left to right, so date(x, 'start of month', '+1 month', '-1"
             " day') is the last day of the month. strftime('%Y-%m') groups the"
             " same rows but yields text, which no date function will accept"
             " back.",
        claims=[("every value is a full ISO date on the 1st",
                 lambda rows, c: all(len(r[0]) == 10 and r[0].endswith('-01')
                                     for r in rows)),
                ("the counts total every service",
                 lambda rows, c: sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM services").fetchone()[0])],
    ),
    dict(
        id=16, ledger="Q417", concept="D2", tier="4 - Dates and times",
        title="Weekends versus weekdays",
        prompt=(
            "How many services ran at the weekend and how many midweek.\n\n"
            "Saturday and Sunday are the weekend.\n\n"
            "Return: part_of_week, services"
        ),
        solution=("SELECT CASE WHEN strftime('%w', run_date) IN ('0', '6')"
                  " THEN 'weekend' ELSE 'weekday' END, COUNT(*)"
                  " FROM services GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN strftime('%w', run_date) IN (0, 6)"
                  " THEN 'weekend' ELSE 'weekday' END, COUNT(*)"
                  " FROM services GROUP BY 1"),
        note="strftime returns TEXT, always. Comparing it to the integers 0 and"
             " 6 never matches -- SQLite does not coerce across storage"
             " classes, so an integer is never equal to a string -- and every"
             " service is quietly reported as a weekday. Quote the literals, or"
             " CAST the strftime. Note %w is day-of-week 0-6 with Sunday 0;"
             " uppercase %W is week-of-year and unrelated.",
        claims=[("two buckets totalling every service",
                 lambda rows, c: len(rows) == 2
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM services").fetchone()[0]),
                ("weekdays outnumber weekend days",
                 lambda rows, c: dict(rows)['weekday'] > dict(rows)['weekend'])],
    ),
    dict(
        id=17, ledger="Q418", concept="D2", tier="4 - Dates and times",
        title="How late did it actually arrive",
        prompt=(
            "For service 1, each stop where the train arrived LATE, with how"
            " many minutes late it was.\n\n"
            "Skipped stops have no actual_arrive and are not late -- they are"
            " unknown. Times are 'HH:MM'.\n\n"
            "Return: stop_seq, sched_arrive, actual_arrive, minutes_late"
        ),
        solution=("SELECT stop_seq, sched_arrive, actual_arrive,"
                  " (CAST(substr(actual_arrive, 1, 2) AS INTEGER) * 60"
                  " + CAST(substr(actual_arrive, 4, 2) AS INTEGER))"
                  " - (CAST(substr(sched_arrive, 1, 2) AS INTEGER) * 60"
                  " + CAST(substr(sched_arrive, 4, 2) AS INTEGER))"
                  " FROM stops WHERE service_id = 1"
                  " AND actual_arrive IS NOT NULL"
                  " AND actual_arrive > sched_arrive"),
        trap_sql=("SELECT stop_seq, sched_arrive, actual_arrive,"
                  " actual_arrive - sched_arrive FROM stops"
                  " WHERE service_id = 1 AND actual_arrive > sched_arrive"),
        note="Two separate things. 'HH:MM' compares correctly as text -- it is"
             " zero-padded and fixed width -- so actual > sched is a valid test"
             " for lateness. Arithmetic on it is not: subtraction coerces to"
             " numbers and reads '09:47' as 9. And the NULL check is redundant"
             " here only because NULL > anything is NULL; stating it makes the"
             " intent visible rather than accidental.",
        claims=[("every row is genuinely late by a positive number of minutes",
                 lambda rows, c: all(r[3] > 0 for r in rows))],
    ),
    dict(
        id=18, ledger="Q419", concept="D2", tier="4 - Dates and times",
        title="The last service of each month",
        prompt=(
            "For each calendar month, the run_date of the last day in that"
            " month on which any service ran.\n\n"
            "Build the month's last day with date modifiers rather than"
            " assuming 30 or 31.\n\n"
            "Return: month_start, last_running_day"
        ),
        solution=("SELECT date(run_date, 'start of month'), MAX(run_date)"
                  " FROM services GROUP BY 1"),
        trap_sql=("SELECT date(run_date, 'start of month'), MIN(run_date)"
                  " FROM services GROUP BY 1"),
        note="The last day a service RAN is a fact about the data, so it is"
             " MAX(run_date) -- not something to compute from the calendar."
             " Worth knowing the chain that WOULD give the calendar month-end,"
             " though: date(x, 'start of month', '+1 month', '-1 day') handles"
             " February and leap years without you knowing the length. Here"
             " services run every day, so the two happen to agree -- which is"
             " exactly when a wrong method is hardest to notice.",
        claims=[("every last_running_day is in its own month",
                 lambda rows, c: all(r[1][:7] == r[0][:7] for r in rows))],
    ),
    # ================================================== 5 Joins and grain
    dict(
        id=19, ledger="Q420", concept="J2", tier="5 - Joins and grain",
        title="Every station, called at or not",
        prompt=(
            "One row per station: id, name, and how many services call"
            " there.\n\n"
            "Ten stations are on no line at all. They must appear with 0, so"
            " all 60 come back.\n\n"
            "Return: station_id, name, calls"
        ),
        solution=("SELECT st.station_id, st.name, COUNT(sp.service_id)"
                  " FROM stations st LEFT JOIN stops sp"
                  " ON sp.station_id = st.station_id GROUP BY 1, 2"),
        trap_sql=("SELECT st.station_id, st.name, COUNT(sp.service_id)"
                  " FROM stations st JOIN stops sp"
                  " ON sp.station_id = st.station_id GROUP BY 1, 2"),
        note="An inner join can only return stations that matched, so the ten"
             " unserved ones vanish rather than showing 0. LEFT JOIN plus"
             " COUNT(a column from the right side) is the pairing -- COUNT(*)"
             " would give those ten a phantom 1.",
        claims=[("all 60 stations, ten with none",
                 lambda rows, c: len(rows) == 60
                 and sum(1 for r in rows if r[2] == 0) == 10)],
    ),
    dict(
        id=20, ledger="Q421", concept="J2", tier="5 - Joins and grain",
        title="Units that have never run",
        prompt=(
            "Rolling stock that has never been assigned to any service.\n\n"
            "Write it as an outer join that keeps the non-matches. There are"
            " 5.\n\n"
            "Return: unit_id, model"
        ),
        solution=("SELECT r.unit_id, r.model FROM rolling_stock r"
                  " LEFT JOIN service_units u ON u.unit_id = r.unit_id"
                  " WHERE u.service_id IS NULL"),
        trap_sql=("SELECT r.unit_id, r.model FROM rolling_stock r"
                  " LEFT JOIN service_units u ON u.unit_id = r.unit_id"
                  " AND u.service_id IS NULL"),
        note="The anti-join is two halves: LEFT JOIN to keep the unmatched"
             " units, then WHERE <right column> IS NULL to keep only those."
             " Moved into ON, that test becomes part of what counts as a match,"
             " matches nothing, and returns all 50 units.",
        claims=[("5 units, none of them ever assigned",
                 lambda rows, c: len(rows) == 5
                 and not {r[0] for r in rows} & {
                     x[0] for x in c.execute(
                         "SELECT DISTINCT unit_id FROM service_units")})],
    ),
    dict(
        id=21, ledger="Q422", concept="E1", tier="5 - Joins and grain",
        title="Stations a journey begins at",
        prompt=(
            "Stations that are the FIRST stop of at least one service.\n\n"
            "Six qualify -- one per line. One row per station, however many"
            " thousand services start there.\n\n"
            "Return: station_id, name"
        ),
        solution=("SELECT st.station_id, st.name FROM stations st"
                  " WHERE EXISTS (SELECT 1 FROM stops sp"
                  " WHERE sp.station_id = st.station_id AND sp.stop_seq = 1)"),
        trap_sql=("SELECT st.station_id, st.name FROM stations st"
                  " JOIN stops sp ON sp.station_id = st.station_id"
                  " WHERE sp.stop_seq = 1"),
        note="Joining down to stops to answer a question ABOUT stations changes"
             " the grain: you get one row per qualifying stop, and every line"
             " runs thousands of services, so each of the six stations comes"
             " back thousands of times. EXISTS asks the question without"
             " changing what a row is -- it returns yes or no and stops at the"
             " first hit. SELECT DISTINCT would patch the join, but EXISTS says"
             " what you meant and does far less work.",
        claims=[("six stations, none listed twice",
                 lambda rows, c: len(rows) == 6
                 and len({r[0] for r in rows}) == 6),
                ("a plain join really would return thousands",
                 lambda rows, c: c.execute(
                     "SELECT COUNT(*) FROM stops WHERE stop_seq = 1"
                 ).fetchone()[0] > 1000)],
    ),
    dict(
        id=22, ledger="Q423", concept="C2", tier="5 - Joins and grain",
        title="Three measures per line",
        prompt=(
            "One row per line: how many services it ran, how many tickets were"
            " sold on them, and how many incidents were reported.\n\n"
            "Services is the parent; tickets and incidents are independent"
            " children of it. All six lines appear.\n\n"
            "Return: line_id, services, tickets, incidents"
        ),
        solution=("SELECT l.line_id,"
                  " (SELECT COUNT(*) FROM services s"
                  " WHERE s.line_id = l.line_id),"
                  " (SELECT COUNT(*) FROM tickets t JOIN services s"
                  " ON s.service_id = t.service_id WHERE s.line_id = l.line_id),"
                  " (SELECT COUNT(*) FROM incidents i JOIN services s"
                  " ON s.service_id = i.service_id WHERE s.line_id = l.line_id)"
                  " FROM lines l"),
        trap_sql=("SELECT l.line_id, COUNT(DISTINCT s.service_id),"
                  " COUNT(t.ticket_id), COUNT(i.incident_id) FROM lines l"
                  " JOIN services s ON s.line_id = l.line_id"
                  " LEFT JOIN tickets t ON t.service_id = s.service_id"
                  " LEFT JOIN incidents i ON i.service_id = s.service_id"
                  " GROUP BY 1"),
        note="Two child tables joined to the same parent multiply: a service"
             " with 6 tickets and 1 incident yields 6 rows, and one with 6"
             " tickets and 2 incidents yields 12. COUNT(DISTINCT) rescues the"
             " service count and nothing else -- which is the dangerous part,"
             " because one column looks right while the other two are"
             " inflated.",
        claims=[("six lines, all three totals matching their tables",
                 lambda rows, c: len(rows) == 6
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM services").fetchone()[0]
                 and sum(r[2] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM tickets").fetchone()[0]
                 and sum(r[3] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM incidents").fetchone()[0])],
    ),
    # ============================================ 6 Windows and recursion
    dict(
        id=23, ledger="Q424", concept="W1", tier="6 - Windows and recursion",
        title="Revenue accumulating through the year",
        prompt=(
            "One row per calendar month of 2025: the month start, that month's"
            " ticket revenue in pounds, and the running total for the year to"
            " that point.\n\n"
            "Return: month_start, revenue, running_total"
        ),
        solution=("WITH m AS (SELECT date(sold_at, 'start of month') AS ms,"
                  " SUM(price_pence) / 100.0 AS rev FROM tickets"
                  " WHERE sold_at >= '2025-01-01' AND sold_at < '2026-01-01'"
                  " GROUP BY 1)"
                  " SELECT ms, ROUND(rev, 2),"
                  " ROUND(SUM(rev) OVER (ORDER BY ms), 2) FROM m"),
        trap_sql=("WITH m AS (SELECT date(sold_at, 'start of month') AS ms,"
                  " SUM(price_pence) / 100.0 AS rev FROM tickets"
                  " WHERE sold_at >= '2025-01-01' AND sold_at < '2026-01-01'"
                  " GROUP BY 1)"
                  " SELECT ms, ROUND(rev, 2), ROUND(SUM(rev) OVER (), 2)"
                  " FROM m"),
        note="ORDER BY inside OVER() is the whole difference. SUM(x) OVER ()"
             " sees every row at once and repeats the year's total on each"
             " line; SUM(x) OVER (ORDER BY ms) sees only rows up to the current"
             " one. A running total over positive numbers can only go up -- if"
             " yours is flat, there is no ORDER BY in the window.",
        claims=[("twelve months, running total ending at the year's revenue",
                 lambda rows, c: len(rows) == 12 and abs(
                     max(r[2] for r in rows) - sum(r[1] for r in rows)) < 0.5)],
    ),
    dict(
        id=24, ledger="Q425", concept="R1", tier="6 - Windows and recursion",
        title="Everyone under the top manager",
        prompt=(
            "Everyone below the one member of staff who reports to nobody, with"
            " how many levels below they sit.\n\n"
            "Their direct reports are 1, those people's reports 2. 39 rows.\n\n"
            "Return: staff_id, name, level"
        ),
        solution=("WITH RECURSIVE below(id, name, lvl) AS ("
                  " SELECT staff_id, name, 1 FROM staff"
                  " WHERE reports_to = (SELECT staff_id FROM staff"
                  " WHERE reports_to IS NULL)"
                  " UNION ALL"
                  " SELECT s.staff_id, s.name, b.lvl + 1 FROM staff s"
                  " JOIN below b ON s.reports_to = b.id)"
                  " SELECT id, name, lvl FROM below"),
        trap_sql=("SELECT staff_id, name, 1 FROM staff"
                  " WHERE reports_to = (SELECT staff_id FROM staff"
                  " WHERE reports_to IS NULL)"),
        note="The plain query gives the four direct reports and stops. Each"
             " recursive pass takes whoever was found last time and looks for"
             " people reporting to them, until a pass finds nobody. Note the"
             " step's SELECT draws from `staff`, not from `below` -- a step"
             " that only selects from the CTE cannot advance and loops forever.",
        claims=[("39 rows over two levels",
                 lambda rows, c: len(rows) == 39
                 and {r[2] for r in rows} == {1, 2})],
    ),
    dict(
        id=25, ledger="Q426", concept="X6", tier="7 - Query efficiency",
        title="Group the way the index already is",
        prompt=(
            "How many services ran on each distinct date.\n\n"
            "The editor's query sorts all 13,104 rows into a temporary"
            " structure first. services.run_date is indexed, and an index is"
            " already grouped -- your plan must NOT contain 'TEMP B-TREE'.\n\n"
            "Return: run_date, services"
        ),
        solution="SELECT run_date, COUNT(*) FROM services GROUP BY run_date",
        starter_sql=SLOW_GROUP, trap_sql=SLOW_GROUP,
        plan_forbids=("TEMP B-TREE",),
        note="GROUP BY has the same relationship with indexes that ORDER BY"
             " does: both need rows brought together in order, and an index"
             " already holds them that way. Grouping by run_date || '' produces"
             " identical values, and that is not enough -- SQLite matches the"
             " indexed COLUMN, not the values, so it falls back to sorting"
             " everything into a temp b-tree before it can count.",
        claims=[("one row per distinct run_date",
                 lambda rows, c: len(rows) == c.execute(
                     "SELECT COUNT(DISTINCT run_date) FROM services"
                 ).fetchone()[0]),
                ("the counts total every service",
                 lambda rows, c: sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM services").fetchone()[0])],
    ),
    # ================================================== 7 Query efficiency
    # Each of these OPENS with the slow query already in the editor. It returns
    # the right answer; only the plan is wrong.
    dict(
        id=26, ledger="Q427", concept="X1", tier="7 - Query efficiency",
        title="A year of services, without scanning",
        prompt=(
            "How many services ran during 2025.\n\n"
            "The editor already contains a query that gets this right by"
            " reading all 13,104 rows. services.run_date is indexed -- make the"
            " plan say SEARCH instead of SCAN.\n\n"
            "Return: one row, one column: the count"
        ),
        solution=("SELECT COUNT(*) FROM services WHERE run_date >= '2025-01-01'"
                  " AND run_date < '2026-01-01'"),
        starter_sql=SLOW_YEAR, trap_sql=SLOW_YEAR,
        plan_forbids=("SCAN",),
        note="An index is on the COLUMN, not on expressions of it. Wrapping"
             " run_date in strftime() means SQLite must compute the function"
             " for every row to find out which match -- which is the scan. Test"
             " the bare column as a RANGE instead. Note the upper bound is"
             " < '2026-01-01' rather than <= '2025-12-31': the half-open form"
             " survives a column that later gains a time component.",
        claims=[("matches the count the starter query gives",
                 lambda rows, c: rows[0][0] == c.execute(
                     "SELECT COUNT(*) FROM services"
                     " WHERE strftime('%Y', run_date) = '2025'").fetchone()[0])],
    ),
    dict(
        id=27, ledger="Q428", concept="X2", tier="7 - Query efficiency",
        title="Sort the way the index already is",
        prompt=(
            "The first 20 ticket ids ordered by class, then price, then"
            " ticket_id.\n\n"
            "The editor's query sorts all 40,686 tickets to return 20. There is"
            " an index on tickets(class, price_pence) and an index is already"
            " sorted. Your plan must NOT contain 'TEMP B-TREE'.\n\n"
            "Return: ticket_id"
        ),
        solution=("SELECT ticket_id FROM tickets"
                  " ORDER BY class, price_pence, ticket_id LIMIT 20"),
        starter_sql=SLOW_SORT, trap_sql=SLOW_SORT,
        plan_forbids=("TEMP B-TREE",),
        note="price_pence + 0 has the same value and the same ordering as"
             " price_pence -- and that is not enough. SQLite matches the"
             " indexed COLUMN, not the values an expression happens to produce,"
             " so any arithmetic on it forces a sort of the whole table before"
             " the first of 20 rows can be known. That is what defeats LIMIT: a"
             " temp b-tree must finish before anything can be returned.",
        claims=[("twenty rows",
                 lambda rows, c: len(rows) == 20)],
    ),
    dict(
        id=28, ledger="Q429", concept="X5", tier="7 - Query efficiency",
        title="Keep the index covering",
        prompt=(
            "The class and price of every first-class ticket.\n\n"
            "The editor's query finds the right rows but has to open the table"
            " for each one. tickets(class, price_pence) already holds"
            " everything this question needs -- your plan must say COVERING"
            " INDEX.\n\n"
            "Return: class, price_pence"
        ),
        solution="SELECT class, price_pence FROM tickets WHERE class = 'first'",
        starter_sql=SLOW_COVER, trap_sql=SLOW_COVER,
        plan_requires=("COVERING INDEX",),
        note="A COVERING index holds every column the query mentions, so the"
             " index alone answers it and the table is never touched. The"
             " starter adds `sold_at IS NOT NULL`, which is true for every row"
             " and changes nothing about the output -- but sold_at is not in"
             " the index, so SQLite must fetch each matching row from the table"
             " to check it. Merely MENTIONING a column outside the index costs"
             " the covering read, whether you select it or only filter on it.",
        claims=[("every row is first class",
                 lambda rows, c: len(rows) > 0
                 and all(r[0] == 'first' for r in rows))],
    ),
    dict(
        id=29, ledger="Q430", concept="X1", tier="7 - Query efficiency",
        title="Names beginning with Alan",
        prompt=(
            "Staff whose name starts with 'Alan'.\n\n"
            "staff.name is indexed. The editor's query cannot use that index --"
            " make the plan say SEARCH.\n\n"
            "Return: staff_id, name"
        ),
        solution="SELECT staff_id, name FROM staff WHERE name LIKE 'Alan%'",
        starter_sql=SLOW_LIKE, trap_sql=SLOW_LIKE,
        plan_forbids=("SCAN",),
        note="LIKE with a trailing-only wildcard is index-friendly: 'Alan%'"
             " becomes the range name >= 'Alan' AND name < 'Alab'... which a"
             " B-tree serves directly. substr() is a function on the column and"
             " defeats it, exactly as strftime did in question 26. Two things"
             " would also break it: a LEADING wildcard ('%Alan'), and an index"
             " without COLLATE NOCASE -- LIKE is case-insensitive by default,"
             " so a BINARY index cannot serve it. This one is declared NOCASE"
             " for that reason.",
        claims=[("every row starts with Alan",
                 lambda rows, c: all(r[1].startswith('Alan') for r in rows))],
    ),
    dict(
        id=30, ledger="Q431", concept="X7", tier="7 - Query efficiency",
        title="The anti-join that should not be a join",
        prompt=(
            "How many stations no service calls at.\n\n"
            "The editor's query joins 105,821 stops to 60 stations and throws"
            " nearly all of it away -- it takes about 36ms. Ask the question"
            " once per station instead: your plan must contain 'CORRELATED"
            " SCALAR SUBQUERY'.\n\n"
            "Return: one row, one column: the count"
        ),
        solution=("SELECT COUNT(*) FROM stations st WHERE NOT EXISTS"
                  " (SELECT 1 FROM stops s"
                  " WHERE s.station_id = st.station_id)"),
        starter_sql=SLOW_ANTI, trap_sql=SLOW_ANTI,
        plan_requires=("CORRELATED SCALAR SUBQUERY",),
        note="This runs against the usual advice, which is why it is here. A"
             " LEFT JOIN anti-join builds the whole join and then discards"
             " every row that matched. NOT EXISTS asks one indexed question per"
             " station and stops at the first hit -- 60 cheap seeks against"
             " 105,821 rows joined and thrown away, and it is roughly 1,800"
             " times faster. The rule is not 'avoid correlated subqueries'; it"
             " is 'check whether the correlated column is indexed'. Here"
             " stops.station_id is, so each repeat is a SEARCH.",
        claims=[("matches the anti-join count",
                 lambda rows, c: rows[0][0] == c.execute(
                     "SELECT COUNT(*) FROM stations st LEFT JOIN stops s"
                     " ON s.station_id = st.station_id"
                     " WHERE s.service_id IS NULL").fetchone()[0])],
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
        detail += f"\n  Expected but missing:  {missing[0]}"
    if unexpected:
        detail += f"\n  Returned but wrong:    {unexpected[0]}"
    return False, (f"Right row count ({len(got)}), but the values differ "
                   f"in {len(missing)} row(s).{detail}")
