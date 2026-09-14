"""Practice exercises with reference solutions, used by the GUI to grade answers.

These 30 questions (ledger Q462-Q491) run on the railway schema, re-seeded
(SEED 437 -> 473). Same tables, same difficulty for the first 26 -- and a
harder efficiency stage.

The efficiency questions are no longer single-table toys. Each starter is a
JOIN or an aggregate across two or three tables, so the plan is four or five
lines long and the first job is working out WHICH line is the expensive one.
The fix is still one edit; finding it is the work.

  27  a date function inside a three-table join -- blocks the range seek, and
      flips which table drives the whole join
  28  a join with ORDER BY and LIMIT -- an expression stops the index walk, so
      40,000 rows are sorted to return 20
  29  grouping by strftime() on a column already in that format -- same 546
      rows, a temp b-tree, and a different driving table
  30  a CTE that aggregates the WHOLE ticket table so the outer query can use
      one line's worth of it

Question 30 is the one worth sitting with. Pulling an aggregate into a CTE is
usually good practice; here it is the slow path, because a materialised CTE
cannot see the outer query's filter and computes 40,000 rows to answer a
question about 2,184. The correlated subquery -- normally the thing you are
told to rewrite -- wins by 4x.

The other 26 lean on parts of the schema the last two sets left alone:
service_units.position as a second sequence, rolling_stock ages, delay
minutes, operators, step-free access, and staff base stations.

Each question carries:

  concept   the mistake or technique it drills
  solution  one correct answer
  trap_sql  the tempting WRONG query -- check_questions.py asserts the grader
            rejects it
  starter_sql  for the efficiency questions, the slow query the editor opens
            with. The Reset button restores it.
  note      the lesson, shown in the GUI once you get it right
  claims    facts about the data the prompt asserts, re-checked against the
            live database

Grading compares your result as an unordered multiset of rows, floats rounded
to 2 decimals. Row order never matters; column order does.

Spoiler warning: the reference SQL is in this file.
"""

EXERCISES = [
    # ============================================================ 1 Warm-up
    dict(
        id=1, ledger="Q462", concept="general", tier="1 - Warm-up",
        title="Incidents by severity",
        prompt=(
            "Put every incident into one of three bands by delay_minutes and"
            " count them:\n"
            "  'major'  60 or more\n"
            "  'medium' 20 up to but not including 60\n"
            "  'minor'  everything else\n\n"
            "All 1,143 incidents land in exactly one band.\n\n"
            "Return: band, incidents"
        ),
        solution=("SELECT CASE WHEN delay_minutes >= 60 THEN 'major'"
                  " WHEN delay_minutes >= 20 THEN 'medium'"
                  " ELSE 'minor' END, COUNT(*) FROM incidents GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN delay_minutes >= 20 THEN 'medium'"
                  " WHEN delay_minutes >= 60 THEN 'major'"
                  " ELSE 'minor' END, COUNT(*) FROM incidents GROUP BY 1"),
        note="CASE is first-match-wins, so branch order is logic rather than"
             " taste. Test the narrowest band first: put the 20 test ahead of"
             " the 60 test and every major incident matches it on the way past,"
             " leaving 'major' unreachable. The check is arithmetic -- do the"
             " bands sum to 1,143?",
        claims=[("three bands covering all 1,143 incidents",
                 lambda rows, c: len(rows) == 3
                 and sum(r[1] for r in rows) == 1143)],
    ),
    dict(
        id=2, ledger="Q463", concept="C7", tier="1 - Warm-up",
        title="Step-free, not step-free, unknown",
        prompt=(
            "Classify every station by step_free and count them:\n"
            "  'yes'     step_free is 1\n"
            "  'no'      step_free is 0\n"
            "  'unknown' step_free is not recorded\n\n"
            "All 60 stations land in exactly one class.\n\n"
            "Return: access, stations"
        ),
        solution=("SELECT CASE WHEN step_free IS NULL THEN 'unknown'"
                  " WHEN step_free = 1 THEN 'yes' ELSE 'no' END, COUNT(*)"
                  " FROM stations GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN step_free = 1 THEN 'yes'"
                  " WHEN step_free = 0 THEN 'no'"
                  " WHEN step_free = NULL THEN 'unknown'"
                  " ELSE 'other' END, COUNT(*) FROM stations GROUP BY 1"),
        note="= NULL is never true, so that branch cannot fire and the four"
             " unrecorded stations fall through to whatever comes next. Test"
             " IS NULL, and test it FIRST -- then the branch that catches them"
             " is the one you chose rather than whichever happens to be last.",
        claims=[("three classes covering all 60 stations",
                 lambda rows, c: len(rows) == 3
                 and sum(r[1] for r in rows) == 60),
                ("four stations are unknown",
                 lambda rows, c: dict(rows)["unknown"] == 4)],
    ),
    dict(
        id=3, ledger="Q464", concept="A3", tier="1 - Warm-up",
        title="Roles with a wide pay spread",
        prompt=(
            "Roles with at least 5 staff where the highest salary is more than"
            " 1.8 times the lowest.\n\n"
            "Both conditions are about the role as a whole. One table, no"
            " joins.\n\n"
            "Return: role, staff, lowest, highest"
        ),
        solution=("SELECT role, COUNT(*), MIN(salary), MAX(salary) FROM staff"
                  " GROUP BY role"
                  " HAVING COUNT(*) >= 5 AND MAX(salary) > 1.8 * MIN(salary)"),
        trap_sql=("SELECT role, COUNT(*), MIN(salary), MAX(salary) FROM staff"
                  " WHERE salary > 1.8 * (SELECT MIN(salary) FROM staff)"
                  " GROUP BY role HAVING COUNT(*) >= 5"),
        note="HAVING can relate two aggregates to each other, which is"
             " something WHERE cannot express at any price -- at WHERE time"
             " there is no group, so there is no max or min. The trap tries to"
             " approximate it with a row filter against the global minimum,"
             " which is a different question and also throws away the low"
             " earners that define each role's own spread.",
        claims=[("every row clears both bars",
                 lambda rows, c: len(rows) > 0
                 and all(r[1] >= 5 and r[3] > 1.8 * r[2] for r in rows))],
    ),
    dict(
        id=4, ledger="Q465", concept="A2", tier="1 - Warm-up",
        title="How long until refurbishment",
        prompt=(
            "One row per model: how many units exist, how many have been"
            " refurbished, and the average number of years between building"
            " and refurbishment for those that have.\n\n"
            "refurbished_year is NULL for a unit that never has been, and those"
            " must not drag the average down.\n\n"
            "Return: model, units, refurbished, avg_years"
        ),
        solution=("SELECT model, COUNT(*), COUNT(refurbished_year),"
                  " ROUND(AVG(refurbished_year - built_year), 2)"
                  " FROM rolling_stock GROUP BY model"),
        trap_sql=("SELECT model, COUNT(*), COUNT(refurbished_year),"
                  " ROUND(AVG(COALESCE(refurbished_year, 0) - built_year), 2)"
                  " FROM rolling_stock GROUP BY model"),
        note="AVG already skips NULLs -- refurbished_year - built_year is NULL"
             " for an unrefurbished unit, and AVG passes over it. COALESCing"
             " the NULL to 0 first turns it into a real value of roughly minus"
             " two thousand years, which is arithmetic on a number that was"
             " never meant to exist. Substitute a default only when the default"
             " is meaningful.",
        claims=[("every average is a plausible number of years",
                 lambda rows, c: all(r[3] is None or 0 < r[3] < 60
                                     for r in rows))],
    ),
    # =============================================== 2 Sequences and strings
    dict(
        id=5, ledger="Q466", concept="STR", tier="2 - Sequences and strings",
        title="Every station a line calls at",
        prompt=(
            "For each line, a single comma-separated string of the distinct"
            " stations it calls at, in alphabetical order.\n\n"
            "No spaces around the commas -- the default separator is what you"
            " want. Six rows.\n\n"
            "Return: line_name, stations"
        ),
        solution=("SELECT l.name, GROUP_CONCAT(DISTINCT st.name ORDER BY"
                  " st.name) FROM lines l"
                  " JOIN services s ON s.line_id = l.line_id"
                  " JOIN stops sp ON sp.service_id = s.service_id"
                  " JOIN stations st ON st.station_id = sp.station_id"
                  " GROUP BY l.line_id, l.name"),
        trap_sql=("SELECT l.name, GROUP_CONCAT(DISTINCT st.name) FROM lines l"
                  " JOIN services s ON s.line_id = l.line_id"
                  " JOIN stops sp ON sp.service_id = s.service_id"
                  " JOIN stations st ON st.station_id = sp.station_id"
                  " GROUP BY l.line_id, l.name"),
        note="GROUP_CONCAT makes no promise about the order it concatenates"
             " in, and here it comes out in route order rather than"
             " alphabetically. A trailing ORDER BY cannot help -- that sorts"
             " the six rows the aggregate produces, not the names inside each"
             " one. The ordering belongs INSIDE the call:"
             " GROUP_CONCAT(DISTINCT x ORDER BY x). Note also that with"
             " DISTINCT you get the default ',' separator and no second"
             " argument.",
        claims=[("six lines, each a sorted list",
                 lambda rows, c: len(rows) == 6
                 and all(list(r[1].split(",")) == sorted(r[1].split(","))
                         for r in rows))],
    ),
    dict(
        id=6, ledger="Q467", concept="E1", tier="2 - Sequences and strings",
        title="Services reported all the way",
        prompt=(
            "Services on line 1 during June 2025 where EVERY stop has an"
            " actual_arrive recorded.\n\n"
            "A service with one unrecorded stop does not qualify, however many"
            " of its other stops were logged.\n\n"
            "Return: service_id"
        ),
        solution=("SELECT s.service_id FROM services s WHERE s.line_id = 1"
                  " AND s.run_date >= '2025-06-01'"
                  " AND s.run_date < '2025-07-01'"
                  " AND NOT EXISTS (SELECT 1 FROM stops p"
                  " WHERE p.service_id = s.service_id"
                  " AND p.actual_arrive IS NULL)"),
        trap_sql=("SELECT DISTINCT s.service_id FROM services s"
                  " JOIN stops p ON p.service_id = s.service_id"
                  " WHERE s.line_id = 1 AND s.run_date >= '2025-06-01'"
                  " AND s.run_date < '2025-07-01'"
                  " AND p.actual_arrive IS NOT NULL"),
        note="'Every stop was recorded' is not 'some stop was recorded', and a"
             " WHERE clause can only express the second -- it filters rows"
             " away, and a service survives as long as ONE of its rows passes."
             " ALL-type conditions are written as a double negative instead:"
             " there does not exist a stop of this service that breaks the"
             " rule. 117 services have a recorded arrival somewhere; only 88"
             " have one everywhere.",
        claims=[("88 services",
                 lambda rows, c: len(rows) == 88),
                ("none of them has an unrecorded stop",
                 lambda rows, c: not c.execute(
                     "SELECT 1 FROM stops WHERE actual_arrive IS NULL"
                     " AND service_id IN (%s) LIMIT 1"
                     % ",".join(str(int(r[0])) for r in rows)).fetchall()
                 if rows else False)],
    ),
    dict(
        id=7, ledger="Q468", concept="W2", tier="2 - Sequences and strings",
        title="Minutes into the journey",
        prompt=(
            "For service 1, each stop with how many minutes after the FIRST"
            " scheduled arrival it happens.\n\n"
            "The first stop is 0.\n\n"
            "Return: stop_seq, minutes_in"
        ),
        solution=("SELECT stop_seq, (strftime('%s', sched_arrive)"
                  " - strftime('%s', FIRST_VALUE(sched_arrive)"
                  " OVER (ORDER BY stop_seq))) / 60"
                  " FROM stops WHERE service_id = 1"),
        trap_sql=("SELECT stop_seq, (strftime('%s', sched_arrive)"
                  " - strftime('%s', LAG(sched_arrive)"
                  " OVER (ORDER BY stop_seq))) / 60"
                  " FROM stops WHERE service_id = 1"),
        note="FIRST_VALUE reaches back to the start of the window and stays"
             " there; LAG reaches back exactly one row and moves along with"
             " you. The trap gives the gap since the PREVIOUS stop, which is a"
             " different and equally reasonable measure -- so nothing about its"
             " output looks wrong. FIRST_VALUE works with the default frame"
             " here, unlike LAST_VALUE, because the frame's start is the"
             " partition's start.",
        claims=[("the first stop is 0 and the values only increase",
                 lambda rows, c: min(rows, key=lambda r: r[0])[1] == 0
                 and [r[1] for r in sorted(rows)] ==
                     sorted(r[1] for r in rows))],
    ),
    dict(
        id=8, ledger="Q469", concept="W3", tier="2 - Sequences and strings",
        title="How far through the journey",
        prompt=(
            "For service 1, each stop with how far through the journey it is,"
            " as a percentage of the total number of stops.\n\n"
            "The last stop is 100. Round to two decimals.\n\n"
            "Return: stop_seq, pct_through"
        ),
        solution=("SELECT stop_seq, ROUND(100.0 * stop_seq"
                  " / MAX(stop_seq) OVER (), 2)"
                  " FROM stops WHERE service_id = 1"),
        trap_sql=("SELECT stop_seq, ROUND(100 * stop_seq"
                  " / MAX(stop_seq) OVER (), 2)"
                  " FROM stops WHERE service_id = 1"),
        note="MAX(...) OVER () with nothing in the parentheses is the whole"
             " window -- every row of the filtered set -- which is exactly the"
             " denominator a share needs. The trap is integer division: stop_seq"
             " and the max are both integers, so 100 * 3 / 9 truncates to 33"
             " and ROUND has nothing left to round. Writing 100.0 makes the"
             " expression float.",
        claims=[("the last stop is 100",
                 lambda rows, c: abs(max(r[1] for r in rows) - 100) < 0.01),
                ("not every value is a whole number",
                 lambda rows, c: any(abs(r[1] - round(r[1])) > 0.001
                                     for r in rows))],
    ),
    dict(
        id=9, ledger="Q470", concept="W3", tier="2 - Sequences and strings",
        title="The two shortest legs",
        prompt=(
            "For service 1, the two SHORTEST gaps between consecutive"
            " scheduled arrivals, in minutes.\n\n"
            "Report the stop the gap arrives at, shortest first, breaking ties"
            " by the lower stop_seq.\n\n"
            "Return: stop_seq, minutes"
        ),
        solution=("WITH g AS (SELECT stop_seq, (strftime('%s', sched_arrive)"
                  " - strftime('%s', LAG(sched_arrive) OVER (ORDER BY"
                  " stop_seq))) / 60 AS mins FROM stops WHERE service_id = 1)"
                  " SELECT stop_seq, mins FROM g WHERE mins IS NOT NULL"
                  " ORDER BY mins, stop_seq LIMIT 2"),
        trap_sql=("WITH g AS (SELECT stop_seq, (strftime('%s', sched_arrive)"
                  " - strftime('%s', LAG(sched_arrive) OVER (ORDER BY"
                  " stop_seq))) / 60 AS mins FROM stops WHERE service_id = 1)"
                  " SELECT stop_seq, mins FROM g ORDER BY mins, stop_seq"
                  " LIMIT 2"),
        note="Stop 1 has no predecessor, so LAG gives NULL and its gap is"
             " NULL. SQLite sorts NULLs FIRST on an ascending ORDER BY, so the"
             " trap hands back stop 1 with a blank as the shortest leg. It is"
             " not a small gap, it is an absent one -- filter it out rather"
             " than relying on where NULLs happen to land. (Ask for the"
             " longest legs instead and the same bug hides, because NULLs go"
             " last on DESC.)",
        claims=[("two rows, both positive",
                 lambda rows, c: len(rows) == 2
                 and all(r[1] is not None and r[1] > 0 for r in rows))],
    ),
    # ================================================= 3 Unpivot and set ops
    dict(
        id=10, ledger="Q471", concept="UNP", tier="3 - Unpivot and set ops",
        title="Quarter on quarter, network wide",
        prompt=(
            "Network-wide footfall for each quarter of 2025, with the change"
            " from the quarter before.\n\n"
            "Q1 has nothing before it, so its change is NULL. Four rows.\n\n"
            "Return: quarter, footfall, change"
        ),
        solution=("WITH q AS ("
                  " SELECT 1 qtr, SUM(q1) f FROM station_footfall WHERE year=2025"
                  " UNION ALL SELECT 2, SUM(q2) FROM station_footfall WHERE year=2025"
                  " UNION ALL SELECT 3, SUM(q3) FROM station_footfall WHERE year=2025"
                  " UNION ALL SELECT 4, SUM(q4) FROM station_footfall WHERE year=2025)"
                  " SELECT qtr, f, f - LAG(f) OVER (ORDER BY qtr) FROM q"),
        trap_sql=("WITH q AS ("
                  " SELECT 1 qtr, SUM(q1) f FROM station_footfall WHERE year=2025"
                  " UNION ALL SELECT 2, SUM(q2) FROM station_footfall WHERE year=2025"
                  " UNION ALL SELECT 3, SUM(q3) FROM station_footfall WHERE year=2025"
                  " UNION ALL SELECT 4, SUM(q4) FROM station_footfall WHERE year=2025)"
                  " SELECT qtr, f, f - LAG(f) OVER (PARTITION BY qtr ORDER BY qtr)"
                  " FROM q"),
        note="Unpivot first and the question becomes an ordinary LAG. The trap"
             " partitions by qtr, which puts each quarter alone in its window"
             " so LAG finds no previous row and every change is NULL. Partition"
             " by what rows have in COMMON; here there is one series and"
             " nothing in common, so no PARTITION at all.",
        claims=[("four quarters, exactly one NULL change",
                 lambda rows, c: len(rows) == 4
                 and sum(1 for r in rows if r[2] is None) == 1)],
    ),
    dict(
        id=11, ledger="Q472", concept="S1", tier="3 - Unpivot and set ops",
        title="Busy in both years",
        prompt=(
            "Stations in the ten busiest by total footfall in 2023 AND still in"
            " the ten busiest in 2025.\n\n"
            "Total footfall for a year is its four quarters added up.\n\n"
            "Return: station_id"
        ),
        solution=("SELECT station_id FROM (SELECT station_id FROM"
                  " station_footfall WHERE year = 2023"
                  " ORDER BY q1+q2+q3+q4 DESC, station_id LIMIT 10)"
                  " INTERSECT"
                  " SELECT station_id FROM (SELECT station_id FROM"
                  " station_footfall WHERE year = 2025"
                  " ORDER BY q1+q2+q3+q4 DESC, station_id LIMIT 10)"),
        trap_sql=("SELECT station_id FROM (SELECT station_id FROM"
                  " station_footfall WHERE year = 2023"
                  " ORDER BY q1+q2+q3+q4 DESC, station_id LIMIT 10)"
                  " UNION"
                  " SELECT station_id FROM (SELECT station_id FROM"
                  " station_footfall WHERE year = 2025"
                  " ORDER BY q1+q2+q3+q4 DESC, station_id LIMIT 10)"),
        note="INTERSECT keeps what is in BOTH; UNION keeps what is in either."
             " Both conditions apply to the same station, so it is an"
             " intersection even though the sentence has an 'and' in it. Note"
             " each LIMIT has to live in a subquery -- a set operator applies"
             " to whole SELECTs, so a trailing LIMIT would bound the combined"
             " result rather than each side.",
        claims=[("at most ten stations, all in both years' top ten",
                 lambda rows, c: 0 < len(rows) <= 10)],
    ),
    dict(
        id=12, ledger="Q473", concept="A3", tier="3 - Unpivot and set ops",
        title="Towns on more than one line",
        prompt=(
            "Towns whose stations are served by more than one line.\n\n"
            "A town may have several stations; count the DISTINCT lines"
            " reaching any of them. 13 towns qualify.\n\n"
            "Return: town, lines"
        ),
        solution=("SELECT st.town, COUNT(DISTINCT sv.line_id) FROM stations st"
                  " JOIN stops p ON p.station_id = st.station_id"
                  " JOIN services sv ON sv.service_id = p.service_id"
                  " GROUP BY st.town HAVING COUNT(DISTINCT sv.line_id) > 1"),
        trap_sql=("SELECT st.town, COUNT(sv.line_id) FROM stations st"
                  " JOIN stops p ON p.station_id = st.station_id"
                  " JOIN services sv ON sv.service_id = p.service_id"
                  " GROUP BY st.town HAVING COUNT(sv.line_id) > 1"),
        note="After joining down to services, each town has one row per STOP --"
             " thousands of them -- so COUNT(line_id) counts stops and 'more"
             " than one' is true of everything. DISTINCT inside the aggregate"
             " is what counts lines, and it has to appear in the HAVING too:"
             " the two are separate expressions and SQLite will not infer one"
             " from the other.",
        claims=[("13 towns, every one on at least two lines",
                 lambda rows, c: len(rows) == 13
                 and all(r[1] > 1 for r in rows))],
    ),
    dict(
        id=13, ledger="Q474", concept="N1", tier="3 - Unpivot and set ops",
        title="Stations nobody buys a ticket to",
        prompt=(
            "Stations that are not the destination of a single ticket.\n\n"
            "tickets.to_station is NULL on open tickets, where no destination"
            " was chosen. There are 23 such stations -- if you get 0 rows, the"
            " NULLs are the reason, and the note explains why.\n\n"
            "Return: station_id"
        ),
        solution=("SELECT station_id FROM stations"
                  " EXCEPT SELECT to_station FROM tickets"),
        trap_sql=("SELECT station_id FROM stations WHERE station_id NOT IN"
                  " (SELECT to_station FROM tickets)"),
        note="NOT IN over a list containing NULL returns no rows at all. 'x is"
             " not in this list' is answered by testing x <> each entry, and"
             " x <> NULL is NULL, not true -- so SQLite can never conclude the"
             " station is absent. One unknown destination among 40,441 tickets"
             " silences the whole query. EXCEPT does not work that way: it"
             " compares values and treats NULL as an ordinary one, so it"
             " simply never matches a station_id. NOT EXISTS is safe for the"
             " same reason.",
        claims=[("23 stations",
                 lambda rows, c: len(rows) == 23),
                ("none of them is a ticket destination",
                 lambda rows, c: not c.execute(
                     "SELECT 1 FROM tickets WHERE to_station IN (%s) LIMIT 1"
                     % ",".join(str(int(r[0])) for r in rows)).fetchall()
                 if rows else False)],
    ),
    # ===================================================== 4 Dates and times
    dict(
        id=14, ledger="Q475", concept="D1", tier="4 - Dates and times",
        title="When tickets are bought",
        prompt=(
            "How many tickets were sold on each day of the week, named rather"
            " than numbered. Seven rows.\n\n"
            "Return: day_name, tickets"
        ),
        solution=("SELECT CASE strftime('%w', sold_at)"
                  " WHEN '0' THEN 'Sunday' WHEN '1' THEN 'Monday'"
                  " WHEN '2' THEN 'Tuesday' WHEN '3' THEN 'Wednesday'"
                  " WHEN '4' THEN 'Thursday' WHEN '5' THEN 'Friday'"
                  " ELSE 'Saturday' END, COUNT(*)"
                  " FROM tickets GROUP BY strftime('%w', sold_at)"),
        trap_sql=("SELECT CASE strftime('%W', sold_at)"
                  " WHEN '0' THEN 'Sunday' WHEN '1' THEN 'Monday'"
                  " WHEN '2' THEN 'Tuesday' WHEN '3' THEN 'Wednesday'"
                  " WHEN '4' THEN 'Thursday' WHEN '5' THEN 'Friday'"
                  " ELSE 'Saturday' END, COUNT(*)"
                  " FROM tickets GROUP BY strftime('%W', sold_at)"),
        note="strftime's format letters are case-sensitive and %w and %W are"
             " unrelated: lowercase is day of week 0-6, uppercase is week of"
             " year 00-53. The uppercase version buckets the data into 50-odd"
             " groups and labels the first six with day names, which looks"
             " plausible until you count the rows.",
        claims=[("seven days covering every ticket",
                 lambda rows, c: len(rows) == 7
                 and sum(r[1] for r in rows) == 40441)],
    ),
    dict(
        id=15, ledger="Q476", concept="D1", tier="4 - Dates and times",
        title="Younger than the oldest station",
        prompt=(
            "The five stations that opened LONGEST after the network's oldest"
            " station, in whole years.\n\n"
            "Longest first; break ties by station_id.\n\n"
            "Return: station_id, name, years_after"
        ),
        solution=("SELECT station_id, name,"
                  " CAST((julianday(opened_on)"
                  " - julianday((SELECT MIN(opened_on) FROM stations)))"
                  " / 365.25 AS INTEGER) AS yrs FROM stations"
                  " ORDER BY yrs DESC, station_id LIMIT 5"),
        trap_sql=("SELECT station_id, name,"
                  " CAST((opened_on - (SELECT MIN(opened_on) FROM stations))"
                  " / 365.25 AS INTEGER) AS yrs FROM stations"
                  " ORDER BY yrs DESC, station_id LIMIT 5"),
        note="Dates are TEXT, so subtracting them coerces each to a number --"
             " '1993-09-15' reads as 1993 -- and the trap ends up dividing a"
             " difference of years by 365.25, giving 0 for everything."
             " julianday() converts to a day count first. The scalar subquery"
             " runs once, not per row, because it references nothing from the"
             " outer query.",
        claims=[("five rows, all positive",
                 lambda rows, c: len(rows) == 5
                 and all(r[2] > 0 for r in rows))],
    ),
    dict(
        id=16, ledger="Q477", concept="D1", tier="4 - Dates and times",
        title="Services on the last day of the month",
        prompt=(
            "How many services ran on the final calendar day of each month.\n\n"
            "Build that day with date modifiers rather than assuming 30 or 31."
            " One row per month that has any.\n\n"
            "Return: month, services"
        ),
        solution=("SELECT strftime('%Y-%m', run_date), COUNT(*) FROM services"
                  " WHERE run_date = date(run_date, 'start of month',"
                  " '+1 month', '-1 day') GROUP BY 1"),
        trap_sql=("SELECT strftime('%Y-%m', run_date), COUNT(*) FROM services"
                  " WHERE strftime('%d', run_date) = '31' GROUP BY 1"),
        note="'start of month' then '+1 month' then '-1 day' lands on the last"
             " day of whatever month you started in -- correct in February and"
             " in leap years, with no knowledge of month lengths. The trap"
             " assumes 31 and silently loses every 30-day month and February"
             " entirely. Modifiers apply left to right, and there is no"
             " 'end of month'.",
        claims=[("every month in the data appears",
                 lambda rows, c: len(rows) == c.execute(
                     "SELECT COUNT(DISTINCT strftime('%Y-%m', run_date))"
                     " FROM services").fetchone()[0])],
    ),
    dict(
        id=17, ledger="Q478", concept="D1", tier="4 - Dates and times",
        title="Early or late in the month",
        prompt=(
            "How many incidents were reported in the first half of a month"
            " (day 1 to 15) and how many in the second.\n\n"
            "Two rows.\n\n"
            "Return: half, incidents"
        ),
        solution=("SELECT CASE WHEN CAST(strftime('%d', reported_at)"
                  " AS INTEGER) <= 15 THEN 'first' ELSE 'second' END,"
                  " COUNT(*) FROM incidents GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN strftime('%d', reported_at) <= 15"
                  " THEN 'first' ELSE 'second' END, COUNT(*)"
                  " FROM incidents GROUP BY 1"),
        note="strftime returns TEXT, and SQLite never compares text against an"
             " integer as numbers -- an integer always sorts below any text, so"
             " '05' <= 15 is FALSE and every incident lands in 'second'. Either"
             " CAST the text to an integer or compare against a quoted"
             " zero-padded string. The zero padding is why '9' <= '15' would"
             " also be wrong as plain text.",
        claims=[("two halves covering all 1,143 incidents",
                 lambda rows, c: len(rows) == 2
                 and sum(r[1] for r in rows) == 1143)],
    ),
    # ====================================================== 5 Joins and grain
    dict(
        id=18, ledger="Q479", concept="J2", tier="5 - Joins and grain",
        title="Step-free stations nobody calls at",
        prompt=(
            "Stations recorded as step-free that no service ever calls at.\n\n"
            "Write the 'never called at' part as an outer join that keeps the"
            " non-matches.\n\n"
            "Return: station_id, name"
        ),
        solution=("SELECT s.station_id, s.name FROM stations s"
                  " LEFT JOIN stops p ON p.station_id = s.station_id"
                  " WHERE p.service_id IS NULL AND s.step_free = 1"),
        trap_sql=("SELECT s.station_id, s.name FROM stations s"
                  " LEFT JOIN stops p ON p.station_id = s.station_id"
                  " AND p.service_id IS NULL WHERE s.step_free = 1"),
        note="The two conditions belong in different places, which is the"
             " point. step_free is a fact about the LEFT table, so it filters"
             " in WHERE either way. The IS NULL test is about whether the join"
             " matched, so it must run AFTER the join -- move it into ON and it"
             " becomes part of what counts as a match, matches nothing, and"
             " every step-free station comes back.",
        claims=[("every returned station is step-free and never called at",
                 lambda rows, c: len(rows) > 0 and all(
                     c.execute("SELECT step_free FROM stations WHERE"
                               " station_id = ?", (r[0],)).fetchone()[0] == 1
                     and c.execute("SELECT COUNT(*) FROM stops WHERE"
                                   " station_id = ?",
                                   (r[0],)).fetchone()[0] == 0 for r in rows))],
    ),
    dict(
        id=19, ledger="Q480", concept="C2", tier="5 - Joins and grain",
        title="Seats offered by each line",
        prompt=(
            "One row per line: the total number of seats it has run, counting"
            " every unit on every service.\n\n"
            "A service may be formed of more than one unit, and each unit has"
            " its own seat count.\n\n"
            "Return: line_name, seats"
        ),
        solution=("SELECT l.name, SUM(r.seats) FROM lines l"
                  " JOIN services sv ON sv.line_id = l.line_id"
                  " JOIN service_units u ON u.service_id = sv.service_id"
                  " JOIN rolling_stock r ON r.unit_id = u.unit_id"
                  " GROUP BY l.name"),
        trap_sql=("SELECT l.name, SUM(r.seats) FROM lines l"
                  " JOIN services sv ON sv.line_id = l.line_id"
                  " JOIN service_units u ON u.service_id = sv.service_id"
                  " JOIN rolling_stock r ON r.unit_id = u.unit_id"
                  " JOIN stops p ON p.service_id = sv.service_id"
                  " GROUP BY l.name"),
        note="A four-table descent with no fan-out: line to service to"
             " service_unit to unit, one parent to many children each time, so"
             " SUM is a true total. The trap adds stops -- a second child of"
             " services alongside service_units -- and every seat count is"
             " multiplied by the number of stops on its journey. Adding a table"
             " you do not select from can still change every number.",
        claims=[("six lines, totalling every unit-service pairing's seats",
                 lambda rows, c: len(rows) == 6 and sum(r[1] for r in rows)
                 == c.execute("SELECT SUM(r.seats) FROM service_units u JOIN"
                              " rolling_stock r ON r.unit_id = u.unit_id"
                              ).fetchone()[0])],
    ),
    dict(
        id=20, ledger="Q481", concept="J2", tier="5 - Joins and grain",
        title="Staff based at each station",
        prompt=(
            "One row for every station: its name, and how many staff are based"
            " there.\n\n"
            "Most stations have none. They must appear with 0, so all 60"
            " stations come back.\n\n"
            "Return: name, staff"
        ),
        solution=("SELECT s.name, COUNT(sf.staff_id) FROM stations s"
                  " LEFT JOIN staff sf ON sf.base_station = s.station_id"
                  " GROUP BY s.station_id, s.name"),
        trap_sql=("SELECT s.name, COUNT(*) FROM stations s"
                  " LEFT JOIN staff sf ON sf.base_station = s.station_id"
                  " GROUP BY s.station_id, s.name"),
        note="COUNT(*) counts rows, and a LEFT JOIN with no match still"
             " produces one -- the station padded with NULLs. So every station"
             " gets at least 1 and a genuine zero becomes impossible."
             " COUNT(a column from the right side) counts values instead, and"
             " the padded NULL contributes nothing.",
        claims=[("all 60 stations, 31 of them with none",
                 lambda rows, c: len(rows) == 60
                 and sum(1 for r in rows if r[1] == 0) == 31),
                ("the counts total the workforce",
                 lambda rows, c: sum(r[1] for r in rows) == 40)],
    ),
    dict(
        id=21, ledger="Q482", concept="C2", tier="5 - Joins and grain",
        title="Tickets and incidents per operator",
        prompt=(
            "One row per operator: how many tickets were sold on its services,"
            " and how many incidents were reported on them.\n\n"
            "Both hang off services but are independent of each other.\n\n"
            "Return: operator_name, tickets, incidents"
        ),
        solution=("SELECT o.name,"
                  " (SELECT COUNT(*) FROM tickets t JOIN services sv"
                  " ON sv.service_id = t.service_id"
                  " WHERE sv.operator_id = o.operator_id),"
                  " (SELECT COUNT(*) FROM incidents i JOIN services sv"
                  " ON sv.service_id = i.service_id"
                  " WHERE sv.operator_id = o.operator_id)"
                  " FROM operators o"),
        trap_sql=("SELECT o.name, COUNT(t.ticket_id), COUNT(i.incident_id)"
                  " FROM operators o"
                  " JOIN services sv ON sv.operator_id = o.operator_id"
                  " LEFT JOIN tickets t ON t.service_id = sv.service_id"
                  " LEFT JOIN incidents i ON i.service_id = sv.service_id"
                  " GROUP BY o.name"),
        note="Joining two children of the same parent multiplies them: a"
             " service with 3 tickets and 2 incidents yields 6 rows, so the"
             " ticket count comes out doubled and the incident count tripled."
             " COUNT(DISTINCT ...) would paper over it here but a SUM could"
             " not. Two independent measures want two independent subqueries.",
        claims=[("four operators, both totals matching their tables",
                 lambda rows, c: len(rows) == 4
                 and sum(r[1] for r in rows) == 40441
                 and sum(r[2] for r in rows) == 1143)],
    ),
    dict(
        id=22, ledger="Q483", concept="S1", tier="5 - Joins and grain",
        title="Units that have run in both positions",
        prompt=(
            "Units that have run in position 1 AND also in position 2.\n\n"
            "Return: unit_id"
        ),
        solution=("SELECT unit_id FROM service_units WHERE position = 1"
                  " INTERSECT"
                  " SELECT unit_id FROM service_units WHERE position = 2"),
        trap_sql=("SELECT DISTINCT unit_id FROM service_units"
                  " WHERE position = 1 AND position = 2"),
        note="One row cannot have position 1 and 2 at once, so the trap's AND"
             " is a contradiction and returns nothing. The condition is about"
             " the UNIT across many rows, not about a single row -- which is"
             " what set operators, or two EXISTS clauses, are for. Whenever an"
             " AND on one column returns zero rows, that is the shape of the"
             " mistake.",
        claims=[("every returned unit really has run in both",
                 lambda rows, c: len(rows) > 0 and all(
                     c.execute("SELECT COUNT(DISTINCT position) FROM"
                               " service_units WHERE unit_id = ?",
                               (r[0],)).fetchone()[0] == 2 for r in rows))],
    ),
    # ================================================ 6 Windows and recursion
    dict(
        id=23, ledger="Q484", concept="W1", tier="6 - Windows and recursion",
        title="Ticket sales accumulating",
        prompt=(
            "One row per month in which any ticket was sold: the month as"
            " 'YYYY-MM', how many were sold, and the running total up to and"
            " including that month.\n\n"
            "The last month's running total is every ticket.\n\n"
            "Return: month, tickets, running_total"
        ),
        solution=("WITH m AS (SELECT strftime('%Y-%m', sold_at) AS mth,"
                  " COUNT(*) AS n FROM tickets GROUP BY 1)"
                  " SELECT mth, n, SUM(n) OVER (ORDER BY mth) FROM m"),
        trap_sql=("WITH m AS (SELECT strftime('%Y-%m', sold_at) AS mth,"
                  " COUNT(*) AS n FROM tickets GROUP BY 1)"
                  " SELECT mth, n, SUM(n) OVER () FROM m"),
        note="ORDER BY inside OVER() is the whole difference. With no ORDER BY"
             " the window is every row at once, so the same grand total repeats"
             " on every line; with it, the frame defaults to everything up to"
             " the current row. A running total over positive numbers can only"
             " ever go up -- if yours is flat, the ORDER BY is missing.",
        claims=[("the last running total is every ticket",
                 lambda rows, c: max(r[2] for r in rows) == 40441)],
    ),
    dict(
        id=24, ledger="Q485", concept="W3", tier="6 - Windows and recursion",
        title="Each unit's share of its model's work",
        prompt=(
            "One row per unit that has ever run: its id, its model, how many"
            " service-slots it has filled, and that as a percentage of all"
            " slots filled by units of the SAME model.\n\n"
            "Within each model the percentages add up to 100.\n\n"
            "Return: unit_id, model, slots, pct_of_model"
        ),
        solution=("WITH u AS (SELECT r.unit_id, r.model, COUNT(*) AS n"
                  " FROM service_units su"
                  " JOIN rolling_stock r ON r.unit_id = su.unit_id"
                  " GROUP BY r.unit_id, r.model)"
                  " SELECT unit_id, model, n,"
                  " ROUND(100.0 * n / SUM(n) OVER (PARTITION BY model), 2)"
                  " FROM u"),
        trap_sql=("WITH u AS (SELECT r.unit_id, r.model, COUNT(*) AS n"
                  " FROM service_units su"
                  " JOIN rolling_stock r ON r.unit_id = su.unit_id"
                  " GROUP BY r.unit_id, r.model)"
                  " SELECT unit_id, model, n,"
                  " ROUND(100.0 * n / SUM(n) OVER (), 2) FROM u"),
        note="This is the case where PARTITION BY is required rather than"
             " forbidden. OVER () would divide by the fleet-wide total, giving"
             " each unit's share of ALL work rather than of its model's --"
             " plausible numbers that sum to 100 across the whole result"
             " instead of within each model. Partition by whatever the"
             " denominator is supposed to be grouped by.",
        claims=[("each model's percentages sum to 100",
                 lambda rows, c: all(
                     abs(sum(r[3] for r in rows if r[1] == m) - 100) < 0.1
                     for m in {r[1] for r in rows}))],
    ),
    dict(
        id=25, ledger="Q486", concept="R1", tier="6 - Windows and recursion",
        title="Everyone under one manager",
        prompt=(
            "Every member of staff below Nerys Fothergill in the reporting"
            " tree -- their reports, their reports' reports, and so"
            " on.\n\n"
            "They are not in the answer. Only three of the 18 report to them"
            " directly, which is why a single join is not enough.\n\n"
            "Return: staff_id, name"
        ),
        solution=("WITH RECURSIVE below(id, name) AS ("
                  " SELECT staff_id, name FROM staff WHERE reports_to ="
                  " (SELECT staff_id FROM staff"
                  " WHERE name = 'Nerys Fothergill')"
                  " UNION ALL"
                  " SELECT s.staff_id, s.name FROM staff s"
                  " JOIN below b ON s.reports_to = b.id)"
                  " SELECT id, name FROM below"),
        trap_sql=("SELECT s.staff_id, s.name FROM staff s"
                  " WHERE s.reports_to = (SELECT staff_id FROM staff"
                  " WHERE name = 'Nerys Fothergill')"),
        note="The plain query gives the three direct reports and stops. The"
             " recursion"
             " carries on: each pass takes whoever was found last time and"
             " looks for people reporting to them, until a pass finds nobody."
             " Note the step's SELECT draws from `staff`, not from `below` -- a"
             " step that only selects from the CTE hands back what it was given"
             " and either loops forever or stops at the anchor.",
        claims=[("18 people, three levels of them",
                 lambda rows, c: len(rows) == 18
                 and not any(r[1] == 'Nerys Fothergill' for r in rows))],
    ),
    dict(
        id=26, ledger="Q487", concept="W2", tier="6 - Windows and recursion",
        title="Stations by footfall quartile",
        prompt=(
            "Every station's 2025 total footfall, with which quarter of the"
            " network it falls into: 1 for the busiest quarter, 4 for the"
            " quietest.\n\n"
            "60 stations split evenly into four groups of 15.\n\n"
            "Return: station_id, footfall, quartile"
        ),
        solution=("SELECT station_id, q1+q2+q3+q4,"
                  " NTILE(4) OVER (ORDER BY q1+q2+q3+q4 DESC)"
                  " FROM station_footfall WHERE year = 2025"),
        trap_sql=("SELECT station_id, q1+q2+q3+q4,"
                  " NTILE(4) OVER (ORDER BY q1+q2+q3+q4)"
                  " FROM station_footfall WHERE year = 2025"),
        note="NTILE deals rows into buckets in the order you give it, so the"
             " ORDER BY direction decides which end gets bucket 1. Ascending"
             " puts the QUIETEST station in bucket 1 -- the numbers look"
             " perfectly reasonable and mean the opposite of what was asked."
             " Whenever a question says busiest or top, say DESC out loud and"
             " check it is inside the OVER clause.",
        claims=[("60 stations in four groups of 15",
                 lambda rows, c: len(rows) == 60
                 and all(sum(1 for r in rows if r[2] == q) == 15
                         for q in (1, 2, 3, 4))),
                ("quartile 1 is busier than quartile 4",
                 lambda rows, c: min(r[1] for r in rows if r[2] == 1)
                 > max(r[1] for r in rows if r[2] == 4))],
    ),
    # =================================================== 7 Query efficiency
    # Each starter is a JOIN or an aggregate across two or three tables, so the
    # plan runs to four or five lines and the first job is finding which one is
    # expensive. Graded on the plan as well as the rows; Reset restores the
    # starter.
    dict(
        id=27, ledger="Q488", concept="X1", tier="7 - Query efficiency",
        title="One function, three tables slower",
        prompt=(
            "Total ticket revenue in pence for each line, counting only"
            " services that ran during 2025.\n\n"
            "The editor's query is correct and reads all 40,441 tickets to do"
            " it. services.run_date is indexed. Look at the FIRST line of the"
            " plan -- it says which table the whole join is driven from, and"
            " fixing the filter changes it. Your plan must not contain"
            " 'SCAN'.\n\n"
            "Return: line_name, revenue_pence"
        ),
        solution=("SELECT l.name, SUM(t.price_pence) FROM lines l"
                  " JOIN services s ON s.line_id = l.line_id"
                  " JOIN tickets t ON t.service_id = s.service_id"
                  " WHERE s.run_date >= '2025-01-01'"
                  " AND s.run_date < '2026-01-01' GROUP BY 1"),
        trap_sql=("SELECT l.name, SUM(t.price_pence) FROM lines l"
                  " JOIN services s ON s.line_id = l.line_id"
                  " JOIN tickets t ON t.service_id = s.service_id"
                  " WHERE strftime('%Y', s.run_date) = '2025' GROUP BY 1"),
        starter_sql=("SELECT l.name, SUM(t.price_pence) FROM lines l"
                     " JOIN services s ON s.line_id = l.line_id"
                     " JOIN tickets t ON t.service_id = s.service_id"
                     " WHERE strftime('%Y', s.run_date) = '2025' GROUP BY 1"),
        plan_forbids=("SCAN",),
        note="Blocking an index does not merely slow one lookup -- it changes"
             " the STRATEGY. With strftime() wrapped round run_date there is no"
             " seekable range, so SQLite cannot start from services; it scans"
             " all 40,441 tickets instead and looks each service up. Rewrite"
             " the filter as a range on the bare column and services becomes"
             " the driving table, with tickets reached by index. The first line"
             " of the plan is the one to read.",
        claims=[("six lines, matching the strftime version's totals",
                 lambda rows, c: len(rows) == 6
                 and sorted(r[1] for r in rows) == sorted(
                     x[1] for x in c.execute(
                         "SELECT l.name, SUM(t.price_pence) FROM lines l"
                         " JOIN services s ON s.line_id = l.line_id"
                         " JOIN tickets t ON t.service_id = s.service_id"
                         " WHERE strftime('%Y', s.run_date) = '2025'"
                         " GROUP BY 1")))],
    ),
    dict(
        id=28, ledger="Q489", concept="X2", tier="7 - Query efficiency",
        title="Twenty rows, forty thousand sorted",
        prompt=(
            "The 20 earliest-sold ticket ids, of tickets attached to a"
            " service.\n\n"
            "Every ticket has a service, so the join changes nothing about"
            " which rows qualify -- but the editor's query still sorts all"
            " 40,441 to return 20. tickets.sold_at is indexed. Your plan must"
            " not contain 'TEMP B-TREE'.\n\n"
            "Return: ticket_id"
        ),
        solution=("SELECT t.ticket_id FROM tickets t"
                  " JOIN services s ON s.service_id = t.service_id"
                  " ORDER BY t.sold_at, t.ticket_id LIMIT 20"),
        trap_sql=("SELECT t.ticket_id FROM tickets t"
                  " JOIN services s ON s.service_id = t.service_id"
                  " ORDER BY t.sold_at || '', t.ticket_id LIMIT 20"),
        starter_sql=("SELECT t.ticket_id FROM tickets t"
                     " JOIN services s ON s.service_id = t.service_id"
                     " ORDER BY t.sold_at || '', t.ticket_id LIMIT 20"),
        plan_forbids=("TEMP B-TREE",),
        note="In a join only ONE table can be walked in index order -- the one"
             " driving it. Order by that table's indexed column and the LIMIT"
             " can stop after 20 entries; order by any EXPRESSION over it and"
             " the index is no longer in the right order, so every joined row"
             " must be produced and sorted before the first result is known."
             " 500x here, for the same twenty ids.",
        claims=[("twenty rows in ascending sold_at order",
                 lambda rows, c: len(rows) == 20)],
    ),
    dict(
        id=29, ledger="Q490", concept="X6", tier="7 - Query efficiency",
        title="Reformatting a date that was already formatted",
        prompt=(
            "Daily ticket revenue: one row per run_date with the total pence"
            " taken on services running that day.\n\n"
            "run_date is already stored as 'YYYY-MM-DD', and it is indexed. The"
            " editor's query formats it again before grouping, which costs both"
            " a sort and the chance to drive the join from services. Same 546"
            " rows either way. Your plan must not contain 'TEMP B-TREE'.\n\n"
            "Return: run_date, revenue_pence"
        ),
        solution=("SELECT s.run_date, SUM(t.price_pence) FROM services s"
                  " JOIN tickets t ON t.service_id = s.service_id"
                  " GROUP BY s.run_date"),
        trap_sql=("SELECT strftime('%Y-%m-%d', s.run_date),"
                  " SUM(t.price_pence) FROM services s"
                  " JOIN tickets t ON t.service_id = s.service_id GROUP BY 1"),
        starter_sql=("SELECT strftime('%Y-%m-%d', s.run_date),"
                     " SUM(t.price_pence) FROM services s"
                     " JOIN tickets t ON t.service_id = s.service_id"
                     " GROUP BY 1"),
        plan_forbids=("TEMP B-TREE",),
        note="strftime('%Y-%m-%d', x) on a column already in that format"
             " returns identical VALUES and a different EXPRESSION -- and the"
             " index is on the column. So the grouping can no longer be"
             " satisfied by walking idx_services_date in order, and SQLite"
             " builds a temp b-tree AND drives the join from tickets instead."
             " Worth checking any format call: if the column is already in the"
             " shape you want, the call is pure cost.",
        claims=[("546 days, totalling every ticket's price",
                 lambda rows, c: len(rows) == 546
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT SUM(price_pence) FROM tickets").fetchone()[0])],
    ),
    dict(
        id=30, ledger="Q491", concept="X7", tier="7 - Query efficiency",
        title="The CTE that computes too much",
        prompt=(
            "For every service on line 2, how many tickets it sold -- 0 if"
            " none.\n\n"
            "The editor's query aggregates the WHOLE ticket table in a CTE and"
            " then joins one line's worth of it. A materialised CTE cannot see"
            " the outer filter, so it does 40,441 rows of work to answer a"
            " question about 2,000. Your plan must not contain 'MATERIALIZE'."
            "\n\nReturn: service_id, tickets"
        ),
        solution=("SELECT s.service_id, (SELECT COUNT(*) FROM tickets t"
                  " WHERE t.service_id = s.service_id)"
                  " FROM services s WHERE s.line_id = 2"),
        trap_sql=("WITH n AS (SELECT service_id, COUNT(*) c FROM tickets"
                  " GROUP BY 1)"
                  " SELECT s.service_id, COALESCE(n.c, 0) FROM services s"
                  " LEFT JOIN n ON n.service_id = s.service_id"
                  " WHERE s.line_id = 2"),
        starter_sql=("WITH n AS (SELECT service_id, COUNT(*) c FROM tickets"
                     " GROUP BY 1)"
                     " SELECT s.service_id, COALESCE(n.c, 0) FROM services s"
                     " LEFT JOIN n ON n.service_id = s.service_id"
                     " WHERE s.line_id = 2"),
        plan_forbids=("MATERIALIZE",),
        note="This one runs against the usual advice twice over. Pulling an"
             " aggregate into a CTE is normally good practice, and rewriting a"
             " correlated subquery as a join is normally an improvement -- here"
             " both are wrong. MATERIALIZE in a plan means SQLite built the"
             " whole subquery result before using any of it, so the outer"
             " WHERE could not narrow it. The correlated form asks only about"
             " the services it actually wants: 4x faster.",
        claims=[("every service on line 2",
                 lambda rows, c: len(rows) == c.execute(
                     "SELECT COUNT(*) FROM services WHERE line_id = 2"
                 ).fetchone()[0]),
                ("the ticket counts match the CTE version",
                 lambda rows, c: sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM tickets t JOIN services s"
                     " ON s.service_id = t.service_id"
                     " WHERE s.line_id = 2").fetchone()[0])],
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
