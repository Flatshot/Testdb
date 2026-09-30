"""Practice exercises: fifteen questions on the hospital schema.

The sixth set on the district hospital, beside the fifth Python set
(pyexercises.py), at the level of the set before it. Same data: SEED 731,
not re-seeded. Twelve SELECT questions -- shifts pivoted by kind, HAVING on
a share of controlled drugs, printf() padding, which stay of three was the
longest, the last day of a month by modifiers, observations by hour,
procedures that overlapped in one theatre, days in hospital across
admissions with open ends, consultant-surgeon pairs, admissions with
neither procedure nor prescription, a gap to the leader by FIRST_VALUE,
and a cumulative share -- and three WRITABLE questions on constructs no
earlier writable stage used:

  * PRAGMA foreign_keys OFF, a load, and PRAGMA foreign_key_check
  * a JSON column filled by UPDATE with json_group_array
  * an AFTER UPDATE OF trigger that closes the open stay on discharge

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script -- the statement your trigger should
act on.
"""

import sqlite3

EXERCISES = [
    # ========================================================== 1 Warm-up
    dict(
        id=1, ledger="Q802", concept="A1", tier="1 - Warm-up",
        title="Days and nights, side by side",
        prompt=(
            "One row per ward: how many day shifts and how many night"
            " shifts have been worked there, as two columns, and the"
            " percentage of shifts that were nights to one decimal.\n\n"
            "Return: ward_id, day_shifts, night_shifts, pct_night"
        ),
        solution=("SELECT ward_id, SUM(kind = 'day'), SUM(kind = 'night'),"
                  " ROUND(100.0 * SUM(kind = 'night') / COUNT(*), 1) FROM shifts"
                  " GROUP BY ward_id"),
        trap_sql=("SELECT ward_id, SUM(kind = 'day'), SUM(kind = 'night'),"
                  " ROUND(100 * SUM(kind = 'night') / COUNT(*), 1) FROM shifts"
                  " GROUP BY ward_id"),
        note="Two conditional SUMs make the pivot. The percentage is the"
             " old integer-division trap in a new coat: 100 * nights and"
             " COUNT(*) are both integers, so 38.5 becomes 38 before ROUND"
             " can act. One real number in the expression is enough --"
             " 100.0 -- and it has to be inside the division, not applied"
             " after it.",
        claims=[("eight wards, about a third nights",
                 lambda rows, c: len(rows) == 8
                 and all(30 < r[3] < 45 for r in rows))],
    ),
    dict(
        id=2, ledger="Q803", concept="A3", tier="1 - Warm-up",
        title="Heavy on the controlled drugs",
        prompt=(
            "Prescribers who have written at least 460 prescriptions, of"
            " which at least 20 per cent were for controlled drugs --"
            " tested on the exact share, before rounding: staff_id,"
            " prescriptions, controlled, and the percentage to one"
            " decimal. `controlled` is on drugs.\n\n"
            "Return: staff_id, prescriptions, controlled, pct"
        ),
        solution=("SELECT p.prescribed_by, COUNT(*), SUM(d.controlled),"
                  " ROUND(100.0 * SUM(d.controlled) / COUNT(*), 1) FROM prescriptions p"
                  " JOIN drugs d ON d.drug_id = p.drug_id GROUP BY p.prescribed_by"
                  " HAVING COUNT(*) >= 460 AND 100.0 * SUM(d.controlled) / COUNT(*) >= 20"),
        trap_sql=("SELECT p.prescribed_by, COUNT(*), COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / COUNT(*), 1) FROM prescriptions p"
                  " JOIN drugs d ON d.drug_id = p.drug_id WHERE d.controlled = 1"
                  " GROUP BY p.prescribed_by HAVING COUNT(*) >= 92"),
        note="The share needs the whole group present, so the controlled"
             " flag is summed, not filtered. Two conditions on aggregates"
             " sit together in one HAVING with AND. The join brings the"
             " flag over from drugs; the grouping stays on the prescriber."
             " Three of the twenty-six pass; a fourth sits at 19.96 per"
             " cent, which rounds to 20.0 but is not 20.",
        claims=[("three prescribers, a fifth or so controlled",
                 lambda rows, c: len(rows) == 3
                 and all(r[1] >= 460 and 20 <= r[3] < 25 for r in rows))],
    ),
    # ======================================== 2 Strings and sequences
    dict(
        id=3, ledger="Q804", concept="STR", tier="2 - Strings and sequences",
        title="Reference numbers, zero-padded",
        prompt=(
            "Patients 1 to 5 with a reference of the form 'P00001' -- the"
            " letter P and the id padded with zeros to five digits."
            " printf('%05d', n) pads a number.\n\n"
            "Return: patient_id, reference"
        ),
        solution=("SELECT patient_id, printf('P%05d', patient_id) FROM patients"
                  " WHERE patient_id <= 5"),
        trap_sql=("SELECT patient_id, 'P' || patient_id FROM patients"
                  " WHERE patient_id <= 5"),
        note="printf() is C's formatting in SQL: %d an integer, %05d"
             " padded with zeros to width 5, %s a string, %.2f two"
             " decimals. Concatenation with || gives 'P1', which sorts"
             " 'P10' before 'P2' -- the padding is what makes the"
             " references sort as text in numeric order. format() is the"
             " same function under its newer name.",
        claims=[("five references, six characters each",
                 lambda rows, c: len(rows) == 5
                 and all(len(r[1]) == 6 and r[1].startswith('P0') for r in rows))],
    ),
    dict(
        id=4, ledger="Q805", concept="SEQ", tier="2 - Strings and sequences",
        title="Which of three stays was the longest",
        prompt=(
            "For admissions that had exactly three ward stays: how often"
            " the LONGEST of the three was stay 1, stay 2 and stay 3."
            " Three rows. An open stay runs to 2026-06-30 23:59; find each"
            " admission's longest stay first, then count by its"
            " stay_seq.\n\n"
            "Return: stay_seq, admissions"
        ),
        solution=("SELECT stay_seq, COUNT(*) FROM (SELECT stay_seq, ROW_NUMBER() OVER"
                  " (PARTITION BY admission_id ORDER BY julianday(COALESCE(to_at,"
                  " '2026-06-30 23:59')) - julianday(from_at) DESC) rn FROM ward_stays"
                  " WHERE admission_id IN (SELECT admission_id FROM ward_stays"
                  " GROUP BY admission_id HAVING COUNT(*) = 3)) WHERE rn = 1"
                  " GROUP BY stay_seq"),
        trap_sql=("SELECT stay_seq, COUNT(*) FROM (SELECT stay_seq, ROW_NUMBER() OVER"
                  " (PARTITION BY admission_id ORDER BY julianday(COALESCE(to_at,"
                  " '2026-06-30 23:59')) - julianday(from_at)) rn FROM ward_stays"
                  " WHERE admission_id IN (SELECT admission_id FROM ward_stays"
                  " GROUP BY admission_id HAVING COUNT(*) = 3)) WHERE rn = 1"
                  " GROUP BY stay_seq"),
        note="Top-1 per group, then a count of WHICH position won. The"
             " admissions with three stays come from a HAVING COUNT(*) = 3"
             " subquery; ROW_NUMBER ordered by length DESC marks the"
             " longest; the outer query counts the winners by stay_seq."
             " Without DESC the shortest wins, and the first stay is"
             " shortest more often than it is longest.",
        claims=[("three positions, the first stay winning most often",
                 lambda rows, c: len(rows) == 3
                 and max(rows, key=lambda r: r[1])[0] == 1
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM ward_stays WHERE stay_seq = 3").fetchone()[0])],
    ),
    # ============================================== 3 Dates and times
    dict(
        id=5, ledger="Q806", concept="D2", tier="3 - Dates and times",
        title="First and last day of the month",
        prompt=(
            "For admissions 1 to 5: the first and the last day of the"
            " month they were admitted in, as dates. date() takes"
            " modifiers: 'start of month', '+1 month', '-1 day'.\n\n"
            "Return: admission_id, month_start, month_end"
        ),
        solution=("SELECT admission_id, date(admitted_at, 'start of month'),"
                  " date(admitted_at, 'start of month', '+1 month', '-1 day')"
                  " FROM admissions WHERE admission_id <= 5"),
        trap_sql=("SELECT admission_id, date(admitted_at, 'start of month'),"
                  " date(admitted_at, '+1 month', '-1 day')"
                  " FROM admissions WHERE admission_id <= 5"),
        note="Modifiers apply left to right, each to the result of the"
             " last. 'start of month' first, then '+1 month' lands on the"
             " first of the NEXT month, then '-1 day' steps back to the"
             " last day of this one -- 28, 29, 30 or 31 without a lookup"
             " table. '+1 month' straight from the 29th of March gives the"
             " 29th of April, and '-1 day' from there is the 28th, which"
             " is nobody's month end.",
        claims=[("five rows, every month_end after its month_start",
                 lambda rows, c: len(rows) == 5
                 and all(r[1][:7] == r[2][:7] and r[1].endswith('-01')
                         and r[2][8:] in ('28', '29', '30', '31') for r in rows))],
    ),
    dict(
        id=6, ledger="Q807", concept="D1", tier="3 - Dates and times",
        title="Readings round the clock",
        prompt=(
            "Observations by the hour of day they were taken, 0 to 23 as"
            " an integer: how many, and the average heart rate to one"
            " decimal. strftime('%H') gives the hour, as text.\n\n"
            "Return: hour, readings, avg_hr"
        ),
        solution=("SELECT CAST(strftime('%H', taken_at) AS INTEGER), COUNT(*),"
                  " ROUND(AVG(heart_rate), 1) FROM observations GROUP BY 1"),
        trap_sql=("SELECT strftime('%H', taken_at), COUNT(*),"
                  " ROUND(AVG(heart_rate), 1) FROM observations GROUP BY 1"),
        note="%H is the two-digit hour, zero-padded, as text: '07'. The"
             " question wants the integer, and CAST is the conversion. The"
             " grouping is the same either way -- 24 groups -- so the"
             " difference is purely in the type of the first column, which"
             " the grader checks, and which any ORDER BY or comparison"
             " downstream would feel.",
        claims=[("twenty-four hours, rates in the eighties",
                 lambda rows, c: len(rows) == 24
                 and {r[0] for r in rows} == set(range(24))
                 and all(80 < r[2] < 95 for r in rows))],
    ),
    # ==================================== 4 Intervals and occupancy
    dict(
        id=7, ledger="Q808", concept="INT", tier="4 - Intervals and occupancy",
        title="Two on the table at once",
        prompt=(
            "For each theatre, how many PAIRS of procedures overlapped in"
            " time -- a procedure runs from performed_at for"
            " duration_minutes, and datetime(performed_at, '+' ||"
            " duration_minutes || ' minutes') is when it ended. Only"
            " procedures with a recorded duration; each pair once.\n\n"
            "Return: theatre, overlapping_pairs"
        ),
        solution=("SELECT a.theatre, COUNT(*) FROM procedures a JOIN procedures b"
                  " ON b.theatre = a.theatre AND b.procedure_id > a.procedure_id"
                  " AND a.duration_minutes IS NOT NULL AND b.duration_minutes IS NOT NULL"
                  " AND a.performed_at < datetime(b.performed_at, '+' || b.duration_minutes"
                  " || ' minutes') AND b.performed_at < datetime(a.performed_at, '+' ||"
                  " a.duration_minutes || ' minutes') GROUP BY a.theatre"),
        trap_sql=("SELECT a.theatre, COUNT(*) FROM procedures a JOIN procedures b"
                  " ON b.theatre = a.theatre AND b.procedure_id <> a.procedure_id"
                  " AND a.duration_minutes IS NOT NULL AND b.duration_minutes IS NOT NULL"
                  " AND a.performed_at < datetime(b.performed_at, '+' || b.duration_minutes"
                  " || ' minutes') AND b.performed_at < datetime(a.performed_at, '+' ||"
                  " a.duration_minutes || ' minutes') GROUP BY a.theatre"),
        note="An interval whose end has to be COMPUTED: datetime() with a"
             " modifier built from a column, '+' || minutes || ' minutes'."
             " Then the usual overlap test. The trap pairs each procedure"
             " with every other, so each pair is counted twice, once from"
             " each side -- b.procedure_id > a.procedure_id keeps one"
             " ordering of the pair.",
        claims=[("six theatres, dozens of overlaps each",
                 lambda rows, c: len(rows) == 6
                 and all(50 < r[1] < 150 for r in rows))],
    ),
    dict(
        id=8, ledger="Q809", concept="INT", tier="4 - Intervals and occupancy",
        title="Forty days in hospital",
        prompt=(
            "Patients who have spent more than 40 days in hospital"
            " altogether, adding up every admission as of 2026-06-30 23:59"
            " -- an open admission counts up to then. With their number of"
            " admissions and the total to one decimal.\n\n"
            "Return: patient_id, admissions, total_days"
        ),
        solution=("SELECT patient_id, COUNT(*), ROUND(SUM(julianday(COALESCE(discharged_at,"
                  " '2026-06-30 23:59')) - julianday(admitted_at)), 1) FROM admissions"
                  " GROUP BY patient_id HAVING SUM(julianday(COALESCE(discharged_at,"
                  " '2026-06-30 23:59')) - julianday(admitted_at)) > 40"),
        trap_sql=("SELECT patient_id, COUNT(*), ROUND(SUM(julianday(discharged_at)"
                  " - julianday(admitted_at)), 1) FROM admissions GROUP BY patient_id"
                  " HAVING SUM(julianday(discharged_at) - julianday(admitted_at)) > 40"),
        note="A sum of intervals with an open end supplied. Without the"
             " COALESCE an open admission contributes NULL, SUM skips it,"
             " and a patient still in after a long stay can fall below"
             " the line -- five of the thirty-nine here have an open"
             " admission. The HAVING repeats the SUM; an alias from the"
             " SELECT list works in SQLite but not everywhere.",
        claims=[("a few dozen patients, some with an admission still open",
                 lambda rows, c: 20 < len(rows) < 60
                 and all(r[2] > 40 for r in rows)
                 and c.execute("SELECT COUNT(*) FROM admissions WHERE discharged_at IS NULL"
                               " AND patient_id IN (%s)" % ",".join(str(r[0]) for r in rows)
                               ).fetchone()[0] >= 3)],
    ),
    # ============================================== 5 Joins and grain
    dict(
        id=9, ledger="Q810", concept="C2", tier="5 - Joins and grain",
        title="Consultant and surgeon, a regular pair",
        prompt=(
            "Pairs of consultant and surgeon who have worked on the same"
            " admissions at least 25 times -- the consultant is on the"
            " admission, the surgeon on the procedure -- with the number"
            " of procedures and of distinct admissions.\n\n"
            "Return: consultant_id, surgeon_id, procedures, admissions"
        ),
        solution=("SELECT a.consultant_id, p.surgeon_id, COUNT(*),"
                  " COUNT(DISTINCT a.admission_id) FROM procedures p"
                  " JOIN admissions a ON a.admission_id = p.admission_id"
                  " GROUP BY a.consultant_id, p.surgeon_id HAVING COUNT(*) >= 25"),
        trap_sql=("SELECT a.consultant_id, p.surgeon_id, COUNT(*),"
                  " COUNT(DISTINCT a.admission_id) FROM procedures p"
                  " JOIN admissions a ON a.admission_id = p.admission_id"
                  " GROUP BY a.consultant_id, p.surgeon_id"
                  " HAVING COUNT(DISTINCT a.admission_id) >= 25"),
        note="Grouping by two columns from two tables makes the pair the"
             " grain. Procedures and admissions are different counts of"
             " the same rows -- one admission can carry several"
             " procedures -- and the threshold is on procedures, so the"
             " HAVING must use COUNT(*), not the DISTINCT count, or fewer"
             " pairs pass.",
        claims=[("around ten pairs, procedures at or above admissions",
                 lambda rows, c: 5 < len(rows) < 20
                 and all(r[2] >= 25 and r[2] >= r[3] for r in rows))],
    ),
    dict(
        id=10, ledger="Q811", concept="E1", tier="5 - Joins and grain",
        title="Neither cut nor dosed",
        prompt=(
            "For each admitting ward, how many admissions had NO procedure"
            " AND NO prescription -- nothing done at all. Two NOT EXISTS,"
            " and mind the connective.\n\n"
            "Return: ward_id, admissions"
        ),
        solution=("SELECT ward_id, COUNT(*) FROM admissions a WHERE NOT EXISTS"
                  " (SELECT 1 FROM procedures p WHERE p.admission_id = a.admission_id)"
                  " AND NOT EXISTS (SELECT 1 FROM prescriptions x"
                  " WHERE x.admission_id = a.admission_id) GROUP BY ward_id"),
        trap_sql=("SELECT ward_id, COUNT(*) FROM admissions a WHERE NOT EXISTS"
                  " (SELECT 1 FROM procedures p WHERE p.admission_id = a.admission_id)"
                  " OR NOT EXISTS (SELECT 1 FROM prescriptions x"
                  " WHERE x.admission_id = a.admission_id) GROUP BY ward_id"),
        note="'No procedure and no prescription' is two absences joined"
             " by AND. Joined by OR it reads 'missing at least one', which"
             " is six times as many admissions. De Morgan is the rule:"
             " NOT (A OR B) is NOT A AND NOT B. Each NOT EXISTS is"
             " correlated on the admission and tests one child table.",
        claims=[("eight wards, a few dozen each",
                 lambda rows, c: len(rows) == 8
                 and all(20 < r[1] < 80 for r in rows))],
    ),
    # ============================================== 6 Window functions
    dict(
        id=11, ledger="Q812", concept="W1", tier="6 - Window functions",
        title="Behind the leader",
        prompt=(
            "Wards by admissions in June 2026: each ward's count, its"
            " DENSE_RANK with 1 for the most, and how many admissions"
            " behind the leading ward it is -- 0 for the leader."
            " FIRST_VALUE over the same ordering gives the leader's"
            " count on every row.\n\n"
            "Return: ward_id, admissions, rank, behind"
        ),
        solution=("SELECT ward_id, n, DENSE_RANK() OVER (ORDER BY n DESC),"
                  " FIRST_VALUE(n) OVER (ORDER BY n DESC) - n FROM (SELECT ward_id,"
                  " COUNT(*) n FROM admissions WHERE admitted_at >= '2026-06-01'"
                  " AND admitted_at < '2026-07-01' GROUP BY ward_id)"),
        trap_sql=("SELECT ward_id, n, DENSE_RANK() OVER (ORDER BY n DESC),"
                  " FIRST_VALUE(n) OVER (ORDER BY n) - n FROM (SELECT ward_id,"
                  " COUNT(*) n FROM admissions WHERE admitted_at >= '2026-06-01'"
                  " AND admitted_at < '2026-07-01' GROUP BY ward_id)"),
        note="Two windows over the same ordering: DENSE_RANK for the"
             " place, FIRST_VALUE for the top row's value on every row,"
             " and the subtraction happens outside the window. Ordered"
             " ascending, FIRST_VALUE is the SMALLEST count and 'behind'"
             " goes negative. A named WINDOW clause would let the two"
             " share one definition.",
        claims=[("eight wards, the leader at 0, two tied",
                 lambda rows, c: len(rows) == 8
                 and min(r[3] for r in rows) == 0
                 and all(r[3] >= 0 for r in rows)
                 and len({r[2] for r in rows}) < 8)],
    ),
    dict(
        id=12, ledger="Q813", concept="W3", tier="6 - Window functions",
        title="Running share of admissions",
        prompt=(
            "Wards ordered from most admissions to fewest, each with its"
            " count and the CUMULATIVE share of all admissions up to and"
            " including it, to one decimal -- the last row reaches 100."
            " Ties by the lower ward_id. Two window SUMs: one ordered, one"
            " not.\n\n"
            "Return: ward_id, admissions, cumulative_pct"
        ),
        solution=("SELECT ward_id, n, ROUND(100.0 * SUM(n) OVER (ORDER BY n DESC, ward_id)"
                  " / SUM(n) OVER (), 1) FROM (SELECT ward_id, COUNT(*) n FROM admissions"
                  " GROUP BY ward_id)"),
        trap_sql=("SELECT ward_id, n, ROUND(100.0 * SUM(n) OVER (ORDER BY n DESC, ward_id)"
                  " / SUM(n) OVER (ORDER BY n DESC, ward_id), 1) FROM (SELECT ward_id,"
                  " COUNT(*) n FROM admissions GROUP BY ward_id)"),
        note="SUM OVER with an ORDER BY is a running total; the same SUM"
             " OVER () with no ORDER BY is the grand total. Their ratio is"
             " the cumulative share, and it climbs to 100 on the last row."
             " Make the denominator a running total too and every row"
             " divides itself by itself: 100.0 all the way down.",
        claims=[("eight wards, climbing to 100",
                 lambda rows, c: len(rows) == 8
                 and max(r[2] for r in rows) == 100.0
                 and len({r[2] for r in rows}) == 8)],
    ),
    # ============================================= 7 Changing the data
    dict(
        id=13, ledger="Q814", concept="FK", tier="7 - Changing the data",
        kind="script",
        title="Load first, check afterwards",
        prompt=(
            "Create `referrals (referral_id INTEGER PRIMARY KEY, patient_id"
            " INTEGER NOT NULL referencing patients, referred_on TEXT NOT"
            " NULL)`. Then, with foreign keys switched OFF by PRAGMA, insert"
            " referrals for patients 1, 2 and 9999 -- the last does not"
            " exist -- switch them back ON, and use PRAGMA foreign_key_check"
            " (or the pragma_foreign_key_check table) to find and DELETE"
            " the offending row.\n\n"
            "Checked: the referrals left, and how many foreign-key"
            " violations remain"
        ),
        solution=("CREATE TABLE referrals (\n"
                  "  referral_id INTEGER PRIMARY KEY,\n"
                  "  patient_id  INTEGER NOT NULL REFERENCES patients(patient_id),\n"
                  "  referred_on TEXT    NOT NULL\n"
                  ");\n"
                  "PRAGMA foreign_keys = OFF;\n"
                  "INSERT INTO referrals (patient_id, referred_on)\n"
                  "VALUES (1, '2026-07-01'), (2, '2026-07-01'), (9999, '2026-07-01');\n"
                  "PRAGMA foreign_keys = ON;\n"
                  "DELETE FROM referrals WHERE rowid IN\n"
                  "  (SELECT rowid FROM pragma_foreign_key_check('referrals'));"),
        trap_sql=("CREATE TABLE referrals (\n"
                  "  referral_id INTEGER PRIMARY KEY,\n"
                  "  patient_id  INTEGER NOT NULL REFERENCES patients(patient_id),\n"
                  "  referred_on TEXT    NOT NULL\n"
                  ");\n"
                  "PRAGMA foreign_keys = OFF;\n"
                  "INSERT INTO referrals (patient_id, referred_on)\n"
                  "VALUES (1, '2026-07-01'), (2, '2026-07-01'), (9999, '2026-07-01');\n"
                  "PRAGMA foreign_keys = ON;"),
        probe_sql=("SELECT (SELECT group_concat(patient_id) FROM (SELECT patient_id"
                   " FROM referrals ORDER BY referral_id)),"
                   " (SELECT COUNT(*) FROM pragma_foreign_key_check('referrals'))"),
        note="Foreign keys are enforced only while PRAGMA foreign_keys is"
             " ON, and turning it off is how a bulk load arrives in any"
             " order. Nothing is re-checked when it goes back on -- the"
             " bad row is simply there. pragma_foreign_key_check lists"
             " every violating row with its table and rowid, which is"
             " exactly the key a DELETE needs. Load, check, fix: the"
             " check is the step people skip.",
        claims=[("two referrals left, no violations",
                 lambda rows, c: rows == [('1,2', 0)])],
    ),
    dict(
        id=14, ledger="Q815", concept="JSN", tier="7 - Changing the data",
        kind="script",
        title="A route stored as JSON",
        prompt=(
            "Add a column `route` (TEXT) to admissions and fill it, for"
            " EVERY admission, with a JSON array of the ward_ids of its"
            " stays in stay_seq order -- '[1,5,2]' for admission 12."
            " json_group_array(... ORDER BY ...) builds the array; an UPDATE"
            " with a correlated subquery fills the column.\n\n"
            "Checked: admission 12's route, how many routes are valid JSON"
            " arrays, and how many have three wards"
        ),
        solution=("ALTER TABLE admissions ADD COLUMN route TEXT;\n"
                  "UPDATE admissions SET route = (\n"
                  "  SELECT json_group_array(ward_id ORDER BY stay_seq)\n"
                  "  FROM ward_stays s WHERE s.admission_id = admissions.admission_id\n"
                  ");"),
        trap_sql=("ALTER TABLE admissions ADD COLUMN route TEXT;\n"
                  "UPDATE admissions SET route = (\n"
                  "  SELECT group_concat(ward_id, ',' ORDER BY stay_seq)\n"
                  "  FROM ward_stays s WHERE s.admission_id = admissions.admission_id\n"
                  ");"),
        probe_sql=("SELECT (SELECT route FROM admissions WHERE admission_id = 12),"
                   " (SELECT COUNT(*) FROM admissions WHERE json_valid(route)"
                   " AND json_type(route) = 'array'),"
                   " (SELECT COUNT(*) FROM admissions WHERE json_array_length(route) = 3)"),
        note="json_group_array is an aggregate that builds a JSON array,"
             " and it takes an ORDER BY inside the call, so the route is"
             " in stay order. group_concat gives '1,5,2', which looks"
             " close but is not JSON: json_valid says no and"
             " json_array_length errors. A JSON column can then be queried"
             " with json_each and ->> without parsing text yourself.",
        claims=[("admission 12 went 1, 5, 2; every route valid",
                 lambda rows, c: rows[0][0] == '[1,5,2]' and rows[0][1] == 6000
                 and rows[0][2] == c.execute(
                     "SELECT COUNT(*) FROM ward_stays WHERE stay_seq = 3").fetchone()[0])],
    ),
    dict(
        id=15, ledger="Q816", concept="TRG", tier="7 - Changing the data",
        kind="script",
        title="Discharge closes the stay",
        prompt=(
            "Write a trigger so that when an admission's discharged_at is"
            " set -- an UPDATE OF that column from NULL to a value -- the"
            " admission's OPEN ward stay gets that value as its to_at."
            " After your script, the question discharges admission 173 at"
            " '2026-07-01 09:00'.\n\n"
            "Checked: admission 173's stays with their to_at, and how many"
            " open stays it has left"
        ),
        solution=("CREATE TRIGGER close_stay_on_discharge\n"
                  "AFTER UPDATE OF discharged_at ON admissions\n"
                  "WHEN OLD.discharged_at IS NULL AND NEW.discharged_at IS NOT NULL\n"
                  "BEGIN\n"
                  "  UPDATE ward_stays SET to_at = NEW.discharged_at\n"
                  "  WHERE admission_id = NEW.admission_id AND to_at IS NULL;\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER close_stay_on_discharge\n"
                  "AFTER UPDATE OF discharged_at ON admissions\n"
                  "WHEN OLD.discharged_at IS NULL AND NEW.discharged_at IS NOT NULL\n"
                  "BEGIN\n"
                  "  UPDATE ward_stays SET to_at = NEW.discharged_at\n"
                  "  WHERE admission_id = NEW.admission_id;\n"
                  "END;"),
        driver_sql=("UPDATE admissions SET discharged_at = '2026-07-01 09:00'"
                    " WHERE admission_id = 173;"),
        probe_sql=("SELECT stay_seq, to_at FROM ward_stays WHERE admission_id = 173"
                   " UNION ALL SELECT 'open', COUNT(*) FROM ward_stays"
                   " WHERE admission_id = 173 AND to_at IS NULL"),
        note="UPDATE OF column fires only when that column is named in the"
             " SET, and the WHEN clause narrows it to the NULL-to-value"
             " transition. The body keeps two tables consistent, which is"
             " what triggers are for. The trap's UPDATE has no to_at IS"
             " NULL, so it rewrites the earlier, closed stay's end as"
             " well -- admission 173 moved ward on the 28th, and that"
             " history is lost.",
        claims=[("the first stay untouched, the second closed, none open",
                 lambda rows, c: rows == [(1, '2026-06-28 13:17'), (2, '2026-07-01 09:00'),
                                          ('open', 0)])],
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
