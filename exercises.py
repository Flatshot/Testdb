"""Practice exercises: fifteen questions on the library schema.

The ninth set on the library (SEED 861), and a step UP: every question
combines TWO tools the earlier sets taught separately. Windows over CTEs
-- a rank within the year over monthly counts, quartiles of borrowers by
NTILE, the biggest day-on-day jump by LAG and a LIMIT. EXISTS, CASE and
HAVING -- a conditional SUM whose condition is an EXISTS, a CASE whose
branches are EXISTS tests in the right order, and two HAVING conditions
one of which is a SUM over a comparison. Recursion meets intervals -- a
calendar of months and one of days, each joined to an interval test with
the open end supplied. JSON in aggregates -- json_object inside
json_group_array over a grouped CTE, and a ranked CTE packed into a JSON
array. Text with aggregation -- GROUP_CONCAT DISTINCT over a SUBSTR, and
a HAVING over an extracted surname. And three WRITABLE questions, each
two steps:

  * a BEFORE INSERT trigger whose WHEN is an interval test
  * a CTE with ROW_NUMBER feeding an UPDATE
  * a view and the INSTEAD OF trigger that makes it updatable

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script -- the rows your trigger should
sort.
"""

import sqlite3

EXERCISES = [
    # =================================================== 1 Windows over CTEs
    dict(
        id=1, ledger="Q967", concept="W2", tier="1 - Windows over CTEs",
        title="Each month's rank within its year",
        prompt=(
            "For each month of the data: its loans, and its rank within"
            " ITS YEAR by loans, 1 for the year's busiest month. A CTE of"
            " loans per month that also carries the year, then DENSE_RANK"
            " partitioned by that year.\n\n"
            "Return: month, loans, rank_in_year"
        ),
        solution=("WITH m AS (SELECT strftime('%Y', loaned_on) AS y, strftime('%Y-%m', loaned_on) AS ym, COUNT(*) AS n"
                  " FROM loans GROUP BY ym)"
                  " SELECT ym, n, DENSE_RANK() OVER (PARTITION BY y ORDER BY n DESC) FROM m"),
        trap_sql=("WITH m AS (SELECT strftime('%Y', loaned_on) AS y, strftime('%Y-%m', loaned_on) AS ym, COUNT(*) AS n"
                  " FROM loans GROUP BY ym)"
                  " SELECT ym, n, DENSE_RANK() OVER (ORDER BY n DESC) FROM m"),
        note="The CTE does the grouping and keeps the year as a column;"
             " the window ranks the grouped rows, and PARTITION BY y is"
             " what makes the ranking restart each year. Without it the"
             " eighteen months are ranked together and 2026 has no month"
             " ranked 1.",
        claims=[("eighteen months, two ranked first",
                 lambda rows, c: len(rows) == 18 and sum(r[2] == 1 for r in rows) == 2)],
    ),
    dict(
        id=2, ledger="Q968", concept="W2", tier="1 - Windows over CTEs",
        title="Borrowers in quartiles",
        prompt=(
            "Split the borrowers -- members with at least one loan --"
            " into four equal groups by loan count, quartile 1 the"
            " LIGHTEST readers: for each quartile, the loans its members"
            " made in all, and the smallest and largest loan count in it."
            " A CTE of loans"
            " per member, NTILE(4) over it, then a GROUP BY the tile.\n\n"
            "Return: quartile, loans, min_loans, max_loans"
        ),
        solution=("WITH per AS (SELECT member_id, COUNT(*) AS n FROM loans GROUP BY member_id),"
                  " t AS (SELECT n, NTILE(4) OVER (ORDER BY n) AS q FROM per)"
                  " SELECT q, SUM(n), MIN(n), MAX(n) FROM t GROUP BY q"),
        trap_sql=("WITH per AS (SELECT member_id, COUNT(*) AS n FROM loans GROUP BY member_id),"
                  " t AS (SELECT n, NTILE(4) OVER (ORDER BY n DESC) AS q FROM per)"
                  " SELECT q, SUM(n), MIN(n), MAX(n) FROM t GROUP BY q"),
        note="NTILE(4) numbers the rows 1 to 4 in equal-sized bands in"
             " the window's order, so ORDER BY n ascending puts the"
             " lightest readers in tile 1; DESC reverses the tiles. The"
             " third step groups by the tile number, which only exists"
             " once the window has run -- hence the second CTE. Each tile"
             " holds 325 members, so the loan totals are what show how"
             " lopsided reading is.",
        claims=[("four tiles, the top one holding most of the loans",
                 lambda rows, c: len(rows) == 4 and sum(r[1] for r in rows) == 23976
                 and dict((r[0], r[3]) for r in rows)[4] > 200
                 and dict((r[0], r[2]) for r in rows)[1] < 5)],
    ),
    dict(
        id=3, ledger="Q969", concept="W3", tier="1 - Windows over CTEs",
        title="The biggest jump in a day",
        prompt=(
            "The 2026 day whose loan count rose most over the previous"
            " day: the day, its loans and the rise. A CTE of loans per"
            " day over ALL the data, a second with LAG for the change,"
            " then the largest change among 2026's days -- ORDER BY and"
            " LIMIT 1, ties to the earlier day.\n\n"
            "Return: day, loans, rise"
        ),
        solution=("WITH d AS (SELECT loaned_on, COUNT(*) AS n FROM loans GROUP BY loaned_on),"
                  " ch AS (SELECT loaned_on, n, n - LAG(n) OVER (ORDER BY loaned_on) AS c FROM d)"
                  " SELECT loaned_on, n, c FROM ch WHERE loaned_on >= '2026-01-01' ORDER BY c DESC, loaned_on LIMIT 1"),
        trap_sql=("WITH d AS (SELECT loaned_on, COUNT(*) AS n FROM loans GROUP BY loaned_on),"
                  " ch AS (SELECT loaned_on, n, n - LEAD(n) OVER (ORDER BY loaned_on) AS c FROM d)"
                  " SELECT loaned_on, n, c FROM ch WHERE loaned_on >= '2026-01-01' ORDER BY c DESC, loaned_on LIMIT 1"),
        note="LAG looks at the day before, which is what 'rose over the"
             " previous day' means; LEAD looks at the day after and"
             " finds the biggest FALL instead, labelled as a rise. The"
             " year filter goes in the final SELECT, not the CTEs: 1"
             " January needs 31 December to compare with.",
        claims=[("20 June 2026, up by 25",
                 lambda rows, c: rows == [('2026-06-20', 59, 25)])],
    ),
    # ============================================ 2 EXISTS, CASE and HAVING
    dict(
        id=4, ledger="Q970", concept="E1", tier="2 - EXISTS, CASE and HAVING",
        title="Copies that have never gone out",
        prompt=(
            "For each branch: its copies, how many of them have been"
            " loaned at least once, and how many never. The 'at least"
            " once' is an EXISTS per copy, summed -- a loan join would"
            " count loans, not copies.\n\n"
            "Return: branch_id, copies, loaned_ever, never"
        ),
        solution=("SELECT c.branch_id, COUNT(*),"
                  " SUM(EXISTS (SELECT 1 FROM loans l WHERE l.copy_id = c.copy_id)),"
                  " SUM(NOT EXISTS (SELECT 1 FROM loans l WHERE l.copy_id = c.copy_id))"
                  " FROM copies c GROUP BY c.branch_id"),
        trap_sql=("SELECT c.branch_id, COUNT(DISTINCT c.copy_id), COUNT(l.loan_id),"
                  " COUNT(DISTINCT c.copy_id) - COUNT(l.loan_id)"
                  " FROM copies c LEFT JOIN loans l ON l.copy_id = c.copy_id GROUP BY c.branch_id"),
        note="EXISTS is a boolean, 1 or 0, and SUM of it over the copies"
             " counts the copies for which it is true -- a conditional"
             " count whose condition is a subquery. The join version"
             " counts rows of the join, which is loans, so 'loaned ever'"
             " comes out in the thousands and 'never' goes negative.",
        claims=[("six branches, about a hundred never-loaned copies in all",
                 lambda rows, c: len(rows) == 6
                 and all(r[2] + r[3] == r[1] for r in rows)
                 and 100 <= sum(r[3] for r in rows) <= 120)],
    ),
    dict(
        id=5, ledger="Q971", concept="C7", tier="2 - EXISTS, CASE and HAVING",
        title="Debtor, borrower or lapsed",
        prompt=(
            "Put every member in one class and count each: 'debtor' if"
            " they have an UNPAID fine; otherwise 'borrower' if they have"
            " any loan; otherwise 'lapsed'. A CASE whose WHENs are EXISTS"
            " tests, in that order.\n\n"
            "Return: class, members"
        ),
        solution=("SELECT CASE WHEN EXISTS (SELECT 1 FROM fines f JOIN loans l ON l.loan_id = f.loan_id"
                  " WHERE l.member_id = m.member_id AND f.paid_on IS NULL) THEN 'debtor'"
                  " WHEN EXISTS (SELECT 1 FROM loans l WHERE l.member_id = m.member_id) THEN 'borrower'"
                  " ELSE 'lapsed' END, COUNT(*) FROM members m GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN EXISTS (SELECT 1 FROM loans l WHERE l.member_id = m.member_id) THEN 'borrower'"
                  " WHEN EXISTS (SELECT 1 FROM fines f JOIN loans l ON l.loan_id = f.loan_id"
                  " WHERE l.member_id = m.member_id AND f.paid_on IS NULL) THEN 'debtor'"
                  " ELSE 'lapsed' END, COUNT(*) FROM members m GROUP BY 1"),
        note="Every debtor is also a borrower, so the two classes"
             " overlap and CASE's first-match rule decides who wins:"
             " the narrower test has to come first. With 'borrower'"
             " tested first no member is ever a debtor. An EXISTS can"
             " sit anywhere a boolean can, including inside a WHEN.",
        claims=[("three classes, seven hundred or so debtors, two hundred lapsed",
                 lambda rows, c: dict(rows).get('lapsed') == 200
                 and 700 < dict(rows).get('debtor', 0) < 740
                 and sum(r[1] for r in rows) == 1500)],
    ),
    dict(
        id=6, ledger="Q972", concept="A3", tier="2 - EXISTS, CASE and HAVING",
        title="Spread out, but not at Central",
        prompt=(
            "Books with copies at three or more DIFFERENT branches but no"
            " copy at Central (branch 1): book_id and the number of"
            " branches. Both conditions are about the book's whole set of"
            " copies, so both are HAVING -- a WHERE branch_id <> 1 would"
            " hide Central's copies rather than exclude the book.\n\n"
            "Return: book_id, branches"
        ),
        solution=("SELECT book_id, COUNT(DISTINCT branch_id) FROM copies GROUP BY book_id"
                  " HAVING COUNT(DISTINCT branch_id) >= 3 AND SUM(branch_id = 1) = 0"),
        trap_sql=("SELECT book_id, COUNT(DISTINCT branch_id) FROM copies WHERE branch_id <> 1"
                  " GROUP BY book_id HAVING COUNT(DISTINCT branch_id) >= 3"),
        note="SUM(branch_id = 1) = 0 says 'none of this book's copies is"
             " at Central', an aggregate fact. Filtering Central's copies"
             " out first makes every book look as if it has none there,"
             " and twice as many books qualify. 'Not at X' about a group"
             " is a HAVING, not a WHERE.",
        claims=[("a hundred and thirty or so books",
                 lambda rows, c: 115 < len(rows) < 140 and all(r[1] >= 3 for r in rows))],
    ),
    # =========================================== 3 Recursion meets intervals
    dict(
        id=7, ledger="Q973", concept="INT", tier="3 - Recursion meets intervals",
        title="Loans open at each month's end",
        prompt=(
            "For each month from 2025-01 to 2026-06, how many loans were"
            " OUT on the last day of the month: started on or before it,"
            " and not returned by it -- NULL returned_on means still out."
            " A recursive CTE of month starts, date(first, '+1 month',"
            " '-1 day') for the last day, and the interval test with"
            " COALESCE.\n\n"
            "Return: month_start, open_at_end"
        ),
        solution=("WITH RECURSIVE m(first) AS (SELECT '2025-01-01' UNION ALL SELECT date(first, '+1 month') FROM m"
                  " WHERE first < '2026-06-01')"
                  " SELECT first, (SELECT COUNT(*) FROM loans l WHERE l.loaned_on <= date(m.first, '+1 month', '-1 day')"
                  " AND COALESCE(l.returned_on, '9999') > date(m.first, '+1 month', '-1 day')) FROM m"),
        trap_sql=("WITH RECURSIVE m(first) AS (SELECT '2025-01-01' UNION ALL SELECT date(first, '+1 month') FROM m"
                  " WHERE first < '2026-06-01')"
                  " SELECT first, (SELECT COUNT(*) FROM loans l WHERE l.loaned_on <= date(m.first, '+1 month', '-1 day')"
                  " AND l.returned_on > date(m.first, '+1 month', '-1 day')) FROM m"),
        note="Two modifiers chain: '+1 month' then '-1 day' is the last"
             " day of the month however long it is. The interval test is"
             " the same as every 'on a day' question, and the COALESCE"
             " is what makes June 2026 right -- the 685 loans still out"
             " at the end of the data have a NULL end, and NULL > a date"
             " is never true.",
        claims=[("eighteen months, June 2026 with the 685 still out",
                 lambda rows, c: len(rows) == 18 and ('2026-06-01', 685) in rows
                 and all(500 < r[1] < 900 for r in rows))],
    ),
    dict(
        id=8, ledger="Q974", concept="R1", tier="3 - Recursion meets intervals",
        title="Old Town's copies out, day by day",
        prompt=(
            "For every day of June 2026, how many of branch 6's copies"
            " were out on loan that day -- loaned on or before the day"
            " and not back before it. A recursive CTE of days, and per"
            " day a count over loans joined to copies, with the open end"
            " supplied.\n\n"
            "Return: day, copies_out"
        ),
        solution=("WITH RECURSIVE d(day) AS (SELECT '2026-06-01' UNION ALL SELECT date(day, '+1 day') FROM d"
                  " WHERE day < '2026-06-30')"
                  " SELECT day, (SELECT COUNT(*) FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " WHERE c.branch_id = 6 AND l.loaned_on <= d.day AND COALESCE(l.returned_on, '9999') > d.day) FROM d"),
        trap_sql=("WITH RECURSIVE d(day) AS (SELECT '2026-06-01' UNION ALL SELECT date(day, '+1 day') FROM d"
                  " WHERE day < '2026-06-30')"
                  " SELECT day, (SELECT COUNT(*) FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " WHERE c.branch_id = 6 AND l.loaned_on = d.day) FROM d"),
        note="A loan is out on a day if the day falls inside its"
             " interval, which is two comparisons; counting the loans"
             " that STARTED that day is one comparison and a different"
             " question -- about five a day instead of a hundred and"
             " twenty. The calendar supplies the days; the subquery"
             " answers for each.",
        claims=[("thirty days, a hundred or so copies out on each",
                 lambda rows, c: len(rows) == 30 and all(90 < r[1] < 150 for r in rows))],
    ),
    # ================================================== 4 JSON in aggregates
    dict(
        id=9, ledger="Q975", concept="JSN", tier="4 - JSON in aggregates",
        title="Each genre's stock by condition, as JSON",
        prompt=(
            "For each genre, ONE JSON array of objects, one object per"
            " condition in alphabetical order, each with keys condition"
            " and copies: a CTE counting copies per genre and condition,"
            " then json_group_array of a json_object, with ORDER BY"
            " condition inside the json_group_array.\n\n"
            "Return: genre, stock"
        ),
        solution=("WITH t AS (SELECT b.genre, c.condition, COUNT(*) AS n FROM copies c"
                  " JOIN books b ON b.book_id = c.book_id GROUP BY b.genre, c.condition)"
                  " SELECT genre, json_group_array(json_object('condition', condition, 'copies', n) ORDER BY condition)"
                  " FROM t GROUP BY genre"),
        trap_sql=("WITH t AS (SELECT b.genre, c.condition, COUNT(*) AS n FROM copies c"
                  " JOIN books b ON b.book_id = c.book_id GROUP BY b.genre, c.condition)"
                  " SELECT genre, json_group_array(json_object('condition', condition, 'copies', n) ORDER BY n)"
                  " FROM t GROUP BY genre"),
        note="Two levels of grouping: the CTE groups to (genre,"
             " condition) and counts; the outer query groups to genre and"
             " packs each group's rows into JSON. json_object builds one"
             " element, json_group_array collects them, and its ORDER BY"
             " decides the array order -- by condition name, as asked,"
             " not by count.",
        claims=[("eight genres, three objects each in alphabetical order",
                 lambda rows, c: len(rows) == 8
                 and all([o['condition'] for o in __import__('json').loads(r[1])]
                         == ['damaged', 'good', 'worn'] for r in rows))],
    ),
    dict(
        id=10, ledger="Q976", concept="JSN", tier="4 - JSON in aggregates",
        title="The three most borrowed titles per genre, as a list",
        prompt=(
            "For each genre, a JSON array of its three most borrowed"
            " titles, most borrowed first -- ties by lower book_id. A"
            " CTE that counts loans per book and numbers the books within"
            " their genre by ROW_NUMBER, then json_group_array of the"
            " titles numbered 3 or less, ordered by that number.\n\n"
            "Return: genre, top3"
        ),
        solution=("WITH r AS (SELECT b.genre, b.title, COUNT(*) AS n,"
                  " ROW_NUMBER() OVER (PARTITION BY b.genre ORDER BY COUNT(*) DESC, b.book_id) AS rn"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id JOIN books b ON b.book_id = c.book_id"
                  " GROUP BY b.book_id)"
                  " SELECT genre, json_group_array(title ORDER BY rn) FROM r WHERE rn <= 3 GROUP BY genre"),
        trap_sql=("WITH r AS (SELECT b.genre, b.title, COUNT(*) AS n,"
                  " ROW_NUMBER() OVER (PARTITION BY b.genre ORDER BY COUNT(*) DESC, b.book_id) AS rn"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id JOIN books b ON b.book_id = c.book_id"
                  " GROUP BY b.book_id)"
                  " SELECT genre, json_group_array(title ORDER BY rn) FROM r GROUP BY genre"),
        note="The window numbers every book; the WHERE rn <= 3 in the"
             " outer query is what keeps three -- without it every title"
             " in the genre goes into the array. A ranked CTE followed by"
             " a filter on the rank is the top-N pattern; here its result"
             " is packed into JSON rather than returned as rows.",
        claims=[("eight genres, three titles each",
                 lambda rows, c: len(rows) == 8
                 and all(len(__import__('json').loads(r[1])) == 3 for r in rows))],
    ),
    # ============================================== 5 Text with aggregation
    dict(
        id=11, ledger="Q977", concept="STR", tier="5 - Text with aggregation",
        title="The surnames at each branch, once each",
        prompt=(
            "For each branch, the DISTINCT surnames of its staff --"
            " the part of name after the space -- joined into one"
            " comma-separated string in alphabetical order."
            " GROUP_CONCAT(DISTINCT ... ORDER BY ...) over a SUBSTR;"
            " two colleagues who share a surname contribute it once.\n\n"
            "Return: branch_id, surnames"
        ),
        solution=("SELECT branch_id, GROUP_CONCAT(DISTINCT SUBSTR(name, INSTR(name, ' ') + 1)"
                  " ORDER BY SUBSTR(name, INSTR(name, ' ') + 1)) FROM staff GROUP BY branch_id"),
        trap_sql=("SELECT branch_id, GROUP_CONCAT(SUBSTR(name, INSTR(name, ' ') + 1)"
                  " ORDER BY SUBSTR(name, INSTR(name, ' ') + 1)) FROM staff GROUP BY branch_id"),
        note="GROUP_CONCAT accepts DISTINCT like COUNT does, and in"
             " SQLite 3.44 and later an ORDER BY as well -- but not a"
             " custom separator together with DISTINCT, so the default"
             " comma it is. The expression being concatenated is the"
             " SUBSTR, and the ORDER BY repeats it. Central has two"
             " Ekwuemes; without DISTINCT the name appears twice.",
        claims=[("six branches, no surname repeated in any",
                 lambda rows, c: len(rows) == 6
                 and all(len(r[1].split(',')) == len(set(r[1].split(','))) for r in rows))],
    ),
    dict(
        id=12, ledger="Q978", concept="STR", tier="5 - Text with aggregation",
        title="Authors who share a surname",
        prompt=(
            "Surnames held by MORE THAN ONE author: the surname, how"
            " many authors have it, and their full names joined with"
            " ', ' in alphabetical order. The surname is a SUBSTR from"
            " INSTR; group by that expression and filter the groups in"
            " HAVING.\n\n"
            "Return: surname, authors, names"
        ),
        solution=("SELECT SUBSTR(name, INSTR(name, ' ') + 1) AS surname, COUNT(*), GROUP_CONCAT(name, ', ' ORDER BY name)"
                  " FROM authors GROUP BY surname HAVING COUNT(*) > 1"),
        trap_sql=("SELECT SUBSTR(name, INSTR(name, ' ') + 1) AS surname, COUNT(*), GROUP_CONCAT(name, ', ' ORDER BY name)"
                  " FROM authors GROUP BY name HAVING COUNT(*) > 1"),
        note="GROUP BY can take an expression, or the alias of one, and"
             " that is what groups the authors by surname. Grouping by"
             " the full name instead groups the two Priya Achebes together"
             " and nobody else -- the question of who shares a SURNAME"
             " needs the surname to be the group. Twenty-four surnames"
             " are shared.",
        claims=[("twenty-four surnames, each held by two or more",
                 lambda rows, c: len(rows) == 24 and all(r[1] >= 2 for r in rows)
                 and all(r[2].count(', ') == r[1] - 1 for r in rows))],
    ),
    # ================================================= 6 Changing the data
    dict(
        id=13, ledger="Q979", concept="TRG", tier="6 - Changing the data",
        kind="script",
        title="One loan at a time per copy",
        prompt=(
            "Write a BEFORE INSERT trigger on loans that refuses --"
            " RAISE(ABORT, ...) -- a loan of a copy that is ALREADY OUT:"
            " a loan of the same copy with returned_on NULL exists. The"
            " question then lends copy 4, which is out, and copy 1,"
            " which is on the shelf.\n\n"
            "Checked: which of the two loans exist"
        ),
        solution=("CREATE TRIGGER one_loan_per_copy BEFORE INSERT ON loans\n"
                  "WHEN EXISTS (SELECT 1 FROM loans l WHERE l.copy_id = NEW.copy_id AND l.returned_on IS NULL)\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'copy is already out');\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER one_loan_per_copy BEFORE INSERT ON loans\n"
                  "WHEN EXISTS (SELECT 1 FROM loans l WHERE l.copy_id = NEW.copy_id)\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'copy is already out');\n"
                  "END;"),
        driver_sql=("INSERT INTO loans (copy_id, member_id, loaned_on, due_on) VALUES (4, 5, '2026-07-01', '2026-07-22');\n"
                    "INSERT INTO loans (copy_id, member_id, loaned_on, due_on) VALUES (1, 5, '2026-07-01', '2026-07-22');"),
        probe_sql="SELECT copy_id FROM loans WHERE loan_id > 23976 ORDER BY loan_id",
        note="The WHEN is an EXISTS over the table being inserted into,"
             " correlated on NEW.copy_id, and the interval condition is"
             " the open end: returned_on IS NULL. Without it any copy"
             " that has EVER been lent is refused, which is almost all of"
             " them -- copy 1 has fourteen loans in its history and is"
             " nevertheless on the shelf.",
        claims=[("copy 4 refused, copy 1 lent",
                 lambda rows, c: rows == [(1,)])],
    ),
    dict(
        id=14, ledger="Q980", concept="DML", tier="6 - Changing the data",
        kind="script",
        title="Grace for the five most overdue",
        prompt=(
            "The five loans that are furthest past due on 2026-06-30 --"
            " still out, earliest due_on first, ties by lower loan_id --"
            " get one more renewal: set renewals to 2 and push due_on"
            " fourteen days on. A CTE with ROW_NUMBER picks them, and the"
            " UPDATE's WHERE is an IN over the CTE.\n\n"
            "Checked: the renewals and due_on of the five"
        ),
        solution=("WITH ranked AS (SELECT loan_id, ROW_NUMBER() OVER (ORDER BY due_on, loan_id) AS rn\n"
                  "                FROM loans WHERE returned_on IS NULL AND due_on < '2026-06-30')\n"
                  "UPDATE loans SET renewals = 2, due_on = date(due_on, '+14 days')\n"
                  "WHERE loan_id IN (SELECT loan_id FROM ranked WHERE rn <= 5);"),
        trap_sql=("WITH ranked AS (SELECT loan_id, ROW_NUMBER() OVER (ORDER BY due_on DESC, loan_id) AS rn\n"
                  "                FROM loans WHERE returned_on IS NULL AND due_on < '2026-06-30')\n"
                  "UPDATE loans SET renewals = 2, due_on = date(due_on, '+14 days')\n"
                  "WHERE loan_id IN (SELECT loan_id FROM ranked WHERE rn <= 5);"),
        probe_sql=("SELECT loan_id, renewals, due_on FROM loans"
                   " WHERE loan_id IN (21461, 7469, 3607, 20653, 5719) ORDER BY loan_id"),
        note="A WITH clause can precede an UPDATE, and the CTE is where"
             " the window function lives -- an UPDATE cannot hold one"
             " directly. 'Furthest past due' is the EARLIEST due date,"
             " so the numbering is ascending; DESC picks the five that"
             " only just fell due. date(due_on, '+14 days') moves the"
             " date; renewals = 2 is the cap the table's CHECK allows.",
        claims=[("all five renewed twice and due a fortnight later",
                 lambda rows, c: len(rows) == 5 and all(r[1] == 2 for r in rows)
                 and (21461, 2, '2026-05-07') in rows)],
    ),
    dict(
        id=15, ledger="Q981", concept="VIEW", tier="6 - Changing the data",
        kind="script",
        title="A view you can write to",
        prompt=(
            "Create a view `member_contact (member_id, name, area)` over"
            " members, with area being postcode_area -- then make it"
            " UPDATABLE: an INSTEAD OF UPDATE OF area trigger on the view"
            " that writes NEW.area into members.postcode_area for the row"
            " whose member_id is OLD.member_id. The question then runs"
            " UPDATE member_contact SET area = 'LS1' WHERE member_id ="
            " 3.\n\n"
            "Checked: member 3's postcode_area"
        ),
        solution=("CREATE VIEW member_contact AS\n"
                  "  SELECT member_id, name, postcode_area AS area FROM members;\n"
                  "CREATE TRIGGER contact_area INSTEAD OF UPDATE OF area ON member_contact\n"
                  "BEGIN\n"
                  "  UPDATE members SET postcode_area = NEW.area WHERE member_id = OLD.member_id;\n"
                  "END;"),
        trap_sql=("CREATE VIEW member_contact AS\n"
                  "  SELECT member_id, name, postcode_area AS area FROM members;"),
        driver_sql="UPDATE member_contact SET area = 'LS1' WHERE member_id = 3;",
        probe_sql="SELECT postcode_area FROM members WHERE member_id = 3",
        note="A view is read-only unless an INSTEAD OF trigger says what"
             " an UPDATE, INSERT or DELETE on it should do; SQLite then"
             " runs the trigger body in place of the statement. OLD and"
             " NEW are the view's rows, so OLD.member_id identifies the"
             " member and NEW.area is the value to write. Without the"
             " trigger the question's UPDATE is simply refused.",
        claims=[("member 3 moved to LS1",
                 lambda rows, c: rows == [('LS1',)])],
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
