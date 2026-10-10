"""Practice exercises: fifteen questions on the library schema.

The fifth set on the library (SEED 861), and the second REVISION set: the
same concepts the library sets have taught, paired up differently and
asked afresh. Windows and text -- the top three borrowers of each branch
by DENSE_RANK, titles by their first word with SUBSTR's length argument
right. Intervals and CASE -- holds fulfilled within a week by julianday
arithmetic inside a conditional SUM, loans by renewals with the WHENs in
an order that reaches every class. Recursion and set operations -- the
decades since 1900 with the empty ones kept, books at Central but not Old
Town by EXCEPT the right way round. Subqueries and dates -- members whose
first loan is recent by a HAVING on MIN, quarters by arithmetic on the
month, salary against the role's average by a correlated subquery. EXISTS
and grain -- holds waiting while a copy sits on a shelf, three levels of
author, book and copy counted at the right grain. And three WRITABLE
questions:

  * a BEFORE INSERT trigger that counts a member's open holds
  * an UPDATE with a CASE whose ELSE keeps the rows it does not change
  * CREATE TABLE ... AS SELECT to archive, then a DELETE with the same WHERE

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script -- the holds your trigger should
sort.
"""

import sqlite3

EXERCISES = [
    # ==================================================== 1 Windows and text
    dict(
        id=1, ledger="Q907", concept="W2", tier="1 - Windows and text",
        title="Each branch's three keenest borrowers",
        prompt=(
            "For each home branch, the members with the three highest"
            " loan counts -- ALL of them when members tie, so a branch"
            " may show more than three rows. DENSE_RANK within the"
            " branch, by loans descending.\n\n"
            "Return: home_branch_id, member_id, loans, place"
        ),
        solution=("SELECT home_branch_id, member_id, n, place FROM ("
                  "SELECT m.home_branch_id, m.member_id, COUNT(*) AS n,"
                  " DENSE_RANK() OVER (PARTITION BY m.home_branch_id ORDER BY COUNT(*) DESC) AS place"
                  " FROM loans l JOIN members m ON m.member_id = l.member_id GROUP BY m.member_id)"
                  " WHERE place <= 3"),
        trap_sql=("SELECT home_branch_id, member_id, n, place FROM ("
                  "SELECT m.home_branch_id, m.member_id, COUNT(*) AS n,"
                  " ROW_NUMBER() OVER (PARTITION BY m.home_branch_id ORDER BY COUNT(*) DESC, m.member_id) AS place"
                  " FROM loans l JOIN members m ON m.member_id = l.member_id GROUP BY m.member_id)"
                  " WHERE place <= 3"),
        note="Three ranking functions, three answers to a tie. ROW_NUMBER"
             " picks one of the tied members and drops the other, which"
             " is what 'all of them when members tie' rules out. RANK"
             " keeps both but skips a place afterwards, so a tie for"
             " second leaves no third. DENSE_RANK keeps both AND"
             " continues at third, which is what 'the three highest"
             " counts' means.",
        claims=[("nineteen rows across six branches, one tie",
                 lambda rows, c: len(rows) == 19 and len({r[0] for r in rows}) == 6
                 and all(1 <= r[3] <= 3 for r in rows))],
    ),
    dict(
        id=2, ledger="Q908", concept="STR", tier="1 - Windows and text",
        title="Titles by their first word",
        prompt=(
            "How many titles begin with each first word -- the text"
            " before the first space, without the space. Every title has"
            " at least two words. SUBSTR(text, start, length) with INSTR"
            " finding the space.\n\n"
            "Return: first_word, titles"
        ),
        solution="SELECT SUBSTR(title, 1, INSTR(title, ' ') - 1), COUNT(*) FROM books GROUP BY 1",
        trap_sql="SELECT SUBSTR(title, 1, INSTR(title, ' ')), COUNT(*) FROM books GROUP BY 1",
        note="INSTR gives the position of the space, and a SUBSTR of that"
             " LENGTH from position 1 runs up to and including it, so the"
             " word comes out as 'The ' with a trailing space -- a"
             " different string from 'The', and a different group. The"
             " length wanted is one less than the position. Thirty-five"
             " first words, five of them from the title frames.",
        claims=[("thirty-five first words, 'The' the commonest",
                 lambda rows, c: len(rows) == 35
                 and max(rows, key=lambda r: r[1])[0] == 'The'
                 and all(' ' not in r[0] for r in rows))],
    ),
    # ================================================= 2 Intervals and CASE
    dict(
        id=3, ledger="Q909", concept="INT", tier="2 - Intervals and CASE",
        title="Holds fulfilled within the week",
        prompt=(
            "For each branch the hold was placed at: how many holds were"
            " fulfilled, how many of those within 7 days of being placed,"
            " and how many took longer. The wait is julianday arithmetic"
            " -- placed_at carries a time, which julianday handles -- and"
            " the split is a conditional SUM.\n\n"
            "Return: branch_id, fulfilled, within_week, longer"
        ),
        solution=("SELECT branch_id, COUNT(fulfilled_on),"
                  " SUM(julianday(fulfilled_on) - julianday(placed_at) <= 7),"
                  " SUM(julianday(fulfilled_on) - julianday(placed_at) > 7)"
                  " FROM holds GROUP BY branch_id"),
        trap_sql=("SELECT branch_id, COUNT(fulfilled_on),"
                  " SUM(fulfilled_on - placed_at <= 7),"
                  " SUM(fulfilled_on - placed_at > 7)"
                  " FROM holds GROUP BY branch_id"),
        note="Subtracting two date strings in SQLite converts each to a"
             " number first -- the leading '2026' -- and the difference"
             " is 0, which is 'within a week' for every hold ever"
             " fulfilled. julianday() turns both into days, with the"
             " fraction of a day the time contributes. SUM over a"
             " comparison skips the NULL the open holds produce, so"
             " within_week and longer add up to fulfilled.",
        claims=[("six branches, within and longer adding up to fulfilled",
                 lambda rows, c: len(rows) == 6
                 and all(r[2] + r[3] == r[1] and r[3] > r[2] for r in rows))],
    ),
    dict(
        id=4, ledger="Q910", concept="C7", tier="2 - Intervals and CASE",
        title="Renewed once, twice, or not at all",
        prompt=(
            "Loans by how often they were renewed -- labelled 'none',"
            " 'once', 'twice' from the renewals column -- with the count"
            " and the percentage returned late, to one decimal. A loan"
            " still out is not late.\n\n"
            "Return: renewed, loans, pct_late"
        ),
        solution=("SELECT CASE renewals WHEN 0 THEN 'none' WHEN 1 THEN 'once' ELSE 'twice' END,"
                  " COUNT(*), ROUND(100.0 * SUM(returned_on > due_on) / COUNT(*), 1)"
                  " FROM loans GROUP BY renewals"),
        trap_sql=("SELECT CASE WHEN renewals > 0 THEN 'once' WHEN renewals = 2 THEN 'twice' ELSE 'none' END,"
                  " COUNT(*), ROUND(100.0 * SUM(returned_on > due_on) / COUNT(*), 1)"
                  " FROM loans GROUP BY 1"),
        note="renewals > 0 is already true for 2, so the 'twice' branch"
             " is never reached and the twice-renewed loans are labelled"
             " 'once'. The simple form, CASE renewals WHEN 0 ... , tests"
             " equality against each value in turn and cannot overlap."
             " Renewing cuts the late rate from a quarter to under five"
             " per cent.",
        claims=[("three classes, the late rate falling with renewals",
                 lambda rows, c: len(rows) == 3
                 and dict((r[0], r[2]) for r in rows)['none']
                 > dict((r[0], r[2]) for r in rows)['once']
                 > dict((r[0], r[2]) for r in rows)['twice'])],
    ),
    # ========================================== 3 Recursion and set operations
    dict(
        id=5, ledger="Q911", concept="R1", tier="3 - Recursion and set operations",
        title="Branches opened, decade by decade",
        prompt=(
            "For every decade from 1900 to 2010 -- 1900, 1910, ..., 2010"
            " -- how many branches opened in it, 0 for the decades with"
            " none. Build the decades with a recursive CTE and count the"
            " branches whose opened_on falls in each.\n\n"
            "Return: decade, branches"
        ),
        solution=("WITH RECURSIVE d(decade) AS (SELECT 1900 UNION ALL SELECT decade + 10 FROM d WHERE decade < 2010)"
                  " SELECT d.decade, (SELECT COUNT(*) FROM branches b"
                  " WHERE CAST(strftime('%Y', b.opened_on) AS INTEGER) / 10 * 10 = d.decade) FROM d"),
        trap_sql=("SELECT CAST(strftime('%Y', opened_on) AS INTEGER) / 10 * 10, COUNT(*)"
                  " FROM branches GROUP BY 1"),
        note="Six branches can only make six groups, and the decades"
             " nobody opened anything in have no row to count. The"
             " recursive CTE makes all twelve, and a correlated count or"
             " LEFT JOIN gives the empty ones a 0. Integer division then"
             " multiplication, year / 10 * 10, rounds a year down to its"
             " decade.",
        claims=[("twelve decades, six with a branch",
                 lambda rows, c: len(rows) == 12 and sum(r[1] for r in rows) == 6
                 and sum(r[1] == 0 for r in rows) == 6)],
    ),
    dict(
        id=6, ledger="Q912", concept="S1", tier="3 - Recursion and set operations",
        title="At Central but not at Old Town",
        prompt=(
            "Books with a copy at Central (branch 1) but no copy at Old"
            " Town (branch 6), using EXCEPT between two queries over"
            " copies. Each book once.\n\n"
            "Return: book_id"
        ),
        solution=("SELECT book_id FROM copies WHERE branch_id = 1"
                  " EXCEPT SELECT book_id FROM copies WHERE branch_id = 6"),
        trap_sql=("SELECT book_id FROM copies WHERE branch_id = 6"
                  " EXCEPT SELECT book_id FROM copies WHERE branch_id = 1"),
        note="EXCEPT is not symmetric: A EXCEPT B is what A has that B"
             " does not, so the branch that must HAVE the book goes"
             " first. Reversed, it lists what Old Town has that Central"
             " lacks, a different set of a different size. EXCEPT also"
             " removes duplicates, so a book with three copies at Central"
             " is one row.",
        claims=[("a hundred and fifty or so books",
                 lambda rows, c: 140 < len(rows) < 160
                 and len({r[0] for r in rows}) == len(rows))],
    ),
    # ================================================ 4 Subqueries and dates
    dict(
        id=7, ledger="Q913", concept="X1", tier="4 - Subqueries and dates",
        title="Late starters",
        prompt=(
            "Members whose FIRST loan was on or after 2025-06-01: their"
            " member_id and the date of that first loan. A member with"
            " loans before that date is excluded even if they also"
            " borrowed after it.\n\n"
            "Return: member_id, first_loan"
        ),
        solution=("SELECT member_id, MIN(loaned_on) FROM loans GROUP BY member_id"
                  " HAVING MIN(loaned_on) >= '2025-06-01'"),
        trap_sql=("SELECT member_id, MIN(loaned_on) FROM loans WHERE loaned_on >= '2025-06-01'"
                  " GROUP BY member_id"),
        note="A WHERE on the date throws away the early loans BEFORE the"
             " MIN is taken, so every member's 'first loan' becomes their"
             " first loan since June, and almost everyone qualifies. The"
             " condition is about the member's minimum, which only exists"
             " after grouping -- HAVING, or a derived table filtered"
             " afterwards.",
        claims=[("a few dozen members, every first loan in or after June 2025",
                 lambda rows, c: 10 < len(rows) < 300
                 and all(r[1] >= '2025-06-01' for r in rows))],
    ),
    dict(
        id=8, ledger="Q914", concept="D1", tier="4 - Subqueries and dates",
        title="Loans by quarter",
        prompt=(
            "How many loans started in each quarter of each year: the"
            " year as a number, the quarter as 1 to 4. There is no"
            " strftime code for the quarter; derive it from the month"
            " number with integer arithmetic.\n\n"
            "Return: year, quarter, loans"
        ),
        solution=("SELECT CAST(strftime('%Y', loaned_on) AS INTEGER),"
                  " (CAST(strftime('%m', loaned_on) AS INTEGER) + 2) / 3, COUNT(*)"
                  " FROM loans GROUP BY 1, 2"),
        trap_sql=("SELECT CAST(strftime('%Y', loaned_on) AS INTEGER),"
                  " CAST(strftime('%m', loaned_on) AS INTEGER) / 3, COUNT(*)"
                  " FROM loans GROUP BY 1, 2"),
        note="month / 3 puts January and February in quarter 0 and March"
             " in quarter 1 -- the boundaries are off by two months."
             " (month + 2) / 3 maps 1-3 to 1, 4-6 to 2, and so on, because"
             " integer division rounds down. Six quarters of around four"
             " thousand loans.",
        claims=[("six quarters of four thousand or so",
                 lambda rows, c: len(rows) == 6 and all(3800 < r[2] < 4300 for r in rows)
                 and {r[1] for r in rows} == {1, 2, 3, 4})],
    ),
    dict(
        id=9, ledger="Q915", concept="X1", tier="4 - Subqueries and dates",
        title="Paid against the role's average",
        prompt=(
            "Each staff member's salary, the average salary of their"
            " ROLE rounded to whole pounds, and how far above or below it"
            " they are. The role average is a correlated subquery that"
            " refers to the outer row's role.\n\n"
            "Return: staff_id, salary, role_avg, diff"
        ),
        solution=("SELECT s.staff_id, s.salary,"
                  " ROUND((SELECT AVG(salary) FROM staff r WHERE r.role = s.role)),"
                  " s.salary - ROUND((SELECT AVG(salary) FROM staff r WHERE r.role = s.role))"
                  " FROM staff s"),
        trap_sql=("SELECT s.staff_id, s.salary,"
                  " ROUND((SELECT AVG(salary) FROM staff)),"
                  " s.salary - ROUND((SELECT AVG(salary) FROM staff))"
                  " FROM staff s"),
        note="A subquery with no reference to the outer row is the same"
             " value for everyone -- the average of all staff, which"
             " makes every assistant look underpaid and every manager"
             " overpaid. r.role = s.role is what makes it correlated:"
             " evaluated per outer row, against that row's role. A"
             " window AVG(salary) OVER (PARTITION BY role) says the same.",
        claims=[("thirty-one staff, three distinct role averages",
                 lambda rows, c: len(rows) == 31 and len({r[2] for r in rows}) == 3
                 and all(r[3] == r[1] - r[2] for r in rows))],
    ),
    # ===================================================== 5 EXISTS and grain
    dict(
        id=10, ledger="Q916", concept="E1", tier="5 - EXISTS and grain",
        title="Waiting while a copy sits on a shelf",
        prompt=(
            "Open holds -- fulfilled_on and cancelled_on both NULL --"
            " whose book has a copy available RIGHT NOW somewhere in the"
            " service: a copy not withdrawn and with no open loan."
            " Return the hold and its book.\n\n"
            "Return: hold_id, book_id"
        ),
        solution=("SELECT h.hold_id, h.book_id FROM holds h"
                  " WHERE h.fulfilled_on IS NULL AND h.cancelled_on IS NULL"
                  " AND EXISTS (SELECT 1 FROM copies c WHERE c.book_id = h.book_id"
                  " AND c.withdrawn_on IS NULL"
                  " AND NOT EXISTS (SELECT 1 FROM loans l WHERE l.copy_id = c.copy_id AND l.returned_on IS NULL))"),
        trap_sql=("SELECT h.hold_id, h.book_id FROM holds h"
                  " WHERE h.fulfilled_on IS NULL AND h.cancelled_on IS NULL"
                  " AND EXISTS (SELECT 1 FROM copies c WHERE c.book_id = h.book_id"
                  " AND NOT EXISTS (SELECT 1 FROM loans l WHERE l.copy_id = c.copy_id AND l.returned_on IS NULL))"),
        note="'Available' is the two-part rule from the first library set"
             " -- not withdrawn, not out -- and a withdrawn copy has no"
             " open loan precisely because it cannot be lent, so without"
             " the withdrawn test every withdrawn copy counts as being on"
             " the shelf. EXISTS inside EXISTS reads as English: there is"
             " a copy of this book for which there is no open loan.",
        claims=[("three hundred or so of the waiting holds",
                 lambda rows, c: 290 < len(rows) < 337)],
    ),
    dict(
        id=11, ledger="Q917", concept="C2", tier="5 - EXISTS and grain",
        title="Books and copies, per author",
        prompt=(
            "For each author who has at least one book: how many books,"
            " and how many copies of them in all. Books with no copies"
            " still count as books. Author, book and copy are three"
            " grains, and the join to copies multiplies the book rows.\n\n"
            "Return: author_id, books, copies"
        ),
        solution=("SELECT a.author_id, COUNT(DISTINCT b.book_id), COUNT(c.copy_id)"
                  " FROM authors a JOIN books b ON b.author_id = a.author_id"
                  " LEFT JOIN copies c ON c.book_id = b.book_id GROUP BY a.author_id"),
        trap_sql=("SELECT a.author_id, COUNT(b.book_id), COUNT(c.copy_id)"
                  " FROM authors a JOIN books b ON b.author_id = a.author_id"
                  " LEFT JOIN copies c ON c.book_id = b.book_id GROUP BY a.author_id"),
        note="After the join to copies there is one row per COPY, and"
             " COUNT(b.book_id) counts the book once per copy -- the book"
             " count comes out equal to the copy count. COUNT(DISTINCT"
             " b.book_id) counts each book once however many copies it"
             " has, and the LEFT JOIN keeps a book with none as one row"
             " whose NULL copy_id COUNT ignores.",
        claims=[("a hundred and nine authors, more copies than books",
                 lambda rows, c: len(rows) == 109
                 and all(r[2] >= r[1] for r in rows)
                 and sum(r[1] for r in rows) == 600)],
    ),
    # ================================================= 6 Changing the data
    dict(
        id=12, ledger="Q918", concept="TRG", tier="6 - Changing the data",
        kind="script",
        title="Three open holds at most",
        prompt=(
            "Write a BEFORE INSERT trigger on holds that refuses a new"
            " hold -- RAISE(ABORT, ...) -- when the member already has"
            " three or more OPEN holds, fulfilled_on and cancelled_on"
            " both NULL. The question then inserts a hold for member 930,"
            " who has three waiting, and one for member 1, who has"
            " none.\n\n"
            "Checked: which of the two holds exist"
        ),
        solution=("CREATE TRIGGER hold_limit BEFORE INSERT ON holds\n"
                  "WHEN (SELECT COUNT(*) FROM holds h WHERE h.member_id = NEW.member_id\n"
                  "      AND h.fulfilled_on IS NULL AND h.cancelled_on IS NULL) >= 3\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'member already has three open holds');\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER hold_limit BEFORE INSERT ON holds\n"
                  "WHEN (SELECT COUNT(*) FROM holds h WHERE h.member_id = NEW.member_id) >= 3\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'member already has three open holds');\n"
                  "END;"),
        driver_sql=("INSERT INTO holds (book_id, member_id, placed_at, branch_id)"
                    " VALUES (12, 930, '2026-07-01 09:00', 1);\n"
                    "INSERT INTO holds (book_id, member_id, placed_at, branch_id)"
                    " VALUES (12, 982, '2026-07-01 09:05', 1);"),
        probe_sql="SELECT member_id FROM holds WHERE hold_id > 1500 ORDER BY hold_id",
        note="The count in the WHEN has to be of OPEN holds; counting"
             " every hold the member ever placed refuses members whose"
             " holds were all fulfilled or cancelled long ago -- which is"
             " member 982, with several holds in the history and none"
             " open. The two members are the two halves of the rule.",
        claims=[("930 refused, 982 accepted",
                 lambda rows, c: rows == [(982,)])],
    ),
    dict(
        id=13, ledger="Q919", concept="DML", tier="6 - Changing the data",
        kind="script",
        title="A pay rise by role",
        prompt=(
            "Give every assistant a 5 per cent rise and every librarian 3"
            " per cent, rounded to whole pounds with ROUND; managers'"
            " salaries do not change. One UPDATE with a CASE in its SET.\n\n"
            "Checked: the total salary of each role"
        ),
        solution=("UPDATE staff SET salary = CASE role"
                  " WHEN 'assistant' THEN ROUND(salary * 1.05)"
                  " WHEN 'librarian' THEN ROUND(salary * 1.03)"
                  " ELSE salary END;"),
        trap_sql=("UPDATE staff SET salary = CASE role"
                  " WHEN 'assistant' THEN ROUND(salary * 1.05)"
                  " WHEN 'librarian' THEN ROUND(salary * 1.03) END;"),
        probe_sql="SELECT role, SUM(salary) FROM staff GROUP BY role ORDER BY role",
        note="A CASE with no ELSE is NULL for the rows no WHEN matches,"
             " and an UPDATE writes that NULL -- here into a NOT NULL"
             " column, so SQLite refuses the whole statement and nobody"
             " gets a rise. ELSE salary keeps the managers as they were."
             " The alternative is a WHERE role <> 'manager', which"
             " updates fewer rows and needs no ELSE.",
        claims=[("assistants and librarians up, managers unchanged",
                 lambda rows, c: dict(rows)['manager'] == 205813
                 and dict(rows)['assistant'] == 301931 and dict(rows)['librarian'] == 398503)],
    ),
    dict(
        id=14, ledger="Q920", concept="DDL", tier="6 - Changing the data",
        kind="script",
        title="Archive the closed holds",
        prompt=(
            "Move the CLOSED holds -- fulfilled or cancelled -- out of"
            " holds into a new table `holds_archive` with the same"
            " columns: CREATE TABLE ... AS SELECT to copy them, then"
            " DELETE them from holds with the same condition. Open holds"
            " stay where they are.\n\n"
            "Checked: how many rows holds and holds_archive each have,"
            " and how many open holds are left in holds"
        ),
        solution=("CREATE TABLE holds_archive AS SELECT * FROM holds"
                  " WHERE fulfilled_on IS NOT NULL OR cancelled_on IS NOT NULL;\n"
                  "DELETE FROM holds WHERE fulfilled_on IS NOT NULL OR cancelled_on IS NOT NULL;"),
        trap_sql=("CREATE TABLE holds_archive AS SELECT * FROM holds"
                  " WHERE fulfilled_on IS NOT NULL OR cancelled_on IS NOT NULL;\n"
                  "DELETE FROM holds;"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM holds), (SELECT COUNT(*) FROM holds_archive),"
                   " (SELECT COUNT(*) FROM holds WHERE fulfilled_on IS NULL AND cancelled_on IS NULL)"),
        note="CREATE TABLE AS SELECT makes the table from the query's"
             " columns and fills it in one statement -- no CREATE, no"
             " column list, no INSERT. The DELETE that follows must use"
             " the SAME condition, or the open holds go too and the"
             " archive is of closed holds while the waiting members have"
             " simply vanished. Note that 'archive' tables made this way"
             " have no PRIMARY KEY or constraints of their own.",
        claims=[("337 open holds kept, 1163 archived",
                 lambda rows, c: rows == [(337, 1163, 337)])],
    ),
    dict(
        id=15, ledger="Q921", concept="VIEW", tier="6 - Changing the data",
        kind="script",
        title="The queue, as a view",
        prompt=(
            "Create a view `hold_queue (hold_id, book_id, member_id,"
            " position)` of the OPEN holds, numbered within each book by"
            " placed_at from 1 -- the queue position. Closed holds are"
            " not in the view and do not take a number.\n\n"
            "Checked: the view's size, how many holds are at position 1 --"
            " one per book with a queue -- and the longest queue"
        ),
        solution=("CREATE VIEW hold_queue AS\n"
                  "  SELECT hold_id, book_id, member_id,\n"
                  "         ROW_NUMBER() OVER (PARTITION BY book_id ORDER BY placed_at) AS position\n"
                  "  FROM holds WHERE fulfilled_on IS NULL AND cancelled_on IS NULL;"),
        trap_sql=("CREATE VIEW hold_queue AS\n"
                  "  SELECT hold_id, book_id, member_id,\n"
                  "         ROW_NUMBER() OVER (PARTITION BY book_id ORDER BY placed_at) AS position\n"
                  "  FROM holds;"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM hold_queue),"
                   " (SELECT COUNT(*) FROM hold_queue WHERE position = 1),"
                   " (SELECT MAX(position) FROM hold_queue)"),
        note="The WHERE runs before the window function, so filtering to"
             " open holds is what makes the numbering a QUEUE: without it"
             " the fulfilled holds of the past take positions 1, 2, 3 and"
             " the member actually next in line is numbered tenth. A view"
             " can hold a window function, and the probe queries it like"
             " a table.",
        claims=[("337 in the queue, 140 books with someone at the front, seven deep at most",
                 lambda rows, c: rows == [(337, 140, 7)])],
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
