"""Practice exercises: fifteen questions on the hospital schema.

The eighth set on the district hospital, beside the seventh Python set
(pyexercises.py), at the level of the three sets before it -- and the first
on RE-SEEDED data: SEED 846, so every count, average and id has changed
since Q702, and a remembered answer is worth nothing. Twelve SELECT
questions -- temperatures taken against readings made, HAVING on two
conditions, short names by length(), the second stay against the first,
quarters by arithmetic on the month, birthdays by '%m-%d', midnights
crossed, peak concurrent prescriptions per drug, prescriptions by the
admitting consultant, patients who only ever saw one ward, a rank within
a partition, and LAG of a ward -- and three WRITABLE questions on
constructs no earlier writable stage used:

  * a CHECK that the value is a real date, with date()
  * INSERT ... SELECT ... WHERE NOT EXISTS, adding only what is missing
  * a UNIQUE index on an expression

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script -- the inserts your constraint or
index should sort.
"""

import sqlite3

EXERCISES = [
    # ========================================================== 1 Warm-up
    dict(
        id=1, ledger="Q832", concept="A2", tier="1 - Warm-up",
        title="Temperatures taken",
        prompt=(
            "For each admitting ward: how many observations its admissions"
            " have, how many of those recorded a temperature, and the"
            " lowest and highest temperature seen. temp_c is NULL where it"
            " was not taken.\n\n"
            "Return: ward_id, readings, with_temp, lowest, highest"
        ),
        solution=("SELECT a.ward_id, COUNT(*), COUNT(o.temp_c), MIN(o.temp_c), MAX(o.temp_c)"
                  " FROM observations o JOIN admissions a ON a.admission_id = o.admission_id"
                  " GROUP BY a.ward_id"),
        trap_sql=("SELECT a.ward_id, COUNT(*), COUNT(*), MIN(o.temp_c), MAX(o.temp_c)"
                  " FROM observations o JOIN admissions a ON a.admission_id = o.admission_id"
                  " GROUP BY a.ward_id"),
        note="COUNT(*) counts rows; COUNT(column) counts rows where the"
             " column is not NULL. That is the whole difference between"
             " readings and with_temp, and the one place a NULL changes a"
             " count. MIN and MAX skip the NULLs on their own, so the two"
             " extremes need no COALESCE.",
        claims=[("eight wards, about a tenth of readings without a temperature",
                 lambda rows, c: len(rows) == 8
                 and all(0.85 < r[2] / r[1] < 0.95 and r[3] < r[4] for r in rows))],
    ),
    dict(
        id=2, ledger="Q833", concept="A3", tier="1 - Warm-up",
        title="Well-typed postcodes",
        prompt=(
            "Postcode areas with at least 125 patients, of whom fewer than"
            " 10 per cent have no recorded blood group: the area, its"
            " patients, how many have no blood group, and that percentage"
            " to one decimal.\n\n"
            "Return: postcode_area, patients, untyped, pct_untyped"
        ),
        solution=("SELECT postcode_area, COUNT(*), SUM(blood_group IS NULL),"
                  " ROUND(100.0 * SUM(blood_group IS NULL) / COUNT(*), 1) FROM patients"
                  " GROUP BY postcode_area HAVING COUNT(*) >= 125"
                  " AND 100.0 * SUM(blood_group IS NULL) / COUNT(*) < 10"),
        trap_sql=("SELECT postcode_area, COUNT(*), COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / COUNT(*), 1) FROM patients"
                  " WHERE blood_group IS NULL GROUP BY postcode_area"
                  " HAVING COUNT(*) >= 125"),
        note="Two conditions on the group, one on its size and one on a"
             " share within it, both in HAVING. SUM(blood_group IS NULL)"
             " counts the untyped without removing the typed, which the"
             " share needs as its denominator; filtering to IS NULL in"
             " WHERE leaves nothing to divide by and no area with 125"
             " untyped patients.",
        claims=[("four areas, all under a tenth untyped",
                 lambda rows, c: len(rows) == 4
                 and all(r[1] >= 125 and r[3] < 10 for r in rows))],
    ),
    # ======================================== 2 Strings and sequences
    dict(
        id=3, ledger="Q834", concept="STR", tier="2 - Strings and sequences",
        title="Short names",
        prompt=(
            "Patients whose full name -- space included -- is ten"
            " characters or fewer, with the name and its length().\n\n"
            "Return: patient_id, name, chars"
        ),
        solution=("SELECT patient_id, name, length(name) FROM patients"
                  " WHERE length(name) <= 10"),
        trap_sql=("SELECT patient_id, name, length(replace(name, ' ', '')) FROM patients"
                  " WHERE length(replace(name, ' ', '')) <= 10"),
        note="length() counts characters, spaces included; it is the"
             " string as stored. Stripping the space first measures a"
             " different thing and lets in five times as many names. Names"
             " repeat in this data -- several patients are called Rosa"
             " Iqbal -- which is why the id is in the answer.",
        claims=[("a few dozen patients, every name at most ten characters",
                 lambda rows, c: 20 < len(rows) < 80
                 and all(r[2] <= 10 and len(r[1]) == r[2] for r in rows))],
    ),
    dict(
        id=4, ledger="Q835", concept="SEQ", tier="2 - Strings and sequences",
        title="Longer the second time",
        prompt=(
            "For admissions with EXACTLY two ward stays, per admitting"
            " ward: how many there are, how many had a second stay longer"
            " than the first, and the percentage to one decimal. An open"
            " second stay runs to 2026-06-30 23:59.\n\n"
            "Return: ward_id, two_stay_admissions, second_longer, pct"
        ),
        solution=("SELECT a.ward_id, COUNT(*), SUM(julianday(COALESCE(s2.to_at, '2026-06-30 23:59'))"
                  " - julianday(s2.from_at) > julianday(s1.to_at) - julianday(s1.from_at)),"
                  " ROUND(100.0 * SUM(julianday(COALESCE(s2.to_at, '2026-06-30 23:59'))"
                  " - julianday(s2.from_at) > julianday(s1.to_at) - julianday(s1.from_at))"
                  " / COUNT(*), 1) FROM ward_stays s1 JOIN ward_stays s2"
                  " ON s2.admission_id = s1.admission_id AND s1.stay_seq = 1 AND s2.stay_seq = 2"
                  " JOIN admissions a ON a.admission_id = s1.admission_id"
                  " WHERE NOT EXISTS (SELECT 1 FROM ward_stays s3"
                  " WHERE s3.admission_id = s1.admission_id AND s3.stay_seq = 3)"
                  " GROUP BY a.ward_id"),
        trap_sql=("SELECT a.ward_id, COUNT(*), SUM(julianday(COALESCE(s2.to_at, '2026-06-30 23:59'))"
                  " - julianday(s2.from_at) > julianday(s1.to_at) - julianday(s1.from_at)),"
                  " ROUND(100.0 * SUM(julianday(COALESCE(s2.to_at, '2026-06-30 23:59'))"
                  " - julianday(s2.from_at) > julianday(s1.to_at) - julianday(s1.from_at))"
                  " / COUNT(*), 1) FROM ward_stays s1 JOIN ward_stays s2"
                  " ON s2.admission_id = s1.admission_id AND s1.stay_seq = 1 AND s2.stay_seq = 2"
                  " JOIN admissions a ON a.admission_id = s1.admission_id"
                  " GROUP BY a.ward_id"),
        note="Stays 1 and 2 of one admission side by side is a self-join"
             " with both sequence numbers pinned; 'exactly two' then needs"
             " a NOT EXISTS for a third. Without it the admissions that"
             " went on to a third ward are counted too, and their second"
             " stay was a stop on the way. The first stay always has an"
             " end -- a second stay followed it -- so only s2 needs the"
             " COALESCE.",
        claims=[("eight wards, about half longer the second time",
                 lambda rows, c: len(rows) == 8
                 and all(35 < r[3] < 65 for r in rows))],
    ),
    # ============================================== 3 Dates and times
    dict(
        id=5, ledger="Q836", concept="D1", tier="3 - Dates and times",
        title="Admissions by quarter",
        prompt=(
            "Admissions per calendar quarter: the year as an integer, the"
            " quarter 1 to 4, and the count. The quarter comes from the"
            " month by integer arithmetic -- months 1 to 3 are quarter 1,"
            " 4 to 6 quarter 2 -- and (month + 2) / 3 does it in whole"
            " numbers.\n\n"
            "Return: year, quarter, admissions"
        ),
        solution=("SELECT CAST(strftime('%Y', admitted_at) AS INTEGER),"
                  " (CAST(strftime('%m', admitted_at) AS INTEGER) + 2) / 3, COUNT(*)"
                  " FROM admissions GROUP BY 1, 2"),
        trap_sql=("SELECT CAST(strftime('%Y', admitted_at) AS INTEGER),"
                  " CAST(strftime('%m', admitted_at) AS INTEGER) / 3, COUNT(*)"
                  " FROM admissions GROUP BY 1, 2"),
        note="Integer division, used on purpose: (m + 2) / 3 maps 1-3 to"
             " 1, 4-6 to 2 and so on, because the remainder is thrown"
             " away. m / 3 alone maps 1 and 2 to 0 and 3 to 1, five"
             " buckets with the wrong edges. The year has to be in the"
             " grouping too, or Q1 of 2025 and Q1 of 2026 merge. CASE"
             " WHEN would do it in four lines; the arithmetic in one.",
        claims=[("six quarters, about a thousand each",
                 lambda rows, c: len(rows) == 6
                 and {r[1] for r in rows} == {1, 2, 3, 4}
                 and all(800 < r[2] < 1200 for r in rows))],
    ),
    dict(
        id=6, ledger="Q837", concept="D2", tier="3 - Dates and times",
        title="Birthdays in the first week of July",
        prompt=(
            "How many patients have a birthday on each day from 1 to 7"
            " July, whatever year they were born: the month-and-day as"
            " 'MM-DD' and the count. strftime('%m-%d', born_on) gives a"
            " string that ignores the year.\n\n"
            "Return: month_day, patients"
        ),
        solution=("SELECT strftime('%m-%d', born_on), COUNT(*) FROM patients"
                  " WHERE strftime('%m-%d', born_on) BETWEEN '07-01' AND '07-07' GROUP BY 1"),
        trap_sql=("SELECT strftime('%m-%d', born_on), COUNT(*) FROM patients"
                  " WHERE born_on BETWEEN '07-01' AND '07-07' GROUP BY 1"),
        note="A birthday is a month and a day with the year cut off, and"
             " strftime with a format of your own makes exactly that"
             " string, which then compares as text in calendar order. The"
             " full date compared with '07-01' is comparing '1962-...'"
             " with '07-...' -- never between -- so the trap returns"
             " nothing. Any strftime format is a grouping key.",
        claims=[("seven days, a handful of birthdays each",
                 lambda rows, c: len(rows) == 7
                 and all(r[0].startswith('07-') and 0 < r[1] < 15 for r in rows))],
    ),
    # ==================================== 4 Intervals and occupancy
    dict(
        id=7, ledger="Q838", concept="INT", tier="4 - Intervals and occupancy",
        title="Nights in hospital",
        prompt=(
            "For admissions 1 to 10 that are completed: the number of"
            " NIGHTS spent in -- the midnights between admission and"
            " discharge, which is the difference between the two DATES,"
            " not the rounded length of stay. A patient in from 23:00 to"
            " 02:00 spent one night and three hours.\n\n"
            "Return: admission_id, nights"
        ),
        solution=("SELECT admission_id, CAST(julianday(date(discharged_at))"
                  " - julianday(date(admitted_at)) AS INTEGER) FROM admissions"
                  " WHERE admission_id <= 10 AND discharged_at IS NOT NULL"),
        trap_sql=("SELECT admission_id, CAST(ROUND(julianday(discharged_at)"
                  " - julianday(admitted_at)) AS INTEGER) FROM admissions"
                  " WHERE admission_id <= 10 AND discharged_at IS NOT NULL"),
        note="Nights are calendar boundaries, so cut both datetimes to"
             " their day with date() and subtract: that counts the"
             " midnights crossed exactly. Rounding the length of stay"
             " counts something else -- a 2.6-day stay from Monday"
             " afternoon to Thursday morning is three nights, but rounds"
             " to 3 only by luck, and a 2.4-day one rounds to 2. The"
             " hotel question, in a hospital.",
        claims=[("ten admissions, whole numbers of nights",
                 lambda rows, c: len(rows) == 10
                 and all(isinstance(r[1], int) and 0 <= r[1] < 30 for r in rows))],
    ),
    dict(
        id=8, ledger="Q839", concept="INT", tier="4 - Intervals and occupancy",
        title="Peak demand for each drug",
        prompt=(
            "For each drug, the most prescriptions of it that were running"
            " on any one day: a prescription runs from started_on to"
            " ended_on inclusive, open ones to 2026-06-30. Turn each into a"
            " +1 on its start day and a -1 on the day AFTER its end, run a"
            " total per drug in date order, and take the maximum. Count a"
            " -1 before a +1 on the same day.\n\n"
            "Return: drug, peak"
        ),
        solution=("WITH ev AS (SELECT drug_id, started_on t, 1 d FROM prescriptions UNION ALL"
                  " SELECT drug_id, date(COALESCE(ended_on, '2026-06-30'), '+1 day'), -1"
                  " FROM prescriptions), run AS (SELECT drug_id, SUM(d) OVER (PARTITION BY drug_id"
                  " ORDER BY t, d ROWS UNBOUNDED PRECEDING) occ FROM ev)"
                  " SELECT dr.name, MAX(run.occ) FROM run JOIN drugs dr ON dr.drug_id = run.drug_id"
                  " GROUP BY dr.name"),
        trap_sql=("WITH ev AS (SELECT drug_id, started_on t, 1 d FROM prescriptions UNION ALL"
                  " SELECT drug_id, COALESCE(ended_on, '2026-06-30'), -1"
                  " FROM prescriptions), run AS (SELECT drug_id, SUM(d) OVER (PARTITION BY drug_id"
                  " ORDER BY t, d ROWS UNBOUNDED PRECEDING) occ FROM ev)"
                  " SELECT dr.name, MAX(run.occ) FROM run JOIN drugs dr ON dr.drug_id = run.drug_id"
                  " GROUP BY dr.name"),
        note="The running-occupancy pattern on DATES, where the end is"
             " inclusive: a course ending on the 10th was still running on"
             " the 10th, so its -1 belongs on the 11th -- date(ended_on,"
             " '+1 day'). Put it on the 10th and a course that starts the"
             " day another ends is never counted alongside it, and the"
             " peaks come out low. The ORDER BY t, d tie-break is the"
             " same as for datetimes.",
        claims=[("forty drugs, peaks of a handful",
                 lambda rows, c: len(rows) == 40
                 and all(3 <= r[1] <= 12 for r in rows))],
    ),
    # ============================================== 5 Joins and grain
    dict(
        id=9, ledger="Q840", concept="C2", tier="5 - Joins and grain",
        title="Prescribed by their own consultant",
        prompt=(
            "For each admitting ward: how many prescriptions its"
            " admissions have, and how many were written by the"
            " admission's OWN consultant -- prescribed_by equal to the"
            " admission's consultant_id -- with the percentage to one"
            " decimal.\n\n"
            "Return: ward_id, prescriptions, by_own_consultant, pct"
        ),
        solution=("SELECT a.ward_id, COUNT(*), SUM(p.prescribed_by = a.consultant_id),"
                  " ROUND(100.0 * SUM(p.prescribed_by = a.consultant_id) / COUNT(*), 1)"
                  " FROM prescriptions p JOIN admissions a ON a.admission_id = p.admission_id"
                  " GROUP BY a.ward_id"),
        trap_sql=("SELECT a.ward_id, COUNT(*), SUM(s.role = 'consultant'),"
                  " ROUND(100.0 * SUM(s.role = 'consultant') / COUNT(*), 1)"
                  " FROM prescriptions p JOIN admissions a ON a.admission_id = p.admission_id"
                  " JOIN staff s ON s.staff_id = p.prescribed_by GROUP BY a.ward_id"),
        note="Two foreign keys compared with each other: the prescriber"
             " on the prescription against the consultant on its"
             " admission, no third table needed. 'Written by a consultant'"
             " -- any consultant -- is a different question, ten times"
             " the size, and needs staff to answer. Read which column the"
             " question compares with which.",
        claims=[("eight wards, a few per cent by the own consultant",
                 lambda rows, c: len(rows) == 8
                 and all(2 < r[3] < 8 for r in rows))],
    ),
    dict(
        id=10, ledger="Q841", concept="E1", tier="5 - Joins and grain",
        title="Only ever one ward",
        prompt=(
            "Patients with three or more admissions whose every ward stay,"
            " across all of them, was on the SAME ward: patient_id, their"
            " admissions, and that ward. COUNT(DISTINCT) of the stays'"
            " ward being 1 is the test.\n\n"
            "Return: patient_id, admissions, ward_id"
        ),
        solution=("SELECT a.patient_id, COUNT(DISTINCT a.admission_id), MIN(s.ward_id)"
                  " FROM admissions a JOIN ward_stays s ON s.admission_id = a.admission_id"
                  " GROUP BY a.patient_id HAVING COUNT(DISTINCT a.admission_id) >= 3"
                  " AND COUNT(DISTINCT s.ward_id) = 1"),
        trap_sql=("SELECT patient_id, COUNT(*), MIN(ward_id) FROM admissions"
                  " GROUP BY patient_id HAVING COUNT(*) >= 3"
                  " AND COUNT(DISTINCT ward_id) = 1"),
        note="'Only ever' is all-or-none, and COUNT(DISTINCT x) = 1 says"
             " every row agrees -- a third spelling after NOT EXISTS and"
             " SUM(...) = 0. The wards a patient was on are in ward_stays;"
             " admissions.ward_id is only where each admission started,"
             " so the trap counts patients who were admitted to one ward"
             " and moved about freely. MIN(ward_id) returns the one value"
             " the HAVING has just guaranteed.",
        claims=[("a couple of dozen patients",
                 lambda rows, c: 10 < len(rows) < 60
                 and all(r[1] >= 3 for r in rows))],
    ),
    # ============================================== 6 Window functions
    dict(
        id=11, ledger="Q842", concept="W2", tier="6 - Window functions",
        title="Each ward's busiest consultants",
        prompt=(
            "For every ward and consultant who has admitted to it: the"
            " admissions, and the consultant's RANK within THAT ward, 1"
            " for the most, ties sharing a rank.\n\n"
            "Return: ward_id, consultant_id, admissions, rank_in_ward"
        ),
        solution=("SELECT ward_id, consultant_id, COUNT(*),"
                  " RANK() OVER (PARTITION BY ward_id ORDER BY COUNT(*) DESC)"
                  " FROM admissions GROUP BY ward_id, consultant_id"),
        trap_sql=("SELECT ward_id, consultant_id, COUNT(*),"
                  " RANK() OVER (ORDER BY COUNT(*) DESC)"
                  " FROM admissions GROUP BY ward_id, consultant_id"),
        note="A window over grouped rows, partitioned by one of the"
             " grouping columns: the ranking restarts for each ward."
             " Without PARTITION BY it ranks all eighty ward-consultant"
             " pairs against each other, and the busiest consultant on a"
             " quiet ward comes out thirtieth. Two consultants tie at the"
             " top of one ward here, which is RANK's job.",
        claims=[("eighty pairs, every ward with a rank 1",
                 lambda rows, c: len(rows) == 80
                 and sum(r[3] == 1 for r in rows) >= 8)],
    ),
    dict(
        id=12, ledger="Q843", concept="W3", tier="6 - Window functions",
        title="Patient 86, ward by ward",
        prompt=(
            "Patient 86 has the most admissions. For each of them in time"
            " order: when admitted, the admitting ward, the ward of the"
            " PREVIOUS admission -- NULL for the first -- and whether it"
            " is the same ward, as 1 or 0 (0 for the first).\n\n"
            "Return: admitted_at, ward_id, previous_ward, same_ward"
        ),
        solution=("SELECT admitted_at, ward_id, prev, COALESCE(ward_id = prev, 0) FROM (SELECT"
                  " admitted_at, ward_id, LAG(ward_id) OVER (ORDER BY admitted_at) prev"
                  " FROM admissions WHERE patient_id = 86)"),
        trap_sql=("SELECT admitted_at, ward_id, prev, COALESCE(ward_id = prev, 0) FROM (SELECT"
                  " admitted_at, ward_id, LAG(ward_id) OVER (ORDER BY admission_id) prev"
                  " FROM admissions WHERE patient_id = 86)"),
        note="LAG of a column that is not a number: it carries whatever"
             " the previous row held. 'Previous' is defined by the"
             " window's ORDER BY, and admission ids were not handed out in"
             " time order, so ordering by id shuffles the history."
             " ward_id = prev is NULL on the first row, where prev is"
             " NULL; COALESCE turns that into the 0 the question asks for.",
        claims=[("dozens of admissions, one with no previous ward",
                 lambda rows, c: len(rows) > 20
                 and sum(r[2] is None for r in rows) == 1
                 and sum(r[3] for r in rows) > 0)],
    ),
    # ============================================= 7 Changing the data
    dict(
        id=13, ledger="Q844", concept="DDL", tier="7 - Changing the data",
        kind="script",
        title="A column that must be a real date",
        prompt=(
            "Create `clinic_bookings (booking_id INTEGER PRIMARY KEY,"
            " patient_id INTEGER NOT NULL referencing patients, booked_for"
            " TEXT NOT NULL)` where booked_for must be a valid date in"
            " 'YYYY-MM-DD' form. date(x) returns NULL for anything it"
            " cannot read, and returns x unchanged when x is already a"
            " well-formed date -- a CHECK can use both facts, but mind"
            " that a CHECK which comes out NULL counts as PASSED, so"
            " compare with IS rather than =. After your"
            " script, the question inserts '2026-07-14', '2026-02-30',"
            " '14/07/2026' and 'tomorrow' for patient 1.\n\n"
            "Checked: the bookings that were accepted"
        ),
        solution=("CREATE TABLE clinic_bookings (\n"
                  "  booking_id INTEGER PRIMARY KEY,\n"
                  "  patient_id INTEGER NOT NULL REFERENCES patients(patient_id),\n"
                  "  booked_for TEXT    NOT NULL CHECK (date(booked_for) IS booked_for)\n"
                  ");"),
        trap_sql=("CREATE TABLE clinic_bookings (\n"
                  "  booking_id INTEGER PRIMARY KEY,\n"
                  "  patient_id INTEGER NOT NULL REFERENCES patients(patient_id),\n"
                  "  booked_for TEXT    NOT NULL CHECK (booked_for LIKE '____-__-__')\n"
                  ");"),
        driver_sql=("INSERT INTO clinic_bookings (patient_id, booked_for) VALUES (1, '2026-07-14');\n"
                    "INSERT INTO clinic_bookings (patient_id, booked_for) VALUES (1, '2026-02-30');\n"
                    "INSERT INTO clinic_bookings (patient_id, booked_for) VALUES (1, '14/07/2026');\n"
                    "INSERT INTO clinic_bookings (patient_id, booked_for) VALUES (1, 'tomorrow');"),
        probe_sql="SELECT booked_for FROM clinic_bookings ORDER BY booking_id",
        note="SQLite has no DATE type, so the table has to enforce the"
             " format itself. date(x) IS x is the test: a real date comes"
             " back unchanged and passes; '2026-02-30' is read, normalised"
             " to March 2nd, and no longer matches; garbage becomes NULL."
             " The catch is that a CHECK evaluating to NULL is treated as"
             " satisfied, so date(x) = x would let 'tomorrow' through --"
             " IS compares NULL as a value and refuses it. A LIKE pattern"
             " checks the shape only and lets February 30th in.",
        claims=[("only the real date lands",
                 lambda rows, c: rows == [('2026-07-14',)])],
    ),
    dict(
        id=14, ledger="Q845", concept="DML", tier="7 - Changing the data",
        kind="script",
        title="Add only what is missing",
        prompt=(
            "Create `ward_notes (ward_id INTEGER PRIMARY KEY referencing"
            " wards, note TEXT NOT NULL)` and insert notes for wards 1, 3"
            " and 5 (any text). Then, in ONE statement, give every ward"
            " that has no note yet the note 'none recorded' -- without"
            " touching the three that exist. INSERT ... SELECT with a NOT"
            " EXISTS is the shape.\n\n"
            "Checked: how many wards have a note, and how many of those"
            " notes read 'none recorded'"
        ),
        solution=("CREATE TABLE ward_notes (\n"
                  "  ward_id INTEGER PRIMARY KEY REFERENCES wards(ward_id),\n"
                  "  note    TEXT NOT NULL\n"
                  ");\n"
                  "INSERT INTO ward_notes VALUES (1, 'refurbished 2025'), (3, 'step-down beds'),"
                  " (5, 'isolation side room');\n"
                  "INSERT INTO ward_notes (ward_id, note)\n"
                  "SELECT w.ward_id, 'none recorded' FROM wards w\n"
                  "WHERE NOT EXISTS (SELECT 1 FROM ward_notes n WHERE n.ward_id = w.ward_id);"),
        trap_sql=("CREATE TABLE ward_notes (\n"
                  "  ward_id INTEGER PRIMARY KEY REFERENCES wards(ward_id),\n"
                  "  note    TEXT NOT NULL\n"
                  ");\n"
                  "INSERT INTO ward_notes VALUES (1, 'refurbished 2025'), (3, 'step-down beds'),"
                  " (5, 'isolation side room');\n"
                  "INSERT OR REPLACE INTO ward_notes (ward_id, note)\n"
                  "SELECT ward_id, 'none recorded' FROM wards;"),
        probe_sql=("SELECT COUNT(*), SUM(note = 'none recorded') FROM ward_notes"),
        note="INSERT ... SELECT with an anti-join adds exactly the rows"
             " that are absent and leaves the present ones alone -- the"
             " idiom for filling gaps. INSERT OR REPLACE over every ward"
             " fills the gaps too, but by overwriting the three real notes"
             " with the placeholder; a plain INSERT would stop at the"
             " first duplicate key. INSERT OR IGNORE is the other correct"
             " spelling here, since the key is what makes a note 'exist'.",
        claims=[("eight notes, five of them placeholders",
                 lambda rows, c: rows == [(8, 5)])],
    ),
    dict(
        id=15, ledger="Q846", concept="IDX", tier="7 - Changing the data",
        kind="script",
        title="Unique regardless of case",
        prompt=(
            "drugs.name is already UNIQUE, but 'Morphine' and 'morphine'"
            " are different strings to a plain UNIQUE. Create a unique"
            " index named `idx_drugs_name_ci` so that no two drugs can have"
            " names that differ only in case -- an index on an EXPRESSION"
            " of the column. After your script, the question inserts a"
            " drug called 'morphine' and one called 'Linezolid'.\n\n"
            "Checked: how many drugs there are, and whether 'morphine' is"
            " among them"
        ),
        solution="CREATE UNIQUE INDEX idx_drugs_name_ci ON drugs (lower(name));",
        trap_sql="CREATE UNIQUE INDEX idx_drugs_name_ci ON drugs (name);",
        driver_sql=("INSERT INTO drugs (name, form, unit_mg, price_pence, controlled)"
                    " VALUES ('morphine', 'tablet', 10, 180, 1);\n"
                    "INSERT INTO drugs (name, form, unit_mg, price_pence, controlled)"
                    " VALUES ('Linezolid', 'tablet', 600, 950, 0);"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM drugs),"
                   " (SELECT COUNT(*) FROM drugs WHERE name = 'morphine')"),
        note="An index can be built on an expression, and a UNIQUE one"
             " then enforces uniqueness of the expression's value: two"
             " names with the same lower() cannot coexist. A second unique"
             " index on the bare column repeats what the table already"
             " promises and lets 'morphine' in. COLLATE NOCASE on the"
             " column would be the other route; the expression index"
             " works without changing the table.",
        claims=[("forty-one drugs, no lower-case morphine",
                 lambda rows, c: rows == [(41, 0)])],
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
