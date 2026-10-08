"""Practice exercises: fifteen questions on the library schema.

The fourth set on the library (SEED 861), and a REVISION set: the tiers
pair up concepts the three library sets before it introduced, in a new
order, with every question new. Dates and set operations -- loans by
weekday, fined AND waiting by INTERSECT. Grain and CASE -- two children of
a branch counted without multiplying, fines banded by a CASE whose order
matters. Windows and recursion -- the second most borrowed title per
genre, the gap between one loan of a copy and the next by LAG, a calendar
of weeks with a half-open boundary. EXISTS and text -- books stocked at
every branch by a double NOT EXISTS, words per title by LENGTH and
REPLACE, initials by || . Intervals and NULLs -- two loans out at once
with the open end supplied, holds counted three ways in one row. And
three WRITABLE questions:

  * an AFTER UPDATE trigger that raises a fine when a loan comes back late
  * an UPDATE whose WHERE is a correlated count
  * a view of what each member owes

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script -- the returns your trigger should
price.
"""

import sqlite3

EXERCISES = [
    # ============================================ 1 Dates and set operations
    dict(
        id=1, ledger="Q892", concept="D1", tier="1 - Dates and set operations",
        title="Loans by day of the week",
        prompt=(
            "How many loans started on each day of the week, with the day"
            " as strftime's %w gives it: '0' for Sunday through '6' for"
            " Saturday.\n\n"
            "Return: weekday, loans"
        ),
        solution="SELECT strftime('%w', loaned_on), COUNT(*) FROM loans GROUP BY 1",
        trap_sql="SELECT strftime('%W', loaned_on), COUNT(*) FROM loans GROUP BY 1",
        note="strftime's letters are case-sensitive: %w is the day of the"
             " week, %W is the week of the year, and the second gives"
             " fifty-three groups instead of seven. The library lends"
             " seven days a week, and the counts are close to even.",
        claims=[("seven days, each with three thousand or so",
                 lambda rows, c: len(rows) == 7 and all(3300 < r[1] < 3600 for r in rows))],
    ),
    dict(
        id=2, ledger="Q893", concept="S1", tier="1 - Dates and set operations",
        title="Fined and waiting",
        prompt=(
            "Members who have had a fine -- any fine, paid or not -- AND"
            " have placed a hold -- any hold. Use INTERSECT between a"
            " query over fines, joined to loans for the member, and a"
            " query over holds.\n\n"
            "Return: member_id"
        ),
        solution=("SELECT l.member_id FROM fines f JOIN loans l ON l.loan_id = f.loan_id"
                  " INTERSECT SELECT member_id FROM holds"),
        trap_sql=("SELECT l.member_id FROM fines f JOIN loans l ON l.loan_id = f.loan_id"
                  " UNION SELECT member_id FROM holds"),
        note="INTERSECT keeps the rows both queries have; UNION keeps the"
             " rows either has, so it answers 'fined OR waiting' and"
             " returns four hundred more members. Both remove duplicates,"
             " so a member with ten fines is one row. Fines reach the"
             " member through loans.",
        claims=[("eight hundred or so members",
                 lambda rows, c: 780 < len(rows) < 840)],
    ),
    # ===================================================== 2 Grain and CASE
    dict(
        id=3, ledger="Q894", concept="C2", tier="2 - Grain and CASE",
        title="Staff and copies, per branch",
        prompt=(
            "For each branch: how many staff work there and how many"
            " copies it holds. Staff and copies are two separate children"
            " of a branch, and joining both to branches in one FROM"
            " multiplies them together.\n\n"
            "Return: branch_id, staff, copies"
        ),
        solution=("SELECT b.branch_id, (SELECT COUNT(*) FROM staff s WHERE s.branch_id = b.branch_id),"
                  " (SELECT COUNT(*) FROM copies c WHERE c.branch_id = b.branch_id) FROM branches b"),
        trap_sql=("SELECT b.branch_id, COUNT(s.staff_id), COUNT(c.copy_id) FROM branches b"
                  " JOIN staff s ON s.branch_id = b.branch_id"
                  " JOIN copies c ON c.branch_id = b.branch_id GROUP BY b.branch_id"),
        note="Two one-to-many joins from the same parent give staff times"
             " copies rows per branch, and both COUNTs are of that"
             " product -- five staff and 381 copies become 1,905 of each."
             " Count each child on its own: a scalar subquery per column,"
             " or COUNT(DISTINCT ...), or two grouped subqueries joined"
             " back to branches.",
        claims=[("six branches, five or six staff and a few hundred copies",
                 lambda rows, c: len(rows) == 6
                 and all(4 <= r[1] <= 7 and 300 < r[2] < 450 for r in rows))],
    ),
    dict(
        id=4, ledger="Q895", concept="C7", tier="2 - Grain and CASE",
        title="Fines in bands",
        prompt=(
            "Put every fine in a band by amount_pence and count and total"
            " each band: 'small' up to 100, 'medium' up to 500, 'capped'"
            " when exactly 1000 -- the cap -- and 'large' for the rest."
            " The order of the WHENs is part of the answer.\n\n"
            "Return: band, fines, pence"
        ),
        solution=("SELECT CASE WHEN amount_pence <= 100 THEN 'small'"
                  " WHEN amount_pence <= 500 THEN 'medium'"
                  " WHEN amount_pence = 1000 THEN 'capped' ELSE 'large' END,"
                  " COUNT(*), SUM(amount_pence) FROM fines GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN amount_pence <= 500 THEN 'medium'"
                  " WHEN amount_pence <= 100 THEN 'small'"
                  " WHEN amount_pence = 1000 THEN 'capped' ELSE 'large' END,"
                  " COUNT(*), SUM(amount_pence) FROM fines GROUP BY 1"),
        note="CASE stops at the first WHEN that is true. With <= 500"
             " tested before <= 100, every small fine is already"
             " 'medium' by the time the second WHEN is reached, and the"
             " 'small' band is empty. Bands tested from the narrowest"
             " condition outward do not need the lower bound written.",
        claims=[("four bands, the capped ones all 1000",
                 lambda rows, c: len(rows) == 4
                 and dict((r[0], r[2] / r[1]) for r in rows)['capped'] == 1000
                 and sum(r[1] for r in rows) == 4085)],
    ),
    # ============================================= 3 Windows and recursion
    dict(
        id=5, ledger="Q896", concept="W2", tier="3 - Windows and recursion",
        title="The runner-up in each genre",
        prompt=(
            "For each genre, the SECOND most borrowed book: its book_id"
            " and loan count. Order books within a genre by loans"
            " descending, ties broken by the lower book_id, and take the"
            " one in position 2 -- ROW_NUMBER, not RANK.\n\n"
            "Return: genre, book_id, loans"
        ),
        solution=("SELECT genre, book_id, n FROM (SELECT b.genre, b.book_id, COUNT(*) AS n,"
                  " ROW_NUMBER() OVER (PARTITION BY b.genre ORDER BY COUNT(*) DESC, b.book_id) AS rn"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " JOIN books b ON b.book_id = c.book_id GROUP BY b.book_id) WHERE rn = 2"),
        trap_sql=("SELECT genre, book_id, n FROM (SELECT b.genre, b.book_id, COUNT(*) AS n,"
                  " RANK() OVER (PARTITION BY b.genre ORDER BY COUNT(*) DESC) AS rn"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " JOIN books b ON b.book_id = c.book_id GROUP BY b.book_id) WHERE rn = 2"),
        note="RANK gives tied rows the same number and skips the next,"
             " so a genre whose top two books tie has two rank-1 rows and"
             " no rank 2 at all, and a genre with a tie for second has"
             " two. ROW_NUMBER with a tie-break in its ORDER BY numbers"
             " every row once, and 'position 2' means exactly one row"
             " per genre.",
        claims=[("eight genres, one runner-up each",
                 lambda rows, c: len(rows) == 8 and len({r[0] for r in rows}) == 8
                 and all(90 <= r[2] <= 100 for r in rows))],
    ),
    dict(
        id=6, ledger="Q897", concept="W3", tier="3 - Windows and recursion",
        title="How long copy 1 sat on the shelf",
        prompt=(
            "For each loan of copy 1, in order of loaned_on: loan_id,"
            " loaned_on, and the number of days between the PREVIOUS"
            " loan's return and this loan's start -- NULL for the first."
            " LAG over returned_on, then julianday arithmetic.\n\n"
            "Return: loan_id, loaned_on, shelf_days"
        ),
        solution=("SELECT loan_id, loaned_on, CAST(julianday(loaned_on)"
                  " - julianday(LAG(returned_on) OVER (ORDER BY loaned_on)) AS INTEGER)"
                  " FROM loans WHERE copy_id = 1"),
        trap_sql=("SELECT loan_id, loaned_on, CAST(julianday(loaned_on)"
                  " - julianday(LAG(loaned_on) OVER (ORDER BY loaned_on)) AS INTEGER)"
                  " FROM loans WHERE copy_id = 1"),
        note="LAG(returned_on) reaches back to the previous row's RETURN,"
             " which is when the copy came back to the shelf; LAG("
             "loaned_on) measures from the previous loan's start, which"
             " includes the time the copy was out. The window needs its"
             " own ORDER BY -- the WHERE narrows the rows, the OVER"
             " clause orders them.",
        claims=[("fourteen loans, the first with no gap, the rest positive",
                 lambda rows, c: len(rows) == 14
                 and sum(r[2] is None for r in rows) == 1
                 and all(r[2] is None or r[2] >= 0 for r in rows))],
    ),
    dict(
        id=7, ledger="Q898", concept="R1", tier="3 - Windows and recursion",
        title="Twelve weeks of loans",
        prompt=(
            "For each of the twelve weeks starting Monday 2026-01-05: the"
            " week's first day and how many loans started in it -- from"
            " that Monday up to but NOT including the next. Build the"
            " Mondays with a recursive CTE, date(start, '+7 days').\n\n"
            "Return: week_start, loans"
        ),
        solution=("WITH RECURSIVE w(start) AS (SELECT '2026-01-05' UNION ALL"
                  " SELECT date(start, '+7 days') FROM w WHERE start < '2026-03-23')"
                  " SELECT start, (SELECT COUNT(*) FROM loans l WHERE l.loaned_on >= w.start"
                  " AND l.loaned_on < date(w.start, '+7 days')) FROM w"),
        trap_sql=("WITH RECURSIVE w(start) AS (SELECT '2026-01-05' UNION ALL"
                  " SELECT date(start, '+7 days') FROM w WHERE start < '2026-03-23')"
                  " SELECT start, (SELECT COUNT(*) FROM loans l WHERE l.loaned_on >= w.start"
                  " AND l.loaned_on <= date(w.start, '+7 days')) FROM w"),
        note="A week is a half-open interval: Monday inclusive, next Monday"
             " exclusive. With <= the next Monday's loans are counted in"
             " both weeks, and every total is forty or so too high. The"
             " recursion stops at the twelfth Monday because the WHERE"
             " compares the start it is about to extend from.",
        claims=[("twelve weeks of about three hundred",
                 lambda rows, c: len(rows) == 12 and all(280 <= r[1] <= 340 for r in rows)
                 and min(rows)[0] == '2026-01-05' and max(rows)[0] == '2026-03-23')],
    ),
    # ==================================================== 4 EXISTS and text
    dict(
        id=8, ledger="Q899", concept="E1", tier="4 - EXISTS and text",
        title="Stocked at every branch",
        prompt=(
            "Books that have at least one copy at EVERY branch -- all"
            " six. 'Every' is a double negative: no branch exists at which"
            " no copy of the book exists.\n\n"
            "Return: book_id, title"
        ),
        solution=("SELECT b.book_id, b.title FROM books b WHERE NOT EXISTS ("
                  "SELECT 1 FROM branches br WHERE NOT EXISTS ("
                  "SELECT 1 FROM copies c WHERE c.book_id = b.book_id AND c.branch_id = br.branch_id))"),
        trap_sql=("SELECT b.book_id, b.title FROM books b JOIN copies c ON c.book_id = b.book_id"
                  " GROUP BY b.book_id HAVING COUNT(*) >= 6"),
        note="Six copies is not six branches: a book can have six copies"
             " at two branches. COUNT(DISTINCT c.branch_id) = 6 in the"
             " HAVING would also be right, and is the shorter way; the"
             " nested NOT EXISTS is the general shape of 'for all', which"
             " SQL does not have a word for.",
        claims=[("seven books",
                 lambda rows, c: len(rows) == 7)],
    ),
    dict(
        id=9, ledger="Q900", concept="STR", tier="4 - EXISTS and text",
        title="Words per title",
        prompt=(
            "How many titles have two words, three, four and five. Count"
            " the spaces -- LENGTH of the title minus LENGTH with the"
            " spaces removed -- and remember that words are one more than"
            " spaces.\n\n"
            "Return: words, titles"
        ),
        solution=("SELECT LENGTH(title) - LENGTH(REPLACE(title, ' ', '')) + 1, COUNT(*)"
                  " FROM books GROUP BY 1"),
        trap_sql=("SELECT LENGTH(title) - LENGTH(REPLACE(title, ' ', '')), COUNT(*)"
                  " FROM books GROUP BY 1"),
        note="SQLite has no word-count function, and the idiom is to"
             " measure what disappears when the separator is removed."
             " That counts separators; the fencepost +1 turns spaces"
             " into words. Without it every group is labelled one short.",
        claims=[("two to five words, six hundred titles",
                 lambda rows, c: [r[0] for r in sorted(rows)] == [2, 3, 4, 5]
                 and sum(r[1] for r in rows) == 600)],
    ),
    dict(
        id=10, ledger="Q901", concept="STR", tier="4 - EXISTS and text",
        title="Staff initials",
        prompt=(
            "Each staff member's initials: the first letter of the name"
            " and the first letter after the space, joined with ||."
            " SUBSTR takes (text, start, length) and INSTR finds the"
            " space.\n\n"
            "Return: staff_id, initials"
        ),
        solution=("SELECT staff_id, SUBSTR(name, 1, 1) || SUBSTR(name, INSTR(name, ' ') + 1, 1)"
                  " FROM staff"),
        trap_sql=("SELECT staff_id, SUBSTR(name, 1, 1) || SUBSTR(name, INSTR(name, ' '), 1)"
                  " FROM staff"),
        note="|| is SQL's string concatenation -- not +, which in SQLite"
             " tries to add the two as numbers and gives 0. The second"
             " SUBSTR starts one past the space, and the third argument"
             " limits it to one character; without the +1 the 'initial'"
             " is the space itself.",
        claims=[("thirty-one pairs of capitals",
                 lambda rows, c: len(rows) == 31
                 and all(len(r[1]) == 2 and r[1].isupper() for r in rows))],
    ),
    # ================================================= 5 Intervals and NULLs
    dict(
        id=11, ledger="Q902", concept="INT", tier="5 - Intervals and NULLs",
        title="Two books out at once",
        prompt=(
            "For each home branch, how many of its members have at some"
            " point had two loans out at the same time: two loans of"
            " theirs whose intervals overlap, a loan still out running to"
            " the end of the data. Pair each loan with a later loan_id of"
            " the same member, and supply the open end with COALESCE.\n\n"
            "Return: home_branch_id, members"
        ),
        solution=("SELECT m.home_branch_id, COUNT(*) FROM members m WHERE EXISTS ("
                  "SELECT 1 FROM loans a JOIN loans b ON b.member_id = a.member_id AND b.loan_id > a.loan_id"
                  " WHERE a.member_id = m.member_id"
                  " AND a.loaned_on <= COALESCE(b.returned_on, '9999')"
                  " AND b.loaned_on <= COALESCE(a.returned_on, '9999'))"
                  " GROUP BY m.home_branch_id"),
        trap_sql=("SELECT m.home_branch_id, COUNT(*) FROM members m WHERE EXISTS ("
                  "SELECT 1 FROM loans a JOIN loans b ON b.member_id = a.member_id AND b.loan_id > a.loan_id"
                  " WHERE a.member_id = m.member_id"
                  " AND a.loaned_on <= b.returned_on AND b.loaned_on <= a.returned_on)"
                  " GROUP BY m.home_branch_id"),
        note="Two intervals overlap when each starts before the other"
             " ends -- the test every interval question comes back to."
             " A loan still out has no end, and a comparison with NULL"
             " is never true, so without COALESCE the members whose only"
             " overlap involves an open loan are missed. Almost every"
             " borrower has doubled up at some point.",
        claims=[("six branches, almost every borrower",
                 lambda rows, c: len(rows) == 6 and 1200 < sum(r[1] for r in rows) < 1300)],
    ),
    dict(
        id=12, ledger="Q903", concept="N1", tier="5 - Intervals and NULLs",
        title="Holds, three ways, per branch",
        prompt=(
            "For each branch the hold was placed at: holds placed, how"
            " many were fulfilled, how many cancelled, and how many are"
            " still waiting -- neither. COUNT(column) counts the non-NULL"
            " values, and waiting is not 'placed minus fulfilled'.\n\n"
            "Return: branch_id, placed, fulfilled, cancelled, waiting"
        ),
        solution=("SELECT branch_id, COUNT(*), COUNT(fulfilled_on), COUNT(cancelled_on),"
                  " SUM(fulfilled_on IS NULL AND cancelled_on IS NULL) FROM holds GROUP BY branch_id"),
        trap_sql=("SELECT branch_id, COUNT(*), COUNT(fulfilled_on), COUNT(cancelled_on),"
                  " COUNT(*) - COUNT(fulfilled_on) FROM holds GROUP BY branch_id"),
        note="COUNT(fulfilled_on) is the number of holds with a"
             " fulfilment date, which is the NULL-counting rule put to"
             " work. 'Waiting' has two NULLs to test, and placed minus"
             " fulfilled counts the cancelled holds as waiting. SUM of"
             " a boolean is the other idiom for a conditional count.",
        claims=[("six branches, the four parts adding up",
                 lambda rows, c: len(rows) == 6
                 and all(r[2] + r[3] + r[4] == r[1] for r in rows)
                 and sum(r[4] for r in rows) == 337)],
    ),
    # ================================================= 6 Changing the data
    dict(
        id=13, ledger="Q904", concept="TRG", tier="6 - Changing the data",
        kind="script",
        title="A fine the moment a book comes back late",
        prompt=(
            "Write an AFTER UPDATE trigger on loans that fires when"
            " returned_on changes from NULL to a date AFTER due_on, and"
            " inserts a fine for that loan: 20 pence a day late, capped"
            " at 1000, issued_on the return date. A return on or before"
            " due_on raises nothing. The question then returns loan 4107"
            " (due 2026-06-20) on 2026-07-10, and loan 6876 on its due"
            " date.\n\n"
            "Checked: how many new fines there are, the amount of loan"
            " 4107's, and whether loan 6876 is marked returned"
        ),
        solution=("CREATE TRIGGER fine_late_return AFTER UPDATE OF returned_on ON loans\n"
                  "WHEN OLD.returned_on IS NULL AND NEW.returned_on > NEW.due_on\n"
                  "BEGIN\n"
                  "  INSERT INTO fines (loan_id, amount_pence, issued_on)\n"
                  "  VALUES (NEW.loan_id,\n"
                  "          MIN(20 * CAST(julianday(NEW.returned_on) - julianday(NEW.due_on) AS INTEGER), 1000),\n"
                  "          NEW.returned_on);\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER fine_late_return AFTER UPDATE OF returned_on ON loans\n"
                  "WHEN OLD.returned_on IS NULL\n"
                  "BEGIN\n"
                  "  INSERT INTO fines (loan_id, amount_pence, issued_on)\n"
                  "  VALUES (NEW.loan_id,\n"
                  "          MIN(20 * CAST(julianday(NEW.returned_on) - julianday(NEW.due_on) AS INTEGER), 1000),\n"
                  "          NEW.returned_on);\n"
                  "END;"),
        driver_sql=("UPDATE loans SET returned_on = '2026-07-10' WHERE loan_id = 4107;\n"
                    "UPDATE loans SET returned_on = due_on WHERE loan_id = 6876;"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM fines WHERE fine_id > 4085),"
                   " (SELECT amount_pence FROM fines WHERE fine_id > 4085 AND loan_id = 4107),"
                   " (SELECT returned_on IS NOT NULL FROM loans WHERE loan_id = 6876)"),
        note="AFTER UPDATE sees both versions of the row: OLD.returned_on"
             " says the loan was open, NEW.returned_on says when it came"
             " back, and the WHEN decides whether the trigger fires at"
             " all. Without the late test the on-time return is fined 0"
             " pence, which the fines table's CHECK (amount_pence > 0)"
             " refuses -- and that refusal aborts the UPDATE itself, so"
             " the loan is not even marked returned. MIN(x, 1000) is the"
             " two-argument scalar.",
        claims=[("one fine of 400 pence, and the on-time return recorded",
                 lambda rows, c: rows == [(1, 400, 1)])],
    ),
    dict(
        id=14, ledger="Q905", concept="DML", tier="6 - Changing the data",
        kind="script",
        title="Well-thumbed copies",
        prompt=(
            "Mark as 'worn' every copy in 'good' condition that has been"
            " loaned 15 times or more. Copies already worn or damaged are"
            " left as they are, whatever their loan count. The count is a"
            " correlated subquery in the WHERE.\n\n"
            "Checked: how many copies are in each condition"
        ),
        solution=("UPDATE copies SET condition = 'worn' WHERE condition = 'good'"
                  " AND (SELECT COUNT(*) FROM loans l WHERE l.copy_id = copies.copy_id) >= 15;"),
        trap_sql=("UPDATE copies SET condition = 'worn'"
                  " WHERE (SELECT COUNT(*) FROM loans l WHERE l.copy_id = copies.copy_id) >= 15;"),
        probe_sql="SELECT condition, COUNT(*) FROM copies GROUP BY condition ORDER BY condition",
        note="An UPDATE can test each row against a subquery that refers"
             " to it -- copies.copy_id inside the count -- and that is how"
             " a condition on another table reaches a WHERE. The"
             " condition = 'good' is the half that is easy to drop, and"
             " dropping it promotes damaged copies to worn.",
        claims=[("damaged untouched, worn up by the heavily loaned good copies",
                 lambda rows, c: dict(rows)['damaged'] == 223
                 and dict(rows)['good'] < 1309 and dict(rows)['worn'] == 694 + 1309 - dict(rows)['good'])],
    ),
    dict(
        id=15, ledger="Q906", concept="VIEW", tier="6 - Changing the data",
        kind="script",
        title="What each member owes",
        prompt=(
            "Create a view `member_debts (member_id, owed_pence)` with one"
            " row per member who has at least one UNPAID fine, and the"
            " total of their unpaid fines. Members with no unpaid fines"
            " are not in the view, nor are paid fines in the total.\n\n"
            "Checked: how many members the view holds, what they owe in"
            " all, and member 1149's row"
        ),
        solution=("CREATE VIEW member_debts AS\n"
                  "  SELECT l.member_id, SUM(f.amount_pence) AS owed_pence\n"
                  "  FROM fines f JOIN loans l ON l.loan_id = f.loan_id\n"
                  "  WHERE f.paid_on IS NULL GROUP BY l.member_id;"),
        trap_sql=("CREATE VIEW member_debts AS\n"
                  "  SELECT l.member_id, SUM(f.amount_pence) AS owed_pence\n"
                  "  FROM fines f JOIN loans l ON l.loan_id = f.loan_id\n"
                  "  GROUP BY l.member_id;"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM member_debts), (SELECT SUM(owed_pence) FROM member_debts),"
                   " (SELECT owed_pence FROM member_debts WHERE member_id = 1149)"),
        note="The WHERE goes before the GROUP BY, and it is what makes"
             " this a view of DEBTS rather than of fines ever raised:"
             " without it every member who was ever late is listed with"
             " their lifetime total. A view of a grouped query is still"
             " queried like a table -- the probe reads it three ways.",
        claims=[("seven hundred or so debtors, 1149 owing 6480",
                 lambda rows, c: rows == [(719, 414960, 6480)])],
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
