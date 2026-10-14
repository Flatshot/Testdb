"""Practice exercises: fifteen questions on the library schema.

The eighth set on the library (SEED 861), on five tiers none of the
library sets have used. Aggregates and totals -- HAVING with two or three
aggregate conditions, a total row by UNION ALL, and a COUNT(DISTINCT) over
a pair of columns. String tricks -- printf for a left-justified column, a
slug by LOWER and REPLACE, and LTRIM's character-set trap against SUBSTR.
Pivots both ways -- three SUMs into one row, and one row's three counts
into three rows. SQLite's bare columns -- the other columns of the row
MIN or MAX picked, a rule SQLite has and most databases do not. And three
WRITABLE questions:

  * a trigger that LOGS a change to a table it creates
  * a correlated DELETE
  * an idempotent INSERT ... SELECT ... WHERE NOT EXISTS

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script -- the updates your trigger should
log.
"""

import sqlite3

EXERCISES = [
    # ================================================ 1 Aggregates and totals
    dict(
        id=1, ledger="Q952", concept="A3", tier="1 - Aggregates and totals",
        title="Big branches with a damage problem",
        prompt=(
            "Branches holding at least 350 copies of which more than 10"
            " per cent are damaged: branch_id, copies, and the damaged"
            " percentage to one decimal. Both conditions are about the"
            " branch as a whole, so both go in HAVING -- a WHERE on"
            " condition would change what is being counted.\n\n"
            "Return: branch_id, copies, pct_damaged"
        ),
        solution=("SELECT branch_id, COUNT(*), ROUND(100.0 * AVG(condition = 'damaged'), 1) FROM copies"
                  " GROUP BY branch_id HAVING COUNT(*) >= 350 AND AVG(condition = 'damaged') > 0.1"),
        trap_sql=("SELECT branch_id, COUNT(*), ROUND(100.0 * AVG(condition = 'damaged'), 1) FROM copies"
                  " WHERE condition = 'damaged' GROUP BY branch_id HAVING COUNT(*) >= 35"),
        note="AVG of a comparison is the fraction of rows where it holds,"
             " which is the neatest way to get a percentage out of a"
             " group. A WHERE on condition leaves only the damaged copies"
             " in the group, so COUNT(*) is the damaged count and the"
             " average is 100 per cent everywhere -- the whole-branch"
             " figures are gone before HAVING can look at them.",
        claims=[("two branches, Northgate and Eastfield",
                 lambda rows, c: {r[0] for r in rows} == {2, 5}
                 and all(r[1] >= 350 and r[2] > 10 for r in rows))],
    ),
    dict(
        id=2, ledger="Q953", concept="A3", tier="1 - Aggregates and totals",
        title="Regulars who are never late",
        prompt=(
            "Members with at least 10 loans, NONE of which came back"
            " late: member_id and their loan count. 'None late' is an"
            " aggregate condition -- a SUM of the late test equal to"
            " zero -- not a WHERE.\n\n"
            "Return: member_id, loans"
        ),
        solution=("SELECT member_id, COUNT(*) FROM loans GROUP BY member_id"
                  " HAVING COUNT(*) >= 10 AND SUM(returned_on > due_on) = 0"),
        trap_sql=("SELECT member_id, COUNT(*) FROM loans GROUP BY member_id"
                  " HAVING COUNT(*) >= 10 AND COUNT(returned_on > due_on) = 0"),
        note="SUM(returned_on > due_on) adds a 1 for every late return"
             " and is 0 when there were none. COUNT of the same expression"
             " counts the rows where it is not NULL -- every returned"
             " loan, true or false alike -- so it is never 0 and no member"
             " qualifies. A WHERE returned_on <= due_on would instead"
             " count only the on-time loans and let late members through.",
        claims=[("eighty or so members",
                 lambda rows, c: 70 < len(rows) < 100 and all(r[1] >= 10 for r in rows))],
    ),
    dict(
        id=3, ledger="Q954", concept="A3", tier="1 - Aggregates and totals",
        title="Long books from a long way back",
        prompt=(
            "Genres whose books average more than 480 pages AND whose"
            " earliest publication year is before 1900: genre, the"
            " average pages rounded to a whole number, and that earliest"
            " year. The average is over ALL the genre's books.\n\n"
            "Return: genre, avg_pages, earliest"
        ),
        solution=("SELECT genre, CAST(ROUND(AVG(pages)) AS INTEGER), MIN(published_year) FROM books"
                  " GROUP BY genre HAVING AVG(pages) > 480 AND MIN(published_year) < 1900"),
        trap_sql=("SELECT genre, CAST(ROUND(AVG(pages)) AS INTEGER), MIN(published_year) FROM books"
                  " WHERE published_year < 1900 GROUP BY genre HAVING AVG(pages) > 480"),
        note="'Earliest year before 1900' is a fact about the group's"
             " MIN, so it is a HAVING. Moving it to WHERE keeps only the"
             " nineteenth-century books, and the average is then of"
             " those few books, not of the genre -- cookery jumps from"
             " 528 to 880 pages. Two HAVING conditions, two aggregates,"
             " no WHERE.",
        claims=[("four genres, cookery the longest",
                 lambda rows, c: len(rows) == 4
                 and max(rows, key=lambda r: r[1])[0] == 'cookery'
                 and all(r[2] < 1900 for r in rows))],
    ),
    dict(
        id=4, ledger="Q955", concept="S1", tier="1 - Aggregates and totals",
        title="Copies per branch, with a total row",
        prompt=(
            "Copies per branch as six rows with the branch_id as text,"
            " plus a seventh row labelled 'all' with the total: a GROUP"
            " BY query UNION ALL a one-row total query. CAST the id to"
            " TEXT so the two queries' first columns agree.\n\n"
            "Return: branch, copies"
        ),
        solution=("SELECT CAST(branch_id AS TEXT), COUNT(*) FROM copies GROUP BY branch_id"
                  " UNION ALL SELECT 'all', COUNT(*) FROM copies"),
        trap_sql="SELECT CAST(branch_id AS TEXT), COUNT(*) FROM copies GROUP BY branch_id",
        note="SQL has no row for 'and the total' in a plain GROUP BY;"
             " other databases offer ROLLUP, SQLite does not, and UNION"
             " ALL of a second query is the portable way. The columns of"
             " the two halves must match in number and kind, which is why"
             " the id becomes text to sit beside the word 'all'.",
        claims=[("seven rows, the total equal to the sum of the six",
                 lambda rows, c: len(rows) == 7
                 and dict(rows)['all'] == sum(r[1] for r in rows if r[0] != 'all'))],
    ),
    dict(
        id=5, ledger="Q956", concept="A2", tier="1 - Aggregates and totals",
        title="Readers of a title, not loans of it",
        prompt=(
            "For each genre: loans, and how many DISTINCT member-and-"
            "title pairs those loans are -- a member who borrowed the"
            " same title three times is one pair. COUNT(DISTINCT) takes"
            " one expression, so join the two ids into one with ||.\n\n"
            "Return: genre, loans, pairs"
        ),
        solution=("SELECT b.genre, COUNT(*), COUNT(DISTINCT l.member_id || ':' || c.book_id)"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id JOIN books b ON b.book_id = c.book_id"
                  " GROUP BY b.genre"),
        trap_sql=("SELECT b.genre, COUNT(*), COUNT(DISTINCT l.member_id || c.book_id)"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id JOIN books b ON b.book_id = c.book_id"
                  " GROUP BY b.genre"),
        note="COUNT(DISTINCT a, b) is not SQL; the idiom is to concatenate"
             " the columns into one value. The separator matters: 12 ||"
             " 34 and 123 || 4 are both '1234', so without ':' different"
             " pairs collide and the count is slightly short. Re-borrowing"
             " is common enough that pairs run a few per cent below loans.",
        claims=[("eight genres, pairs a little below loans",
                 lambda rows, c: len(rows) == 8 and all(0.9 < r[2] / r[1] < 1 for r in rows))],
    ),
    # ======================================================= 2 String tricks
    dict(
        id=6, ledger="Q957", concept="STR", tier="2 - String tricks",
        title="A column of titles, padded to the right",
        prompt=(
            "The poetry titles each padded with spaces on the RIGHT to"
            " 24 characters and followed by '|', so the bars line up in"
            " a fixed-width listing: printf with %-24s.\n\n"
            "Return: book_id, padded"
        ),
        solution="SELECT book_id, printf('%-24s|', title) FROM books WHERE genre = 'poetry'",
        trap_sql="SELECT book_id, printf('%24s|', title) FROM books WHERE genre = 'poetry'",
        note="%24s pads on the LEFT, pushing the text to the right; the"
             " minus sign in %-24s left-justifies, padding on the right."
             " A title longer than 24 characters is not cut -- printf"
             " widths are minimums.",
        claims=[("fifty-four poetry titles, every bar at column 25 or later",
                 lambda rows, c: len(rows) == 54
                 and all(r[1].endswith('|') and len(r[1]) >= 25 for r in rows))],
    ),
    dict(
        id=7, ledger="Q958", concept="STR", tier="2 - String tricks",
        title="Slugs for the poetry titles",
        prompt=(
            "A web slug for each poetry title: the title in lower case"
            " with every space replaced by a hyphen -- 'lost-library'."
            " LOWER and REPLACE, one inside the other.\n\n"
            "Return: book_id, slug"
        ),
        solution="SELECT book_id, LOWER(REPLACE(title, ' ', '-')) FROM books WHERE genre = 'poetry'",
        trap_sql="SELECT book_id, REPLACE(title, ' ', '-') FROM books WHERE genre = 'poetry'",
        note="String functions nest like any others: REPLACE swaps the"
             " spaces, LOWER folds the case, in either order. Without"
             " LOWER the slug keeps its capitals, and URLs are usually"
             " case-sensitive, so 'Lost-Library' and 'lost-library' are"
             " two different pages.",
        claims=[("fifty-four slugs, all lower case, no spaces",
                 lambda rows, c: len(rows) == 54
                 and all(r[1] == r[1].lower() and ' ' not in r[1] and '-' in r[1] for r in rows))],
    ),
    dict(
        id=8, ledger="Q959", concept="STR", tier="2 - String tricks",
        title="After 'Poems for a'",
        prompt=(
            "For the titles that begin 'Poems for a ', the rest of the"
            " title after that prefix -- 'Paper Tower' from 'Poems for a"
            " Paper Tower'. The prefix is twelve characters, so SUBSTR"
            " from position 13. LTRIM(title, 'Poems for a ') is NOT the"
            " same thing.\n\n"
            "Return: book_id, rest"
        ),
        solution="SELECT book_id, SUBSTR(title, 13) FROM books WHERE title LIKE 'Poems for a %'",
        trap_sql="SELECT book_id, LTRIM(title, 'Poems for a ') FROM books WHERE title LIKE 'Poems for a %'",
        note="LTRIM's second argument is a SET of characters, not a"
             " prefix: it strips from the left for as long as the next"
             " character is any of P, o, e, m, s, f, r, a or a space. A"
             " title whose next word starts with P -- 'Poems for a Paper"
             " Tower', 'Poems for a Painted Season' -- loses its P as"
             " well. SUBSTR cuts at a position and cannot overshoot.",
        claims=[("sixty-one titles, each rest starting with a capital",
                 lambda rows, c: len(rows) == 61
                 and all(r[1][0].isupper() for r in rows))],
    ),
    # ====================================================== 3 Pivots both ways
    dict(
        id=9, ledger="Q960", concept="C7", tier="3 - Pivots both ways",
        title="Loans per genre, one column a year",
        prompt=(
            "For each genre, its loans in 2025 and in 2026 as two"
            " columns: a pivot by conditional SUM. Compare the year as"
            " text -- strftime returns text, and '2025' is not 2025.\n\n"
            "Return: genre, loans_2025, loans_2026"
        ),
        solution=("SELECT b.genre, SUM(strftime('%Y', l.loaned_on) = '2025'), SUM(strftime('%Y', l.loaned_on) = '2026')"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id JOIN books b ON b.book_id = c.book_id"
                  " GROUP BY b.genre"),
        trap_sql=("SELECT b.genre, SUM(strftime('%Y', l.loaned_on) = 2025), SUM(strftime('%Y', l.loaned_on) = 2026)"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id JOIN books b ON b.book_id = c.book_id"
                  " GROUP BY b.genre"),
        note="strftime returns TEXT, and in SQLite text never equals an"
             " integer -- '2025' = 2025 is false, so both columns are 0"
             " for every genre, with no error to say why. Compare with"
             " the string '2025', or CAST the strftime to INTEGER first."
             " The same trap bites in WHERE strftime('%m', ...) = 6.",
        claims=[("eight genres, two-thirds of loans in 2025",
                 lambda rows, c: len(rows) == 8
                 and all(r[1] > r[2] > 0 for r in rows)
                 and sum(r[1] + r[2] for r in rows) == 23976)],
    ),
    dict(
        id=10, ledger="Q961", concept="S1", tier="3 - Pivots both ways",
        title="Branch 4's holds, one row a status",
        prompt=(
            "The holds placed at branch 4 as THREE rows -- 'fulfilled',"
            " 'cancelled', 'waiting' -- each with its count: an unpivot,"
            " three one-row queries joined by UNION ALL.\n\n"
            "Return: status, holds"
        ),
        solution=("SELECT 'fulfilled', COUNT(fulfilled_on) FROM holds WHERE branch_id = 4"
                  " UNION ALL SELECT 'cancelled', COUNT(cancelled_on) FROM holds WHERE branch_id = 4"
                  " UNION ALL SELECT 'waiting', SUM(fulfilled_on IS NULL AND cancelled_on IS NULL)"
                  " FROM holds WHERE branch_id = 4"),
        trap_sql=("SELECT 'fulfilled', COUNT(fulfilled_on) FROM holds WHERE branch_id = 4"
                  " UNION ALL SELECT 'cancelled', COUNT(cancelled_on) FROM holds WHERE branch_id = 4"
                  " UNION ALL SELECT 'waiting', COUNT(*) - COUNT(fulfilled_on) FROM holds WHERE branch_id = 4"),
        note="A pivot turns rows into columns; an unpivot turns columns"
             " back into rows, and in SQLite that is a UNION ALL with a"
             " label in each part. The third count is the one to get"
             " right: 'waiting' is neither fulfilled nor cancelled, and"
             " placed minus fulfilled counts the cancelled holds as"
             " waiting.",
        claims=[("three rows adding up to branch 4's holds",
                 lambda rows, c: len(rows) == 3 and sum(r[1] for r in rows) ==
                 c.execute("SELECT COUNT(*) FROM holds WHERE branch_id = 4").fetchone()[0])],
    ),
    # ================================================= 4 SQLite bare columns
    dict(
        id=11, ledger="Q962", concept="BARE", tier="4 - SQLite bare columns",
        title="Each Old Town member's latest loan",
        prompt=(
            "For each member whose home branch is 6 and who has borrowed:"
            " their latest loaned_on, and the copy_id of THAT loan. In"
            " SQLite, a column selected alongside a single MAX comes from"
            " the row the MAX was found in -- a 'bare column' -- so no"
            " subquery is needed.\n\n"
            "Return: member_id, last_loan, copy_id"
        ),
        solution=("SELECT l.member_id, MAX(l.loaned_on), l.copy_id FROM loans l"
                  " JOIN members m ON m.member_id = l.member_id WHERE m.home_branch_id = 6"
                  " GROUP BY l.member_id"),
        trap_sql=("SELECT l.member_id, MIN(l.loaned_on), l.copy_id FROM loans l"
                  " JOIN members m ON m.member_id = l.member_id WHERE m.home_branch_id = 6"
                  " GROUP BY l.member_id"),
        note="Most databases refuse a non-aggregated column in a GROUP BY"
             " query; SQLite allows it, and when the query has exactly one"
             " MIN or MAX it guarantees the bare columns come from that"
             " row. It is a convenience worth knowing and worth not"
             " relying on elsewhere -- Postgres would need a window or a"
             " correlated subquery for the same answer.",
        claims=[("239 members, every latest loan in the data's range",
                 lambda rows, c: len(rows) == 239
                 and all('2025-01-01' <= r[1] <= '2026-06-30' for r in rows)
                 and all(c.execute("SELECT loaned_on FROM loans WHERE member_id = ? AND copy_id = ?",
                                   (r[0], r[2])).fetchone()[0] == r[1] for r in rows[:20]))],
    ),
    dict(
        id=12, ledger="Q963", concept="BARE", tier="4 - SQLite bare columns",
        title="The longest-serving person at each branch",
        prompt=(
            "For each branch: the name and hired_on of its longest-"
            "serving member of staff, using MIN(hired_on) and the bare"
            " name column beside it.\n\n"
            "Return: branch_id, name, hired_on"
        ),
        solution="SELECT branch_id, name, MIN(hired_on) FROM staff GROUP BY branch_id",
        trap_sql="SELECT branch_id, name, MAX(hired_on) FROM staff GROUP BY branch_id",
        note="MIN of a date is the earliest, and the name beside it is"
             " that person's -- SQLite's bare-column rule again. MAX"
             " gives the newest recruit. The rule holds for a single"
             " MIN or MAX only; with two aggregates, or with SUM, the"
             " bare column is from an unspecified row.",
        claims=[("six branches, Zara Yilmaz at Old Town",
                 lambda rows, c: len(rows) == 6 and (6, 'Zara Yilmaz', '2009-10-09') in rows)],
    ),
    # ================================================= 5 Changing the data
    dict(
        id=13, ledger="Q964", concept="TRG", tier="5 - Changing the data",
        kind="script",
        title="A log of condition changes",
        prompt=(
            "Create a table `condition_log (log_id INTEGER PRIMARY KEY,"
            " copy_id INTEGER NOT NULL, old_condition TEXT NOT NULL,"
            " new_condition TEXT NOT NULL)` and an AFTER UPDATE OF"
            " condition trigger on copies that inserts a row into it --"
            " only when the condition actually CHANGED. The question then"
            " marks copies 1 and 2 damaged and re-saves copy 3 unchanged.\n\n"
            "Checked: the log's copy_id, old and new, in log order"
        ),
        solution=("CREATE TABLE condition_log (log_id INTEGER PRIMARY KEY, copy_id INTEGER NOT NULL,\n"
                  "  old_condition TEXT NOT NULL, new_condition TEXT NOT NULL);\n"
                  "CREATE TRIGGER log_condition AFTER UPDATE OF condition ON copies\n"
                  "WHEN OLD.condition <> NEW.condition\n"
                  "BEGIN\n"
                  "  INSERT INTO condition_log (copy_id, old_condition, new_condition)\n"
                  "  VALUES (NEW.copy_id, OLD.condition, NEW.condition);\n"
                  "END;"),
        trap_sql=("CREATE TABLE condition_log (log_id INTEGER PRIMARY KEY, copy_id INTEGER NOT NULL,\n"
                  "  old_condition TEXT NOT NULL, new_condition TEXT NOT NULL);\n"
                  "CREATE TRIGGER log_condition AFTER UPDATE OF condition ON copies\n"
                  "BEGIN\n"
                  "  INSERT INTO condition_log (copy_id, old_condition, new_condition)\n"
                  "  VALUES (NEW.copy_id, OLD.condition, NEW.condition);\n"
                  "END;"),
        driver_sql=("UPDATE copies SET condition = 'damaged' WHERE copy_id IN (1, 2);\n"
                    "UPDATE copies SET condition = condition WHERE copy_id = 3;"),
        probe_sql="SELECT copy_id, old_condition, new_condition FROM condition_log ORDER BY log_id",
        note="An audit trigger has OLD and NEW side by side, and the WHEN"
             " is what keeps the log honest: UPDATE OF condition fires"
             " whenever the column is ASSIGNED, including to its own"
             " value, so without the comparison copy 3 gets a row saying"
             " good became good. AFTER is right for logging -- the change"
             " has happened by the time the row is written.",
        claims=[("two entries, copy 3 not among them",
                 lambda rows, c: rows == [(1, 'worn', 'damaged'), (2, 'good', 'damaged')])],
    ),
    dict(
        id=14, ledger="Q965", concept="DML", tier="5 - Changing the data",
        kind="script",
        title="Holds that can never be met where they stand",
        prompt=(
            "Delete the OPEN holds -- fulfilled_on and cancelled_on both"
            " NULL -- placed at a branch that holds no copy of the book"
            " at all. Closed holds stay, whatever branch they name. The"
            " test on copies is a correlated NOT EXISTS inside the"
            " DELETE's WHERE.\n\n"
            "Checked: how many holds remain, how many of them are open,"
            " and how many open holds are still at a branch without the"
            " book"
        ),
        solution=("DELETE FROM holds WHERE fulfilled_on IS NULL AND cancelled_on IS NULL"
                  " AND NOT EXISTS (SELECT 1 FROM copies c WHERE c.book_id = holds.book_id"
                  " AND c.branch_id = holds.branch_id);"),
        trap_sql=("DELETE FROM holds WHERE NOT EXISTS (SELECT 1 FROM copies c"
                  " WHERE c.book_id = holds.book_id AND c.branch_id = holds.branch_id);"),
        probe_sql=("SELECT COUNT(*), SUM(fulfilled_on IS NULL AND cancelled_on IS NULL),"
                   " SUM(fulfilled_on IS NULL AND cancelled_on IS NULL AND NOT EXISTS ("
                   "SELECT 1 FROM copies c WHERE c.book_id = holds.book_id AND c.branch_id = holds.branch_id))"
                   " FROM holds"),
        note="A DELETE's WHERE can be correlated like any other: inside"
             " the subquery, holds.book_id and holds.branch_id refer to"
             " the row being judged. The 'open' half of the condition is"
             " the half that keeps history -- without it, six hundred"
             " closed holds whose branch happened to lack the book are"
             " erased too.",
        claims=[("176 open holds removed, closed ones kept",
                 lambda rows, c: rows == [(1500 - 176, 337 - 176, 0)])],
    ),
    dict(
        id=15, ledger="Q966", concept="DML", tier="5 - Changing the data",
        kind="script",
        title="A copy for every title, and no more than that",
        prompt=(
            "Give every book that has NO copies one copy at Central"
            " (branch 1), acquired '2026-07-01', in 'good' condition --"
            " with a single INSERT ... SELECT whose WHERE NOT EXISTS skips"
            " the books already stocked, so running it twice adds nothing"
            " the second time.\n\n"
            "Checked: how many copies there are, how many books still have"
            " none, and how many copies were acquired on 2026-07-01"
        ),
        solution=("INSERT INTO copies (book_id, branch_id, acquired_on, condition)"
                  " SELECT b.book_id, 1, '2026-07-01', 'good' FROM books b"
                  " WHERE NOT EXISTS (SELECT 1 FROM copies c WHERE c.book_id = b.book_id);"),
        trap_sql=("INSERT INTO copies (book_id, branch_id, acquired_on, condition)"
                  " SELECT b.book_id, 1, '2026-07-01', 'good' FROM books b;"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM copies),"
                   " (SELECT COUNT(*) FROM books b WHERE NOT EXISTS (SELECT 1 FROM copies c WHERE c.book_id = b.book_id)),"
                   " (SELECT COUNT(*) FROM copies WHERE acquired_on = '2026-07-01')"),
        note="INSERT ... SELECT inserts whatever the SELECT returns, and"
             " the NOT EXISTS is what makes it IDEMPOTENT: the second"
             " run finds every book stocked and inserts nothing. Without"
             " it all six hundred titles get a new copy every time the"
             " script runs. Twenty books lacked a copy; twenty copies"
             " are added.",
        claims=[("twenty copies added, none missing",
                 lambda rows, c: rows == [(2246, 0, 20)])],
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
