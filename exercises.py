"""Practice exercises: thirty questions on the railway schema.

Twenty-two are SELECT questions across the usual tiers, graded on the rows
they return. The last eight are something the tool has not had before:
WRITABLE questions, graded on the state of the database after your script
runs. They cover what SQLite has in place of a procedural language --

  * UPDATE and DELETE driven by subqueries, and INSERT ... SELECT
  * UPSERT: INSERT ... ON CONFLICT DO UPDATE, against INSERT OR IGNORE
  * transactions with SAVEPOINT and ROLLBACK TO
  * triggers -- SQLite's only procedural construct -- with RAISE() as its
    error handling, and a cross-table rule no CHECK constraint can express
  * an AFTER UPDATE audit trigger, restricted to one column and one condition
  * a view, and the fan-out that makes a view lie
  * a generated column

Each of those runs in a throwaway in-memory copy of the database, so nothing
you write can reach the real file, and every Run starts from the same
pristine state. The question's `probe_sql` then reads the result, and that
is what is compared with the reference. A `driver_sql`, where present, is
what the question itself runs AFTER your script -- the inserts that should
fire your trigger, or be refused by it.
"""

import sqlite3

EXERCISES = [
    # ========================================================== 1 Warm-up
    dict(
        id=1, ledger="Q552", concept="A2", tier="1 - Warm-up",
        title="Pay by role",
        prompt=(
            "One row per role: how many staff, the lowest and highest salary,"
            " and the average to the nearest pound.\n\n"
            "Return: role, staff, lowest, highest, avg_salary"
        ),
        solution=("SELECT role, COUNT(*), MIN(salary), MAX(salary),"
                  " ROUND(AVG(salary)) FROM staff GROUP BY 1"),
        trap_sql=("SELECT role, COUNT(*), MIN(salary), MAX(salary),"
                  " AVG(salary) FROM staff GROUP BY 1"),
        note="ROUND with no second argument rounds to a whole number, which is"
             " what 'nearest pound' asks for. AVG on an INTEGER column still"
             " returns a REAL, so the trap hands back 46424.1 where 46424 was"
             " wanted -- and nothing about the number looks wrong.",
        claims=[("four roles, every average a whole number",
                 lambda rows, c: len(rows) == 4
                 and all(r[4] == int(r[4]) for r in rows))],
    ),
    dict(
        id=2, ledger="Q553", concept="A2", tier="1 - Warm-up",
        title="Each class's share of the tickets",
        prompt=(
            "One row per class: how many tickets, and what percentage of all"
            " tickets that is, to two decimals.\n\n"
            "Return: class, tickets, pct"
        ),
        solution=("SELECT class, COUNT(*), ROUND(100.0 * COUNT(*)"
                  " / (SELECT COUNT(*) FROM tickets), 2) FROM tickets"
                  " GROUP BY 1"),
        trap_sql=("SELECT class, COUNT(*), ROUND(100 * COUNT(*)"
                  " / (SELECT COUNT(*) FROM tickets), 2) FROM tickets"
                  " GROUP BY 1"),
        note="100 * 11504 / 34528 is integer division all the way through --"
             " 1150400 / 34528 truncates to 33 -- and ROUND(33, 2) is still"
             " 33. One float anywhere in the expression makes the rest float;"
             " 100.0 is the cheapest place to put it. The uncorrelated"
             " subquery runs once, not per group.",
        claims=[("three classes summing to 100 percent",
                 lambda rows, c: len(rows) == 3
                 and abs(sum(r[2] for r in rows) - 100) < 0.05)],
    ),
    dict(
        id=3, ledger="Q554", concept="A3", tier="1 - Warm-up",
        title="Large, well-paid roles",
        prompt=(
            "Roles with at least 8 staff whose average salary is above 40000,"
            " with the count and the average to the nearest pound.\n\n"
            "Both conditions are about the role as a whole.\n\n"
            "Return: role, staff, avg_salary"
        ),
        solution=("SELECT role, COUNT(*), ROUND(AVG(salary)) FROM staff"
                  " GROUP BY role HAVING COUNT(*) >= 8 AND AVG(salary) > 40000"),
        trap_sql=("SELECT role, COUNT(*), ROUND(AVG(salary)) FROM staff"
                  " WHERE salary > 40000 GROUP BY role HAVING COUNT(*) >= 8"),
        note="WHERE salary > 40000 filters PEOPLE, so the count and the average"
             " are then computed over only the well-paid ones -- a different"
             " question. A condition on an aggregate belongs in HAVING, which"
             " sees each group whole. FROM, WHERE, GROUP BY, HAVING, SELECT,"
             " ORDER BY is the order to hold in your head.",
        claims=[("every role returned satisfies both conditions",
                 lambda rows, c: len(rows) > 0
                 and all(r[1] >= 8 and r[2] > 40000 for r in rows))],
    ),
    # ========================================== 2 Sequences and strings
    dict(
        id=4, ledger="Q555", concept="W3", tier="2 - Sequences and strings",
        title="Minutes between calls",
        prompt=(
            "For service 301, the minutes between each stop's scheduled arrival"
            " and the previous stop's.\n\n"
            "The first stop has no previous, so its gap is NULL.\n\n"
            "Return: stop_seq, gap_minutes"
        ),
        solution=("SELECT stop_seq, (strftime('%s', sched_arrive)"
                  " - strftime('%s', LAG(sched_arrive) OVER"
                  " (ORDER BY stop_seq))) / 60 FROM stops"
                  " WHERE service_id = 301"),
        trap_sql=("SELECT stop_seq, (strftime('%s', sched_arrive)"
                  " - strftime('%s', LAG(sched_arrive) OVER"
                  " (ORDER BY stop_seq))) FROM stops WHERE service_id = 301"),
        note="strftime('%s', x) is seconds since 1970, so the difference of"
             " two is seconds and needs dividing by 60. Integer division is"
             " fine here because every gap is a whole number of minutes; it"
             " would not be if the timetable held seconds.",
        claims=[("first gap NULL, the rest positive and under an hour",
                 lambda rows, c: rows[0][1] is None
                 and all(0 < r[1] < 60 for r in rows[1:]))],
    ),
    dict(
        id=5, ledger="Q556", concept="STR", tier="2 - Sequences and strings",
        title="The last word of a station's name",
        prompt=(
            "How many stations end in each word -- 'Bridge', 'Halt', 'Parkway'"
            " and so on. Only stations whose name has more than one word.\n\n"
            "Most common first, ties by the word.\n\n"
            "Return: last_word, stations"
        ),
        solution=("SELECT SUBSTR(name, LENGTH(RTRIM(name,"
                  " REPLACE(name, ' ', ''))) + 1), COUNT(*) FROM stations"
                  " WHERE INSTR(name, ' ') > 0 GROUP BY 1"
                  " ORDER BY 2 DESC, 1"),
        trap_sql=("SELECT SUBSTR(name, LENGTH(RTRIM(name,"
                  " REPLACE(name, ' ', ''))) + 1), COUNT(*) FROM stations"
                  " GROUP BY 1 ORDER BY 2 DESC, 1"),
        note="There is no reverse-find in SQLite. The idiom: RTRIM(name,"
             " chars) strips every trailing character that appears in `chars`,"
             " and passing the name with its spaces removed strips exactly the"
             " last word -- leaving 'Quarrydale ', whose length + 1 is where"
             " the last word starts. (INSTR finds the FIRST space, which only"
             " works while every name has two words.) The trap forgets to"
             " exclude the single-word stations, each of which then appears as"
             " its own 'ending' with a count of 1.",
        claims=[("several endings, 'Bridge' the most common",
                 lambda rows, c: len(rows) > 4 and rows[0][0] == 'Bridge')],
    ),
    dict(
        id=6, ledger="Q557", concept="W2", tier="2 - Sequences and strings",
        title="Minutes until the next call",
        prompt=(
            "For service 301, each stop with the minutes until the NEXT"
            " scheduled arrival.\n\n"
            "The last stop has none, so it is NULL.\n\n"
            "Return: stop_seq, minutes_to_next"
        ),
        solution=("SELECT stop_seq, (strftime('%s', LEAD(sched_arrive) OVER"
                  " (ORDER BY stop_seq)) - strftime('%s', sched_arrive)) / 60"
                  " FROM stops WHERE service_id = 301"),
        trap_sql=("SELECT stop_seq, (strftime('%s', sched_arrive)"
                  " - strftime('%s', LEAD(sched_arrive) OVER"
                  " (ORDER BY stop_seq))) / 60"
                  " FROM stops WHERE service_id = 301"),
        note="Question 4 mirrored: LEAD instead of LAG, and the subtraction"
             " the other way round -- next minus this. The trap has the"
             " function right and the order wrong, so every value is negative."
             " With LEAD the NULL lands on the LAST row; if it is on row 1 you"
             " have LAG.",
        claims=[("last gap NULL, the rest positive",
                 lambda rows, c: rows[-1][1] is None
                 and all(r[1] > 0 for r in rows[:-1]))],
    ),
    dict(
        id=7, ledger="Q558", concept="S1", tier="2 - Sequences and strings",
        title="Towns line 3 serves that line 5 does not",
        prompt=(
            "Towns with a station on line 3's route that have NO station on"
            " line 5's route.\n\n"
            "The two lines share three towns; four are line 3's alone.\n\n"
            "Return: town"
        ),
        solution=("SELECT st.town FROM stops sp JOIN services s"
                  " ON s.service_id = sp.service_id JOIN stations st"
                  " ON st.station_id = sp.station_id WHERE s.line_id = 3"
                  " EXCEPT SELECT st.town FROM stops sp JOIN services s"
                  " ON s.service_id = sp.service_id JOIN stations st"
                  " ON st.station_id = sp.station_id WHERE s.line_id = 5"),
        trap_sql=("SELECT DISTINCT st.town FROM stops sp JOIN services s"
                  " ON s.service_id = sp.service_id JOIN stations st"
                  " ON st.station_id = sp.station_id"
                  " WHERE s.line_id = 3 AND s.line_id <> 5"),
        note="A row belongs to one line, so `line_id = 3 AND line_id <> 5` is"
             " just `line_id = 3` -- it says nothing about line 5 at all, and"
             " returns all seven towns. 'Has none on line 5' compares two SETS"
             " of towns, which is what EXCEPT does. NOT EXISTS with a"
             " correlated subquery says the same thing row by row.",
        claims=[("four towns, none of them on line 5",
                 lambda rows, c: len(rows) == 4 and not c.execute(
                     "SELECT 1 FROM stops sp JOIN services s"
                     " ON s.service_id = sp.service_id JOIN stations st"
                     " ON st.station_id = sp.station_id WHERE s.line_id = 5"
                     " AND st.town IN (%s) LIMIT 1"
                     % ",".join("'%s'" % r[0] for r in rows)).fetchall())],
    ),
    # ============================================ 3 Unpivot and set ops
    dict(
        id=8, ledger="Q559", concept="UNP", tier="3 - Unpivot and set ops",
        title="The network by quarter, 2024",
        prompt=(
            "Total footfall across every station for each quarter of 2024,"
            " as four ROWS labelled 'q1' to 'q4'.\n\n"
            "Return: quarter, footfall"
        ),
        solution=("SELECT 'q1', SUM(q1) FROM station_footfall WHERE year = 2024"
                  " UNION ALL SELECT 'q2', SUM(q2) FROM station_footfall"
                  " WHERE year = 2024 UNION ALL SELECT 'q3', SUM(q3)"
                  " FROM station_footfall WHERE year = 2024"
                  " UNION ALL SELECT 'q4', SUM(q4) FROM station_footfall"
                  " WHERE year = 2024"),
        trap_sql=("SELECT 'q1', SUM(q1) FROM station_footfall WHERE year = 2024"
                  " UNION SELECT 'q2', SUM(q2) FROM station_footfall"
                  " WHERE year = 2024 UNION SELECT 'q3', SUM(q2)"
                  " FROM station_footfall WHERE year = 2024"
                  " UNION SELECT 'q4', SUM(q4) FROM station_footfall"
                  " WHERE year = 2024"),
        note="Four columns become four rows with four SELECTs and UNION ALL --"
             " SQLite has no UNPIVOT. The trap's third branch sums q2 under"
             " the q3 label, which is the hazard of copy-and-paste unpivots:"
             " every branch looks the same and one wrong letter is invisible."
             " It also uses UNION, which sorts and deduplicates four rows for"
             " nothing.",
        claims=[("four quarters, all different totals",
                 lambda rows, c: len(rows) == 4
                 and len({r[1] for r in rows}) == 4)],
    ),
    dict(
        id=9, ledger="Q560", concept="J1", tier="3 - Unpivot and set ops",
        title="Busier than the year before",
        prompt=(
            "Stations whose total footfall in 2025 was higher than in 2024,"
            " with both totals.\n\n"
            "Return: station_id, footfall_2025, footfall_2024"
        ),
        solution=("SELECT a.station_id, a.q1 + a.q2 + a.q3 + a.q4,"
                  " b.q1 + b.q2 + b.q3 + b.q4 FROM station_footfall a"
                  " JOIN station_footfall b ON b.station_id = a.station_id"
                  " AND b.year = 2024 WHERE a.year = 2025"
                  " AND a.q1 + a.q2 + a.q3 + a.q4 > b.q1 + b.q2 + b.q3 + b.q4"),
        trap_sql=("SELECT a.station_id, a.q1 + a.q2 + a.q3 + a.q4,"
                  " b.q1 + b.q2 + b.q3 + b.q4 FROM station_footfall a"
                  " JOIN station_footfall b ON b.station_id = a.station_id"
                  " WHERE a.year = 2025 AND b.year = 2024"
                  " AND a.q1 + a.q2 + a.q3 > b.q1 + b.q2 + b.q3 + b.q4"),
        note="A self-join: the same table twice, one alias per year, joined on"
             " the station. The trap leaves q4 out of one side -- three"
             " quarters against four -- which is the kind of slip a long"
             " expression written twice invites. Unpivoting first, so each"
             " year is one number, removes the chance to make it.",
        claims=[("every row's 2025 total exceeds its 2024 total",
                 lambda rows, c: len(rows) > 5
                 and all(r[1] > r[2] for r in rows))],
    ),
    dict(
        id=10, ledger="Q561", concept="S1", tier="3 - Unpivot and set ops",
        title="Models on every line",
        prompt=(
            "Models of rolling stock that have worked on ALL six lines.\n\n"
            "Do not hard-code the six.\n\n"
            "Return: model"
        ),
        solution=("SELECT r.model FROM service_units su JOIN rolling_stock r"
                  " ON r.unit_id = su.unit_id JOIN services s"
                  " ON s.service_id = su.service_id GROUP BY r.model"
                  " HAVING COUNT(DISTINCT s.line_id) ="
                  " (SELECT COUNT(*) FROM lines)"),
        trap_sql=("SELECT r.model FROM service_units su JOIN rolling_stock r"
                  " ON r.unit_id = su.unit_id JOIN services s"
                  " ON s.service_id = su.service_id GROUP BY r.model"
                  " HAVING COUNT(s.line_id) >= (SELECT COUNT(*) FROM lines)"),
        note="'All six' is a count of DISTINCT lines equal to the number of"
             " lines. COUNT(s.line_id) counts workings, and every model has"
             " thousands of those, so the trap returns all of them. This is"
             " relational division; the GROUP BY / HAVING COUNT(DISTINCT)"
             " shape is the standard way to write it.",
        claims=[("fewer than all the models",
                 lambda rows, c: 0 < len(rows) < c.execute(
                     "SELECT COUNT(DISTINCT model) FROM rolling_stock"
                 ).fetchone()[0])],
    ),
    # ================================================= 4 Dates and times
    dict(
        id=11, ledger="Q562", concept="D1", tier="4 - Dates and times",
        title="Weekdays and weekends, by month",
        prompt=(
            "For each month, how many services ran on weekdays and how many"
            " at the weekend.\n\n"
            "Return: month, weekday, weekend"
        ),
        solution=("SELECT strftime('%Y-%m', run_date),"
                  " SUM(strftime('%w', run_date) NOT IN ('0', '6')),"
                  " SUM(strftime('%w', run_date) IN ('0', '6'))"
                  " FROM services GROUP BY 1"),
        trap_sql=("SELECT strftime('%Y-%m', run_date),"
                  " SUM(strftime('%w', run_date) NOT IN (0, 6)),"
                  " SUM(strftime('%w', run_date) IN (0, 6))"
                  " FROM services GROUP BY 1"),
        note="strftime returns TEXT, and IN does not coerce: '0' is not in"
             " (0, 6). So the trap's weekend column is 0 for every month and"
             " everything lands on the weekday side. Quote the digits, or"
             " CAST the strftime. SUM of a boolean is a compact way to count"
             " matches -- true is 1, false is 0.",
        claims=[("eighteen months, weekends the smaller number",
                 lambda rows, c: len(rows) == 18
                 and all(0 < r[2] < r[1] for r in rows))],
    ),
    dict(
        id=12, ledger="Q563", concept="W3", tier="4 - Dates and times",
        title="Which day of the week sells",
        prompt=(
            "How many tickets were sold on each day of the week, and what"
            " percentage of all tickets that is, to two decimals.\n\n"
            "Report the day as strftime's number, 0 for Sunday through 6, in"
            " that order.\n\n"
            "Return: weekday, tickets, pct"
        ),
        solution=("SELECT strftime('%w', sold_at), COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)"
                  " FROM tickets GROUP BY 1 ORDER BY 1"),
        trap_sql=("SELECT strftime('%W', sold_at), COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)"
                  " FROM tickets GROUP BY 1 ORDER BY 1"),
        note="%w is the weekday; %W is the week of the year. The trap gets"
             " seventy-odd rows instead of seven, each a plausible-looking"
             " percentage. SUM(COUNT(*)) OVER () supplies the grand total from"
             " the grouped rows without a second pass over the table.",
        claims=[("seven days summing to 100 percent",
                 lambda rows, c: len(rows) == 7
                 and abs(sum(r[2] for r in rows) - 100) < 0.05)],
    ),
    dict(
        id=13, ledger="Q564", concept="D1", tier="4 - Dates and times",
        title="How old units are when refurbished",
        prompt=(
            "For each model, the average age in years at which its units were"
            " refurbished, to one decimal.\n\n"
            "Units never refurbished must not count at all.\n\n"
            "Return: model, avg_age"
        ),
        solution=("SELECT model, ROUND(AVG(refurbished_year - built_year), 1)"
                  " FROM rolling_stock WHERE refurbished_year IS NOT NULL"
                  " GROUP BY 1"),
        trap_sql=("SELECT model, ROUND(AVG(COALESCE(refurbished_year, 2026)"
                  " - built_year), 1) FROM rolling_stock GROUP BY 1"),
        note="The trap treats 'never refurbished' as 'refurbished this year',"
             " which drags every average up and invents a figure for models"
             " with no refurbishments at all. AVG already skips NULLs, so the"
             " untouched column would have been right; the WHERE makes the"
             " intent explicit and also drops models with nothing to average.",
        claims=[("only models with a refurbished unit",
                 lambda rows, c: len(rows) == c.execute(
                     "SELECT COUNT(DISTINCT model) FROM rolling_stock"
                     " WHERE refurbished_year IS NOT NULL").fetchone()[0])],
    ),
    dict(
        id=14, ledger="Q565", concept="D2", tier="4 - Dates and times",
        title="The second Monday of each month",
        prompt=(
            "How many services ran on the SECOND Monday of each month.\n\n"
            "Build it with modifiers. All eighteen months.\n\n"
            "Return: month, services"
        ),
        solution=("SELECT strftime('%Y-%m', run_date), COUNT(*) FROM services"
                  " WHERE run_date = date(run_date, 'start of month',"
                  " 'weekday 1', '+7 days') GROUP BY 1"),
        trap_sql=("SELECT strftime('%Y-%m', run_date), COUNT(*) FROM services"
                  " WHERE run_date = date(run_date, 'start of month',"
                  " '-1 day', 'weekday 1', '+7 days') GROUP BY 1"),
        note="'start of month' then 'weekday 1' is the first Monday -- it"
             " stays if the 1st is a Monday and advances otherwise -- and"
             " '+7 days' is the second. The trap steps back a day first,"
             " which lands in the previous month and then, when THAT month"
             " ends on a Monday, 'weekday 1' does not move: April and July"
             " 2025 come back with the wrong day's count. Same slip as Q534,"
             " one week later.",
        claims=[("eighteen months, each count that of a Monday",
                 lambda rows, c: len(rows) == 18)],
    ),
    # ================================================= 5 Joins and grain
    dict(
        id=15, ledger="Q566", concept="J2", tier="5 - Joins and grain",
        title="Staff based at each station",
        prompt=(
            "Every station with the number of staff based there -- stations"
            " with nobody must appear with 0, so all 60 rows come back.\n\n"
            "Return: station, staff"
        ),
        solution=("SELECT st.name, COUNT(sf.staff_id) FROM stations st"
                  " LEFT JOIN staff sf ON sf.base_station = st.station_id"
                  " GROUP BY st.station_id, st.name"),
        trap_sql=("SELECT st.name, COUNT(*) FROM stations st"
                  " LEFT JOIN staff sf ON sf.base_station = st.station_id"
                  " GROUP BY st.station_id, st.name"),
        note="COUNT(*) counts the row an outer join produces for a station"
             " with no staff -- NULLs and all -- so the empty stations report"
             " 1. COUNT of a column from the RIGHT table skips those NULLs."
             " Whenever you count over an outer join, name a column.",
        claims=[("all 60 stations, some with none, totalling the staff",
                 lambda rows, c: len(rows) == 60
                 and any(r[1] == 0 for r in rows)
                 and sum(r[1] for r in rows) == 40)],
    ),
    dict(
        id=16, ledger="Q567", concept="C2", tier="5 - Joins and grain",
        title="Tickets and units per service",
        prompt=(
            "For services 1 to 10: how many tickets each sold and how many"
            " units it was formed of.\n\n"
            "Both hang off `services`, so a service with 6 tickets and 2 units"
            " produces 12 joined rows. The counts must survive that.\n\n"
            "Return: service_id, tickets, units"
        ),
        solution=("SELECT s.service_id, COUNT(DISTINCT t.ticket_id),"
                  " COUNT(DISTINCT u.unit_id) FROM services s"
                  " LEFT JOIN tickets t ON t.service_id = s.service_id"
                  " LEFT JOIN service_units u ON u.service_id = s.service_id"
                  " WHERE s.service_id <= 10 GROUP BY s.service_id"),
        trap_sql=("SELECT s.service_id, COUNT(t.ticket_id),"
                  " COUNT(u.unit_id) FROM services s"
                  " LEFT JOIN tickets t ON t.service_id = s.service_id"
                  " LEFT JOIN service_units u ON u.service_id = s.service_id"
                  " WHERE s.service_id <= 10 GROUP BY s.service_id"),
        note="Two children of one parent multiply. Six tickets by two units is"
             " twelve rows, so COUNT(t.ticket_id) says 12 and COUNT(u.unit_id)"
             " says 12. COUNT(DISTINCT id) repairs a count because the"
             " duplicates share an id. It cannot repair a SUM -- that is"
             " question 17 of the last set, and question 29 here.",
        claims=[("ten services, and a two-unit service shows 2 not 12",
                 lambda rows, c: len(rows) == 10
                 and any(r[2] == 2 for r in rows)
                 and all(r[2] <= 2 for r in rows))],
    ),
    dict(
        id=17, ledger="Q568", concept="J2", tier="5 - Joins and grain",
        title="Units that have never run",
        prompt=(
            "Units of rolling stock that have never been assigned to a"
            " service. Write it as an outer join that keeps the"
            " non-matches.\n\n"
            "Return: unit_id, model"
        ),
        solution=("SELECT r.unit_id, r.model FROM rolling_stock r"
                  " LEFT JOIN service_units u ON u.unit_id = r.unit_id"
                  " WHERE u.unit_id IS NULL"),
        trap_sql=("SELECT r.unit_id, r.model FROM rolling_stock r"
                  " LEFT JOIN service_units u ON u.unit_id = r.unit_id"
                  " WHERE u.position IS NULL OR u.position <> 1"),
        note="The anti-join: keep every unit, then keep only those where the"
             " join found nothing. Test IS NULL on a column that can never be"
             " NULL in a real match -- the key -- and put nothing else in"
             " WHERE. The trap adds a second condition on the right table,"
             " which lets matched rows back in and returns units that ran in"
             " position 2.",
        claims=[("five units, none of them in service_units",
                 lambda rows, c: len(rows) == 5
                 and not c.execute(
                     "SELECT 1 FROM service_units WHERE unit_id IN (%s)"
                     " LIMIT 1" % ",".join(str(int(r[0])) for r in rows)
                 ).fetchall())],
    ),
    dict(
        id=18, ledger="Q569", concept="E1", tier="5 - Joins and grain",
        title="Services formed of two units",
        prompt=(
            "Services on 2025-06-02 formed of exactly two units, with the two"
            " unit ids in position order as 'front+rear'.\n\n"
            "Return: service_id, formation"
        ),
        solution=("SELECT su.service_id, GROUP_CONCAT(su.unit_id, '+'"
                  " ORDER BY su.position) FROM service_units su"
                  " JOIN services s ON s.service_id = su.service_id"
                  " WHERE s.run_date = '2025-06-02' GROUP BY su.service_id"
                  " HAVING COUNT(*) = 2"),
        trap_sql=("SELECT su.service_id, GROUP_CONCAT(su.unit_id, '+'"
                  " ORDER BY su.position) FROM service_units su"
                  " JOIN services s ON s.service_id = su.service_id"
                  " WHERE s.run_date = '2025-06-02' AND su.position = 2"
                  " GROUP BY su.service_id"),
        note="'Exactly two' is a property of the GROUP and lives in HAVING. The"
             " trap filters to position-2 rows, which does find the two-unit"
             " services -- but then only the rear unit is left to concatenate,"
             " so every formation is one id. A WHERE clause cannot both select"
             " a group and keep all its rows.",
        claims=[("every formation has one plus sign",
                 lambda rows, c: len(rows) > 3
                 and all(r[1].count('+') == 1 for r in rows))],
    ),
    # ================================================= 6 Window functions
    dict(
        id=19, ledger="Q570", concept="W1", tier="6 - Window functions",
        title="Incidents accumulating, per line",
        prompt=(
            "Incidents by line and month, with a running total that restarts"
            " for each line.\n\n"
            "Return: line_id, month, incidents, running_total"
        ),
        solution=("SELECT s.line_id, strftime('%Y-%m', i.reported_at) m,"
                  " COUNT(*), SUM(COUNT(*)) OVER (PARTITION BY s.line_id"
                  " ORDER BY strftime('%Y-%m', i.reported_at) ROWS BETWEEN"
                  " UNBOUNDED PRECEDING AND CURRENT ROW) FROM incidents i"
                  " JOIN services s ON s.service_id = i.service_id"
                  " GROUP BY 1, 2"),
        trap_sql=("SELECT s.line_id, strftime('%Y-%m', i.reported_at) m,"
                  " COUNT(*), SUM(COUNT(*)) OVER ("
                  " ORDER BY strftime('%Y-%m', i.reported_at) ROWS BETWEEN"
                  " UNBOUNDED PRECEDING AND CURRENT ROW) FROM incidents i"
                  " JOIN services s ON s.service_id = i.service_id"
                  " GROUP BY 1, 2"),
        note="Without PARTITION BY the running total runs across every line"
             " at once -- and because the rows are ordered by month only,"
             " six lines' worth of the same month arrive together and the"
             " total jumps in lumps. PARTITION BY line_id restarts the"
             " accumulation, and ORDER BY inside the partition decides the"
             " direction.",
        claims=[("each line's last running total is its own incident count",
                 lambda rows, c: all(
                     max(r[3] for r in rows if r[0] == lid) == sum(
                         r[2] for r in rows if r[0] == lid)
                     for lid in {r[0] for r in rows}))],
    ),
    dict(
        id=20, ledger="Q571", concept="W2", tier="6 - Window functions",
        title="Lines by revenue",
        prompt=(
            "Every line with its ticket revenue in pence and its rank, 1 for"
            " the highest.\n\n"
            "Return: line_name, revenue, rank"
        ),
        solution=("SELECT l.name, SUM(t.price_pence), DENSE_RANK() OVER"
                  " (ORDER BY SUM(t.price_pence) DESC) FROM lines l"
                  " JOIN services s ON s.line_id = l.line_id"
                  " JOIN tickets t ON t.service_id = s.service_id"
                  " GROUP BY l.name"),
        trap_sql=("SELECT l.name, SUM(t.price_pence), DENSE_RANK() OVER"
                  " (ORDER BY SUM(t.price_pence)) FROM lines l"
                  " JOIN services s ON s.line_id = l.line_id"
                  " JOIN tickets t ON t.service_id = s.service_id"
                  " GROUP BY l.name"),
        note="The ORDER BY inside OVER decides which end is rank 1. Ascending"
             " puts the poorest line first, which is a perfectly tidy result"
             " for the opposite question. Ranking an aggregate is fine because"
             " windows run after GROUP BY -- SUM(...) inside the OVER is the"
             " grouped value.",
        claims=[("six lines, rank 1 has the most revenue",
                 lambda rows, c: len(rows) == 6
                 and max(rows, key=lambda r: r[1])[2] == 1)],
    ),
    dict(
        id=21, ledger="Q572", concept="W3", tier="6 - Window functions",
        title="Share of the day's takings",
        prompt=(
            "For every service on 2025-05-05 that sold tickets: its revenue"
            " and what percentage of that DAY's revenue it is, to two"
            " decimals.\n\n"
            "The percentages add to 100.\n\n"
            "Return: service_id, revenue, pct_of_day"
        ),
        solution=("SELECT s.service_id, SUM(t.price_pence), ROUND(100.0"
                  " * SUM(t.price_pence) / SUM(SUM(t.price_pence)) OVER (), 2)"
                  " FROM services s JOIN tickets t"
                  " ON t.service_id = s.service_id"
                  " WHERE s.run_date = '2025-05-05' GROUP BY s.service_id"),
        trap_sql=("SELECT s.service_id, SUM(t.price_pence), ROUND(100.0"
                  " * SUM(t.price_pence) / (SELECT SUM(price_pence)"
                  " FROM tickets), 2) FROM services s JOIN tickets t"
                  " ON t.service_id = s.service_id"
                  " WHERE s.run_date = '2025-05-05' GROUP BY s.service_id"),
        note="The denominator has to be the day's total, and the window over"
             " the grouped rows IS the day's total, because the WHERE has"
             " already narrowed the rows to that day. The trap's scalar"
             " subquery reaches back to the whole table -- every ticket ever"
             " sold -- so the percentages are tiny and sum to nothing like"
             " 100.",
        claims=[("the shares sum to 100",
                 lambda rows, c: len(rows) > 5
                 and abs(sum(r[2] for r in rows) - 100) < 0.05)],
    ),
    dict(
        id=22, ledger="Q573", concept="W2", tier="6 - Window functions",
        title="Three best services per line",
        prompt=(
            "For each line, its three highest-earning services. Eighteen"
            " rows; ties by the lower service_id.\n\n"
            "Return: line_id, service_id, revenue"
        ),
        solution=("SELECT line_id, service_id, r FROM (SELECT s.line_id,"
                  " s.service_id, SUM(t.price_pence) r, ROW_NUMBER() OVER"
                  " (PARTITION BY s.line_id ORDER BY SUM(t.price_pence) DESC,"
                  " s.service_id) rn FROM services s JOIN tickets t"
                  " ON t.service_id = s.service_id GROUP BY s.service_id)"
                  " WHERE rn <= 3"),
        trap_sql=("SELECT line_id, service_id, r FROM (SELECT s.line_id,"
                  " s.service_id, SUM(t.price_pence) r, ROW_NUMBER() OVER"
                  " (PARTITION BY s.line_id ORDER BY SUM(t.price_pence) DESC,"
                  " s.service_id) rn FROM services s JOIN tickets t"
                  " ON t.service_id = s.service_id GROUP BY s.service_id)"
                  " WHERE rn < 3"),
        note="Top-N per group: number in a subquery, filter outside, because"
             " WHERE runs before the window exists. ROW_NUMBER starts at 1, so"
             " 'three per line' is rn <= 3; the trap's rn < 3 hands back two."
             " ROW_NUMBER with an explicit tiebreak guarantees exactly N; RANK"
             " would return more when revenues tie.",
        claims=[("exactly three per line",
                 lambda rows, c: len(rows) == 18
                 and all(sum(1 for r in rows if r[0] == lid) == 3
                         for lid in {r[0] for r in rows}))],
    ),
    # ================================================ 7 Changing the data
    # Writable questions. The editor's script runs in a throwaway copy of the
    # database, then probe_sql reads the result and THAT is compared with the
    # reference. driver_sql, where present, is run by the question after the
    # script -- to fire a trigger, or to be refused by one.
    dict(
        id=23, ledger="Q574", concept="DML", tier="7 - Changing the data",
        kind="script",
        title="Refurbish the old fleet",
        prompt=(
            "Record a 2026 refurbishment for every unit built before 2010 that"
            " has never been refurbished. Units that HAVE been refurbished must"
            " keep their existing year.\n\n"
            "23 units change. Write the UPDATE.\n\n"
            "Checked: refurbished_year, grouped by whether the unit was built"
            " before 2010"
        ),
        solution=("UPDATE rolling_stock\n"
                  "SET refurbished_year = 2026\n"
                  "WHERE refurbished_year IS NULL AND built_year < 2010;"),
        trap_sql=("UPDATE rolling_stock\n"
                  "SET refurbished_year = 2026\n"
                  "WHERE built_year < 2010;"),
        probe_sql=("SELECT built_year < 2010 AS old, refurbished_year, COUNT(*)"
                   " FROM rolling_stock GROUP BY 1, 2 ORDER BY 1, 2"),
        note="An UPDATE with no guard rewrites every row its WHERE reaches --"
             " here it stamps 2026 over fourteen genuine refurbishment years,"
             " and nothing warns you. 'Rows changed: 37' against an expected"
             " 23 is the tell, and the reason the status bar reports it. In"
             " T-SQL the guard is the same clause; the difference is only that"
             " SQLite has no @@ROWCOUNT to check afterwards.",
        claims=[("thirteen units still unrefurbished, all built 2010 or later",
                 lambda rows, c: any(r[0] == 0 and r[1] is None and r[2] == 13
                                     for r in rows)
                 and not any(r[0] == 1 and r[1] is None for r in rows))],
    ),
    dict(
        id=24, ledger="Q575", concept="DML", tier="7 - Changing the data",
        kind="script",
        title="Archive the cancellations",
        prompt=(
            "Move the cancelled services out of `services`: create a table"
            " `cancelled_services` holding copies of all 314 cancelled rows,"
            " then delete them from `services`.\n\n"
            "Two statements. CREATE TABLE ... AS SELECT builds a table and"
            " fills it in one go.\n\n"
            "Checked: how many services remain, how many of those are"
            " cancelled, and how many rows the archive holds"
        ),
        solution=("CREATE TABLE cancelled_services AS\n"
                  "SELECT * FROM services WHERE cancelled = 1;\n"
                  "DELETE FROM services WHERE cancelled = 1;"),
        trap_sql=("CREATE TABLE cancelled_services AS\n"
                  "SELECT * FROM services WHERE cancelled = 1;\n"
                  "DELETE FROM services WHERE service_id IN"
                  " (SELECT service_id FROM cancelled_services)"
                  " AND cancelled = 0;"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM services),"
                   " (SELECT COUNT(*) FROM services WHERE cancelled = 1),"
                   " (SELECT COUNT(*) FROM cancelled_services)"),
        note="Copy first, delete second -- the other order loses the rows."
             " CREATE TABLE AS takes the column names and types from the"
             " SELECT but NOT the constraints, so the archive has no primary"
             " key; fine for a copy, wrong for a table you mean to keep. The"
             " DELETE works because cancelled services have no stops, tickets"
             " or units pointing at them -- with foreign keys on, deleting a"
             " referenced row fails. The trap's DELETE contradicts itself and"
             " removes nothing.",
        claims=[("314 archived, none left, and the count dropped by 314",
                 lambda rows, c: rows[0][2] == 314 and rows[0][1] == 0
                 and rows[0][0] == 11114 - 314)],
    ),
    dict(
        id=25, ledger="Q576", concept="UPS", tier="7 - Changing the data",
        kind="script",
        title="Insert or update, in one statement",
        prompt=(
            "Station 1's 2025 footfall row exists. Write ONE INSERT that would"
            " create it if it did not, and -- since it does -- updates q1 to"
            " 22000 while leaving q2, q3 and q4 alone.\n\n"
            "Use the values (1, 2025, 22000, 24295, 17202, 17975).\n\n"
            "Checked: that row, and the table's row count"
        ),
        solution=("INSERT INTO station_footfall (station_id, year, q1, q2, q3, q4)\n"
                  "VALUES (1, 2025, 22000, 24295, 17202, 17975)\n"
                  "ON CONFLICT (station_id, year) DO UPDATE SET q1 = excluded.q1;"),
        trap_sql=("INSERT OR IGNORE INTO station_footfall"
                  " (station_id, year, q1, q2, q3, q4)\n"
                  "VALUES (1, 2025, 22000, 24295, 17202, 17975);"),
        probe_sql=("SELECT year, q1, q2, q3, q4,"
                   " (SELECT COUNT(*) FROM station_footfall)"
                   " FROM station_footfall WHERE station_id = 1 AND year = 2025"),
        note="UPSERT. ON CONFLICT names the unique key that might collide and"
             " DO UPDATE says what to do when it does; `excluded` is the row"
             " you TRIED to insert, so `q1 = excluded.q1` takes the new value."
             " INSERT OR IGNORE is the trap: on a collision it silently does"
             " nothing, leaving the old q1 in place, and reports success. This"
             " is SQLite's MERGE.",
        claims=[("q1 updated, the other quarters and the row count untouched",
                 lambda rows, c: rows[0][1] == 22000 and rows[0][2] == 24295
                 and rows[0][5] == 180)],
    ),
    dict(
        id=26, ledger="Q577", concept="TXN", tier="7 - Changing the data",
        kind="script",
        title="A raise, half of which is withdrawn",
        prompt=(
            "In one transaction: give every driver a 3% raise, then set a"
            " savepoint, then give every guard 3% too -- then roll back to the"
            " savepoint so the guards' raise is undone, and commit.\n\n"
            "Keep salaries whole pounds: CAST(ROUND(salary * 1.03) AS"
            " INTEGER). The drivers' raise must survive; the guards' must"
            " not.\n\n"
            "Checked: total salary by role for drivers and guards"
        ),
        solution=("BEGIN;\n"
                  "UPDATE staff SET salary = CAST(ROUND(salary * 1.03) AS INTEGER)"
                  " WHERE role = 'driver';\n"
                  "SAVEPOINT guards;\n"
                  "UPDATE staff SET salary = CAST(ROUND(salary * 1.03) AS INTEGER)"
                  " WHERE role = 'guard';\n"
                  "ROLLBACK TO guards;\n"
                  "COMMIT;"),
        trap_sql=("BEGIN;\n"
                  "UPDATE staff SET salary = CAST(ROUND(salary * 1.03) AS INTEGER)"
                  " WHERE role = 'driver';\n"
                  "SAVEPOINT guards;\n"
                  "UPDATE staff SET salary = CAST(ROUND(salary * 1.03) AS INTEGER)"
                  " WHERE role = 'guard';\n"
                  "ROLLBACK;"),
        probe_sql=("SELECT role, SUM(salary) FROM staff"
                   " WHERE role IN ('driver', 'guard') GROUP BY 1"),
        note="ROLLBACK TO a savepoint undoes only what came after it and leaves"
             " the transaction open; plain ROLLBACK undoes everything since"
             " BEGIN and ends it, so the trap loses the drivers' raise too and"
             " never commits. Note that ROLLBACK TO does not RELEASE the"
             " savepoint -- COMMIT does, along with everything else. This is"
             " the T-SQL SAVE TRANSACTION / ROLLBACK TRANSACTION name pattern"
             " with different keywords.",
        claims=[("drivers up, guards unchanged",
                 lambda rows, c: dict(rows)['guard'] == 687388
                 and dict(rows)['driver'] > 384984)],
    ),
    dict(
        id=27, ledger="Q578", concept="TRG", tier="7 - Changing the data",
        kind="script",
        title="A rule no CHECK can express",
        prompt=(
            "An incident cannot be reported before its service ran. Write a"
            " trigger that refuses any INSERT into `incidents` whose"
            " reported_at is earlier than that service's run_date. Same day is"
            " fine.\n\n"
            "After your script, the question inserts three incidents for"
            " service 1 (which ran 2025-01-01): reported 2024-12-31, 2025-01-01"
            " and 2025-01-02. Exactly one should be refused.\n\n"
            "Checked: which of the three landed"
        ),
        solution=("CREATE TRIGGER incident_after_service\n"
                  "BEFORE INSERT ON incidents\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'incident reported before the service ran')\n"
                  "  WHERE NEW.reported_at <\n"
                  "        (SELECT run_date FROM services"
                  " WHERE service_id = NEW.service_id);\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER incident_after_service\n"
                  "BEFORE INSERT ON incidents\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'incident reported before the service ran')\n"
                  "  WHERE NEW.reported_at <=\n"
                  "        (SELECT run_date FROM services"
                  " WHERE service_id = NEW.service_id);\n"
                  "END;"),
        driver_sql=("INSERT INTO incidents (service_id, reported_at, kind,"
                    " delay_minutes) VALUES (1, '2024-12-31', 'fault', 5);\n"
                    "INSERT INTO incidents (service_id, reported_at, kind,"
                    " delay_minutes) VALUES (1, '2025-01-01', 'fault', 5);\n"
                    "INSERT INTO incidents (service_id, reported_at, kind,"
                    " delay_minutes) VALUES (1, '2025-01-02', 'fault', 5);"),
        probe_sql=("SELECT reported_at FROM incidents WHERE service_id = 1"
                   " AND kind = 'fault' AND delay_minutes = 5 ORDER BY 1"),
        note="A CHECK constraint can only see its own row; this rule needs"
             " another table, and that is what triggers are for. The body is"
             " a SELECT that calls RAISE(ABORT, msg) -- RAISE is a function,"
             " and a SELECT that produces a row executes it, so the WHERE is"
             " the condition. NEW.column is the row being inserted. The trap's"
             " <= refuses same-day incidents too. This is SQLite's THROW /"
             " RAISERROR, and BEFORE INSERT its INSTEAD OF -- there is no"
             " TRY/CATCH; the abort rolls back the statement.",
        claims=[("two of the three landed, and not the early one",
                 lambda rows, c: [r[0] for r in rows]
                 == ['2025-01-01', '2025-01-02'])],
    ),
    dict(
        id=28, ledger="Q579", concept="TRG", tier="7 - Changing the data",
        kind="script",
        title="An audit trail for pay changes",
        prompt=(
            "Create a table `salary_audit (staff_id, old_salary, new_salary)`"
            " and a trigger that writes a row to it whenever a member of"
            " staff's salary ACTUALLY changes -- not when some other column is"
            " updated, and not when a salary is set to the value it already"
            " had.\n\n"
            "After your script, the question runs three UPDATEs: staff 2's"
            " salary to 50000, staff 3's salary to itself, and staff 4's name"
            " to itself. Exactly one audit row should result.\n\n"
            "Checked: the audit table"
        ),
        solution=("CREATE TABLE salary_audit (staff_id INTEGER,"
                  " old_salary INTEGER, new_salary INTEGER);\n"
                  "CREATE TRIGGER log_salary\n"
                  "AFTER UPDATE OF salary ON staff\n"
                  "WHEN OLD.salary <> NEW.salary\n"
                  "BEGIN\n"
                  "  INSERT INTO salary_audit VALUES"
                  " (NEW.staff_id, OLD.salary, NEW.salary);\n"
                  "END;"),
        trap_sql=("CREATE TABLE salary_audit (staff_id INTEGER,"
                  " old_salary INTEGER, new_salary INTEGER);\n"
                  "CREATE TRIGGER log_salary\n"
                  "AFTER UPDATE ON staff\n"
                  "BEGIN\n"
                  "  INSERT INTO salary_audit VALUES"
                  " (NEW.staff_id, OLD.salary, NEW.salary);\n"
                  "END;"),
        driver_sql=("UPDATE staff SET salary = 50000 WHERE staff_id = 2;\n"
                    "UPDATE staff SET salary = salary WHERE staff_id = 3;\n"
                    "UPDATE staff SET name = name WHERE staff_id = 4;"),
        probe_sql=("SELECT staff_id, old_salary, new_salary FROM salary_audit"
                   " ORDER BY 1"),
        note="Two filters, in two places. UPDATE OF salary fires the trigger"
             " only when that column is in the SET list; WHEN OLD.salary <>"
             " NEW.salary fires it only when the value moved. The trap has"
             " neither and logs all three updates, two of them non-events."
             " OLD and NEW are the row before and after, which is the same"
             " pair T-SQL calls deleted and inserted -- except those are"
             " tables holding every affected row, and SQLite's trigger runs"
             " once PER ROW.",
        claims=[("one audit row, for staff 2",
                 lambda rows, c: rows == [(2, 47267, 50000)])],
    ),
    dict(
        id=29, ledger="Q580", concept="VIEW", tier="7 - Changing the data",
        kind="script",
        title="A view that does not lie",
        prompt=(
            "Create a view `line_revenue (line_name, revenue_pence)` giving"
            " each line's total ticket revenue.\n\n"
            "Six rows when selected. Be careful what you join: a view is a"
            " saved query, and a fan-out saved is a fan-out every time anyone"
            " uses it.\n\n"
            "Checked: SELECT * FROM line_revenue"
        ),
        solution=("CREATE VIEW line_revenue AS\n"
                  "SELECT l.name AS line_name, SUM(t.price_pence) AS revenue_pence\n"
                  "FROM lines l\n"
                  "JOIN services s ON s.line_id = l.line_id\n"
                  "JOIN tickets t ON t.service_id = s.service_id\n"
                  "GROUP BY l.name;"),
        trap_sql=("CREATE VIEW line_revenue AS\n"
                  "SELECT l.name AS line_name, SUM(t.price_pence) AS revenue_pence\n"
                  "FROM lines l\n"
                  "JOIN services s ON s.line_id = l.line_id\n"
                  "JOIN stops p ON p.service_id = s.service_id\n"
                  "JOIN tickets t ON t.service_id = s.service_id\n"
                  "GROUP BY l.name;"),
        probe_sql="SELECT * FROM line_revenue ORDER BY 1",
        note="A view is a named SELECT, re-run on every reference; it stores"
             " no data and cannot go stale, but it also cannot be checked"
             " once and trusted. The trap joins `stops`, which adds no column"
             " and multiplies every ticket by the service's number of calls --"
             " revenue seven times too high, in a view called line_revenue,"
             " for as long as it exists. Views are where a grain mistake does"
             " the most damage, because nobody re-reads them.",
        claims=[("six lines, revenue matching the ticket table",
                 lambda rows, c: len(rows) == 6
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT SUM(price_pence) FROM tickets").fetchone()[0])],
    ),
    dict(
        id=30, ledger="Q581", concept="GEN", tier="7 - Changing the data",
        kind="script",
        title="A column that computes itself",
        prompt=(
            "Add a column `price_pounds` to `tickets` that is always the price"
            " in pounds, as a REAL -- computed from price_pence, never stored"
            " out of step with it.\n\n"
            "A generated column. ALTER TABLE can add one as long as it is"
            " VIRTUAL.\n\n"
            "Checked: price_pounds for tickets 1 to 3"
        ),
        solution=("ALTER TABLE tickets ADD COLUMN price_pounds REAL\n"
                  "GENERATED ALWAYS AS (price_pence / 100.0) VIRTUAL;"),
        trap_sql=("ALTER TABLE tickets ADD COLUMN price_pounds REAL\n"
                  "GENERATED ALWAYS AS (price_pence / 100) VIRTUAL;"),
        probe_sql=("SELECT ticket_id, price_pounds FROM tickets"
                   " WHERE ticket_id <= 3"),
        note="GENERATED ALWAYS AS (expr) defines the column by a formula over"
             " the row; VIRTUAL computes it on read, STORED writes it to disk"
             " (and cannot be added by ALTER TABLE). Declaring it REAL does"
             " not make the arithmetic real -- price_pence / 100 is integer"
             " division before the type is ever consulted, so the trap stores"
             " 11.0 for 1165 pence. Same rule as every division question in"
             " this set, now baked into the schema. T-SQL calls this a"
             " computed column.",
        claims=[("three tickets, pounds with pence",
                 lambda rows, c: len(rows) == 3
                 and any(r[1] != int(r[1]) for r in rows))],
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
