"""Practice exercises: thirty questions on the railway schema.

Twenty-two are SELECT questions across the usual tiers, graded on the rows
they return. The last eight are WRITABLE questions, graded on the state of the
database after your script runs. They cover what SQLite has in place of a
procedural language, and this set takes constructs none of the three earlier
sets did --

  * UPDATE against INSERT OR REPLACE, and what "replace" really does
  * DELETE driven by a window function in a subquery
  * a multi-row INSERT with named columns and defaults
  * conflict clauses inside a transaction: OR IGNORE against OR ROLLBACK
  * a BEFORE DELETE trigger that cascades by hand
  * an AFTER INSERT trigger that fills in the row just written
  * a view built on another view
  * an index, and the leading-column rule that decides whether it is used

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script -- the delete your trigger must
cascade, or the inserts it must fill in.
"""

import sqlite3

EXERCISES = [
    # ========================================================== 1 Warm-up
    dict(
        id=1, ledger="Q642", concept="A2", tier="1 - Warm-up",
        title="Incidents by kind",
        prompt=(
            "One row per kind of incident: how many, and what percentage of"
            " all incidents that is, to two decimals.\n\n"
            "Return: kind, incidents, pct"
        ),
        solution=("SELECT kind, COUNT(*), ROUND(100.0 * COUNT(*)"
                  " / (SELECT COUNT(*) FROM incidents), 2) FROM incidents"
                  " GROUP BY 1"),
        trap_sql=("SELECT kind, COUNT(*), ROUND(100 * COUNT(*)"
                  " / (SELECT COUNT(*) FROM incidents), 2) FROM incidents"
                  " GROUP BY 1"),
        note="100 * 201 / 971 is integer division and lands on 20; the"
             " ROUND then has nothing to work with. One REAL anywhere in"
             " the expression makes the whole thing REAL, and 100.0 is the"
             " cheapest place to put it. The scalar subquery runs once for"
             " the whole statement, not once per group.",
        claims=[("five kinds summing to 100 percent",
                 lambda rows, c: len(rows) == 5
                 and abs(sum(r[2] for r in rows) - 100) < 0.05)],
    ),
    dict(
        id=2, ledger="Q643", concept="A1", tier="1 - Warm-up",
        title="Open returns by class",
        prompt=(
            "One row per class: tickets sold, how many of them are open"
            " returns -- no destination recorded -- and what percentage of"
            " the class that is, to two decimals.\n\n"
            "Return: class, tickets, open_returns, pct"
        ),
        solution=("SELECT class, COUNT(*), SUM(to_station IS NULL),"
                  " ROUND(100.0 * SUM(to_station IS NULL) / COUNT(*), 2)"
                  " FROM tickets GROUP BY 1"),
        trap_sql=("SELECT class, COUNT(*), COUNT(to_station),"
                  " ROUND(100.0 * COUNT(to_station) / COUNT(*), 2)"
                  " FROM tickets GROUP BY 1"),
        note="COUNT(to_station) counts the rows where it is NOT NULL -- the"
             " tickets WITH a destination -- so the trap reports 95% where"
             " 5% was asked. Counting the NULLs takes a condition: SUM(x IS"
             " NULL), or COUNT(*) - COUNT(x). A comparison is 0 or 1 in"
             " SQLite, which is what makes SUM of one a count.",
        claims=[("three classes, open returns a few percent of each",
                 lambda rows, c: len(rows) == 3
                 and all(0 < r[3] < 10 for r in rows))],
    ),
    dict(
        id=3, ledger="Q644", concept="A3", tier="1 - Warm-up",
        title="Big operators that cancel",
        prompt=(
            "Operators that scheduled at least 2750 services AND cancelled"
            " more than 3% of them, with the service count and the rate to"
            " two decimals.\n\n"
            "Both conditions describe the operator as a whole.\n\n"
            "Return: operator, services, cancel_pct"
        ),
        solution=("SELECT o.name, COUNT(*), ROUND(100.0 * AVG(s.cancelled), 2)"
                  " FROM operators o JOIN services s"
                  " ON s.operator_id = o.operator_id GROUP BY o.name"
                  " HAVING COUNT(*) >= 2750 AND AVG(s.cancelled) > 0.03"),
        trap_sql=("SELECT o.name, COUNT(*), ROUND(100.0 * AVG(s.cancelled), 2)"
                  " FROM operators o JOIN services s"
                  " ON s.operator_id = o.operator_id WHERE s.cancelled = 1"
                  " GROUP BY o.name HAVING COUNT(*) >= 2750"),
        note="AVG of a 0/1 column is the fraction that are 1 -- a rate in"
             " one word. The trap filters to cancelled services first, so"
             " its count is of cancellations, never near 2750, and its"
             " average is 1.0 for everyone: no rows. Conditions about the"
             " group go in HAVING; the join is needed only for the name.",
        claims=[("at least one operator, each meeting both conditions",
                 lambda rows, c: len(rows) > 0
                 and all(r[1] >= 2750 and r[2] > 3 for r in rows))],
    ),
    # ========================================== 2 Sequences and strings
    dict(
        id=4, ledger="Q645", concept="W3", tier="2 - Sequences and strings",
        title="Legs that ran slow",
        prompt=(
            "For service 500, each leg's scheduled minutes and actual"
            " minutes -- from the previous stop's arrival to this one's,"
            " timetabled and as it happened -- and the minutes lost, actual"
            " minus scheduled.\n\n"
            "The first stop has no leg, so it is NULL across.\n\n"
            "Return: stop_seq, sched_leg, actual_leg, lost"
        ),
        solution=("SELECT stop_seq, sched_leg, actual_leg, actual_leg - sched_leg"
                  " FROM (SELECT stop_seq, (strftime('%s', sched_arrive)"
                  " - strftime('%s', LAG(sched_arrive) OVER w)) / 60 sched_leg,"
                  " (strftime('%s', actual_arrive) - strftime('%s',"
                  " LAG(actual_arrive) OVER w)) / 60 actual_leg FROM stops"
                  " WHERE service_id = 500 WINDOW w AS (ORDER BY stop_seq))"),
        trap_sql=("SELECT stop_seq, sched_leg, actual_leg, actual_leg - sched_leg"
                  " FROM (SELECT stop_seq, (strftime('%s', sched_arrive)"
                  " - strftime('%s', LAG(sched_arrive) OVER w)) / 60 sched_leg,"
                  " (strftime('%s', actual_arrive) - strftime('%s',"
                  " sched_arrive)) / 60 actual_leg FROM stops"
                  " WHERE service_id = 500 WINDOW w AS (ORDER BY stop_seq))"),
        note="Two LAGs over the same window, one per time column. The"
             " trap's 'actual leg' is actual minus SCHEDULED at the same"
             " stop -- that is lateness, not a leg -- and the arithmetic"
             " that follows is meaningless but produces tidy small numbers."
             " A named WINDOW keeps the two LAGs in step. Reused in"
             " question 20 with a different offset.",
        claims=[("first row blank, then legs of a few minutes",
                 lambda rows, c: rows[0][1] is None and rows[0][3] is None
                 and all(0 < r[1] < 30 for r in rows[1:]))],
    ),
    dict(
        id=5, ledger="Q646", concept="STR", tier="2 - Sequences and strings",
        title="A handle for every member of staff",
        prompt=(
            "Every member of staff with a login handle: the name in lower"
            " case with the space replaced by a dot -- 'Gareth Sedgwick'"
            " becomes 'gareth.sedgwick'.\n\n"
            "Return: staff_id, handle"
        ),
        solution="SELECT staff_id, LOWER(REPLACE(name, ' ', '.')) FROM staff",
        trap_sql="SELECT staff_id, REPLACE(name, ' ', '.') FROM staff",
        note="Two string functions nested: REPLACE swaps every occurrence of"
             " one substring for another, LOWER folds the case. The trap"
             " forgets the second and hands back 'Gareth.Sedgwick', which"
             " reads fine and is not what was asked. Order does not matter"
             " here; it would if the replacement itself had capitals.",
        claims=[("forty handles, all lower case with one dot",
                 lambda rows, c: len(rows) == 40 and all(
                     r[1] == r[1].lower() and r[1].count('.') == 1
                     for r in rows))],
    ),
    dict(
        id=6, ledger="Q647", concept="W1", tier="2 - Sequences and strings",
        title="The second call",
        prompt=(
            "For every service that ran on 2025-04-07, the station_id of its"
            " SECOND stop -- one row per service, and no row of NULLs.\n\n"
            "Use NTH_VALUE, and mind its frame.\n\n"
            "Return: service_id, second_call"
        ),
        solution=("SELECT DISTINCT service_id, NTH_VALUE(station_id, 2) OVER"
                  " (PARTITION BY service_id ORDER BY stop_seq ROWS BETWEEN"
                  " UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) FROM stops"
                  " WHERE service_id IN (SELECT service_id FROM services"
                  " WHERE run_date = '2025-04-07')"),
        trap_sql=("SELECT DISTINCT service_id, NTH_VALUE(station_id, 2) OVER"
                  " (PARTITION BY service_id ORDER BY stop_seq) FROM stops"
                  " WHERE service_id IN (SELECT service_id FROM services"
                  " WHERE run_date = '2025-04-07')"),
        note="With an ORDER BY and no frame clause, a window runs from the"
             " start of the partition to the CURRENT row -- so on the first"
             " stop there is no second value yet, and NTH_VALUE returns"
             " NULL. DISTINCT then keeps two rows per service, one of them"
             " NULL. Widening the frame to the whole partition makes every"
             " row see the same second value. LAST_VALUE has the identical"
             " trap.",
        claims=[("one row per running service, none NULL",
                 lambda rows, c: len(rows) == len({r[0] for r in rows})
                 and all(r[1] is not None for r in rows)
                 and len(rows) == c.execute(
                     "SELECT COUNT(*) FROM services WHERE run_date"
                     " = '2025-04-07' AND cancelled = 0").fetchone()[0])],
    ),
    dict(
        id=7, ledger="Q648", concept="S1", tier="2 - Sequences and strings",
        title="One line or the other, not both",
        prompt=(
            "Towns with a station on line 4's route or on line 5's, but NOT"
            " on both.\n\n"
            "Each line calls in eight towns; three are shared.\n\n"
            "Return: town"
        ),
        solution=("SELECT town FROM (SELECT st.town FROM stops sp JOIN services s"
                  " ON s.service_id = sp.service_id JOIN stations st"
                  " ON st.station_id = sp.station_id WHERE s.line_id = 4"
                  " UNION SELECT st.town FROM stops sp JOIN services s"
                  " ON s.service_id = sp.service_id JOIN stations st"
                  " ON st.station_id = sp.station_id WHERE s.line_id = 5)"
                  " EXCEPT SELECT st.town FROM stops sp JOIN services s"
                  " ON s.service_id = sp.service_id JOIN stations st"
                  " ON st.station_id = sp.station_id WHERE s.line_id = 4"
                  " INTERSECT SELECT st.town FROM stops sp JOIN services s"
                  " ON s.service_id = sp.service_id JOIN stations st"
                  " ON st.station_id = sp.station_id WHERE s.line_id = 5"),
        trap_sql=("SELECT st.town FROM stops sp JOIN services s"
                  " ON s.service_id = sp.service_id JOIN stations st"
                  " ON st.station_id = sp.station_id WHERE s.line_id = 4"
                  " EXCEPT SELECT st.town FROM stops sp JOIN services s"
                  " ON s.service_id = sp.service_id JOIN stations st"
                  " ON st.station_id = sp.station_id WHERE s.line_id = 5"),
        note="Symmetric difference: (A UNION B) EXCEPT (A INTERSECT B). The"
             " trap is A EXCEPT B, which is only line 4's own towns and"
             " misses line 5's. SQLite evaluates compound operators left to"
             " right with no precedence, so the union sits in a subquery to"
             " be computed first; the EXCEPT then takes away the intersect"
             " that follows it.",
        claims=[("five towns, each on exactly one of the two lines",
                 lambda rows, c: len(rows) == 5 and all(
                     c.execute("SELECT COUNT(DISTINCT s.line_id) FROM stops sp"
                               " JOIN services s ON s.service_id = sp.service_id"
                               " JOIN stations st ON st.station_id = sp.station_id"
                               " WHERE st.town = ? AND s.line_id IN (4, 5)",
                               (r[0],)).fetchone()[0] == 1 for r in rows))],
    ),
    # ============================================ 3 Unpivot and set ops
    dict(
        id=8, ledger="Q649", concept="UNP", tier="3 - Unpivot and set ops",
        title="Station 9, quarter on quarter",
        prompt=(
            "Station 9's footfall as one row per quarter across all three"
            " years, labelled like '2024-q3', with the change from the"
            " previous quarter. Twelve rows in order; the first has no"
            " change.\n\n"
            "Return: period, footfall, change"
        ),
        solution=("SELECT p, f, f - LAG(f) OVER (ORDER BY p) FROM"
                  " (SELECT year || '-q1' p, q1 f FROM station_footfall"
                  " WHERE station_id = 9 UNION ALL SELECT year || '-q2', q2"
                  " FROM station_footfall WHERE station_id = 9 UNION ALL"
                  " SELECT year || '-q3', q3 FROM station_footfall"
                  " WHERE station_id = 9 UNION ALL SELECT year || '-q4', q4"
                  " FROM station_footfall WHERE station_id = 9) ORDER BY p"),
        trap_sql=("SELECT p, f, f - LAG(f) OVER (ORDER BY f) FROM"
                  " (SELECT year || '-q1' p, q1 f FROM station_footfall"
                  " WHERE station_id = 9 UNION ALL SELECT year || '-q2', q2"
                  " FROM station_footfall WHERE station_id = 9 UNION ALL"
                  " SELECT year || '-q3', q3 FROM station_footfall"
                  " WHERE station_id = 9 UNION ALL SELECT year || '-q4', q4"
                  " FROM station_footfall WHERE station_id = 9) ORDER BY p"),
        note="Unpivot, then a window over the result. The label is built so"
             " that text order IS time order -- '2023-q4' < '2024-q1' -- and"
             " the LAG orders by it. The trap orders the LAG by footfall,"
             " so 'previous' means next-smallest and every change is"
             " positive. The outer ORDER BY only sorts the display; the"
             " window's ORDER BY decides what 'previous' means.",
        claims=[("twelve periods, changes summing to last minus first",
                 lambda rows, c: len(rows) == 12 and rows[0][2] is None
                 and sum(r[2] for r in rows[1:]) == rows[-1][1] - rows[0][1])],
    ),
    dict(
        id=9, ledger="Q650", concept="J1", tier="3 - Unpivot and set ops",
        title="Opened within a year of each other",
        prompt=(
            "Pairs of stations that opened within 365 days of one another,"
            " each pair once with the lower station_id first, and both"
            " dates.\n\n"
            "Not 'the same calendar year': December and the following"
            " January count.\n\n"
            "Return: station_a, station_b, opened_a, opened_b"
        ),
        solution=("SELECT a.station_id, b.station_id, a.opened_on, b.opened_on"
                  " FROM stations a JOIN stations b ON b.station_id > a.station_id"
                  " AND ABS(julianday(b.opened_on) - julianday(a.opened_on)) <= 365"),
        trap_sql=("SELECT a.station_id, b.station_id, a.opened_on, b.opened_on"
                  " FROM stations a JOIN stations b ON b.station_id > a.station_id"
                  " AND strftime('%Y', b.opened_on) = strftime('%Y', a.opened_on)"),
        note="A non-equi self-join: the ON condition is a distance, not an"
             " equality. ABS of a julianday difference is days apart in"
             " either direction; the trap's same-year test misses pairs"
             " that straddle New Year and admits none that are more than a"
             " year apart only by luck. Half the pairs go missing.",
        claims=[("twenty-odd pairs, each within a year",
                 lambda rows, c: 15 < len(rows) < 40 and all(
                     r[0] < r[1] and abs(c.execute(
                         "SELECT julianday(?) - julianday(?)", (r[3], r[2])
                     ).fetchone()[0]) <= 365 for r in rows))],
    ),
    dict(
        id=10, ledger="Q651", concept="S1", tier="3 - Unpivot and set ops",
        title="Lines that have run every model",
        prompt=(
            "Lines on which every model of rolling stock has worked at"
            " least once. Do not hard-code the number of models.\n\n"
            "Return: line_id"
        ),
        solution=("SELECT s.line_id FROM service_units su JOIN rolling_stock r"
                  " ON r.unit_id = su.unit_id JOIN services s"
                  " ON s.service_id = su.service_id GROUP BY s.line_id"
                  " HAVING COUNT(DISTINCT r.model) ="
                  " (SELECT COUNT(DISTINCT model) FROM rolling_stock)"),
        trap_sql=("SELECT s.line_id FROM service_units su JOIN rolling_stock r"
                  " ON r.unit_id = su.unit_id JOIN services s"
                  " ON s.service_id = su.service_id GROUP BY s.line_id"
                  " HAVING COUNT(r.model) >="
                  " (SELECT COUNT(DISTINCT model) FROM rolling_stock)"),
        note="Relational division, from the other side of question 10 of"
             " two sets ago: there it was models that reach every line,"
             " here lines that have seen every model. The count on the"
             " left must be of DISTINCT models -- every line has thousands"
             " of workings, so the trap's plain COUNT passes all six. Both"
             " sides of the comparison are counts, so nothing is typed in.",
        claims=[("some lines but not all",
                 lambda rows, c: 0 < len(rows) < 6)],
    ),
    # ================================================= 4 Dates and times
    dict(
        id=11, ledger="Q652", concept="C2", tier="4 - Dates and times",
        title="Incident rate by day of the week",
        prompt=(
            "For each day of the week -- strftime's number, 0 for Sunday --"
            " how many services ran, how many incidents were reported, and"
            " incidents per hundred services to one decimal.\n\n"
            "Services and incidents are counted from different tables; do"
            " not let one multiply the other.\n\n"
            "Return: weekday, services, incidents, per_100"
        ),
        solution=("WITH sv AS (SELECT strftime('%w', run_date) d, COUNT(*) n"
                  " FROM services GROUP BY 1), inc AS (SELECT"
                  " strftime('%w', reported_at) d, COUNT(*) n FROM incidents"
                  " GROUP BY 1) SELECT sv.d, sv.n, inc.n,"
                  " ROUND(100.0 * inc.n / sv.n, 1) FROM sv"
                  " JOIN inc ON inc.d = sv.d"),
        trap_sql=("SELECT strftime('%w', s.run_date), COUNT(s.service_id),"
                  " COUNT(i.incident_id), ROUND(100.0 * COUNT(i.incident_id)"
                  " / COUNT(s.service_id), 1) FROM services s"
                  " JOIN incidents i ON i.service_id = s.service_id"
                  " GROUP BY 1"),
        note="The trap's inner join keeps only services that HAD an"
             " incident, so services and incidents come out equal and the"
             " rate is 100 on every day. Two independent counts want two"
             " independent aggregations, joined on the key they share --"
             " here the weekday number. A LEFT JOIN with COUNT(i.incident_id)"
             " would also work, because there is only one child table.",
        claims=[("seven days, rates under twenty percent",
                 lambda rows, c: len(rows) == 7
                 and all(0 < r[3] < 20 for r in rows))],
    ),
    dict(
        id=12, ledger="Q653", concept="STR", tier="4 - Dates and times",
        title="Journey time as hours and minutes",
        prompt=(
            "For every service that ran on 2025-03-03, its scheduled"
            " journey -- departure to last call -- formatted as 'h:mm', so"
            " 72 minutes shows as '1:12' and 50 as '0:50'.\n\n"
            "Return: service_id, journey"
        ),
        solution=("SELECT service_id, printf('%d:%02d', m / 60, m % 60) FROM"
                  " (SELECT s.service_id, (strftime('%s', MAX(sp.sched_arrive))"
                  " - strftime('%s', s.depart_time)) / 60 m FROM services s"
                  " JOIN stops sp ON sp.service_id = s.service_id"
                  " WHERE s.run_date = '2025-03-03' GROUP BY s.service_id)"),
        trap_sql=("SELECT service_id, printf('%d:%d', m / 60, m % 60) FROM"
                  " (SELECT s.service_id, (strftime('%s', MAX(sp.sched_arrive))"
                  " - strftime('%s', s.depart_time)) / 60 m FROM services s"
                  " JOIN stops sp ON sp.service_id = s.service_id"
                  " WHERE s.run_date = '2025-03-03' GROUP BY s.service_id)"),
        note="printf (also spelled format) is the formatting tool: %d for"
             " an integer, %02d for an integer padded with zeros to two"
             " places. The trap's %d gives '1:5' for sixty-five minutes."
             " Minutes to hours and minutes is integer division and"
             " modulo; the total is computed in a subquery so the outer"
             " query can name it once and use it twice.",
        claims=[("services that ran that day, every journey h:mm",
                 lambda rows, c: len(rows) > 10 and all(
                     len(r[1].split(':')[1]) == 2 for r in rows))],
    ),
    dict(
        id=13, ledger="Q654", concept="D1", tier="4 - Dates and times",
        title="Tickets by week of 2025",
        prompt=(
            "How many tickets were sold in each week of 2025, numbered by"
            " strftime's '%W' -- week 00 is the days before the first"
            " Monday. Only 2025.\n\n"
            "Return: week, tickets"
        ),
        solution=("SELECT strftime('%W', sold_at), COUNT(*) FROM tickets"
                  " WHERE sold_at BETWEEN '2025-01-01' AND '2025-12-31'"
                  " GROUP BY 1"),
        trap_sql=("SELECT strftime('%W', sold_at), COUNT(*) FROM tickets"
                  " GROUP BY 1"),
        note="A week number without a year is ambiguous the moment the data"
             " spans two: the trap has fifty-three rows too, each one the"
             " sum of 2025's week and 2026's, and nothing about the shape"
             " says so. Either filter to the year, as here, or group by"
             " '%Y-%W'. The BETWEEN on an ISO date string is a text"
             " comparison and works because the format sorts.",
        claims=[("fifty-three weeks summing to 2025's tickets",
                 lambda rows, c: len(rows) == 53
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM tickets WHERE sold_at < '2026-01-01'"
                 ).fetchone()[0])],
    ),
    dict(
        id=14, ledger="Q655", concept="D2", tier="4 - Dates and times",
        title="Day of the year, across the boundary",
        prompt=(
            "For incidents reported between 2025-12-28 and 2026-01-04, the"
            " day of the year each fell on: 1 for the 1st of January, 365"
            " for the 31st of December. Oldest first, then incident_id.\n\n"
            "Build it from the 'start of year' modifier, not from a"
            " hard-coded date.\n\n"
            "Return: incident_id, reported_at, day_of_year"
        ),
        solution=("SELECT incident_id, reported_at, CAST(julianday(reported_at)"
                  " - julianday(reported_at, 'start of year') + 1 AS INTEGER)"
                  " FROM incidents WHERE reported_at BETWEEN '2025-12-28'"
                  " AND '2026-01-04' ORDER BY reported_at, incident_id"),
        trap_sql=("SELECT incident_id, reported_at, CAST(julianday(reported_at)"
                  " - julianday('2026-01-01') + 1 AS INTEGER)"
                  " FROM incidents WHERE reported_at BETWEEN '2025-12-28'"
                  " AND '2026-01-04' ORDER BY reported_at, incident_id"),
        note="'start of year' rewinds a date to its own 1st of January, so"
             " the subtraction is relative to the right year for every"
             " row. The trap anchors on one year and the December rows"
             " come out negative. strftime('%j') is the one-call answer"
             " and worth knowing; the modifier is what generalises to"
             " 'days since the start of the quarter' where no code"
             " exists.",
        claims=[("rows either side of New Year, days positive on both",
                 lambda rows, c: len(rows) > 4
                 and any(r[1] < '2026' for r in rows)
                 and any(r[1] >= '2026' for r in rows)
                 and all(r[2] > 0 for r in rows))],
    ),
    # ================================================= 5 Joins and grain
    dict(
        id=15, ledger="Q656", concept="J2", tier="5 - Joins and grain",
        title="Incidents while each unit was in the train",
        prompt=(
            "Every unit of rolling stock with the number of incidents that"
            " happened on services it was part of. Units with none -- and"
            " the five that have never run -- must appear with 0, so all 50"
            " rows come back.\n\n"
            "Return: unit_id, incidents"
        ),
        solution=("SELECT r.unit_id, COUNT(i.incident_id) FROM rolling_stock r"
                  " LEFT JOIN service_units su ON su.unit_id = r.unit_id"
                  " LEFT JOIN incidents i ON i.service_id = su.service_id"
                  " GROUP BY r.unit_id"),
        trap_sql=("SELECT r.unit_id, COUNT(i.incident_id) FROM rolling_stock r"
                  " LEFT JOIN service_units su ON su.unit_id = r.unit_id"
                  " JOIN incidents i ON i.service_id = su.service_id"
                  " GROUP BY r.unit_id"),
        note="A chain of outer joins is only as outer as its weakest link."
             " The trap's second join is inner, so a unit whose services"
             " had no incident produces no row, and the never-run units"
             " vanish with it: 45 rows. Every hop from the table you want"
             " to keep whole has to be LEFT. COUNT of the far table's key"
             " reads 0 on the rows the outer joins preserve.",
        claims=[("fifty units, some with none",
                 lambda rows, c: len(rows) == 50
                 and any(r[1] == 0 for r in rows)
                 and any(r[1] > 0 for r in rows))],
    ),
    dict(
        id=16, ledger="Q657", concept="C2", tier="5 - Joins and grain",
        title="Three counts per service",
        prompt=(
            "For every service scheduled on 2025-03-03: how many stops,"
            " how many units and how many tickets. Three children of one"
            " parent; a cancelled service has none of any and shows"
            " zeros.\n\n"
            "Return: service_id, stops, units, tickets"
        ),
        solution=("SELECT s.service_id, COUNT(DISTINCT sp.stop_seq),"
                  " COUNT(DISTINCT su.unit_id), COUNT(DISTINCT t.ticket_id)"
                  " FROM services s LEFT JOIN stops sp"
                  " ON sp.service_id = s.service_id LEFT JOIN service_units su"
                  " ON su.service_id = s.service_id LEFT JOIN tickets t"
                  " ON t.service_id = s.service_id"
                  " WHERE s.run_date = '2025-03-03' GROUP BY s.service_id"),
        trap_sql=("SELECT s.service_id, COUNT(sp.stop_seq),"
                  " COUNT(su.unit_id), COUNT(t.ticket_id)"
                  " FROM services s LEFT JOIN stops sp"
                  " ON sp.service_id = s.service_id LEFT JOIN service_units su"
                  " ON su.service_id = s.service_id LEFT JOIN tickets t"
                  " ON t.service_id = s.service_id"
                  " WHERE s.run_date = '2025-03-03' GROUP BY s.service_id"),
        note="Eight stops, two units and four tickets is sixty-four rows"
             " after three joins, and each plain COUNT reports 64."
             " COUNT(DISTINCT key) recovers each count because every child"
             " has its own key -- stop_seq is unique within the service."
             " This works for counts; three SUMs would need three"
             " separate aggregations. The cancelled service's zeros come"
             " from the LEFT JOINs.",
        claims=[("every service that day, a cancelled one with zeros",
                 lambda rows, c: len(rows) == c.execute(
                     "SELECT COUNT(*) FROM services WHERE run_date"
                     " = '2025-03-03'").fetchone()[0]
                 and any(r[1] == 0 and r[2] == 0 for r in rows)
                 and all(r[1] <= 10 and r[2] <= 2 for r in rows))],
    ),
    dict(
        id=17, ledger="Q658", concept="J2", tier="5 - Joins and grain",
        title="Based where no train stops",
        prompt=(
            "Staff whose base station is one that no service has ever"
            " called at.\n\n"
            "Return: staff_id, name, base_station"
        ),
        solution=("SELECT sf.staff_id, sf.name, sf.base_station FROM staff sf"
                  " WHERE NOT EXISTS (SELECT 1 FROM stops sp"
                  " WHERE sp.station_id = sf.base_station)"),
        trap_sql=("SELECT sf.staff_id, sf.name, sf.base_station FROM staff sf"
                  " WHERE NOT EXISTS (SELECT 1 FROM stops sp"
                  " WHERE sp.station_id = sf.base_station AND sp.stop_seq = 1)"),
        note="An anti-join through a foreign key: the subquery looks for"
             " ANY stop at the base station. The trap looks only for stops"
             " that START a service, and 'no service starts here' is true"
             " of most stations -- 37 staff instead of 7. When an anti-join"
             " returns more than you expected, the extra condition in the"
             " subquery is usually why: every condition there narrows what"
             " counts as a match, and so widens the non-matches.",
        claims=[("a handful of staff, none at a station with a stop",
                 lambda rows, c: 3 < len(rows) < 15 and not c.execute(
                     "SELECT 1 FROM stops WHERE station_id IN (%s) LIMIT 1"
                     % ",".join(str(int(r[2])) for r in rows)).fetchall())],
    ),
    dict(
        id=18, ledger="Q659", concept="E1", tier="5 - Joins and grain",
        title="Clean days",
        prompt=(
            "Days in January 2025 on which NO service was cancelled, with"
            " how many services ran.\n\n"
            "Return: day, services"
        ),
        solution=("SELECT run_date, COUNT(*) FROM services"
                  " WHERE run_date BETWEEN '2025-01-01' AND '2025-01-31'"
                  " GROUP BY run_date HAVING SUM(cancelled) = 0"),
        trap_sql=("SELECT run_date, COUNT(*) FROM services"
                  " WHERE run_date BETWEEN '2025-01-01' AND '2025-01-31'"
                  " AND cancelled = 0 GROUP BY run_date"),
        note="'None cancelled' is a fact about the whole day: the sum of the"
             " cancelled flags is 0. The trap filters the cancelled rows"
             " OUT and then reports every day -- each with its running"
             " services counted, which looks plausible and is the wrong"
             " list. All-or-none conditions live in HAVING; a WHERE can"
             " only ever remove rows, never ask about the rows it removed.",
        claims=[("some days but not all, none with a cancellation",
                 lambda rows, c: 5 < len(rows) < 31 and not c.execute(
                     "SELECT 1 FROM services WHERE cancelled = 1 AND run_date"
                     " IN (%s) LIMIT 1" % ",".join("'%s'" % r[0] for r in rows)
                 ).fetchall())],
    ),
    # ================================================= 6 Window functions
    dict(
        id=19, ledger="Q660", concept="W1", tier="6 - Window functions",
        title="How far through the year's takings",
        prompt=(
            "For each month of 2025: that month's ticket revenue in pence,"
            " and the percentage of the YEAR's revenue taken by the end of"
            " it, to two decimals. December reads 100.\n\n"
            "Return: month, revenue, cumulative_pct"
        ),
        solution=("SELECT m, r, ROUND(100.0 * SUM(r) OVER (ORDER BY m)"
                  " / SUM(r) OVER (), 2) FROM (SELECT strftime('%Y-%m', sold_at)"
                  " m, SUM(price_pence) r FROM tickets"
                  " WHERE sold_at < '2026-01-01' GROUP BY 1)"),
        trap_sql=("SELECT m, r, ROUND(100.0 * r / SUM(r) OVER (), 2)"
                  " FROM (SELECT strftime('%Y-%m', sold_at)"
                  " m, SUM(price_pence) r FROM tickets"
                  " WHERE sold_at < '2026-01-01' GROUP BY 1)"),
        note="Two windows in one expression: a running total over ORDER BY"
             " m on top, the grand total with no ORDER BY underneath."
             " With ORDER BY, SUM accumulates; without it, SUM is the same"
             " total on every row. The trap gives each month's own share,"
             " which sums to 100 but never reaches it. The year filter"
             " sits in the inner query so the grand total is 2025's.",
        claims=[("twelve months, climbing to 100",
                 lambda rows, c: len(rows) == 12
                 and abs(rows[-1][2] - 100) < 0.01
                 and all(rows[i][2] < rows[i+1][2] for i in range(11)))],
    ),
    dict(
        id=20, ledger="Q661", concept="W2", tier="6 - Window functions",
        title="Year on year, by month",
        prompt=(
            "Tickets sold per month, each with the count for the SAME month"
            " a year earlier and the difference. The first twelve months"
            " have no earlier year, so those two columns are NULL.\n\n"
            "Return: month, tickets, year_before, change"
        ),
        solution=("SELECT m, n, LAG(n, 12) OVER w, n - LAG(n, 12) OVER w"
                  " FROM (SELECT strftime('%Y-%m', sold_at) m, COUNT(*) n"
                  " FROM tickets GROUP BY 1) WINDOW w AS (ORDER BY m)"),
        trap_sql=("SELECT m, n, LAG(n) OVER w, n - LAG(n) OVER w"
                  " FROM (SELECT strftime('%Y-%m', sold_at) m, COUNT(*) n"
                  " FROM tickets GROUP BY 1) WINDOW w AS (ORDER BY m)"),
        note="LAG takes an offset: LAG(n, 12) is the value twelve rows back,"
             " which on a monthly series is the same month last year. The"
             " default offset is 1, and the trap reports month-on-month"
             " change under a year-on-year heading. This only works"
             " because every month is present; a missing month would shift"
             " the comparison, and a date spine would be the fix.",
        claims=[("eighteen months, the first twelve blank",
                 lambda rows, c: len(rows) == 18
                 and all(r[2] is None for r in rows[:12])
                 and all(r[2] is not None for r in rows[12:]))],
    ),
    dict(
        id=21, ledger="Q662", concept="W3", tier="6 - Window functions",
        title="Each operator's share of each line",
        prompt=(
            "For every line and operator: how many services, and what"
            " percentage of THAT LINE's services the operator ran, to two"
            " decimals. Each line's four percentages add to 100.\n\n"
            "Return: line_id, operator_id, services, pct_of_line"
        ),
        solution=("SELECT line_id, operator_id, COUNT(*), ROUND(100.0 * COUNT(*)"
                  " / SUM(COUNT(*)) OVER (PARTITION BY line_id), 2)"
                  " FROM services GROUP BY 1, 2"),
        trap_sql=("SELECT line_id, operator_id, COUNT(*), ROUND(100.0 * COUNT(*)"
                  " / SUM(COUNT(*)) OVER (PARTITION BY operator_id), 2)"
                  " FROM services GROUP BY 1, 2"),
        note="The partition names the thing the share is OF. Partitioned by"
             " operator, the trap gives each operator's spread across the"
             " six lines -- a sensible number that answers the transposed"
             " question, with each row's percentage about a sixth instead"
             " of a quarter. SUM(COUNT(*)) OVER is the grouped count added"
             " up within the partition.",
        claims=[("twenty-four rows, each line summing to 100",
                 lambda rows, c: len(rows) == 24 and all(
                     abs(sum(r[3] for r in rows if r[0] == lid) - 100) < 0.05
                     for lid in {r[0] for r in rows}))],
    ),
    dict(
        id=22, ledger="Q663", concept="W1", tier="6 - Window functions",
        title="Records set",
        prompt=(
            "For each day of January 2025: tickets sold, the highest daily"
            " count seen so far that month (today included), and 1 if today"
            " set or equalled that record, else 0.\n\n"
            "Return: day, tickets, record_so_far, is_record"
        ),
        solution=("SELECT sold_at, n, MAX(n) OVER w, n = MAX(n) OVER w"
                  " FROM (SELECT sold_at, COUNT(*) n FROM tickets"
                  " WHERE sold_at < '2025-02-01' GROUP BY 1)"
                  " WINDOW w AS (ORDER BY sold_at ROWS UNBOUNDED PRECEDING)"),
        trap_sql=("SELECT sold_at, n, MAX(n) OVER w, n = MAX(n) OVER w"
                  " FROM (SELECT sold_at, COUNT(*) n FROM tickets"
                  " WHERE sold_at < '2025-02-01' GROUP BY 1)"
                  " WINDOW w AS (ORDER BY sold_at ROWS BETWEEN UNBOUNDED"
                  " PRECEDING AND UNBOUNDED FOLLOWING)"),
        note="A running maximum: MAX over a frame from the start of the"
             " partition to the current row, which is what ORDER BY plus"
             " ROWS UNBOUNDED PRECEDING says -- the frame's end defaults to"
             " CURRENT ROW. The trap spells out a frame to UNBOUNDED"
             " FOLLOWING, which is the whole month on every row, so only"
             " the best day is ever flagged. 'So far' means the frame"
             " stops at the current row.",
        claims=[("31 days, the first a record, the record never falling",
                 lambda rows, c: len(rows) == 31 and rows[0][3] == 1
                 and all(rows[i][2] <= rows[i+1][2] for i in range(30))
                 and 1 < sum(r[3] for r in rows) < 31)],
    ),
    # ================================================ 7 Changing the data
    # Writable questions. The editor's script runs in a sandbox copy of the
    # database, then probe_sql reads the result and THAT is compared with the
    # reference. driver_sql, where present, is run by the question after the
    # script -- to fire a trigger, or to be refused by one.
    dict(
        id=23, ledger="Q664", concept="UPS", tier="7 - Changing the data",
        kind="script",
        title="Correct a row without replacing it",
        prompt=(
            "Station 7's 2024 q3 footfall was mis-keyed. Set it to 70000,"
            " leaving the other three quarters as they are -- and leaving"
            " the ROW as it is: the same physical row, corrected, not a new"
            " row in its place.\n\n"
            "INSERT OR REPLACE looks like an update and is not one.\n\n"
            "Checked: the row's rowid and its four quarters"
        ),
        solution=("UPDATE station_footfall SET q3 = 70000\n"
                  "WHERE station_id = 7 AND year = 2024;"),
        trap_sql=("INSERT OR REPLACE INTO station_footfall"
                  " (station_id, year, q1, q2, q3, q4)\n"
                  "VALUES (7, 2024, 75035, 76384, 70000, 85690);"),
        probe_sql=("SELECT rowid, q1, q2, q3, q4 FROM station_footfall"
                   " WHERE station_id = 7 AND year = 2024"),
        note="REPLACE is DELETE then INSERT. The values all come out right"
             " and the row is a different row: a new rowid, any DELETE"
             " triggers fired, any column not supplied reset to its"
             " default. That is sometimes what you want, and never what"
             " 'correct this figure' means. An UPDATE touches one column of"
             " one row; UPSERT (ON CONFLICT DO UPDATE) is the form that"
             " inserts-or-updates without replacing.",
        claims=[("the same rowid, only q3 changed",
                 lambda rows, c: rows == [(20, 75035, 76384, 70000, 85690)])],
    ),
    dict(
        id=24, ledger="Q665", concept="DML", tier="7 - Changing the data",
        kind="script",
        title="Prune the incident log",
        prompt=(
            "Keep only the three most recent incidents on each line and"
            " delete the rest. 'Most recent' is by reported_at, then by the"
            " higher incident_id.\n\n"
            "A DELETE cannot use a window function directly; number the"
            " rows in a subquery and delete what is not in the keep"
            " list.\n\n"
            "Checked: per line, how many incidents remain and the earliest"
            " date among them"
        ),
        solution=("DELETE FROM incidents\n"
                  "WHERE incident_id NOT IN (\n"
                  "  SELECT incident_id FROM (\n"
                  "    SELECT i.incident_id, ROW_NUMBER() OVER (\n"
                  "      PARTITION BY s.line_id\n"
                  "      ORDER BY i.reported_at DESC, i.incident_id DESC) AS rn\n"
                  "    FROM incidents i JOIN services s ON s.service_id = i.service_id)\n"
                  "  WHERE rn <= 3);"),
        trap_sql=("DELETE FROM incidents\n"
                  "WHERE incident_id NOT IN (\n"
                  "  SELECT incident_id FROM (\n"
                  "    SELECT i.incident_id, ROW_NUMBER() OVER (\n"
                  "      PARTITION BY s.line_id\n"
                  "      ORDER BY i.reported_at DESC, i.incident_id DESC) AS rn\n"
                  "    FROM incidents i JOIN services s ON s.service_id = i.service_id)\n"
                  "  WHERE rn < 3);"),
        probe_sql=("SELECT s.line_id, COUNT(*), MIN(i.reported_at) FROM incidents i"
                   " JOIN services s ON s.service_id = i.service_id"
                   " GROUP BY 1 ORDER BY 1"),
        note="Top-N per group, turned into a keep list for a DELETE. The"
             " window has to run in a subquery because WHERE -- a DELETE's"
             " included -- is evaluated before windows exist. NOT IN is"
             " safe: incident_id is a primary key and never NULL. The trap"
             " keeps two per line; 'rows changed' says 959 instead of 953."
             " The same shape with rn > 3 and IN deletes the same rows.",
        claims=[("three per line, eighteen in all",
                 lambda rows, c: len(rows) == 6 and all(r[1] == 3 for r in rows)
                 and c.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
                 == 18)],
    ),
    dict(
        id=25, ledger="Q666", concept="INS", tier="7 - Changing the data",
        kind="script",
        title="Three extra services",
        prompt=(
            "Add three services to the timetable in ONE INSERT: line 1,"
            " operator 2, on 2026-07-01, departing 07:15, 11:40 and"
            " 16:05. Let the table assign the ids and default the cancelled"
            " flag; name the columns you supply.\n\n"
            "Checked: line, operator, date, departure and cancelled flag for"
            " every service after the last existing id"
        ),
        solution=("INSERT INTO services (line_id, operator_id, run_date, depart_time)\n"
                  "VALUES (1, 2, '2026-07-01', '07:15'),\n"
                  "       (1, 2, '2026-07-01', '11:40'),\n"
                  "       (1, 2, '2026-07-01', '16:05');"),
        trap_sql=("INSERT INTO services (line_id, operator_id, depart_time, run_date)\n"
                  "VALUES (1, 2, '2026-07-01', '07:15'),\n"
                  "       (1, 2, '2026-07-01', '11:40'),\n"
                  "       (1, 2, '2026-07-01', '16:05');"),
        probe_sql=("SELECT line_id, operator_id, run_date, depart_time, cancelled"
                   " FROM services WHERE service_id > 11141 ORDER BY service_id"),
        note="A multi-row VALUES is one statement and one transaction, and"
             " the columns left out take their defaults: an INTEGER PRIMARY"
             " KEY becomes the next id, cancelled becomes its DEFAULT 0."
             " The trap names the columns in one order and supplies values"
             " in another, so every date lands in depart_time and every"
             " time in run_date -- both TEXT, so nothing complains. Always"
             " name the columns, and read the list twice.",
        claims=[("three rows, all on the date, none cancelled",
                 lambda rows, c: len(rows) == 3
                 and all(r[2] == '2026-07-01' and r[4] == 0 for r in rows)
                 and [r[3] for r in rows] == ['07:15', '11:40', '16:05'])],
    ),
    dict(
        id=26, ledger="Q667", concept="TXN", tier="7 - Changing the data",
        kind="script",
        title="Insert if absent, and carry on",
        prompt=(
            "In one transaction: give every guard a 3% raise, then add two"
            " stations -- 'Southwell' and 'Southwell Parkway', both in town"
            " Southwell, opened 2026-07-01, step_free 1 -- and commit."
            " 'Southwell' already exists and station names are UNIQUE: that"
            " insert must be skipped, not fail, and the transaction must"
            " still commit.\n\n"
            "Whole pounds: CAST(ROUND(salary * 1.03) AS INTEGER).\n\n"
            "Checked: the station count, the guards' total salary, and"
            " whether 'Southwell Parkway' exists"
        ),
        solution=("BEGIN;\n"
                  "UPDATE staff SET salary = CAST(ROUND(salary * 1.03) AS INTEGER)"
                  " WHERE role = 'guard';\n"
                  "INSERT OR IGNORE INTO stations (name, town, opened_on, step_free)\n"
                  "VALUES ('Southwell', 'Southwell', '2026-07-01', 1);\n"
                  "INSERT OR IGNORE INTO stations (name, town, opened_on, step_free)\n"
                  "VALUES ('Southwell Parkway', 'Southwell', '2026-07-01', 1);\n"
                  "COMMIT;"),
        trap_sql=("BEGIN;\n"
                  "UPDATE staff SET salary = CAST(ROUND(salary * 1.03) AS INTEGER)"
                  " WHERE role = 'guard';\n"
                  "INSERT OR ROLLBACK INTO stations (name, town, opened_on, step_free)\n"
                  "VALUES ('Southwell', 'Southwell', '2026-07-01', 1);\n"
                  "INSERT OR ROLLBACK INTO stations (name, town, opened_on, step_free)\n"
                  "VALUES ('Southwell Parkway', 'Southwell', '2026-07-01', 1);\n"
                  "COMMIT;"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM stations),"
                   " (SELECT SUM(salary) FROM staff WHERE role = 'guard'),"
                   " (SELECT COUNT(*) FROM stations WHERE name = 'Southwell Parkway')"),
        note="The conflict clause decides what a constraint failure does to"
             " the statement AND the transaction. OR IGNORE skips the"
             " offending row and continues; the default, OR ABORT, fails"
             " the statement but leaves the transaction open; OR ROLLBACK"
             " -- the trap -- undoes the whole transaction, raise"
             " included, and the COMMIT then has nothing to commit. OR"
             " REPLACE is the fifth, from question 23. This is the"
             " nearest SQLite comes to TRY/CATCH.",
        claims=[("one station added, guards up three percent",
                 lambda rows, c: rows == [(61, 493768, 1)])],
    ),
    dict(
        id=27, ledger="Q668", concept="TRG", tier="7 - Changing the data",
        kind="script",
        title="Cascade by hand",
        prompt=(
            "The foreign keys on `services` do not cascade, so deleting a"
            " service with stops, tickets, units or incidents fails. Write"
            " a trigger that removes a service's rows from all FOUR child"
            " tables whenever the service itself is deleted.\n\n"
            "After your script, the question deletes service 1, which has"
            " 8 stops, 4 tickets and 2 units.\n\n"
            "Checked: whether service 1 still exists, and how many stops,"
            " tickets and units still name it"
        ),
        solution=("CREATE TRIGGER cascade_service\n"
                  "BEFORE DELETE ON services\n"
                  "BEGIN\n"
                  "  DELETE FROM stops WHERE service_id = OLD.service_id;\n"
                  "  DELETE FROM tickets WHERE service_id = OLD.service_id;\n"
                  "  DELETE FROM service_units WHERE service_id = OLD.service_id;\n"
                  "  DELETE FROM incidents WHERE service_id = OLD.service_id;\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER cascade_service\n"
                  "BEFORE DELETE ON services\n"
                  "BEGIN\n"
                  "  DELETE FROM stops WHERE service_id = OLD.service_id;\n"
                  "  DELETE FROM tickets WHERE service_id = OLD.service_id;\n"
                  "  DELETE FROM incidents WHERE service_id = OLD.service_id;\n"
                  "END;"),
        driver_sql="DELETE FROM services WHERE service_id = 1;",
        probe_sql=("SELECT (SELECT COUNT(*) FROM services WHERE service_id = 1),"
                   " (SELECT COUNT(*) FROM stops WHERE service_id = 1),"
                   " (SELECT COUNT(*) FROM tickets WHERE service_id = 1),"
                   " (SELECT COUNT(*) FROM service_units WHERE service_id = 1)"),
        note="A trigger body may hold several statements, and a BEFORE"
             " DELETE trigger runs them before the parent row goes. The"
             " trap forgets service_units; the two unit rows are still"
             " pointing at service 1 when the statement ends, the foreign"
             " key check fails, and the whole delete -- trigger work"
             " included -- is rolled back, so nothing changes. SQLite"
             " checks foreign keys at the END of the statement, which is"
             " why an AFTER DELETE trigger would have worked here too."
             " ON DELETE CASCADE in the schema is the declarative version.",
        claims=[("service 1 and all its children gone",
                 lambda rows, c: rows == [(0, 0, 0, 0)])],
    ),
    dict(
        id=28, ledger="Q669", concept="TRG", tier="7 - Changing the data",
        kind="script",
        title="Fill in the blank on the way in",
        prompt=(
            "A ticket inserted with no destination should be given one: the"
            " last stop of its service. Write a trigger that fills"
            " to_station after such an insert -- and leaves alone any"
            " ticket that arrived with a destination.\n\n"
            "After your script, the question inserts two tickets on service"
            " 1 from station 49: one with to_station NULL, one with"
            " to_station 35.\n\n"
            "Checked: the destination of every ticket after the last"
            " existing id"
        ),
        solution=("CREATE TRIGGER default_destination\n"
                  "AFTER INSERT ON tickets\n"
                  "WHEN NEW.to_station IS NULL\n"
                  "BEGIN\n"
                  "  UPDATE tickets\n"
                  "  SET to_station = (SELECT station_id FROM stops\n"
                  "                    WHERE service_id = NEW.service_id\n"
                  "                    ORDER BY stop_seq DESC LIMIT 1)\n"
                  "  WHERE ticket_id = NEW.ticket_id;\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER default_destination\n"
                  "AFTER INSERT ON tickets\n"
                  "BEGIN\n"
                  "  UPDATE tickets\n"
                  "  SET to_station = (SELECT station_id FROM stops\n"
                  "                    WHERE service_id = NEW.service_id\n"
                  "                    ORDER BY stop_seq DESC LIMIT 1)\n"
                  "  WHERE ticket_id = NEW.ticket_id;\n"
                  "END;"),
        driver_sql=("INSERT INTO tickets (service_id, from_station, to_station,"
                    " class, price_pence, sold_at)"
                    " VALUES (1, 49, NULL, 'standard', 1000, '2025-01-01');\n"
                    "INSERT INTO tickets (service_id, from_station, to_station,"
                    " class, price_pence, sold_at)"
                    " VALUES (1, 49, 35, 'standard', 1000, '2025-01-01');"),
        probe_sql=("SELECT ticket_id, to_station FROM tickets"
                   " WHERE ticket_id > 34548 ORDER BY 1"),
        note="SQLite cannot change NEW inside a BEFORE trigger, as other"
             " databases can; the idiom is an AFTER INSERT trigger that"
             " updates the row just written, found by NEW.ticket_id -- the"
             " id the table assigned. The WHEN clause is the whole"
             " difference: without it the trap overwrites the destination"
             " a ticket came in with. An UPDATE inside an INSERT trigger"
             " does not re-fire it, because it is a different event.",
        claims=[("two tickets: the blank one filled, the other kept",
                 lambda rows, c: [r[1] for r in rows] == [46, 35])],
    ),
    dict(
        id=29, ledger="Q670", concept="VIEW", tier="7 - Changing the data",
        kind="script",
        title="A view over a view",
        prompt=(
            "Create `line_daily (line_id, run_date, services)` -- services"
            " per line per day -- and then `line_monthly (line_id, month,"
            " services)` built ON TOP OF line_daily, summing its rows by"
            " '%Y-%m'.\n\n"
            "Eighteen rows per line in the monthly view: January 2025 and"
            " January 2026 are different months.\n\n"
            "Checked: line 1's rows of line_monthly, in month order"
        ),
        solution=("CREATE VIEW line_daily AS\n"
                  "SELECT line_id, run_date, COUNT(*) AS services\n"
                  "FROM services GROUP BY line_id, run_date;\n"
                  "CREATE VIEW line_monthly AS\n"
                  "SELECT line_id, strftime('%Y-%m', run_date) AS month,"
                  " SUM(services) AS services\n"
                  "FROM line_daily GROUP BY line_id, month;"),
        trap_sql=("CREATE VIEW line_daily AS\n"
                  "SELECT line_id, run_date, COUNT(*) AS services\n"
                  "FROM services GROUP BY line_id, run_date;\n"
                  "CREATE VIEW line_monthly AS\n"
                  "SELECT line_id, strftime('%m', run_date) AS month,"
                  " SUM(services) AS services\n"
                  "FROM line_daily GROUP BY line_id, month;"),
        probe_sql=("SELECT month, services FROM line_monthly WHERE line_id = 1"
                   " ORDER BY month"),
        note="Views stack: the monthly view reads the daily one as if it"
             " were a table, and SQLite inlines both at query time. The"
             " second level must SUM the first's counts, not COUNT its rows"
             " -- COUNT(*) over line_daily would give days per month. The"
             " trap's '%m' folds the two Januaries together, twelve rows"
             " for eighteen, the same slip as question 11 of the last set,"
             " now frozen into a view for everyone who uses it.",
        claims=[("eighteen months for line 1, summing to its services",
                 lambda rows, c: len(rows) == 18
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM services WHERE line_id = 1"
                 ).fetchone()[0])],
    ),
    dict(
        id=30, ledger="Q671", concept="X3", tier="7 - Changing the data",
        kind="script",
        title="An index the lookup can use",
        prompt=(
            "Staff are looked up by base station -- `WHERE base_station ="
            " ?` -- and there is no index for it. Create one that lets that"
            " lookup SEARCH instead of SCAN. Name it as you like.\n\n"
            "An index helps a lookup only if the looked-up column is its"
            " FIRST column.\n\n"
            "Checked: whether any index on staff has base_station as its"
            " leading column, and how many staff are based at station 14"
        ),
        solution="CREATE INDEX idx_staff_base ON staff(base_station);",
        trap_sql="CREATE INDEX idx_staff_role_base ON staff(role, base_station);",
        probe_sql=("SELECT (SELECT COUNT(*) FROM pragma_index_list('staff') il"
                   " WHERE EXISTS (SELECT 1 FROM pragma_index_info(il.name) ii"
                   " WHERE ii.name = 'base_station' AND ii.seqno = 0)),"
                   " (SELECT COUNT(*) FROM staff WHERE base_station = 14)"),
        note="A B-tree index is sorted by its first column, then its second"
             " within that. The trap's (role, base_station) index is"
             " ordered by role, so finding a base_station means reading"
             " all of it -- EXPLAIN QUERY PLAN still says SCAN. The probe"
             " reads the schema through pragma_index_list and"
             " pragma_index_info, which is how you check what an index"
             " actually covers. This is the efficiency stage's lesson"
             " from the other end: writing the index instead of reading"
             " the plan.",
        claims=[("an index leads with base_station",
                 lambda rows, c: rows[0][0] == 1)],
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
