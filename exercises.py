"""Practice exercises: fifteen questions on the hospital schema.

The fifth set on the district hospital, beside the fourth Python set
(pyexercises.py), back at the level of Q752-Q771 after the easier set
before it. Same data: SEED 731, not re-seeded. Twelve SELECT questions --
an average of products, HAVING on a share, surnames shared by several
staff, an admission that came back to its first ward, stays that crossed
a month end, %W against %U, the peak occupancy of each ward from a
running sum, two prescriptions of one drug at once, an admission against
its own ward's average, three children of one parent, a seven-day moving
average, and the second-longest stay per ward -- and three WRITABLE
questions on constructs no earlier writable stage used:

  * ON UPDATE CASCADE
  * a CHECK constraint built on json_valid()
  * INSTEAD OF UPDATE on a view

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script -- the statements your key, check
or trigger should follow, refuse or redirect.
"""

import sqlite3

EXERCISES = [
    # ========================================================== 1 Warm-up
    dict(
        id=1, ledger="Q787", concept="A2", tier="1 - Warm-up",
        title="Milligrams a day, by form",
        prompt=(
            "For each form of drug: how many prescriptions, the average"
            " DAILY dose in mg to one decimal -- dose_mg times"
            " times_per_day, averaged over prescriptions -- and the"
            " largest daily dose.\n\n"
            "Return: form, prescriptions, avg_daily_mg, max_daily_mg"
        ),
        solution=("SELECT d.form, COUNT(*), ROUND(AVG(p.dose_mg * p.times_per_day), 1),"
                  " MAX(p.dose_mg * p.times_per_day) FROM prescriptions p"
                  " JOIN drugs d ON d.drug_id = p.drug_id GROUP BY d.form"),
        trap_sql=("SELECT d.form, COUNT(*), ROUND(AVG(p.dose_mg) * AVG(p.times_per_day), 1),"
                  " MAX(p.dose_mg) * MAX(p.times_per_day) FROM prescriptions p"
                  " JOIN drugs d ON d.drug_id = p.drug_id GROUP BY d.form"),
        note="The average of a product is not the product of the averages:"
             " a big dose given once a day and a small one given six times"
             " pull the two apart. Compute the daily dose per row, inside"
             " the aggregate, and then average or take the max of THAT."
             " MAX(a) * MAX(b) has the same flaw -- the largest dose and"
             " the most frequent schedule need not be on the same row.",
        claims=[("four forms, tablets the most prescribed",
                 lambda rows, c: len(rows) == 4
                 and max(rows, key=lambda r: r[1])[0] == 'tablet'
                 and all(r[2] < r[3] for r in rows))],
    ),
    dict(
        id=2, ledger="Q788", concept="A3", tier="1 - Warm-up",
        title="Mostly emergencies",
        prompt=(
            "Consultants for whom at least 55 per cent of admissions came"
            " in as emergencies: consultant_id, admissions, emergencies,"
            " and the percentage to one decimal.\n\n"
            "Return: consultant_id, admissions, emergencies, pct"
        ),
        solution=("SELECT consultant_id, COUNT(*), SUM(admitted_via = 'emergency'),"
                  " ROUND(100.0 * SUM(admitted_via = 'emergency') / COUNT(*), 1)"
                  " FROM admissions GROUP BY consultant_id"
                  " HAVING 100.0 * SUM(admitted_via = 'emergency') / COUNT(*) >= 55"),
        trap_sql=("SELECT consultant_id, COUNT(*), COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / COUNT(*), 1)"
                  " FROM admissions WHERE admitted_via = 'emergency'"
                  " GROUP BY consultant_id HAVING COUNT(*) >= 330"),
        note="A share needs both the part and the whole in the same"
             " group. Filter to emergencies in WHERE and the whole is gone:"
             " every consultant is at 100 per cent and the count is of"
             " emergencies only. Keep every row, count the part with a"
             " conditional SUM, and put the ratio in HAVING. The"
             " percentages here run from 54 to 57, so the threshold cuts"
             " the ten consultants roughly in half.",
        claims=[("about half the consultants, all between 55 and 60",
                 lambda rows, c: 3 <= len(rows) <= 7
                 and all(55 <= r[3] < 60 for r in rows))],
    ),
    # ======================================== 2 Strings and sequences
    dict(
        id=3, ledger="Q789", concept="STR", tier="2 - Strings and sequences",
        title="Surnames on the payroll",
        prompt=(
            "Surnames shared by THREE or more staff, with how many, and"
            " their staff_ids as one comma-separated string in id order."
            " The surname is everything after the single space in the"
            " name.\n\n"
            "Return: surname, people, staff_ids"
        ),
        solution=("SELECT substr(name, instr(name, ' ') + 1), COUNT(*),"
                  " group_concat(staff_id ORDER BY staff_id) FROM staff"
                  " GROUP BY 1 HAVING COUNT(*) >= 3"),
        trap_sql=("SELECT substr(name, instr(name, ' ')), COUNT(*),"
                  " group_concat(staff_id ORDER BY staff_id) FROM staff"
                  " GROUP BY 1 HAVING COUNT(*) >= 3"),
        note="instr() gives the position OF the space, so the surname"
             " starts one past it; substr(name, instr(name, ' ')) keeps"
             " the space as a leading character. The grouping still works,"
             " because every ' Baxter' matches every other ' Baxter', but"
             " the string returned is wrong. Grouping by an expression and"
             " ordering inside group_concat are both routine by now.",
        claims=[("nine surnames, Papadopoulos the most common",
                 lambda rows, c: len(rows) == 9
                 and max(rows, key=lambda r: r[1])[0] == 'Papadopoulos'
                 and all(r[0] == r[0].strip() and r[2].count(',') == r[1] - 1
                         for r in rows))],
    ),
    dict(
        id=4, ledger="Q790", concept="SEQ", tier="2 - Strings and sequences",
        title="Back where they started",
        prompt=(
            "Admissions that moved ward twice and ended up back on the"
            " ward they were admitted to -- stay 3 on the same ward as"
            " stay 1 -- counted per ward. Two rows of ward_stays for one"
            " admission, joined.\n\n"
            "Return: ward_id, returned"
        ),
        solution=("SELECT a.ward_id, COUNT(*) FROM ward_stays a JOIN ward_stays b"
                  " ON b.admission_id = a.admission_id AND a.stay_seq = 1"
                  " AND b.stay_seq = 3 AND b.ward_id = a.ward_id GROUP BY a.ward_id"),
        trap_sql=("SELECT a.ward_id, COUNT(*) FROM ward_stays a JOIN ward_stays b"
                  " ON b.admission_id = a.admission_id AND a.stay_seq = 1"
                  " AND b.stay_seq = 2 AND b.ward_id = a.ward_id GROUP BY a.ward_id"),
        note="Two specific rows of one admission -- the first stay and the"
             " third -- are a self-join with both sequence numbers pinned."
             " The trap pins the second stay instead, and consecutive"
             " stays are never on the same ward -- a move is a move -- so"
             " it finds nothing. Coming back means going somewhere else"
             " in between, which is why the question says stay 3.",
        claims=[("eight wards, a handful each",
                 lambda rows, c: len(rows) == 8
                 and all(0 < r[1] < 20 for r in rows))],
    ),
    # ============================================== 3 Dates and times
    dict(
        id=5, ledger="Q791", concept="D1", tier="3 - Dates and times",
        title="Crossing the month end",
        prompt=(
            "For each month of admission, 'YYYY-MM': how many completed"
            " admissions began in it, how many of them were discharged in"
            " a LATER month than they were admitted, and the percentage to"
            " one decimal. Compare months, not lengths of stay.\n\n"
            "Return: month, admissions, crossed, pct"
        ),
        solution=("SELECT strftime('%Y-%m', admitted_at), COUNT(*),"
                  " SUM(strftime('%Y-%m', discharged_at) > strftime('%Y-%m', admitted_at)),"
                  " ROUND(100.0 * SUM(strftime('%Y-%m', discharged_at)"
                  " > strftime('%Y-%m', admitted_at)) / COUNT(*), 1)"
                  " FROM admissions WHERE discharged_at IS NOT NULL GROUP BY 1"),
        trap_sql=("SELECT strftime('%Y-%m', admitted_at), COUNT(*),"
                  " SUM(julianday(discharged_at) - julianday(admitted_at) > 30),"
                  " ROUND(100.0 * SUM(julianday(discharged_at) - julianday(admitted_at) > 30)"
                  " / COUNT(*), 1)"
                  " FROM admissions WHERE discharged_at IS NOT NULL GROUP BY 1"),
        note="'A later month' is about calendar boundaries: a two-day stay"
             " from 31 May crosses one, a 29-day stay from 1 May does not."
             " No stay here runs 30 days, so the trap's column is all"
             " zeros. Two 'YYYY-MM' strings compare correctly as text, so"
             " > between them is the whole test.",
        claims=[("eighteen months, up to a fifth crossing",
                 lambda rows, c: len(rows) == 18
                 and all(0 <= r[3] < 25 for r in rows)
                 and sum(r[2] for r in rows) > 300)],
    ),
    dict(
        id=6, ledger="Q792", concept="D2", tier="3 - Dates and times",
        title="Weeks that start on Monday",
        prompt=(
            "Admissions per week of 2026, for weeks 1 to 10, with the"
            " week as an integer. A week starts on MONDAY, and week 1 is"
            " the first week with a Monday in it -- which is what"
            " strftime('%W') numbers. Its sibling '%U' starts weeks on"
            " Sunday.\n\n"
            "Return: week, admissions"
        ),
        solution=("SELECT CAST(strftime('%W', admitted_at) AS INTEGER), COUNT(*)"
                  " FROM admissions WHERE admitted_at >= '2026' GROUP BY 1"
                  " HAVING CAST(strftime('%W', admitted_at) AS INTEGER) BETWEEN 1 AND 10"),
        trap_sql=("SELECT CAST(strftime('%U', admitted_at) AS INTEGER), COUNT(*)"
                  " FROM admissions WHERE admitted_at >= '2026' GROUP BY 1"
                  " HAVING CAST(strftime('%U', admitted_at) AS INTEGER) BETWEEN 1 AND 10"),
        note="strftime has two week numbers, one letter apart: %W counts"
             " weeks from Monday, %U from Sunday, and every Sunday's"
             " admissions land in a different week under each. Both are"
             " zero-padded text, so CAST them. The BETWEEN on the week can"
             " go in HAVING since it filters groups; WHERE on the"
             " expression would work too.",
        claims=[("ten weeks, sixty-odd admissions each",
                 lambda rows, c: len(rows) == 10
                 and {r[0] for r in rows} == set(range(1, 11))
                 and all(40 < r[1] < 100 for r in rows))],
    ),
    # ==================================== 4 Intervals and occupancy
    dict(
        id=7, ledger="Q793", concept="INT", tier="4 - Intervals and occupancy",
        title="Each ward's peak in June",
        prompt=(
            "The most patients each ward held at any one instant during"
            " June 2026. Turn every ward stay into a +1 event at from_at"
            " and a -1 at to_at, run a total per ward in time order over"
            " ALL events, and take the highest value reached at an event"
            " inside June. At the same instant, count the departure"
            " before the arrival.\n\n"
            "Return: ward_id, peak"
        ),
        solution=("WITH ev AS (SELECT ward_id, from_at t, 1 d FROM ward_stays UNION ALL"
                  " SELECT ward_id, to_at, -1 FROM ward_stays WHERE to_at IS NOT NULL),"
                  " run AS (SELECT ward_id, t, SUM(d) OVER (PARTITION BY ward_id"
                  " ORDER BY t, d ROWS UNBOUNDED PRECEDING) occ FROM ev)"
                  " SELECT ward_id, MAX(occ) FROM run"
                  " WHERE t >= '2026-06-01' AND t < '2026-07-01' GROUP BY ward_id"),
        trap_sql=("WITH ev AS (SELECT ward_id, from_at t, 1 d FROM ward_stays"
                  " WHERE from_at >= '2026-06-01' AND from_at < '2026-07-01' UNION ALL"
                  " SELECT ward_id, to_at, -1 FROM ward_stays WHERE to_at >= '2026-06-01'"
                  " AND to_at < '2026-07-01'),"
                  " run AS (SELECT ward_id, t, SUM(d) OVER (PARTITION BY ward_id"
                  " ORDER BY t, d ROWS UNBOUNDED PRECEDING) occ FROM ev)"
                  " SELECT ward_id, MAX(occ) FROM run GROUP BY ward_id"),
        note="A running occupancy must start from empty, which means"
             " running over EVERY event and only then keeping the June"
             " ones -- the trap filters the events first, so the patients"
             " already on the ward on 1 June are never counted in and the"
             " peak is too low. ORDER BY t, d puts a -1 before a +1 at the"
             " same instant, so a bed handed over does not count twice."
             " ROWS UNBOUNDED PRECEDING makes the frame explicit.",
        claims=[("eight wards, peaks under the bed count",
                 lambda rows, c: len(rows) == 8
                 and all(3 < r[1] <= c.execute(
                     "SELECT beds FROM wards WHERE ward_id = ?", (r[0],)).fetchone()[0]
                     for r in rows))],
    ),
    dict(
        id=8, ledger="Q794", concept="INT", tier="4 - Intervals and occupancy",
        title="Twice at once",
        prompt=(
            "For each drug, how many admissions had two prescriptions of"
            " it RUNNING AT THE SAME TIME -- two rows of prescriptions for"
            " the same admission and drug whose date ranges overlap. Count"
            " each admission once. An open prescription runs to"
            " 2026-06-30.\n\n"
            "Return: drug, admissions"
        ),
        solution=("SELECT d.name, COUNT(DISTINCT a.admission_id) FROM prescriptions a"
                  " JOIN prescriptions b ON b.admission_id = a.admission_id"
                  " AND b.drug_id = a.drug_id AND b.prescription_id > a.prescription_id"
                  " AND a.started_on <= COALESCE(b.ended_on, '2026-06-30')"
                  " AND b.started_on <= COALESCE(a.ended_on, '2026-06-30')"
                  " JOIN drugs d ON d.drug_id = a.drug_id GROUP BY d.name"),
        trap_sql=("SELECT d.name, COUNT(DISTINCT a.admission_id) FROM prescriptions a"
                  " JOIN prescriptions b ON b.admission_id = a.admission_id"
                  " AND b.drug_id = a.drug_id AND b.prescription_id > a.prescription_id"
                  " JOIN drugs d ON d.drug_id = a.drug_id GROUP BY d.name"),
        note="Same admission, same drug, two different rows: that is the"
             " self-join, with the id inequality so each pair is seen"
             " once. Then the overlap test -- each starts before the other"
             " ends -- with the open ends supplied. Without it, a course"
             " that ended in March and one that began in May count as"
             " concurrent. COUNT(DISTINCT) because an admission with three"
             " overlapping courses forms three pairs.",
        claims=[("every drug, a dozen admissions at most",
                 lambda rows, c: len(rows) == 40
                 and all(0 < r[1] <= 15 for r in rows))],
    ),
    # ============================================== 5 Joins and grain
    dict(
        id=9, ledger="Q795", concept="E2", tier="5 - Joins and grain",
        title="Longer than the ward's usual",
        prompt=(
            "For completed admissions that began in June 2026, per"
            " admitting ward: how many there were, and how many lasted"
            " longer than THAT WARD's average completed length of stay"
            " over all time. The comparison is against the ward's own"
            " average, so it is a correlated subquery.\n\n"
            "Return: ward_id, admissions, above_average"
        ),
        solution=("SELECT a.ward_id, COUNT(*), SUM(julianday(a.discharged_at)"
                  " - julianday(a.admitted_at) > (SELECT AVG(julianday(x.discharged_at)"
                  " - julianday(x.admitted_at)) FROM admissions x WHERE x.ward_id = a.ward_id"
                  " AND x.discharged_at IS NOT NULL)) FROM admissions a"
                  " WHERE a.discharged_at IS NOT NULL AND a.admitted_at >= '2026-06-01'"
                  " GROUP BY a.ward_id"),
        trap_sql=("SELECT a.ward_id, COUNT(*), SUM(julianday(a.discharged_at)"
                  " - julianday(a.admitted_at) > (SELECT AVG(julianday(x.discharged_at)"
                  " - julianday(x.admitted_at)) FROM admissions x"
                  " WHERE x.discharged_at IS NOT NULL)) FROM admissions a"
                  " WHERE a.discharged_at IS NOT NULL AND a.admitted_at >= '2026-06-01'"
                  " GROUP BY a.ward_id"),
        note="A correlated subquery is one that refers to the outer row --"
             " here x.ward_id = a.ward_id -- and so is re-evaluated per"
             " row against that row's ward. Leave the correlation out and"
             " the subquery is one hospital-wide average, the same for"
             " every ward, and a geriatric ward with long stays looks"
             " uniformly 'above average'. A CTE of per-ward averages"
             " joined in is the other spelling.",
        claims=[("eight wards, a third or so above their own average",
                 lambda rows, c: len(rows) == 8
                 and all(0.1 < r[2] / r[1] < 0.6 for r in rows))],
    ),
    dict(
        id=10, ledger="Q796", concept="C2", tier="5 - Joins and grain",
        title="Three children of one admission",
        prompt=(
            "For admissions 1 to 10: how many ward stays, procedures and"
            " prescriptions each has. Three tables hang off admissions,"
            " and joining all three at once multiplies each count by the"
            " other two.\n\n"
            "Return: admission_id, stays, procedures, prescriptions"
        ),
        solution=("SELECT a.admission_id, (SELECT COUNT(*) FROM ward_stays s"
                  " WHERE s.admission_id = a.admission_id), (SELECT COUNT(*)"
                  " FROM procedures p WHERE p.admission_id = a.admission_id),"
                  " (SELECT COUNT(*) FROM prescriptions x WHERE x.admission_id"
                  " = a.admission_id) FROM admissions a WHERE a.admission_id <= 10"),
        trap_sql=("SELECT a.admission_id, COUNT(DISTINCT s.stay_seq),"
                  " COUNT(p.procedure_id), COUNT(x.prescription_id) FROM admissions a"
                  " LEFT JOIN ward_stays s ON s.admission_id = a.admission_id"
                  " LEFT JOIN procedures p ON p.admission_id = a.admission_id"
                  " LEFT JOIN prescriptions x ON x.admission_id = a.admission_id"
                  " WHERE a.admission_id <= 10 GROUP BY a.admission_id"),
        note="Three one-to-many joins on the same parent make a product:"
             " an admission with 2 stays, 3 procedures and 4 prescriptions"
             " becomes 24 rows, and the plain counts are 24, not 2, 3, 4."
             " COUNT(DISTINCT) rescues a count of distinct KEYS but not"
             " here -- procedure_id and prescription_id are distinct on"
             " every product row, so they are multiplied anyway. Count"
             " each child on its own, in a subquery or a pre-aggregated"
             " CTE, and only then bring the numbers together.",
        claims=[("ten admissions, small counts, at least one with two stays",
                 lambda rows, c: len(rows) == 10
                 and all(r[1] <= 3 and r[2] < 10 and r[3] < 10 for r in rows)
                 and any(r[1] >= 2 for r in rows))],
    ),
    # ============================================== 6 Window functions
    dict(
        id=11, ledger="Q797", concept="W1", tier="6 - Window functions",
        title="A week's worth, smoothed",
        prompt=(
            "For each day of June 2026: the admissions that day, and the"
            " seven-day moving average -- that day and the six before it,"
            " to two decimals. Days early in the month average over what"
            " there is. Every day of June has admissions, so a calendar is"
            " not needed.\n\n"
            "Return: day, admissions, avg7"
        ),
        solution=("SELECT day, n, ROUND(AVG(n) OVER (ORDER BY day ROWS BETWEEN 6 PRECEDING"
                  " AND CURRENT ROW), 2) FROM (SELECT date(admitted_at) day, COUNT(*) n"
                  " FROM admissions WHERE admitted_at >= '2026-06-01'"
                  " AND admitted_at < '2026-07-01' GROUP BY 1)"),
        trap_sql=("SELECT day, n, ROUND(AVG(n) OVER (ORDER BY day), 2)"
                  " FROM (SELECT date(admitted_at) day, COUNT(*) n"
                  " FROM admissions WHERE admitted_at >= '2026-06-01'"
                  " AND admitted_at < '2026-07-01' GROUP BY 1)"),
        note="A window with ORDER BY and no frame clause defaults to"
             " everything from the first row to the current one -- a"
             " running average, not a moving one. ROWS BETWEEN 6 PRECEDING"
             " AND CURRENT ROW is the seven-day frame, and it shrinks at"
             " the start of the month because there is nothing before"
             " day 1. The daily counts are aggregated first, in the"
             " subquery; the window runs over those rows.",
        claims=[("thirty days, averages near a dozen",
                 lambda rows, c: len(rows) == 30
                 and all(5 < r[2] < 20 for r in rows))],
    ),
    dict(
        id=12, ledger="Q798", concept="W2", tier="6 - Window functions",
        title="Second-longest stay on each ward",
        prompt=(
            "For each admitting ward, the SECOND-longest completed"
            " admission: its id and its length in days to two decimals."
            " Ties by the lower admission_id.\n\n"
            "Return: ward_id, admission_id, days"
        ),
        solution=("SELECT ward_id, admission_id, ROUND(los, 2) FROM (SELECT ward_id,"
                  " admission_id, julianday(discharged_at) - julianday(admitted_at) los,"
                  " ROW_NUMBER() OVER (PARTITION BY ward_id ORDER BY julianday(discharged_at)"
                  " - julianday(admitted_at) DESC, admission_id) rn FROM admissions"
                  " WHERE discharged_at IS NOT NULL) WHERE rn = 2"),
        trap_sql=("SELECT ward_id, admission_id, ROUND(los, 2) FROM (SELECT ward_id,"
                  " admission_id, julianday(discharged_at) - julianday(admitted_at) los,"
                  " ROW_NUMBER() OVER (PARTITION BY ward_id ORDER BY julianday(discharged_at)"
                  " - julianday(admitted_at), admission_id) rn FROM admissions"
                  " WHERE discharged_at IS NOT NULL) WHERE rn = 2"),
        note="Top-N per group generalises: number the rows within each"
             " partition in the order that matters and keep the number you"
             " want -- 2 here. DESC is what makes 'second-longest' rather"
             " than 'second-shortest', which is what the trap returns."
             " The tiebreak decides which of two equal stays is second.",
        claims=[("eight wards, stays of two to three weeks",
                 lambda rows, c: len(rows) == 8
                 and all(14 < r[2] < 28 for r in rows))],
    ),
    # ============================================= 7 Changing the data
    dict(
        id=13, ledger="Q799", concept="DDL", tier="7 - Changing the data",
        kind="script",
        title="Rename the key and the children follow",
        prompt=(
            "Create `ward_codes (code TEXT PRIMARY KEY, ward_id INTEGER NOT"
            " NULL referencing wards)` and `ward_sections (section_id INTEGER"
            " PRIMARY KEY, code TEXT NOT NULL referencing ward_codes, label"
            " TEXT NOT NULL)`, such that changing a code in ward_codes"
            " changes it in every section that uses it. Insert codes 'NIG'"
            " for ward 1 and 'SEA' for ward 2, and sections 'bay A' and"
            " 'bay B' under NIG and 'bay A' under SEA. After your script,"
            " the question renames NIG to 'NGT'.\n\n"
            "Checked: each section's code, in section order"
        ),
        solution=("CREATE TABLE ward_codes (\n"
                  "  code    TEXT    PRIMARY KEY,\n"
                  "  ward_id INTEGER NOT NULL REFERENCES wards(ward_id)\n"
                  ");\n"
                  "CREATE TABLE ward_sections (\n"
                  "  section_id INTEGER PRIMARY KEY,\n"
                  "  code       TEXT NOT NULL REFERENCES ward_codes(code) ON UPDATE CASCADE,\n"
                  "  label      TEXT NOT NULL\n"
                  ");\n"
                  "INSERT INTO ward_codes VALUES ('NIG', 1), ('SEA', 2);\n"
                  "INSERT INTO ward_sections (code, label)\n"
                  "VALUES ('NIG', 'bay A'), ('NIG', 'bay B'), ('SEA', 'bay A');"),
        trap_sql=("CREATE TABLE ward_codes (\n"
                  "  code    TEXT    PRIMARY KEY,\n"
                  "  ward_id INTEGER NOT NULL REFERENCES wards(ward_id)\n"
                  ");\n"
                  "CREATE TABLE ward_sections (\n"
                  "  section_id INTEGER PRIMARY KEY,\n"
                  "  code       TEXT NOT NULL REFERENCES ward_codes(code),\n"
                  "  label      TEXT NOT NULL\n"
                  ");\n"
                  "INSERT INTO ward_codes VALUES ('NIG', 1), ('SEA', 2);\n"
                  "INSERT INTO ward_sections (code, label)\n"
                  "VALUES ('NIG', 'bay A'), ('NIG', 'bay B'), ('SEA', 'bay A');"),
        driver_sql="UPDATE ward_codes SET code = 'NGT' WHERE code = 'NIG';",
        probe_sql="SELECT section_id, code FROM ward_sections ORDER BY section_id",
        note="A foreign key has an ON UPDATE action as well as ON DELETE,"
             " and it matters exactly when the parent key is a natural"
             " value that can change, like a code. CASCADE rewrites the"
             " children; the default refuses the rename while children"
             " exist, which is what the trap does -- the update fails and"
             " every section still says NIG. Surrogate integer keys never"
             " change, which is one argument for them.",
        claims=[("the two NIG sections now read NGT",
                 lambda rows, c: rows == [(1, 'NGT'), (2, 'NGT'), (3, 'SEA')])],
    ),
    dict(
        id=14, ledger="Q800", concept="JSN", tier="7 - Changing the data",
        kind="script",
        title="A column that must hold JSON",
        prompt=(
            "Create `device_readings (reading_id INTEGER PRIMARY KEY,"
            " admission_id INTEGER NOT NULL referencing admissions, payload"
            " TEXT NOT NULL)` where payload must be VALID JSON -- a CHECK"
            " constraint can call json_valid(). After your script, the"
            " question inserts three payloads for admission 1:"
            " '{\"spo2\": 97}', 'spo2=97' and '[97, 98]'.\n\n"
            "Checked: the payloads that were accepted, in insertion order"
        ),
        solution=("CREATE TABLE device_readings (\n"
                  "  reading_id   INTEGER PRIMARY KEY,\n"
                  "  admission_id INTEGER NOT NULL REFERENCES admissions(admission_id),\n"
                  "  payload      TEXT    NOT NULL CHECK (json_valid(payload))\n"
                  ");"),
        trap_sql=("CREATE TABLE device_readings (\n"
                  "  reading_id   INTEGER PRIMARY KEY,\n"
                  "  admission_id INTEGER NOT NULL REFERENCES admissions(admission_id),\n"
                  "  payload      TEXT    NOT NULL CHECK (payload LIKE '{%')\n"
                  ");"),
        driver_sql=("INSERT INTO device_readings (admission_id, payload)"
                    " VALUES (1, '{\"spo2\": 97}');\n"
                    "INSERT INTO device_readings (admission_id, payload)"
                    " VALUES (1, 'spo2=97');\n"
                    "INSERT INTO device_readings (admission_id, payload)"
                    " VALUES (1, '[97, 98]');"),
        probe_sql="SELECT payload FROM device_readings ORDER BY reading_id",
        note="A CHECK constraint can call any deterministic function, and"
             " json_valid() is one: it accepts the object and the array"
             " and refuses the bare text. Testing for a leading brace"
             " refuses the array, which is valid JSON, and would accept"
             " '{not json' too. Once the column is known to hold JSON,"
             " json_extract(payload, '$.spo2') and ->> can be used on it"
             " without a guard.",
        claims=[("the object and the array land, the bare text is refused",
                 lambda rows, c: rows == [('{"spo2": 97}',), ('[97, 98]',)])],
    ),
    dict(
        id=15, ledger="Q801", concept="VIEW", tier="7 - Changing the data",
        kind="script",
        title="Editing through a view",
        prompt=(
            "Create a view `patient_contact (patient_id, name,"
            " postcode_area)` over patients, and make an UPDATE of"
            " postcode_area on the VIEW change the patient underneath --"
            " an INSTEAD OF UPDATE trigger. After your script, the question"
            " runs UPDATE patient_contact SET postcode_area = 'LS99' WHERE"
            " patient_id = 3.\n\n"
            "Checked: patient 3's postcode in the table, and how many"
            " patients have postcode LS99"
        ),
        solution=("CREATE VIEW patient_contact AS\n"
                  "  SELECT patient_id, name, postcode_area FROM patients;\n"
                  "CREATE TRIGGER patient_contact_update\n"
                  "INSTEAD OF UPDATE OF postcode_area ON patient_contact\n"
                  "BEGIN\n"
                  "  UPDATE patients SET postcode_area = NEW.postcode_area\n"
                  "  WHERE patient_id = OLD.patient_id;\n"
                  "END;"),
        trap_sql=("CREATE VIEW patient_contact AS\n"
                  "  SELECT patient_id, name, postcode_area FROM patients;\n"
                  "CREATE TRIGGER patient_contact_update\n"
                  "INSTEAD OF UPDATE OF postcode_area ON patient_contact\n"
                  "BEGIN\n"
                  "  UPDATE patients SET postcode_area = NEW.postcode_area;\n"
                  "END;"),
        driver_sql="UPDATE patient_contact SET postcode_area = 'LS99' WHERE patient_id = 3;",
        probe_sql=("SELECT (SELECT postcode_area FROM patients WHERE patient_id = 3),"
                   " (SELECT COUNT(*) FROM patients WHERE postcode_area = 'LS99')"),
        note="A view is read-only unless a trigger says what an UPDATE on"
             " it means. INSTEAD OF UPDATE fires once per view row the"
             " statement matched, with OLD and NEW for that row -- and the"
             " trigger body has to say WHICH patient to change, by"
             " OLD.patient_id. The trap's body has no WHERE, so the one"
             " row that matched the view updates every patient in the"
             " table. Without the trigger at all, the UPDATE is refused:"
             " 'cannot modify patient_contact because it is a view'.",
        claims=[("patient 3 moved, nobody else",
                 lambda rows, c: rows == [('LS99', 1)])],
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
