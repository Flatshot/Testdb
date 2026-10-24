"""Practice exercises: fifteen questions on the library schema.

The fifteenth set on the library (SEED 861), two tools per question, with
the tiers named by task. Renewals -- a renewal rate ranked by DENSE_RANK,
lateness by renewal count with a conditional AVG, the keenest renewers by
HAVING with a ratio. The catalogue -- the longest book per genre through
a bare column, publication decades with a cumulative share, an author's
cookbooks as JSON behind a LIKE. Staff and salaries -- a rank within the
role beside a gap to the top, service bands by CASE over julianday,
wage bill per copy by two scalar subqueries against an average. A day in
the life -- four counts stacked by UNION ALL, the busiest hour by strftime
under ROW_NUMBER, a day's returns with their fines through a LEFT JOIN. And
three WRITABLE questions in two steps each:

  * a BEFORE UPDATE trigger that checks the date arithmetic of a renewal
  * an UPDATE whose SET and WHERE both hold a correlated average
  * CREATE TABLE ... AS SELECT followed by CREATE INDEX on it

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script.
"""

import sqlite3

EXERCISES = [
    # ============================================================= 1 Renewals
    dict(
        id=1, ledger="Q1057", concept="W2", tier="1 - Renewals",
        title="Which genres get renewed",
        prompt=(
            "For each genre, the percentage of its loans that were"
            " renewed at least once, to one decimal, and the genre's"
            " place by that rate, 1 for the highest. AVG of the comparison"
            " renewals > 0 through the two joins, and DENSE_RANK over the"
            " grouped rate.\n\n"
            "Return: genre, pct_renewed, place"
        ),
        solution=("SELECT b.genre, ROUND(100.0 * AVG(l.renewals > 0), 1),"
                  " DENSE_RANK() OVER (ORDER BY AVG(l.renewals > 0) DESC)"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id JOIN books b ON b.book_id = c.book_id"
                  " GROUP BY b.genre"),
        trap_sql=("SELECT b.genre, ROUND(100.0 * AVG(l.renewals), 1),"
                  " DENSE_RANK() OVER (ORDER BY AVG(l.renewals) DESC)"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id JOIN books b ON b.book_id = c.book_id"
                  " GROUP BY b.genre"),
        note="renewals > 0 is a 1-or-0 per loan, so its AVG is the share"
             " of loans renewed; AVG(renewals) is the average NUMBER of"
             " renewals, around 0.7, and a hundred times that is not a"
             " percentage of anything. The window ranks the grouped rows"
             " by the same expression.",
        claims=[("eight genres, all near a half, biography first",
                 lambda rows, c: len(rows) == 8 and all(45 < r[1] < 55 for r in rows)
                 and min(rows, key=lambda r: r[2])[0] == 'biography')],
    ),
    dict(
        id=2, ledger="Q1058", concept="N1", tier="1 - Renewals",
        title="Does renewing help?",
        prompt=(
            "For each renewal count 0, 1 and 2, over the RETURNED loans:"
            " the percentage returned late, and the average days late"
            " AMONG the late ones, both to one decimal. A CASE with no"
            " ELSE inside the second AVG, so on-time loans are NULL and"
            " skipped rather than counted as 0.\n\n"
            "Return: renewals, pct_late, avg_days_late"
        ),
        solution=("SELECT renewals, ROUND(100.0 * AVG(returned_on > due_on), 1),"
                  " ROUND(AVG(CASE WHEN returned_on > due_on THEN julianday(returned_on) - julianday(due_on) END), 1)"
                  " FROM loans WHERE returned_on IS NOT NULL GROUP BY renewals"),
        trap_sql=("SELECT renewals, ROUND(100.0 * AVG(returned_on > due_on), 1),"
                  " ROUND(AVG(MAX(julianday(returned_on) - julianday(due_on), 0)), 1)"
                  " FROM loans WHERE returned_on IS NOT NULL GROUP BY renewals"),
        note="Two averages over the same group that treat the on-time"
             " loans differently on purpose: the rate counts them as 0,"
             " the days-late average leaves them out. MAX(d, 0) puts a 0"
             " in for every on-time loan and the average collapses to a"
             " day or two. Renewing cuts the late RATE sharply but barely"
             " changes how late the late ones are.",
        claims=[("three rows, the late rate falling with renewals, days late steady",
                 lambda rows, c: len(rows) == 3
                 and dict((r[0], r[1]) for r in rows)[0] > dict((r[0], r[1]) for r in rows)[1] > dict((r[0], r[1]) for r in rows)[2]
                 and all(13 < r[2] < 17 for r in rows))],
    ),
    dict(
        id=3, ledger="Q1059", concept="A3", tier="1 - Renewals",
        title="The keenest renewers",
        prompt=(
            "The ten members with the most renewals per loan among"
            " members with at least 10 loans, ties by lower member_id:"
            " member_id, loans, and renewals per loan to two decimals."
            " GROUP BY with HAVING on the count, a floating-point ratio"
            " of SUM over COUNT, ORDER BY and LIMIT.\n\n"
            "Return: member_id, loans, renewals_per_loan"
        ),
        solution=("SELECT member_id, COUNT(*), ROUND(1.0 * SUM(renewals) / COUNT(*), 2) AS r FROM loans"
                  " GROUP BY member_id HAVING COUNT(*) >= 10 ORDER BY r DESC, member_id LIMIT 10"),
        trap_sql=("SELECT member_id, COUNT(*), ROUND(SUM(renewals) / COUNT(*), 2) AS r FROM loans"
                  " GROUP BY member_id HAVING COUNT(*) >= 10 ORDER BY r DESC, member_id LIMIT 10"),
        note="SUM(renewals) / COUNT(*) is integer division -- 18 / 14 is"
             " 1 -- so every member's ratio is 0 or 1 and the top ten is"
             " decided by the tie-break alone. The 1.0 * makes it a real"
             " ratio. The tenth and eleventh members tie on 1.14, which"
             " is why the question fixes the tie-break.",
        claims=[("ten members, the keenest at 1.29",
                 lambda rows, c: len(rows) == 10 and rows[0] == (1174, 14, 1.29) and all(r[1] >= 10 for r in rows))],
    ),
    # ======================================================== 2 The catalogue
    dict(
        id=4, ledger="Q1060", concept="BARE", tier="2 - The catalogue",
        title="The longest book in each genre",
        prompt=(
            "For each genre: the title and page count of its longest"
            " book. MAX(pages) with title as a bare column -- SQLite"
            " brings the title from the row the MAX came from. Each"
            " genre's maximum is held by one book.\n\n"
            "Return: genre, title, pages"
        ),
        solution="SELECT genre, title, MAX(pages) FROM books GROUP BY genre",
        trap_sql="SELECT genre, title, MIN(pages) FROM books GROUP BY genre",
        note="The bare-column rule again, with no join at all this time:"
             " one table, one MAX, and the other selected column comes"
             " from the same row. MIN is the shortest book, which is"
             " also a fair question but not this one.",
        claims=[("eight genres, every title really the longest",
                 lambda rows, c: len(rows) == 8
                 and all(r[2] == c.execute("SELECT MAX(pages) FROM books WHERE genre = ?", (r[0],)).fetchone()[0]
                         and c.execute("SELECT pages FROM books WHERE title = ?", (r[1],)).fetchone()[0] == r[2]
                         for r in rows))],
    ),
    dict(
        id=5, ledger="Q1061", concept="W1", tier="2 - The catalogue",
        title="The catalogue by decade of publication",
        prompt=(
            "Books per decade of publication -- published_year / 10 * 10"
            " -- with the cumulative percentage of the catalogue"
            " published by the end of that decade, to one decimal. A"
            " running window SUM over the grouped counts, divided by the"
            " catalogue's 600.\n\n"
            "Return: decade, books, cum_pct"
        ),
        solution=("SELECT published_year / 10 * 10 AS d, COUNT(*),"
                  " ROUND(100.0 * SUM(COUNT(*)) OVER (ORDER BY published_year / 10 * 10) / (SELECT COUNT(*) FROM books), 1)"
                  " FROM books GROUP BY d"),
        trap_sql=("SELECT published_year / 10 * 10 AS d, COUNT(*),"
                  " ROUND(100.0 * SUM(COUNT(*)) OVER () / (SELECT COUNT(*) FROM books), 1)"
                  " FROM books GROUP BY d"),
        note="Integer division then multiplication rounds a year down to"
             " its decade, and the decade is both the GROUP BY and the"
             " window's ORDER BY. The ORDER BY is what makes the SUM"
             " cumulative; without it every decade shows 100. The last"
             " decade, the 2020s, holds a sixth of the catalogue.",
        claims=[("sixteen decades, the last reaching a hundred",
                 lambda rows, c: len(rows) == 16 and max(rows)[2] == 100.0 and sum(r[1] for r in rows) == 600)],
    ),
    dict(
        id=6, ledger="Q1062", concept="JSN", tier="2 - The catalogue",
        title="Authors with more than one cookbook",
        prompt=(
            "Authors with two or more titles ending in 'Cookbook':"
            " author_id, the total pages of those cookbooks, and the"
            " titles as a JSON array in alphabetical order. A LIKE in the"
            " WHERE, GROUP BY author, HAVING on the count, SUM(pages) and"
            " json_group_array with ORDER BY.\n\n"
            "Return: author_id, cookbook_pages, titles"
        ),
        solution=("SELECT author_id, SUM(pages), json_group_array(title ORDER BY title) FROM books"
                  " WHERE title LIKE '%Cookbook' GROUP BY author_id HAVING COUNT(*) >= 2"),
        trap_sql=("SELECT author_id, SUM(pages), json_group_array(title ORDER BY title) FROM books"
                  " GROUP BY author_id HAVING COUNT(*) >= 2"),
        note="The WHERE narrows to cookbooks BEFORE the grouping, so the"
             " page total and the array are of cookbooks only; without it"
             " the question becomes 'authors with two or more books', a"
             " hundred and nine of them with every title listed. LIKE"
             " with a leading wildcard is fine here -- there is no index"
             " to lose.",
        claims=[("eleven authors, every title a cookbook",
                 lambda rows, c: len(rows) == 11
                 and all(all(t.endswith('Cookbook') for t in __import__('json').loads(r[2])) for r in rows)
                 and len({r[1] for r in rows}) > 1)],
    ),
    # ================================================== 3 Staff and salaries
    dict(
        id=7, ledger="Q1063", concept="W2", tier="3 - Staff and salaries",
        title="Where each person stands in their role",
        prompt=(
            "Every member of staff with their place by salary within"
            " their ROLE, 1 for the best paid, and how far below the"
            " role's top salary they are. DENSE_RANK partitioned by"
            " role, and MAX(salary) OVER the same partition minus the"
            " salary.\n\n"
            "Return: staff_id, role, place, gap"
        ),
        solution=("SELECT staff_id, role, DENSE_RANK() OVER (PARTITION BY role ORDER BY salary DESC),"
                  " MAX(salary) OVER (PARTITION BY role) - salary FROM staff"),
        trap_sql=("SELECT staff_id, role, DENSE_RANK() OVER (ORDER BY salary DESC),"
                  " MAX(salary) OVER () - salary FROM staff"),
        note="Two windows over the same partition: a ranking and an"
             " aggregate. Without PARTITION BY role both compare everyone"
             " with everyone, so every assistant trails the best-paid"
             " manager by twenty thousand and ranks in the twenties. The"
             " top of each role has a gap of 0.",
        claims=[("thirty-one staff, three people with a gap of 0",
                 lambda rows, c: len(rows) == 31 and sum(r[3] == 0 for r in rows) == 3
                 and sum(r[2] == 1 for r in rows) == 3)],
    ),
    dict(
        id=8, ledger="Q1064", concept="C7", tier="3 - Staff and salaries",
        title="Pay by length of service",
        prompt=(
            "Staff in three bands by years of service on 2026-06-30 --"
            " 'under 5', '5 to 14', '15 and over' -- with how many are in"
            " each and their average salary in whole pounds. Years of"
            " service are the julianday difference over 365.25; the band"
            " is a CASE with the smallest band tested first.\n\n"
            "Return: band, staff, avg_salary"
        ),
        solution=("SELECT CASE WHEN (julianday('2026-06-30') - julianday(hired_on)) / 365.25 < 5 THEN 'under 5'"
                  " WHEN (julianday('2026-06-30') - julianday(hired_on)) / 365.25 < 15 THEN '5 to 14'"
                  " ELSE '15 and over' END, COUNT(*), CAST(ROUND(AVG(salary)) AS INTEGER) FROM staff GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN (julianday('2026-06-30') - julianday(hired_on)) / 365.25 < 15 THEN '5 to 14'"
                  " WHEN (julianday('2026-06-30') - julianday(hired_on)) / 365.25 < 5 THEN 'under 5'"
                  " ELSE '15 and over' END, COUNT(*), CAST(ROUND(AVG(salary)) AS INTEGER) FROM staff GROUP BY 1"),
        note="Dividing a julianday difference by 365.25 gives years as a"
             " fraction, which the CASE bands. Narrowest first: tested"
             " the other way, everyone under 15 years is already '5 to"
             " 14' and the 'under 5' band is empty. The newest recruits"
             " are, as it happens, the best paid on average -- two of"
             " the five are managers.",
        claims=[("three bands adding up to thirty-one staff",
                 lambda rows, c: len(rows) == 3 and sum(r[1] for r in rows) == 31
                 and all(20000 < r[2] < 35000 for r in rows))],
    ),
    dict(
        id=9, ledger="Q1065", concept="C2", tier="3 - Staff and salaries",
        title="Wage bill per copy, where it runs high",
        prompt=(
            "Branches whose total staff salary per copy held is above the"
            " service-wide figure -- all salaries over all copies. Staff"
            " and copies are two children of a branch, so each total is"
            " its own scalar subquery; the comparison is against a"
            " scalar subquery too. Whole pounds per copy.\n\n"
            "Return: branch_id, salary_per_copy"
        ),
        solution=("SELECT b.branch_id, CAST(ROUND((SELECT SUM(salary) FROM staff s WHERE s.branch_id = b.branch_id) * 1.0"
                  " / (SELECT COUNT(*) FROM copies c WHERE c.branch_id = b.branch_id)) AS INTEGER) AS spc"
                  " FROM branches b WHERE (SELECT SUM(salary) FROM staff s WHERE s.branch_id = b.branch_id) * 1.0"
                  " / (SELECT COUNT(*) FROM copies c WHERE c.branch_id = b.branch_id)"
                  " > (SELECT SUM(salary) FROM staff) * 1.0 / (SELECT COUNT(*) FROM copies)"),
        trap_sql=("SELECT b.branch_id, CAST(ROUND(SUM(s.salary) * 1.0 / COUNT(c.copy_id)) AS INTEGER) AS spc"
                  " FROM branches b JOIN staff s ON s.branch_id = b.branch_id JOIN copies c ON c.branch_id = b.branch_id"
                  " GROUP BY b.branch_id HAVING SUM(s.salary) * 1.0 / COUNT(c.copy_id)"
                  " > (SELECT SUM(salary) FROM staff) * 1.0 / (SELECT COUNT(*) FROM copies)"),
        note="Joining staff and copies to the same branch multiplies"
             " them: SUM(salary) is each salary repeated once per copy,"
             " and the ratio is inflated by the number of staff. Scalar"
             " subqueries total each child on its own. Central, with"
             " seven staff and 381 copies, spends the most per copy.",
        claims=[("three branches above the average, Central the highest",
                 lambda rows, c: {r[0] for r in rows} == {1, 2, 4} and all(r[1] > 395 for r in rows)
                 and max(rows, key=lambda r: r[1])[0] == 1)],
    ),
    # ==================================================== 4 A day in the life
    dict(
        id=10, ledger="Q1066", concept="S1", tier="4 - A day in the life",
        title="Monday 2 March 2026, in four numbers",
        prompt=(
            "For 2026-03-02, four rows labelled 'loans', 'returns',"
            " 'holds' and 'fines' with how many of each happened that"
            " day: loans started, loans returned, holds placed -- date()"
            " of placed_at -- and fines issued. Four one-row queries"
            " stacked by UNION ALL.\n\n"
            "Return: event, count"
        ),
        solution=("SELECT 'loans', COUNT(*) FROM loans WHERE loaned_on = '2026-03-02'"
                  " UNION ALL SELECT 'returns', COUNT(*) FROM loans WHERE returned_on = '2026-03-02'"
                  " UNION ALL SELECT 'holds', COUNT(*) FROM holds WHERE date(placed_at) = '2026-03-02'"
                  " UNION ALL SELECT 'fines', COUNT(*) FROM fines WHERE issued_on = '2026-03-02'"),
        trap_sql=("SELECT 'loans', COUNT(*) FROM loans WHERE loaned_on = '2026-03-02'"
                  " UNION ALL SELECT 'returns', COUNT(*) FROM loans WHERE returned_on = '2026-03-02'"
                  " UNION ALL SELECT 'holds', COUNT(*) FROM holds WHERE placed_at = '2026-03-02'"
                  " UNION ALL SELECT 'fines', COUNT(*) FROM fines WHERE issued_on = '2026-03-02'"),
        note="Four unrelated counts become one result through UNION ALL"
             " with a label column. The holds count is the one that"
             " needs care: placed_at carries a time, so it never equals a"
             " bare date and date() has to cut the time off first. The"
             " nine fines are the nine late returns of the day.",
        claims=[("four events, the fines matching the late returns",
                 lambda rows, c: len(rows) == 4 and dict(rows)['holds'] == 2 and dict(rows)['fines'] == 9)],
    ),
    dict(
        id=11, ledger="Q1067", concept="D1", tier="4 - A day in the life",
        title="When members place holds",
        prompt=(
            "The three hours of the day in which the most holds have been"
            " placed, ties by the earlier hour: the hour as strftime's"
            " %H, and the count. GROUP BY the hour, ROW_NUMBER over the"
            " counts, keep the first three.\n\n"
            "Return: hour, holds"
        ),
        solution=("SELECT h, n FROM (SELECT strftime('%H', placed_at) AS h, COUNT(*) AS n,"
                  " ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC, strftime('%H', placed_at)) AS rn FROM holds GROUP BY h)"
                  " WHERE rn <= 3"),
        trap_sql=("SELECT h, n FROM (SELECT strftime('%M', placed_at) AS h, COUNT(*) AS n,"
                  " ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC, strftime('%M', placed_at)) AS rn FROM holds GROUP BY h)"
                  " WHERE rn <= 3"),
        note="%H is the hour and %M the minute -- strftime's letters are"
             " case-sensitive and %M groups the holds into sixty bins of"
             " a different kind. The ranking's second key, the hour"
             " itself, settles the tie between 10 and 18 o'clock.",
        claims=[("three hours, one o'clock in the morning the busiest",
                 lambda rows, c: len(rows) == 3 and rows[0] == ('01', 74))],
    ),
    dict(
        id=12, ledger="Q1068", concept="J2", tier="4 - A day in the life",
        title="Monday's returns, and what they cost",
        prompt=(
            "Every loan returned on 2026-03-02: loan_id, 1 or 0 for"
            " whether it was late, and the fine in pence -- 0 when there"
            " is none. A LEFT JOIN to fines so on-time returns keep their"
            " row, and COALESCE for the missing amount.\n\n"
            "Return: loan_id, late, fine_pence"
        ),
        solution=("SELECT l.loan_id, l.returned_on > l.due_on, COALESCE(f.amount_pence, 0) FROM loans l"
                  " LEFT JOIN fines f ON f.loan_id = l.loan_id WHERE l.returned_on = '2026-03-02'"),
        trap_sql=("SELECT l.loan_id, l.returned_on > l.due_on, COALESCE(f.amount_pence, 0) FROM loans l"
                  " JOIN fines f ON f.loan_id = l.loan_id WHERE l.returned_on = '2026-03-02'"),
        note="Forty of the forty-nine returns have no fine, and an inner"
             " join drops them, leaving only the nine late ones. The LEFT"
             " JOIN keeps every return with a NULL amount, and COALESCE"
             " turns the NULL into the 0 the question asks for. The late"
             " flag is a bare comparison, which SQLite returns as 1 or 0.",
        claims=[("forty-nine returns, nine late and fined",
                 lambda rows, c: len(rows) == 49 and sum(r[1] for r in rows) == 9
                 and sum(r[2] > 0 for r in rows) == 9)],
    ),
    # ================================================= 5 Changing the data
    dict(
        id=13, ledger="Q1069", concept="TRG", tier="5 - Changing the data",
        kind="script",
        title="A renewal moves the due date by exactly a fortnight",
        prompt=(
            "Write a BEFORE UPDATE OF renewals trigger on loans that"
            " refuses -- RAISE(ABORT, ...) -- any update that raises"
            " renewals unless the new due_on is exactly OLD.due_on plus"
            " 14 days. The question then renews loan 156 properly, loan"
            " 180 without moving its due date, and loan 4107 with only"
            " seven days added.\n\n"
            "Checked: the renewals and due_on of the three loans"
        ),
        solution=("CREATE TRIGGER renewal_is_a_fortnight BEFORE UPDATE OF renewals ON loans\n"
                  "WHEN NEW.renewals > OLD.renewals AND NEW.due_on <> date(OLD.due_on, '+14 days')\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'a renewal adds exactly fourteen days');\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER renewal_is_a_fortnight BEFORE UPDATE OF renewals ON loans\n"
                  "WHEN NEW.renewals > OLD.renewals AND NEW.due_on = OLD.due_on\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'a renewal adds exactly fourteen days');\n"
                  "END;"),
        driver_sql=("UPDATE loans SET renewals = 1, due_on = date(due_on, '+14 days') WHERE loan_id = 156;\n"
                    "UPDATE loans SET renewals = 1 WHERE loan_id = 180;\n"
                    "UPDATE loans SET renewals = 1, due_on = date(due_on, '+7 days') WHERE loan_id = 4107;"),
        probe_sql="SELECT loan_id, renewals, due_on FROM loans WHERE loan_id IN (156, 180, 4107) ORDER BY loan_id",
        note="OLD and NEW together let a trigger check the RELATIONSHIP"
             " between before and after, and date arithmetic inside the"
             " WHEN says what the right relationship is. Refusing only an"
             " unchanged due date lets a seven-day renewal through; the"
             " rule is 'not exactly fourteen', which is <> date(OLD.due_on,"
             " '+14 days').",
        claims=[("156 renewed, 180 and 4107 refused",
                 lambda rows, c: rows == [(156, 1, '2026-07-31'), (180, 0, '2026-07-12'), (4107, 0, '2026-06-20')])],
    ),
    dict(
        id=14, ledger="Q1070", concept="DML", tier="5 - Changing the data",
        kind="script",
        title="Bring the underpaid librarians up to their branch's average",
        prompt=(
            "Every librarian paid LESS than the average librarian salary"
            " at their own branch is raised to that average, rounded to"
            " whole pounds. One UPDATE whose SET and WHERE both use a"
            " correlated subquery over staff for the same branch and"
            " role. Nobody else changes.\n\n"
            "Checked: the total salary of each role"
        ),
        solution=("UPDATE staff SET salary = (SELECT CAST(ROUND(AVG(s2.salary)) AS INTEGER) FROM staff s2"
                  " WHERE s2.role = 'librarian' AND s2.branch_id = staff.branch_id)"
                  " WHERE role = 'librarian' AND salary < (SELECT AVG(s2.salary) FROM staff s2"
                  " WHERE s2.role = 'librarian' AND s2.branch_id = staff.branch_id);"),
        trap_sql=("UPDATE staff SET salary = (SELECT CAST(ROUND(AVG(s2.salary)) AS INTEGER) FROM staff s2"
                  " WHERE s2.role = 'librarian')"
                  " WHERE role = 'librarian' AND salary < (SELECT AVG(s2.salary) FROM staff s2 WHERE s2.role = 'librarian');"),
        probe_sql="SELECT role, SUM(salary) FROM staff GROUP BY role ORDER BY role",
        note="A correlated subquery in SET computes a different value"
             " per row -- here the average for the row's own branch --"
             " and the same subquery in WHERE picks the rows below it."
             " SQLite evaluates the averages before any row changes, so"
             " the raise does not chase itself. Without the branch"
             " correlation the service-wide average is used, a different"
             " set of people and a different total.",
        claims=[("librarians' total up, the other roles unchanged",
                 lambda rows, c: dict(rows)['assistant'] == 287552 and dict(rows)['manager'] == 205813
                 and 386897 < dict(rows)['librarian'] < 400000)],
    ),
    dict(
        id=15, ledger="Q1071", concept="DDL", tier="5 - Changing the data",
        kind="script",
        title="A table of late returns, indexed",
        prompt=(
            "Create a table `late_returns` with CREATE TABLE ... AS SELECT"
            " holding, for every loan returned AFTER its due date, the"
            " loan_id, member_id, and days_late as a whole number -- then"
            " CREATE INDEX idx_late_member ON late_returns (member_id)."
            " On-time and open loans are not in it.\n\n"
            "Checked: how many rows the table holds, the largest days_late,"
            " and whether the index exists"
        ),
        solution=("CREATE TABLE late_returns AS\n"
                  "  SELECT loan_id, member_id, CAST(julianday(returned_on) - julianday(due_on) AS INTEGER) AS days_late\n"
                  "  FROM loans WHERE returned_on > due_on;\n"
                  "CREATE INDEX idx_late_member ON late_returns (member_id);"),
        trap_sql=("CREATE TABLE late_returns AS\n"
                  "  SELECT loan_id, member_id, CAST(julianday(returned_on) - julianday(due_on) AS INTEGER) AS days_late\n"
                  "  FROM loans WHERE returned_on IS NOT NULL;\n"
                  "CREATE INDEX idx_late_member ON late_returns (member_id);"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM late_returns), (SELECT MAX(days_late) FROM late_returns),"
                   " (SELECT COUNT(*) FROM sqlite_master WHERE type = 'index' AND name = 'idx_late_member')"),
        note="CREATE TABLE AS SELECT makes a table whose shape is the"
             " query's, with no keys or indexes of its own -- so a second"
             " statement adds the index a lookup by member will want."
             " The WHERE is the whole definition of the table: returned"
             " IS NOT NULL keeps every returned loan, nineteen thousand"
             " of them on time with days_late at or below zero.",
        claims=[("4,085 late returns, indexed",
                 lambda rows, c: rows[0][0] == 4085 and rows[0][2] == 1 and rows[0][1] > 30)],
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
