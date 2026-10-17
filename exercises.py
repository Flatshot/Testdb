"""Practice exercises: fifteen questions on the library schema.

The tenth set on the library (SEED 861), the second at two tools per
question, with the tools paired differently. Plans and CASE -- a date
range that lets idx_loans_due be searched, with a CASE on the rows it
finds; a covering read of idx_loans_copy with a CASE on the weekday. JSON
and dates -- json_group_array DISTINCT over strftime years, and json_each
over a list of dates with a due-date count beside each. Bare columns and
open ends -- MAX's row among the never-loaned copies, MIN's row among the
open holds. Set operations and text -- INTERSECT of first words, EXCEPT of
surnames. Windows and NULLs -- a running total of unpaid pence through a
CASE, and COALESCE over LAG. Recursion and text -- a comma list split into
rows by recursion, and quarters labelled by printf. And three WRITABLE
questions in two steps each:

  * a BEFORE UPDATE trigger that compares OLD.due_on with a date
  * a table filled by INSERT ... SELECT, then an UPSERT with JSON in it
  * a DELETE by ROW_NUMBER that keeps one row per member

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script.

The two query-plan questions carry `plan_requires` / `plan_forbids`, checked
against EXPLAIN QUERY PLAN, and a `starter_sql` that opens in the editor:
correct, slow, and the thing to improve.
"""

import sqlite3

EXERCISES = [
    # ==================================================== 1 Plans and CASE
    dict(
        id=1, ledger="Q982", concept="X5", tier="1 - Plans and CASE",
        title="Due in May, found by the index",
        prompt=(
            "Every loan due in May 2026, with a status: 'out' if"
            " returned_on is NULL, else 'returned'. The query in the"
            " editor is correct but wraps due_on in strftime, which reads"
            " all 24,000 loans. Rewrite the WHERE as a RANGE on the bare"
            " column so idx_loans_due can be searched. Your plan must"
            " mention idx_loans_due with SEARCH, not SCAN.\n\n"
            "Return: loan_id, status"
        ),
        starter_sql=("SELECT loan_id, CASE WHEN returned_on IS NULL THEN 'out' ELSE 'returned' END"
                     " FROM loans WHERE strftime('%Y-%m', due_on) = '2026-05'"),
        solution=("SELECT loan_id, CASE WHEN returned_on IS NULL THEN 'out' ELSE 'returned' END"
                  " FROM loans WHERE due_on >= '2026-05-01' AND due_on < '2026-06-01'"),
        trap_sql=("SELECT loan_id, CASE WHEN returned_on IS NULL THEN 'out' ELSE 'returned' END"
                  " FROM loans WHERE due_on LIKE '2026-05%'"),
        note="An index on a date column is searchable by a RANGE of the"
             " stored text -- on or after the 1st, before the 1st of the"
             " next month -- and not by any function of the column."
             " strftime hides the column; so does LIKE here, which SQLite"
             " will not turn into a range on a BINARY column. The CASE is"
             " unaffected by any of this: it runs on whatever rows arrive.",
        plan_requires=("SEARCH loans USING INDEX idx_loans_due",),
        plan_forbids=("SCAN",),
        claims=[("thirteen hundred or so loans, ten of them out",
                 lambda rows, c: 1300 < len(rows) < 1400 and sum(r[1] == 'out' for r in rows) == 10)],
    ),
    dict(
        id=2, ledger="Q983", concept="X5", tier="1 - Plans and CASE",
        title="Copy 1's loans, weekday or weekend, from the index alone",
        prompt=(
            "For copy 1, each loan's loaned_on and whether it was a"
            " 'weekend' (strftime %w of '0' or '6') or a 'weekday'. The"
            " index idx_loans_copy holds copy_id and loaned_on, so a"
            " query that touches only those columns can be answered from"
            " the index without opening the table: your plan must say"
            " COVERING INDEX idx_loans_copy with SEARCH. The query in the"
            " editor is correct and scans.\n\n"
            "Return: loaned_on, day_type"
        ),
        starter_sql=("SELECT loaned_on, CASE WHEN strftime('%w', loaned_on) IN ('0', '6') THEN 'weekend'"
                     " ELSE 'weekday' END FROM loans WHERE copy_id + 0 = 1"),
        solution=("SELECT loaned_on, CASE WHEN strftime('%w', loaned_on) IN ('0', '6') THEN 'weekend'"
                  " ELSE 'weekday' END FROM loans WHERE copy_id = 1"),
        trap_sql=("SELECT loaned_on, CASE WHEN strftime('%w', loaned_on) IN ('0', '6') THEN 'weekend'"
                  " ELSE 'weekday' END FROM loans WHERE copy_id = 1 AND returned_on IS NOT NULL"),
        note="Two things have to be true for a COVERING read: the WHERE"
             " must let the index be searched -- copy_id = 1, not copy_id"
             " + 0 = 1 -- and every column the query mentions must be in"
             " the index. Mention returned_on, even only in the WHERE,"
             " and SQLite must visit the table for each row: the plan"
             " keeps SEARCH but drops the word COVERING. The CASE over"
             " loaned_on is fine, because loaned_on is in the index.",
        plan_requires=("SEARCH loans USING COVERING INDEX idx_loans_copy",),
        claims=[("fourteen loans of copy 1, a few at weekends",
                 lambda rows, c: len(rows) == 14 and 1 <= sum(r[1] == 'weekend' for r in rows) <= 8)],
    ),
    # ==================================================== 2 JSON and dates
    dict(
        id=3, ledger="Q984", concept="JSN", tier="2 - JSON and dates",
        title="The years each branch withdrew stock, as JSON",
        prompt=(
            "For each branch that has withdrawn copies, a JSON array of"
            " the DISTINCT years in which it withdrew them, ascending:"
            " strftime for the year of withdrawn_on, json_group_array"
            " with DISTINCT and an ORDER BY inside its parentheses, over"
            " the withdrawn copies only.\n\n"
            "Return: branch_id, years"
        ),
        solution=("SELECT branch_id, json_group_array(DISTINCT strftime('%Y', withdrawn_on)"
                  " ORDER BY strftime('%Y', withdrawn_on)) FROM copies WHERE withdrawn_on IS NOT NULL"
                  " GROUP BY branch_id"),
        trap_sql=("SELECT branch_id, json_group_array(strftime('%Y', withdrawn_on)"
                  " ORDER BY strftime('%Y', withdrawn_on)) FROM copies WHERE withdrawn_on IS NOT NULL"
                  " GROUP BY branch_id"),
        note="json_group_array accepts DISTINCT and ORDER BY like"
             " GROUP_CONCAT does. Without DISTINCT a branch that withdrew"
             " six copies in 2024 says '2024' six times, which is still"
             " valid JSON and still wrong. The WHERE keeps the NULLs of"
             " the copies still on the shelf out of the array; strftime"
             " of NULL is NULL, and JSON would carry it as null.",
        claims=[("six arrays, no repeats, not all alike",
                 lambda rows, c: len(rows) == 6
                 and all(len(set(__import__('json').loads(r[1]))) == len(__import__('json').loads(r[1]))
                         for r in rows)
                 and len({r[1] for r in rows}) > 1)],
    ),
    dict(
        id=4, ledger="Q985", concept="JSN", tier="2 - JSON and dates",
        title="Three dates to check, from a JSON list",
        prompt=(
            "Given the JSON list '[\"2026-01-15\", \"2026-03-01\","
            " \"2026-06-30\"]': for each date, how many loans were DUE"
            " that day, and the day of the week as strftime's %w gives"
            " it. json_each turns the list into rows with a `value`"
            " column.\n\n"
            "Return: day, due, weekday"
        ),
        solution=("SELECT value, (SELECT COUNT(*) FROM loans l WHERE l.due_on = value), strftime('%w', value)"
                  " FROM json_each('[\"2026-01-15\", \"2026-03-01\", \"2026-06-30\"]')"),
        trap_sql=("SELECT value, (SELECT COUNT(*) FROM loans l WHERE l.loaned_on = value), strftime('%w', value)"
                  " FROM json_each('[\"2026-01-15\", \"2026-03-01\", \"2026-06-30\"]')"),
        note="json_each hands each element over as `value`, and the"
             " element is a date string, so strftime and a correlated"
             " count both work on it directly. The count is of due_on,"
             " the column the question names; loaned_on gives how many"
             " loans STARTED that day, and no loan started on 30 June.",
        claims=[("three days, the last one a Tuesday",
                 lambda rows, c: len(rows) == 3 and ('2026-06-30', 34, '2') in rows)],
    ),
    # ========================================== 3 Bare columns and open ends
    dict(
        id=5, ledger="Q986", concept="BARE", tier="3 - Bare columns and open ends",
        title="The newest copy nobody has borrowed, per branch",
        prompt=(
            "For each branch: among its copies that have NEVER been"
            " loaned, the most recently acquired one -- copy_id and"
            " acquired_on. NOT EXISTS against loans picks the never-"
            "loaned copies; MAX(acquired_on) with copy_id as a bare"
            " column picks the newest.\n\n"
            "Return: branch_id, copy_id, acquired_on"
        ),
        solution=("SELECT branch_id, copy_id, MAX(acquired_on) FROM copies c"
                  " WHERE NOT EXISTS (SELECT 1 FROM loans l WHERE l.copy_id = c.copy_id) GROUP BY branch_id"),
        trap_sql="SELECT branch_id, copy_id, MAX(acquired_on) FROM copies GROUP BY branch_id",
        note="The WHERE narrows the copies BEFORE the grouping, so the"
             " MAX is taken over the never-loaned ones only, and SQLite's"
             " bare-column rule brings that copy's id along. Without the"
             " NOT EXISTS the answer is each branch's newest copy of all,"
             " most of which have been out several times.",
        claims=[("six branches, every copy named never loaned",
                 lambda rows, c: len(rows) == 6
                 and all(c.execute("SELECT COUNT(*) FROM loans WHERE copy_id = ?", (r[1],)).fetchone()[0] == 0
                         for r in rows))],
    ),
    dict(
        id=6, ledger="Q987", concept="BARE", tier="3 - Bare columns and open ends",
        title="Each member's oldest open hold at Northgate",
        prompt=(
            "For each member with an OPEN hold at branch 2 -- fulfilled_on"
            " and cancelled_on both NULL -- their earliest such hold:"
            " member_id, the book, and when it was placed. MIN(placed_at)"
            " with book_id as a bare column, over the open holds only.\n\n"
            "Return: member_id, book_id, placed_at"
        ),
        solution=("SELECT member_id, book_id, MIN(placed_at) FROM holds"
                  " WHERE branch_id = 2 AND fulfilled_on IS NULL AND cancelled_on IS NULL GROUP BY member_id"),
        trap_sql=("SELECT member_id, book_id, MIN(placed_at) FROM holds"
                  " WHERE branch_id = 2 GROUP BY member_id"),
        note="'Open' is the two-NULL test, and it belongs in the WHERE"
             " so that closed holds are not candidates for the MIN. Leave"
             " it out and the query returns every member who ever held"
             " at Northgate, with their first hold ever -- four times as"
             " many rows, most of them long since fulfilled.",
        claims=[("fifty-six members, every hold still open",
                 lambda rows, c: len(rows) == 56
                 and all(c.execute("SELECT COUNT(*) FROM holds WHERE member_id = ? AND book_id = ? AND placed_at = ?"
                                   " AND fulfilled_on IS NULL AND cancelled_on IS NULL", r).fetchone()[0] == 1
                         for r in rows))],
    ),
    # ============================================ 4 Set operations and text
    dict(
        id=7, ledger="Q988", concept="S1", tier="4 - Set operations and text",
        title="First words that fiction and poetry share",
        prompt=(
            "The first words of titles that occur in BOTH fiction and"
            " poetry: SUBSTR up to the space in each genre's titles, and"
            " INTERSECT between the two.\n\n"
            "Return: first_word"
        ),
        solution=("SELECT SUBSTR(title, 1, INSTR(title, ' ') - 1) FROM books WHERE genre = 'fiction'"
                  " INTERSECT SELECT SUBSTR(title, 1, INSTR(title, ' ') - 1) FROM books WHERE genre = 'poetry'"),
        trap_sql=("SELECT SUBSTR(title, 1, INSTR(title, ' ') - 1) FROM books WHERE genre = 'fiction'"
                  " UNION SELECT SUBSTR(title, 1, INSTR(title, ' ') - 1) FROM books WHERE genre = 'poetry'"),
        note="A set operation works on whatever its two SELECTs produce,"
             " including computed text, so the SUBSTR is written on both"
             " sides. INTERSECT keeps the words both genres use; UNION"
             " keeps the words either uses, which here is more than twice"
             " as many.",
        claims=[("fourteen shared first words, 'The' among them",
                 lambda rows, c: len(rows) == 14 and ('The',) in rows)],
    ),
    dict(
        id=8, ledger="Q989", concept="S1", tier="4 - Set operations and text",
        title="Member surnames no staff member has",
        prompt=(
            "Surnames -- the part of name after the space -- that some"
            " MEMBER has and no member of STAFF has, each once: EXCEPT"
            " between the two tables' extracted surnames.\n\n"
            "Return: surname"
        ),
        solution=("SELECT SUBSTR(name, INSTR(name, ' ') + 1) FROM members"
                  " EXCEPT SELECT SUBSTR(name, INSTR(name, ' ') + 1) FROM staff"),
        trap_sql=("SELECT SUBSTR(name, INSTR(name, ' ') + 1) FROM staff"
                  " EXCEPT SELECT SUBSTR(name, INSTR(name, ' ') + 1) FROM members"),
        note="EXCEPT removes duplicates as it goes, so a surname shared"
             " by thirty members comes out once. The order of the two"
             " SELECTs is the question: members minus staff gives eight"
             " surnames, staff minus members gives none, because every"
             " staff surname also belongs to some member.",
        claims=[("eight surnames",
                 lambda rows, c: len(rows) == 8)],
    ),
    # ================================================== 5 Windows and NULLs
    dict(
        id=9, ledger="Q990", concept="W1", tier="5 - Windows and NULLs",
        title="Unpaid fines mounting up, month by month",
        prompt=(
            "For each month fines were issued: how many of that month's"
            " fines are still unpaid, and the running total in pence of"
            " unpaid fines issued up to and including that month. The"
            " unpaid amount is a conditional SUM -- a CASE with no ELSE,"
            " which SUM skips as NULL -- and the running total is a"
            " window SUM over it.\n\n"
            "Return: month, unpaid, running_unpaid_pence"
        ),
        solution=("SELECT strftime('%Y-%m', issued_on) AS m, SUM(paid_on IS NULL),"
                  " SUM(SUM(CASE WHEN paid_on IS NULL THEN amount_pence END))"
                  " OVER (ORDER BY strftime('%Y-%m', issued_on)) FROM fines GROUP BY m"),
        trap_sql=("SELECT strftime('%Y-%m', issued_on) AS m, COUNT(paid_on),"
                  " SUM(SUM(CASE WHEN paid_on IS NULL THEN amount_pence END))"
                  " OVER (ORDER BY strftime('%Y-%m', issued_on)) FROM fines GROUP BY m"),
        note="COUNT(paid_on) counts the fines WITH a payment date -- the"
             " paid ones -- which is the opposite of what was asked; the"
             " unpaid count is SUM(paid_on IS NULL). The CASE with no"
             " ELSE yields NULL for paid fines, SUM ignores the NULLs,"
             " and the outer window SUM accumulates the monthly results"
             " in date order.",
        claims=[("eighteen months, the last running total equal to all unpaid pence",
                 lambda rows, c: len(rows) == 18 and max(rows)[2] == 414960
                 and sum(r[1] for r in rows) == 1380)],
    ),
    dict(
        id=10, ledger="Q991", concept="W3", tier="5 - Windows and NULLs",
        title="The gaps between one member's loans",
        prompt=(
            "Member 834's loans in date order: loan_id, loaned_on, and"
            " the whole number of days since their PREVIOUS loan -- 0,"
            " not NULL, for the first. LAG gives the previous date,"
            " julianday the difference, and COALESCE turns the first"
            " row's NULL into 0.\n\n"
            "Return: loan_id, loaned_on, gap_days"
        ),
        solution=("SELECT loan_id, loaned_on, COALESCE(CAST(julianday(loaned_on)"
                  " - julianday(LAG(loaned_on) OVER (ORDER BY loaned_on)) AS INTEGER), 0)"
                  " FROM loans WHERE member_id = 834"),
        trap_sql=("SELECT loan_id, loaned_on, CAST(julianday(loaned_on)"
                  " - julianday(LAG(loaned_on) OVER (ORDER BY loaned_on)) AS INTEGER)"
                  " FROM loans WHERE member_id = 834"),
        note="LAG has nothing to look back to on the first row and"
             " returns NULL, which julianday and the subtraction pass"
             " along. COALESCE(..., 0) is the fix when the question wants"
             " a number there; LAG's third argument, a default, is the"
             " other way: LAG(loaned_on, 1, loaned_on) gives a gap of 0"
             " as well.",
        claims=[("fifteen loans, the first with a gap of 0 and none NULL",
                 lambda rows, c: len(rows) == 15 and all(r[2] is not None for r in rows)
                 and min(rows, key=lambda r: r[1])[2] == 0)],
    ),
    # ================================================ 6 Recursion and text
    dict(
        id=11, ledger="Q992", concept="R1", tier="6 - Recursion and text",
        title="A comma list turned into rows",
        prompt=(
            "Split the text 'fiction,poetry,travel' into one row per"
            " genre with a recursive CTE -- each step takes the part"
            " before the first comma and carries the rest forward -- and"
            " count the books in each. Append a trailing comma to the"
            " text first so the last item ends like the others.\n\n"
            "Return: genre, books"
        ),
        solution=("WITH RECURSIVE s(item, rest) AS (SELECT '', 'fiction,poetry,travel,'"
                  " UNION ALL SELECT SUBSTR(rest, 1, INSTR(rest, ',') - 1), SUBSTR(rest, INSTR(rest, ',') + 1)"
                  " FROM s WHERE rest <> '')"
                  " SELECT item, (SELECT COUNT(*) FROM books b WHERE b.genre = s.item) FROM s WHERE item <> ''"),
        trap_sql=("WITH RECURSIVE s(item, rest) AS (SELECT '', 'fiction,poetry,travel'"
                  " UNION ALL SELECT SUBSTR(rest, 1, INSTR(rest, ',') - 1), SUBSTR(rest, INSTR(rest, ',') + 1)"
                  " FROM s WHERE INSTR(rest, ',') > 0)"
                  " SELECT item, (SELECT COUNT(*) FROM books b WHERE b.genre = s.item) FROM s WHERE item <> ''"),
        note="The classic recursive string split: the anchor holds the"
             " whole text as `rest`, and each step peels one item off the"
             " front with SUBSTR and INSTR. Stopping when no comma is left"
             " loses the final item, because it never had a comma after"
             " it -- hence the trailing comma, so every item ends the same"
             " way and the loop runs until rest is empty.",
        claims=[("three genres, fiction the largest",
                 lambda rows, c: len(rows) == 3 and ('fiction', 153) in rows and ('travel', 71) in rows)],
    ),
    dict(
        id=12, ledger="Q993", concept="R1", tier="6 - Recursion and text",
        title="Six quarters, labelled",
        prompt=(
            "Loans per quarter from 2025Q1 to 2026Q2, labelled like"
            " '2025Q1': a recursive CTE of quarter starts stepping"
            " '+3 months', printf to build the label from strftime's"
            " year and (month + 2) / 3, and a count of the loans from"
            " each start up to but not including the next.\n\n"
            "Return: quarter, loans"
        ),
        solution=("WITH RECURSIVE qs(start) AS (SELECT '2025-01-01' UNION ALL SELECT date(start, '+3 months')"
                  " FROM qs WHERE start < '2026-04-01')"
                  " SELECT printf('%sQ%d', strftime('%Y', start), (CAST(strftime('%m', start) AS INTEGER) + 2) / 3),"
                  " (SELECT COUNT(*) FROM loans l WHERE l.loaned_on >= qs.start AND l.loaned_on < date(qs.start, '+3 months'))"
                  " FROM qs"),
        trap_sql=("WITH RECURSIVE qs(start) AS (SELECT '2025-01-01' UNION ALL SELECT date(start, '+3 months')"
                  " FROM qs WHERE start < '2026-04-01')"
                  " SELECT printf('%sQ%d', strftime('%Y', start), (CAST(strftime('%m', start) AS INTEGER) + 2) / 3),"
                  " (SELECT COUNT(*) FROM loans l WHERE l.loaned_on >= qs.start AND l.loaned_on <= date(qs.start, '+3 months'))"
                  " FROM qs"),
        note="printf's %s takes the year text and %d the quarter number,"
             " so the label is built in one call. The counting window is"
             " half-open, start inclusive and next start exclusive;"
             " with <= the first day of each following quarter is counted"
             " twice and every total is a day too big.",
        claims=[("six quarters of about four thousand",
                 lambda rows, c: len(rows) == 6 and sum(r[1] for r in rows) == 23976
                 and {r[0] for r in rows} == {'2025Q1', '2025Q2', '2025Q3', '2025Q4', '2026Q1', '2026Q2'})],
    ),
    # ================================================= 7 Changing the data
    dict(
        id=13, ledger="Q994", concept="TRG", tier="7 - Changing the data",
        kind="script",
        title="No renewal once a loan is overdue",
        prompt=(
            "Write a BEFORE UPDATE OF renewals trigger on loans that"
            " refuses -- RAISE(ABORT, ...) -- to raise renewals on a loan"
            " whose due_on BEFORE the update, OLD.due_on, is earlier than"
            " '2026-06-30'. The question then renews loan 4107, due 20"
            " June, and loan 156, due 17 July, each by one renewal and"
            " fourteen days.\n\n"
            "Checked: the renewals and due_on of both loans"
        ),
        solution=("CREATE TRIGGER no_late_renewal BEFORE UPDATE OF renewals ON loans\n"
                  "WHEN NEW.renewals > OLD.renewals AND OLD.due_on < '2026-06-30'\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'loan is overdue and cannot be renewed');\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER no_late_renewal BEFORE UPDATE OF renewals ON loans\n"
                  "WHEN NEW.renewals > OLD.renewals AND NEW.due_on < '2026-06-30'\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'loan is overdue and cannot be renewed');\n"
                  "END;"),
        driver_sql=("UPDATE loans SET renewals = renewals + 1, due_on = date(due_on, '+14 days') WHERE loan_id = 4107;\n"
                    "UPDATE loans SET renewals = renewals + 1, due_on = date(due_on, '+14 days') WHERE loan_id = 156;"),
        probe_sql="SELECT loan_id, renewals, due_on FROM loans WHERE loan_id IN (4107, 156) ORDER BY loan_id",
        note="In a BEFORE UPDATE trigger OLD is the row as it stands and"
             " NEW is the row as it would become. The rule is about the"
             " loan's CURRENT due date, so the test is on OLD.due_on;"
             " the same renewal pushes NEW.due_on fourteen days on, past"
             " 30 June for loan 4107, so a test on NEW lets the overdue"
             " loan through.",
        claims=[("4107 refused, 156 renewed",
                 lambda rows, c: rows == [(156, 1, '2026-07-31'), (4107, 0, '2026-06-20')])],
    ),
    dict(
        id=14, ledger="Q995", concept="DML", tier="7 - Changing the data",
        kind="script",
        title="Opening hours, with one branch different",
        prompt=(
            "Create `branch_hours (branch_id INTEGER PRIMARY KEY, hours"
            " TEXT NOT NULL)` and fill it for EVERY branch from branches"
            " with the JSON '{\"sat\": \"09:00-13:00\"}' -- INSERT ..."
            " SELECT. Then record that Old Town (branch 6) opens"
            " '10:00-16:00' on Saturdays with an INSERT ... ON CONFLICT"
            " (branch_id) DO UPDATE, so the same statement would work"
            " whether or not the row existed.\n\n"
            "Checked: each branch's Saturday hours, read with json_extract"
        ),
        solution=("CREATE TABLE branch_hours (branch_id INTEGER PRIMARY KEY, hours TEXT NOT NULL);\n"
                  "INSERT INTO branch_hours SELECT branch_id, '{\"sat\": \"09:00-13:00\"}' FROM branches;\n"
                  "INSERT INTO branch_hours (branch_id, hours) VALUES (6, '{\"sat\": \"10:00-16:00\"}')\n"
                  "  ON CONFLICT (branch_id) DO UPDATE SET hours = excluded.hours;"),
        trap_sql=("CREATE TABLE branch_hours (branch_id INTEGER PRIMARY KEY, hours TEXT NOT NULL);\n"
                  "INSERT INTO branch_hours SELECT branch_id, '{\"sat\": \"09:00-13:00\"}' FROM branches;\n"
                  "INSERT INTO branch_hours (branch_id, hours) VALUES (6, '{\"sat\": \"10:00-16:00\"}');"),
        probe_sql="SELECT branch_id, json_extract(hours, '$.sat') FROM branch_hours ORDER BY branch_id",
        note="Two steps: a bulk INSERT ... SELECT that seeds every branch,"
             " then an UPSERT for the exception. The plain INSERT for"
             " branch 6 collides with the row the first step created and"
             " fails, leaving Old Town on the default hours; ON CONFLICT"
             " DO UPDATE turns the collision into the update that was"
             " meant. json_extract reads the value back out of the text.",
        claims=[("six branches, Old Town open longer",
                 lambda rows, c: len(rows) == 6 and (6, '10:00-16:00') in rows
                 and sum(r[1] == '09:00-13:00' for r in rows) == 5)],
    ),
    dict(
        id=15, ledger="Q996", concept="DML", tier="7 - Changing the data",
        kind="script",
        title="One closed hold per member, the latest kept",
        prompt=(
            "Thin the history: for each member, keep only their most"
            " recent CLOSED hold -- fulfilled or cancelled -- by placed_at,"
            " and delete their other closed holds. Open holds are not"
            " touched. ROW_NUMBER partitioned by member over the closed"
            " holds, newest first, in a subquery that picks the hold_ids"
            " to delete.\n\n"
            "Checked: holds remaining, open holds remaining, and how many"
            " members still have more than one closed hold"
        ),
        solution=("DELETE FROM holds WHERE hold_id IN ("
                  "SELECT hold_id FROM (SELECT hold_id, ROW_NUMBER() OVER (PARTITION BY member_id ORDER BY placed_at DESC) AS rn"
                  " FROM holds WHERE fulfilled_on IS NOT NULL OR cancelled_on IS NOT NULL) WHERE rn > 1);"),
        trap_sql=("DELETE FROM holds WHERE hold_id IN ("
                  "SELECT hold_id FROM (SELECT hold_id, ROW_NUMBER() OVER (PARTITION BY member_id ORDER BY placed_at DESC) AS rn"
                  " FROM holds) WHERE rn > 1);"),
        probe_sql=("SELECT COUNT(*), SUM(fulfilled_on IS NULL AND cancelled_on IS NULL),"
                   " (SELECT COUNT(*) FROM (SELECT member_id FROM holds WHERE fulfilled_on IS NOT NULL OR cancelled_on IS NOT NULL"
                   " GROUP BY member_id HAVING COUNT(*) > 1)) FROM holds"),
        note="The WHERE inside the numbering subquery is what keeps the"
             " open holds out of it: number only the closed holds, and"
             " only closed holds can be deleted. Number every hold and an"
             " open hold can be the one kept, with the member's closed"
             " ones all deleted -- or an open hold deleted because a"
             " closed one is newer.",
        claims=[("1098 holds left, all 337 open ones among them, no member with two closed",
                 lambda rows, c: rows == [(1500 - 402, 337, 0)])],
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
