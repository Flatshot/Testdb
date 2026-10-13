"""Practice exercises: fifteen questions on the library schema.

The seventh set on the library (SEED 861), on five tiers none of the
library sets have used. CTE chains -- two or three WITH clauses that build
on each other: members above their own branch's average, the busiest day
of each month, a month's share of its year. IN, EXISTS and JOIN -- three
ways to ask 'has at least one', where the join needs DISTINCT, a NOT IN
whose subquery contains a NULL returns nothing, and two conditions that
must hold for the SAME row. Formatting -- printf for zero-padded codes and
for pounds with two decimals, strftime for a date written the British way.
Numeric functions -- ROUND against CAST, ABS for a deviation, / and % to
split pence into pounds and pence. And three WRITABLE questions:

  * a BEFORE DELETE trigger that protects open holds
  * a view built on another view
  * an UPDATE whose WHERE is a subquery inside a subquery

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script -- the deletes your trigger should
sort.
"""

import sqlite3

EXERCISES = [
    # ========================================================== 1 CTE chains
    dict(
        id=1, ledger="Q937", concept="CTE", tier="1 - CTE chains",
        title="Above the average for their own branch",
        prompt=(
            "Members who have borrowed more often than the average"
            " borrower of THEIR OWN home branch. Three steps in WITH: loans"
            " per member with their home branch; the average of those"
            " counts per branch; then the members above their branch's"
            " figure.\n\n"
            "Return: member_id, home_branch_id, loans"
        ),
        solution=("WITH per AS (SELECT m.member_id, m.home_branch_id, COUNT(*) AS n"
                  " FROM loans l JOIN members m ON m.member_id = l.member_id GROUP BY m.member_id),"
                  " avg_b AS (SELECT home_branch_id, AVG(n) AS a FROM per GROUP BY home_branch_id)"
                  " SELECT p.member_id, p.home_branch_id, p.n FROM per p"
                  " JOIN avg_b b ON b.home_branch_id = p.home_branch_id WHERE p.n > b.a"),
        trap_sql=("WITH per AS (SELECT m.member_id, m.home_branch_id, COUNT(*) AS n"
                  " FROM loans l JOIN members m ON m.member_id = l.member_id GROUP BY m.member_id)"
                  " SELECT member_id, home_branch_id, n FROM per WHERE n > (SELECT AVG(n) FROM per)"),
        note="A CTE can read the CTE before it, which is what makes a"
             " chain: per-member counts, then per-branch averages OF those"
             " counts, then the join that compares each member with their"
             " own branch. One global average is a different question --"
             " a branch of light readers has members above its own average"
             " who are below the service's.",
        claims=[("two hundred or so members, from every branch",
                 lambda rows, c: 190 < len(rows) < 240 and len({r[1] for r in rows}) == 6)],
    ),
    dict(
        id=2, ledger="Q938", concept="CTE", tier="1 - CTE chains",
        title="The busiest day of each month",
        prompt=(
            "For each month of the data, the day with the most loans"
            " started, and how many: a CTE of loans per day, a second"
            " CTE that numbers the days within their month by loans"
            " descending -- ties broken by the earlier day -- and a"
            " final SELECT of the days numbered 1.\n\n"
            "Return: month, day, loans"
        ),
        solution=("WITH d AS (SELECT loaned_on, COUNT(*) AS n FROM loans GROUP BY loaned_on),"
                  " r AS (SELECT strftime('%Y-%m', loaned_on) AS m, loaned_on, n,"
                  " ROW_NUMBER() OVER (PARTITION BY strftime('%Y-%m', loaned_on) ORDER BY n DESC, loaned_on) AS rn"
                  " FROM d) SELECT m, loaned_on, n FROM r WHERE rn = 1"),
        trap_sql=("WITH d AS (SELECT loaned_on, COUNT(*) AS n FROM loans GROUP BY loaned_on),"
                  " r AS (SELECT strftime('%Y-%m', loaned_on) AS m, loaned_on, n,"
                  " ROW_NUMBER() OVER (PARTITION BY strftime('%Y-%m', loaned_on) ORDER BY n, loaned_on) AS rn"
                  " FROM d) SELECT m, loaned_on, n FROM r WHERE rn = 1"),
        note="The first CTE changes the grain from loans to days; the"
             " second ranks days within months; the final SELECT filters"
             " on the rank, which no WHERE in the second CTE could do. The"
             " window's ORDER BY decides what 'number 1' means -- DESC for"
             " the busiest, and without it the quietest day of each month"
             " comes back instead.",
        claims=[("eighteen months, each busiest day in the forties or more",
                 lambda rows, c: len(rows) == 18 and all(r[2] >= 45 for r in rows)
                 and all(r[1].startswith(r[0]) for r in rows))],
    ),
    dict(
        id=3, ledger="Q939", concept="CTE", tier="1 - CTE chains",
        title="Each month's share of its year",
        prompt=(
            "For each month: its loans, and what percentage of THAT"
            " YEAR's loans they are, to one decimal. A CTE of loans per"
            " month that also carries the year, a second CTE summing the"
            " first per year, and a join between the two on the year.\n\n"
            "Return: month, loans, pct_of_year"
        ),
        solution=("WITH m AS (SELECT strftime('%Y', loaned_on) AS y, strftime('%Y-%m', loaned_on) AS ym, COUNT(*) AS n"
                  " FROM loans GROUP BY ym),"
                  " yt AS (SELECT y, SUM(n) AS t FROM m GROUP BY y)"
                  " SELECT m.ym, m.n, ROUND(100.0 * m.n / yt.t, 1) FROM m JOIN yt ON yt.y = m.y"),
        trap_sql=("WITH m AS (SELECT strftime('%Y-%m', loaned_on) AS ym, COUNT(*) AS n FROM loans GROUP BY ym)"
                  " SELECT ym, n, ROUND(100.0 * n / (SELECT SUM(n) FROM m), 1) FROM m"),
        note="The second CTE aggregates the first again, at a coarser"
             " grain -- months into years -- and the join brings the"
             " year's total back down to each month's row. Dividing by"
             " the grand total gives a share of the whole eighteen months,"
             " so 2025's months add up to two-thirds rather than a"
             " hundred. SUM(n) OVER (PARTITION BY y) would say the same"
             " in one CTE.",
        claims=[("eighteen months, each year's shares adding up to a hundred",
                 lambda rows, c: len(rows) == 18
                 and 99.5 < sum(r[2] for r in rows if r[0] < '2026') < 100.5
                 and 99.5 < sum(r[2] for r in rows if r[0] >= '2026') < 100.5)],
    ),
    # ================================================= 2 IN, EXISTS and JOIN
    dict(
        id=4, ledger="Q940", concept="X1", tier="2 - IN, EXISTS and JOIN",
        title="Members who have ever been fined",
        prompt=(
            "Every member who has had at least one fine, paid or not,"
            " ONCE each: member_id and name. Fines reach the member"
            " through loans. EXISTS, IN or a join with DISTINCT all"
            " work; a plain join does not.\n\n"
            "Return: member_id, name"
        ),
        solution=("SELECT m.member_id, m.name FROM members m WHERE EXISTS ("
                  "SELECT 1 FROM fines f JOIN loans l ON l.loan_id = f.loan_id WHERE l.member_id = m.member_id)"),
        trap_sql=("SELECT m.member_id, m.name FROM members m"
                  " JOIN loans l ON l.member_id = m.member_id JOIN fines f ON f.loan_id = l.loan_id"),
        note="'Has at least one' is a question about existence, and"
             " EXISTS answers it once per member however many fines they"
             " have. A join produces one row per FINE -- four thousand"
             " rows for twelve hundred members -- and needs DISTINCT to"
             " collapse them, which costs a sort. IN (SELECT member_id"
             " ...) is the third spelling and also deduplicates.",
        claims=[("eleven hundred or so members, each once",
                 lambda rows, c: 1150 < len(rows) < 1220
                 and len({r[0] for r in rows}) == len(rows))],
    ),
    dict(
        id=5, ledger="Q941", concept="N1", tier="2 - IN, EXISTS and JOIN",
        title="Days with loans but no hold fulfilled",
        prompt=(
            "Days on which loans started but NO hold was fulfilled: the"
            " day and how many loans. Beware NOT IN against"
            " holds.fulfilled_on, which is NULL for the open holds -- a"
            " single NULL in a NOT IN list makes the whole test unknown"
            " for every row. Exclude the NULLs, or use NOT EXISTS.\n\n"
            "Return: day, loans"
        ),
        solution=("SELECT loaned_on, COUNT(*) FROM loans"
                  " WHERE NOT EXISTS (SELECT 1 FROM holds h WHERE h.fulfilled_on = loans.loaned_on)"
                  " GROUP BY loaned_on"),
        trap_sql=("SELECT loaned_on, COUNT(*) FROM loans"
                  " WHERE loaned_on NOT IN (SELECT fulfilled_on FROM holds)"
                  " GROUP BY loaned_on"),
        note="x NOT IN (a, b, NULL) is x <> a AND x <> b AND x <> NULL,"
             " and the last part is NULL, so the whole thing is never"
             " true -- the query returns nothing and gives no hint why."
             " NOT EXISTS compares row by row and a NULL simply fails to"
             " match. If NOT IN is wanted, the subquery needs WHERE"
             " fulfilled_on IS NOT NULL.",
        claims=[("a hundred or so days",
                 lambda rows, c: 90 < len(rows) < 130)],
    ),
    dict(
        id=6, ledger="Q942", concept="E1", tier="2 - IN, EXISTS and JOIN",
        title="A hold at their own branch",
        prompt=(
            "Members who have placed a hold to collect at their OWN home"
            " branch -- a single hold whose branch_id equals the member's"
            " home_branch_id. Two conditions on the same hold row, which"
            " is one correlated EXISTS, not two IN tests.\n\n"
            "Return: member_id"
        ),
        solution=("SELECT m.member_id FROM members m WHERE EXISTS ("
                  "SELECT 1 FROM holds h WHERE h.member_id = m.member_id AND h.branch_id = m.home_branch_id)"),
        trap_sql=("SELECT m.member_id FROM members m"
                  " WHERE m.member_id IN (SELECT member_id FROM holds)"
                  " AND m.home_branch_id IN (SELECT branch_id FROM holds)"),
        note="Two separate IN tests ask two separate questions -- has"
             " this member any hold, and has any hold ever been placed"
             " at this branch -- and both are true for almost everyone."
             " The question needs ONE hold that satisfies both, so both"
             " conditions go inside the same EXISTS, where h is a"
             " single row.",
        claims=[("two hundred or so members",
                 lambda rows, c: 190 < len(rows) < 240)],
    ),
    # ========================================================== 3 Formatting
    dict(
        id=7, ledger="Q943", concept="FMT", tier="3 - Formatting",
        title="Membership codes",
        prompt=(
            "For the members of branch 6: a membership code made of 'M'"
            " and the member_id zero-padded to four digits -- M0011,"
            " M0014 -- using printf('%04d', ...) and ||.\n\n"
            "Return: member_id, code"
        ),
        solution="SELECT member_id, 'M' || printf('%04d', member_id) FROM members WHERE home_branch_id = 6",
        trap_sql="SELECT member_id, 'M' || member_id FROM members WHERE home_branch_id = 6",
        note="printf is C's: %d is an integer, 04 says four wide and"
             " padded with zeros. Without it 'M' || 11 is 'M11', a code"
             " whose length depends on the number, which sorts wrongly as"
             " text -- M1000 before M11. format() is a synonym in newer"
             " SQLite.",
        claims=[("266 codes, all five characters",
                 lambda rows, c: len(rows) == 266 and all(len(r[1]) == 5 and r[1][0] == 'M' for r in rows))],
    ),
    dict(
        id=8, ledger="Q944", concept="FMT", tier="3 - Formatting",
        title="What the biggest debtors owe, in pounds",
        prompt=(
            "Members whose UNPAID fines add up to 5000 pence or more:"
            " member_id and the total as text in pounds with exactly two"
            " decimals and a leading pound sign -- '£55.60', not 55.6."
            " printf('%.2f', ...) does the decimals.\n\n"
            "Return: member_id, owed"
        ),
        solution=("SELECT l.member_id, printf('£%.2f', SUM(f.amount_pence) / 100.0)"
                  " FROM fines f JOIN loans l ON l.loan_id = f.loan_id WHERE f.paid_on IS NULL"
                  " GROUP BY l.member_id HAVING SUM(f.amount_pence) >= 5000"),
        trap_sql=("SELECT l.member_id, ROUND(SUM(f.amount_pence) / 100.0, 2)"
                  " FROM fines f JOIN loans l ON l.loan_id = f.loan_id WHERE f.paid_on IS NULL"
                  " GROUP BY l.member_id HAVING SUM(f.amount_pence) >= 5000"),
        note="ROUND gives a NUMBER, and 55.60 as a number is 55.6 -- the"
             " trailing zero is not a property of a number. Money shown to"
             " a person is text, and printf('%.2f') always writes two"
             " decimals. The division by 100.0 is what turns pence into"
             " pounds without truncating.",
        claims=[("four debtors, 1149 owing £64.80",
                 lambda rows, c: len(rows) == 4 and (1149, '£64.80') in rows)],
    ),
    dict(
        id=9, ledger="Q945", concept="FMT", tier="3 - Formatting",
        title="Opening dates, written the British way",
        prompt=(
            "Each branch's opening date written day/month/year --"
            " 12/05/1902 for 1902-05-12 -- using strftime.\n\n"
            "Return: branch_id, opened"
        ),
        solution="SELECT branch_id, strftime('%d/%m/%Y', opened_on) FROM branches",
        trap_sql="SELECT branch_id, strftime('%m/%d/%Y', opened_on) FROM branches",
        note="strftime formats a date for display; %d, %m and %Y are day,"
             " month and four-digit year, in whatever order and with"
             " whatever separators you write between them. The stored"
             " form stays ISO, which is what compares and sorts correctly"
             " -- formatting is for the last step only.",
        claims=[("six dates, Central's 12/05/1902",
                 lambda rows, c: len(rows) == 6 and (1, '12/05/1902') in rows)],
    ),
    # =================================================== 4 Numeric functions
    dict(
        id=10, ledger="Q946", concept="NUM", tier="4 - Numeric functions",
        title="Average pages per genre, to the nearest page",
        prompt=(
            "The average page count of each genre's books, as a whole"
            " number rounded to the NEAREST page -- ROUND, not CAST,"
            " which truncates.\n\n"
            "Return: genre, avg_pages"
        ),
        solution="SELECT genre, CAST(ROUND(AVG(pages)) AS INTEGER) FROM books GROUP BY genre",
        trap_sql="SELECT genre, CAST(AVG(pages) AS INTEGER) FROM books GROUP BY genre",
        note="CAST(x AS INTEGER) throws the fraction away, so 412.9"
             " becomes 412; ROUND goes to the nearest, 413. The two agree"
             " only when the fraction is under a half. ROUND alone returns"
             " a float, 413.0, so the CAST around it makes the whole"
             " number an integer.",
        claims=[("eight genres, three to five hundred pages",
                 lambda rows, c: len(rows) == 8 and all(300 < r[1] < 600 for r in rows)
                 and len({r[1] for r in rows}) > 1)],
    ),
    dict(
        id=11, ledger="Q947", concept="NUM", tier="4 - Numeric functions",
        title="How far each branch is from the average stock",
        prompt=(
            "For each branch: its copies, and how far that is from the"
            " average branch's copies -- total copies over six -- as a"
            " whole number that is never negative: ABS of the difference,"
            " rounded.\n\n"
            "Return: branch_id, copies, deviation"
        ),
        solution=("SELECT branch_id, COUNT(*),"
                  " CAST(ROUND(ABS(COUNT(*) - (SELECT COUNT(*) / 6.0 FROM copies))) AS INTEGER)"
                  " FROM copies GROUP BY branch_id"),
        trap_sql=("SELECT branch_id, COUNT(*),"
                  " CAST(ROUND(COUNT(*) - (SELECT COUNT(*) / 6.0 FROM copies)) AS INTEGER)"
                  " FROM copies GROUP BY branch_id"),
        note="ABS turns a signed difference into a distance, which is"
             " what 'how far from' means; without it the branches below"
             " average come out negative. The average itself is a scalar"
             " subquery, and the 6.0 keeps the division from being integer.",
        claims=[("six branches, deviations between ten and fifty",
                 lambda rows, c: len(rows) == 6 and all(5 <= r[2] <= 50 for r in rows)
                 and sum(r[1] for r in rows) == 2226)],
    ),
    dict(
        id=12, ledger="Q948", concept="NUM", tier="4 - Numeric functions",
        title="Pounds and pence, split",
        prompt=(
            "The total of fines, unpaid and paid separately, split into"
            " whole pounds and the pence left over -- 4149 pounds and 60"
            " pence from 414,960 -- with integer division and the %"
            " remainder operator.\n\n"
            "Return: paid, pounds, pence"
        ),
        solution=("SELECT paid_on IS NOT NULL, SUM(amount_pence) / 100, SUM(amount_pence) % 100"
                  " FROM fines GROUP BY 1"),
        trap_sql=("SELECT paid_on IS NOT NULL, SUM(amount_pence) / 100.0, SUM(amount_pence) % 100"
                  " FROM fines GROUP BY 1"),
        note="Integer division and modulo are a pair: a / 100 is how"
             " many whole hundreds, a % 100 is what is left, and together"
             " they rebuild a. Dividing by 100.0 gives 4149.6, which is"
             " the amount in pounds, not the pounds part of it.",
        claims=[("two rows, the unpaid total 4149 pounds and 60 pence",
                 lambda rows, c: (0, 4149, 60) in rows and len(rows) == 2)],
    ),
    # ================================================= 5 Changing the data
    dict(
        id=13, ledger="Q949", concept="TRG", tier="5 - Changing the data",
        kind="script",
        title="Open holds cannot be deleted",
        prompt=(
            "Write a BEFORE DELETE trigger on holds that refuses --"
            " RAISE(ABORT, ...) -- to delete a hold that is still OPEN,"
            " fulfilled_on and cancelled_on both NULL; closed holds may"
            " go. The question then deletes hold 1 (open), hold 2"
            " (fulfilled) and hold 7 (cancelled).\n\n"
            "Checked: which of the three holds still exist"
        ),
        solution=("CREATE TRIGGER keep_open_holds BEFORE DELETE ON holds\n"
                  "WHEN OLD.fulfilled_on IS NULL AND OLD.cancelled_on IS NULL\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'cancel the hold instead of deleting it');\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER keep_open_holds BEFORE DELETE ON holds\n"
                  "WHEN OLD.fulfilled_on IS NULL\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'cancel the hold instead of deleting it');\n"
                  "END;"),
        driver_sql=("DELETE FROM holds WHERE hold_id = 1;\n"
                    "DELETE FROM holds WHERE hold_id = 2;\n"
                    "DELETE FROM holds WHERE hold_id = 7;"),
        probe_sql="SELECT hold_id FROM holds WHERE hold_id IN (1, 2, 7) ORDER BY hold_id",
        note="A DELETE trigger sees the row about to go as OLD -- there"
             " is no NEW. 'Open' is two NULLs, and testing only"
             " fulfilled_on treats a cancelled hold as open, so the"
             " cancelled one is protected along with the live one."
             " BEFORE is the right time: the RAISE stops the delete before"
             " anything has changed.",
        claims=[("hold 1 kept, 2 and 7 gone",
                 lambda rows, c: rows == [(1,)])],
    ),
    dict(
        id=14, ledger="Q950", concept="VIEW", tier="5 - Changing the data",
        kind="script",
        title="A view on a view",
        prompt=(
            "Create a view `open_loans (loan_id, copy_id, member_id,"
            " due_on)` of the loans with no returned_on, then a second"
            " view `overdue_by_branch (branch_id, overdue)` that reads"
            " open_loans -- not loans -- joined to copies, counting per"
            " branch the open loans due before 2026-06-30.\n\n"
            "Checked: the second view's rows"
        ),
        solution=("CREATE VIEW open_loans AS\n"
                  "  SELECT loan_id, copy_id, member_id, due_on FROM loans WHERE returned_on IS NULL;\n"
                  "CREATE VIEW overdue_by_branch AS\n"
                  "  SELECT c.branch_id, COUNT(*) AS overdue FROM open_loans o\n"
                  "  JOIN copies c ON c.copy_id = o.copy_id WHERE o.due_on < '2026-06-30'\n"
                  "  GROUP BY c.branch_id;"),
        trap_sql=("CREATE VIEW open_loans AS\n"
                  "  SELECT loan_id, copy_id, member_id, due_on FROM loans WHERE returned_on IS NULL;\n"
                  "CREATE VIEW overdue_by_branch AS\n"
                  "  SELECT c.branch_id, COUNT(*) AS overdue FROM loans o\n"
                  "  JOIN copies c ON c.copy_id = o.copy_id WHERE o.due_on < '2026-06-30'\n"
                  "  GROUP BY c.branch_id;"),
        probe_sql="SELECT branch_id, overdue FROM overdue_by_branch ORDER BY branch_id",
        note="A view can be built on a view, and the point is that the"
             " first one's rule -- open means no returned_on -- is written"
             " once and inherited. Reading loans directly in the second"
             " view loses that rule, and every loan ever due before June"
             " counts as overdue: thousands per branch instead of twenty.",
        claims=[("six branches, ten to thirty overdue each",
                 lambda rows, c: len(rows) == 6 and all(8 <= r[1] <= 30 for r in rows))],
    ),
    dict(
        id=15, ledger="Q951", concept="DML", tier="5 - Changing the data",
        kind="script",
        title="Old Town gets a manager",
        prompt=(
            "Branch 6 has no manager. Promote its longest-serving"
            " librarian -- the earliest hired_on among branch 6's"
            " librarians -- to 'manager', and nobody else. One UPDATE"
            " whose WHERE finds that one staff_id with a subquery.\n\n"
            "Checked: how many managers each branch has, and who branch"
            " 6's is"
        ),
        solution=("UPDATE staff SET role = 'manager' WHERE staff_id = ("
                  "SELECT staff_id FROM staff WHERE branch_id = 6 AND role = 'librarian'"
                  " ORDER BY hired_on LIMIT 1);"),
        trap_sql=("UPDATE staff SET role = 'manager' WHERE branch_id = 6 AND role = 'librarian';"),
        probe_sql=("SELECT branch_id, COUNT(*), MIN(staff_id) FROM staff WHERE role = 'manager'"
                   " GROUP BY branch_id ORDER BY branch_id"),
        note="An UPDATE's WHERE can be a scalar subquery that picks the"
             " one row: ORDER BY hired_on LIMIT 1 inside it is 'the"
             " earliest'. Without the subquery the WHERE describes both"
             " librarians and both are promoted. A subquery that could"
             " return more than one row needs IN; this one is built to"
             " return exactly one, so = is right.",
        claims=[("six branches with one manager each, Zara Yilmaz at Old Town",
                 lambda rows, c: len(rows) == 6 and all(r[1] == 1 for r in rows)
                 and (6, 1, 28) in rows)],
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
