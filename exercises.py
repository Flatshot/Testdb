"""Practice exercises: fifteen questions on the hospital schema.

The fourth set on the district hospital, beside the third Python set
(pyexercises.py), and a step EASIER than the three before it -- the same
seven stages, one or two questions each, with the lesson of each question
sitting closer to the surface. Same data as before: SEED 731, not
re-seeded. Twelve SELECT questions -- the price list by category, HAVING
on a count, substr() from 1, the second stay of an admission, a year as a
number, julianday() for a length, what was running on one day, stays that
touched a weekend, a NULL that = cannot find, a manager who may not exist,
ROW_NUMBER, a share of the whole -- and three WRITABLE questions, graded on
the state of the database after your script runs:

  * an UPDATE with arithmetic and a WHERE
  * ALTER TABLE ... DROP COLUMN
  * DROP INDEX and CREATE INDEX: replacing one index with another

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference.
"""

import sqlite3

EXERCISES = [
    # ========================================================== 1 Warm-up
    dict(
        id=1, ledger="Q772", concept="A2", tier="1 - Warm-up",
        title="The price list",
        prompt=(
            "One row per category in procedure_types -- the catalogue of"
            " what CAN be done, not the procedures performed: the"
            " cheapest, the dearest and the average tariff of the types"
            " listed, in POUNDS to two decimals. Tariffs are stored in"
            " pence.\n\n"
            "Return: category, cheapest, dearest, average"
        ),
        solution=("SELECT category, ROUND(MIN(tariff_pence) / 100.0, 2),"
                  " ROUND(MAX(tariff_pence) / 100.0, 2), ROUND(AVG(tariff_pence) / 100.0, 2)"
                  " FROM procedure_types GROUP BY category"),
        trap_sql=("SELECT t.category, ROUND(MIN(t.tariff_pence) / 100.0, 2),"
                  " ROUND(MAX(t.tariff_pence) / 100.0, 2), ROUND(AVG(t.tariff_pence) / 100.0, 2)"
                  " FROM procedures p JOIN procedure_types t ON t.code = p.code"
                  " GROUP BY t.category"),
        note="Read the question for WHICH table answers it. The catalogue"
             " has ten types per category; the procedures table has"
             " fifteen hundred rows per category, one per operation"
             " performed, and joining to it averages those -- a tariff"
             " performed often counts many times. The min and max happen"
             " to agree either way; the average does not. / 100.0 keeps"
             " the pounds real.",
        claims=[("three categories, the average between the ends",
                 lambda rows, c: len(rows) == 3
                 and all(r[1] < r[3] < r[2] for r in rows))],
    ),
    dict(
        id=2, ledger="Q773", concept="A3", tier="1 - Warm-up",
        title="The most prescribed",
        prompt=(
            "Drugs that have been prescribed more than 330 times, with the"
            " count. The condition is on the count, so it cannot go in"
            " WHERE.\n\n"
            "Return: drug, prescriptions"
        ),
        solution=("SELECT d.name, COUNT(*) FROM prescriptions p"
                  " JOIN drugs d ON d.drug_id = p.drug_id"
                  " GROUP BY d.name HAVING COUNT(*) > 330"),
        trap_sql=("SELECT d.name, COUNT(*) FROM prescriptions p"
                  " JOIN drugs d ON d.drug_id = p.drug_id"
                  " WHERE COUNT(*) > 330 GROUP BY d.name"),
        note="WHERE runs before the rows are grouped, so there is no count"
             " yet to test -- SQLite refuses it with 'misuse of aggregate'."
             " HAVING runs after GROUP BY and is where a condition on an"
             " aggregate lives. Only four drugs pass 330; the least"
             " prescribed has 263.",
        claims=[("four drugs, one of them Fentanyl",
                 lambda rows, c: len(rows) == 4
                 and any(r[0] == 'Fentanyl' for r in rows)
                 and all(r[1] > 330 for r in rows))],
    ),
    # ======================================== 2 Strings and sequences
    dict(
        id=3, ledger="Q774", concept="STR", tier="2 - Strings and sequences",
        title="Three-letter ward codes",
        prompt=(
            "Every ward with a code made from the first three letters of"
            " its name in upper case -- 'Nightingale' gives 'NIG'."
            " substr(text, start, length) counts from 1.\n\n"
            "Return: ward_id, name, code"
        ),
        solution="SELECT ward_id, name, upper(substr(name, 1, 3)) FROM wards",
        trap_sql="SELECT ward_id, name, upper(substr(name, 0, 3)) FROM wards",
        note="SQL strings start at position 1, not 0. substr(name, 0, 3)"
             " asks for three characters starting one BEFORE the first,"
             " and SQLite quietly returns the two that exist -- 'NI'. Off"
             " by one at the start of a string is the commonest substr"
             " mistake for anyone coming from Python.",
        claims=[("eight wards, three-letter upper-case codes",
                 lambda rows, c: len(rows) == 8
                 and all(len(r[2]) == 3 and r[2] == r[2].upper() for r in rows))],
    ),
    dict(
        id=4, ledger="Q775", concept="SEQ", tier="2 - Strings and sequences",
        title="Where the second stay was",
        prompt=(
            "For each ward, how many admissions had their SECOND stay"
            " there -- stay_seq exactly 2 in ward_stays. A third stay does"
            " not count.\n\n"
            "Return: ward_id, second_stays"
        ),
        solution="SELECT ward_id, COUNT(*) FROM ward_stays WHERE stay_seq = 2 GROUP BY ward_id",
        trap_sql="SELECT ward_id, COUNT(*) FROM ward_stays WHERE stay_seq >= 2 GROUP BY ward_id",
        note="stay_seq numbers the stays of one admission from 1, so 'the"
             " second stay' is a plain equality. >= 2 takes in every later"
             " stay as well, and some admissions have three. The filter"
             " goes in WHERE because it is on a column, not on the count.",
        claims=[("eight wards, a couple of hundred second stays each",
                 lambda rows, c: len(rows) == 8
                 and all(150 < r[1] < 300 for r in rows))],
    ),
    # ============================================== 3 Dates and times
    dict(
        id=5, ledger="Q776", concept="D1", tier="3 - Dates and times",
        title="Admissions by year",
        prompt=(
            "How many admissions there were in each year, with the year as"
            " a NUMBER. strftime('%Y', ...) gives the year as text.\n\n"
            "Return: year, admissions"
        ),
        solution=("SELECT CAST(strftime('%Y', admitted_at) AS INTEGER), COUNT(*)"
                  " FROM admissions GROUP BY 1"),
        trap_sql="SELECT strftime('%Y', admitted_at), COUNT(*) FROM admissions GROUP BY 1",
        note="strftime returns TEXT, and '2025' is not the number 2025 --"
             " it compares and sorts as a string, and the grader sees a"
             " different type. CAST(... AS INTEGER) converts it. GROUP BY"
             " 1 groups by the first output column, so the expression is"
             " written once.",
        claims=[("two years, both integers",
                 lambda rows, c: len(rows) == 2
                 and {r[0] for r in rows} == {2025, 2026})],
    ),
    dict(
        id=6, ledger="Q777", concept="D1", tier="3 - Dates and times",
        title="How long admissions 1 to 5 lasted",
        prompt=(
            "For admissions 1 to 5, the length of stay in days to one"
            " decimal: discharged_at minus admitted_at. They are text, so"
            " turn each into a number of days with julianday() before"
            " subtracting.\n\n"
            "Return: admission_id, days"
        ),
        solution=("SELECT admission_id, ROUND(julianday(discharged_at)"
                  " - julianday(admitted_at), 1) FROM admissions WHERE admission_id <= 5"),
        trap_sql=("SELECT admission_id, ROUND(discharged_at - admitted_at, 1)"
                  " FROM admissions WHERE admission_id <= 5"),
        note="Subtracting two datetime strings does not error: SQLite"
             " converts each to a number by reading the leading digits, so"
             " '2026-04-02 00:19' becomes 2026, and 2026 - 2026 is 0."
             " julianday() turns the whole datetime into a count of days"
             " with a fraction for the time, and the difference of two is"
             " a length in days.",
        claims=[("five admissions, all under a week",
                 lambda rows, c: len(rows) == 5
                 and all(0 < r[1] < 7 for r in rows))],
    ),
    # ==================================== 4 Intervals and occupancy
    dict(
        id=7, ledger="Q778", concept="INT", tier="4 - Intervals and occupancy",
        title="Running on the last Sunday",
        prompt=(
            "For each drug that had at least one, how many prescriptions"
            " were running on 2026-06-28: started on or before that day"
            " and not ended before it. A prescription with no end date is"
            " still running.\n\n"
            "Return: drug, running"
        ),
        solution=("SELECT d.name, COUNT(*) FROM prescriptions p"
                  " JOIN drugs d ON d.drug_id = p.drug_id"
                  " WHERE p.started_on <= '2026-06-28'"
                  " AND COALESCE(p.ended_on, '9999') >= '2026-06-28' GROUP BY d.name"),
        trap_sql=("SELECT d.name, COUNT(*) FROM prescriptions p"
                  " JOIN drugs d ON d.drug_id = p.drug_id"
                  " WHERE p.started_on <= '2026-06-28'"
                  " AND p.ended_on >= '2026-06-28' GROUP BY d.name"),
        note="A day inside an interval: start <= day AND end >= day. An"
             " open prescription has a NULL end, and NULL >= '2026-06-28'"
             " is not true, so the trap drops every course still running"
             " -- the ones most likely to be running on that day."
             " COALESCE gives the comparison a value to work with; '9999'"
             " is later than any real date.",
        claims=[("most drugs, a few running each",
                 lambda rows, c: 20 < len(rows) <= 40
                 and all(0 < r[1] < 10 for r in rows))],
    ),
    dict(
        id=8, ledger="Q779", concept="INT", tier="4 - Intervals and occupancy",
        title="Touching the last weekend",
        prompt=(
            "For each ward, how many ward stays overlapped the weekend of"
            " 2026-06-27 and 2026-06-28 at all -- began before the weekend"
            " ended and had not ended before it began. An open stay has"
            " not ended.\n\n"
            "Return: ward_id, stays"
        ),
        solution=("SELECT ward_id, COUNT(*) FROM ward_stays"
                  " WHERE from_at < '2026-06-29' AND COALESCE(to_at, '9999') > '2026-06-27'"
                  " GROUP BY ward_id"),
        trap_sql=("SELECT ward_id, COUNT(*) FROM ward_stays"
                  " WHERE from_at >= '2026-06-27' AND from_at < '2026-06-29'"
                  " GROUP BY ward_id"),
        note="Two intervals overlap when each starts before the other"
             " ends: the stay started before Monday, and the weekend"
             " started before the stay ended. The trap only counts stays"
             " that BEGAN on the weekend and misses everyone already on"
             " the ward on Friday night. '2026-06-27' as a bare date is"
             " midnight at the start of Saturday.",
        claims=[("eight wards, more than the starts alone",
                 lambda rows, c: len(rows) == 8
                 and sum(r[1] for r in rows) > c.execute(
                     "SELECT COUNT(*) FROM ward_stays WHERE from_at >= '2026-06-27'"
                     " AND from_at < '2026-06-29'").fetchone()[0])],
    ),
    # ============================================== 5 Joins and grain
    dict(
        id=9, ledger="Q780", concept="C7", tier="5 - Joins and grain",
        title="Blood group unknown",
        prompt=(
            "For each admitting ward, how many admissions were of a"
            " patient whose blood group is not recorded -- NULL in"
            " patients.\n\n"
            "Return: ward_id, admissions"
        ),
        solution=("SELECT a.ward_id, COUNT(*) FROM admissions a"
                  " JOIN patients p ON p.patient_id = a.patient_id"
                  " WHERE p.blood_group IS NULL GROUP BY a.ward_id"),
        trap_sql=("SELECT a.ward_id, COUNT(*) FROM admissions a"
                  " JOIN patients p ON p.patient_id = a.patient_id"
                  " WHERE p.blood_group = NULL GROUP BY a.ward_id"),
        note="Nothing equals NULL, not even NULL: blood_group = NULL is"
             " never true, so the trap returns no rows at all. IS NULL is"
             " the test, and IS NOT NULL its opposite. The join is by"
             " patient, and the count is of admissions, so a patient"
             " admitted three times counts three.",
        claims=[("eight wards, about a hundred each",
                 lambda rows, c: len(rows) == 8
                 and all(50 < r[1] < 150 for r in rows))],
    ),
    dict(
        id=10, ledger="Q781", concept="J2", tier="5 - Joins and grain",
        title="Who each person reports to",
        prompt=(
            "Staff 1 to 10 with the NAME of the person they report to. The"
            " four division heads report to nobody, and must still appear,"
            " with NULL for the manager.\n\n"
            "Return: staff_id, name, manager"
        ),
        solution=("SELECT s.staff_id, s.name, m.name FROM staff s"
                  " LEFT JOIN staff m ON m.staff_id = s.reports_to"
                  " WHERE s.staff_id <= 10"),
        trap_sql=("SELECT s.staff_id, s.name, m.name FROM staff s"
                  " JOIN staff m ON m.staff_id = s.reports_to"
                  " WHERE s.staff_id <= 10"),
        note="The table joined to itself, under two aliases: s is the"
             " person, m is their manager, matched by reports_to. An inner"
             " join drops anyone whose reports_to is NULL, because NULL"
             " matches no staff_id -- the four heads vanish. LEFT JOIN"
             " keeps them with NULL on the manager side.",
        claims=[("ten staff, four with no manager",
                 lambda rows, c: len(rows) == 10
                 and sum(r[2] is None for r in rows) == 4)],
    ),
    # ============================================== 6 Window functions
    dict(
        id=11, ledger="Q782", concept="W2", tier="6 - Window functions",
        title="Patient 1500's admissions, numbered",
        prompt=(
            "Every admission of patient 1500 -- the most admitted patient"
            " -- numbered 1, 2, 3 ... in the order they happened. Ids are"
            " not in time order, so number by admitted_at.\n\n"
            "Return: n, admission_id, admitted_at"
        ),
        solution=("SELECT ROW_NUMBER() OVER (ORDER BY admitted_at), admission_id,"
                  " admitted_at FROM admissions WHERE patient_id = 1500"),
        trap_sql=("SELECT ROW_NUMBER() OVER (ORDER BY admission_id), admission_id,"
                  " admitted_at FROM admissions WHERE patient_id = 1500"),
        note="ROW_NUMBER() hands out 1, 2, 3 in the order the OVER clause"
             " names, which need not be the order the rows are shown in."
             " Ordered by admission_id it numbers by when the row was"
             " created, and this patient's ids were dealt out of order --"
             " the first admission has id 2415. The window is the only"
             " place the numbering order is decided.",
        claims=[("eighteen admissions, numbered 1 to 18",
                 lambda rows, c: len(rows) == 18
                 and sorted(r[0] for r in rows) == list(range(1, 19)))],
    ),
    dict(
        id=12, ledger="Q783", concept="W3", tier="6 - Window functions",
        title="Each ward's share of the beds",
        prompt=(
            "Every ward with its beds and what percentage of ALL the"
            " hospital's beds that is, to one decimal. A window SUM with"
            " an empty OVER () gives the total on every row.\n\n"
            "Return: ward_id, beds, pct_of_beds"
        ),
        solution=("SELECT ward_id, beds, ROUND(100.0 * beds / SUM(beds) OVER (), 1)"
                  " FROM wards"),
        trap_sql=("SELECT ward_id, beds, ROUND(100 * beds / SUM(beds) OVER (), 1)"
                  " FROM wards"),
        note="SUM(beds) OVER () is the total of the whole table, repeated"
             " on each row, with no GROUP BY collapsing anything -- that"
             " is what makes a share possible in one query. 100 * beds"
             " and the SUM are both integers, so their division is an"
             " integer too, and 12.0 becomes 11. One real number in the"
             " expression -- 100.0 -- keeps the fraction.",
        claims=[("eight wards, shares adding to 100",
                 lambda rows, c: len(rows) == 8
                 and abs(sum(r[2] for r in rows) - 100) < 0.5)],
    ),
    # ============================================= 7 Changing the data
    dict(
        id=13, ledger="Q784", concept="DML", tier="7 - Changing the data",
        kind="script",
        title="A rise for the porters",
        prompt=(
            "Give every porter a 5 per cent rise, rounded to the nearest"
            " whole pound, and nobody else anything. One UPDATE.\n\n"
            "Checked: the total salary of each role"
        ),
        solution=("UPDATE staff SET salary = ROUND(salary * 1.05)"
                  " WHERE role = 'porter';"),
        trap_sql="UPDATE staff SET salary = ROUND(salary * 1.05);",
        probe_sql="SELECT role, CAST(SUM(salary) AS INTEGER) FROM staff GROUP BY role",
        note="An UPDATE without a WHERE changes EVERY row, silently and"
             " without asking -- here, the whole payroll. The WHERE is the"
             " part to write first. The SET can use the column's own"
             " current value, so salary * 1.05 reads the old salary and"
             " writes the new one in a single statement.",
        claims=[("porters up by a twentieth, everyone else unchanged",
                 lambda rows, c: dict(rows)['porter'] == round(
                     c.execute("SELECT SUM(ROUND(salary))"
                               " FROM staff WHERE role = 'porter'").fetchone()[0])
                 and dict(rows)['nurse'] == c.execute(
                     "SELECT SUM(salary) FROM staff WHERE role = 'nurse'").fetchone()[0])],
    ),
    dict(
        id=14, ledger="Q785", concept="ALT", tier="7 - Changing the data",
        kind="script",
        title="A column nobody needs",
        prompt=(
            "Remove the `floor` column from wards -- the column itself, not"
            " its values -- leaving the other four columns and all eight"
            " rows as they are.\n\n"
            "Checked: the columns of wards, in order, and its row count"
        ),
        solution="ALTER TABLE wards DROP COLUMN floor;",
        trap_sql="UPDATE wards SET floor = 0;",
        probe_sql=("SELECT (SELECT group_concat(name) FROM (SELECT name FROM"
                   " pragma_table_info('wards') ORDER BY cid)),"
                   " (SELECT COUNT(*) FROM wards)"),
        note="ALTER TABLE ... DROP COLUMN removes the column from the"
             " definition and from every row. Setting its values to 0 or"
             " NULL leaves the column in place, and a NOT NULL column"
             " will not even take the NULL. DROP COLUMN refuses a column"
             " that is part of a key, an index or a constraint; the"
             " rebuild dance is for those.",
        claims=[("four columns left, eight rows",
                 lambda rows, c: rows == [('ward_id,name,specialty,beds', 8)])],
    ),
    dict(
        id=15, ledger="Q786", concept="IDX", tier="7 - Changing the data",
        kind="script",
        title="Swap one index for another",
        prompt=(
            "observations has an index `idx_obs_taken` on taken_at alone."
            " Replace it: drop that index, and create `idx_obs_by` on"
            " (taken_by, taken_at), so that a lookup by the nurse and then"
            " by time can use it. The other index on the table stays.\n\n"
            "Checked: the names of the table's indexes, and the columns of"
            " idx_obs_by in order"
        ),
        solution=("DROP INDEX idx_obs_taken;\n"
                  "CREATE INDEX idx_obs_by ON observations (taken_by, taken_at);"),
        trap_sql="CREATE INDEX idx_obs_by ON observations (taken_by, taken_at);",
        probe_sql=("SELECT (SELECT group_concat(name) FROM (SELECT name FROM"
                   " pragma_index_list('observations') ORDER BY name)),"
                   " (SELECT group_concat(name) FROM (SELECT name FROM"
                   " pragma_index_info('idx_obs_by') ORDER BY seqno))"),
        note="An index costs space and slows every insert, so one that is"
             " superseded should go: DROP INDEX by name. Column order in a"
             " composite index matters -- (taken_by, taken_at) serves a"
             " search by nurse, and by nurse then time, but not by time"
             " alone. pragma_index_list and pragma_index_info are how you"
             " read the indexes back.",
        claims=[("two indexes, the new one on the two columns in order",
                 lambda rows, c: rows == [('idx_obs_admission,idx_obs_by',
                                           'taken_by,taken_at')])],
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
