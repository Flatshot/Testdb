"""Practice exercises: thirty questions on the hospital schema.

A new schema -- a district hospital, after the college, the workshop and the
railway -- chosen for a shape none of those had: intervals. Sixteen of the
twenty-two SELECT questions are familiar shapes against the new tables; six
are on ground the railway could not offer -- open intervals, occupancy at an
instant, overlapping intervals, readmission within a window, a running
occupancy from events, and a join on two intervals overlapping. The last
eight are WRITABLE questions, graded on the state of the database after your
script runs, on constructs none of the five earlier writable stages used --

  * WITH RECURSIVE in front of an UPDATE
  * AUTOINCREMENT, against the id reuse of a plain INTEGER PRIMARY KEY
  * ON DELETE CASCADE declared in the table
  * a DEFERRABLE INITIALLY DEFERRED foreign key, checked at COMMIT
  * RAISE(FAIL) against RAISE(ABORT)
  * INSTEAD OF DELETE on a view: a soft delete
  * a partial UNIQUE index
  * CREATE TEMP TABLE and the temp schema

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script -- the inserts and deletes your
table, trigger, view or index should refuse, cascade, soften or let through.
"""

import sqlite3

EXERCISES = [
    # ========================================================== 1 Warm-up
    dict(
        id=1, ledger="Q702", concept="A2", tier="1 - Warm-up",
        title="Beds and admissions per ward",
        prompt=(
            "One row per ward: its name, how many beds it has, how many"
            " admissions it has taken (as the admitting ward), and"
            " admissions per bed to one decimal.\n\n"
            "Return: ward, beds, admissions, per_bed"
        ),
        solution=("SELECT w.name, w.beds, COUNT(a.admission_id),"
                  " ROUND(1.0 * COUNT(a.admission_id) / w.beds, 1) FROM wards w"
                  " LEFT JOIN admissions a ON a.ward_id = w.ward_id"
                  " GROUP BY w.ward_id"),
        trap_sql=("SELECT w.name, w.beds, COUNT(a.admission_id),"
                  " ROUND(COUNT(a.admission_id) / w.beds, 1) FROM wards w"
                  " LEFT JOIN admissions a ON a.ward_id = w.ward_id"
                  " GROUP BY w.ward_id"),
        note="A new schema, the same first lesson: two INTEGERs divide to"
             " an INTEGER, and ROUND cannot put back what the division"
             " threw away -- 736 / 30 is 24, not 24.5. One REAL anywhere in"
             " the expression makes it real. The LEFT JOIN is habit here;"
             " every ward has admissions, but the day one does not is the"
             " day COUNT(*) would have said 1.",
        claims=[("eight wards, per-bed figures with a fractional part",
                 lambda rows, c: len(rows) == 8
                 and any(r[3] != int(r[3]) for r in rows))],
    ),
    dict(
        id=2, ledger="Q703", concept="A2", tier="1 - Warm-up",
        title="How patients arrive",
        prompt=(
            "One row per route of admission -- emergency, referral,"
            " transfer -- with how many admissions came that way and what"
            " percentage of all admissions that is, to two decimals.\n\n"
            "Return: admitted_via, admissions, pct"
        ),
        solution=("SELECT admitted_via, COUNT(*), ROUND(100.0 * COUNT(*)"
                  " / (SELECT COUNT(*) FROM admissions), 2) FROM admissions"
                  " GROUP BY 1"),
        trap_sql=("SELECT admitted_via, COUNT(*), ROUND(100 * COUNT(*)"
                  " / (SELECT COUNT(*) FROM admissions), 2) FROM admissions"
                  " GROUP BY 1"),
        note="100 * 3303 / 6000 is integer division to 55, and ROUND(55, 2)"
             " is 55. Write 100.0. The uncorrelated subquery is evaluated"
             " once for the statement, not once per group; SUM(COUNT(*))"
             " OVER () would give the same total without a second pass.",
        claims=[("three routes summing to 100 percent",
                 lambda rows, c: len(rows) == 3
                 and abs(sum(r[2] for r in rows) - 100) < 0.05)],
    ),
    dict(
        id=3, ledger="Q704", concept="A3", tier="1 - Warm-up",
        title="Busy consultants with long stays",
        prompt=(
            "Consultants with at least 600 completed admissions whose"
            " patients' average length of stay is over 3.2 days, with"
            " both figures -- the average to two decimals.\n\n"
            "Length of stay is discharged_at minus admitted_at; julianday()"
            " of each gives days. Only discharged admissions count.\n\n"
            "Return: consultant_id, admissions, avg_days"
        ),
        solution=("SELECT consultant_id, COUNT(*), ROUND(AVG(julianday(discharged_at)"
                  " - julianday(admitted_at)), 2) FROM admissions"
                  " WHERE discharged_at IS NOT NULL GROUP BY consultant_id"
                  " HAVING COUNT(*) >= 600 AND AVG(julianday(discharged_at)"
                  " - julianday(admitted_at)) > 3.2"),
        trap_sql=("SELECT consultant_id, COUNT(*), ROUND(AVG(julianday(discharged_at)"
                  " - julianday(admitted_at)), 2) FROM admissions"
                  " WHERE discharged_at IS NOT NULL AND julianday(discharged_at)"
                  " - julianday(admitted_at) > 3.2 GROUP BY consultant_id"
                  " HAVING COUNT(*) >= 600"),
        note="julianday() turns a date or datetime string into a day count"
             " with a fraction, so subtracting two gives days including"
             " the hours. The trap filters to LONG stays before counting,"
             " so no consultant reaches 600 and the average is of long"
             " stays only. A condition on the group's average is HAVING;"
             " the WHERE is for the rows -- here, the ones with an end.",
        claims=[("at least one consultant, each meeting both conditions",
                 lambda rows, c: len(rows) > 0
                 and all(r[1] >= 600 and r[2] > 3.2 for r in rows))],
    ),
    # ========================================== 2 Sequences and strings
    dict(
        id=4, ledger="Q705", concept="W3", tier="2 - Sequences and strings",
        title="One admission's moves",
        prompt=(
            "Admission 12 moved ward twice. For each of its stays: the"
            " ward, how many hours it lasted to one decimal, and the ward"
            " the patient came FROM -- NULL for the first stay.\n\n"
            "ward_stays is keyed on (admission_id, stay_seq).\n\n"
            "Return: stay_seq, ward_id, hours, from_ward"
        ),
        solution=("SELECT stay_seq, ward_id, ROUND((julianday(to_at)"
                  " - julianday(from_at)) * 24, 1), LAG(ward_id) OVER"
                  " (ORDER BY stay_seq) FROM ward_stays WHERE admission_id = 12"),
        trap_sql=("SELECT stay_seq, ward_id, ROUND((julianday(to_at)"
                  " - julianday(from_at)) * 24, 1), LEAD(ward_id) OVER"
                  " (ORDER BY stay_seq) FROM ward_stays WHERE admission_id = 12"),
        note="The sequence inside a parent again -- stops were to a"
             " service what stays are to an admission -- and LAG along it"
             " is 'where were they before'. LEAD is 'where do they go"
             " next', with the NULL on the last row instead of the first."
             " julianday differences are in days; times 24 for hours.",
        claims=[("three stays, the first from nowhere, hours positive",
                 lambda rows, c: len(rows) == 3 and rows[0][3] is None
                 and all(r[2] > 0 for r in rows))],
    ),
    dict(
        id=5, ledger="Q706", concept="STR", tier="2 - Sequences and strings",
        title="Initials",
        prompt=(
            "Patients 1 to 10 with their initials as 'A.B.' -- first"
            " letter of each name, each followed by a full stop. Every"
            " name is two words.\n\n"
            "Return: patient_id, initials"
        ),
        solution=("SELECT patient_id, SUBSTR(name, 1, 1) || '.'"
                  " || SUBSTR(name, INSTR(name, ' ') + 1, 1) || '.' FROM patients"
                  " WHERE patient_id <= 10"),
        trap_sql=("SELECT patient_id, SUBSTR(name, 1, 1) || '.'"
                  " || SUBSTR(name, INSTR(name, ' '), 1) || '.' FROM patients"
                  " WHERE patient_id <= 10"),
        note="INSTR finds the space; the surname starts one character"
             " after it. The trap takes the character AT the space and"
             " produces 'A. .' -- the count is right, the strings are"
             " wrong, and only the grader notices. SUBSTR(x, pos, 1) is a"
             " single character; || joins the pieces.",
        claims=[("ten sets of initials, four characters, no spaces",
                 lambda rows, c: len(rows) == 10 and all(
                     len(r[1]) == 4 and ' ' not in r[1] for r in rows))],
    ),
    dict(
        id=6, ledger="Q707", concept="S1", tier="2 - Sequences and strings",
        title="Only ever an emergency",
        prompt=(
            "Patients who have been admitted as an emergency and have"
            " NEVER been admitted any other way.\n\n"
            "Return: patient_id"
        ),
        solution=("SELECT patient_id FROM admissions WHERE admitted_via = 'emergency'"
                  " EXCEPT SELECT patient_id FROM admissions"
                  " WHERE admitted_via <> 'emergency'"),
        trap_sql=("SELECT DISTINCT patient_id FROM admissions"
                  " WHERE admitted_via = 'emergency' AND admitted_via <> 'referral'"),
        note="'Never any other way' is about a patient's whole history,"
             " which is a set of patients to take away: EXCEPT. The trap"
             " tests one ROW at a time, and an emergency row is trivially"
             " not a referral, so it returns every emergency patient --"
             " four times too many. NOT EXISTS with a correlated subquery"
             " says the same thing per row and is the other right answer.",
        claims=[("hundreds of patients, none with a non-emergency admission",
                 lambda rows, c: 100 < len(rows) < 1000 and not c.execute(
                     "SELECT 1 FROM admissions WHERE admitted_via <> 'emergency'"
                     " AND patient_id IN (%s) LIMIT 1"
                     % ",".join(str(int(r[0])) for r in rows)).fetchall())],
    ),
    dict(
        id=7, ledger="Q708", concept="W1", tier="2 - Sequences and strings",
        title="First and last readings",
        prompt=(
            "For admissions 1 to 5, the heart rate at the first observation"
            " and at the last -- one row per admission, no NULLs.\n\n"
            "FIRST_VALUE and LAST_VALUE; mind the frame on the second.\n\n"
            "Return: admission_id, first_hr, last_hr"
        ),
        solution=("SELECT DISTINCT admission_id, FIRST_VALUE(heart_rate) OVER w,"
                  " LAST_VALUE(heart_rate) OVER (PARTITION BY admission_id"
                  " ORDER BY taken_at ROWS BETWEEN UNBOUNDED PRECEDING AND"
                  " UNBOUNDED FOLLOWING) FROM observations WHERE admission_id <= 5"
                  " WINDOW w AS (PARTITION BY admission_id ORDER BY taken_at)"),
        trap_sql=("SELECT DISTINCT admission_id, FIRST_VALUE(heart_rate) OVER w,"
                  " LAST_VALUE(heart_rate) OVER w FROM observations"
                  " WHERE admission_id <= 5"
                  " WINDOW w AS (PARTITION BY admission_id ORDER BY taken_at)"),
        note="With ORDER BY and no frame, a window ends at the CURRENT row,"
             " so LAST_VALUE is just the current row's value and DISTINCT"
             " keeps one row per reading -- 36 rows for five admissions."
             " FIRST_VALUE is unharmed because the frame always starts at"
             " the top. Widen the frame to the whole partition for the"
             " last. MIN and MAX of taken_at with a self-join is the older"
             " way.",
        claims=[("five admissions, one row each",
                 lambda rows, c: len(rows) == 5
                 and len({r[0] for r in rows}) == 5)],
    ),
    # ================================================= 3 Dates and times
    dict(
        id=8, ledger="Q709", concept="D1", tier="3 - Dates and times",
        title="Admissions by month",
        prompt=(
            "For each month, by date of admission: how many admissions,"
            " and the average completed length of stay in days to one"
            " decimal. Eighteen months -- January 2025 and January 2026"
            " are different months. Still-open admissions count as"
            " admissions but not in the average.\n\n"
            "Return: month, admissions, avg_days"
        ),
        solution=("SELECT strftime('%Y-%m', admitted_at), COUNT(*),"
                  " ROUND(AVG(julianday(discharged_at) - julianday(admitted_at)), 1)"
                  " FROM admissions GROUP BY 1"),
        trap_sql=("SELECT strftime('%m', admitted_at), COUNT(*),"
                  " ROUND(AVG(julianday(discharged_at) - julianday(admitted_at)), 1)"
                  " FROM admissions GROUP BY 1"),
        note="strftime reads a 'YYYY-MM-DD HH:MM' string as happily as a"
             " date. '%m' alone folds the two Januaries together -- twelve"
             " rows for eighteen -- so group by '%Y-%m'. AVG skips NULLs,"
             " and julianday(NULL) is NULL, so the open admissions leave"
             " the average alone without being told to.",
        claims=[("eighteen months, stays averaging a few days",
                 lambda rows, c: len(rows) == 18
                 and all(1 < r[2] < 6 for r in rows))],
    ),
    dict(
        id=9, ledger="Q710", concept="D1", tier="3 - Dates and times",
        title="Admitted in the night",
        prompt=(
            "For each route of admission: how many admissions, how many of"
            " them arrived between 22:00 and 06:00, and the percentage to"
            " one decimal.\n\n"
            "The time is the tail of admitted_at, from character 12. The"
            " night wraps past midnight.\n\n"
            "Return: admitted_via, admissions, at_night, pct"
        ),
        solution=("SELECT admitted_via, COUNT(*), SUM(SUBSTR(admitted_at, 12) >= '22:00'"
                  " OR SUBSTR(admitted_at, 12) < '06:00'), ROUND(100.0"
                  " * SUM(SUBSTR(admitted_at, 12) >= '22:00'"
                  " OR SUBSTR(admitted_at, 12) < '06:00') / COUNT(*), 1)"
                  " FROM admissions GROUP BY 1"),
        trap_sql=("SELECT admitted_via, COUNT(*), SUM(SUBSTR(admitted_at, 12)"
                  " BETWEEN '22:00' AND '06:00'), ROUND(100.0"
                  " * SUM(SUBSTR(admitted_at, 12) BETWEEN '22:00' AND '06:00')"
                  " / COUNT(*), 1) FROM admissions GROUP BY 1"),
        note="A range that crosses midnight is two ranges: at or after"
             " 22:00, OR before 06:00. BETWEEN '22:00' AND '06:00' asks for"
             " a time that is both later than 22:00 and earlier than"
             " 06:00, which is nothing, so the trap counts zero at night."
             " 'HH:MM' compares correctly as text because it is"
             " zero-padded; strftime('%H') and CAST work too.",
        claims=[("three routes, a third of each at night",
                 lambda rows, c: len(rows) == 3
                 and all(20 < r[3] < 50 for r in rows))],
    ),
    dict(
        id=10, ledger="Q711", concept="INT", tier="3 - Dates and times",
        title="Length of stay so far",
        prompt=(
            "For admissions in June 2026, per ward: how many, how many are"
            " still in, and the average length of stay in days to two"
            " decimals AS OF the end of the data, 2026-06-30 23:59 -- so"
            " a patient still in has been in from admission until then.\n\n"
            "Open intervals: an end that is NULL means 'not yet'.\n\n"
            "Return: ward_id, admissions, still_in, avg_days"
        ),
        solution=("SELECT ward_id, COUNT(*), SUM(discharged_at IS NULL),"
                  " ROUND(AVG(julianday(COALESCE(discharged_at, '2026-06-30 23:59'))"
                  " - julianday(admitted_at)), 2) FROM admissions"
                  " WHERE admitted_at >= '2026-06-01' GROUP BY 1"),
        trap_sql=("SELECT ward_id, COUNT(*), SUM(discharged_at IS NULL),"
                  " ROUND(AVG(julianday(discharged_at) - julianday(admitted_at)), 2)"
                  " FROM admissions WHERE admitted_at >= '2026-06-01' GROUP BY 1"),
        note="An open interval has a start and no end. To measure it you"
             " supply the end -- the snapshot -- with COALESCE, and every"
             " current patient counts for the time they HAVE been in. The"
             " trap lets AVG skip them, which quietly drops the longest"
             " stays of the month, because the ones still in are the ones"
             " that have gone on longest. The same COALESCE is the key to"
             " questions 11 and 12.",
        claims=[("eight wards, some patients still in",
                 lambda rows, c: len(rows) == 8
                 and sum(r[2] for r in rows) > 10)],
    ),
    # ========================================= 4 Intervals and occupancy
    dict(
        id=11, ledger="Q712", concept="INT", tier="4 - Intervals and occupancy",
        title="Who was where at eight o'clock",
        prompt=(
            "How many patients were on each ward at 2026-06-30 08:00,"
            " from ward_stays: a stay covers that instant if it began at"
            " or before it and had not ended -- and a stay with no end"
            " had not ended.\n\n"
            "Return: ward_id, patients"
        ),
        solution=("SELECT ward_id, COUNT(*) FROM ward_stays"
                  " WHERE from_at <= '2026-06-30 08:00'"
                  " AND (to_at IS NULL OR to_at > '2026-06-30 08:00') GROUP BY 1"),
        trap_sql=("SELECT ward_id, COUNT(*) FROM ward_stays"
                  " WHERE from_at <= '2026-06-30 08:00'"
                  " AND to_at > '2026-06-30 08:00' GROUP BY 1"),
        note="Point-in-time occupancy: start <= T and end > T. The NULL"
             " ends are the patients still there, and NULL > T is not"
             " true, so the trap silently loses every one of them -- most"
             " of the ward, this close to the end of the data. Either the"
             " IS NULL clause or a COALESCE to the snapshot; both say 'no"
             " end yet means still here'.",
        claims=[("eight wards, matching the open stays and the closed ones spanning it",
                 lambda rows, c: len(rows) == 8
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM ward_stays WHERE from_at <= '2026-06-30 08:00'"
                     " AND COALESCE(to_at, '9999') > '2026-06-30 08:00'"
                 ).fetchone()[0])],
    ),
    dict(
        id=12, ledger="Q713", concept="INT", tier="4 - Intervals and occupancy",
        title="Admitted twice at once",
        prompt=(
            "Pairs of admissions of the SAME patient whose intervals"
            " overlap -- a data-quality check. Each pair once, the lower"
            " admission_id first. An open admission runs to the snapshot,"
            " 2026-06-30 23:59.\n\n"
            "Two intervals overlap when each starts before the other"
            " ends.\n\n"
            "Return: admission_a, admission_b, patient_id"
        ),
        solution=("SELECT a.admission_id, b.admission_id, a.patient_id"
                  " FROM admissions a JOIN admissions b ON b.patient_id = a.patient_id"
                  " AND b.admission_id > a.admission_id"
                  " AND a.admitted_at < COALESCE(b.discharged_at, '2026-06-30 23:59')"
                  " AND b.admitted_at < COALESCE(a.discharged_at, '2026-06-30 23:59')"),
        trap_sql=("SELECT a.admission_id, b.admission_id, a.patient_id"
                  " FROM admissions a JOIN admissions b ON b.patient_id = a.patient_id"
                  " AND b.admission_id > a.admission_id"
                  " AND b.admitted_at BETWEEN a.admitted_at"
                  " AND COALESCE(a.discharged_at, '2026-06-30 23:59')"),
        note="The overlap test is symmetric: A starts before B ends AND B"
             " starts before A ends. The trap asks only whether B started"
             " during A, and admission ids are not in time order, so when"
             " the higher id was admitted first the pair is missed -- half"
             " of them. Two datetimes in the same format compare as text;"
             " no julianday needed until you subtract.",
        claims=[("more than a hundred pairs, each genuinely overlapping",
                 lambda rows, c: len(rows) > 100 and all(
                     r[0] < r[1] and c.execute(
                         "SELECT a.admitted_at < COALESCE(b.discharged_at, '9999')"
                         " AND b.admitted_at < COALESCE(a.discharged_at, '9999')"
                         " FROM admissions a, admissions b WHERE a.admission_id = ?"
                         " AND b.admission_id = ?", (r[0], r[1])).fetchone()[0]
                     for r in rows))],
    ),
    dict(
        id=13, ledger="Q714", concept="INT", tier="4 - Intervals and occupancy",
        title="Back within thirty days",
        prompt=(
            "For each route of admission: how many admissions, how many of"
            " them were READMISSIONS -- the same patient had been discharged"
            " within the previous 30 days -- and the percentage to one"
            " decimal.\n\n"
            "Measure from the previous DISCHARGE, not the previous"
            " admission.\n\n"
            "Return: admitted_via, admissions, readmissions, pct"
        ),
        solution=("SELECT a.admitted_via, COUNT(*), SUM(EXISTS (SELECT 1"
                  " FROM admissions p WHERE p.patient_id = a.patient_id"
                  " AND p.discharged_at <= a.admitted_at"
                  " AND julianday(a.admitted_at) - julianday(p.discharged_at) <= 30)),"
                  " ROUND(100.0 * SUM(EXISTS (SELECT 1 FROM admissions p"
                  " WHERE p.patient_id = a.patient_id"
                  " AND p.discharged_at <= a.admitted_at"
                  " AND julianday(a.admitted_at) - julianday(p.discharged_at) <= 30))"
                  " / COUNT(*), 1) FROM admissions a GROUP BY 1"),
        trap_sql=("SELECT a.admitted_via, COUNT(*), SUM(EXISTS (SELECT 1"
                  " FROM admissions p WHERE p.patient_id = a.patient_id"
                  " AND p.admitted_at < a.admitted_at"
                  " AND julianday(a.admitted_at) - julianday(p.admitted_at) <= 30)),"
                  " ROUND(100.0 * SUM(EXISTS (SELECT 1 FROM admissions p"
                  " WHERE p.patient_id = a.patient_id"
                  " AND p.admitted_at < a.admitted_at"
                  " AND julianday(a.admitted_at) - julianday(p.admitted_at) <= 30))"
                  " / COUNT(*), 1) FROM admissions a GROUP BY 1"),
        note="EXISTS inside SUM: the subquery is 1 or 0 per admission, so"
             " the SUM counts the admissions that have such a predecessor."
             " The trap measures from the previous admission's START, which"
             " over-counts by the length of that stay -- a patient admitted"
             " for three weeks and back a fortnight later is a readmission"
             " by the first rule and not the second. NULL discharge dates"
             " fail the <= and are rightly ignored.",
        claims=[("three routes, a fifth to a third readmitted",
                 lambda rows, c: len(rows) == 3
                 and all(15 < r[3] < 35 for r in rows))],
    ),
    dict(
        id=14, ledger="Q715", concept="INT", tier="4 - Intervals and occupancy",
        title="Nightingale, day by day",
        prompt=(
            "For each day in January 2025 on which someone arrived on or"
            " left ward 1: the net change that day -- arrivals minus"
            " departures, by ward_stays -- and how many patients were on"
            " the ward at the end of it. The ward was empty on"
            " 2025-01-01.\n\n"
            "Turn every stay into a +1 event and a -1 event, then run a"
            " total over the days.\n\n"
            "Return: day, net, occupancy"
        ),
        solution=("WITH ev AS (SELECT date(from_at) d, 1 delta FROM ward_stays"
                  " WHERE ward_id = 1 UNION ALL SELECT date(to_at), -1"
                  " FROM ward_stays WHERE ward_id = 1 AND to_at IS NOT NULL),"
                  " daily AS (SELECT d, SUM(delta) net FROM ev GROUP BY d)"
                  " SELECT d, net, SUM(net) OVER (ORDER BY d) FROM daily"
                  " WHERE d < '2025-02-01'"),
        trap_sql=("SELECT d, n, SUM(n) OVER (ORDER BY d) FROM (SELECT date(from_at) d,"
                  " COUNT(*) n FROM ward_stays WHERE ward_id = 1 GROUP BY 1)"
                  " WHERE d < '2025-02-01'"),
        note="A running balance from events: each interval becomes two"
             " rows, +1 at its start and -1 at its end, UNION ALL puts them"
             " in one column, and a window running total over the dates"
             " is the occupancy. The trap counts arrivals only, so the"
             " ward fills forever. The filter to January sits OUTSIDE the"
             " running total, which must start from the empty ward; here"
             " the data starts on the 1st, so the two coincide.",
        claims=[("occupancy never negative, and some days are net departures",
                 lambda rows, c: len(rows) > 15
                 and all(r[2] >= 0 for r in rows)
                 and any(r[1] < 0 for r in rows)
                 and rows[0][1] == rows[0][2])],
    ),
    # ================================================= 5 Joins and grain
    dict(
        id=15, ledger="Q716", concept="C2", tier="5 - Joins and grain",
        title="Procedures and prescriptions, per ward",
        prompt=(
            "For each ward, by admitting ward: how many procedures and how"
            " many prescriptions its admissions have had.\n\n"
            "Both hang off `admissions`. Joining both at once multiplies"
            " each by the other.\n\n"
            "Return: ward_id, procedures, prescriptions"
        ),
        solution=("WITH pr AS (SELECT a.ward_id, COUNT(*) n FROM procedures p"
                  " JOIN admissions a ON a.admission_id = p.admission_id GROUP BY 1),"
                  " rx AS (SELECT a.ward_id, COUNT(*) n FROM prescriptions p"
                  " JOIN admissions a ON a.admission_id = p.admission_id GROUP BY 1)"
                  " SELECT w.ward_id, pr.n, rx.n FROM wards w"
                  " JOIN pr ON pr.ward_id = w.ward_id JOIN rx ON rx.ward_id = w.ward_id"),
        trap_sql=("SELECT a.ward_id, COUNT(p.procedure_id), COUNT(r.prescription_id)"
                  " FROM admissions a JOIN procedures p ON p.admission_id = a.admission_id"
                  " JOIN prescriptions r ON r.admission_id = a.admission_id GROUP BY 1"),
        note="An admission with 2 procedures and 3 prescriptions is 6 rows"
             " once both are joined, and both counts read 6. Worse, an"
             " admission with prescriptions but no procedure vanishes from"
             " the inner join altogether. Aggregate each child to the ward"
             " on its own and join the two small results. COUNT(DISTINCT)"
             " would repair the counts but not the vanishing.",
        claims=[("eight wards, both totals matching their tables",
                 lambda rows, c: len(rows) == 8
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM procedures").fetchone()[0]
                 and sum(r[2] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM prescriptions").fetchone()[0])],
    ),
    dict(
        id=16, ledger="Q717", concept="J2", tier="5 - Joins and grain",
        title="Never admitted",
        prompt=(
            "Patients who have never been admitted. Write it as an outer"
            " join that keeps the non-matches.\n\n"
            "Return: patient_id, name"
        ),
        solution=("SELECT p.patient_id, p.name FROM patients p LEFT JOIN admissions a"
                  " ON a.patient_id = p.patient_id WHERE a.admission_id IS NULL"),
        trap_sql=("SELECT p.patient_id, p.name FROM patients p LEFT JOIN admissions a"
                  " ON a.patient_id = p.patient_id WHERE a.discharged_at IS NULL"),
        note="The anti-join tests a column that cannot be NULL in a real"
             " match -- the key. discharged_at CAN be NULL in a real match,"
             " for a patient still in, so the trap returns them too and"
             " calls current inpatients 'never admitted'. When an"
             " anti-join returns more than expected, look at which column"
             " it tests.",
        claims=[("hundreds of patients, none with an admission",
                 lambda rows, c: 300 < len(rows) < 700 and not c.execute(
                     "SELECT 1 FROM admissions WHERE patient_id IN (%s) LIMIT 1"
                     % ",".join(str(int(r[0])) for r in rows)).fetchall())],
    ),
    dict(
        id=17, ledger="Q718", concept="J2", tier="5 - Joins and grain",
        title="Never on the rota",
        prompt=(
            "Staff who have never worked a shift, with their role.\n\n"
            "Return: staff_id, name, role"
        ),
        solution=("SELECT s.staff_id, s.name, s.role FROM staff s WHERE NOT EXISTS"
                  " (SELECT 1 FROM shifts sh WHERE sh.staff_id = s.staff_id)"),
        trap_sql=("SELECT s.staff_id, s.name, s.role FROM staff s"
                  " WHERE s.staff_id NOT IN (SELECT taken_by FROM observations)"),
        note="NOT EXISTS against the rota. The trap asks the observations"
             " table instead -- who has never TAKEN a reading -- which is a"
             " different question with a much longer answer, because"
             " consultants, porters and pharmacists never take readings"
             " however many shifts they work. Read the prompt for the"
             " table it names.",
        claims=[("three people",
                 lambda rows, c: len(rows) == 3)],
    ),
    dict(
        id=18, ledger="Q719", concept="INT", tier="5 - Joins and grain",
        title="Controlled drugs on Fleming",
        prompt=(
            "For each controlled drug, how many prescriptions of it were"
            " running while the patient was on ward 5 -- Fleming -- at any"
            " point, whether or not they were admitted there.\n\n"
            "A prescription runs from started_on to ended_on (dates); a"
            " stay from from_at to to_at (datetimes, date() them). NULL ends"
            " run to 2026-06-30.\n\n"
            "Return: drug, prescriptions"
        ),
        solution=("SELECT d.name, COUNT(*) FROM prescriptions p JOIN drugs d"
                  " ON d.drug_id = p.drug_id JOIN ward_stays s"
                  " ON s.admission_id = p.admission_id AND s.ward_id = 5"
                  " AND p.started_on <= date(COALESCE(s.to_at, '2026-06-30 23:59'))"
                  " AND COALESCE(p.ended_on, '2026-06-30') >= date(s.from_at)"
                  " WHERE d.controlled = 1 GROUP BY d.name"),
        trap_sql=("SELECT d.name, COUNT(*) FROM prescriptions p JOIN drugs d"
                  " ON d.drug_id = p.drug_id JOIN admissions a"
                  " ON a.admission_id = p.admission_id WHERE d.controlled = 1"
                  " AND a.ward_id = 5 GROUP BY d.name"),
        note="A join on two INTERVALS overlapping, instead of two keys"
             " matching: the prescription's dates against the stay's, with"
             " the open ends supplied. The trap joins on the admitting ward,"
             " which misses every patient MOVED to Fleming and counts every"
             " one moved away -- close numbers, both wrong. date() on a"
             " datetime keeps the day; the two sides then compare as dates.",
        claims=[("seven controlled drugs, more than the admitting-ward count finds",
                 lambda rows, c: len(rows) == 7
                 and sum(r[1] for r in rows) > c.execute(
                     "SELECT COUNT(*) FROM prescriptions p JOIN drugs d"
                     " ON d.drug_id = p.drug_id JOIN admissions a"
                     " ON a.admission_id = p.admission_id"
                     " WHERE d.controlled = 1 AND a.ward_id = 5").fetchone()[0])],
    ),
    # ================================================= 6 Window functions
    dict(
        id=19, ledger="Q720", concept="W1", tier="6 - Window functions",
        title="Admissions accumulating, per ward",
        prompt=(
            "Admissions by ward and month of admission, with a running"
            " total that restarts for each ward.\n\n"
            "Return: ward_id, month, admissions, running_total"
        ),
        solution=("SELECT ward_id, m, n, SUM(n) OVER (PARTITION BY ward_id ORDER BY m)"
                  " FROM (SELECT ward_id, strftime('%Y-%m', admitted_at) m, COUNT(*) n"
                  " FROM admissions GROUP BY 1, 2)"),
        trap_sql=("SELECT ward_id, m, n, SUM(n) OVER (ORDER BY m)"
                  " FROM (SELECT ward_id, strftime('%Y-%m', admitted_at) m, COUNT(*) n"
                  " FROM admissions GROUP BY 1, 2)"),
        note="PARTITION BY restarts the accumulation per ward; ORDER BY"
             " inside the window decides the direction. Without the"
             " partition the trap adds every ward's month together, and"
             " because eight rows share each month value the total jumps"
             " in lumps of eight. A window over a grouped subquery is the"
             " tidy shape: aggregate first, then accumulate.",
        claims=[("each ward's last running total is its own count",
                 lambda rows, c: len(rows) == 144 and all(
                     max(r[3] for r in rows if r[0] == w) == sum(
                         r[2] for r in rows if r[0] == w)
                     for w in {r[0] for r in rows}))],
    ),
    dict(
        id=20, ledger="Q721", concept="W2", tier="6 - Window functions",
        title="Consultants by caseload",
        prompt=(
            "Every consultant who has admitted anyone, with their number of"
            " admissions and their rank -- 1 for the most. Two consultants"
            " tie; they share a rank, and no rank is skipped after them.\n\n"
            "Return: consultant_id, admissions, rank"
        ),
        solution=("SELECT consultant_id, COUNT(*), DENSE_RANK() OVER"
                  " (ORDER BY COUNT(*) DESC) FROM admissions GROUP BY 1"),
        trap_sql=("SELECT consultant_id, COUNT(*), DENSE_RANK() OVER"
                  " (ORDER BY COUNT(*)) FROM admissions GROUP BY 1"),
        note="DENSE_RANK shares a rank on a tie and does not skip after it;"
             " RANK shares and skips; ROW_NUMBER never shares. 'No rank is"
             " skipped' names the first. The trap ranks ascending, so 1"
             " is the LIGHTEST caseload. Ranking an aggregate works because"
             " windows run after GROUP BY.",
        claims=[("rank 1 is the biggest caseload, and a rank is shared",
                 lambda rows, c: max(rows, key=lambda r: r[1])[2] == 1
                 and len([r[2] for r in rows]) > len({r[2] for r in rows}))],
    ),
    dict(
        id=21, ledger="Q722", concept="W3", tier="6 - Window functions",
        title="Each route's share of the ward",
        prompt=(
            "For every ward and route of admission: how many admissions,"
            " and what percentage of THAT WARD's admissions came by that"
            " route, to two decimals. Each ward's three shares add to"
            " 100.\n\n"
            "Return: ward_id, admitted_via, admissions, pct_of_ward"
        ),
        solution=("SELECT ward_id, admitted_via, COUNT(*), ROUND(100.0 * COUNT(*)"
                  " / SUM(COUNT(*)) OVER (PARTITION BY ward_id), 2) FROM admissions"
                  " GROUP BY 1, 2"),
        trap_sql=("SELECT ward_id, admitted_via, COUNT(*), ROUND(100.0 * COUNT(*)"
                  " / SUM(COUNT(*)) OVER (), 2) FROM admissions GROUP BY 1, 2"),
        note="SUM(COUNT(*)) OVER (PARTITION BY ward_id) is the ward's total,"
             " computed from the grouped rows beside them. OVER () with no"
             " partition is the hospital's total, and the trap's"
             " twenty-four shares add to 100 once instead of eight times."
             " The partition names what the share is OF.",
        claims=[("twenty-four rows, each ward summing to 100",
                 lambda rows, c: len(rows) == 24 and all(
                     abs(sum(r[3] for r in rows if r[0] == w) - 100) < 0.05
                     for w in {r[0] for r in rows}))],
    ),
    dict(
        id=22, ledger="Q723", concept="W2", tier="6 - Window functions",
        title="The three highest earners per category",
        prompt=(
            "For each category of procedure -- surgical, diagnostic,"
            " therapeutic -- the three surgeons whose procedures of that"
            " category carry the highest total tariff, with the total in"
            " pence. Nine rows; ties by the lower surgeon_id.\n\n"
            "Return: category, surgeon_id, tariff_pence"
        ),
        solution=("SELECT category, surgeon_id, t FROM (SELECT pt.category, p.surgeon_id,"
                  " SUM(pt.tariff_pence) t, ROW_NUMBER() OVER (PARTITION BY pt.category"
                  " ORDER BY SUM(pt.tariff_pence) DESC, p.surgeon_id) rn"
                  " FROM procedures p JOIN procedure_types pt ON pt.code = p.code"
                  " GROUP BY 1, 2) WHERE rn <= 3"),
        trap_sql=("SELECT category, surgeon_id, t FROM (SELECT pt.category, p.surgeon_id,"
                  " SUM(pt.tariff_pence) t, ROW_NUMBER() OVER (PARTITION BY pt.category"
                  " ORDER BY SUM(pt.tariff_pence) DESC, p.surgeon_id) rn"
                  " FROM procedures p JOIN procedure_types pt ON pt.code = p.code"
                  " GROUP BY 1, 2) WHERE rn < 3"),
        note="Top-N per group: number inside a subquery, filter outside,"
             " because WHERE runs before the window exists. rn <= 3 is"
             " three; the trap's rn < 3 is two. The tariff comes from"
             " procedure_types by code, so the join is needed for the"
             " money and the category both.",
        claims=[("three per category",
                 lambda rows, c: len(rows) == 9 and all(
                     sum(1 for r in rows if r[0] == cat) == 3
                     for cat in {r[0] for r in rows}))],
    ),
    # ================================================ 7 Changing the data
    # Writable questions. The editor's script runs in a sandbox copy of the
    # database, then probe_sql reads the result and THAT is compared with the
    # reference. driver_sql, where present, is run by the question after the
    # script -- to fire a trigger, or to be refused by a constraint.
    dict(
        id=23, ledger="Q724", concept="R1", tier="7 - Changing the data",
        kind="script",
        title="Fill the division down the tree",
        prompt=(
            "Only the four division heads carry a division; the 56 people"
            " under them have NULL. Fill every NULL with the division of"
            " the head at the top of that person's chain, in ONE UPDATE"
            " fed by a recursive CTE.\n\n"
            "Managers do not always have lower ids than their reports, so"
            " copying from the direct manager will not cascade.\n\n"
            "Checked: staff per division"
        ),
        solution=("WITH RECURSIVE tree(staff_id, division) AS (\n"
                  "  SELECT staff_id, division FROM staff WHERE reports_to IS NULL\n"
                  "  UNION ALL\n"
                  "  SELECT s.staff_id, tree.division\n"
                  "  FROM staff s JOIN tree ON s.reports_to = tree.staff_id)\n"
                  "UPDATE staff\n"
                  "SET division = (SELECT division FROM tree"
                  " WHERE tree.staff_id = staff.staff_id)\n"
                  "WHERE division IS NULL;"),
        trap_sql=("UPDATE staff\n"
                  "SET division = (SELECT b.division FROM staff b"
                  " WHERE b.staff_id = staff.reports_to)\n"
                  "WHERE division IS NULL;"),
        probe_sql="SELECT division, COUNT(*) FROM staff GROUP BY 1 ORDER BY 1",
        note="A WITH -- recursive included -- can front an UPDATE. The CTE"
             " walks every chain from its head down, carrying the head's"
             " division, and the UPDATE looks each person up in it. The"
             " trap copies from the direct manager and relies on rows"
             " updated earlier in the same statement being visible to later"
             " ones; that works exactly when the manager's row came first,"
             " and 18 people are left NULL because theirs did not.",
        claims=[("nobody left without a division",
                 lambda rows, c: dict(rows) == {'Medicine': 10, 'Nursing': 30,
                                                'Pharmacy': 4, 'Surgery': 16})],
    ),
    dict(
        id=24, ledger="Q725", concept="DDL", tier="7 - Changing the data",
        kind="script",
        title="An id that is never reused",
        prompt=(
            "Create `incident_log (log_id INTEGER PRIMARY KEY, note TEXT NOT"
            " NULL)` so that an id, once used, is never handed out again --"
            " even after the row that had it is deleted.\n\n"
            "After your script, the question inserts two notes, deletes"
            " the second, and inserts a third. The third must get id 3, not"
            " 2.\n\n"
            "Checked: SELECT * FROM incident_log"
        ),
        solution=("CREATE TABLE incident_log (\n"
                  "  log_id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                  "  note   TEXT NOT NULL\n"
                  ");"),
        trap_sql=("CREATE TABLE incident_log (\n"
                  "  log_id INTEGER PRIMARY KEY,\n"
                  "  note   TEXT NOT NULL\n"
                  ");"),
        driver_sql=("INSERT INTO incident_log (note) VALUES ('lift fault');\n"
                    "INSERT INTO incident_log (note) VALUES ('entered in error');\n"
                    "DELETE FROM incident_log WHERE note = 'entered in error';\n"
                    "INSERT INTO incident_log (note) VALUES ('spill on floor 2');"),
        probe_sql="SELECT log_id, note FROM incident_log ORDER BY 1",
        note="A plain INTEGER PRIMARY KEY hands out max(rowid) + 1, so once"
             " the highest row is deleted its id comes round again -- and"
             " an audit trail whose ids get reused is not an audit trail."
             " AUTOINCREMENT records the largest id ever used in"
             " sqlite_sequence and never goes back. It costs a little on"
             " every insert, which is why SQLite makes you ask for it.",
        claims=[("ids 1 and 3, never 2 again",
                 lambda rows, c: rows == [(1, 'lift fault'), (3, 'spill on floor 2')])],
    ),
    dict(
        id=25, ledger="Q726", concept="DDL", tier="7 - Changing the data",
        kind="script",
        title="Notes that go with the patient",
        prompt=(
            "Create `patient_notes (note_id INTEGER PRIMARY KEY, patient_id"
            " INTEGER NOT NULL referencing patients, note TEXT NOT NULL)`"
            " such that deleting a patient deletes their notes with them.\n\n"
            "After your script, the question adds two notes for patient 6"
            " -- who has never been admitted -- and then deletes patient"
            " 6. Both the patient and the notes should be gone.\n\n"
            "Checked: whether patient 6 exists, and how many notes there"
            " are"
        ),
        solution=("CREATE TABLE patient_notes (\n"
                  "  note_id    INTEGER PRIMARY KEY,\n"
                  "  patient_id INTEGER NOT NULL REFERENCES patients(patient_id)"
                  " ON DELETE CASCADE,\n"
                  "  note       TEXT NOT NULL\n"
                  ");"),
        trap_sql=("CREATE TABLE patient_notes (\n"
                  "  note_id    INTEGER PRIMARY KEY,\n"
                  "  patient_id INTEGER NOT NULL REFERENCES patients(patient_id),\n"
                  "  note       TEXT NOT NULL\n"
                  ");"),
        driver_sql=("INSERT INTO patient_notes (patient_id, note)"
                    " VALUES (6, 'allergic to penicillin');\n"
                    "INSERT INTO patient_notes (patient_id, note)"
                    " VALUES (6, 'prefers morning appointments');\n"
                    "DELETE FROM patients WHERE patient_id = 6;"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM patients WHERE patient_id = 6),"
                   " (SELECT COUNT(*) FROM patient_notes)"),
        note="ON DELETE CASCADE is the declarative version of the trigger an"
             " earlier set wrote by hand: delete the parent and the"
             " children go too. Without it -- the trap -- the foreign key"
             " does its default job and REFUSES the delete, so the patient"
             " and both notes remain. The other options are SET NULL and"
             " RESTRICT. All of them only work with PRAGMA foreign_keys on,"
             " which the sandbox sets and SQLite by default does not.",
        claims=[("patient gone, notes gone",
                 lambda rows, c: rows == [(0, 0)])],
    ),
    dict(
        id=26, ledger="Q727", concept="TXN", tier="7 - Changing the data",
        kind="script",
        title="The child before the parent",
        prompt=(
            "Create `referrals (referral_id INTEGER PRIMARY KEY, patient_id"
            " INTEGER NOT NULL referencing patients, referred_on TEXT NOT"
            " NULL)`, then in one transaction insert a referral for patient"
            " 2001 -- who does not exist yet -- and THEN insert patient"
            " 2001 (any name and details), and commit.\n\n"
            "The foreign key has to be DEFERRABLE INITIALLY DEFERRED, or"
            " the first insert fails.\n\n"
            "Checked: how many referrals, and whether patient 2001 exists"
        ),
        solution=("CREATE TABLE referrals (\n"
                  "  referral_id INTEGER PRIMARY KEY,\n"
                  "  patient_id  INTEGER NOT NULL REFERENCES patients(patient_id)\n"
                  "              DEFERRABLE INITIALLY DEFERRED,\n"
                  "  referred_on TEXT NOT NULL\n"
                  ");\n"
                  "BEGIN;\n"
                  "INSERT INTO referrals (patient_id, referred_on)"
                  " VALUES (2001, '2026-07-01');\n"
                  "INSERT INTO patients (patient_id, name, born_on, sex, blood_group,"
                  " postcode_area)\n"
                  "VALUES (2001, 'Nia Baxter', '1988-03-09', 'F', NULL, 'LS6');\n"
                  "COMMIT;"),
        trap_sql=("CREATE TABLE referrals (\n"
                  "  referral_id INTEGER PRIMARY KEY,\n"
                  "  patient_id  INTEGER NOT NULL REFERENCES patients(patient_id),\n"
                  "  referred_on TEXT NOT NULL\n"
                  ");\n"
                  "BEGIN;\n"
                  "INSERT INTO referrals (patient_id, referred_on)"
                  " VALUES (2001, '2026-07-01');\n"
                  "INSERT INTO patients (patient_id, name, born_on, sex, blood_group,"
                  " postcode_area)\n"
                  "VALUES (2001, 'Nia Baxter', '1988-03-09', 'F', NULL, 'LS6');\n"
                  "COMMIT;"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM referrals),"
                   " (SELECT COUNT(*) FROM patients WHERE patient_id = 2001)"),
        note="A foreign key is normally checked as each statement ends. A"
             " DEFERRED one is checked at COMMIT instead, so inside a"
             " transaction the rows can arrive in any order as long as"
             " everything lines up by the end. The trap's immediate check"
             " fails the first insert and the script stops there. Deferred"
             " keys are how circular references get loaded; use them for"
             " that and not as a habit, because a failure surfaces late.",
        claims=[("one referral, one new patient",
                 lambda rows, c: rows == [(1, 1)])],
    ),
    dict(
        id=27, ledger="Q728", concept="TRG", tier="7 - Changing the data",
        kind="script",
        title="Fail the row, keep what came before",
        prompt=(
            "Write a trigger that refuses any observation with a heart rate"
            " over 200 -- but using RAISE(FAIL, ...) rather than ABORT, so"
            " that rows already written by the same statement stay"
            " written.\n\n"
            "After your script, the question inserts three observations"
            " for admission 1 in ONE statement; the third is the bad one."
            " The first two should land.\n\n"
            "Checked: time and heart rate of admission 1's observations on"
            " or after 2026-07-01"
        ),
        solution=("CREATE TRIGGER sane_heart_rate\n"
                  "BEFORE INSERT ON observations\n"
                  "WHEN NEW.heart_rate > 200\n"
                  "BEGIN\n"
                  "  SELECT RAISE(FAIL, 'heart rate out of range');\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER sane_heart_rate\n"
                  "BEFORE INSERT ON observations\n"
                  "WHEN NEW.heart_rate > 200\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'heart rate out of range');\n"
                  "END;"),
        driver_sql=("INSERT INTO observations (admission_id, taken_at, taken_by,"
                    " heart_rate, systolic, diastolic, temp_c) VALUES\n"
                    "  (1, '2026-07-01 08:00', 3, 72, 120, 80, 36.8),\n"
                    "  (1, '2026-07-01 12:00', 3, 75, 118, 79, 36.9),\n"
                    "  (1, '2026-07-01 16:00', 3, 240, 121, 82, 37.0);"),
        probe_sql=("SELECT taken_at, heart_rate FROM observations"
                   " WHERE admission_id = 1 AND taken_at >= '2026-07-01' ORDER BY 1"),
        note="The four RAISE forms differ in how much they undo. ABORT"
             " backs out the whole statement -- all three rows. FAIL stops"
             " the statement with the same error but KEEPS the rows it had"
             " already written, so the first two survive. ROLLBACK undoes"
             " the transaction; IGNORE skips the row and carries on. FAIL"
             " is rarely what you want -- a half-applied statement is hard"
             " to reason about -- but it is the one that explains the"
             " other three.",
        claims=[("two readings landed, the third did not",
                 lambda rows, c: rows == [('2026-07-01 08:00', 72),
                                          ('2026-07-01 12:00', 75)])],
    ),
    dict(
        id=28, ledger="Q729", concept="VIEW", tier="7 - Changing the data",
        kind="script",
        title="Stop, do not delete",
        prompt=(
            "Create a view `open_prescriptions (prescription_id,"
            " admission_id, drug_id, started_on)` over the prescriptions"
            " with no end date, and make DELETE on the view END the"
            " prescription -- set ended_on to '2026-07-01' -- rather than"
            " remove it.\n\n"
            "After your script, the question runs DELETE FROM"
            " open_prescriptions WHERE prescription_id = 367.\n\n"
            "Checked: the prescription count, 367's ended_on, and how many"
            " are still open"
        ),
        solution=("CREATE VIEW open_prescriptions AS\n"
                  "SELECT prescription_id, admission_id, drug_id, started_on\n"
                  "FROM prescriptions WHERE ended_on IS NULL;\n"
                  "CREATE TRIGGER stop_prescription\n"
                  "INSTEAD OF DELETE ON open_prescriptions\n"
                  "BEGIN\n"
                  "  UPDATE prescriptions SET ended_on = '2026-07-01'\n"
                  "  WHERE prescription_id = OLD.prescription_id;\n"
                  "END;"),
        trap_sql=("CREATE VIEW open_prescriptions AS\n"
                  "SELECT prescription_id, admission_id, drug_id, started_on\n"
                  "FROM prescriptions WHERE ended_on IS NULL;\n"
                  "CREATE TRIGGER stop_prescription\n"
                  "INSTEAD OF DELETE ON open_prescriptions\n"
                  "BEGIN\n"
                  "  DELETE FROM prescriptions\n"
                  "  WHERE prescription_id = OLD.prescription_id;\n"
                  "END;"),
        driver_sql="DELETE FROM open_prescriptions WHERE prescription_id = 367;",
        probe_sql=("SELECT (SELECT COUNT(*) FROM prescriptions),"
                   " (SELECT ended_on FROM prescriptions WHERE prescription_id = 367),"
                   " (SELECT COUNT(*) FROM open_prescriptions)"),
        note="A soft delete: the row leaves the VIEW because it no longer"
             " matches the view's WHERE, and the history keeps it. INSTEAD"
             " OF DELETE sees OLD -- the view row being 'deleted' -- and"
             " does whatever the deletion should mean. The trap really"
             " deletes, and the medical record loses a prescription that"
             " was given. Clinical, financial and audit data are the"
             " places a DELETE should usually be an UPDATE.",
        claims=[("nothing deleted, 367 ended, one fewer open",
                 lambda rows, c: rows == [(12389, '2026-07-01', 70)])],
    ),
    dict(
        id=29, ledger="Q730", concept="IDX", tier="7 - Changing the data",
        kind="script",
        title="One open admission per patient",
        prompt=(
            "A patient cannot be admitted twice at once. Enforce it with a"
            " UNIQUE index on `admissions` that applies only to rows with"
            " no discharge -- a partial index -- so past admissions do not"
            " count.\n\n"
            "After your script, the question inserts two admissions for"
            " patient 1500, who is currently in: one still open, one"
            " already discharged. Only the open one should be refused.\n\n"
            "Checked: how many partial unique indexes admissions has, and"
            " patient 1500's admission count"
        ),
        solution=("CREATE UNIQUE INDEX one_open_admission\n"
                  "ON admissions (patient_id) WHERE discharged_at IS NULL;"),
        trap_sql=("CREATE INDEX one_open_admission\n"
                  "ON admissions (patient_id) WHERE discharged_at IS NULL;"),
        driver_sql=("INSERT INTO admissions (patient_id, ward_id, consultant_id,"
                    " admitted_at, discharged_at, admitted_via, priority)\n"
                    "VALUES (1500, 3, 48, '2026-06-30 10:00', NULL, 'emergency',"
                    " 'urgent');\n"
                    "INSERT INTO admissions (patient_id, ward_id, consultant_id,"
                    " admitted_at, discharged_at, admitted_via, priority)\n"
                    "VALUES (1500, 3, 48, '2026-05-01 10:00', '2026-05-03 10:00',"
                    " 'referral', 'routine');"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM pragma_index_list('admissions')"
                   " WHERE \"unique\" = 1 AND partial = 1),"
                   " (SELECT COUNT(*) FROM admissions WHERE patient_id = 1500)"),
        note="A partial index has a WHERE: it indexes only the rows that"
             " match, and a UNIQUE one enforces uniqueness among those rows"
             " only. 'At most one open admission per patient' is exactly"
             " that -- a rule an ordinary UNIQUE(patient_id) could never"
             " express, since patients come back. The trap builds the"
             " partial index without UNIQUE, which speeds the lookup and"
             " stops nothing. pragma_index_list reports both flags.",
        claims=[("one partial unique index, one admission refused",
                 lambda rows, c: rows == [(1, 19)])],
    ),
    dict(
        id=30, ledger="Q731", concept="TMP", tier="7 - Changing the data",
        kind="script",
        title="Scratch space that leaves no trace",
        prompt=(
            "Find the admissions that have run more than 20 days as of"
            " 2026-06-30 23:59 -- open ones included -- and put their ids"
            " in a TEMPORARY table `long_stays`. Then raise every 'routine'"
            " admission in that list to 'urgent', reading the list from"
            " the temp table.\n\n"
            "A temp table lives in the `temp` schema and vanishes with the"
            " connection; nothing permanent should be left behind.\n\n"
            "Checked: how many admissions are urgent, whether long_stays"
            " exists in the main schema, and whether it exists in temp"
        ),
        solution=("CREATE TEMP TABLE long_stays AS\n"
                  "SELECT admission_id FROM admissions\n"
                  "WHERE julianday(COALESCE(discharged_at, '2026-06-30 23:59'))\n"
                  "      - julianday(admitted_at) > 20;\n"
                  "UPDATE admissions SET priority = 'urgent'\n"
                  "WHERE priority = 'routine'\n"
                  "  AND admission_id IN (SELECT admission_id FROM temp.long_stays);"),
        trap_sql=("CREATE TABLE long_stays AS\n"
                  "SELECT admission_id FROM admissions\n"
                  "WHERE julianday(COALESCE(discharged_at, '2026-06-30 23:59'))\n"
                  "      - julianday(admitted_at) > 20;\n"
                  "UPDATE admissions SET priority = 'urgent'\n"
                  "WHERE priority = 'routine'\n"
                  "  AND admission_id IN (SELECT admission_id FROM long_stays);"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM admissions WHERE priority = 'urgent'),"
                   " (SELECT COUNT(*) FROM sqlite_master WHERE name = 'long_stays'),"
                   " (SELECT COUNT(*) FROM sqlite_temp_master WHERE name = 'long_stays')"),
        note="CREATE TEMP TABLE makes a table in the `temp` schema, private"
             " to this connection and dropped when it closes -- the right"
             " home for a staging list. It is catalogued in"
             " sqlite_temp_master, not sqlite_master. The trap leaves a"
             " permanent table behind, which the next person finds and"
             " wonders about. temp.name qualifies it; a bare name finds the"
             " temp table first if both exist.",
        claims=[("five raised, no permanent table, one temp table",
                 lambda rows, c: rows == [(2462, 0, 1)])],
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
