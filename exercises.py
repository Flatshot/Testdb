"""Practice exercises: twenty questions on the hospital schema.

The third set on the district hospital, beside the second Python set
(pyexercises.py). Same data as before -- SEED 731, not re-seeded -- and
fifteen SELECT questions that repeat nothing from Q702-Q751: a pivot by
conditional aggregation, two aggregates in HAVING on another entity, hours
to a first event, a username built from a name, a district as a number,
same-day discharges, LEAD, who was already on the ward, the longest gap
between admissions, days on a drug with open ends, an anti-join on a date,
all-or-none, distinct staff per ward, NTILE quartiles, and top-1 per group
with a tiebreak. The last five are WRITABLE questions, graded on the state
of the database after your script runs, on constructs none of the seven
earlier writable stages used --

  * DEFAULT values on columns
  * UNIQUE with COLLATE NOCASE
  * ON DELETE SET NULL
  * a WITHOUT ROWID table with a composite key
  * ALTER TABLE ... RENAME TO / RENAME COLUMN, and what follows the rename

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script -- the inserts and deletes your
table should fill in, refuse, or follow.
"""

import sqlite3

EXERCISES = [
    # ========================================================== 1 Warm-up
    dict(
        id=1, ledger="Q752", concept="A1", tier="1 - Warm-up",
        title="Priorities, side by side",
        prompt=(
            "One row per consultant who has admitted anyone, with their"
            " admissions split into three columns by priority: how many"
            " were immediate, how many urgent, how many routine. Three"
            " counts on one row, not three rows.\n\n"
            "Return: consultant_id, immediate, urgent, routine"
        ),
        solution=("SELECT consultant_id, SUM(priority = 'immediate'),"
                  " SUM(priority = 'urgent'), SUM(priority = 'routine')"
                  " FROM admissions GROUP BY consultant_id"),
        trap_sql=("SELECT consultant_id, COUNT(priority = 'immediate'),"
                  " COUNT(priority = 'urgent'), COUNT(priority = 'routine')"
                  " FROM admissions GROUP BY consultant_id"),
        note="A pivot by hand: one aggregate per column, each counting only"
             " the rows that match. SUM of a comparison works because a"
             " comparison is 1 or 0 in SQLite; SUM(CASE WHEN ... THEN 1"
             " ELSE 0 END) is the portable spelling. COUNT of a comparison"
             " counts every row, since 0 is not NULL, so all three columns"
             " come out equal to the total.",
        claims=[("ten consultants, routine the largest column",
                 lambda rows, c: len(rows) == 10
                 and all(r[3] > r[2] > r[1] for r in rows))],
    ),
    dict(
        id=2, ledger="Q753", concept="A3", tier="1 - Warm-up",
        title="Long operations",
        prompt=(
            "Surgeons who have performed at least 175 procedures and whose"
            " average recorded duration is over 160 minutes: surgeon_id,"
            " their procedures, and the average to one decimal. A NULL"
            " duration is unknown and simply not averaged.\n\n"
            "Return: surgeon_id, procedures, avg_minutes"
        ),
        solution=("SELECT surgeon_id, COUNT(*), ROUND(AVG(duration_minutes), 1)"
                  " FROM procedures GROUP BY surgeon_id"
                  " HAVING COUNT(*) >= 175 AND AVG(duration_minutes) > 160"),
        trap_sql=("SELECT surgeon_id, COUNT(*), ROUND(AVG(duration_minutes), 1)"
                  " FROM procedures WHERE duration_minutes > 160"
                  " GROUP BY surgeon_id HAVING COUNT(*) >= 175"),
        note="'Average over 160' is a condition on the group, so it goes in"
             " HAVING. Put duration > 160 in WHERE and you keep only the"
             " long procedures, then average those -- every average is"
             " over 160 by construction, and the counts are of long"
             " procedures only. HAVING can use an aggregate the SELECT"
             " list does not even show.",
        claims=[("a handful of surgeons, averages in the 160s",
                 lambda rows, c: 3 <= len(rows) <= 10
                 and all(160 < r[2] < 175 and r[1] >= 175 for r in rows))],
    ),
    dict(
        id=3, ledger="Q754", concept="D1", tier="1 - Warm-up",
        title="Hours to the first procedure",
        prompt=(
            "For each admitting ward: the average number of hours between"
            " admission and the FIRST procedure of the admission, to one"
            " decimal, over admissions that had at least one. Find each"
            " admission's earliest performed_at first, then average the"
            " difference.\n\n"
            "Return: ward_id, avg_hours"
        ),
        solution=("SELECT a.ward_id, ROUND(AVG(24 * (julianday(f.first_at)"
                  " - julianday(a.admitted_at))), 1) FROM admissions a"
                  " JOIN (SELECT admission_id, MIN(performed_at) first_at"
                  " FROM procedures GROUP BY admission_id) f"
                  " ON f.admission_id = a.admission_id GROUP BY a.ward_id"),
        trap_sql=("SELECT a.ward_id, ROUND(AVG(24 * (julianday(p.performed_at)"
                  " - julianday(a.admitted_at))), 1) FROM admissions a"
                  " JOIN procedures p ON p.admission_id = a.admission_id"
                  " GROUP BY a.ward_id"),
        note="Two grains: the question is one number per ADMISSION -- its"
             " first procedure -- averaged per ward. Joining procedures"
             " directly averages over every procedure, so an admission"
             " with four procedures weighs four times as much and its later"
             " ones pull the figure up. The subquery collapses procedures"
             " to one row per admission before the join.",
        claims=[("eight wards, a day and a half or so each",
                 lambda rows, c: len(rows) == 8
                 and all(24 < r[1] < 48 for r in rows))],
    ),
    # ======================================== 2 Strings and sequences
    dict(
        id=4, ledger="Q755", concept="STR", tier="2 - Strings and sequences",
        title="Usernames that collide",
        prompt=(
            "A username is the staff member's name in lower case with the"
            " space replaced by a full stop: 'Xiu Chowdhury' becomes"
            " 'xiu.chowdhury'. Which usernames would belong to more than"
            " one person, and which staff_ids would share them -- as one"
            " comma-separated string in id order, such as '17,42'?\n\n"
            "Return: username, staff_ids"
        ),
        solution=("SELECT lower(replace(name, ' ', '.')),"
                  " group_concat(staff_id ORDER BY staff_id) FROM staff"
                  " GROUP BY 1 HAVING COUNT(*) > 1"),
        trap_sql=("SELECT lower(name), group_concat(staff_id ORDER BY staff_id)"
                  " FROM staff GROUP BY 1 HAVING COUNT(*) > 1"),
        note="replace(name, ' ', '.') swaps every space; lower() folds the"
             " case; and you can GROUP BY the expression -- or by its"
             " position, 1 -- without naming it. group_concat with ORDER BY"
             " inside the call fixes the order of the ids. The trap groups"
             " by the right thing but returns the wrong string: the question"
             " asks for the username, full stop included, not the name.",
        claims=[("three collisions, two ids each",
                 lambda rows, c: len(rows) == 3
                 and all(r[1].count(",") == 1 and "." in r[0]
                         and r[0] == r[0].lower() for r in rows))],
    ),
    dict(
        id=5, ledger="Q756", concept="STR", tier="2 - Strings and sequences",
        title="Leeds districts as numbers",
        prompt=(
            "Patients whose postcode area starts with LS, counted by the"
            " district NUMBER that follows the letters -- 'LS16' is"
            " district 16. Return the district as an integer, not text,"
            " so that it sorts as a number.\n\n"
            "Return: district, patients"
        ),
        solution=("SELECT CAST(substr(postcode_area, 3) AS INTEGER), COUNT(*)"
                  " FROM patients WHERE postcode_area LIKE 'LS%' GROUP BY 1"),
        trap_sql=("SELECT substr(postcode_area, 3), COUNT(*)"
                  " FROM patients WHERE postcode_area LIKE 'LS%' GROUP BY 1"),
        note="substr(x, 3) with no length runs to the end of the string,"
             " and returns TEXT: '16' sorts before '2' because '1' comes"
             " before '2'. CAST(... AS INTEGER) makes it a number, and the"
             " grader sees a different type in the column. LIKE 'LS%'"
             " matches the prefix; % is any run of characters.",
        claims=[("thirteen districts, all integers",
                 lambda rows, c: len(rows) == 13
                 and all(isinstance(r[0], int) for r in rows))],
    ),
    # ============================================== 3 Dates and times
    dict(
        id=6, ledger="Q757", concept="D1", tier="3 - Dates and times",
        title="In and out the same day",
        prompt=(
            "For each ward, by admitting ward: how many completed"
            " admissions it has had, how many of them were discharged on"
            " the same CALENDAR DAY they were admitted, and the percentage"
            " to one decimal.\n\n"
            "Return: ward_id, completed, same_day, pct"
        ),
        solution=("SELECT ward_id, COUNT(*), SUM(date(admitted_at) = date(discharged_at)),"
                  " ROUND(100.0 * SUM(date(admitted_at) = date(discharged_at))"
                  " / COUNT(*), 1) FROM admissions WHERE discharged_at IS NOT NULL"
                  " GROUP BY ward_id"),
        trap_sql=("SELECT ward_id, COUNT(*), SUM(julianday(discharged_at)"
                  " - julianday(admitted_at) < 1),"
                  " ROUND(100.0 * SUM(julianday(discharged_at)"
                  " - julianday(admitted_at) < 1) / COUNT(*), 1) FROM admissions"
                  " WHERE discharged_at IS NOT NULL GROUP BY ward_id"),
        note="'The same day' is about the calendar, not about 24 hours."
             " date() cuts a datetime to its day, and two equal days is"
             " the test. Under 24 hours is a different question: a patient"
             " admitted at 23:00 and out at 06:00 was in for seven hours"
             " across two days, and one admitted at 01:00 and out at 23:30"
             " was in for a whole day on one.",
        claims=[("eight wards, about a tenth same-day",
                 lambda rows, c: len(rows) == 8
                 and all(5 < r[3] < 15 for r in rows))],
    ),
    dict(
        id=7, ledger="Q758", concept="W3", tier="3 - Dates and times",
        title="The next admission",
        prompt=(
            "For admissions 1 to 10: when the same patient was NEXT"
            " admitted, and the days from this admission's discharge to"
            " that, to one decimal. NULL in both if there was no next"
            " admission; negative if the next one began before this one"
            " ended. LEAD is LAG's mirror.\n\n"
            "Return: admission_id, next_admitted_at, days_between"
        ),
        solution=("SELECT admission_id, nxt, ROUND(julianday(nxt)"
                  " - julianday(discharged_at), 1) FROM (SELECT admission_id,"
                  " discharged_at, LEAD(admitted_at) OVER (PARTITION BY patient_id"
                  " ORDER BY admitted_at) nxt FROM admissions)"
                  " WHERE admission_id <= 10"),
        trap_sql=("SELECT admission_id, nxt, ROUND(julianday(nxt)"
                  " - julianday(discharged_at), 1) FROM (SELECT admission_id,"
                  " discharged_at, LEAD(admitted_at) OVER (PARTITION BY patient_id"
                  " ORDER BY admitted_at) nxt FROM admissions WHERE admission_id <= 10)"),
        note="The window has to see the patient's WHOLE history, so the"
             " filter to admissions 1 to 10 goes OUTSIDE the subquery. Put"
             " it inside and LEAD only looks among those ten rows -- the"
             " next admission of patient 1103 is not one of them, so it"
             " reports none. Two of the ten overlap the admission that"
             " follows, which is the negative gap.",
        claims=[("ten rows, two with no next admission, one negative gap",
                 lambda rows, c: len(rows) == 10
                 and sum(r[1] is None for r in rows) == 2
                 and any(r[2] is not None and r[2] < 0 for r in rows))],
    ),
    # ==================================== 4 Intervals and occupancy
    dict(
        id=8, ledger="Q759", concept="INT", tier="4 - Intervals and occupancy",
        title="Already on the ward",
        prompt=(
            "For admissions 1 to 10: how many OTHER patients were on the"
            " admitting ward at the moment of admission -- ward_stays on"
            " that ward whose interval covers admitted_at, not counting"
            " this admission's own stay. A stay with no end is still"
            " running.\n\n"
            "Return: admission_id, ward_id, already_there"
        ),
        solution=("SELECT a.admission_id, a.ward_id, COUNT(s.admission_id)"
                  " FROM admissions a LEFT JOIN ward_stays s ON s.ward_id = a.ward_id"
                  " AND s.admission_id <> a.admission_id"
                  " AND s.from_at <= a.admitted_at"
                  " AND COALESCE(s.to_at, '9999') > a.admitted_at"
                  " WHERE a.admission_id <= 10 GROUP BY a.admission_id"),
        trap_sql=("SELECT a.admission_id, a.ward_id, COUNT(s.admission_id)"
                  " FROM admissions a LEFT JOIN ward_stays s ON s.ward_id = a.ward_id"
                  " AND s.from_at <= a.admitted_at"
                  " AND COALESCE(s.to_at, '9999') > a.admitted_at"
                  " WHERE a.admission_id <= 10 GROUP BY a.admission_id"),
        note="The admission's own first stay begins exactly at admitted_at,"
             " so it satisfies from_at <= admitted_at and counts itself"
             " unless excluded -- every answer one too high. A join"
             " condition can carry an inequality on the key as easily as"
             " an equality. LEFT JOIN with COUNT(s.admission_id) keeps an"
             " admission to an empty ward as 0.",
        claims=[("ten rows, a few patients each",
                 lambda rows, c: len(rows) == 10
                 and all(0 <= r[2] < 20 for r in rows))],
    ),
    dict(
        id=9, ledger="Q760", concept="INT", tier="4 - Intervals and occupancy",
        title="The longest time away",
        prompt=(
            "For patients with at least NINE admissions: the longest gap,"
            " in days to one decimal, between being discharged and next"
            " being admitted. Measure from the previous DISCHARGE, in"
            " admission order.\n\n"
            "Return: patient_id, longest_gap_days"
        ),
        solution=("SELECT patient_id, ROUND(MAX(gap), 1) FROM (SELECT patient_id,"
                  " julianday(admitted_at) - LAG(julianday(discharged_at)) OVER"
                  " (PARTITION BY patient_id ORDER BY admitted_at) gap"
                  " FROM admissions) GROUP BY patient_id HAVING COUNT(*) >= 9"),
        trap_sql=("SELECT patient_id, ROUND(MAX(gap), 1) FROM (SELECT patient_id,"
                  " julianday(admitted_at) - LAG(julianday(admitted_at)) OVER"
                  " (PARTITION BY patient_id ORDER BY admitted_at) gap"
                  " FROM admissions) GROUP BY patient_id HAVING COUNT(*) >= 9"),
        note="LAG of a DIFFERENT column than the one you subtract from:"
             " this admission's start minus the previous one's END. The"
             " trap measures start to start, which includes the previous"
             " stay and overstates every gap by its length. COUNT(*) in the"
             " HAVING counts the patient's admissions, and the NULL gap on"
             " the first row is ignored by MAX.",
        claims=[("about a hundred patients, gaps under two years",
                 lambda rows, c: 50 < len(rows) < 150
                 and all(0 < r[1] < 730 for r in rows))],
    ),
    dict(
        id=10, ledger="Q761", concept="INT", tier="4 - Intervals and occupancy",
        title="Days on a drug",
        prompt=(
            "For each drug, the total number of prescription-days as of"
            " 2026-06-30: each prescription contributes ended_on minus"
            " started_on in days, and a prescription with no end runs to"
            " 2026-06-30. Dates, not datetimes, so the answer is a whole"
            " number.\n\n"
            "Return: drug, days"
        ),
        solution=("SELECT d.name, CAST(SUM(julianday(COALESCE(p.ended_on, '2026-06-30'))"
                  " - julianday(p.started_on)) AS INTEGER) FROM prescriptions p"
                  " JOIN drugs d ON d.drug_id = p.drug_id GROUP BY d.name"),
        trap_sql=("SELECT d.name, CAST(SUM(julianday(p.ended_on)"
                  " - julianday(p.started_on)) AS INTEGER) FROM prescriptions p"
                  " JOIN drugs d ON d.drug_id = p.drug_id GROUP BY d.name"),
        note="SUM skips a NULL term, so without the COALESCE every open"
             " prescription contributes nothing and the drugs still being"
             " given are the ones undercounted. Supplying the snapshot as"
             " the end is the same move as in the interval questions"
             " before; here the ends are dates, so julianday of each is a"
             " whole number and so is the sum.",
        claims=[("forty drugs, hundreds of days each",
                 lambda rows, c: len(rows) == 40
                 and all(300 < r[1] < 1500 for r in rows))],
    ),
    # ============================================== 5 Joins and grain
    dict(
        id=11, ledger="Q762", concept="J2", tier="5 - Joins and grain",
        title="Operating off the rota",
        prompt=(
            "For each surgeon: how many procedures they have performed,"
            " and how many of those were on a day the surgeon had NO shift"
            " in the rota. shifts has one row per person per day, so"
            " match on staff and on date(performed_at).\n\n"
            "Return: surgeon_id, procedures, off_rota"
        ),
        solution=("SELECT p.surgeon_id, COUNT(*), SUM(sh.shift_id IS NULL)"
                  " FROM procedures p LEFT JOIN shifts sh ON sh.staff_id = p.surgeon_id"
                  " AND sh.shift_date = date(p.performed_at) GROUP BY p.surgeon_id"),
        trap_sql=("SELECT p.surgeon_id, COUNT(*), SUM(sh.shift_id IS NULL)"
                  " FROM procedures p LEFT JOIN shifts sh ON sh.staff_id = p.surgeon_id"
                  " WHERE sh.shift_date = date(p.performed_at) GROUP BY p.surgeon_id"),
        note="A LEFT JOIN keeps every procedure and leaves the shift"
             " columns NULL where there was no match -- and IS NULL on the"
             " right-hand key is then the count of non-matches. Move the"
             " date condition into WHERE and the NULL rows fail it, which"
             " turns the LEFT JOIN back into an inner one: off_rota is 0"
             " and the procedure counts drop to the matched ones.",
        claims=[("twenty-six surgeons, around two fifths off rota",
                 lambda rows, c: len(rows) == 26
                 and all(0.25 < r[2] / r[1] < 0.6 for r in rows))],
    ),
    dict(
        id=12, ledger="Q763", concept="E1", tier="5 - Joins and grain",
        title="Always routine",
        prompt=(
            "Patients with at least four admissions, EVERY one of which"
            " was routine priority, with their number of admissions.\n\n"
            "Return: patient_id, admissions"
        ),
        solution=("SELECT patient_id, COUNT(*) FROM admissions GROUP BY patient_id"
                  " HAVING COUNT(*) >= 4 AND SUM(priority <> 'routine') = 0"),
        trap_sql=("SELECT patient_id, COUNT(*) FROM admissions WHERE priority = 'routine'"
                  " GROUP BY patient_id HAVING COUNT(*) >= 4"),
        note="'Every admission was routine' means 'no admission was not"
             " routine', and SUM(priority <> 'routine') = 0 says exactly"
             " that. Filtering to routine in WHERE finds patients with four"
             " ROUTINE admissions, who may have had six urgent ones too."
             " NOT EXISTS against the same table is the other spelling;"
             " the aggregate one needs no second scan.",
        claims=[("a dozen or so patients, four to six admissions each",
                 lambda rows, c: 8 < len(rows) < 30
                 and all(4 <= r[1] <= 8 for r in rows))],
    ),
    dict(
        id=13, ledger="Q764", concept="C2", tier="5 - Joins and grain",
        title="How many hands on each ward",
        prompt=(
            "For each ward: how many shifts have been worked there, how"
            " many DIFFERENT staff have worked them, and shifts per person"
            " to one decimal.\n\n"
            "Return: ward_id, shifts, staff, per_person"
        ),
        solution=("SELECT ward_id, COUNT(*), COUNT(DISTINCT staff_id),"
                  " ROUND(1.0 * COUNT(*) / COUNT(DISTINCT staff_id), 1)"
                  " FROM shifts GROUP BY ward_id"),
        trap_sql=("SELECT ward_id, COUNT(*), COUNT(staff_id),"
                  " ROUND(1.0 * COUNT(*) / COUNT(staff_id), 1)"
                  " FROM shifts GROUP BY ward_id"),
        note="COUNT(staff_id) counts rows with a staff_id, which is every"
             " row, so it equals COUNT(*) and the ratio is 1.0 everywhere."
             " COUNT(DISTINCT staff_id) counts people. The 1.0 * keeps the"
             " division real; two integer counts divided give an integer.",
        claims=[("eight wards, dozens of staff on each",
                 lambda rows, c: len(rows) == 8
                 and all(30 < r[2] < 80 and 10 < r[3] < 80 for r in rows))],
    ),
    # ============================================== 6 Window functions
    dict(
        id=14, ledger="Q765", concept="DST", tier="6 - Window functions",
        title="Length of stay in quarters",
        prompt=(
            "Split the completed admissions into four equal groups by"
            " length of stay -- NTILE(4) ordered by the stay -- and for"
            " each group give the count and the shortest, longest and"
            " average stay in days, to two decimals.\n\n"
            "Return: quarter, admissions, shortest, longest, avg_days"
        ),
        solution=("SELECT q, COUNT(*), ROUND(MIN(los), 2), ROUND(MAX(los), 2),"
                  " ROUND(AVG(los), 2) FROM (SELECT NTILE(4) OVER (ORDER BY los) q, los"
                  " FROM (SELECT julianday(discharged_at) - julianday(admitted_at) los"
                  " FROM admissions WHERE discharged_at IS NOT NULL)) GROUP BY q"),
        trap_sql=("SELECT q, COUNT(*), ROUND(MIN(los), 2), ROUND(MAX(los), 2),"
                  " ROUND(AVG(los), 2) FROM (SELECT NTILE(4) OVER (ORDER BY admitted_at) q,"
                  " julianday(discharged_at) - julianday(admitted_at) los"
                  " FROM admissions WHERE discharged_at IS NOT NULL) GROUP BY q"),
        note="NTILE(n) deals the rows into n groups of equal size in the"
             " window's ORDER, so the order IS the question: by length of"
             " stay, the first quarter is the shortest quarter. Ordered by"
             " admission date, the groups are four spans of time and say"
             " nothing about the stays. The subquery computes the stay"
             " once so the window and the aggregates share it.",
        claims=[("four quarters of equal size, each longer than the last",
                 lambda rows, c: len(rows) == 4
                 and max(r[1] for r in rows) - min(r[1] for r in rows) <= 1
                 and [r[4] for r in sorted(rows)] == sorted(r[4] for r in rows))],
    ),
    dict(
        id=15, ledger="Q766", concept="W2", tier="6 - Window functions",
        title="Each ward's busiest month",
        prompt=(
            "For each ward, the month -- 'YYYY-MM' of admitted_at -- in"
            " which it took the most admissions, with the count. If two"
            " months tie, the EARLIER one.\n\n"
            "Return: ward_id, month, admissions"
        ),
        solution=("SELECT ward_id, month, n FROM (SELECT ward_id, month, n,"
                  " ROW_NUMBER() OVER (PARTITION BY ward_id ORDER BY n DESC, month) rn"
                  " FROM (SELECT ward_id, strftime('%Y-%m', admitted_at) month, COUNT(*) n"
                  " FROM admissions GROUP BY 1, 2)) WHERE rn = 1"),
        trap_sql=("SELECT ward_id, month, n FROM (SELECT ward_id, month, n,"
                  " ROW_NUMBER() OVER (PARTITION BY ward_id ORDER BY n DESC, month) rn"
                  " FROM (SELECT ward_id, strftime('%m', admitted_at) month, COUNT(*) n"
                  " FROM admissions GROUP BY 1, 2)) WHERE rn = 1"),
        note="Aggregate first -- one row per ward and month -- then rank"
             " those rows within each ward and keep the first. The tiebreak"
             " on month is part of the answer. The trap keys the month on"
             " '%m' alone, so May 2025 and May 2026 are one bucket: the"
             " counts double up and the answer names a month of the year,"
             " not a month. Eighteen months of data need the year in the"
             " key.",
        claims=[("eight wards, each with a 'YYYY-MM' month",
                 lambda rows, c: len(rows) == 8
                 and all(len(r[1]) == 7 and r[1][4] == '-' for r in rows))],
    ),
    # ============================================= 7 Changing the data
    dict(
        id=16, ledger="Q767", concept="DDL", tier="7 - Changing the data",
        kind="script",
        title="Fill in what was left out",
        prompt=(
            "Create `ward_rounds (round_id INTEGER PRIMARY KEY, ward_id"
            " INTEGER NOT NULL referencing wards, held_on TEXT NOT NULL,"
            " start_time TEXT NOT NULL, attendees INTEGER NOT NULL)` so that"
            " an insert giving only a ward_id succeeds, with held_on"
            " '2026-07-01', start_time '08:00' and attendees 0 filled in"
            " by the table. After your script, the question inserts a"
            " round for ward 3 giving nothing else, and one for ward 5"
            " giving a start_time of '14:00'.\n\n"
            "Checked: the four value columns of each round"
        ),
        solution=("CREATE TABLE ward_rounds (\n"
                  "  round_id   INTEGER PRIMARY KEY,\n"
                  "  ward_id    INTEGER NOT NULL REFERENCES wards(ward_id),\n"
                  "  held_on    TEXT    NOT NULL DEFAULT '2026-07-01',\n"
                  "  start_time TEXT    NOT NULL DEFAULT '08:00',\n"
                  "  attendees  INTEGER NOT NULL DEFAULT 0\n"
                  ");"),
        trap_sql=("CREATE TABLE ward_rounds (\n"
                  "  round_id   INTEGER PRIMARY KEY,\n"
                  "  ward_id    INTEGER NOT NULL REFERENCES wards(ward_id),\n"
                  "  held_on    TEXT    NOT NULL,\n"
                  "  start_time TEXT    NOT NULL,\n"
                  "  attendees  INTEGER NOT NULL\n"
                  ");"),
        driver_sql=("INSERT INTO ward_rounds (ward_id) VALUES (3);\n"
                    "INSERT INTO ward_rounds (ward_id, start_time) VALUES (5, '14:00');"),
        probe_sql=("SELECT ward_id, held_on, start_time, attendees FROM ward_rounds"
                   " ORDER BY round_id"),
        note="A DEFAULT is what a column takes when an INSERT leaves it"
             " out. Without one, NOT NULL makes the column mandatory and"
             " both inserts are refused -- the probe finds an empty table."
             " A given value always wins over the default, as 14:00 does."
             " The default can be an expression in parentheses, such as"
             " DEFAULT (date('now')), and CURRENT_DATE is allowed bare.",
        claims=[("two rounds, the defaults on one and the override on the other",
                 lambda rows, c: rows == [(3, '2026-07-01', '08:00', 0),
                                          (5, '2026-07-01', '14:00', 0)])],
    ),
    dict(
        id=17, ledger="Q768", concept="DDL", tier="7 - Changing the data",
        kind="script",
        title="Unique whatever the case",
        prompt=(
            "Create `ward_tags (tag_id INTEGER PRIMARY KEY, tag TEXT NOT"
            " NULL)` where a tag must be unique REGARDLESS OF CASE --"
            " 'Isolation' and 'isolation' are the same tag. A collation"
            " does it. After your script, the question inserts 'Isolation',"
            " 'isolation', 'ISOLATION' and 'Bariatric', in that order.\n\n"
            "Checked: the tags that survive, in insertion order"
        ),
        solution=("CREATE TABLE ward_tags (\n"
                  "  tag_id INTEGER PRIMARY KEY,\n"
                  "  tag    TEXT NOT NULL COLLATE NOCASE UNIQUE\n"
                  ");"),
        trap_sql=("CREATE TABLE ward_tags (\n"
                  "  tag_id INTEGER PRIMARY KEY,\n"
                  "  tag    TEXT NOT NULL UNIQUE\n"
                  ");"),
        driver_sql=("INSERT INTO ward_tags (tag) VALUES ('Isolation');\n"
                    "INSERT INTO ward_tags (tag) VALUES ('isolation');\n"
                    "INSERT INTO ward_tags (tag) VALUES ('ISOLATION');\n"
                    "INSERT INTO ward_tags (tag) VALUES ('Bariatric');"),
        probe_sql="SELECT tag FROM ward_tags ORDER BY tag_id",
        note="A column's collation decides what counts as equal for that"
             " column: in comparisons, in ORDER BY, and in a UNIQUE"
             " constraint. COLLATE NOCASE folds ASCII case, so the second"
             " and third inserts are duplicates of the first and are"
             " refused. A plain UNIQUE is BINARY and keeps all three. The"
             " same clause can go on the index instead: CREATE UNIQUE"
             " INDEX ... ON ward_tags (tag COLLATE NOCASE).",
        claims=[("two tags survive of four",
                 lambda rows, c: rows == [('Isolation',), ('Bariatric',)])],
    ),
    dict(
        id=18, ledger="Q769", concept="DDL", tier="7 - Changing the data",
        kind="script",
        title="The booking outlives the theatre",
        prompt=(
            "Create `theatres (theatre_no INTEGER PRIMARY KEY, name TEXT NOT"
            " NULL)` with rows 1, 2 and 3 (any names), and `theatre_bookings"
            " (booking_id INTEGER PRIMARY KEY, theatre_no INTEGER referencing"
            " theatres, booked_for TEXT NOT NULL)` with bookings 1 to 4 for"
            " theatres 1, 2, 2 and 3 (any text). Deleting a theatre must"
            " KEEP its bookings and blank their theatre_no. After your"
            " script, the question deletes theatre 2.\n\n"
            "Checked: each booking's theatre_no"
        ),
        solution=("CREATE TABLE theatres (\n"
                  "  theatre_no INTEGER PRIMARY KEY,\n"
                  "  name       TEXT NOT NULL\n"
                  ");\n"
                  "CREATE TABLE theatre_bookings (\n"
                  "  booking_id INTEGER PRIMARY KEY,\n"
                  "  theatre_no INTEGER REFERENCES theatres(theatre_no) ON DELETE SET NULL,\n"
                  "  booked_for TEXT NOT NULL\n"
                  ");\n"
                  "INSERT INTO theatres VALUES (1, 'Main'), (2, 'Day case'), (3, 'Cardiac');\n"
                  "INSERT INTO theatre_bookings (theatre_no, booked_for)\n"
                  "VALUES (1, 'hip'), (2, 'cataract'), (2, 'hernia'), (3, 'bypass');"),
        trap_sql=("CREATE TABLE theatres (\n"
                  "  theatre_no INTEGER PRIMARY KEY,\n"
                  "  name       TEXT NOT NULL\n"
                  ");\n"
                  "CREATE TABLE theatre_bookings (\n"
                  "  booking_id INTEGER PRIMARY KEY,\n"
                  "  theatre_no INTEGER REFERENCES theatres(theatre_no),\n"
                  "  booked_for TEXT NOT NULL\n"
                  ");\n"
                  "INSERT INTO theatres VALUES (1, 'Main'), (2, 'Day case'), (3, 'Cardiac');\n"
                  "INSERT INTO theatre_bookings (theatre_no, booked_for)\n"
                  "VALUES (1, 'hip'), (2, 'cataract'), (2, 'hernia'), (3, 'bypass');"),
        driver_sql="DELETE FROM theatres WHERE theatre_no = 2;",
        probe_sql="SELECT booking_id, theatre_no FROM theatre_bookings ORDER BY 1",
        note="ON DELETE has five answers: NO ACTION and RESTRICT refuse the"
             " delete while children exist, CASCADE deletes the children"
             " too, SET NULL keeps them and blanks the key, SET DEFAULT"
             " points them at the column's default. The trap is the"
             " default, NO ACTION, so the delete is refused and both"
             " bookings still say theatre 2. SET NULL needs the column to"
             " allow NULL, which is why theatre_no is not NOT NULL.",
        claims=[("two bookings orphaned, two untouched",
                 lambda rows, c: rows == [(1, 1), (2, None), (3, None), (4, 3)])],
    ),
    dict(
        id=19, ledger="Q770", concept="DDL", tier="7 - Changing the data",
        kind="script",
        title="One row per bed, no rowid",
        prompt=(
            "Create `bed_state (ward_id INTEGER NOT NULL referencing wards,"
            " bed_no INTEGER NOT NULL, admission_id INTEGER referencing"
            " admissions, PRIMARY KEY (ward_id, bed_no))` as a WITHOUT"
            " ROWID table, and fill it with one row per bed of every ward --"
            " bed_no 1 up to the ward's beds -- with admission_id NULL. A"
            " recursive CTE can count to each ward's beds.\n\n"
            "Checked: whether the table is WITHOUT ROWID, the row count,"
            " the highest bed number on ward 5, and how many beds are taken"
        ),
        solution=("CREATE TABLE bed_state (\n"
                  "  ward_id      INTEGER NOT NULL REFERENCES wards(ward_id),\n"
                  "  bed_no       INTEGER NOT NULL,\n"
                  "  admission_id INTEGER REFERENCES admissions(admission_id),\n"
                  "  PRIMARY KEY (ward_id, bed_no)\n"
                  ") WITHOUT ROWID;\n"
                  "WITH RECURSIVE b(ward_id, bed_no, beds) AS (\n"
                  "  SELECT ward_id, 1, beds FROM wards\n"
                  "  UNION ALL\n"
                  "  SELECT ward_id, bed_no + 1, beds FROM b WHERE bed_no < beds\n"
                  ")\n"
                  "INSERT INTO bed_state (ward_id, bed_no)\n"
                  "SELECT ward_id, bed_no FROM b;"),
        trap_sql=("CREATE TABLE bed_state (\n"
                  "  ward_id      INTEGER NOT NULL REFERENCES wards(ward_id),\n"
                  "  bed_no       INTEGER NOT NULL,\n"
                  "  admission_id INTEGER REFERENCES admissions(admission_id),\n"
                  "  PRIMARY KEY (ward_id, bed_no)\n"
                  ");\n"
                  "WITH RECURSIVE b(ward_id, bed_no, beds) AS (\n"
                  "  SELECT ward_id, 1, beds FROM wards\n"
                  "  UNION ALL\n"
                  "  SELECT ward_id, bed_no + 1, beds FROM b WHERE bed_no < beds\n"
                  ")\n"
                  "INSERT INTO bed_state (ward_id, bed_no)\n"
                  "SELECT ward_id, bed_no FROM b;"),
        probe_sql=("SELECT (SELECT sql LIKE '%WITHOUT ROWID%' FROM sqlite_master"
                   " WHERE name = 'bed_state'), (SELECT COUNT(*) FROM bed_state),"
                   " (SELECT MAX(bed_no) FROM bed_state WHERE ward_id = 5),"
                   " (SELECT COUNT(*) FROM bed_state WHERE admission_id IS NOT NULL)"),
        note="Every ordinary SQLite table has a hidden rowid, and a"
             " composite PRIMARY KEY is just a unique index beside it."
             " WITHOUT ROWID makes the key the table's own storage order,"
             " which is smaller and faster to look up by (ward_id, bed_no)"
             " -- the one rule is that a WITHOUT ROWID table MUST declare a"
             " PRIMARY KEY, and SELECT rowid from it is an error. The"
             " recursive CTE counts from 1 to beds separately for each"
             " ward, because each row carries its own limit.",
        claims=[("184 beds, none taken, ward 5 numbered to 16",
                 lambda rows, c: rows == [(1, c.execute(
                     "SELECT SUM(beds) FROM wards").fetchone()[0], 16, 0)])],
    ),
    dict(
        id=20, ledger="Q771", concept="DDL", tier="7 - Changing the data",
        kind="script",
        title="Renamed, and still referenced",
        prompt=(
            "Rename the table `procedure_types` to `procedure_catalogue`,"
            " and its column `tariff_pence` to `price_pence`, with ALTER"
            " TABLE -- so that the rows, the primary key and the foreign"
            " key from procedures all carry over. Do not rebuild the"
            " table.\n\n"
            "Checked: whether price_pence exists, how many procedures still"
            " join to the catalogue by code, and whether the old name is gone"
        ),
        solution=("ALTER TABLE procedure_types RENAME TO procedure_catalogue;\n"
                  "ALTER TABLE procedure_catalogue RENAME COLUMN tariff_pence TO price_pence;"),
        trap_sql=("CREATE TABLE procedure_catalogue AS\n"
                  "SELECT code, name, category, tariff_pence AS price_pence"
                  " FROM procedure_types;\n"
                  "DROP TABLE procedure_types;"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM pragma_table_info('procedure_catalogue')"
                   " WHERE name = 'price_pence'), (SELECT COUNT(*) FROM procedures p"
                   " JOIN procedure_catalogue c ON c.code = p.code),"
                   " (SELECT COUNT(*) FROM sqlite_master WHERE name = 'procedure_types')"),
        note="RENAME TO and RENAME COLUMN rewrite the schema in place: the"
             " data, the key and the indexes stay, and every foreign key"
             " that pointed at the old name is updated to the new one."
             " Rebuilding by copy-and-drop loses the primary key -- CTAS"
             " copies none -- and the DROP is refused anyway, because"
             " procedures still references procedure_types and foreign"
             " keys are on. ADD COLUMN and DROP COLUMN are the other two"
             " things ALTER TABLE can do here.",
        claims=[("the column renamed, every procedure still joined, the old name gone",
                 lambda rows, c: rows == [(1, c.execute(
                     "SELECT COUNT(*) FROM procedures").fetchone()[0], 0)])],
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
