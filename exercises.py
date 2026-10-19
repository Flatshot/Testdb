"""Practice exercises: fifteen questions on the library schema.

The eleventh set on the library (SEED 861), the third at two tools per
question, and the first to pass Q1000. Dates and windows -- a share of the
week by strftime under a window SUM, quarters by date arithmetic under
LAG. Grain and JSON -- DISTINCT titles packed into JSON beside a copy
count, and json_group_object over a grouped CTE. EXISTS and text -- LIKE
with NOT EXISTS, and a surname extracted on both sides of a correlated
EXISTS. Recursion and plans -- a recursive list of ids joined to the
rowid, graded on the plan; and recursive bands joined to a half-open
range. Aggregates and NULLs -- COUNT(column) in HAVING, and COALESCE
inside AVG. Set operations and dates -- EXCEPT of Sundays, INTERSECT of
days. And three WRITABLE questions in two steps each:

  * an AFTER INSERT trigger that logs a JSON object
  * an UPDATE whose SET holds a CASE inside a date modifier
  * a view holding DENSE_RANK over a grouped query

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script.

The query-plan question carries `plan_requires` / `plan_forbids`, checked
against EXPLAIN QUERY PLAN, and a `starter_sql` that opens in the editor:
correct, slow, and the thing to improve.
"""

import sqlite3

EXERCISES = [
    # ================================================== 1 Dates and windows
    dict(
        id=1, ledger="Q997", concept="W3", tier="1 - Dates and windows",
        title="Each weekday's share of the loans",
        prompt=(
            "For each day of the week -- strftime's %w, '0' for Sunday"
            " -- how many loans started on it and what percentage of ALL"
            " loans that is, to one decimal. The total is a window SUM"
            " over the grouped counts, with no PARTITION.\n\n"
            "Return: weekday, loans, pct"
        ),
        solution=("SELECT strftime('%w', loaned_on), COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) FROM loans GROUP BY 1"),
        trap_sql=("SELECT strftime('%w', loaned_on), COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY strftime('%w', loaned_on)), 1)"
                  " FROM loans GROUP BY 1"),
        note="SUM(COUNT(*)) OVER () adds up the seven grouped counts and"
             " puts the total on every row, so each row can divide by"
             " it. PARTITION BY the weekday makes each partition one row,"
             " and every share comes out as 100. The seven shares should"
             " add up to a hundred, and they are close to equal.",
        claims=[("seven days, shares adding up to a hundred",
                 lambda rows, c: len(rows) == 7 and 99.5 < sum(r[2] for r in rows) < 100.5
                 and all(13 < r[2] < 16 for r in rows))],
    ),
    dict(
        id=2, ledger="Q998", concept="D1", tier="1 - Dates and windows",
        title="Quarter on quarter",
        prompt=(
            "Loans per quarter, labelled '2025Q1' and so on, with the"
            " change from the previous quarter -- NULL for the first."
            " The label is strftime's year, 'Q', and (month + 2) / 3"
            " joined with ||; the change is LAG over the grouped"
            " counts in label order.\n\n"
            "Return: quarter, loans, change"
        ),
        solution=("SELECT strftime('%Y', loaned_on) || 'Q' || ((CAST(strftime('%m', loaned_on) AS INTEGER) + 2) / 3) AS q,"
                  " COUNT(*), COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY"
                  " strftime('%Y', loaned_on) || 'Q' || ((CAST(strftime('%m', loaned_on) AS INTEGER) + 2) / 3))"
                  " FROM loans GROUP BY q"),
        trap_sql=("SELECT strftime('%Y', loaned_on) || 'Q' || ((CAST(strftime('%m', loaned_on) AS INTEGER) + 2) / 3) AS q,"
                  " COUNT(*), COUNT(*) - LEAD(COUNT(*)) OVER (ORDER BY"
                  " strftime('%Y', loaned_on) || 'Q' || ((CAST(strftime('%m', loaned_on) AS INTEGER) + 2) / 3))"
                  " FROM loans GROUP BY q"),
        note="The quarter label is text built from two strftime calls,"
             " and because the year comes first it sorts correctly, so"
             " the window can ORDER BY it. LAG reaches the quarter"
             " before; LEAD the quarter after, which puts the NULL on"
             " the last row and flips every sign.",
        claims=[("six quarters, the first with no change",
                 lambda rows, c: len(rows) == 6 and min(rows)[2] is None
                 and sum(r[1] for r in rows) == 23976)],
    ),
    # ====================================================== 2 Grain and JSON
    dict(
        id=3, ledger="Q999", concept="C2", tier="2 - Grain and JSON",
        title="Prolific authors: their titles and their copies",
        prompt=(
            "For each author with three or more books: how many copies"
            " of their books exist in all, and their titles as one JSON"
            " array in alphabetical order. Joining copies multiplies the"
            " title rows, so the array needs DISTINCT -- json_group_array"
            "(DISTINCT title ORDER BY title) -- and the HAVING needs"
            " COUNT(DISTINCT book_id).\n\n"
            "Return: author_id, copies, titles"
        ),
        solution=("SELECT a.author_id, COUNT(c.copy_id), json_group_array(DISTINCT b.title ORDER BY b.title)"
                  " FROM authors a JOIN books b ON b.author_id = a.author_id"
                  " LEFT JOIN copies c ON c.book_id = b.book_id"
                  " GROUP BY a.author_id HAVING COUNT(DISTINCT b.book_id) >= 3"),
        trap_sql=("SELECT a.author_id, COUNT(c.copy_id), json_group_array(b.title ORDER BY b.title)"
                  " FROM authors a JOIN books b ON b.author_id = a.author_id"
                  " LEFT JOIN copies c ON c.book_id = b.book_id"
                  " GROUP BY a.author_id HAVING COUNT(DISTINCT b.book_id) >= 3"),
        note="After the join to copies there is one row per copy, which"
             " is right for counting copies and wrong for listing titles:"
             " a title with four copies would appear four times in the"
             " array. DISTINCT inside json_group_array fixes the list the"
             " same way COUNT(DISTINCT book_id) fixes the HAVING.",
        claims=[("a hundred authors, no title repeated in any array",
                 lambda rows, c: len(rows) == 100
                 and all(len(__import__('json').loads(r[2])) == len(set(__import__('json').loads(r[2])))
                         and len(__import__('json').loads(r[2])) >= 3 for r in rows))],
    ),
    dict(
        id=4, ledger="Q1000", concept="JSN", tier="2 - Grain and JSON",
        title="Each branch's stock as a JSON object",
        prompt=(
            "For each branch, ONE JSON object whose keys are the"
            " conditions and whose values are the copy counts -- {"
            "\"damaged\": 32, \"good\": 220, \"worn\": 129}. A CTE"
            " grouped by branch and condition, then json_group_object("
            "condition, n) grouped by branch; grouping the CTE by"
            " branch_id, condition puts the keys in alphabetical order.\n\n"
            "Return: branch_id, stock"
        ),
        solution=("WITH t AS (SELECT branch_id, condition, COUNT(*) AS n FROM copies GROUP BY branch_id, condition)"
                  " SELECT branch_id, json_group_object(condition, n) FROM t GROUP BY branch_id"),
        trap_sql=("WITH t AS (SELECT branch_id, condition, COUNT(*) AS n FROM copies GROUP BY branch_id, condition)"
                  " SELECT branch_id, json_group_array(n) FROM t GROUP BY branch_id"),
        note="json_group_object takes a key and a value per row and"
             " builds one object per group, where json_group_array would"
             " give a bare list of numbers with no way to tell which"
             " count is which. Two levels of grouping again: the CTE to"
             " (branch, condition), the outer query to branch.",
        claims=[("six objects with the three conditions as keys",
                 lambda rows, c: len(rows) == 6
                 and all(sorted(__import__('json').loads(r[1])) == ['damaged', 'good', 'worn'] for r in rows))],
    ),
    # ====================================================== 3 EXISTS and text
    dict(
        id=5, ledger="Q1001", concept="E1", tier="3 - EXISTS and text",
        title="'The' titles that Central does not hold",
        prompt=(
            "Books whose title begins 'The ' and of which Central (branch"
            " 1) holds NO copy: book_id and title. LIKE for the prefix,"
            " NOT EXISTS over copies for the branch.\n\n"
            "Return: book_id, title"
        ),
        solution=("SELECT b.book_id, b.title FROM books b WHERE b.title LIKE 'The %'"
                  " AND NOT EXISTS (SELECT 1 FROM copies c WHERE c.book_id = b.book_id AND c.branch_id = 1)"),
        trap_sql=("SELECT b.book_id, b.title FROM books b WHERE b.title LIKE 'The %'"
                  " AND EXISTS (SELECT 1 FROM copies c WHERE c.book_id = b.book_id AND c.branch_id <> 1)"),
        note="'Has a copy somewhere else' is not 'has no copy at"
             " Central': a book stocked at Central AND Northgate passes"
             " the first and fails the second. The negative has to be"
             " written as a negative, NOT EXISTS, with the branch inside"
             " it. The LIKE with a trailing space keeps 'Theory...' out.",
        claims=[("eighty-eight books, every title starting with The",
                 lambda rows, c: len(rows) == 88 and all(r[1].startswith('The ') for r in rows))],
    ),
    dict(
        id=6, ledger="Q1002", concept="STR", tier="3 - EXISTS and text",
        title="Members who share a surname with their branch's staff",
        prompt=(
            "Members whose surname -- the part of name after the space"
            " -- is also the surname of a member of staff at the member's"
            " OWN home branch: member_id and name. A correlated EXISTS"
            " over staff that extracts the surname on both sides and"
            " matches the branch.\n\n"
            "Return: member_id, name"
        ),
        solution=("SELECT m.member_id, m.name FROM members m WHERE EXISTS ("
                  "SELECT 1 FROM staff s WHERE s.branch_id = m.home_branch_id"
                  " AND SUBSTR(s.name, INSTR(s.name, ' ') + 1) = SUBSTR(m.name, INSTR(m.name, ' ') + 1))"),
        trap_sql=("SELECT m.member_id, m.name FROM members m WHERE EXISTS ("
                  "SELECT 1 FROM staff s"
                  " WHERE SUBSTR(s.name, INSTR(s.name, ' ') + 1) = SUBSTR(m.name, INSTR(m.name, ' ') + 1))"),
        note="A correlated subquery can compare computed text from both"
             " rows, and the SUBSTR has to be written for each side."
             " The branch match is the second condition, and without it"
             " two-thirds of the members qualify -- the twenty or so"
             " surnames in use are shared by everyone.",
        claims=[("a few hundred members",
                 lambda rows, c: 100 < len(rows) < 500)],
    ),
    # =================================================== 4 Recursion and plans
    dict(
        id=7, ledger="Q1003", concept="X5", tier="4 - Recursion and plans",
        title="The first hundred loans, by their primary key",
        prompt=(
            "The members who hold loans 1 to 100: the loan number and"
            " member_id. A recursive CTE counts 1 to 100, and a join to"
            " loans looks each one up. The query in the editor is"
            " correct and makes SQLite scan loans for every number;"
            " write the join condition on the bare loan_id so each"
            " lookup is a rowid search. Your plan must say USING INTEGER"
            " PRIMARY KEY.\n\n"
            "Return: n, member_id"
        ),
        starter_sql=("WITH RECURSIVE nums(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM nums WHERE n < 100)"
                     " SELECT n, l.member_id FROM nums JOIN loans l ON l.loan_id + 0 = nums.n"),
        solution=("WITH RECURSIVE nums(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM nums WHERE n < 100)"
                  " SELECT n, l.member_id FROM nums JOIN loans l ON l.loan_id = nums.n"),
        trap_sql=("WITH RECURSIVE nums(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM nums WHERE n < 100)"
                  " SELECT n, l.member_id FROM nums JOIN loans l ON CAST(l.loan_id AS TEXT) = CAST(nums.n AS TEXT)"),
        note="loan_id is an INTEGER PRIMARY KEY, which in SQLite IS the"
             " rowid, and a lookup by it is the fastest search there is."
             " Arithmetic or a CAST on the column hides that from the"
             " planner, which falls back to scanning -- or, in the"
             " starter's case, building a temporary index on the CTE."
             " The recursion is only the list of numbers to look up.",
        plan_requires=("USING INTEGER PRIMARY KEY",),
        plan_forbids=("AUTOMATIC",),
        claims=[("a hundred loans",
                 lambda rows, c: len(rows) == 100 and {r[0] for r in rows} == set(range(1, 101)))],
    ),
    dict(
        id=8, ledger="Q1004", concept="R1", tier="4 - Recursion and plans",
        title="Fines in bands of a hundred pence",
        prompt=(
            "How many fines fall in each band of 100 pence -- 0 to 99,"
            " 100 to 199, ... 900 to 999, and 1000 on its own at the cap"
            " -- the band's lower edge and the count, every band present."
            " A recursive CTE of lower edges 0, 100, ... 1000, and a"
            " count of fines at or above the edge and BELOW the next.\n\n"
            "Return: band_from, fines"
        ),
        solution=("WITH RECURSIVE b(lo) AS (SELECT 0 UNION ALL SELECT lo + 100 FROM b WHERE lo < 1000)"
                  " SELECT lo, (SELECT COUNT(*) FROM fines f WHERE f.amount_pence >= b.lo AND f.amount_pence < b.lo + 100)"
                  " FROM b"),
        trap_sql=("WITH RECURSIVE b(lo) AS (SELECT 0 UNION ALL SELECT lo + 100 FROM b WHERE lo < 1000)"
                  " SELECT lo, (SELECT COUNT(*) FROM fines f WHERE f.amount_pence >= b.lo AND f.amount_pence <= b.lo + 100)"
                  " FROM b"),
        note="Bands are half-open like weeks: the lower edge is in, the"
             " upper edge belongs to the next band. Fines are multiples"
             " of 20 pence, so hundreds of them sit exactly on an edge,"
             " and with <= each of those is counted in two bands. The"
             " recursion is what gives the empty bands a row -- there"
             " are none here, but there would be a 1100 band if the cap"
             " ever rose.",
        claims=[("eleven bands adding up to every fine, the smallest band the fullest",
                 lambda rows, c: len(rows) == 11 and sum(r[1] for r in rows) == 4085
                 and max(rows, key=lambda r: r[1])[0] == 0)],
    ),
    # ================================================ 5 Aggregates and NULLs
    dict(
        id=9, ledger="Q1005", concept="N1", tier="5 - Aggregates and NULLs",
        title="Members who have never paid a fine",
        prompt=(
            "Members with at least two fines, NONE of them paid: member_id"
            " and the number of fines. COUNT(paid_on) counts the paid"
            " ones -- the non-NULL rule -- so 'none paid' is COUNT(paid_on)"
            " = 0 in the HAVING, beside the count of all.\n\n"
            "Return: member_id, fines"
        ),
        solution=("SELECT l.member_id, COUNT(*) FROM fines f JOIN loans l ON l.loan_id = f.loan_id"
                  " GROUP BY l.member_id HAVING COUNT(f.paid_on) = 0 AND COUNT(*) >= 2"),
        trap_sql=("SELECT l.member_id, COUNT(*) FROM fines f JOIN loans l ON l.loan_id = f.loan_id"
                  " GROUP BY l.member_id HAVING SUM(f.paid_on IS NULL) >= 2"),
        note="'At least two unpaid' is not 'none paid': a member with"
             " three unpaid fines and one paid passes the first test and"
             " fails the second. COUNT(paid_on) = 0 says there is no"
             " payment date anywhere in the group, which is the"
             " NULL-counting rule doing exactly what was asked.",
        claims=[("forty-nine members",
                 lambda rows, c: len(rows) == 49 and all(r[1] >= 2 for r in rows))],
    ),
    dict(
        id=10, ledger="Q1006", concept="N1", tier="5 - Aggregates and NULLs",
        title="How long a hold takes, counting the ones still waiting",
        prompt=(
            "For each branch, the average days from placing a hold to"
            " its fulfilment, to one decimal, over the holds that were"
            " NOT cancelled -- with a hold still waiting counted as"
            " waiting until 2026-06-30. COALESCE(fulfilled_on,"
            " '2026-06-30') inside the julianday, inside the AVG.\n\n"
            "Return: branch_id, avg_days"
        ),
        solution=("SELECT branch_id, ROUND(AVG(julianday(COALESCE(fulfilled_on, '2026-06-30')) - julianday(placed_at)), 1)"
                  " FROM holds WHERE cancelled_on IS NULL GROUP BY branch_id"),
        trap_sql=("SELECT branch_id, ROUND(AVG(julianday(fulfilled_on) - julianday(placed_at)), 1)"
                  " FROM holds WHERE cancelled_on IS NULL GROUP BY branch_id"),
        note="AVG skips NULLs, so without the COALESCE the open holds"
             " drop out of the average and it reports twenty days --"
             " the experience of the lucky ones. Counting the waiting"
             " holds as still waiting at the end of the data gives"
             " seventy, which is the honest figure. The two tools are"
             " the NULL substitute and the aggregate it feeds.",
        claims=[("six branches, all between fifty and a hundred days",
                 lambda rows, c: len(rows) == 6 and all(50 < r[1] < 100 for r in rows))],
    ),
    # ============================================ 6 Set operations and dates
    dict(
        id=11, ledger="Q1007", concept="S1", tier="6 - Set operations and dates",
        title="Sundays with loans but no holds",
        prompt=(
            "The Sundays -- strftime('%w') = '0' -- on which loans"
            " started but no hold was placed: the dates. EXCEPT between"
            " the Sunday loan dates and the hold dates, with date() cut"
            " from placed_at on the holds side.\n\n"
            "Return: day"
        ),
        solution=("SELECT loaned_on FROM loans WHERE strftime('%w', loaned_on) = '0'"
                  " EXCEPT SELECT date(placed_at) FROM holds"),
        trap_sql=("SELECT loaned_on FROM loans WHERE strftime('%w', loaned_on) = '0'"
                  " EXCEPT SELECT placed_at FROM holds"),
        note="EXCEPT compares values exactly, and placed_at carries a"
             " time of day, so without date() no hold ever matches a"
             " loan date and every Sunday survives. The weekday filter"
             " belongs to the first SELECT only -- the holds side is"
             " every hold, whatever day it was placed.",
        claims=[("a handful of Sundays",
                 lambda rows, c: 1 <= len(rows) < 20
                 and all(c.execute("SELECT strftime('%w', ?)", (r[0],)).fetchone()[0] == '0' for r in rows))],
    ),
    dict(
        id=12, ledger="Q1008", concept="S1", tier="6 - Set operations and dates",
        title="Days with both a fine and a fulfilment",
        prompt=(
            "The days on which at least one fine was issued AND at least"
            " one hold was fulfilled: INTERSECT between the two date"
            " columns.\n\n"
            "Return: day"
        ),
        solution="SELECT issued_on FROM fines INTERSECT SELECT fulfilled_on FROM holds",
        trap_sql="SELECT issued_on FROM fines UNION SELECT fulfilled_on FROM holds WHERE fulfilled_on IS NOT NULL",
        note="INTERSECT keeps the dates both columns contain; UNION keeps"
             " the dates either contains, a hundred more. The NULL"
             " fulfilled_on values of the open holds never intersect with"
             " anything, so INTERSECT needs no WHERE to exclude them --"
             " UNION would carry a NULL row without one.",
        claims=[("four hundred or so days",
                 lambda rows, c: 400 < len(rows) < 460)],
    ),
    # ================================================= 7 Changing the data
    dict(
        id=13, ledger="Q1009", concept="TRG", tier="7 - Changing the data",
        kind="script",
        title="Every new hold, logged as JSON",
        prompt=(
            "Create `hold_log (log_id INTEGER PRIMARY KEY, payload TEXT"
            " NOT NULL)` and an AFTER INSERT trigger on holds that writes"
            " one row per new hold whose payload is a JSON object with"
            " keys hold_id, member_id and book_id taken from NEW. The"
            " question then inserts two holds.\n\n"
            "Checked: the member_id and book_id read back from each"
            " payload with json_extract"
        ),
        solution=("CREATE TABLE hold_log (log_id INTEGER PRIMARY KEY, payload TEXT NOT NULL);\n"
                  "CREATE TRIGGER log_hold AFTER INSERT ON holds\n"
                  "BEGIN\n"
                  "  INSERT INTO hold_log (payload)\n"
                  "  VALUES (json_object('hold_id', NEW.hold_id, 'member_id', NEW.member_id, 'book_id', NEW.book_id));\n"
                  "END;"),
        trap_sql=("CREATE TABLE hold_log (log_id INTEGER PRIMARY KEY, payload TEXT NOT NULL);\n"
                  "CREATE TRIGGER log_hold AFTER INSERT ON holds\n"
                  "BEGIN\n"
                  "  INSERT INTO hold_log (payload)\n"
                  "  VALUES (json_array(NEW.hold_id, NEW.member_id, NEW.book_id));\n"
                  "END;"),
        driver_sql=("INSERT INTO holds (book_id, member_id, placed_at, branch_id) VALUES (12, 5, '2026-07-01 09:00', 1);\n"
                    "INSERT INTO holds (book_id, member_id, placed_at, branch_id) VALUES (40, 9, '2026-07-01 09:05', 2);"),
        probe_sql=("SELECT log_id, json_extract(payload, '$.member_id'), json_extract(payload, '$.book_id')"
                   " FROM hold_log ORDER BY log_id"),
        note="A trigger body can call any function, and json_object"
             " turns NEW's columns into a self-describing record -- the"
             " usual shape for an audit log that other systems read."
             " json_array stores the same three numbers without their"
             " names, and json_extract by key finds nothing in it. In an"
             " AFTER INSERT trigger NEW.hold_id already has its value.",
        claims=[("two payloads, members 5 and 9",
                 lambda rows, c: rows == [(1, 5, 12), (2, 9, 40)])],
    ),
    dict(
        id=14, ledger="Q1010", concept="DML", tier="7 - Changing the data",
        kind="script",
        title="Grace by how often a loan was renewed",
        prompt=(
            "Extend the due_on of every loan that is still OUT: by 7"
            " days if it has never been renewed, by 3 days if renewed"
            " once, and not at all if renewed twice. One UPDATE whose"
            " SET uses date() with a CASE on renewals choosing the"
            " modifier -- '+7 days', '+3 days', '+0 days'.\n\n"
            "Checked: the total loan length of the open loans at each"
            " renewal count, and of the returned loans"
        ),
        solution=("UPDATE loans SET due_on = date(due_on,"
                  " CASE renewals WHEN 0 THEN '+7 days' WHEN 1 THEN '+3 days' ELSE '+0 days' END)"
                  " WHERE returned_on IS NULL;"),
        trap_sql=("UPDATE loans SET due_on = date(due_on,"
                  " CASE renewals WHEN 0 THEN '+7 days' WHEN 1 THEN '+3 days' ELSE '+0 days' END);"),
        probe_sql=("SELECT renewals, SUM(julianday(due_on) - julianday(loaned_on)) FROM loans WHERE returned_on IS NULL"
                   " GROUP BY renewals UNION ALL"
                   " SELECT -1, SUM(julianday(due_on) - julianday(loaned_on)) FROM loans WHERE returned_on IS NOT NULL"),
        note="A date modifier is just text, so a CASE can choose it: the"
             " CASE is evaluated per row and date() applies whichever"
             " string it produced. The WHERE on returned_on is the half"
             " that keeps history intact -- without it twenty-three"
             " thousand finished loans get due dates they never had.",
        claims=[("open loans extended by renewal count, returned loans untouched",
                 lambda rows, c: dict(rows)[-1] == 705495.0 and dict(rows)[2] == 5145.0
                 and dict(rows)[0] == 9380.0 and dict(rows)[1] == 9310.0)],
    ),
    dict(
        id=15, ledger="Q1011", concept="VIEW", tier="7 - Changing the data",
        kind="script",
        title="A leaderboard as a view",
        prompt=(
            "Create a view `member_rank (member_id, loans, place)` over"
            " the members who have borrowed: each member's loan count and"
            " their place by that count, 1 for the most, with ties"
            " sharing a place and no numbers skipped -- DENSE_RANK over"
            " a GROUP BY.\n\n"
            "Checked: how many members are in the top three places, and"
            " the fewest loans among them"
        ),
        solution=("CREATE VIEW member_rank AS\n"
                  "  SELECT member_id, COUNT(*) AS loans, DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) AS place\n"
                  "  FROM loans GROUP BY member_id;"),
        trap_sql=("CREATE VIEW member_rank AS\n"
                  "  SELECT member_id, COUNT(*) AS loans, ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) AS place\n"
                  "  FROM loans GROUP BY member_id;"),
        probe_sql="SELECT COUNT(*), MIN(loans) FROM member_rank WHERE place <= 3",
        note="A view can hold a window function over a grouped query,"
             " and DENSE_RANK is the ranking that treats a tie as a"
             " shared place and carries on at the next number. Two"
             " members tie in the top three, so DENSE_RANK puts four"
             " members there; ROW_NUMBER breaks the tie arbitrarily and"
             " shows three.",
        claims=[("four members in the top three places",
                 lambda rows, c: rows[0][0] == 4 and rows[0][1] > 200)],
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
