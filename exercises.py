"""Practice exercises: fifteen questions on the library schema.

The third set on the library (SEED 861), and the second with the TOPICS
mixed up: six tiers that neither library set before it used. Subqueries
-- a scalar one in SELECT for a share of the whole, a derived table in FROM
to compare each borrower with the average borrower. String aggregation and
DISTINCT -- GROUP_CONCAT with its own ORDER BY, and COUNT(DISTINCT) beside
COUNT. Outer joins and NULL tests -- a condition that belongs in ON, an
anti-join by LEFT JOIN ... IS NULL, and IS NOT where <> loses the NULLs.
Window frames -- a running total, LAG for month-on-month change, and a
three-month moving average by ROWS BETWEEN. Ordering and limits -- a page
by OFFSET with a tie-break, a top ten in the right direction. And three
WRITABLE questions on constraints:

  * a CREATE TABLE whose CHECKs are exercised by the question's own inserts
  * a partial UNIQUE index, where the unconditional one cannot even be built
  * INSERT ... ON CONFLICT DO UPDATE, where OR REPLACE breaks a foreign key

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script -- the rows your constraint should
accept or refuse.
"""

import sqlite3

EXERCISES = [
    # ========================================================= 1 Subqueries
    dict(
        id=1, ledger="Q877", concept="X1", tier="1 - Subqueries",
        title="Each branch's share of the stock",
        prompt=(
            "For each branch: how many copies it holds, and what"
            " percentage of ALL copies that is, to one decimal. The total"
            " is a scalar subquery -- (SELECT COUNT(*) FROM copies) --"
            " used inside the outer query's arithmetic.\n\n"
            "Return: branch_id, copies, pct"
        ),
        solution=("SELECT branch_id, COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM copies), 1)"
                  " FROM copies GROUP BY branch_id"),
        trap_sql=("SELECT branch_id, COUNT(*),"
                  " 100 * COUNT(*) / (SELECT COUNT(*) FROM copies)"
                  " FROM copies GROUP BY branch_id"),
        note="A scalar subquery returns one value and can sit anywhere a"
             " value can -- here as the denominator, evaluated once. The"
             " arithmetic around it is integer unless something makes it"
             " not: 100 * 381 / 2226 is 17, and the .1 is gone before"
             " ROUND could see it. 100.0 makes the whole expression a"
             " float.",
        claims=[("six branches, shares adding up to a hundred",
                 lambda rows, c: len(rows) == 6
                 and 99.5 < sum(r[2] for r in rows) < 100.5
                 and all(15 < r[2] < 19 for r in rows))],
    ),
    dict(
        id=2, ledger="Q878", concept="X1", tier="1 - Subqueries",
        title="Above the average borrower",
        prompt=(
            "Members who have borrowed more often than the AVERAGE"
            " BORROWER -- the average of loans per member over the"
            " members who have at least one loan, not over all 1,500"
            " members. Build the per-member counts once as a derived"
            " table in FROM, and take the average of that.\n\n"
            "Return: member_id, loans"
        ),
        solution=("SELECT member_id, n FROM (SELECT member_id, COUNT(*) AS n FROM loans GROUP BY member_id) t"
                  " WHERE n > (SELECT AVG(n) FROM (SELECT COUNT(*) AS n FROM loans GROUP BY member_id))"),
        trap_sql=("SELECT member_id, COUNT(*) FROM loans GROUP BY member_id"
                  " HAVING COUNT(*) > (SELECT 1.0 * COUNT(*) / (SELECT COUNT(*) FROM members) FROM loans)"),
        note="The average borrower has about eighteen loans; the average"
             " MEMBER has about sixteen, because two hundred members have"
             " none and pull the figure down. Dividing total loans by"
             " total members is the second average. The first needs the"
             " per-member counts to exist as rows before they can be"
             " averaged -- which is what a derived table in FROM is for.",
        claims=[("a hundred and seventy borrowers, none with fewer than nineteen loans",
                 lambda rows, c: 150 < len(rows) < 200 and min(r[1] for r in rows) >= 19)],
    ),
    # ======================================= 2 String aggregation and DISTINCT
    dict(
        id=3, ledger="Q879", concept="STR", tier="2 - String aggregation and DISTINCT",
        title="An author's titles on one line",
        prompt=(
            "For each author with three or more books in the catalogue:"
            " author_id and their titles joined into ONE string with '; '"
            " between them, in alphabetical order of title. GROUP_CONCAT"
            " takes an ORDER BY inside its parentheses.\n\n"
            "Return: author_id, titles"
        ),
        solution=("SELECT author_id, GROUP_CONCAT(title, '; ' ORDER BY title) FROM books"
                  " GROUP BY author_id HAVING COUNT(*) >= 3"),
        trap_sql=("SELECT author_id, GROUP_CONCAT(title, '; ') FROM books"
                  " GROUP BY author_id HAVING COUNT(*) >= 3"),
        note="GROUP_CONCAT joins a group's values into one string, in"
             " whatever order the rows arrived -- which here is book_id"
             " order, not alphabetical. An ORDER BY in the outer query"
             " sorts the ROWS, not the pieces inside each string; the"
             " ORDER BY that controls the pieces goes inside the"
             " function, GROUP_CONCAT(title, '; ' ORDER BY title).",
        claims=[("a hundred authors, every list alphabetical",
                 lambda rows, c: len(rows) == 100
                 and all(r[1].split('; ') == sorted(r[1].split('; ')) for r in rows))],
    ),
    dict(
        id=4, ledger="Q880", concept="A2", tier="2 - String aggregation and DISTINCT",
        title="Loans and readers, per genre",
        prompt=(
            "For each genre: how many loans its books have had, and how"
            " many DIFFERENT members made them. A member who borrowed ten"
            " children's books is ten loans and one reader.\n\n"
            "Return: genre, loans, readers"
        ),
        solution=("SELECT b.genre, COUNT(*), COUNT(DISTINCT l.member_id) FROM loans l"
                  " JOIN copies c ON c.copy_id = l.copy_id JOIN books b ON b.book_id = c.book_id"
                  " GROUP BY b.genre"),
        trap_sql=("SELECT b.genre, COUNT(*), COUNT(l.member_id) FROM loans l"
                  " JOIN copies c ON c.copy_id = l.copy_id JOIN books b ON b.book_id = c.book_id"
                  " GROUP BY b.genre"),
        note="COUNT(member_id) counts rows with a member -- every loan"
             " has one, so it is COUNT(*) under another name. COUNT("
             "DISTINCT member_id) counts the different members. The loan"
             " reaches its genre through two joins: copy to book.",
        claims=[("eight genres, readers well below loans",
                 lambda rows, c: len(rows) == 8
                 and all(r[2] < r[1] and r[2] <= 1300 for r in rows))],
    ),
    # ============================================ 3 Outer joins and NULL tests
    dict(
        id=5, ledger="Q881", concept="J2", tier="3 - Outer joins and NULL tests",
        title="Every member of Old Town, borrowing or not",
        prompt=(
            "For EVERY member whose home branch is 6: member_id and how"
            " many loans they have taken out since 2026-01-01 -- 0 for the"
            " members with none, who must still appear. The date test"
            " belongs in the join's ON clause, not in WHERE.\n\n"
            "Return: member_id, loans_2026"
        ),
        solution=("SELECT m.member_id, COUNT(l.loan_id) FROM members m"
                  " LEFT JOIN loans l ON l.member_id = m.member_id AND l.loaned_on >= '2026-01-01'"
                  " WHERE m.home_branch_id = 6 GROUP BY m.member_id"),
        trap_sql=("SELECT m.member_id, COUNT(l.loan_id) FROM members m"
                  " LEFT JOIN loans l ON l.member_id = m.member_id"
                  " WHERE m.home_branch_id = 6 AND l.loaned_on >= '2026-01-01' GROUP BY m.member_id"),
        note="A LEFT JOIN keeps every member; a WHERE on the loan side"
             " then throws away the rows whose loan is NULL, because NULL"
             " >= '2026-01-01' is not true -- and the members with no"
             " recent loan vanish with them. A condition on the OUTER"
             " side of an outer join goes in ON, where it decides which"
             " loans match, not which members survive.",
        claims=[("two hundred and sixty-six members, twenty-seven with none",
                 lambda rows, c: len(rows) == 266 and sum(r[1] == 0 for r in rows) == 27)],
    ),
    dict(
        id=6, ledger="Q882", concept="J2", tier="3 - Outer joins and NULL tests",
        title="Authors with nothing in the catalogue",
        prompt=(
            "Authors who have no books at all, found with a LEFT JOIN and"
            " a test for NULL on the books side -- an anti-join -- rather"
            " than NOT IN or NOT EXISTS.\n\n"
            "Return: author_id, name"
        ),
        solution=("SELECT a.author_id, a.name FROM authors a"
                  " LEFT JOIN books b ON b.author_id = a.author_id WHERE b.book_id IS NULL"),
        trap_sql=("SELECT a.author_id, a.name FROM books b"
                  " LEFT JOIN authors a ON a.author_id = b.author_id WHERE b.book_id IS NULL"),
        note="The table whose rows must all survive goes on the LEFT. From"
             " books LEFT JOIN authors, every row is a book, and no book"
             " has a NULL book_id, so nothing is found. From authors LEFT"
             " JOIN books, an author with no books gets one row with the"
             " book columns NULL, and that is the row the WHERE keeps.",
        claims=[("eleven unpublished authors",
                 lambda rows, c: len(rows) == 11)],
    ),
    dict(
        id=7, ledger="Q883", concept="N1", tier="3 - Outer joins and NULL tests",
        title="Everyone outside LS1",
        prompt=(
            "For each home branch, how many of its members do NOT live in"
            " postcode area 'LS1' -- counting the members with no recorded"
            " area among them, since they are not in LS1 either.\n\n"
            "Return: home_branch_id, members"
        ),
        solution=("SELECT home_branch_id, COUNT(*) FROM members"
                  " WHERE postcode_area IS NOT 'LS1' GROUP BY home_branch_id"),
        trap_sql=("SELECT home_branch_id, COUNT(*) FROM members"
                  " WHERE postcode_area <> 'LS1' GROUP BY home_branch_id"),
        note="NULL <> 'LS1' is NULL, not true, so WHERE drops the hundred"
             " or so members with no recorded area -- the opposite of"
             " what the question asked. IS NOT is the NULL-safe"
             " comparison: NULL IS NOT 'LS1' is true. COALESCE("
             "postcode_area, '') <> 'LS1' says the same thing the long"
             " way.",
        claims=[("six branches, over two hundred each",
                 lambda rows, c: len(rows) == 6 and all(r[1] > 200 for r in rows)
                 and sum(r[1] for r in rows) ==
                 c.execute("SELECT COUNT(*) FROM members WHERE postcode_area IS NULL"
                           " OR postcode_area <> 'LS1'").fetchone()[0])],
    ),
    # ====================================================== 4 Window frames
    dict(
        id=8, ledger="Q884", concept="W1", tier="4 - Window frames",
        title="Fines issued in 2026, running total",
        prompt=(
            "For each month of 2026 in the data: the pence of fines issued"
            " that month, and the running total from January up to and"
            " including that month. A window SUM over the monthly SUM,"
            " ordered by month.\n\n"
            "Return: month, pence, cumulative"
        ),
        solution=("SELECT strftime('%Y-%m', issued_on) AS month, SUM(amount_pence),"
                  " SUM(SUM(amount_pence)) OVER (ORDER BY strftime('%Y-%m', issued_on))"
                  " FROM fines WHERE issued_on >= '2026-01-01' GROUP BY month"),
        trap_sql=("SELECT strftime('%Y-%m', issued_on) AS month, SUM(amount_pence),"
                  " SUM(SUM(amount_pence)) OVER ()"
                  " FROM fines WHERE issued_on >= '2026-01-01' GROUP BY month"),
        note="SUM(SUM(x)) OVER (...) reads oddly and is exactly right: the"
             " inner SUM is the group's total, the outer one is a window"
             " over those totals. The ORDER BY in the window is what"
             " makes it a RUNNING total -- without it the frame is every"
             " row, and each month shows the grand total for the year.",
        claims=[("six months, the last cumulative equal to the year's total",
                 lambda rows, c: len(rows) == 6
                 and max(rows)[2] == sum(r[1] for r in rows)
                 and min(rows)[2] == min(rows)[1])],
    ),
    dict(
        id=9, ledger="Q885", concept="W1", tier="4 - Window frames",
        title="Loans month on month",
        prompt=(
            "For each month of the data: how many loans started, and the"
            " change from the previous month -- this month minus last,"
            " NULL for the first month. LAG looks back one row.\n\n"
            "Return: month, loans, change"
        ),
        solution=("SELECT strftime('%Y-%m', loaned_on) AS month, COUNT(*),"
                  " COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY strftime('%Y-%m', loaned_on))"
                  " FROM loans GROUP BY month"),
        trap_sql=("SELECT strftime('%Y-%m', loaned_on) AS month, COUNT(*),"
                  " COUNT(*) - LEAD(COUNT(*)) OVER (ORDER BY strftime('%Y-%m', loaned_on))"
                  " FROM loans GROUP BY month"),
        note="LAG reaches the previous row in the window's order, LEAD the"
             " next; with LEAD the 'change' is next month's drop with the"
             " sign flipped, and the NULL lands on the LAST month instead"
             " of the first. The window function is applied to the"
             " aggregate, COUNT(*), after the GROUP BY has done its work.",
        claims=[("eighteen months, the first with no change",
                 lambda rows, c: len(rows) == 18
                 and min(rows)[2] is None and max(rows)[2] is not None
                 and sum(r[1] for r in rows) == 23976)],
    ),
    dict(
        id=10, ledger="Q886", concept="W1", tier="4 - Window frames",
        title="A three-month moving average",
        prompt=(
            "For each month of the data: the average number of loans"
            " started over that month and the two before it, to one"
            " decimal -- so the first month averages itself alone and the"
            " second averages two. The frame is ROWS BETWEEN 2 PRECEDING"
            " AND CURRENT ROW.\n\n"
            "Return: month, moving_avg"
        ),
        solution=("SELECT strftime('%Y-%m', loaned_on) AS month,"
                  " ROUND(AVG(COUNT(*)) OVER (ORDER BY strftime('%Y-%m', loaned_on)"
                  " ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1)"
                  " FROM loans GROUP BY month"),
        trap_sql=("SELECT strftime('%Y-%m', loaned_on) AS month,"
                  " ROUND(AVG(COUNT(*)) OVER (ORDER BY strftime('%Y-%m', loaned_on)), 1)"
                  " FROM loans GROUP BY month"),
        note="An ORDER BY in a window with no frame clause means 'from the"
             " start up to this row' -- a RUNNING average, which by June"
             " 2026 is averaging eighteen months. ROWS BETWEEN 2 PRECEDING"
             " AND CURRENT ROW fixes the frame at three rows, and the"
             " frame simply has fewer rows at the start.",
        claims=[("eighteen months, the first equal to its own count",
                 lambda rows, c: len(rows) == 18 and min(rows)[1] == 1169.0
                 and all(1150 < r[1] < 1450 for r in rows))],
    ),
    # ================================================ 5 Ordering and limits
    dict(
        id=11, ledger="Q887", concept="O1", tier="5 - Ordering and limits",
        title="The third page of members",
        prompt=(
            "The member list is shown twenty to a page, sorted by name"
            " and, where two members share a name, by member_id. Return"
            " the THIRD page -- rows 41 to 60 of that ordering.\n\n"
            "Return: member_id, name"
        ),
        solution="SELECT member_id, name FROM members ORDER BY name, member_id LIMIT 20 OFFSET 40",
        trap_sql="SELECT member_id, name FROM members ORDER BY name, member_id LIMIT 20 OFFSET 60",
        note="OFFSET counts the rows to SKIP, so page three skips two"
             " pages, forty rows -- not sixty, which is page four. The"
             " tie-break on member_id matters here more than usual: four"
             " hundred names are shared, and without it the page boundary"
             " could fall differently each run.",
        claims=[("twenty rows, still among the A names",
                 lambda rows, c: len(rows) == 20
                 and sorted(rows, key=lambda r: (r[1], r[0])) ==
                 [tuple(r) for r in c.execute("SELECT member_id, name FROM members"
                                              " ORDER BY name, member_id LIMIT 20 OFFSET 40")]
                 and all(r[1][0] in 'AB' for r in rows))],
    ),
    dict(
        id=12, ledger="Q888", concept="O1", tier="5 - Ordering and limits",
        title="The ten most overdue loans",
        prompt=(
            "As of 2026-06-30, the ten loans that are still out and"
            " furthest past their due date: the earliest due_on first,"
            " ties broken by the lower loan_id. Only loans with"
            " returned_on NULL and due_on before that day count.\n\n"
            "Return: loan_id, due_on"
        ),
        solution=("SELECT loan_id, due_on FROM loans WHERE returned_on IS NULL"
                  " AND due_on < '2026-06-30' ORDER BY due_on, loan_id LIMIT 10"),
        trap_sql=("SELECT loan_id, due_on FROM loans WHERE returned_on IS NULL"
                  " AND due_on < '2026-06-30' ORDER BY due_on DESC, loan_id LIMIT 10"),
        note="Most overdue means the OLDEST due date, so the sort is"
             " ascending; DESC gives the ten loans that only just fell"
             " due. The tie-break is not decoration: the tenth and"
             " eleventh loans share a due date, and without loan_id in"
             " the ORDER BY either could be the one returned.",
        claims=[("ten loans, the oldest due in April",
                 lambda rows, c: len(rows) == 10 and min(r[1] for r in rows) == '2026-04-23'
                 and max(r[1] for r in rows) == '2026-05-29')],
    ),
    # ======================================================= 6 Constraints
    dict(
        id=13, ledger="Q889", concept="DDL", tier="6 - Constraints",
        kind="script",
        title="A room-booking table that checks itself",
        prompt=(
            "Create a table `room_bookings (booking_id INTEGER PRIMARY"
            " KEY, member_id INTEGER NOT NULL REFERENCES members("
            "member_id), room TEXT NOT NULL, starts_at TEXT NOT NULL,"
            " ends_at TEXT NOT NULL)` with two CHECKs: room is 'study' or"
            " 'meeting', and ends_at is after starts_at. The question then"
            " tries three bookings: a good one, one in room 'garden', and"
            " one that ends before it starts.\n\n"
            "Checked: how many bookings exist"
        ),
        solution=("CREATE TABLE room_bookings (\n"
                  "  booking_id INTEGER PRIMARY KEY,\n"
                  "  member_id INTEGER NOT NULL REFERENCES members(member_id),\n"
                  "  room TEXT NOT NULL CHECK (room IN ('study', 'meeting')),\n"
                  "  starts_at TEXT NOT NULL,\n"
                  "  ends_at TEXT NOT NULL,\n"
                  "  CHECK (ends_at > starts_at)\n"
                  ");"),
        trap_sql=("CREATE TABLE room_bookings (\n"
                  "  booking_id INTEGER PRIMARY KEY,\n"
                  "  member_id INTEGER NOT NULL REFERENCES members(member_id),\n"
                  "  room TEXT NOT NULL CHECK (room IN ('study', 'meeting')),\n"
                  "  starts_at TEXT NOT NULL,\n"
                  "  ends_at TEXT NOT NULL\n"
                  ");"),
        driver_sql=("INSERT INTO room_bookings (member_id, room, starts_at, ends_at)"
                    " VALUES (3, 'study', '2026-07-01 10:00', '2026-07-01 11:00');\n"
                    "INSERT INTO room_bookings (member_id, room, starts_at, ends_at)"
                    " VALUES (3, 'garden', '2026-07-01 10:00', '2026-07-01 11:00');\n"
                    "INSERT INTO room_bookings (member_id, room, starts_at, ends_at)"
                    " VALUES (4, 'meeting', '2026-07-01 14:00', '2026-07-01 13:00');"),
        probe_sql="SELECT COUNT(*) FROM room_bookings",
        note="A CHECK on one column sits beside that column; a CHECK that"
             " compares two columns is a TABLE constraint, written after"
             " the columns. Both are tested on every INSERT and UPDATE,"
             " and a booking that ends before it starts is refused by the"
             " table itself, with no application code to forget it. The"
             " dates compare correctly as text because of their format.",
        claims=[("one booking of the three",
                 lambda rows, c: rows == [(1,)])],
    ),
    dict(
        id=14, ledger="Q890", concept="DDL", tier="6 - Constraints",
        kind="script",
        title="One open hold per member per book",
        prompt=(
            "Create a UNIQUE index that stops a member holding more than"
            " ONE open hold -- fulfilled_on and cancelled_on both NULL --"
            " on the same book, while leaving their closed holds alone: a"
            " PARTIAL index, with a WHERE. The question then inserts a"
            " second open hold for member 844 on book 275, who already"
            " has one waiting, and an open hold for member 842 on book"
            " 349, whose earlier hold was fulfilled.\n\n"
            "Checked: how many holds exist, and how many open holds"
            " member 842 has on book 349"
        ),
        solution=("CREATE UNIQUE INDEX one_open_hold ON holds (member_id, book_id)\n"
                  "  WHERE fulfilled_on IS NULL AND cancelled_on IS NULL;"),
        trap_sql="CREATE UNIQUE INDEX one_open_hold ON holds (member_id, book_id);",
        driver_sql=("INSERT INTO holds (book_id, member_id, placed_at, branch_id)"
                    " VALUES (275, 844, '2026-07-01 09:00', 4);\n"
                    "INSERT INTO holds (book_id, member_id, placed_at, branch_id)"
                    " VALUES (349, 842, '2026-07-01 09:05', 3);"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM holds),"
                   " (SELECT COUNT(*) FROM holds WHERE member_id = 842 AND book_id = 349"
                   " AND fulfilled_on IS NULL AND cancelled_on IS NULL)"),
        note="A partial index covers only the rows its WHERE selects, so"
             " UNIQUE applies among the open holds and a member can hold"
             " a book again once the last hold closed. The unconditional"
             " index cannot even be created: eight members already have"
             " two holds on one book in the history, so CREATE fails and"
             " nothing is protected.",
        claims=[("one of the two inserts accepted, 842 waiting once",
                 lambda rows, c: rows == [(1501, 1)])],
    ),
    dict(
        id=15, ledger="Q891", concept="DML", tier="6 - Constraints",
        kind="script",
        title="Add or update a branch in one statement",
        prompt=(
            "Record two branches so that the script works whether or not"
            " the name exists: 'Old Town' in 'Castleford', and 'Westgate'"
            " in 'Leeds', both opened_on '2026-09-01'. Where a branch of"
            " that name already exists, UPDATE its town and leave its"
            " branch_id alone; otherwise insert it. Use INSERT ... ON"
            " CONFLICT(name) DO UPDATE -- not INSERT OR REPLACE.\n\n"
            "Checked: every branch's branch_id, name and town"
        ),
        solution=("INSERT INTO branches (name, town, opened_on) VALUES ('Old Town', 'Castleford', '2026-09-01')"
                  " ON CONFLICT(name) DO UPDATE SET town = excluded.town;\n"
                  "INSERT INTO branches (name, town, opened_on) VALUES ('Westgate', 'Leeds', '2026-09-01')"
                  " ON CONFLICT(name) DO UPDATE SET town = excluded.town;"),
        trap_sql=("INSERT OR REPLACE INTO branches (name, town, opened_on) VALUES ('Old Town', 'Castleford', '2026-09-01');\n"
                  "INSERT OR REPLACE INTO branches (name, town, opened_on) VALUES ('Westgate', 'Leeds', '2026-09-01');"),
        probe_sql="SELECT branch_id, name, town FROM branches ORDER BY branch_id",
        note="An UPSERT keeps the existing row and changes the columns"
             " you name; `excluded` is the row that would have been"
             " inserted. INSERT OR REPLACE instead DELETES the old row"
             " and inserts a new one with a new branch_id -- and here it"
             " cannot even do that, because copies, staff and members"
             " point at branch 6, so the foreign keys refuse the delete"
             " and the script fails.",
        claims=[("seven branches, Old Town still number 6",
                 lambda rows, c: len(rows) == 7 and (6, 'Old Town', 'Castleford') in rows
                 and (7, 'Westgate', 'Leeds') in rows)],
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
