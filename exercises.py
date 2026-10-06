"""Practice exercises: fifteen questions on the library schema.

The second set on the library (SEED 861), with the TOPICS mixed up: the
seven stages the hospital sets wore for a year are gone, and the tiers
are now set operations, CASE, self-joins and EXISTS, recursive CTEs, text
and NULLs, and changing the data. Twelve SELECT questions -- borrowers
who never queue by EXCEPT, one member's loans and holds in one list by
UNION ALL, a condition pivot by SUM over CASE, four classes of loan with
the NULL branch first, colleagues in the same role each pair once, books
stocked but never borrowed through copies, in debt AND still holding a
book as two EXISTS, a calendar with the empty day kept, a repayment plan
by recursion, surnames by SUBSTR and INSTR, an 'unknown' label by COALESCE,
and days late on average with on-time as zero -- and three WRITABLE:

  * CREATE TABLE and INSERT ... SELECT to fill a stock table
  * a DELETE with two conditions, where the one forgotten destroys history
  * ALTER TABLE ADD COLUMN and an UPDATE that remembers the never-borrowers

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
    # ==================================================== 1 Set operations
    dict(
        id=1, ledger="Q862", concept="S1", tier="1 - Set operations",
        title="Borrowers who never queue",
        prompt=(
            "Members who have borrowed at least once but have never placed"
            " a hold. Use EXCEPT: one SELECT over loans, one over holds."
            " Members who have never borrowed are not wanted.\n\n"
            "Return: member_id"
        ),
        solution="SELECT member_id FROM loans EXCEPT SELECT member_id FROM holds",
        trap_sql="SELECT member_id FROM members EXCEPT SELECT member_id FROM holds",
        note="EXCEPT keeps the rows of the first SELECT that the second"
             " does not have, and removes duplicates on the way, so a"
             " member with fifty loans comes out once. Which table the"
             " first SELECT reads decides who is being subtracted FROM:"
             " members gives everyone without a hold, including the two"
             " hundred who have never borrowed either.",
        claims=[("about four hundred borrowers have never held",
                 lambda rows, c: 380 < len(rows) < 450
                 and len({r[0] for r in rows}) == len(rows))],
    ),
    dict(
        id=2, ledger="Q863", concept="S1", tier="1 - Set operations",
        title="One member's history, in one list",
        prompt=(
            "Member 834's loans and holds as ONE list. Each loan is a row"
            " with the kind 'loan', the copy's book_id and loaned_on; each"
            " hold is a row with the kind 'hold', its book_id and the DAY"
            " it was placed, as 'YYYY-MM-DD' -- placed_at carries a time"
            " of day as well.\n\n"
            "Return: kind, book_id, on_day"
        ),
        solution=("SELECT 'loan', c.book_id, l.loaned_on FROM loans l"
                  " JOIN copies c ON c.copy_id = l.copy_id WHERE l.member_id = 834"
                  " UNION ALL"
                  " SELECT 'hold', book_id, date(placed_at) FROM holds WHERE member_id = 834"),
        trap_sql=("SELECT 'loan', c.book_id, l.loaned_on FROM loans l"
                  " JOIN copies c ON c.copy_id = l.copy_id WHERE l.member_id = 834"
                  " UNION ALL"
                  " SELECT 'hold', book_id, placed_at FROM holds WHERE member_id = 834"),
        note="UNION ALL stacks two queries that agree on the number and"
             " meaning of their columns; it does not make the values"
             " agree. loaned_on is a day and placed_at is a day AND a"
             " time, so without date() the third column holds two"
             " different kinds of text. A loan needs the copies join to"
             " reach its book; a hold has the book directly.",
        claims=[("fifteen loans and seven holds",
                 lambda rows, c: sum(r[0] == 'loan' for r in rows) == 15
                 and sum(r[0] == 'hold' for r in rows) == 7
                 and all(len(r[2]) == 10 for r in rows))],
    ),
    # =============================================================== 2 CASE
    dict(
        id=3, ledger="Q864", concept="C7", tier="2 - CASE",
        title="Condition of the stock, one row a branch",
        prompt=(
            "For each branch, ONE row with the number of its copies in"
            " each condition as three columns: good, worn, damaged. That"
            " is a pivot -- SUM over a CASE, or over a comparison. Count"
            " withdrawn copies too.\n\n"
            "Return: branch_id, good, worn, damaged"
        ),
        solution=("SELECT branch_id, SUM(condition = 'good'), SUM(condition = 'worn'),"
                  " SUM(condition = 'damaged') FROM copies GROUP BY branch_id"),
        trap_sql=("SELECT branch_id, COUNT(CASE WHEN condition = 'good' THEN 1 ELSE 0 END),"
                  " COUNT(CASE WHEN condition = 'worn' THEN 1 ELSE 0 END),"
                  " COUNT(CASE WHEN condition = 'damaged' THEN 1 ELSE 0 END)"
                  " FROM copies GROUP BY branch_id"),
        note="A GROUP BY condition gives three rows a branch; a pivot"
             " wants three columns, and the tool is a conditional SUM:"
             " SUM(condition = 'good') adds a 1 for every match and a 0"
             " otherwise. COUNT with an ELSE 0 counts the zeros as well --"
             " COUNT counts non-NULL values, and 0 is a value -- so all"
             " three columns come out equal to the branch's total. CASE"
             " ... THEN 1 END with no ELSE, or SUM, is the fix.",
        claims=[("six branches, the three columns adding up to the stock",
                 lambda rows, c: len(rows) == 6
                 and sum(r[1] + r[2] + r[3] for r in rows)
                 == c.execute("SELECT COUNT(*) FROM copies").fetchone()[0]
                 and all(r[1] > r[2] > r[3] for r in rows))],
    ),
    dict(
        id=4, ledger="Q865", concept="C7", tier="2 - CASE",
        title="How loans ended",
        prompt=(
            "Put every loan in one of four classes and count each: 'out'"
            " when returned_on is NULL, 'early' when it was returned"
            " before due_on, 'on time' when returned on due_on, and 'late'"
            " when returned after it.\n\n"
            "Return: class, loans"
        ),
        solution=("SELECT CASE WHEN returned_on IS NULL THEN 'out'"
                  " WHEN returned_on < due_on THEN 'early'"
                  " WHEN returned_on = due_on THEN 'on time' ELSE 'late' END, COUNT(*)"
                  " FROM loans GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN returned_on < due_on THEN 'early'"
                  " WHEN returned_on = due_on THEN 'on time' ELSE 'late' END, COUNT(*)"
                  " FROM loans GROUP BY 1"),
        note="CASE takes the first WHEN that is TRUE, and a comparison"
             " with NULL is neither true nor false, so an open loan falls"
             " past 'early' and 'on time' into the ELSE and is counted as"
             " late. The NULL test goes FIRST, with IS NULL, and then the"
             " comparisons can assume a value is there. 'late' here"
             " should equal the number of fines, because every late"
             " return raised one.",
        claims=[("four classes, late equal to the fines, seven hundred or so out",
                 lambda rows, c: len(rows) == 4
                 and dict((r[0], r[1]) for r in rows)['late']
                 == c.execute("SELECT COUNT(*) FROM fines").fetchone()[0]
                 and 600 < dict((r[0], r[1]) for r in rows)['out'] < 800)],
    ),
    # ============================================== 3 Self-joins and EXISTS
    dict(
        id=5, ledger="Q866", concept="J1", tier="3 - Self-joins and EXISTS",
        title="Colleagues in the same role",
        prompt=(
            "Pairs of staff who work at the same branch in the same role,"
            " each pair ONCE, with the lower staff_id first. Nobody is"
            " paired with themselves.\n\n"
            "Return: branch_id, role, staff_a, staff_b"
        ),
        solution=("SELECT a.branch_id, a.role, a.staff_id, b.staff_id FROM staff a"
                  " JOIN staff b ON b.branch_id = a.branch_id AND b.role = a.role"
                  " AND b.staff_id > a.staff_id"),
        trap_sql=("SELECT a.branch_id, a.role, a.staff_id, b.staff_id FROM staff a"
                  " JOIN staff b ON b.branch_id = a.branch_id AND b.role = a.role"
                  " AND b.staff_id <> a.staff_id"),
        note="A self-join reads one table twice under two aliases. The"
             " condition that keeps a person off their own row is <>, but"
             " <> gives every pair twice -- (4, 5) and (5, 4) -- so the"
             " pair is made ONCE with a strict inequality, b.staff_id >"
             " a.staff_id, which also puts the lower id first. Managers"
             " never appear: each branch has at most one.",
        claims=[("sixteen pairs, no managers among them",
                 lambda rows, c: len(rows) == 16
                 and all(r[2] < r[3] and r[1] != 'manager' for r in rows))],
    ),
    dict(
        id=6, ledger="Q867", concept="E1", tier="3 - Self-joins and EXISTS",
        title="Stocked but never borrowed",
        prompt=(
            "Books that have at least one copy and whose copies have NEVER"
            " been loaned: book_id, title, and how many copies there are."
            " A loan points at a copy, not a book, so the test has to go"
            " through copies.\n\n"
            "Return: book_id, title, copies"
        ),
        solution=("SELECT b.book_id, b.title, COUNT(*) FROM books b"
                  " JOIN copies c ON c.book_id = b.book_id"
                  " WHERE NOT EXISTS (SELECT 1 FROM loans l JOIN copies c2 ON c2.copy_id = l.copy_id"
                  "                   WHERE c2.book_id = b.book_id)"
                  " GROUP BY b.book_id"),
        trap_sql=("SELECT b.book_id, b.title, COUNT(*) FROM books b"
                  " JOIN copies c ON c.book_id = b.book_id"
                  " WHERE b.book_id NOT IN (SELECT copy_id FROM loans)"
                  " GROUP BY b.book_id"),
        note="book_id NOT IN (SELECT copy_id FROM loans) compares a book"
             " number with copy numbers -- two different id spaces that"
             " happen to be integers -- and SQLite does not object. The"
             " subquery has to arrive at book_id: loans joined to copies,"
             " correlated on the book. Only two books in the whole"
             " library have a copy nobody has ever taken out.",
        claims=[("two books, one copy each",
                 lambda rows, c: len(rows) == 2 and all(r[2] == 1 for r in rows))],
    ),
    dict(
        id=7, ledger="Q868", concept="E1", tier="3 - Self-joins and EXISTS",
        title="In debt and still holding a book",
        prompt=(
            "Members who owe an UNPAID fine and ALSO have a loan out right"
            " now -- returned_on NULL. A fine hangs off a loan that has"
            " come back, so the loan that is out is a DIFFERENT loan: two"
            " separate tests on the member, not one join.\n\n"
            "Return: member_id"
        ),
        solution=("SELECT m.member_id FROM members m"
                  " WHERE EXISTS (SELECT 1 FROM fines f JOIN loans l ON l.loan_id = f.loan_id"
                  "               WHERE l.member_id = m.member_id AND f.paid_on IS NULL)"
                  " AND EXISTS (SELECT 1 FROM loans l WHERE l.member_id = m.member_id"
                  "             AND l.returned_on IS NULL)"),
        trap_sql=("SELECT DISTINCT l.member_id FROM fines f JOIN loans l ON l.loan_id = f.loan_id"
                  " WHERE f.paid_on IS NULL AND l.returned_on IS NULL"),
        note="One join from fines to loans puts both conditions on the"
             " SAME loan, and a loan that raised a fine was returned late,"
             " so it is never still out: the result is empty. Two EXISTS"
             " each ask their own question of the member -- any unpaid"
             " fine? any open loan? -- and the member is the only thing"
             " they share.",
        claims=[("two hundred and fifty or so members",
                 lambda rows, c: 230 < len(rows) < 290)],
    ),
    # ===================================================== 4 Recursive CTEs
    dict(
        id=8, ledger="Q869", concept="R1", tier="4 - Recursive CTEs",
        title="Every day of March, holds or not",
        prompt=(
            "For EVERY day of March 2026, how many holds were placed that"
            " day -- including the day with none, which a GROUP BY over"
            " holds alone cannot produce. Build the days with a recursive"
            " CTE, date(day, '+1 day'), and count the holds whose"
            " date(placed_at) is that day.\n\n"
            "Return: day, holds"
        ),
        solution=("WITH RECURSIVE d(day) AS (SELECT '2026-03-01' UNION ALL"
                  " SELECT date(day, '+1 day') FROM d WHERE day < '2026-03-31')"
                  " SELECT d.day, (SELECT COUNT(*) FROM holds h WHERE date(h.placed_at) = d.day)"
                  " FROM d"),
        trap_sql=("SELECT date(placed_at), COUNT(*) FROM holds"
                  " WHERE placed_at >= '2026-03-01' AND placed_at < '2026-04-01'"
                  " GROUP BY 1"),
        note="A table can only group what it has: a day with no holds has"
             " no row to group. The recursive CTE manufactures the thirty-"
             "one days -- anchor the 1st, step +1 day until the 31st --"
             " and the count is then a correlated subquery or a LEFT JOIN"
             " from the calendar, so the empty day keeps a 0. Note"
             " date(placed_at) on the holds side: placed_at has a time.",
        claims=[("thirty-one days, exactly one of them empty",
                 lambda rows, c: len(rows) == 31
                 and sum(r[1] == 0 for r in rows) == 1
                 and sum(r[1] for r in rows) ==
                 c.execute("SELECT COUNT(*) FROM holds WHERE placed_at >= '2026-03-01'"
                           " AND placed_at < '2026-04-01'").fetchone()[0])],
    ),
    dict(
        id=9, ledger="Q870", concept="R1", tier="4 - Recursive CTEs",
        title="Paying it off in instalments",
        prompt=(
            "Member 1149 owes 6480 pence. They pay 1000 pence on"
            " 2026-07-01 and the same again every 7 days until nothing is"
            " owed. List the instalments: its number, the day, and what"
            " remains AFTER it -- never below zero, so the last payment"
            " only clears the 480 left. Use a recursive CTE.\n\n"
            "Return: instalment, pay_on, remaining"
        ),
        solution=("WITH RECURSIVE p(instalment, pay_on, remaining) AS ("
                  " SELECT 1, '2026-07-01', MAX(6480 - 1000, 0)"
                  " UNION ALL SELECT instalment + 1, date(pay_on, '+7 days'),"
                  " MAX(remaining - 1000, 0) FROM p WHERE remaining > 0)"
                  " SELECT instalment, pay_on, remaining FROM p"),
        trap_sql=("WITH RECURSIVE p(instalment, pay_on, remaining) AS ("
                  " SELECT 1, '2026-07-01', 6480 - 1000"
                  " UNION ALL SELECT instalment + 1, date(pay_on, '+7 days'),"
                  " remaining - 1000 FROM p WHERE remaining > 0)"
                  " SELECT instalment, pay_on, remaining FROM p"),
        note="A recursive CTE is a loop: the anchor is the first"
             " instalment, the recursive part makes the next from the"
             " last, and the WHERE is the stopping test -- no more rows"
             " once nothing remains. Without the clamp the seventh row"
             " shows -520 owed: the member has overpaid. SQLite's"
             " two-argument MAX(a, b) is a scalar, the larger of the two,"
             " not the aggregate.",
        claims=[("seven instalments, the last leaving nothing",
                 lambda rows, c: len(rows) == 7
                 and max(rows)[2] == 0 and min(r[2] for r in rows) == 0
                 and max(r[1] for r in rows) == '2026-08-12')],
    ),
    # ==================================================== 5 Text and NULLs
    dict(
        id=10, ledger="Q871", concept="STR", tier="5 - Text and NULLs",
        title="Surnames of the staff",
        prompt=(
            "Each staff member's surname: the part of name AFTER the one"
            " space in it, without the space. INSTR finds the space and"
            " SUBSTR takes from a position to the end.\n\n"
            "Return: staff_id, surname"
        ),
        solution="SELECT staff_id, SUBSTR(name, INSTR(name, ' ') + 1) FROM staff",
        trap_sql="SELECT staff_id, SUBSTR(name, INSTR(name, ' ')) FROM staff",
        note="INSTR returns the position OF the space, and SUBSTR from"
             " that position starts with it -- ' Ekwueme', which is not"
             " the same text as 'Ekwueme' however much it looks like it"
             " in a results grid. The +1 steps past the space. SUBSTR"
             " with no length runs to the end of the string.",
        claims=[("thirty-one surnames, none with a space",
                 lambda rows, c: len(rows) == 31
                 and all(' ' not in r[1] and r[1][0].isupper() for r in rows))],
    ),
    dict(
        id=11, ledger="Q872", concept="N1", tier="5 - Text and NULLs",
        title="Where branch 4's members live",
        prompt=(
            "For the members whose home branch is 4: how many live in"
            " each postcode area, with the members whose area was never"
            " recorded counted together under the label 'unknown'.\n\n"
            "Return: area, members"
        ),
        solution=("SELECT COALESCE(postcode_area, 'unknown'), COUNT(*) FROM members"
                  " WHERE home_branch_id = 4 GROUP BY 1"),
        trap_sql=("SELECT postcode_area, COUNT(*) FROM members"
                  " WHERE home_branch_id = 4 GROUP BY 1"),
        note="GROUP BY puts all the NULL areas in one group, which is the"
             " right grouping -- but the group's label is NULL, not the"
             " word the question asked for. COALESCE(postcode_area,"
             " 'unknown') gives the NULLs a name, and grouping by that"
             " expression (GROUP BY 1, or repeat the expression) labels"
             " the group.",
        claims=[("sixteen areas, nineteen unknown",
                 lambda rows, c: len(rows) == 16
                 and dict(rows)['unknown'] == 19
                 and None not in dict(rows))],
    ),
    dict(
        id=12, ledger="Q873", concept="N1", tier="5 - Text and NULLs",
        title="Days late on average, on time counting as zero",
        prompt=(
            "For each branch, over the RETURNED loans of its copies: the"
            " average number of days late, to two decimals, where a loan"
            " returned on time or early counts as 0 days late -- not as"
            " missing. julianday(returned_on) - julianday(due_on) is the"
            " days late, negative when early.\n\n"
            "Return: branch_id, avg_days_late"
        ),
        solution=("SELECT c.branch_id, ROUND(AVG(MAX(julianday(l.returned_on) - julianday(l.due_on), 0)), 2)"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " WHERE l.returned_on IS NOT NULL GROUP BY c.branch_id"),
        trap_sql=("SELECT c.branch_id, ROUND(AVG(CASE WHEN l.returned_on > l.due_on"
                  " THEN julianday(l.returned_on) - julianday(l.due_on) END), 2)"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " WHERE l.returned_on IS NOT NULL GROUP BY c.branch_id"),
        note="AVG ignores NULLs, so a CASE with no ELSE averages only the"
             " late loans and reports fifteen days where the question"
             " wanted under three. The on-time loans have to contribute a"
             " real 0: MAX(days, 0) clamps the negative values, or a CASE"
             " with ELSE 0. Whether a non-match is NULL or 0 is the whole"
             " difference between 'average among the late' and 'average"
             " over everyone'.",
        claims=[("six branches, all under three days",
                 lambda rows, c: len(rows) == 6
                 and all(2 < r[1] < 3 for r in rows))],
    ),
    # ================================================= 6 Changing the data
    dict(
        id=13, ledger="Q874", concept="DDL", tier="6 - Changing the data",
        kind="script",
        title="A stock table from a query",
        prompt=(
            "Create a table `branch_stock (branch_id INTEGER PRIMARY KEY,"
            " copies INTEGER NOT NULL)` and fill it with one row per"
            " branch: the number of its copies that are NOT withdrawn. Use"
            " INSERT ... SELECT, not typed values.\n\n"
            "Checked: the table's rows"
        ),
        solution=("CREATE TABLE branch_stock (branch_id INTEGER PRIMARY KEY, copies INTEGER NOT NULL);\n"
                  "INSERT INTO branch_stock SELECT branch_id, COUNT(*) FROM copies"
                  " WHERE withdrawn_on IS NULL GROUP BY branch_id;"),
        trap_sql=("CREATE TABLE branch_stock (branch_id INTEGER PRIMARY KEY, copies INTEGER NOT NULL);\n"
                  "INSERT INTO branch_stock SELECT branch_id, COUNT(*) FROM copies"
                  " GROUP BY branch_id;"),
        probe_sql="SELECT branch_id, copies FROM branch_stock ORDER BY branch_id",
        note="INSERT ... SELECT writes a query's rows straight into a"
             " table, one statement for all six branches; the SELECT's"
             " columns line up with the table's by position. The WHERE is"
             " the part of the question that is easy to drop: a hundred"
             " or so copies are withdrawn and are not stock.",
        claims=[("six rows, two thousand one hundred copies in all",
                 lambda rows, c: len(rows) == 6 and rows[0] == (1, 358)
                 and sum(r[1] for r in rows) ==
                 c.execute("SELECT COUNT(*) FROM copies WHERE withdrawn_on IS NULL").fetchone()[0])],
    ),
    dict(
        id=14, ledger="Q875", concept="DML", tier="6 - Changing the data",
        kind="script",
        title="Clear out the old paid fines",
        prompt=(
            "Delete the fines that are PAID and were issued before"
            " 2025-07-01. Unpaid fines from that time stay, however old"
            " they are.\n\n"
            "Checked: how many fines remain, how many of those are"
            " unpaid, and what all the remaining fines add up to"
        ),
        solution="DELETE FROM fines WHERE paid_on IS NOT NULL AND issued_on < '2025-07-01';",
        trap_sql="DELETE FROM fines WHERE issued_on < '2025-07-01';",
        probe_sql="SELECT COUNT(*), SUM(paid_on IS NULL), SUM(amount_pence) FROM fines",
        note="A DELETE's WHERE is the whole statement. Two conditions"
             " were asked for, and the one that gets forgotten -- paid_on"
             " IS NOT NULL -- is the one that matters: without it the"
             " library forgets three hundred debts it is still owed."
             " The probe counts the unpaid fines for exactly that reason.",
        claims=[("thirteen hundred and eighty still unpaid, all of them kept",
                 lambda rows, c: rows == [(3307, 1380, 1008600)])],
    ),
    dict(
        id=15, ledger="Q876", concept="DDL", tier="6 - Changing the data",
        kind="script",
        title="A status column for members",
        prompt=(
            "Add a column `status TEXT NOT NULL DEFAULT 'active'` to"
            " members, then set it to 'lapsed' for every member with no"
            " loan on or after 2026-01-01 -- INCLUDING the members who"
            " have never borrowed at all.\n\n"
            "Checked: how many members carry each status"
        ),
        solution=("ALTER TABLE members ADD COLUMN status TEXT NOT NULL DEFAULT 'active';\n"
                  "UPDATE members SET status = 'lapsed'"
                  " WHERE NOT EXISTS (SELECT 1 FROM loans l WHERE l.member_id = members.member_id"
                  " AND l.loaned_on >= '2026-01-01');"),
        trap_sql=("ALTER TABLE members ADD COLUMN status TEXT NOT NULL DEFAULT 'active';\n"
                  "UPDATE members SET status = 'lapsed'"
                  " WHERE member_id IN (SELECT member_id FROM loans GROUP BY member_id"
                  " HAVING MAX(loaned_on) < '2026-01-01');"),
        probe_sql="SELECT status, COUNT(*) FROM members GROUP BY status ORDER BY status",
        note="ALTER TABLE ADD COLUMN with a DEFAULT gives every existing"
             " row the value at once. The UPDATE then has to find members"
             " with no RECENT loan, and 'latest loan is old' -- a HAVING"
             " on MAX(loaned_on) -- misses the two hundred members with no"
             " loan at all, who have no row to take a MAX of. NOT EXISTS"
             " over recent loans is true for both kinds.",
        claims=[("two hundred and twelve lapsed",
                 lambda rows, c: rows == [('active', 1288), ('lapsed', 212)])],
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
