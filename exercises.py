"""Practice exercises with reference solutions, used by the GUI to grade answers.

These 30 questions (ledger Q432-Q461) run on the railway schema, re-seeded
(SEED 401 -> 437) so every value differs from the last set. The tables are the
same, and so is the difficulty.

Two things changed in the balance:

  * the efficiency stage is down from six questions to FOUR, and the slots go
    back to the other tiers -- windows and recursion in particular, which had
    only two questions last time and now has four
  * every question is new. The schema supports far more than one set could
    use, so this leans on shapes the last set left alone: LAST_VALUE and its
    frame, journey durations, unpivoting to find each station's busiest
    quarter, a recursive walk that builds a string as it goes

The four efficiency questions still open with a query already in the editor --
correct, but taking a slow route -- and are graded on their EXPLAIN QUERY PLAN
as well as their rows. The Reset button puts the original back.

They are four different causes, and the third deliberately contradicts the last
set:

  27  add a predicate that filters NOTHING, to reach a composite index
  28  mixed ORDER BY directions cannot walk one index
  29  here the JOIN beats NOT EXISTS -- the opposite of Q431, because this
      index does not cover the whole inner condition
  30  DISTINCT on a bare column, so the index supplies the deduplication

Question 29 is the one worth sitting with. The last set taught that a
correlated NOT EXISTS beats a LEFT JOIN anti-join; this one is the same shape
on the same schema and the advice reverses, because `stops` is indexed on
station_id alone and the inner condition also tests stop_seq. The rule was
never "prefer NOT EXISTS" -- it is "check whether the index covers what the
subquery asks".

Each question carries:

  concept   the mistake or technique it drills
  solution  one correct answer
  trap_sql  the tempting WRONG query -- check_questions.py asserts the grader
            rejects it
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
        id=1, ledger="Q432", concept="A2", tier="1 - Warm-up",
        title="Refurbished, and not",
        prompt=(
            "One row per model of rolling stock: how many units exist, and how"
            " many of those have been refurbished.\n\n"
            "refurbished_year is NULL for a unit that never has been. One"
            " table, no joins.\n\n"
            "Return: model, units, refurbished"
        ),
        solution=("SELECT model, COUNT(*), COUNT(refurbished_year)"
                  " FROM rolling_stock GROUP BY model"),
        trap_sql=("SELECT model, COUNT(*), COUNT(*)"
                  " FROM rolling_stock GROUP BY model"),
        note="COUNT(*) counts rows; COUNT(column) counts rows where that column"
             " is not NULL. That single difference is the cheapest way to ask"
             " 'how many of these have a value' -- no CASE, no subquery.",
        claims=[("units total the fleet, refurbished is fewer",
                 lambda rows, c: sum(r[1] for r in rows) == 50
                 and sum(r[2] for r in rows) < 50)],
    ),
    dict(
        id=2, ledger="Q433", concept="general", tier="1 - Warm-up",
        title="Stations by the decade they opened",
        prompt=(
            "How many stations opened in each decade, as a label like"
            " '1890s'.\n\n"
            "opened_on is a date. All 60 stations land in exactly one"
            " decade.\n\n"
            "Return: decade, stations"
        ),
        solution=("SELECT ((strftime('%Y', opened_on) / 10) * 10) || 's',"
                  " COUNT(*) FROM stations GROUP BY 1"),
        trap_sql=("SELECT strftime('%Y', opened_on) || 's', COUNT(*)"
                  " FROM stations GROUP BY 1"),
        note="Integer division is the trick: dividing a year by 10 discards the"
             " units digit, and multiplying back gives the decade. It works"
             " because strftime returns text that SQLite coerces to a number"
             " for the arithmetic. Mind the brackets: || binds TIGHTER than *"
             " in SQLite, so without them the expression parses as"
             " (year/10) * (10 || 's'), the '10s' coerces back to 10, and you"
             " get a bare integer year with no suffix at all.",
        claims=[("all 60 stations, in fewer than 60 decades",
                 lambda rows, c: sum(r[1] for r in rows) == 60
                 and len(rows) < 60),
                ("every label ends in s",
                 lambda rows, c: all(r[0].endswith('s') for r in rows))],
    ),
    dict(
        id=3, ledger="Q434", concept="A3", tier="1 - Warm-up",
        title="Roles that are numerous and well paid",
        prompt=(
            "Roles with more than 5 staff whose average salary is above"
            " 32000.\n\n"
            "Both conditions are about the role as a whole. One table, no"
            " joins.\n\n"
            "Return: role, staff, avg_salary"
        ),
        solution=("SELECT role, COUNT(*), ROUND(AVG(salary), 2) FROM staff"
                  " GROUP BY role HAVING COUNT(*) > 5 AND AVG(salary) > 32000"),
        trap_sql=("SELECT role, COUNT(*), ROUND(AVG(salary), 2) FROM staff"
                  " WHERE salary > 32000 GROUP BY role HAVING COUNT(*) > 5"),
        note="Both tests are about the GROUP, so both belong in HAVING. The"
             " trap moves the salary test into WHERE, which throws away the"
             " individual low earners BEFORE grouping -- so the counts are of"
             " high earners only and the averages are of a filtered subset."
             " A role with six staff, four of them well paid, would be counted"
             " as having four.",
        claims=[("every row clears both bars",
                 lambda rows, c: len(rows) > 0
                 and all(r[1] > 5 and r[2] > 32000 for r in rows))],
    ),
    dict(
        id=4, ledger="Q435", concept="A2", tier="1 - Warm-up",
        title="What a ticket costs, by class",
        prompt=(
            "One row per class: the cheapest, dearest and average ticket price"
            " in POUNDS.\n\n"
            "price_pence holds whole pence. Average to two decimals; the min"
            " and max are exact.\n\n"
            "Return: class, cheapest, dearest, average"
        ),
        solution=("SELECT class, MIN(price_pence) / 100.0,"
                  " MAX(price_pence) / 100.0,"
                  " ROUND(AVG(price_pence) / 100.0, 2)"
                  " FROM tickets GROUP BY class"),
        trap_sql=("SELECT class, MIN(price_pence) / 100,"
                  " MAX(price_pence) / 100, ROUND(AVG(price_pence) / 100, 2)"
                  " FROM tickets GROUP BY class"),
        note="Money stored as integer pence is exact -- which is the whole"
             " reason to store it that way -- right up until you divide."
             " price_pence and 100 are both integers, so / 100 truncates and"
             " the pence vanish. / 100.0 makes one operand a float and the"
             " whole expression follows. ROUND cannot rescue it: by the time"
             " ROUND sees the value the decimals are already gone.",
        claims=[("three classes, and every average has pence",
                 lambda rows, c: len(rows) == 3
                 and any(abs(r[3] - round(r[3])) > 0.001 for r in rows))],
    ),
    # =============================================== 2 Sequences and strings
    dict(
        id=5, ledger="Q436", concept="D1", tier="2 - Sequences and strings",
        title="The five longest journeys",
        prompt=(
            "The five services that take the longest from their first"
            " scheduled arrival to their last, in minutes.\n\n"
            "Longest first; break ties by the lower service_id.\n\n"
            "Return: service_id, minutes"
        ),
        solution=("SELECT service_id,"
                  " (strftime('%s', MAX(sched_arrive))"
                  " - strftime('%s', MIN(sched_arrive))) / 60 AS mins"
                  " FROM stops GROUP BY service_id"
                  " ORDER BY mins DESC, service_id LIMIT 5"),
        trap_sql=("SELECT service_id,"
                  " MAX(sched_arrive) - MIN(sched_arrive) AS mins"
                  " FROM stops GROUP BY service_id"
                  " ORDER BY mins DESC, service_id LIMIT 5"),
        note="'HH:MM' is text. Subtracting one from another coerces both to"
             " numbers -- '09:47' reads as 9 -- so the answer is a difference"
             " in hours-as-integers, mostly 0. strftime('%s', ...) converts to"
             " seconds, and the difference between two of those divided by 60"
             " is minutes. The division is exact here because both times are"
             " whole minutes.",
        claims=[("five rows, all positive whole minutes",
                 lambda rows, c: len(rows) == 5
                 and all(r[1] > 0 for r in rows))],
    ),
    dict(
        id=6, ledger="Q437", concept="W2", tier="2 - Sequences and strings",
        title="Where this service ends up",
        prompt=(
            "For service 1, every stop with the name of the station the service"
            " FINISHES at -- repeated on every row.\n\n"
            "Return: stop_seq, station, destination"
        ),
        solution=("SELECT s.stop_seq, sta.name,"
                  " LAST_VALUE(sta.name) OVER (ORDER BY s.stop_seq"
                  " ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)"
                  " FROM stops s JOIN stations sta"
                  " ON sta.station_id = s.station_id WHERE s.service_id = 1"),
        trap_sql=("SELECT s.stop_seq, sta.name,"
                  " LAST_VALUE(sta.name) OVER (ORDER BY s.stop_seq)"
                  " FROM stops s JOIN stations sta"
                  " ON sta.station_id = s.station_id WHERE s.service_id = 1"),
        note="LAST_VALUE with no frame clause returns the CURRENT row, not the"
             " last one -- because the default frame runs from the start of the"
             " partition to the current row, and the last value in that is"
             " wherever you are standing. FIRST_VALUE gets away with the same"
             " default because the frame's start IS the partition's start."
             " Whenever a LAST_VALUE column looks identical to the column"
             " beside it, this is why.",
        claims=[("every row shows the same destination",
                 lambda rows, c: len({r[2] for r in rows}) == 1),
                ("and it is the name at the highest stop_seq",
                 lambda rows, c: rows[0][2] == max(rows, key=lambda r: r[0])[1])],
    ),
    dict(
        id=7, ledger="Q438", concept="W3", tier="2 - Sequences and strings",
        title="The five longest waits between stops",
        prompt=(
            "Across every service, the five largest gaps between one scheduled"
            " arrival and the next on the SAME journey.\n\n"
            "Report the stop the gap arrives at. Largest first; break ties by"
            " service_id then stop_seq.\n\n"
            "Return: service_id, stop_seq, minutes"
        ),
        solution=("WITH g AS (SELECT service_id, stop_seq,"
                  " (strftime('%s', sched_arrive) - strftime('%s',"
                  " LAG(sched_arrive) OVER (PARTITION BY service_id"
                  " ORDER BY stop_seq))) / 60 AS mins FROM stops)"
                  " SELECT service_id, stop_seq, mins FROM g"
                  " WHERE mins IS NOT NULL"
                  " ORDER BY mins DESC, service_id, stop_seq LIMIT 5"),
        trap_sql=("WITH g AS (SELECT service_id, stop_seq,"
                  " (strftime('%s', sched_arrive) - strftime('%s',"
                  " LAG(sched_arrive) OVER (ORDER BY stop_seq)))"
                  " / 60 AS mins FROM stops)"
                  " SELECT service_id, stop_seq, mins FROM g"
                  " WHERE mins IS NOT NULL"
                  " ORDER BY mins DESC, service_id, stop_seq LIMIT 5"),
        note="PARTITION BY service_id is doing essential work here: without it"
             " LAG reaches back to the previous row in the WHOLE table, which"
             " is the last stop of some other service. The gaps it computes are"
             " then differences between unrelated journeys -- often negative,"
             " and never meaningful. Partition by what the rows have in common;"
             " order by what separates them within that.",
        claims=[("five rows, all positive",
                 lambda rows, c: len(rows) == 5
                 and all(r[2] > 0 for r in rows))],
    ),
    dict(
        id=8, ledger="Q439", concept="S1", tier="2 - Sequences and strings",
        title="Always in the middle",
        prompt=(
            "Stations that a service calls at, but which are never the FIRST"
            " stop of any service and never the LAST.\n\n"
            "Return: station_id, name"
        ),
        solution=("SELECT sta.station_id, sta.name FROM stations sta"
                  " WHERE sta.station_id IN ("
                  " SELECT station_id FROM stops"
                  " EXCEPT"
                  " SELECT station_id FROM stops s WHERE s.stop_seq ="
                  " (SELECT MIN(stop_seq) FROM stops x"
                  " WHERE x.service_id = s.service_id)"
                  " OR s.stop_seq = (SELECT MAX(stop_seq) FROM stops x"
                  " WHERE x.service_id = s.service_id))"),
        trap_sql=("SELECT sta.station_id, sta.name FROM stations sta"
                  " WHERE sta.station_id IN ("
                  " SELECT station_id FROM stops"
                  " EXCEPT"
                  " SELECT station_id FROM stops WHERE stop_seq = 1)"),
        note="Two conditions have to be subtracted, not one, and the trap only"
             " removes the first stops. It also hard-codes stop_seq = 1, which"
             " happens to be right here but says nothing about where a journey"
             " begins -- MIN(stop_seq) per service says it. EXCEPT removes"
             " everything in the right-hand set, so both ends can be described"
             " in one subtraction with an OR.",
        claims=[("none of them is ever a first or last stop",
                 lambda rows, c: len(rows) > 0 and all(
                     c.execute("SELECT COUNT(*) FROM stops s WHERE"
                               " s.station_id = ? AND (s.stop_seq ="
                               " (SELECT MIN(stop_seq) FROM stops x WHERE"
                               " x.service_id = s.service_id) OR s.stop_seq ="
                               " (SELECT MAX(stop_seq) FROM stops x WHERE"
                               " x.service_id = s.service_id))",
                               (r[0],)).fetchone()[0] == 0 for r in rows))],
    ),
    dict(
        id=9, ledger="Q440", concept="STR", tier="2 - Sequences and strings",
        title="The first three calls",
        prompt=(
            "For service 1, its first THREE stations as a single string joined"
            " with ' -> ', in stop order.\n\n"
            "One row, one column.\n\n"
            "Return: opening_legs"
        ),
        solution=("SELECT GROUP_CONCAT(name, ' -> ') FROM ("
                  " SELECT sta.name FROM stops s"
                  " JOIN stations sta ON sta.station_id = s.station_id"
                  " WHERE s.service_id = 1 ORDER BY s.stop_seq LIMIT 3)"),
        trap_sql=("SELECT GROUP_CONCAT(sta.name, ' -> ') FROM stops s"
                  " JOIN stations sta ON sta.station_id = s.station_id"
                  " WHERE s.service_id = 1 ORDER BY s.stop_seq LIMIT 3"),
        note="LIMIT applies to the rows a query RETURNS, and an aggregate"
             " returns one row -- so the trap's LIMIT 3 limits the answer to"
             " one row it was going to produce anyway, and GROUP_CONCAT still"
             " sees all nine stations. To limit what an aggregate CONSUMES, the"
             " limiting has to happen first, in a subquery. Same reasoning as"
             " WHERE versus HAVING: it is about which stage does the work.",
        claims=[("one row containing exactly two arrows",
                 lambda rows, c: len(rows) == 1
                 and rows[0][0].count(' -> ') == 2)],
    ),
    # ================================================= 3 Unpivot and set ops
    dict(
        id=10, ledger="Q441", concept="UNP", tier="3 - Unpivot and set ops",
        title="Quarterly totals for the whole network",
        prompt=(
            "Total footfall across ALL stations in each quarter of 2025.\n\n"
            "The table is wide -- q1 to q4 side by side -- so this needs"
            " turning long before it can be grouped. Four rows.\n\n"
            "Return: quarter, footfall"
        ),
        solution=("SELECT 1, SUM(q1) FROM station_footfall WHERE year = 2025"
                  " UNION ALL"
                  " SELECT 2, SUM(q2) FROM station_footfall WHERE year = 2025"
                  " UNION ALL"
                  " SELECT 3, SUM(q3) FROM station_footfall WHERE year = 2025"
                  " UNION ALL"
                  " SELECT 4, SUM(q4) FROM station_footfall WHERE year = 2025"),
        trap_sql=("SELECT 1, SUM(q1) FROM station_footfall"
                  " UNION ALL SELECT 2, SUM(q2) FROM station_footfall"
                  " UNION ALL SELECT 3, SUM(q3) FROM station_footfall"
                  " UNION ALL SELECT 4, SUM(q4) FROM station_footfall"),
        note="Each branch of a UNION ALL is an independent query, so the year"
             " filter has to appear in every one of them. Forget it in any"
             " branch and that quarter silently sums three years instead of"
             " one. The quarter number is a literal in each branch because it"
             " lives in the column NAME, and column names are not data.",
        claims=[("four quarters, totalling 2025's whole table",
                 lambda rows, c: len(rows) == 4
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT SUM(q1+q2+q3+q4) FROM station_footfall"
                     " WHERE year = 2025").fetchone()[0])],
    ),
    dict(
        id=11, ledger="Q442", concept="UNP", tier="3 - Unpivot and set ops",
        title="Each station's busiest quarter",
        prompt=(
            "For each station in 2025, which quarter was its busiest.\n\n"
            "No station ties for its own maximum. One row per station.\n\n"
            "Return: station_id, quarter, footfall"
        ),
        solution=("WITH long AS ("
                  " SELECT station_id, 1 q, q1 f FROM station_footfall"
                  " WHERE year = 2025 UNION ALL"
                  " SELECT station_id, 2, q2 FROM station_footfall"
                  " WHERE year = 2025 UNION ALL"
                  " SELECT station_id, 3, q3 FROM station_footfall"
                  " WHERE year = 2025 UNION ALL"
                  " SELECT station_id, 4, q4 FROM station_footfall"
                  " WHERE year = 2025)"
                  " SELECT station_id, q, f FROM long l WHERE f ="
                  " (SELECT MAX(f) FROM long x WHERE x.station_id ="
                  " l.station_id)"),
        trap_sql=("WITH long AS ("
                  " SELECT station_id, 1 q, q1 f FROM station_footfall"
                  " WHERE year = 2025 UNION ALL"
                  " SELECT station_id, 2, q2 FROM station_footfall"
                  " WHERE year = 2025 UNION ALL"
                  " SELECT station_id, 3, q3 FROM station_footfall"
                  " WHERE year = 2025 UNION ALL"
                  " SELECT station_id, 4, q4 FROM station_footfall"
                  " WHERE year = 2025)"
                  " SELECT station_id, q, f FROM long"
                  " WHERE f = (SELECT MAX(f) FROM long)"),
        note="Unpivot first, then the question becomes an ordinary"
             " greatest-per-group. The subquery must be CORRELATED to the"
             " station -- x.station_id = l.station_id -- or it finds the"
             " busiest quarter on the whole network and returns one row. Note"
             " the CTE is used twice, once as the source and once inside the"
             " subquery under another alias; that is what lets a row be"
             " compared with its own group.",
        claims=[("one row per station",
                 lambda rows, c: len(rows) == 60
                 and len({r[0] for r in rows}) == 60)],
    ),
    dict(
        id=12, ledger="Q443", concept="S1", tier="3 - Unpivot and set ops",
        title="Arrived at, never departed from",
        prompt=(
            "Station-and-class pairs that appear as the DESTINATION of a ticket"
            " but never as the origin of a ticket of that same class.\n\n"
            "Set operators compare whole rows, so both sides are two columns"
            " wide. Tickets with no destination cannot contribute.\n\n"
            "Return: station_id, class"
        ),
        solution=("SELECT to_station, class FROM tickets"
                  " WHERE to_station IS NOT NULL"
                  " EXCEPT SELECT from_station, class FROM tickets"),
        trap_sql=("SELECT from_station, class FROM tickets"
                  " EXCEPT SELECT to_station, class FROM tickets"
                  " WHERE to_station IS NOT NULL"),
        note="EXCEPT is directional, and the trap is this question's mirror"
             " image -- a perfectly reasonable answer to a different question."
             " Nothing about its output says so. Note also that EXCEPT compares"
             " both columns together, so a station that is a destination in"
             " first class and an origin in standard still qualifies for the"
             " first-class pair.",
        claims=[("every pair really is a destination and never an origin",
                 lambda rows, c: len(rows) > 0 and all(
                     c.execute("SELECT COUNT(*) FROM tickets WHERE"
                               " from_station = ? AND class = ?",
                               (r[0], r[1])).fetchone()[0] == 0
                     for r in rows))],
    ),
    dict(
        id=13, ledger="Q444", concept="S1", tier="3 - Unpivot and set ops",
        title="Grew in both directions",
        prompt=(
            "Stations whose Q1 footfall rose from 2024 to 2025 AND whose Q4"
            " footfall did too.\n\n"
            "Return: station_id"
        ),
        solution=("SELECT a.station_id FROM station_footfall a"
                  " JOIN station_footfall b ON b.station_id = a.station_id"
                  " WHERE a.year = 2024 AND b.year = 2025 AND b.q1 > a.q1"
                  " INTERSECT"
                  " SELECT a.station_id FROM station_footfall a"
                  " JOIN station_footfall b ON b.station_id = a.station_id"
                  " WHERE a.year = 2024 AND b.year = 2025 AND b.q4 > a.q4"),
        trap_sql=("SELECT a.station_id FROM station_footfall a"
                  " JOIN station_footfall b ON b.station_id = a.station_id"
                  " WHERE a.year = 2024 AND b.year = 2025 AND b.q1 > a.q1"
                  " UNION"
                  " SELECT a.station_id FROM station_footfall a"
                  " JOIN station_footfall b ON b.station_id = a.station_id"
                  " WHERE a.year = 2024 AND b.year = 2025 AND b.q4 > a.q4"),
        note="Both conditions apply to the same station, so it is an"
             " intersection even though the sentence contains an 'and'. UNION"
             " would answer 'grew in EITHER quarter', which is a strictly"
             " larger set and looks just as plausible. Comparing one year to"
             " another needs the table joined to itself, because the years are"
             " in different rows.",
        claims=[("every station really grew in both quarters",
                 lambda rows, c: len(rows) > 0 and all(
                     c.execute("SELECT COUNT(*) FROM station_footfall a JOIN"
                               " station_footfall b ON b.station_id ="
                               " a.station_id WHERE a.station_id = ? AND"
                               " a.year = 2024 AND b.year = 2025 AND"
                               " b.q1 > a.q1 AND b.q4 > a.q4",
                               (r[0],)).fetchone()[0] == 1 for r in rows))],
    ),
    # ===================================================== 4 Dates and times
    dict(
        id=14, ledger="Q445", concept="D1", tier="4 - Dates and times",
        title="Incidents by week",
        prompt=(
            "How many incidents were reported in each week, where a week is"
            " labelled by the MONDAY it starts on.\n\n"
            "Build that Monday with date modifiers. An incident reported on a"
            " Monday belongs to the week starting that same day.\n\n"
            "Return: week_start, incidents"
        ),
        solution=("SELECT date(reported_at, '-6 days', 'weekday 1'), COUNT(*)"
                  " FROM incidents GROUP BY 1"),
        trap_sql=("SELECT date(reported_at, 'weekday 1', '-7 days'), COUNT(*)"
                  " FROM incidents GROUP BY 1"),
        note="Modifiers apply left to right, and 'weekday 1' means 'move"
             " FORWARD to the next Monday, or stay put if today is one'. That"
             " last clause is the trap: the natural-looking"
             " 'weekday 1' then '-7 days' is correct on six days a week and"
             " lands a week early on Mondays, because nothing moved before the"
             " subtraction. Going back six days FIRST guarantees the following"
             " Monday is this week's, whatever day you started on.",
        claims=[("every label really is a Monday",
                 lambda rows, c: all(
                     c.execute("SELECT strftime('%w', ?)",
                               (r[0],)).fetchone()[0] == '1' for r in rows)),
                ("the counts total every incident",
                 lambda rows, c: sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM incidents").fetchone()[0])],
    ),
    dict(
        id=15, ledger="Q446", concept="D1", tier="4 - Dates and times",
        title="The busiest departure hour",
        prompt=(
            "How many services depart in each hour of the day.\n\n"
            "depart_time is 'HH:MM'. Report the hour as the two-character text"
            " it appears as, so '06' not 6.\n\n"
            "Return: hour, services"
        ),
        solution=("SELECT substr(depart_time, 1, 2), COUNT(*)"
                  " FROM services GROUP BY 1"),
        trap_sql=("SELECT substr(depart_time, 1, 2) + 0, COUNT(*)"
                  " FROM services GROUP BY 1"),
        note="substr() is the tool when a column holds a fixed-width string"
             " that is not a real date -- 'HH:MM' has no date part, so"
             " strftime's hour specifier has nothing to work with unless you"
             " give it one. The trap adds 0, which coerces '06' to the integer"
             " 6: the grouping is unchanged but every label loses its leading"
             " zero, and the column changes type.",
        claims=[("every hour label is two characters",
                 lambda rows, c: all(len(r[0]) == 2 for r in rows)),
                ("the counts total every service",
                 lambda rows, c: sum(r[1] for r in rows) == 13104)],
    ),
    dict(
        id=16, ledger="Q447", concept="D1", tier="4 - Dates and times",
        title="Cancellations by day of the week",
        prompt=(
            "For each day of the week, how many services ran and how many were"
            " cancelled.\n\n"
            "Name the day rather than numbering it. cancelled is 1 or 0. Seven"
            " rows.\n\n"
            "Return: day_name, services, cancelled"
        ),
        solution=("SELECT CASE strftime('%w', run_date)"
                  " WHEN '0' THEN 'Sunday' WHEN '1' THEN 'Monday'"
                  " WHEN '2' THEN 'Tuesday' WHEN '3' THEN 'Wednesday'"
                  " WHEN '4' THEN 'Thursday' WHEN '5' THEN 'Friday'"
                  " ELSE 'Saturday' END, COUNT(*), SUM(cancelled)"
                  " FROM services GROUP BY strftime('%w', run_date)"),
        trap_sql=("SELECT CASE strftime('%w', run_date)"
                  " WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday'"
                  " WHEN 2 THEN 'Tuesday' WHEN 3 THEN 'Wednesday'"
                  " WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday'"
                  " ELSE 'Saturday' END, COUNT(*), SUM(cancelled)"
                  " FROM services GROUP BY strftime('%w', run_date)"),
        note="strftime returns TEXT, so the WHEN values must be quoted."
             " Unquoted they are integers, and SQLite never matches an integer"
             " against text -- so every branch fails and all seven days come"
             " back as 'Saturday' from the ELSE. Note SUM(cancelled) works"
             " because the flag is 1 or 0: summing a boolean counts the trues.",
        claims=[("seven distinct day names",
                 lambda rows, c: len(rows) == 7
                 and len({r[0] for r in rows}) == 7),
                ("the services total the table",
                 lambda rows, c: sum(r[1] for r in rows) == 13104)],
    ),
    dict(
        id=17, ledger="Q448", concept="W3", tier="4 - Dates and times",
        title="Months when incidents rose",
        prompt=(
            "One row per month in which any incident was reported: the month as"
            " 'YYYY-MM', how many there were, and how many more or fewer than"
            " the month before.\n\n"
            "The first month has nothing before it, so its change is NULL.\n\n"
            "Return: month, incidents, change"
        ),
        solution=("WITH m AS (SELECT strftime('%Y-%m', reported_at) AS mth,"
                  " COUNT(*) AS n FROM incidents GROUP BY 1)"
                  " SELECT mth, n, n - LAG(n) OVER (ORDER BY mth) FROM m"),
        trap_sql=("WITH m AS (SELECT strftime('%m', reported_at) AS mth,"
                  " COUNT(*) AS n FROM incidents GROUP BY 1)"
                  " SELECT mth, n, n - LAG(n) OVER (ORDER BY mth) FROM m"),
        note="%m alone is the month number with no year, so the two Januaries"
             " merge and eighteen months collapse into twelve. The LAG is then"
             " comparing a merged bucket with another merged bucket, which is"
             " not a change over time at all. Any grouping by date needs every"
             " component down to the level you want.",
        claims=[("more than twelve months, one NULL change",
                 lambda rows, c: len(rows) > 12
                 and sum(1 for r in rows if r[2] is None) == 1)],
    ),
    # ====================================================== 5 Joins and grain
    dict(
        id=18, ledger="Q449", concept="J2", tier="5 - Joins and grain",
        title="Stations no ticket is bought to",
        prompt=(
            "Every station that is never the destination of a ticket.\n\n"
            "Write it as an outer join that keeps the non-matches, rather than"
            " with NOT IN.\n\n"
            "Return: station_id, name"
        ),
        solution=("SELECT s.station_id, s.name FROM stations s"
                  " LEFT JOIN tickets t ON t.to_station = s.station_id"
                  " WHERE t.ticket_id IS NULL"),
        trap_sql=("SELECT s.station_id, s.name FROM stations s"
                  " WHERE s.station_id NOT IN (SELECT to_station FROM tickets)"),
        note="to_station is NULL on 2,017 tickets, and NOT IN over a list"
             " containing a NULL returns NOTHING -- SQL cannot rule out that"
             " the NULL was the station you asked about. The anti-join has no"
             " such hole. Note the IS NULL must test a NOT NULL column of the"
             " right-hand table (ticket_id), so it can only be true for a"
             " padded row.",
        claims=[("some stations qualify, none of them a real destination",
                 lambda rows, c: len(rows) > 0 and all(
                     c.execute("SELECT COUNT(*) FROM tickets WHERE"
                               " to_station = ?", (r[0],)).fetchone()[0] == 0
                     for r in rows))],
    ),
    dict(
        id=19, ledger="Q450", concept="C2", tier="5 - Joins and grain",
        title="Revenue by line",
        prompt=(
            "One row per line: its name and the total ticket revenue in"
            " POUNDS, to two decimals.\n\n"
            "Tickets belong to services, services to lines. All six lines have"
            " revenue.\n\n"
            "Return: line_name, revenue"
        ),
        solution=("SELECT l.name, ROUND(SUM(t.price_pence) / 100.0, 2)"
                  " FROM lines l JOIN services sv ON sv.line_id = l.line_id"
                  " JOIN tickets t ON t.service_id = sv.service_id"
                  " GROUP BY l.name"),
        trap_sql=("SELECT l.name, ROUND(SUM(t.price_pence) / 100, 2)"
                  " FROM lines l JOIN services sv ON sv.line_id = l.line_id"
                  " JOIN tickets t ON t.service_id = sv.service_id"
                  " GROUP BY l.name"),
        note="A straight descent through foreign keys -- line to service to"
             " ticket, one parent to many children at each step -- so there is"
             " no fan-out and SUM is a true total. The only trap is the"
             " division: SUM(price_pence) is an integer and so is 100, so"
             " / 100 truncates the pence before ROUND ever sees them.",
        claims=[("six lines, and the total matches every ticket",
                 lambda rows, c: len(rows) == 6 and abs(
                     sum(r[1] for r in rows) - c.execute(
                         "SELECT SUM(price_pence) / 100.0 FROM tickets"
                     ).fetchone()[0]) < 0.5)],
    ),
    dict(
        id=20, ledger="Q451", concept="J2", tier="5 - Joins and grain",
        title="Where journeys begin, counted",
        prompt=(
            "One row for every station: its name, and how many services START"
            " there -- that is, have it as their first stop.\n\n"
            "Most stations never start a service. They must appear with 0, so"
            " all 60 stations come back.\n\n"
            "Return: name, services_starting"
        ),
        solution=("SELECT s.name, COUNT(p.service_id) FROM stations s"
                  " LEFT JOIN stops p ON p.station_id = s.station_id"
                  " AND p.stop_seq = 1 GROUP BY s.station_id, s.name"),
        trap_sql=("SELECT s.name, COUNT(p.service_id) FROM stations s"
                  " LEFT JOIN stops p ON p.station_id = s.station_id"
                  " WHERE p.stop_seq = 1 GROUP BY s.station_id, s.name"),
        note="The condition on the right-hand table belongs in ON. In WHERE it"
             " runs after the join has padded the unmatched stations with"
             " NULLs, and NULL = 1 is not true, so they are filtered straight"
             " back out -- 6 rows instead of 60. Pair it with COUNT(a"
             " right-side column), or the 54 stations with none would each"
             " report 1.",
        claims=[("all 60 stations, 54 of them starting nothing",
                 lambda rows, c: len(rows) == 60
                 and sum(1 for r in rows if r[1] == 0) == 54),
                ("the counts total every first stop",
                 lambda rows, c: sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM stops WHERE stop_seq = 1"
                 ).fetchone()[0])],
    ),
    dict(
        id=21, ledger="Q452", concept="C2", tier="5 - Joins and grain",
        title="Tickets and incidents per line",
        prompt=(
            "One row per line: how many tickets were sold on its services, and"
            " how many incidents were reported on them.\n\n"
            "Both hang off services but are independent of each other. All six"
            " lines appear.\n\n"
            "Return: line_name, tickets, incidents"
        ),
        solution=("SELECT l.name,"
                  " (SELECT COUNT(*) FROM tickets t JOIN services sv"
                  " ON sv.service_id = t.service_id"
                  " WHERE sv.line_id = l.line_id),"
                  " (SELECT COUNT(*) FROM incidents i JOIN services sv"
                  " ON sv.service_id = i.service_id"
                  " WHERE sv.line_id = l.line_id)"
                  " FROM lines l"),
        trap_sql=("SELECT l.name, COUNT(t.ticket_id), COUNT(i.incident_id)"
                  " FROM lines l JOIN services sv ON sv.line_id = l.line_id"
                  " LEFT JOIN tickets t ON t.service_id = sv.service_id"
                  " LEFT JOIN incidents i ON i.service_id = sv.service_id"
                  " GROUP BY l.name"),
        note="Joining two children of the same parent multiplies them: a"
             " service with 4 tickets and 2 incidents produces 8 rows, so the"
             " ticket count comes out doubled and the incident count"
             " quadrupled. COUNT(DISTINCT ...) would paper over it here but a"
             " SUM could not. Two independent measures want two independent"
             " subqueries.",
        claims=[("six lines, both totals matching their tables",
                 lambda rows, c: len(rows) == 6
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM tickets").fetchone()[0]
                 and sum(r[2] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM incidents").fetchone()[0])],
    ),
    dict(
        id=22, ledger="Q453", concept="A3", tier="5 - Joins and grain",
        title="Units that get around",
        prompt=(
            "Rolling stock units that have worked on more than one LINE.\n\n"
            "A unit is linked to services through service_units, and a service"
            " belongs to a line.\n\n"
            "Return: unit_id, lines_worked"
        ),
        solution=("SELECT u.unit_id, COUNT(DISTINCT sv.line_id)"
                  " FROM service_units u JOIN services sv"
                  " ON sv.service_id = u.service_id"
                  " GROUP BY u.unit_id HAVING COUNT(DISTINCT sv.line_id) > 1"),
        trap_sql=("SELECT u.unit_id, COUNT(sv.line_id)"
                  " FROM service_units u JOIN services sv"
                  " ON sv.service_id = u.service_id"
                  " GROUP BY u.unit_id HAVING COUNT(sv.line_id) > 1"),
        note="A unit runs hundreds of services, so COUNT(line_id) counts"
             " services, not lines -- and 'more than one' is then true of"
             " almost everything. DISTINCT inside the aggregate is what makes"
             " it count lines. The same DISTINCT has to appear in the HAVING:"
             " the two are separate expressions and SQLite will not infer one"
             " from the other.",
        claims=[("every unit returned really works several lines",
                 lambda rows, c: len(rows) > 0
                 and all(r[1] > 1 for r in rows))],
    ),
    # ================================================ 6 Windows and recursion
    dict(
        id=23, ledger="Q454", concept="W2", tier="6 - Windows and recursion",
        title="Lines ranked by revenue",
        prompt=(
            "The six lines ranked by total ticket revenue in pence, highest"
            " first, with their rank.\n\n"
            "If two lines tied they would share a rank.\n\n"
            "Return: line_name, revenue_pence, rank"
        ),
        solution=("WITH r AS (SELECT l.name, SUM(t.price_pence) AS rev"
                  " FROM lines l JOIN services sv ON sv.line_id = l.line_id"
                  " JOIN tickets t ON t.service_id = sv.service_id"
                  " GROUP BY l.name)"
                  " SELECT name, rev, RANK() OVER (ORDER BY rev DESC) FROM r"),
        trap_sql=("WITH r AS (SELECT l.name, SUM(t.price_pence) AS rev"
                  " FROM lines l JOIN services sv ON sv.line_id = l.line_id"
                  " JOIN tickets t ON t.service_id = sv.service_id"
                  " GROUP BY l.name)"
                  " SELECT name, rev, RANK() OVER (ORDER BY rev) FROM r"),
        note="ORDER BY inside OVER decides which end gets rank 1. Ascending"
             " ranks the SMALLEST first, which is a plausible-looking result"
             " with the ranks exactly reversed. Whenever a question says"
             " highest, biggest or busiest, say DESC out loud and check it is"
             " actually inside the OVER clause rather than at the end of the"
             " query.",
        claims=[("six lines, rank 1 has the most revenue",
                 lambda rows, c: len(rows) == 6
                 and max(rows, key=lambda r: r[1])[2] == 1)],
    ),
    dict(
        id=24, ledger="Q455", concept="W1", tier="6 - Windows and recursion",
        title="Three-month rolling average of incidents",
        prompt=(
            "One row per month in which any incident was reported: the month,"
            " the count, and the average over that month and the two before"
            " it.\n\n"
            "The first month averages just itself, the second two months.\n\n"
            "Return: month, incidents, rolling_avg"
        ),
        solution=("WITH m AS (SELECT strftime('%Y-%m', reported_at) AS mth,"
                  " COUNT(*) AS n FROM incidents GROUP BY 1)"
                  " SELECT mth, n, ROUND(AVG(n) OVER (ORDER BY mth"
                  " ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) FROM m"),
        trap_sql=("WITH m AS (SELECT strftime('%Y-%m', reported_at) AS mth,"
                  " COUNT(*) AS n FROM incidents GROUP BY 1)"
                  " SELECT mth, n, ROUND(AVG(n) OVER (ORDER BY mth), 2) FROM m"),
        note="An OVER() with ORDER BY and no ROWS clause does not mean 'no"
             " frame' -- it means the DEFAULT frame, everything from the start"
             " of the partition to the current row. That is a running average"
             " over all history, not a rolling one. ROWS BETWEEN 2 PRECEDING"
             " AND CURRENT ROW pins the window to three rows.",
        claims=[("the first rolling average equals the first count",
                 lambda rows, c: abs(min(rows, key=lambda r: r[0])[2]
                                     - min(rows, key=lambda r: r[0])[1]) < 0.01)],
    ),
    dict(
        id=25, ledger="Q456", concept="R1", tier="6 - Windows and recursion",
        title="The chain of command",
        prompt=(
            "For every member of staff, their reporting line from the very top"
            " down to them, as one string joined with ' > '.\n\n"
            "The person with no manager is just their own name. Everyone else"
            " is their manager's chain with their own name on the end.\n\n"
            "Return: staff_id, chain"
        ),
        solution=("WITH RECURSIVE ch(id, name, chain) AS ("
                  " SELECT staff_id, name, name FROM staff"
                  " WHERE reports_to IS NULL"
                  " UNION ALL"
                  " SELECT s.staff_id, s.name, ch.chain || ' > ' || s.name"
                  " FROM staff s JOIN ch ON s.reports_to = ch.id)"
                  " SELECT id, chain FROM ch"),
        trap_sql=("SELECT s.staff_id,"
                  " COALESCE(m.name || ' > ', '') || s.name"
                  " FROM staff s LEFT JOIN staff m"
                  " ON m.staff_id = s.reports_to"),
        note="The string is built up AS the walk proceeds: each row inherits"
             " its manager's chain and appends its own name. That is what a"
             " recursive CTE can do that a join cannot -- a single self-join"
             " reaches one level up, so the trap produces 'manager > person'"
             " and stops, correct only for the second level.",
        claims=[("all 40 staff, and exactly one chain with no separator",
                 lambda rows, c: len(rows) == 40
                 and sum(1 for r in rows if ' > ' not in r[1]) == 1)],
    ),
    dict(
        id=26, ledger="Q457", concept="R1", tier="6 - Windows and recursion",
        title="How deep the hierarchy runs",
        prompt=(
            "Every member of staff with how many levels below the top they"
            " sit.\n\n"
            "The person with no manager is 0, their direct reports 1, and so"
            " on. All 40 appear.\n\n"
            "Return: staff_id, name, level"
        ),
        solution=("WITH RECURSIVE t(id, name, lvl) AS ("
                  " SELECT staff_id, name, 0 FROM staff"
                  " WHERE reports_to IS NULL"
                  " UNION ALL"
                  " SELECT s.staff_id, s.name, t.lvl + 1 FROM staff s"
                  " JOIN t ON s.reports_to = t.id)"
                  " SELECT id, name, lvl FROM t"),
        trap_sql=("SELECT staff_id, name,"
                  " CASE WHEN reports_to IS NULL THEN 0 ELSE 1 END"
                  " FROM staff"),
        note="A CASE on reports_to can tell the top from everyone else, and"
             " nothing more -- it cannot distinguish level 1 from level 2,"
             " because that depends on the MANAGER's level, which is not on the"
             " row. The counter is carried through the walk: t.lvl + 1 reads"
             " the value from whichever row this one joined to.",
        claims=[("all 40 staff, exactly one at level 0",
                 lambda rows, c: len(rows) == 40
                 and sum(1 for r in rows if r[2] == 0) == 1),
                ("the tree is more than two levels deep",
                 lambda rows, c: max(r[2] for r in rows) >= 2)],
    ),
    # =================================================== 7 Query efficiency
    # Graded on the PLAN as well as the rows. Each opens with a query already
    # in the editor that is correct and slow; the Reset button restores it.
    dict(
        id=27, ledger="Q458", concept="X3", tier="7 - Query efficiency",
        title="Add a condition to make it faster",
        prompt=(
            "How many tickets cost more than 90 pounds.\n\n"
            "There is an index on tickets(class, price_pence) -- class first."
            " The editor's query cannot use it. Make the plan say SEARCH"
            " instead of SCAN, by ADDING to the WHERE clause rather than"
            " changing what is there.\n\n"
            "Return: one row, one column: the count"
        ),
        solution=("SELECT COUNT(*) FROM tickets"
                  " WHERE class IN ('advance', 'standard', 'first')"
                  " AND price_pence > 9000"),
        trap_sql=("SELECT COUNT(*) FROM tickets WHERE price_pence > 9000"),
        starter_sql="SELECT COUNT(*) FROM tickets WHERE price_pence > 9000",
        plan_forbids=("SCAN",),
        note="A composite index is usable only from the LEFT. Filtering on"
             " price_pence alone skips class, so there is no range to seek and"
             " SQLite reads the whole index. Supplying class -- even with a"
             " list of every value it can take, which removes no rows -- gives"
             " the index its leading column, and the scan becomes three small"
             " seeks. A predicate that filters nothing can still change the"
             " plan, which is the opposite of the usual intuition.",
        claims=[("matches the count without the extra predicate",
                 lambda rows, c: rows[0][0] == c.execute(
                     "SELECT COUNT(*) FROM tickets WHERE price_pence > 9000"
                 ).fetchone()[0])],
    ),
    dict(
        id=28, ledger="Q459", concept="X2", tier="7 - Query efficiency",
        title="One direction or the other, not both",
        prompt=(
            "Every ticket id, ordered by class descending and price"
            " descending.\n\n"
            "The editor's query sorts all 40,702 rows. An index"
            " can be walked forwards or backwards, but not one column each way."
            " Your plan must NOT contain 'TEMP B-TREE'.\n\n"
            "Return: ticket_id"
        ),
        solution=("SELECT ticket_id FROM tickets"
                  " ORDER BY class DESC, price_pence DESC"),
        trap_sql=("SELECT ticket_id FROM tickets"
                  " ORDER BY class ASC, price_pence DESC"),
        starter_sql=("SELECT ticket_id FROM tickets"
                     " ORDER BY class ASC, price_pence DESC"),
        plan_forbids=("TEMP B-TREE",),
        note="An index holds its columns in one fixed order, so SQLite can read"
             " it forwards (all ASC) or backwards (all DESC) and get sorted"
             " rows for free. What it cannot do is walk one column forwards and"
             " the next backwards -- there is no single direction that produces"
             " that, so the rows must be sorted. Both queries return the same"
             " 40,702 ids -- row order is not graded -- so the ONLY difference"
             " between them is the plan, which is what this stage is for.",
        claims=[("every ticket",
                 lambda rows, c: len(rows) == c.execute(
                     "SELECT COUNT(*) FROM tickets").fetchone()[0])],
    ),
    dict(
        id=29, ledger="Q460", concept="X7", tier="7 - Query efficiency",
        title="When the join beats the subquery",
        prompt=(
            "How many stations are the FIRST stop of at least one service.\n\n"
            "The editor's NOT EXISTS-style query is correct and slow. stops is"
            " indexed on station_id alone, and the inner test also checks"
            " stop_seq -- so each probe reads thousands of rows. Rewrite it as"
            " a join. Your plan must NOT contain 'CORRELATED'.\n\n"
            "Return: one row, one column: the count"
        ),
        solution=("SELECT COUNT(DISTINCT p.station_id) FROM stops p"
                  " WHERE p.stop_seq = 1"),
        trap_sql=("SELECT COUNT(*) FROM stations s WHERE EXISTS"
                  " (SELECT 1 FROM stops p WHERE p.station_id = s.station_id"
                  " AND p.stop_seq = 1)"),
        starter_sql=("SELECT COUNT(*) FROM stations s WHERE EXISTS"
                     " (SELECT 1 FROM stops p WHERE p.station_id = s.station_id"
                     " AND p.stop_seq = 1)"),
        plan_forbids=("CORRELATED",),
        note="This contradicts the last set on purpose. There, a correlated NOT"
             " EXISTS beat a LEFT JOIN anti-join and the plan assertion DEMANDED"
             " the subquery. Here the same shape loses, because the index on"
             " stops covers station_id but not stop_seq: each probe seeks to a"
             " station and then reads thousands of its rows looking for"
             " stop_seq = 1. The rule was never 'prefer EXISTS' -- it is 'check"
             " whether the index covers what the subquery asks'. Same schema,"
             " same operators, opposite advice.",
        claims=[("matches the EXISTS version's answer",
                 lambda rows, c: rows[0][0] == c.execute(
                     "SELECT COUNT(*) FROM stations s WHERE EXISTS (SELECT 1"
                     " FROM stops p WHERE p.station_id = s.station_id"
                     " AND p.stop_seq = 1)").fetchone()[0])],
    ),
    dict(
        id=30, ledger="Q461", concept="X6", tier="7 - Query efficiency",
        title="Let the index do the deduplicating",
        prompt=(
            "The distinct ticket classes.\n\n"
            "tickets(class, price_pence) is indexed, and an index is already"
            " grouped by its leading column -- so the deduplication is free if"
            " you let it happen. Your plan must NOT contain 'TEMP B-TREE'.\n\n"
            "Return: class"
        ),
        solution="SELECT DISTINCT class FROM tickets",
        trap_sql="SELECT DISTINCT class || '' FROM tickets",
        starter_sql="SELECT DISTINCT class || '' FROM tickets",
        plan_forbids=("TEMP B-TREE",),
        note="DISTINCT normally builds a temporary b-tree to spot repeats. When"
             " the column is the leading one of an index, equal values are"
             " already adjacent, so SQLite walks the index and emits a value"
             " whenever it changes -- no sort at all. Concatenating an empty"
             " string produces identical VALUES but a different EXPRESSION, and"
             " the index is on the column, so the shortcut is lost.",
        claims=[("three classes",
                 lambda rows, c: len(rows) == 3)],
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
