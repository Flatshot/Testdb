"""Practice exercises: fifteen questions on the library schema.

The twelfth set on the library (SEED 861), the fourth at two tools per
question. CASE and intervals -- open loans split by a CASE on due_on, and
returned loans banded by a CASE on their length. Bare columns and dates --
MAX's row with a strftime label beside it, twice. Windows and JSON -- a
running total packed into a JSON array per year, and LAG inside
json_object inside json_group_array. Text, plans and ranks -- a LIKE that
the NOCASE index can search, graded on the plan; and printf over a
ROW_NUMBER. HAVING and subqueries -- recursive thresholds against a
HAVING, and a HAVING against a scalar subquery. Set operations and windows
-- a top decile by NTILE minus the debtors, and two ranked lists stacked by
UNION ALL. And three WRITABLE questions in two steps each:

  * a BEFORE INSERT trigger whose WHEN is a string test
  * ALTER TABLE ADD COLUMN, then an UPDATE from a CTE with NTILE
  * a DELETE whose WHERE reads a JSON list with json_each

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
    # ================================================== 1 CASE and intervals
    dict(
        id=1, ledger="Q1012", concept="INT", tier="1 - CASE and intervals",
        title="Open loans: overdue or not yet due, per branch",
        prompt=(
            "For each branch, two counts over the loans of its copies"
            " that are still OUT on 2026-06-30: those already past their"
            " due_on, and those not yet due. A conditional SUM, or SUM"
            " over a CASE, on due_on -- with the WHERE that keeps the"
            " returned loans out.\n\n"
            "Return: branch_id, overdue, not_yet_due"
        ),
        solution=("SELECT c.branch_id, SUM(l.due_on < '2026-06-30'), SUM(l.due_on >= '2026-06-30')"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " WHERE l.returned_on IS NULL GROUP BY c.branch_id"),
        trap_sql=("SELECT c.branch_id, SUM(l.due_on < '2026-06-30'), SUM(l.due_on >= '2026-06-30')"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id GROUP BY c.branch_id"),
        note="The CASE -- here a bare comparison summed -- splits the"
             " open loans two ways, but it is the WHERE on returned_on"
             " that decides which loans are being split. Without it"
             " every returned loan whose due date has passed counts as"
             " overdue: thousands per branch instead of twenty.",
        claims=[("six branches, a hundred or so open loans each",
                 lambda rows, c: len(rows) == 6 and sum(r[1] + r[2] for r in rows) == 685
                 and all(r[2] > r[1] for r in rows))],
    ),
    dict(
        id=2, ledger="Q1013", concept="C7", tier="1 - CASE and intervals",
        title="How long loans last",
        prompt=(
            "Returned loans banded by length in days -- julianday("
            "returned_on) - julianday(loaned_on) -- as 'under a week'"
            " (less than 7), 'one to three weeks' (7 up to and including"
            " 21) and 'over three weeks', with the count of each. The"
            " CASE's WHENs test the narrowest band first.\n\n"
            "Return: band, loans"
        ),
        solution=("SELECT CASE WHEN julianday(returned_on) - julianday(loaned_on) < 7 THEN 'under a week'"
                  " WHEN julianday(returned_on) - julianday(loaned_on) <= 21 THEN 'one to three weeks'"
                  " ELSE 'over three weeks' END, COUNT(*) FROM loans WHERE returned_on IS NOT NULL GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN julianday(returned_on) - julianday(loaned_on) <= 21 THEN 'one to three weeks'"
                  " WHEN julianday(returned_on) - julianday(loaned_on) < 7 THEN 'under a week'"
                  " ELSE 'over three weeks' END, COUNT(*) FROM loans WHERE returned_on IS NOT NULL GROUP BY 1"),
        note="The interval's length is a julianday difference, and the"
             " CASE bands it. With <= 21 tested first, every short loan"
             " is already 'one to three weeks' before the under-a-week"
             " test is reached, and that band is empty. The WHERE keeps"
             " open loans out, whose length would be NULL and would fall"
             " into the ELSE.",
        claims=[("three bands, the middle one the largest",
                 lambda rows, c: len(rows) == 3 and sum(r[1] for r in rows) == 23291
                 and max(rows, key=lambda r: r[1])[0] == 'one to three weeks')],
    ),
    # ============================================== 2 Bare columns and dates
    dict(
        id=3, ledger="Q1014", concept="BARE", tier="2 - Bare columns and dates",
        title="Each branch's newest copy, and the month it came",
        prompt=(
            "For each branch: the copy_id of its most recently acquired"
            " copy and the month of that acquisition as 'YYYY-MM'."
            " MAX(acquired_on) with copy_id as a bare column, and"
            " strftime on the MAX for the label.\n\n"
            "Return: branch_id, copy_id, acquired_month"
        ),
        solution=("SELECT branch_id, copy_id, strftime('%Y-%m', MAX(acquired_on)) FROM copies GROUP BY branch_id"),
        trap_sql=("SELECT branch_id, copy_id, strftime('%Y-%m', MIN(acquired_on)) FROM copies GROUP BY branch_id"),
        note="strftime can wrap the aggregate itself, because MAX returns"
             " one date per group. The bare copy_id comes from the row"
             " that date was found in -- the newest copy -- by SQLite's"
             " rule for a single MIN or MAX. MIN gives the oldest copy"
             " and the branch's first month of stock.",
        claims=[("six branches, every newest copy in 2024",
                 lambda rows, c: len(rows) == 6 and all(r[2].startswith('2024') for r in rows)
                 and all(c.execute("SELECT acquired_on FROM copies WHERE copy_id = ?", (r[1],)).fetchone()[0]
                         == c.execute("SELECT MAX(acquired_on) FROM copies WHERE branch_id = ?", (r[0],)).fetchone()[0]
                         for r in rows))],
    ),
    dict(
        id=4, ledger="Q1015", concept="BARE", tier="2 - Bare columns and dates",
        title="The last copy each branch withdrew, and the weekday",
        prompt=(
            "For each branch: the copy it withdrew most recently and"
            " the day of the week of that withdrawal as strftime's %w."
            " MAX(withdrawn_on) over the withdrawn copies, copy_id as a"
            " bare column, strftime on the MAX.\n\n"
            "Return: branch_id, copy_id, weekday"
        ),
        solution=("SELECT branch_id, copy_id, strftime('%w', MAX(withdrawn_on)) FROM copies"
                  " WHERE withdrawn_on IS NOT NULL GROUP BY branch_id"),
        trap_sql=("SELECT branch_id, copy_id, strftime('%w', MIN(withdrawn_on)) FROM copies"
                  " WHERE withdrawn_on IS NOT NULL GROUP BY branch_id"),
        note="MAX ignores NULLs on its own, so the WHERE is not strictly"
             " needed for the date -- but it keeps the bare column"
             " honest, since without it a branch with no withdrawals at"
             " all would still get a row with some arbitrary copy. MIN"
             " is the first withdrawal; the question asks for the last.",
        claims=[("six branches, each copy really the latest withdrawn",
                 lambda rows, c: len(rows) == 6
                 and all(c.execute("SELECT withdrawn_on FROM copies WHERE copy_id = ?", (r[1],)).fetchone()[0]
                         == c.execute("SELECT MAX(withdrawn_on) FROM copies WHERE branch_id = ?", (r[0],)).fetchone()[0]
                         for r in rows))],
    ),
    # ==================================================== 3 Windows and JSON
    dict(
        id=5, ledger="Q1016", concept="W1", tier="3 - Windows and JSON",
        title="Each year's running total, as a JSON array",
        prompt=(
            "For each year, a JSON array of the cumulative loan count"
            " month by month -- January's loans, then January plus"
            " February, and so on. A CTE of loans per month with the"
            " year, a running SUM OVER (PARTITION BY year ORDER BY"
            " month), then json_group_array of that ordered by month,"
            " grouped by year.\n\n"
            "Return: year, cumulative"
        ),
        solution=("WITH m AS (SELECT strftime('%Y', loaned_on) AS y, strftime('%Y-%m', loaned_on) AS ym, COUNT(*) AS n"
                  " FROM loans GROUP BY ym),"
                  " r AS (SELECT y, ym, SUM(n) OVER (PARTITION BY y ORDER BY ym) AS cum FROM m)"
                  " SELECT y, json_group_array(cum ORDER BY ym) FROM r GROUP BY y"),
        trap_sql=("WITH m AS (SELECT strftime('%Y', loaned_on) AS y, strftime('%Y-%m', loaned_on) AS ym, COUNT(*) AS n"
                  " FROM loans GROUP BY ym),"
                  " r AS (SELECT y, ym, SUM(n) OVER (PARTITION BY y) AS cum FROM m)"
                  " SELECT y, json_group_array(cum ORDER BY ym) FROM r GROUP BY y"),
        note="Three layers: group to months, run a window over the"
             " months, pack the windowed rows into JSON. The window's"
             " ORDER BY is what makes the SUM cumulative; without it the"
             " frame is the whole year and every element is the year's"
             " total. The array's own ORDER BY keeps the months in"
             " sequence inside the JSON.",
        claims=[("two years, each array climbing to the year's total",
                 lambda rows, c: len(rows) == 2
                 and all(__import__('json').loads(r[1]) == sorted(__import__('json').loads(r[1])) for r in rows)
                 and sum(__import__('json').loads(r[1])[-1] for r in rows) == 23976)],
    ),
    dict(
        id=6, ledger="Q1017", concept="W3", tier="3 - Windows and JSON",
        title="Two members' loan timelines, as JSON",
        prompt=(
            "For members 834 and 422: one JSON array each of their loans"
            " in date order, each loan a JSON object with keys loan_id,"
            " loaned_on and gap -- the whole days since that member's"
            " previous loan, 0 for the first. LAG partitioned by member"
            " in a CTE, COALESCE for the first row, then json_group_array"
            " of json_object ordered by loaned_on.\n\n"
            "Return: member_id, timeline"
        ),
        solution=("WITH g AS (SELECT member_id, loan_id, loaned_on,"
                  " COALESCE(CAST(julianday(loaned_on) - julianday(LAG(loaned_on) OVER"
                  " (PARTITION BY member_id ORDER BY loaned_on)) AS INTEGER), 0) AS gap"
                  " FROM loans WHERE member_id IN (834, 422))"
                  " SELECT member_id, json_group_array(json_object('loan_id', loan_id, 'loaned_on', loaned_on, 'gap', gap)"
                  " ORDER BY loaned_on) FROM g GROUP BY member_id"),
        trap_sql=("WITH g AS (SELECT member_id, loan_id, loaned_on,"
                  " COALESCE(CAST(julianday(loaned_on) - julianday(LAG(loaned_on) OVER"
                  " (ORDER BY loaned_on)) AS INTEGER), 0) AS gap"
                  " FROM loans WHERE member_id IN (834, 422))"
                  " SELECT member_id, json_group_array(json_object('loan_id', loan_id, 'loaned_on', loaned_on, 'gap', gap)"
                  " ORDER BY loaned_on) FROM g GROUP BY member_id"),
        note="With two members in the CTE the window needs PARTITION BY"
             " member_id, or LAG reaches back into the OTHER member's"
             " loans and the gaps are measured between strangers. The"
             " JSON step is the same as before: json_object builds each"
             " element, json_group_array collects them in the order its"
             " ORDER BY says.",
        claims=[("two timelines, each starting with a gap of 0",
                 lambda rows, c: len(rows) == 2
                 and all(__import__('json').loads(r[1])[0]['gap'] == 0 for r in rows)
                 and all(all(o['gap'] >= 0 for o in __import__('json').loads(r[1])) for r in rows))],
    ),
    # ============================================= 4 Text, plans and ranks
    dict(
        id=7, ledger="Q1018", concept="X5", tier="4 - Text, plans and ranks",
        title="Titles beginning 'The', through the index",
        prompt=(
            "Every book whose title begins 'The ': book_id and title."
            " The query in the editor is correct and scans, because it"
            " wraps title in a function. idx_books_title is a NOCASE"
            " index, and SQLite can turn a LIKE with no leading wildcard"
            " on such a column into a range search on it: write the"
            " condition as a LIKE on the bare column. Your plan must say"
            " SEARCH, not SCAN.\n\n"
            "Return: book_id, title"
        ),
        starter_sql="SELECT book_id, title FROM books WHERE SUBSTR(title, 1, 4) = 'The '",
        solution="SELECT book_id, title FROM books WHERE title LIKE 'The %'",
        trap_sql="SELECT book_id, title FROM books WHERE LOWER(title) LIKE 'the %'",
        note="LIKE 'prefix%' is the one pattern SQLite can optimise: it"
             " becomes title >= 'The ' AND title < 'The!' and the index"
             " is searched for that range -- provided the index's"
             " collation is compatible with LIKE's case-folding, which"
             " NOCASE is. Any function around the column, SUBSTR or"
             " LOWER, takes that away and the whole table is read.",
        plan_requires=("SEARCH books USING COVERING INDEX idx_books_title",),
        plan_forbids=("SCAN",),
        claims=[("a hundred and seventy-two titles",
                 lambda rows, c: len(rows) == 172 and all(r[1].startswith('The ') for r in rows))],
    ),
    dict(
        id=8, ledger="Q1019", concept="W2", tier="4 - Text, plans and ranks",
        title="Badges for the ten keenest readers",
        prompt=(
            "The ten members with the most loans, ties by lower"
            " member_id: member_id, loans, and a badge like '#001' --"
            " a hash and the rank zero-padded to three digits by printf."
            " ROW_NUMBER over the grouped counts, filtered to 10 in an"
            " outer query.\n\n"
            "Return: member_id, loans, badge"
        ),
        solution=("SELECT member_id, n, printf('#%03d', rn) FROM ("
                  "SELECT member_id, COUNT(*) AS n, ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC, member_id) AS rn"
                  " FROM loans GROUP BY member_id) WHERE rn <= 10"),
        trap_sql=("SELECT member_id, n, printf('#%3d', rn) FROM ("
                  "SELECT member_id, COUNT(*) AS n, ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC, member_id) AS rn"
                  " FROM loans GROUP BY member_id) WHERE rn <= 10"),
        note="The window numbers every member; the outer WHERE keeps ten;"
             " printf turns the number into text. %03d pads with zeros,"
             " %3d with spaces -- '#  1' is three characters wide too,"
             " but it is not the badge asked for. The tie-break in the"
             " window's ORDER BY is what makes tenth place well defined.",
        claims=[("ten readers, badges #001 to #010",
                 lambda rows, c: len(rows) == 10 and {r[2] for r in rows} == {f'#{i:03d}' for i in range(1, 11)}
                 and max(r[1] for r in rows) == 237)],
    ),
    # ================================================ 5 HAVING and subqueries
    dict(
        id=9, ledger="Q1020", concept="A3", tier="5 - HAVING and subqueries",
        title="How many members clear each threshold",
        prompt=(
            "For each threshold 5, 10, 15, 20 and 25: how many members"
            " have AT LEAST that many loans. A recursive CTE of the"
            " thresholds, and per threshold a count of the members whose"
            " grouped loan count reaches it -- a HAVING inside a"
            " correlated subquery.\n\n"
            "Return: threshold, members"
        ),
        solution=("WITH RECURSIVE t(n) AS (SELECT 5 UNION ALL SELECT n + 5 FROM t WHERE n < 25)"
                  " SELECT n, (SELECT COUNT(*) FROM (SELECT member_id FROM loans GROUP BY member_id HAVING COUNT(*) >= t.n))"
                  " FROM t"),
        trap_sql=("WITH RECURSIVE t(n) AS (SELECT 5 UNION ALL SELECT n + 5 FROM t WHERE n < 25)"
                  " SELECT n, (SELECT COUNT(*) FROM (SELECT member_id FROM loans GROUP BY member_id HAVING COUNT(*) > t.n))"
                  " FROM t"),
        note="A HAVING can refer to a value from an outer query, which"
             " makes one grouped query answer five different questions."
             " 'At least' is >=; with > the members sitting exactly on a"
             " threshold are dropped, and there are a hundred and"
             " thirty-seven of them on 15 alone.",
        claims=[("five thresholds, falling from thirteen hundred to forty",
                 lambda rows, c: [r[1] for r in sorted(rows)] == [1295, 1153, 575, 114, 40])],
    ),
    dict(
        id=10, ledger="Q1021", concept="A3", tier="5 - HAVING and subqueries",
        title="Branches later than the service as a whole",
        prompt=(
            "Branches whose copies come back late more often than the"
            " service-wide rate: branch_id and the branch's late rate to"
            " four decimals. The rate is AVG(returned_on > due_on), and"
            " the HAVING compares it with the same AVG over all loans"
            " as a scalar subquery. Keep the arithmetic floating-point.\n\n"
            "Return: branch_id, late_rate"
        ),
        solution=("SELECT c.branch_id, ROUND(AVG(l.returned_on > l.due_on), 4)"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id GROUP BY c.branch_id"
                  " HAVING AVG(l.returned_on > l.due_on) > (SELECT AVG(returned_on > due_on) FROM loans)"),
        trap_sql=("SELECT c.branch_id, ROUND(AVG(l.returned_on > l.due_on), 4)"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id GROUP BY c.branch_id"
                  " HAVING SUM(l.returned_on > l.due_on) / COUNT(*) > (SELECT AVG(returned_on > due_on) FROM loans)"),
        note="AVG of a comparison is the fraction of true rows, and AVG"
             " skips the NULLs the open loans produce -- so it is the"
             " late rate among returned loans without any extra WHERE."
             " SUM over COUNT is the same rate done in integers: 700 /"
             " 4000 is 0, which is never above anything, and no branch"
             " qualifies.",
        claims=[("two branches, Hilltop and Eastfield",
                 lambda rows, c: {r[0] for r in rows} == {4, 5} and all(r[1] > 0.175 for r in rows))],
    ),
    # ========================================== 6 Set operations and windows
    dict(
        id=11, ledger="Q1022", concept="S1", tier="6 - Set operations and windows",
        title="The top decile with a clean slate",
        prompt=(
            "Members in the top tenth of borrowers by loan count who owe"
            " NO unpaid fine. NTILE(10) over per-member counts in a CTE,"
            " tile 10 being the heaviest, EXCEPT the members with an"
            " unpaid fine.\n\n"
            "Return: member_id"
        ),
        solution=("WITH per AS (SELECT member_id, COUNT(*) AS n FROM loans GROUP BY member_id),"
                  " t AS (SELECT member_id, NTILE(10) OVER (ORDER BY n) AS d FROM per)"
                  " SELECT member_id FROM t WHERE d = 10"
                  " EXCEPT SELECT l.member_id FROM fines f JOIN loans l ON l.loan_id = f.loan_id WHERE f.paid_on IS NULL"),
        trap_sql=("WITH per AS (SELECT member_id, COUNT(*) AS n FROM loans GROUP BY member_id),"
                  " t AS (SELECT member_id, NTILE(10) OVER (ORDER BY n) AS d FROM per)"
                  " SELECT member_id FROM t WHERE d = 10"
                  " INTERSECT SELECT l.member_id FROM fines f JOIN loans l ON l.loan_id = f.loan_id WHERE f.paid_on IS NULL"),
        note="A CTE can feed a set operation: the first SELECT reads the"
             " tiled members, the second the debtors, and EXCEPT keeps"
             " the heavy readers who are not debtors. INTERSECT keeps the"
             " heavy readers who ARE -- and heavy readers are mostly"
             " debtors, so the two answers are very different sizes.",
        claims=[("nineteen clean heavy readers",
                 lambda rows, c: len(rows) == 19)],
    ),
    dict(
        id=12, ledger="Q1023", concept="W2", tier="6 - Set operations and windows",
        title="The three most and the three least borrowed",
        prompt=(
            "The three books with the most loans and the three with the"
            " fewest, among books that have been loaned at all, as six"
            " rows labelled 'top' and 'bottom': two ranked queries over"
            " a CTE of loans per book -- ROW_NUMBER descending with"
            " book_id as tie-break, and ascending likewise -- stacked"
            " with UNION ALL.\n\n"
            "Return: label, book_id, loans"
        ),
        solution=("WITH n AS (SELECT c.book_id, COUNT(*) AS k FROM loans l JOIN copies c ON c.copy_id = l.copy_id GROUP BY c.book_id)"
                  " SELECT 'top', book_id, k FROM (SELECT book_id, k, ROW_NUMBER() OVER (ORDER BY k DESC, book_id) AS rn FROM n) WHERE rn <= 3"
                  " UNION ALL"
                  " SELECT 'bottom', book_id, k FROM (SELECT book_id, k, ROW_NUMBER() OVER (ORDER BY k, book_id) AS rn FROM n) WHERE rn <= 3"),
        trap_sql=("WITH n AS (SELECT c.book_id, COUNT(*) AS k FROM loans l JOIN copies c ON c.copy_id = l.copy_id GROUP BY c.book_id)"
                  " SELECT 'top', book_id, k FROM (SELECT book_id, k, ROW_NUMBER() OVER (ORDER BY k DESC, book_id) AS rn FROM n) WHERE rn <= 3"
                  " UNION ALL"
                  " SELECT 'bottom', book_id, k FROM (SELECT book_id, k, ROW_NUMBER() OVER (ORDER BY k DESC, book_id) AS rn FROM n) WHERE rn <= 3"),
        note="One CTE, two windows ordered opposite ways, one UNION ALL:"
             " the label column tells the halves apart. The second window"
             " has to be ascending, or 'bottom' is a copy of 'top'. Both"
             " need the book_id tie-break, since several books share the"
             " extreme counts.",
        claims=[("three top around a hundred loans, three bottom under ten",
                 lambda rows, c: len(rows) == 6
                 and all(r[2] >= 100 for r in rows if r[0] == 'top')
                 and all(r[2] <= 10 for r in rows if r[0] == 'bottom'))],
    ),
    # ================================================= 7 Changing the data
    dict(
        id=13, ledger="Q1024", concept="TRG", tier="7 - Changing the data",
        kind="script",
        title="Members need a surname",
        prompt=(
            "Write a BEFORE INSERT trigger on members that refuses --"
            " RAISE(ABORT, ...) -- a name with no space in it, since the"
            " surname questions all split on the space: INSTR(NEW.name,"
            " ' ') = 0 is the test. The question then inserts 'Cher' and"
            " 'Ada Lovelace', both at branch 1.\n\n"
            "Checked: the names of any members added"
        ),
        solution=("CREATE TRIGGER need_surname BEFORE INSERT ON members\n"
                  "WHEN INSTR(NEW.name, ' ') = 0\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'name needs a surname');\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER need_surname BEFORE INSERT ON members\n"
                  "WHEN INSTR(NEW.name, ' ') = 1\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'name needs a surname');\n"
                  "END;"),
        driver_sql=("INSERT INTO members (name, born_on, joined_on, home_branch_id) VALUES ('Cher', '1990-05-20', '2026-07-01', 1);\n"
                    "INSERT INTO members (name, born_on, joined_on, home_branch_id) VALUES ('Ada Lovelace', '1990-05-20', '2026-07-01', 1);"),
        probe_sql="SELECT name FROM members WHERE member_id > 1500 ORDER BY member_id",
        note="A trigger's WHEN can be any expression over NEW, including"
             " a string function: INSTR returns 0 when the space is"
             " absent, which is the condition to refuse. INSTR = 1 would"
             " refuse only names that START with a space, and 'Cher'"
             " walks in. A CHECK constraint on the column would say the"
             " same, but cannot be added to an existing table.",
        claims=[("only Ada Lovelace",
                 lambda rows, c: rows == [('Ada Lovelace',)])],
    ),
    dict(
        id=14, ledger="Q1025", concept="DDL", tier="7 - Changing the data",
        kind="script",
        title="Reader tiers",
        prompt=(
            "Add a column `tier TEXT` to members, then set it for every"
            " member who has borrowed: 'gold' for the quarter with the"
            " most loans, then 'silver', 'bronze' and 'basic'. A CTE of"
            " loans per member with NTILE(4) ordered by loans DESCENDING,"
            " and an UPDATE that reads the tile through a CASE. Members"
            " who never borrowed stay NULL.\n\n"
            "Checked: how many members hold each tier, NULL included"
        ),
        solution=("ALTER TABLE members ADD COLUMN tier TEXT;\n"
                  "WITH per AS (SELECT member_id, COUNT(*) AS n FROM loans GROUP BY member_id),\n"
                  "     t AS (SELECT member_id, NTILE(4) OVER (ORDER BY n DESC) AS q FROM per)\n"
                  "UPDATE members SET tier = (SELECT CASE q WHEN 1 THEN 'gold' WHEN 2 THEN 'silver'\n"
                  "                                  WHEN 3 THEN 'bronze' ELSE 'basic' END\n"
                  "                           FROM t WHERE t.member_id = members.member_id)\n"
                  "WHERE member_id IN (SELECT member_id FROM t);"),
        trap_sql=("ALTER TABLE members ADD COLUMN tier TEXT;\n"
                  "WITH per AS (SELECT member_id, COUNT(*) AS n FROM loans GROUP BY member_id),\n"
                  "     t AS (SELECT member_id, NTILE(4) OVER (ORDER BY n) AS q FROM per)\n"
                  "UPDATE members SET tier = (SELECT CASE q WHEN 1 THEN 'gold' WHEN 2 THEN 'silver'\n"
                  "                                  WHEN 3 THEN 'bronze' ELSE 'basic' END\n"
                  "                           FROM t WHERE t.member_id = members.member_id)\n"
                  "WHERE member_id IN (SELECT member_id FROM t);"),
        probe_sql=("SELECT tier, COUNT(*), MIN(m.member_id) FROM members m GROUP BY tier ORDER BY tier"),
        note="A WITH clause can introduce an UPDATE, and the window"
             " function lives in the CTE. NTILE(4) ORDER BY n DESC puts"
             " the heaviest quarter in tile 1, which the CASE names"
             " gold; ascending order hands gold to the lightest readers."
             " The final WHERE limits the UPDATE to borrowers, so the two"
             " hundred who never borrowed keep a NULL tier.",
        claims=[("four tiers of 325 and 200 NULLs, member 97 gold",
                 lambda rows, c: dict((r[0], r[1]) for r in rows) == {None: 200, 'basic': 325, 'bronze': 325, 'gold': 325, 'silver': 325}
                 and c.execute("SELECT tier FROM members WHERE member_id = 97").fetchone()[0] == 'gold')],
    ),
    dict(
        id=15, ledger="Q1026", concept="DML", tier="7 - Changing the data",
        kind="script",
        title="Cancel the queues for two withdrawn titles",
        prompt=(
            "Books 587 and 275 are being withdrawn: delete every OPEN"
            " hold on them -- fulfilled_on and cancelled_on both NULL --"
            " leaving their closed holds as history. Take the two ids"
            " from the JSON list '[587, 275]' with json_each inside the"
            " DELETE's WHERE.\n\n"
            "Checked: how many holds remain for those two books, and how"
            " many of them are open"
        ),
        solution=("DELETE FROM holds WHERE fulfilled_on IS NULL AND cancelled_on IS NULL"
                  " AND book_id IN (SELECT value FROM json_each('[587, 275]'));"),
        trap_sql=("DELETE FROM holds WHERE book_id IN (SELECT value FROM json_each('[587, 275]'));"),
        probe_sql=("SELECT COUNT(*), SUM(fulfilled_on IS NULL AND cancelled_on IS NULL) FROM holds"
                   " WHERE book_id IN (587, 275)"),
        note="json_each in a subquery turns a JSON list into the IN"
             " list a DELETE can use, which is how a list handed in from"
             " outside reaches SQL without string-building. The open"
             " test is the half that keeps history: without it the"
             " books' twenty fulfilled and cancelled holds go too.",
        claims=[("twenty closed holds kept, none open",
                 lambda rows, c: rows == [(20, 0)])],
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
