"""Practice exercises: twenty questions on the hospital schema.

The second set on the district hospital, alongside the first twenty Python
questions (pyexercises.py). Same data as the previous set -- SEED 731, not
re-seeded -- and fifteen SELECT questions that repeat none of it: a
NULL-aware average, a conditional count, two aggregates in HAVING, a name
split with instr(), consecutive ward stays paired up, weekdays, ages,
occupancy as a percentage of beds, a point inside an interval, an interval
tested on a calendar of instants, wards per patient, an anti-join, a NULL
in a comparison, a top-1 per group, and the biggest gap in a time series.
The last five are WRITABLE questions, graded on the state of the database
after your script runs, on constructs none of the six earlier writable
stages used --

  * a keyed summary table, against CREATE TABLE ... AS SELECT
  * a composite foreign key
  * an index on an expression
  * a BEFORE INSERT trigger that checks another table
  * RAISE(ROLLBACK), against RAISE(ABORT)

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script -- the inserts your table, trigger or
key should refuse or let through.
"""

import sqlite3

EXERCISES = [
    # ========================================================== 1 Warm-up
    dict(
        id=1, ledger="Q732", concept="A2", tier="1 - Warm-up",
        title="Procedures by category",
        prompt=(
            "One row per category of procedure: how many have been"
            " performed, the revenue in POUNDS to two decimals (tariffs are"
            " in pence), and the average duration in minutes to one"
            " decimal -- over the procedures whose duration was recorded.\n\n"
            "Return: category, procedures, revenue_pounds, avg_minutes"
        ),
        solution=("SELECT t.category, COUNT(*), ROUND(SUM(t.tariff_pence) / 100.0, 2),"
                  " ROUND(AVG(p.duration_minutes), 1) FROM procedures p"
                  " JOIN procedure_types t ON t.code = p.code GROUP BY t.category"),
        trap_sql=("SELECT t.category, COUNT(*), ROUND(SUM(t.tariff_pence) / 100.0, 2),"
                  " ROUND(AVG(COALESCE(p.duration_minutes, 0)), 1) FROM procedures p"
                  " JOIN procedure_types t ON t.code = p.code GROUP BY t.category"),
        note="AVG ignores NULLs, which here is what you want: a duration"
             " nobody recorded is unknown, not zero. The trap turns each"
             " NULL into 0 and drags every average down. COUNT(*) still"
             " counts every procedure -- the two aggregates in one row"
             " have different denominators, and that is fine.",
        claims=[("three categories, averages in the low hundreds",
                 lambda rows, c: len(rows) == 3
                 and all(100 < r[3] < 200 for r in rows))],
    ),
    dict(
        id=2, ledger="Q733", concept="C5", tier="1 - Warm-up",
        title="Controlled, by form",
        prompt=(
            "One row per form of drug -- tablet, injection, infusion,"
            " inhaler: how many drugs come in that form, how many of them"
            " are controlled, and the percentage that are, to one"
            " decimal. `controlled` is 0 or 1.\n\n"
            "Return: form, drugs, controlled, pct"
        ),
        solution=("SELECT form, COUNT(*), SUM(controlled),"
                  " ROUND(100.0 * SUM(controlled) / COUNT(*), 1) FROM drugs"
                  " GROUP BY form"),
        trap_sql=("SELECT form, COUNT(*), COUNT(controlled),"
                  " ROUND(100.0 * COUNT(controlled) / COUNT(*), 1) FROM drugs"
                  " GROUP BY form"),
        note="COUNT(column) counts rows where the column is not NULL, and a"
             " 0 is not NULL -- so COUNT(controlled) counts every drug."
             " SUM of a 0/1 column counts the ones, which is the idiom for"
             " 'how many rows satisfy this'. SUM(CASE WHEN ... THEN 1 ELSE"
             " 0 END) is the same idea for any condition.",
        claims=[("four forms, two with no controlled drug",
                 lambda rows, c: len(rows) == 4
                 and sum(r[2] == 0 for r in rows) == 2)],
    ),
    dict(
        id=3, ledger="Q734", concept="A3", tier="1 - Warm-up",
        title="Night owls",
        prompt=(
            "Staff who have worked at least 300 shifts, of which at least"
            " 40 per cent were nights: staff_id, their shifts, their"
            " nights, and the percentage to one decimal.\n\n"
            "Both conditions are about totals, so both belong in HAVING.\n\n"
            "Return: staff_id, shifts, nights, pct_night"
        ),
        solution=("SELECT staff_id, COUNT(*), SUM(kind = 'night'),"
                  " ROUND(100.0 * SUM(kind = 'night') / COUNT(*), 1) FROM shifts"
                  " GROUP BY staff_id HAVING COUNT(*) >= 300"
                  " AND 100.0 * SUM(kind = 'night') / COUNT(*) >= 40"),
        trap_sql=("SELECT staff_id, COUNT(*), COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / COUNT(*), 1) FROM shifts"
                  " WHERE kind = 'night'"
                  " GROUP BY staff_id HAVING COUNT(*) >= 120"),
        note="WHERE filters rows before they are grouped; HAVING filters"
             " groups after. Filter the nights in WHERE and there is"
             " nothing left to divide by -- every percentage is 100 and"
             " the shift count is the night count. A condition on"
             " COUNT(*) or on a ratio of aggregates can only live in"
             " HAVING.",
        claims=[("a handful of staff, none over half nights",
                 lambda rows, c: 2 <= len(rows) <= 15
                 and all(40 <= r[3] < 50 and r[1] >= 300 for r in rows))],
    ),
    # ======================================== 2 Strings and sequences
    dict(
        id=4, ledger="Q735", concept="STR", tier="2 - Strings and sequences",
        title="Surname first",
        prompt=(
            "Patients 1 to 10 with their name turned round, 'Surname,"
            " Forename' -- 'Marcus Lindqvist' becomes 'Lindqvist, Marcus'."
            " Every name is two words separated by one space; instr()"
            " finds the space and substr() takes either side of it.\n\n"
            "Return: patient_id, sorted_name"
        ),
        solution=("SELECT patient_id, substr(name, instr(name, ' ') + 1) || ', '"
                  " || substr(name, 1, instr(name, ' ') - 1) FROM patients"
                  " WHERE patient_id <= 10"),
        trap_sql=("SELECT patient_id, substr(name, instr(name, ' ')) || ', '"
                  " || substr(name, 1, instr(name, ' ')) FROM patients"
                  " WHERE patient_id <= 10"),
        note="instr() returns the 1-based position of the space, and"
             " substr() is 1-based too: the forename is characters 1 to"
             " position - 1, the surname starts at position + 1. Off by one"
             " either way and the space comes along -- ' Lindqvist, Marcus '."
             " There is no split function; this pair is how SQLite splits.",
        claims=[("ten rows, each 'Surname, Forename' with no stray spaces",
                 lambda rows, c: len(rows) == 10 and all(
                     ", " in r[1] and r[1] == r[1].strip()
                     and "  " not in r[1] for r in rows))],
    ),
    dict(
        id=5, ledger="Q736", concept="J1", tier="2 - Strings and sequences",
        title="Where transfers go",
        prompt=(
            "Every move between wards: for each pair of wards, how many"
            " times a patient went straight from the first to the second."
            " A move is two CONSECUTIVE stays of one admission --"
            " stay_seq and stay_seq + 1.\n\n"
            "Return: from_ward, to_ward, transfers"
        ),
        solution=("SELECT a.ward_id, b.ward_id, COUNT(*) FROM ward_stays a"
                  " JOIN ward_stays b ON b.admission_id = a.admission_id"
                  " AND b.stay_seq = a.stay_seq + 1 GROUP BY 1, 2"),
        trap_sql=("SELECT a.ward_id, b.ward_id, COUNT(*) FROM ward_stays a"
                  " JOIN ward_stays b ON b.admission_id = a.admission_id"
                  " AND b.stay_seq > a.stay_seq GROUP BY 1, 2"),
        note="A self-join on the next sequence number pairs each stay with"
             " the one that followed it. stay_seq > a.stay_seq pairs it with"
             " EVERY later stay, so an admission that went 8 -> 3 -> 5 also"
             " counts as a move from 8 to 5. LAG would do this too, with"
             " the previous ward brought onto each row instead of a join.",
        claims=[("dozens of pairs, never a ward to itself",
                 lambda rows, c: len(rows) > 40
                 and all(r[0] != r[1] for r in rows)
                 and sum(r[2] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM ward_stays WHERE stay_seq > 1"
                 ).fetchone()[0])],
    ),
    # ============================================== 3 Dates and times
    dict(
        id=6, ledger="Q737", concept="D1", tier="3 - Dates and times",
        title="Admissions by weekday",
        prompt=(
            "How many admissions arrived on each day of the week, with the"
            " percentage of all admissions to one decimal. strftime('%w')"
            " gives the weekday as a digit, 0 for Sunday through 6 for"
            " Saturday; return the digit as an integer and the English"
            " name.\n\n"
            "Return: day_num, day_name, admissions, pct"
        ),
        solution=("SELECT CAST(strftime('%w', admitted_at) AS INTEGER),"
                  " CASE strftime('%w', admitted_at) WHEN '0' THEN 'Sunday'"
                  " WHEN '1' THEN 'Monday' WHEN '2' THEN 'Tuesday'"
                  " WHEN '3' THEN 'Wednesday' WHEN '4' THEN 'Thursday'"
                  " WHEN '5' THEN 'Friday' ELSE 'Saturday' END, COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM admissions), 1)"
                  " FROM admissions GROUP BY 1"),
        trap_sql=("SELECT CAST(strftime('%w', admitted_at) AS INTEGER),"
                  " CASE strftime('%w', admitted_at) WHEN '1' THEN 'Sunday'"
                  " WHEN '2' THEN 'Monday' WHEN '3' THEN 'Tuesday'"
                  " WHEN '4' THEN 'Wednesday' WHEN '5' THEN 'Thursday'"
                  " WHEN '6' THEN 'Friday' ELSE 'Saturday' END, COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM admissions), 1)"
                  " FROM admissions GROUP BY 1"),
        note="%w counts from Sunday = 0, the C convention, not from Monday"
             " = 1. strftime returns TEXT, so the CASE compares against"
             " '0' and the CAST turns it into a number for the first"
             " column. The share divides by a scalar subquery over the whole"
             " table; a window SUM(COUNT(*)) OVER () is the other way.",
        claims=[("seven days, shares adding to 100",
                 lambda rows, c: len(rows) == 7
                 and abs(sum(r[3] for r in rows) - 100) < 0.5
                 and {r[0] for r in rows} == set(range(7)))],
    ),
    dict(
        id=7, ledger="Q738", concept="D1", tier="3 - Dates and times",
        title="Age at admission",
        prompt=(
            "Admissions by the patient's age on the day they were admitted:"
            " 'under 18', '18-64' and '65 and over', with the count and"
            " the percentage of all admissions to one decimal. Age in"
            " years is the difference in julianday() divided by 365.25,"
            " rounded down.\n\n"
            "Return: band, admissions, pct"
        ),
        solution=("SELECT CASE WHEN age < 18 THEN 'under 18' WHEN age < 65"
                  " THEN '18-64' ELSE '65 and over' END, COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM admissions), 1)"
                  " FROM (SELECT CAST((julianday(a.admitted_at) - julianday(p.born_on))"
                  " / 365.25 AS INTEGER) age FROM admissions a"
                  " JOIN patients p ON p.patient_id = a.patient_id) GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN age < 18 THEN 'under 18' WHEN age < 65"
                  " THEN '18-64' ELSE '65 and over' END, COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM admissions), 1)"
                  " FROM (SELECT CAST(strftime('%Y', a.admitted_at) AS INTEGER)"
                  " - CAST(strftime('%Y', p.born_on) AS INTEGER) age FROM admissions a"
                  " JOIN patients p ON p.patient_id = a.patient_id) GROUP BY 1"),
        note="Subtracting the years says someone born in December 2008 was"
             " 18 in January 2026, a month before their birthday. The"
             " julianday difference counts real days, and CAST AS INTEGER"
             " truncates, which for a positive number is rounding down."
             " The subquery computes the age once so the CASE reads it by"
             " name instead of repeating the expression three times.",
        claims=[("three bands, adults the majority",
                 lambda rows, c: len(rows) == 3
                 and max(rows, key=lambda r: r[1])[0] == '18-64'
                 and abs(sum(r[2] for r in rows) - 100) < 0.5)],
    ),
    # ==================================== 4 Intervals and occupancy
    dict(
        id=8, ledger="Q739", concept="INT", tier="4 - Intervals and occupancy",
        title="Beds in use, March 2026",
        prompt=(
            "For each ward, the percentage of its bed-days used in March"
            " 2026, to one decimal: the days of ward_stays that fell"
            " INSIDE the month, added up, over beds times 31. A stay that"
            " began in February or ran into April counts only for its"
            " March part -- clip each stay to the month with MAX() and"
            " MIN() before subtracting. An open stay runs to"
            " 2026-06-30 23:59.\n\n"
            "Return: ward_id, beds, pct_used"
        ),
        solution=("SELECT w.ward_id, w.beds, ROUND(100.0 * SUM("
                  " julianday(MIN(COALESCE(s.to_at, '2026-06-30 23:59'), '2026-04-01'))"
                  " - julianday(MAX(s.from_at, '2026-03-01'))) / (w.beds * 31), 1)"
                  " FROM wards w JOIN ward_stays s ON s.ward_id = w.ward_id"
                  " AND s.from_at < '2026-04-01'"
                  " AND COALESCE(s.to_at, '2026-06-30 23:59') > '2026-03-01'"
                  " GROUP BY w.ward_id"),
        trap_sql=("SELECT w.ward_id, w.beds, ROUND(100.0 * SUM("
                  " julianday(COALESCE(s.to_at, '2026-06-30 23:59'))"
                  " - julianday(s.from_at)) / (w.beds * 31), 1)"
                  " FROM wards w JOIN ward_stays s ON s.ward_id = w.ward_id"
                  " AND s.from_at < '2026-04-01'"
                  " AND COALESCE(s.to_at, '2026-06-30 23:59') > '2026-03-01'"
                  " GROUP BY w.ward_id"),
        note="Clipping an interval to a window is MAX of the starts and MIN"
             " of the ends -- SQLite's two-argument MAX and MIN are scalar"
             " functions, not aggregates, when given more than one"
             " argument. The trap keeps the stays that touch March but"
             " counts their whole length, so a stay from February to April"
             " contributes sixty days to a thirty-one day month.",
        claims=[("eight wards, all between a tenth and half full",
                 lambda rows, c: len(rows) == 8
                 and all(10 < r[2] < 50 for r in rows))],
    ),
    dict(
        id=9, ledger="Q740", concept="INT", tier="4 - Intervals and occupancy",
        title="Where the patient was",
        prompt=(
            "How many procedures were performed while the patient was on"
            " each ward -- not the ward they were admitted to, but the"
            " ward_stay whose interval contains performed_at. A stay with"
            " no end is still running.\n\n"
            "Return: ward_id, procedures"
        ),
        solution=("SELECT s.ward_id, COUNT(*) FROM procedures p JOIN ward_stays s"
                  " ON s.admission_id = p.admission_id AND p.performed_at >= s.from_at"
                  " AND p.performed_at < COALESCE(s.to_at, '9999') GROUP BY s.ward_id"),
        trap_sql=("SELECT a.ward_id, COUNT(*) FROM procedures p JOIN admissions a"
                  " ON a.admission_id = p.admission_id GROUP BY a.ward_id"),
        note="A point inside an interval: start <= point < end, with the"
             " open end supplied. The join condition does the placing, and"
             " because stays of one admission never overlap each"
             " procedure lands on exactly one of them, so COUNT(*) is"
             " safe. The admitting ward is where the patient STARTED, and"
             " a third of admissions moved on.",
        claims=[("eight wards, every procedure placed exactly once",
                 lambda rows, c: len(rows) == 8
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM procedures").fetchone()[0])],
    ),
    dict(
        id=10, ledger="Q741", concept="INT", tier="4 - Intervals and occupancy",
        title="Fleming at eight, all week",
        prompt=(
            "For each day from 2026-06-24 to 2026-06-30, how many patients"
            " were on ward 5 at 08:00 that morning. Build the seven days"
            " with a recursive CTE, then join ward_stays on the interval"
            " containing that instant -- the day plus ' 08:00'. Stays with"
            " no end are still running.\n\n"
            "Return: day, patients"
        ),
        solution=("WITH RECURSIVE d(day) AS (SELECT '2026-06-24' UNION ALL"
                  " SELECT date(day, '+1 day') FROM d WHERE day < '2026-06-30')"
                  " SELECT d.day, COUNT(s.admission_id) FROM d LEFT JOIN ward_stays s"
                  " ON s.ward_id = 5 AND s.from_at <= d.day || ' 08:00'"
                  " AND COALESCE(s.to_at, '9999') > d.day || ' 08:00' GROUP BY d.day"),
        trap_sql=("WITH RECURSIVE d(day) AS (SELECT '2026-06-24' UNION ALL"
                  " SELECT date(day, '+1 day') FROM d WHERE day < '2026-06-30')"
                  " SELECT d.day, COUNT(s.admission_id) FROM d LEFT JOIN ward_stays s"
                  " ON s.ward_id = 5 AND s.from_at <= d.day"
                  " AND COALESCE(s.to_at, '9999') > d.day GROUP BY d.day"),
        note="A calendar is a recursive CTE with a stop condition; each"
             " row then asks the same interval question at its own"
             " instant. '2026-06-24' alone compares as a string SHORTER"
             " than any datetime on that day, so it means midnight, and"
             " the trap counts the ward at 00:00 -- appending ' 08:00'"
             " moves the instant. The LEFT JOIN keeps a day with nobody on"
             " the ward as a 0.",
        claims=[("seven days, a handful of patients each",
                 lambda rows, c: len(rows) == 7
                 and all(0 < r[1] < 16 for r in rows))],
    ),
    # ============================================== 5 Joins and grain
    dict(
        id=11, ledger="Q742", concept="C2", tier="5 - Joins and grain",
        title="Well travelled",
        prompt=(
            "Patients who have been on SIX or more different wards over"
            " all their admissions, with the number of wards. A patient"
            " who was on a ward twice has been on it once.\n\n"
            "Return: patient_id, wards"
        ),
        solution=("SELECT a.patient_id, COUNT(DISTINCT s.ward_id) FROM admissions a"
                  " JOIN ward_stays s ON s.admission_id = a.admission_id"
                  " GROUP BY a.patient_id HAVING COUNT(DISTINCT s.ward_id) >= 6"),
        trap_sql=("SELECT a.patient_id, COUNT(s.ward_id) FROM admissions a"
                  " JOIN ward_stays s ON s.admission_id = a.admission_id"
                  " GROUP BY a.patient_id HAVING COUNT(s.ward_id) >= 6"),
        note="Two hops -- patient to admissions to stays -- and then the"
             " question is about DISTINCT wards, not stays. COUNT(DISTINCT"
             " ward_id) counts each ward once however many times the"
             " patient passed through it; COUNT(ward_id) counts stays and"
             " admits anyone with six stays on two wards.",
        claims=[("a couple of hundred patients, each on six to eight wards",
                 lambda rows, c: 100 < len(rows) < 400
                 and all(6 <= r[1] <= 8 for r in rows))],
    ),
    dict(
        id=12, ledger="Q743", concept="E1", tier="5 - Joins and grain",
        title="Never in theatre six",
        prompt=(
            "Procedure types that have never been performed in theatre 6,"
            " with their name. A type never performed anywhere qualifies"
            " too.\n\n"
            "Return: code, name"
        ),
        solution=("SELECT t.code, t.name FROM procedure_types t WHERE NOT EXISTS"
                  " (SELECT 1 FROM procedures p WHERE p.code = t.code"
                  " AND p.theatre = 6)"),
        trap_sql=("SELECT DISTINCT t.code, t.name FROM procedure_types t"
                  " JOIN procedures p ON p.code = t.code WHERE p.theatre <> 6"),
        note="'Never in theatre 6' is a statement about ALL of a type's"
             " procedures, and `theatre <> 6` is a statement about one row"
             " -- it finds types that have been performed somewhere else,"
             " which is every type in use. NOT EXISTS (or NOT IN, or a"
             " LEFT JOIN ... IS NULL) is how a row is kept for having no"
             " match, and it keeps the three types never performed at all.",
        claims=[("three types, none of them ever performed",
                 lambda rows, c: len(rows) == 3
                 and all(c.execute("SELECT COUNT(*) FROM procedures WHERE code = ?",
                                   (r[0],)).fetchone()[0] == 0 for r in rows))],
    ),
    dict(
        id=13, ledger="Q744", concept="C7", tier="5 - Joins and grain",
        title="Away from home",
        prompt=(
            "For each role that HAS a home ward -- consultants, doctors,"
            " nurses; pharmacists and porters have NULL -- how many shifts"
            " its staff have worked, how many were on a ward other than"
            " their own, and the percentage to one decimal.\n\n"
            "Return: role, shifts, away, pct_away"
        ),
        solution=("SELECT st.role, COUNT(*), SUM(sh.ward_id <> st.ward_id),"
                  " ROUND(100.0 * SUM(sh.ward_id <> st.ward_id) / COUNT(*), 1)"
                  " FROM shifts sh JOIN staff st ON st.staff_id = sh.staff_id"
                  " WHERE st.ward_id IS NOT NULL GROUP BY st.role"),
        trap_sql=("SELECT st.role, COUNT(*), SUM(sh.ward_id <> st.ward_id),"
                  " ROUND(100.0 * SUM(sh.ward_id <> st.ward_id) / COUNT(*), 1)"
                  " FROM shifts sh JOIN staff st ON st.staff_id = sh.staff_id"
                  " GROUP BY st.role"),
        note="NULL <> 5 is not true and not false but NULL, and SUM skips"
             " it -- so the trap returns five rows, two of them with a NULL"
             " away count and a NULL percentage, and the question only"
             " asked for three. Filter the rows whose comparison can be"
             " answered, or decide explicitly what a missing home ward"
             " means. A NULL never silently becomes a 0.",
        claims=[("three roles, a tenth or so of shifts away",
                 lambda rows, c: len(rows) == 3
                 and all(5 < r[3] < 15 for r in rows))],
    ),
    # ============================================== 6 Window functions
    dict(
        id=14, ledger="Q745", concept="W2", tier="6 - Window functions",
        title="The peak reading",
        prompt=(
            "For admissions 31 to 40: the highest heart rate recorded, and"
            " how many hours after admission it was taken, to one decimal."
            " If the peak was reached more than once, the EARLIEST"
            " time.\n\n"
            "Return: admission_id, peak_hr, hours_in"
        ),
        solution=("SELECT admission_id, heart_rate, hours_in FROM (SELECT o.admission_id,"
                  " o.heart_rate, ROUND(24 * (julianday(o.taken_at)"
                  " - julianday(a.admitted_at)), 1) hours_in, ROW_NUMBER() OVER"
                  " (PARTITION BY o.admission_id ORDER BY o.heart_rate DESC,"
                  " o.taken_at) rn FROM observations o JOIN admissions a"
                  " ON a.admission_id = o.admission_id"
                  " WHERE o.admission_id BETWEEN 31 AND 40) WHERE rn = 1"),
        trap_sql=("SELECT admission_id, heart_rate, hours_in FROM (SELECT o.admission_id,"
                  " o.heart_rate, ROUND(24 * (julianday(o.taken_at)"
                  " - julianday(a.admitted_at)), 1) hours_in, ROW_NUMBER() OVER"
                  " (PARTITION BY o.admission_id ORDER BY o.heart_rate DESC,"
                  " o.taken_at DESC) rn FROM observations o JOIN admissions a"
                  " ON a.admission_id = o.admission_id"
                  " WHERE o.admission_id BETWEEN 31 AND 40) WHERE rn = 1"),
        note="Top-1 per group: ROW_NUMBER over a partition, ordered by the"
             " thing you want the top of, then filtered to 1 in an outer"
             " query. The second ORDER BY key is the tiebreak, and it is"
             " part of the question -- the trap takes the LATEST of a tied"
             " peak. SQLite's bare-column MAX() would find the peak too,"
             " but which tied row it picks is not something you can order.",
        claims=[("ten rows, peaks over 80, and at least one tie broken",
                 lambda rows, c: len(rows) == 10
                 and all(r[1] > 80 for r in rows)
                 and c.execute(
                     "SELECT COUNT(*) FROM (SELECT admission_id FROM observations o"
                     " WHERE admission_id BETWEEN 31 AND 40 AND heart_rate = (SELECT MAX(heart_rate)"
                     " FROM observations WHERE admission_id = o.admission_id)"
                     " GROUP BY 1 HAVING COUNT(*) > 1)").fetchone()[0] >= 1)],
    ),
    dict(
        id=15, ledger="Q746", concept="C3", tier="6 - Window functions",
        title="Gaps in the readings",
        prompt=(
            "For admissions 1 to 10: the longest gap between two"
            " consecutive observations, in hours to one decimal. LAG"
            " brings the previous reading's time onto each row; the"
            " partition matters.\n\n"
            "Return: admission_id, longest_gap_hours"
        ),
        solution=("SELECT admission_id, ROUND(24 * MAX(gap), 1) FROM (SELECT"
                  " admission_id, julianday(taken_at) - LAG(julianday(taken_at)) OVER"
                  " (PARTITION BY admission_id ORDER BY taken_at) gap"
                  " FROM observations WHERE admission_id <= 10) GROUP BY admission_id"),
        trap_sql=("SELECT admission_id, ROUND(24 * MAX(gap), 1) FROM (SELECT"
                  " admission_id, julianday(taken_at) - LAG(julianday(taken_at)) OVER"
                  " (ORDER BY admission_id, taken_at) gap"
                  " FROM observations WHERE admission_id <= 10) GROUP BY admission_id"),
        note="Without PARTITION BY, the first reading of admission 2 looks"
             " back at the last reading of admission 1 -- weeks away -- and"
             " that becomes its longest gap. A partition restarts the"
             " window, so LAG returns NULL on the first row of each"
             " admission and MAX ignores it. The aggregate over a window"
             " result needs the subquery: window functions run after"
             " GROUP BY, not inside it.",
        claims=[("ten rows, every gap under a day",
                 lambda rows, c: len(rows) == 10
                 and all(4 < r[1] < 24 for r in rows))],
    ),
    # ============================================= 7 Changing the data
    dict(
        id=16, ledger="Q747", concept="DDL", tier="7 - Changing the data",
        kind="script",
        title="A summary with a key",
        prompt=(
            "Build `ward_load (ward_id INTEGER PRIMARY KEY, admissions"
            " INTEGER NOT NULL)` holding each ward's number of admissions"
            " as the admitting ward -- eight rows -- so that the table has"
            " a real PRIMARY KEY. CREATE TABLE ... AS SELECT will not give"
            " you one. After your script, the question tries to insert a"
            " second row for ward 1.\n\n"
            "Checked: how many columns are the key, the row count, and the"
            " sum of admissions"
        ),
        solution=("CREATE TABLE ward_load (\n"
                  "  ward_id    INTEGER PRIMARY KEY,\n"
                  "  admissions INTEGER NOT NULL\n"
                  ");\n"
                  "INSERT INTO ward_load (ward_id, admissions)\n"
                  "SELECT ward_id, COUNT(*) FROM admissions GROUP BY ward_id;"),
        trap_sql=("CREATE TABLE ward_load AS\n"
                  "SELECT ward_id, COUNT(*) AS admissions FROM admissions"
                  " GROUP BY ward_id;"),
        driver_sql="INSERT INTO ward_load (ward_id, admissions) VALUES (1, 0);",
        probe_sql=("SELECT (SELECT COUNT(*) FROM pragma_table_info('ward_load')"
                   " WHERE pk = 1), (SELECT COUNT(*) FROM ward_load),"
                   " (SELECT SUM(admissions) FROM ward_load)"),
        note="CREATE TABLE ... AS SELECT copies the rows and guesses the"
             " types, and that is all: no primary key, no NOT NULL, no"
             " default. So the duplicate ward 1 goes in and the table has"
             " nine rows. Declare the table, then INSERT ... SELECT into"
             " it; the key refuses the duplicate and the count stays at"
             " eight. CTAS is for a quick scratch copy, not for a table"
             " you keep.",
        claims=[("one key column, eight rows, every admission counted once",
                 lambda rows, c: rows[0][0] == 1 and rows[0][1] == 8
                 and rows[0][2] == c.execute(
                     "SELECT COUNT(*) FROM admissions").fetchone()[0])],
    ),
    dict(
        id=17, ledger="Q748", concept="DDL", tier="7 - Changing the data",
        kind="script",
        title="A note on one stay",
        prompt=(
            "Create `stay_notes (note_id INTEGER PRIMARY KEY, admission_id"
            " INTEGER NOT NULL, stay_seq INTEGER NOT NULL, note TEXT NOT"
            " NULL)` where the PAIR (admission_id, stay_seq) must match a"
            " row of ward_stays -- a foreign key on two columns at once."
            " After your script, the question inserts a note for stay"
            " (1, 1), one for (1, 9), and one for (999999, 1).\n\n"
            "Checked: which (admission_id, stay_seq) pairs the notes hold"
        ),
        solution=("CREATE TABLE stay_notes (\n"
                  "  note_id      INTEGER PRIMARY KEY,\n"
                  "  admission_id INTEGER NOT NULL,\n"
                  "  stay_seq     INTEGER NOT NULL,\n"
                  "  note         TEXT    NOT NULL,\n"
                  "  FOREIGN KEY (admission_id, stay_seq)\n"
                  "    REFERENCES ward_stays (admission_id, stay_seq)\n"
                  ");"),
        trap_sql=("CREATE TABLE stay_notes (\n"
                  "  note_id      INTEGER PRIMARY KEY,\n"
                  "  admission_id INTEGER NOT NULL REFERENCES admissions(admission_id),\n"
                  "  stay_seq     INTEGER NOT NULL,\n"
                  "  note         TEXT    NOT NULL\n"
                  ");"),
        driver_sql=("INSERT INTO stay_notes (admission_id, stay_seq, note)"
                    " VALUES (1, 1, 'settled');\n"
                    "INSERT INTO stay_notes (admission_id, stay_seq, note)"
                    " VALUES (1, 9, 'no such stay');\n"
                    "INSERT INTO stay_notes (admission_id, stay_seq, note)"
                    " VALUES (999999, 1, 'no such admission');"),
        probe_sql="SELECT admission_id, stay_seq FROM stay_notes ORDER BY note_id",
        note="A foreign key can name several columns, and then the"
             " combination must exist in the parent -- which needs the"
             " parent to have a PRIMARY KEY or UNIQUE on exactly those"
             " columns, as ward_stays does. A key on admission_id alone"
             " checks half the pair: (1, 9) has a real admission and an"
             " imaginary stay, and the trap accepts it. The table-level"
             " FOREIGN KEY (...) REFERENCES ... form is the only way to"
             " write a composite one.",
        claims=[("only the real stay's note survives",
                 lambda rows, c: rows == [(1, 1)])],
    ),
    dict(
        id=18, ledger="Q749", concept="IDX", tier="7 - Changing the data",
        kind="script",
        title="An index on an expression",
        prompt=(
            "The query `SELECT COUNT(*) FROM admissions WHERE"
            " date(admitted_at) = '2026-03-01'` scans the whole table:"
            " the index on admitted_at cannot serve a condition on"
            " date(admitted_at). Create an index named `idx_adm_day` that"
            " CAN -- an index on the expression itself.\n\n"
            "Checked: the query plan of that SELECT"
        ),
        solution="CREATE INDEX idx_adm_day ON admissions (date(admitted_at));",
        trap_sql="CREATE INDEX idx_adm_day ON admissions (admitted_at);",
        probe_sql=("EXPLAIN QUERY PLAN SELECT COUNT(*) FROM admissions"
                   " WHERE date(admitted_at) = '2026-03-01'"),
        note="An index stores the values of whatever it is declared on,"
             " and the planner uses it only when the WHERE compares that"
             " same thing. date(admitted_at) is not admitted_at, so a"
             " second index on the plain column changes nothing -- the plan"
             " still says SCAN. Declared on the expression, the plan says"
             " SEARCH ... USING INDEX idx_adm_day. The expression in the"
             " query has to match the one in the index exactly.",
        claims=[("the plan searches the new index",
                 lambda rows, c: len(rows) == 1
                 and "SEARCH" in rows[0][3] and "idx_adm_day" in rows[0][3])],
    ),
    dict(
        id=19, ledger="Q750", concept="TRG", tier="7 - Changing the data",
        kind="script",
        title="No prescribing after discharge",
        prompt=(
            "Write a BEFORE INSERT trigger on prescriptions that refuses a"
            " prescription whose started_on is after the day its admission"
            " was discharged -- RAISE(ABORT, ...) -- and lets any other"
            " through, including one for an admission still open. The"
            " check needs to read admissions. After your script, the"
            " question inserts one for admission 2 starting 2026-03-01, one"
            " for admission 173 starting 2026-06-20, and one for admission"
            " 1 starting 2026-04-01.\n\n"
            "Checked: the admission and start date of each new prescription"
        ),
        solution=("CREATE TRIGGER rx_after_discharge BEFORE INSERT ON prescriptions\n"
                  "WHEN EXISTS (SELECT 1 FROM admissions\n"
                  "             WHERE admission_id = NEW.admission_id\n"
                  "               AND discharged_at IS NOT NULL\n"
                  "               AND date(discharged_at) < NEW.started_on)\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'admission already discharged');\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER rx_after_discharge BEFORE INSERT ON prescriptions\n"
                  "WHEN NEW.started_on > '2026-06-30'\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'admission already discharged');\n"
                  "END;"),
        driver_sql=("INSERT INTO prescriptions (admission_id, drug_id, prescribed_by,"
                    " started_on, dose_mg, times_per_day) VALUES (2, 1, 5,"
                    " '2026-03-01', 10, 2);\n"
                    "INSERT INTO prescriptions (admission_id, drug_id, prescribed_by,"
                    " started_on, dose_mg, times_per_day) VALUES (173, 1, 5,"
                    " '2026-06-20', 10, 2);\n"
                    "INSERT INTO prescriptions (admission_id, drug_id, prescribed_by,"
                    " started_on, dose_mg, times_per_day) VALUES (1, 1, 5,"
                    " '2026-04-01', 10, 2);"),
        probe_sql=("SELECT admission_id, started_on FROM prescriptions"
                   " WHERE prescription_id > 12389 ORDER BY prescription_id"),
        note="A trigger's WHEN clause can run a subquery, so a rule that"
             " spans two tables -- this row against its parent -- is a"
             " trigger, where a CHECK constraint can only see the row"
             " itself. NEW is the row about to be inserted. The open"
             " admission has a NULL discharge, and the IS NOT NULL keeps"
             " the comparison from going three-valued on it. Admission 1"
             " was discharged on 2026-04-02, so a course starting the day"
             " before is allowed.",
        claims=[("the discharged admission's prescription is refused, two land",
                 lambda rows, c: rows == [(173, '2026-06-20'), (1, '2026-04-01')])],
    ),
    dict(
        id=20, ledger="Q751", concept="TXN", tier="7 - Changing the data",
        kind="script",
        title="Undo everything, not just this row",
        prompt=(
            "Write a BEFORE INSERT trigger on prescriptions that refuses a"
            " dose over 10000 mg with RAISE(ROLLBACK, ...) -- not ABORT."
            " After your script, the question runs, as separate"
            " statements: BEGIN; an insert of 100 mg with id 20001; an"
            " insert of 20000 mg with id 20002; an insert of 100 mg with"
            " id 20003; COMMIT.\n\n"
            "Checked: which of the three ids exist afterwards"
        ),
        solution=("CREATE TRIGGER rx_dose_cap BEFORE INSERT ON prescriptions\n"
                  "WHEN NEW.dose_mg > 10000\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ROLLBACK, 'dose over 10000 mg');\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER rx_dose_cap BEFORE INSERT ON prescriptions\n"
                  "WHEN NEW.dose_mg > 10000\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'dose over 10000 mg');\n"
                  "END;"),
        driver_sql=("BEGIN;\n"
                    "INSERT INTO prescriptions (prescription_id, admission_id, drug_id,"
                    " prescribed_by, started_on, dose_mg, times_per_day)"
                    " VALUES (20001, 1, 1, 5, '2026-04-01', 100, 2);\n"
                    "INSERT INTO prescriptions (prescription_id, admission_id, drug_id,"
                    " prescribed_by, started_on, dose_mg, times_per_day)"
                    " VALUES (20002, 1, 1, 5, '2026-04-01', 20000, 2);\n"
                    "INSERT INTO prescriptions (prescription_id, admission_id, drug_id,"
                    " prescribed_by, started_on, dose_mg, times_per_day)"
                    " VALUES (20003, 1, 1, 5, '2026-04-01', 100, 2);\n"
                    "COMMIT;"),
        probe_sql=("SELECT prescription_id FROM prescriptions"
                   " WHERE prescription_id > 20000 ORDER BY 1"),
        note="ABORT undoes the statement that fired the trigger and leaves"
             " the transaction open, so 20001 and 20003 both survive."
             " ROLLBACK undoes the whole transaction -- 20001 goes too --"
             " and ENDS it, so the next insert runs on its own and commits"
             " itself, and the final COMMIT fails for having no transaction"
             " to commit. Use ROLLBACK when one bad row means the batch is"
             " untrustworthy; ABORT when the rest can stand.",
        claims=[("only the insert after the rollback survives",
                 lambda rows, c: rows == [(20003,)])],
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
