"""Practice exercises: fifteen questions on the library schema.

The fourteenth set on the library (SEED 861), two tools per question, with
the tiers named by task. Late returns -- a late rate by month under LAG,
the worst offenders by a clamped SUM with a ranking, fines by band of days
late. The branches compared -- loans per copy ranked, branch pairs by
self-join with two EXISTS, a manager's name by a conditional MAX. Authors
and titles -- the widest span of years, the commonest title words by a
recursive split, first words shared within an author. Members over time --
cohorts with a running total and an EXISTS share, how recently each
member borrowed by CASE over a LEFT JOIN MAX, membership growth per branch
by a partitioned window. And three WRITABLE questions in two steps each:

  * a BEFORE INSERT trigger that refuses a fine on a loan still out
  * a window in a CTE feeding an UPDATE that trims the queues
  * a view and the INSTEAD OF INSERT trigger that fills in the defaults

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
    # ========================================================= 1 Late returns
    dict(
        id=1, ledger="Q1042", concept="W3", tier="1 - Late returns",
        title="The late rate, month by month",
        prompt=(
            "For each month in which loans were RETURNED -- strftime of"
            " returned_on -- the percentage of that month's returns that"
            " were late, to one decimal, and the change from the previous"
            " month in percentage points, NULL for the first. AVG of the"
            " comparison for the rate, LAG over it for the change.\n\n"
            "Return: month, pct_late, change"
        ),
        solution=("SELECT strftime('%Y-%m', returned_on) AS m, ROUND(100.0 * AVG(returned_on > due_on), 1),"
                  " ROUND(100.0 * AVG(returned_on > due_on) - LAG(100.0 * AVG(returned_on > due_on))"
                  " OVER (ORDER BY strftime('%Y-%m', returned_on)), 1)"
                  " FROM loans WHERE returned_on IS NOT NULL GROUP BY m"),
        trap_sql=("SELECT strftime('%Y-%m', returned_on) AS m, ROUND(100.0 * AVG(returned_on > due_on), 1),"
                  " ROUND(100.0 * AVG(returned_on > due_on) - LAG(100.0 * AVG(returned_on > due_on))"
                  " OVER (ORDER BY strftime('%Y-%m', returned_on)), 1)"
                  " FROM loans GROUP BY m"),
        note="Grouping by the RETURN month is what makes this a rate of"
             " returns; without the WHERE the open loans form a NULL"
             " month of their own, with an AVG of NULL. LAG over the"
             " grouped AVG gives the previous month's rate, and the"
             " difference is in points -- 17.9 from 10.5 is 7.4 points.",
        claims=[("eighteen months, the first with no change, rates settling near a sixth",
                 lambda rows, c: len(rows) == 18 and min(rows)[2] is None
                 and all(10 < r[1] < 25 for r in rows if r[0] >= '2025-03'))],
    ),
    dict(
        id=2, ledger="Q1043", concept="W2", tier="1 - Late returns",
        title="The ten worst offenders",
        prompt=(
            "The ten members with the most days late in TOTAL over their"
            " returned loans, ties by lower member_id: member_id, their"
            " total days late as a whole number, and how many of their"
            " loans were late. Days late per loan is MAX(julianday("
            "returned_on) - julianday(due_on), 0), summed; a late count"
            " is SUM of the comparison; ORDER BY and LIMIT.\n\n"
            "Return: member_id, days_late, late_loans"
        ),
        solution=("SELECT member_id, CAST(SUM(MAX(julianday(returned_on) - julianday(due_on), 0)) AS INTEGER),"
                  " SUM(returned_on > due_on) FROM loans WHERE returned_on IS NOT NULL"
                  " GROUP BY member_id ORDER BY 2 DESC, member_id LIMIT 10"),
        trap_sql=("SELECT member_id, CAST(SUM(julianday(returned_on) - julianday(due_on)) AS INTEGER),"
                  " SUM(returned_on > due_on) FROM loans WHERE returned_on IS NOT NULL"
                  " GROUP BY member_id ORDER BY 2 DESC, member_id LIMIT 10"),
        note="Without the clamp, every early return SUBTRACTS days from"
             " the total, and a member who returns most books early and"
             " a few very late nets out to nothing. MAX(x, 0) keeps only"
             " the late days. Two members tie on 756 days, which is why"
             " the question fixes the tie-break.",
        claims=[("ten members, 97 and 1245 tied at the top",
                 lambda rows, c: len(rows) == 10 and rows[0][0] == 97 and rows[1][0] == 1245
                 and rows[0][1] == rows[1][1] == 756)],
    ),
    dict(
        id=3, ledger="Q1044", concept="C7", tier="1 - Late returns",
        title="What a late return costs, by how late",
        prompt=(
            "Fines grouped by how late the loan came back -- '1 to 7'"
            " days, '8 to 30', 'over 30' -- with how many fines in each"
            " band and the average fine in whole pence. The days late"
            " come from the loan the fine hangs off, julianday(returned_on)"
            " minus julianday(due_on); the band is a CASE; the average is"
            " ROUND(AVG(amount_pence)).\n\n"
            "Return: band, fines, avg_fine"
        ),
        solution=("SELECT CASE WHEN julianday(l.returned_on) - julianday(l.due_on) <= 7 THEN '1 to 7'"
                  " WHEN julianday(l.returned_on) - julianday(l.due_on) <= 30 THEN '8 to 30' ELSE 'over 30' END,"
                  " COUNT(*), CAST(ROUND(AVG(f.amount_pence)) AS INTEGER)"
                  " FROM fines f JOIN loans l ON l.loan_id = f.loan_id GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN julianday(l.returned_on) - julianday(l.due_on) <= 30 THEN '8 to 30'"
                  " WHEN julianday(l.returned_on) - julianday(l.due_on) <= 7 THEN '1 to 7' ELSE 'over 30' END,"
                  " COUNT(*), CAST(ROUND(AVG(f.amount_pence)) AS INTEGER)"
                  " FROM fines f JOIN loans l ON l.loan_id = f.loan_id GROUP BY 1"),
        note="The fine's loan carries the dates, so the join comes first"
             " and the CASE bands the join's rows. Narrowest band first:"
             " with <= 30 tested before <= 7 the short delays are already"
             " '8 to 30' and that band swallows the first. The averages"
             " climb from 76 to 825 pence, with the cap flattening the"
             " top band.",
        claims=[("three bands with rising averages",
                 lambda rows, c: len(rows) == 3 and sum(r[1] for r in rows) == 4085
                 and dict((r[0], r[2]) for r in rows)['1 to 7'] < dict((r[0], r[2]) for r in rows)['8 to 30']
                 < dict((r[0], r[2]) for r in rows)['over 30'])],
    ),
    # ================================================ 2 The branches compared
    dict(
        id=4, ledger="Q1045", concept="C2", tier="2 - The branches compared",
        title="Loans per copy, and who works their stock hardest",
        prompt=(
            "For each branch: loans per copy to two decimals -- all loans"
            " of its copies over all its copies, a LEFT JOIN so copies"
            " never loaned count in the denominator -- and the branch's"
            " place by that ratio, 1 for the highest, with DENSE_RANK.\n\n"
            "Return: branch_id, loans_per_copy, place"
        ),
        solution=("SELECT branch_id, ROUND(1.0 * COUNT(l.loan_id) / COUNT(DISTINCT c.copy_id), 2),"
                  " DENSE_RANK() OVER (ORDER BY 1.0 * COUNT(l.loan_id) / COUNT(DISTINCT c.copy_id) DESC)"
                  " FROM copies c LEFT JOIN loans l ON l.copy_id = c.copy_id GROUP BY c.branch_id"),
        trap_sql=("SELECT branch_id, ROUND(1.0 * COUNT(l.loan_id) / COUNT(*), 2),"
                  " DENSE_RANK() OVER (ORDER BY 1.0 * COUNT(l.loan_id) / COUNT(*) DESC)"
                  " FROM copies c LEFT JOIN loans l ON l.copy_id = c.copy_id GROUP BY c.branch_id"),
        note="After the join there is one row per loan, plus one per"
             " never-loaned copy, so COUNT(*) is not the number of"
             " copies -- COUNT(DISTINCT copy_id) is. The ratio then feeds"
             " a window ranking over the six grouped rows, the same"
             " expression repeated inside the OVER.",
        claims=[("six branches, ratios near eleven, places 1 to 6",
                 lambda rows, c: len(rows) == 6 and all(10 < r[1] < 11.5 for r in rows)
                 and sorted(r[2] for r in rows) == [1, 2, 3, 4, 5, 6])],
    ),
    dict(
        id=5, ledger="Q1046", concept="E1", tier="2 - The branches compared",
        title="Readers two branches share",
        prompt=(
            "For every PAIR of branches, each pair once with the lower id"
            " first, how many members have borrowed a copy held at both."
            " A self-join of branches, and a correlated count of members"
            " with two EXISTS tests -- one per branch -- through loans and"
            " copies.\n\n"
            "Return: branch_a, branch_b, shared_readers"
        ),
        solution=("SELECT b1.branch_id, b2.branch_id, (SELECT COUNT(*) FROM members m"
                  " WHERE EXISTS (SELECT 1 FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " WHERE l.member_id = m.member_id AND c.branch_id = b1.branch_id)"
                  " AND EXISTS (SELECT 1 FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " WHERE l.member_id = m.member_id AND c.branch_id = b2.branch_id))"
                  " FROM branches b1 JOIN branches b2 ON b2.branch_id > b1.branch_id"),
        trap_sql=("SELECT b1.branch_id, b2.branch_id, (SELECT COUNT(*) FROM members m"
                  " WHERE EXISTS (SELECT 1 FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " WHERE l.member_id = m.member_id AND c.branch_id = b1.branch_id)"
                  " AND EXISTS (SELECT 1 FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " WHERE l.member_id = m.member_id AND c.branch_id = b2.branch_id))"
                  " FROM branches b1 JOIN branches b2 ON b2.branch_id <> b1.branch_id"),
        note="The self-join with > makes each pair once; <> makes it"
             " twice, thirty rows for fifteen pairs. The count is a"
             " scalar subquery correlated on BOTH outer rows, and each"
             " EXISTS inside it asks the same question of a different"
             " branch. Members borrow from the whole service, so every"
             " pair shares around a thousand readers.",
        claims=[("fifteen pairs, a thousand or so readers each",
                 lambda rows, c: len(rows) == 15 and all(r[0] < r[1] and 950 < r[2] < 1200 for r in rows))],
    ),
    dict(
        id=6, ledger="Q1047", concept="C7", tier="2 - The branches compared",
        title="Each branch's staff, wage bill and manager",
        prompt=(
            "For each branch: how many staff, the total salary, and the"
            " manager's name -- NULL for the branch with no manager. The"
            " name comes from a conditional aggregate: MAX(CASE WHEN role"
            " = 'manager' THEN name END), which is the one manager's name"
            " or NULL.\n\n"
            "Return: branch_id, staff, salary_bill, manager"
        ),
        solution=("SELECT branch_id, COUNT(*), SUM(salary), MAX(CASE WHEN role = 'manager' THEN name END)"
                  " FROM staff GROUP BY branch_id"),
        trap_sql=("SELECT branch_id, COUNT(*), SUM(salary), MAX(CASE WHEN role = 'manager' THEN name END)"
                  " FROM staff WHERE role = 'manager' GROUP BY branch_id"),
        note="A CASE inside an aggregate picks one row's value out of a"
             " group: the CASE is NULL for everyone but the manager, and"
             " MAX of text ignores NULLs, so the manager's name survives."
             " Filtering to managers in the WHERE would make the staff"
             " count 1 everywhere and lose Old Town altogether.",
        claims=[("six branches, Old Town with no manager",
                 lambda rows, c: len(rows) == 6 and dict((r[0], r[3]) for r in rows)[6] is None
                 and sum(r[1] for r in rows) == 31)],
    ),
    # ==================================================== 3 Authors and titles
    dict(
        id=7, ledger="Q1048", concept="A2", tier="3 - Authors and titles",
        title="The longest writing careers",
        prompt=(
            "The five authors whose books span the most years -- latest"
            " published_year minus earliest -- ties by lower author_id:"
            " author_id, the span, and how many books. GROUP BY author"
            " with MAX minus MIN, ORDER BY and LIMIT.\n\n"
            "Return: author_id, span_years, books"
        ),
        solution=("SELECT author_id, MAX(published_year) - MIN(published_year), COUNT(*) FROM books"
                  " GROUP BY author_id ORDER BY 2 DESC, author_id LIMIT 5"),
        trap_sql=("SELECT author_id, MAX(published_year) - MIN(published_year), COUNT(*) FROM books"
                  " GROUP BY author_id ORDER BY 2 DESC, author_id DESC LIMIT 5"),
        note="Two aggregates of the same column subtracted give a range"
             " per group. Four authors tie on 43 years behind the two on"
             " 44, so the tie-break decides which three of them make the"
             " top five -- the question says lower id first, and a DESC"
             " on the tie-break picks the other three.",
        claims=[("five authors, the top two spanning 44 years",
                 lambda rows, c: len(rows) == 5 and rows[0][1] == 44 and rows[1][1] == 44
                 and [r[0] for r in rows] == [17, 29, 26, 41, 69])],
    ),
    dict(
        id=8, ledger="Q1049", concept="R1", tier="3 - Authors and titles",
        title="The commonest words in the titles",
        prompt=(
            "The ten words that appear in the most titles, ignoring"
            " case, with how many titles each appears in -- ties by the"
            " lower-cased word. A recursive CTE that splits every title"
            " into words (append a trailing space to each title and peel"
            " one word per step with SUBSTR and INSTR), then GROUP BY"
            " LOWER(word) with COUNT(DISTINCT book_id).\n\n"
            "Return: word, titles"
        ),
        solution=("WITH RECURSIVE w(book_id, word, rest) AS (SELECT book_id, '', title || ' ' FROM books"
                  " UNION ALL SELECT book_id, SUBSTR(rest, 1, INSTR(rest, ' ') - 1), SUBSTR(rest, INSTR(rest, ' ') + 1)"
                  " FROM w WHERE rest <> '')"
                  " SELECT LOWER(word), COUNT(DISTINCT book_id) AS n FROM w WHERE word <> ''"
                  " GROUP BY LOWER(word) ORDER BY n DESC, LOWER(word) LIMIT 10"),
        trap_sql=("WITH RECURSIVE w(book_id, word, rest) AS (SELECT book_id, '', title || ' ' FROM books"
                  " UNION ALL SELECT book_id, SUBSTR(rest, 1, INSTR(rest, ' ') - 1), SUBSTR(rest, INSTR(rest, ' ') + 1)"
                  " FROM w WHERE rest <> '')"
                  " SELECT word, COUNT(DISTINCT book_id) AS n FROM w WHERE word <> ''"
                  " GROUP BY word ORDER BY n DESC, word LIMIT 10"),
        note="The recursive split from an earlier set, run over every"
             " title at once by carrying book_id along. LOWER folds 'The'"
             " and 'the' into one word, which the question asks for;"
             " grouped as typed, 'The' and 'the' are two of the top ten"
             " and 'A' and 'a' two more. COUNT(DISTINCT book_id) counts"
             " titles rather than occurrences.",
        claims=[("ten words, 'the' far ahead",
                 lambda rows, c: len(rows) == 10 and rows[0][0] == 'the' and rows[0][1] > 250
                 and all(r[0] == r[0].lower() for r in rows))],
    ),
    dict(
        id=9, ledger="Q1050", concept="STR", tier="3 - Authors and titles",
        title="An author who starts titles the same way",
        prompt=(
            "Author-and-first-word pairs where the author has MORE THAN"
            " ONE book beginning with that word: author_id, the word, how"
            " many books. The first word is SUBSTR up to the space;"
            " GROUP BY both the author and the word, HAVING COUNT(*) >"
            " 1.\n\n"
            "Return: author_id, first_word, books"
        ),
        solution=("SELECT author_id, SUBSTR(title, 1, INSTR(title, ' ') - 1) AS w, COUNT(*) FROM books"
                  " GROUP BY author_id, w HAVING COUNT(*) > 1"),
        trap_sql=("SELECT author_id, SUBSTR(title, 1, INSTR(title, ' ') - 1) AS w, COUNT(*) FROM books"
                  " GROUP BY w HAVING COUNT(*) > 1"),
        note="Grouping by a computed column and a plain one together is"
             " what makes the group 'this author, this first word'."
             " Grouping by the word alone collapses every author into"
             " thirty-three groups with an arbitrary author_id each --"
             " SQLite allows the bare column, which is what makes the"
             " mistake quiet.",
        claims=[("a hundred and thirty or so pairs, 'The' among the words",
                 lambda rows, c: 115 < len(rows) < 145 and all(r[2] > 1 for r in rows)
                 and any(r[1] == 'The' for r in rows))],
    ),
    # ==================================================== 4 Members over time
    dict(
        id=10, ledger="Q1051", concept="W1", tier="4 - Members over time",
        title="Each year's cohort, and how many of them borrow",
        prompt=(
            "For each year members joined: how many joined, the"
            " cumulative membership by the end of that year, and the"
            " percentage of that year's joiners who have ever borrowed,"
            " to one decimal. A window SUM over the grouped counts, and"
            " AVG of an EXISTS over loans for the percentage.\n\n"
            "Return: join_year, joined, cumulative, pct_borrowers"
        ),
        solution=("SELECT strftime('%Y', joined_on) AS y, COUNT(*), SUM(COUNT(*)) OVER (ORDER BY strftime('%Y', joined_on)),"
                  " ROUND(100.0 * AVG(EXISTS (SELECT 1 FROM loans l WHERE l.member_id = m.member_id)), 1)"
                  " FROM members m GROUP BY y"),
        trap_sql=("SELECT strftime('%Y', joined_on) AS y, COUNT(*), SUM(COUNT(*)) OVER (),"
                  " ROUND(100.0 * AVG(EXISTS (SELECT 1 FROM loans l WHERE l.member_id = m.member_id)), 1)"
                  " FROM members m GROUP BY y"),
        note="Two different aggregations over the same group: the window"
             " SUM accumulates the counts across years -- with ORDER BY,"
             " or it is the grand total on every row -- and AVG of the"
             " EXISTS is the fraction of the cohort for whom a loan"
             " exists. Every cohort is around 85 per cent borrowers.",
        claims=[("eleven years, cumulative reaching 1,500",
                 lambda rows, c: len(rows) == 11 and max(r[2] for r in rows) == 1500
                 and all(80 < r[3] < 92 for r in rows))],
    ),
    dict(
        id=11, ledger="Q1052", concept="J2", tier="4 - Members over time",
        title="Northgate's members: active, cooling or dormant",
        prompt=(
            "Branch 2's members in three bands by their most recent loan"
            " as of 2026-06-30: 'active' within the last 90 days,"
            " 'cooling' within 365, 'dormant' otherwise -- INCLUDING"
            " members who have never borrowed. A CTE per member with"
            " MAX(loaned_on) through a LEFT JOIN, then a CASE that tests"
            " the NULL first.\n\n"
            "Return: band, members"
        ),
        solution=("WITH r AS (SELECT m.member_id, MAX(l.loaned_on) AS last FROM members m"
                  " LEFT JOIN loans l ON l.member_id = m.member_id WHERE m.home_branch_id = 2 GROUP BY m.member_id)"
                  " SELECT CASE WHEN last IS NULL OR julianday('2026-06-30') - julianday(last) >= 365 THEN 'dormant'"
                  " WHEN julianday('2026-06-30') - julianday(last) < 90 THEN 'active' ELSE 'cooling' END, COUNT(*)"
                  " FROM r GROUP BY 1"),
        trap_sql=("WITH r AS (SELECT m.member_id, MAX(l.loaned_on) AS last FROM members m"
                  " JOIN loans l ON l.member_id = m.member_id WHERE m.home_branch_id = 2 GROUP BY m.member_id)"
                  " SELECT CASE WHEN last IS NULL OR julianday('2026-06-30') - julianday(last) >= 365 THEN 'dormant'"
                  " WHEN julianday('2026-06-30') - julianday(last) < 90 THEN 'active' ELSE 'cooling' END, COUNT(*)"
                  " FROM r GROUP BY 1"),
        note="The LEFT JOIN gives the never-borrowers a row with a NULL"
             " last loan, and the CASE's first branch sends them to"
             " 'dormant', where the question puts them. An inner join"
             " drops them, and the dormant count falls by the branch's"
             " never-borrowers.",
        claims=[("three bands adding up to Northgate's members",
                 lambda rows, c: len(rows) == 3 and sum(r[1] for r in rows) ==
                 c.execute("SELECT COUNT(*) FROM members WHERE home_branch_id = 2").fetchone()[0]
                 and dict(rows)['dormant'] >= 30)],
    ),
    dict(
        id=12, ledger="Q1053", concept="W1", tier="4 - Members over time",
        title="Membership growth, branch by branch",
        prompt=(
            "For each branch and each year members joined it: how many"
            " joined that year, and the branch's cumulative membership"
            " by then. A window SUM partitioned by branch and ordered by"
            " year, over the grouped counts.\n\n"
            "Return: branch_id, join_year, joined, cumulative"
        ),
        solution=("SELECT home_branch_id, strftime('%Y', joined_on) AS y, COUNT(*),"
                  " SUM(COUNT(*)) OVER (PARTITION BY home_branch_id ORDER BY strftime('%Y', joined_on))"
                  " FROM members GROUP BY home_branch_id, y"),
        trap_sql=("SELECT home_branch_id, strftime('%Y', joined_on) AS y, COUNT(*),"
                  " SUM(COUNT(*)) OVER (ORDER BY strftime('%Y', joined_on))"
                  " FROM members GROUP BY home_branch_id, y"),
        note="PARTITION BY restarts the running total for each branch;"
             " without it the sum runs across all branches in year order,"
             " and -- because several rows share a year -- every branch's"
             " row for that year shows the same service-wide figure. The"
             " last row of each branch should be its member count.",
        claims=[("sixty-six rows, each branch's last cumulative its membership",
                 lambda rows, c: len(rows) == 66
                 and all(max((r[3], r[1]) for r in rows if r[0] == b)[0] ==
                         c.execute("SELECT COUNT(*) FROM members WHERE home_branch_id = ?", (b,)).fetchone()[0]
                         for b in range(1, 7)))],
    ),
    # ================================================= 5 Changing the data
    dict(
        id=13, ledger="Q1054", concept="TRG", tier="5 - Changing the data",
        kind="script",
        title="No fine on a loan that is still out",
        prompt=(
            "Write a BEFORE INSERT trigger on fines that refuses --"
            " RAISE(ABORT, ...) -- a fine whose loan has not been returned:"
            " the loan's returned_on is NULL. The WHEN is an EXISTS over"
            " loans correlated on NEW.loan_id. The question then fines"
            " loan 53, which is out, and loan 1, which came back.\n\n"
            "Checked: the loan_ids of any fines added"
        ),
        solution=("CREATE TRIGGER no_fine_while_out BEFORE INSERT ON fines\n"
                  "WHEN EXISTS (SELECT 1 FROM loans l WHERE l.loan_id = NEW.loan_id AND l.returned_on IS NULL)\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'loan has not been returned');\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER no_fine_while_out BEFORE INSERT ON fines\n"
                  "WHEN EXISTS (SELECT 1 FROM loans l WHERE l.loan_id = NEW.loan_id AND l.returned_on IS NOT NULL)\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'loan has not been returned');\n"
                  "END;"),
        driver_sql=("INSERT INTO fines (loan_id, amount_pence, issued_on) VALUES (53, 100, '2026-07-01');\n"
                    "INSERT INTO fines (loan_id, amount_pence, issued_on) VALUES (1, 100, '2026-07-01');"),
        probe_sql="SELECT loan_id FROM fines WHERE fine_id > 4085 ORDER BY fine_id",
        note="The WHEN reaches into another table through NEW.loan_id,"
             " which is the row about to be inserted. IS NULL is the"
             " condition to refuse; IS NOT NULL refuses the opposite case"
             " and lets the fine on the open loan through while blocking"
             " the legitimate one.",
        claims=[("loan 1 fined, loan 53 refused",
                 lambda rows, c: rows == [(1,)])],
    ),
    dict(
        id=14, ledger="Q1055", concept="DML", tier="5 - Changing the data",
        kind="script",
        title="No queue longer than three",
        prompt=(
            "Cancel, with cancelled_on = '2026-07-01', every OPEN hold"
            " that is beyond position 3 in its book's queue -- the fourth"
            " and later by placed_at. A CTE that numbers the open holds"
            " with ROW_NUMBER partitioned by book, and an UPDATE whose"
            " WHERE is an IN over the hold_ids numbered above 3.\n\n"
            "Checked: how many holds are still open, and the longest"
            " remaining queue"
        ),
        solution=("WITH q AS (SELECT hold_id, ROW_NUMBER() OVER (PARTITION BY book_id ORDER BY placed_at) AS rn\n"
                  "           FROM holds WHERE fulfilled_on IS NULL AND cancelled_on IS NULL)\n"
                  "UPDATE holds SET cancelled_on = '2026-07-01' WHERE hold_id IN (SELECT hold_id FROM q WHERE rn > 3);"),
        trap_sql=("WITH q AS (SELECT hold_id, ROW_NUMBER() OVER (PARTITION BY book_id ORDER BY placed_at) AS rn\n"
                  "           FROM holds WHERE fulfilled_on IS NULL AND cancelled_on IS NULL)\n"
                  "UPDATE holds SET cancelled_on = '2026-07-01' WHERE hold_id IN (SELECT hold_id FROM q WHERE rn >= 3);"),
        probe_sql=("SELECT COUNT(*), (SELECT MAX(n) FROM (SELECT COUNT(*) AS n FROM holds"
                   " WHERE fulfilled_on IS NULL AND cancelled_on IS NULL GROUP BY book_id))"
                   " FROM holds WHERE fulfilled_on IS NULL AND cancelled_on IS NULL"),
        note="The window numbers each queue from 1, and 'beyond position"
             " 3' is rn > 3; rn >= 3 cancels the third person in every"
             " queue as well. Cancelling rather than deleting keeps the"
             " history, which is why the UPDATE sets a date instead of"
             " removing rows.",
        claims=[("forty holds cancelled, no queue longer than three",
                 lambda rows, c: rows == [(337 - 40, 3)])],
    ),
    dict(
        id=15, ledger="Q1056", concept="VIEW", tier="5 - Changing the data",
        kind="script",
        title="A quick way to sign someone up",
        prompt=(
            "Create a view `quick_join (name, home_branch_id)` over"
            " members, and an INSTEAD OF INSERT trigger on it that inserts"
            " into members with NEW.name and NEW.home_branch_id, born_on"
            " '1990-01-01' and joined_on '2026-07-01'. The question then"
            " runs INSERT INTO quick_join (name, home_branch_id) VALUES"
            " ('Ada Lovelace', 1).\n\n"
            "Checked: the name, branch and joined_on of any member added"
        ),
        solution=("CREATE VIEW quick_join AS SELECT name, home_branch_id FROM members;\n"
                  "CREATE TRIGGER quick_join_insert INSTEAD OF INSERT ON quick_join\n"
                  "BEGIN\n"
                  "  INSERT INTO members (name, born_on, joined_on, home_branch_id)\n"
                  "  VALUES (NEW.name, '1990-01-01', '2026-07-01', NEW.home_branch_id);\n"
                  "END;"),
        trap_sql="CREATE VIEW quick_join AS SELECT name, home_branch_id FROM members;",
        driver_sql="INSERT INTO quick_join (name, home_branch_id) VALUES ('Ada Lovelace', 1);",
        probe_sql="SELECT name, home_branch_id, joined_on FROM members WHERE member_id > 1500",
        note="An INSTEAD OF INSERT trigger makes a view accept rows: NEW"
             " carries the view's columns, and the trigger body supplies"
             " whatever else the real table requires. Without it the"
             " question's INSERT is refused as an insert into a view,"
             " and nobody is added.",
        claims=[("Ada Lovelace at Central, joined 2026-07-01",
                 lambda rows, c: rows == [('Ada Lovelace', 1, '2026-07-01')])],
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
