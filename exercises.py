"""Practice exercises: fifteen questions on the library schema.

A NEW schema -- a public library service, after the college, the workshop,
the railway and the hospital -- with the hospital's shapes carried over
(intervals with open ends, two foreign keys to one table, a category with
a natural order) and two of its own: QUEUES, in the holds a member places
on a book, and MONEY OWED, in the fines a late return raises. SEED 861.
Twelve SELECT questions at the level of the last hospital sets -- copies
per genre with the books that have none, heavy borrowers in HAVING,
titles beginning with The, the queue for one book, late returns by month,
what is overdue today, what was out on a date, how long a hold waits, two
children of one book, loans away from home, the most borrowed book per
genre, and each branch's genre mix -- and three WRITABLE questions:

  * a BEFORE INSERT trigger that reads the member's unpaid fines
  * an UPDATE that pays off the small fines, with the WHERE that matters
  * a view of the copies that are actually available

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference. A `driver_sql`, where present, is what the
question itself runs AFTER your script -- the loans your trigger should
sort.
"""

import sqlite3

EXERCISES = [
    # ========================================================== 1 Warm-up
    dict(
        id=1, ledger="Q847", concept="A2", tier="1 - Warm-up",
        title="Copies per title, by genre",
        prompt=(
            "For each genre: how many books -- titles -- the catalogue"
            " lists, how many physical copies there are of them, and"
            " copies per title to one decimal. Twenty titles have no"
            " copies at all and still count as titles.\n\n"
            "Return: genre, titles, copies, per_title"
        ),
        solution=("SELECT b.genre, COUNT(DISTINCT b.book_id), COUNT(c.copy_id),"
                  " ROUND(1.0 * COUNT(c.copy_id) / COUNT(DISTINCT b.book_id), 1)"
                  " FROM books b LEFT JOIN copies c ON c.book_id = b.book_id GROUP BY b.genre"),
        trap_sql=("SELECT b.genre, COUNT(DISTINCT b.book_id), COUNT(c.copy_id),"
                  " ROUND(1.0 * COUNT(c.copy_id) / COUNT(DISTINCT b.book_id), 1)"
                  " FROM books b JOIN copies c ON c.book_id = b.book_id GROUP BY b.genre"),
        note="A new schema, the same first lesson as every one before it:"
             " the join decides who is counted. An inner join drops the"
             " titles with no copies, so the title count is short and the"
             " ratio is high. LEFT JOIN keeps them with a NULL copy_id,"
             " which COUNT(c.copy_id) ignores and COUNT(DISTINCT"
             " b.book_id) does not.",
        claims=[("eight genres, three to four copies a title",
                 lambda rows, c: len(rows) == 8
                 and all(3 < r[3] < 4.5 for r in rows)
                 and sum(r[1] for r in rows) == 600)],
    ),
    dict(
        id=2, ledger="Q848", concept="A3", tier="1 - Warm-up",
        title="Heavy borrowers, often late",
        prompt=(
            "Members with at least 200 loans, at least 40 of which came"
            " back late -- returned after due_on: member_id, loans, late,"
            " and the late percentage to one decimal. A loan still out is"
            " not late by this test.\n\n"
            "Return: member_id, loans, late, pct_late"
        ),
        solution=("SELECT member_id, COUNT(*), SUM(returned_on > due_on),"
                  " ROUND(100.0 * SUM(returned_on > due_on) / COUNT(*), 1) FROM loans"
                  " GROUP BY member_id HAVING COUNT(*) >= 200 AND SUM(returned_on > due_on) >= 40"),
        trap_sql=("SELECT member_id, COUNT(*), COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / COUNT(*), 1) FROM loans"
                  " WHERE returned_on > due_on GROUP BY member_id"
                  " HAVING COUNT(*) >= 40"),
        note="returned_on > due_on is NULL for a loan still out, and SUM"
             " skips it, so 'late' counts exactly the returned-late loans"
             " with no extra condition. Both thresholds are on aggregates,"
             " so both live in HAVING; filtering to the late loans first"
             " loses the total and makes every member 100 per cent late."
             " Thirty heavy readers exist in the data; this keeps seven.",
        claims=[("a handful of members, a fifth of their loans late",
                 lambda rows, c: 3 <= len(rows) <= 8
                 and all(r[1] >= 200 and r[2] >= 40 and 15 < r[3] < 30 for r in rows))],
    ),
    # ======================================== 2 Strings and sequences
    dict(
        id=3, ledger="Q849", concept="STR", tier="2 - Strings and sequences",
        title="Titles that begin with The",
        prompt=(
            "For each genre: how many titles, how many of them BEGIN with"
            " the word 'The', and the percentage to one decimal. 'Beyond"
            " the Door' does not begin with The.\n\n"
            "Return: genre, titles, the_titles, pct"
        ),
        solution=("SELECT genre, COUNT(*), SUM(title LIKE 'The %'),"
                  " ROUND(100.0 * SUM(title LIKE 'The %') / COUNT(*), 1) FROM books"
                  " GROUP BY genre"),
        trap_sql=("SELECT genre, COUNT(*), SUM(title LIKE '%the%'),"
                  " ROUND(100.0 * SUM(title LIKE '%the%') / COUNT(*), 1) FROM books"
                  " GROUP BY genre"),
        note="LIKE 'The %' anchors the pattern at the start and requires"
             " the space, so 'Theory' would not match either. '%the%'"
             " matches anywhere, and since LIKE ignores case for ASCII it"
             " also catches 'Beyond the Door' and 'Notes from the Glass"
             " Harbour' -- half the catalogue. GLOB 'The *' is the"
             " case-sensitive spelling.",
        claims=[("eight genres, a fifth to two fifths beginning with The",
                 lambda rows, c: len(rows) == 8
                 and all(15 < r[3] < 45 for r in rows))],
    ),
    dict(
        id=4, ledger="Q850", concept="SEQ", tier="2 - Strings and sequences",
        title="The queue for book 587",
        prompt=(
            "The members still WAITING for book 587 -- holds neither"
            " fulfilled nor cancelled -- in the order they placed their"
            " hold, with their position in the queue, 1 for the front."
            " Order is placed_at.\n\n"
            "Return: position, member_id, placed_at"
        ),
        solution=("SELECT ROW_NUMBER() OVER (ORDER BY placed_at), member_id, placed_at"
                  " FROM holds WHERE book_id = 587 AND fulfilled_on IS NULL"
                  " AND cancelled_on IS NULL"),
        trap_sql=("SELECT ROW_NUMBER() OVER (ORDER BY placed_at), member_id, placed_at"
                  " FROM holds WHERE book_id = 587"),
        note="A queue is an ordered sequence, and ROW_NUMBER over placed_at"
             " numbers it. Who is IN the queue is the WHERE: a hold that"
             " was fulfilled or cancelled has left it. Count those too and"
             " the positions are inflated by people who are no longer"
             " waiting. Two NULL tests, because a hold can end either way.",
        claims=[("seven waiting, numbered 1 to 7",
                 lambda rows, c: len(rows) == 7
                 and sorted(r[0] for r in rows) == list(range(1, 8)))],
    ),
    # ============================================== 3 Dates and times
    dict(
        id=5, ledger="Q851", concept="D1", tier="3 - Dates and times",
        title="Late returns by month",
        prompt=(
            "For each month of RETURN, 'YYYY-MM': how many loans came back,"
            " how many came back after their due_on, and the percentage to"
            " one decimal. due_on already includes any renewals.\n\n"
            "Return: month, returns, late, pct_late"
        ),
        solution=("SELECT strftime('%Y-%m', returned_on), COUNT(*), SUM(returned_on > due_on),"
                  " ROUND(100.0 * SUM(returned_on > due_on) / COUNT(*), 1) FROM loans"
                  " WHERE returned_on IS NOT NULL GROUP BY 1"),
        trap_sql=("SELECT strftime('%Y-%m', returned_on), COUNT(*),"
                  " SUM(returned_on > date(loaned_on, '+21 days')),"
                  " ROUND(100.0 * SUM(returned_on > date(loaned_on, '+21 days')) / COUNT(*), 1)"
                  " FROM loans WHERE returned_on IS NOT NULL GROUP BY 1"),
        note="The due date is a column, and it is the one to compare with,"
             " because a renewal moved it. Recomputing it as loan date plus"
             " three weeks ignores the renewals and calls a third of the"
             " on-time returns late. Group by the month of the event the"
             " question is about -- the return -- not the loan.",
        claims=[("eighteen months, a fifth or so late",
                 lambda rows, c: len(rows) == 18
                 and all(0 < r[3] < 30 for r in rows))],
    ),
    dict(
        id=6, ledger="Q852", concept="D2", tier="3 - Dates and times",
        title="Overdue at the end of the data",
        prompt=(
            "As of 2026-06-30, per branch holding the copy: how many loans"
            " are still out AND past their due date, and the most days"
            " overdue among them, as a whole number. A loan is overdue"
            " when returned_on is NULL and due_on is before that day.\n\n"
            "Return: branch_id, overdue, max_days_over"
        ),
        solution=("SELECT c.branch_id, COUNT(*),"
                  " CAST(MAX(julianday('2026-06-30') - julianday(l.due_on)) AS INTEGER)"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " WHERE l.returned_on IS NULL AND l.due_on < '2026-06-30' GROUP BY c.branch_id"),
        trap_sql=("SELECT c.branch_id, COUNT(*),"
                  " CAST(MAX(julianday('2026-06-30') - julianday(l.due_on)) AS INTEGER)"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " WHERE l.returned_on IS NULL GROUP BY c.branch_id"),
        note="'Still out' and 'past due' are two conditions, and the second"
             " is the one that makes it overdue: most open loans are simply"
             " not back yet. Without the due_on test the counts are five"
             " times higher and the maximum goes negative -- a loan due"
             " next week is minus seven days over. The branch comes from"
             " the copy, since the loan has no branch of its own.",
        claims=[("six branches, dozens overdue, weeks over at most",
                 lambda rows, c: len(rows) == 6
                 and all(5 < r[1] < 40 and 20 < r[2] < 90 for r in rows))],
    ),
    # ==================================== 4 Intervals and queues
    dict(
        id=7, ledger="Q853", concept="INT", tier="4 - Intervals and queues",
        title="On the shelf in mid-June",
        prompt=(
            "For each branch on 2026-06-15: how many of its copies were"
            " on the books -- not withdrawn by then -- how many of those"
            " were out on loan that day, and how many were available. A"
            " copy is out on a day if a loan of it started on or before"
            " the day and had not been returned before it; NULL"
            " returned_on means not yet returned.\n\n"
            "Return: branch_id, copies, on_loan, available"
        ),
        solution=("SELECT c.branch_id, COUNT(*), SUM(EXISTS (SELECT 1 FROM loans l"
                  " WHERE l.copy_id = c.copy_id AND l.loaned_on <= '2026-06-15'"
                  " AND COALESCE(l.returned_on, '9999') > '2026-06-15')),"
                  " COUNT(*) - SUM(EXISTS (SELECT 1 FROM loans l WHERE l.copy_id = c.copy_id"
                  " AND l.loaned_on <= '2026-06-15' AND COALESCE(l.returned_on, '9999')"
                  " > '2026-06-15')) FROM copies c WHERE c.withdrawn_on IS NULL"
                  " OR c.withdrawn_on > '2026-06-15' GROUP BY c.branch_id"),
        trap_sql=("SELECT c.branch_id, COUNT(*), SUM(EXISTS (SELECT 1 FROM loans l"
                  " WHERE l.copy_id = c.copy_id AND l.loaned_on <= '2026-06-15'"
                  " AND l.returned_on > '2026-06-15')),"
                  " COUNT(*) - SUM(EXISTS (SELECT 1 FROM loans l WHERE l.copy_id = c.copy_id"
                  " AND l.loaned_on <= '2026-06-15' AND l.returned_on > '2026-06-15'))"
                  " FROM copies c WHERE c.withdrawn_on IS NULL"
                  " OR c.withdrawn_on > '2026-06-15' GROUP BY c.branch_id"),
        note="A day inside an interval, per copy, as an EXISTS that SUM"
             " can count: the loan began on or before the day and had not"
             " ended. The open end is the trap again -- a loan not yet"
             " returned has NULL returned_on, and NULL > day is not true,"
             " so without COALESCE every copy out on an unreturned loan"
             " looks available. Withdrawn copies leave the denominator"
             " by the WHERE.",
        claims=[("six branches, about a third of copies out",
                 lambda rows, c: len(rows) == 6
                 and all(0.25 < r[2] / r[1] < 0.45 and r[1] == r[2] + r[3] for r in rows))],
    ),
    dict(
        id=8, ledger="Q854", concept="INT", tier="4 - Intervals and queues",
        title="How long a hold waits",
        prompt=(
            "For each pickup branch: how many holds have been FULFILLED,"
            " and the average wait in days from the day the hold was"
            " placed to the day it was fulfilled, to one decimal."
            " placed_at is a datetime; cut it to its date first.\n\n"
            "Return: branch_id, fulfilled, avg_wait_days"
        ),
        solution=("SELECT branch_id, COUNT(*), ROUND(AVG(julianday(fulfilled_on)"
                  " - julianday(date(placed_at))), 1) FROM holds"
                  " WHERE fulfilled_on IS NOT NULL GROUP BY branch_id"),
        trap_sql=("SELECT branch_id, COUNT(*), ROUND(AVG(julianday(COALESCE(fulfilled_on,"
                  " cancelled_on)) - julianday(date(placed_at))), 1) FROM holds"
                  " WHERE fulfilled_on IS NOT NULL OR cancelled_on IS NOT NULL GROUP BY branch_id"),
        note="A hold ends one of two ways, and the question is about one"
             " of them. Folding the cancellations in with COALESCE measures"
             " how long people waited before giving up as well, and counts"
             " them as fulfilled. date(placed_at) drops the time of day so"
             " the difference is in whole days, as the fulfilment date is.",
        claims=[("six branches, about three weeks' wait",
                 lambda rows, c: len(rows) == 6
                 and all(15 < r[2] < 25 for r in rows))],
    ),
    # ============================================== 5 Joins and grain
    dict(
        id=9, ledger="Q855", concept="C2", tier="5 - Joins and grain",
        title="Copies and holds, per genre",
        prompt=(
            "For each genre: how many copies its books have, and how many"
            " holds have ever been placed on them. Both hang off books."
            " Joining both at once multiplies each by the other.\n\n"
            "Return: genre, copies, holds"
        ),
        solution=("SELECT b.genre, (SELECT COUNT(*) FROM copies c JOIN books x"
                  " ON x.book_id = c.book_id WHERE x.genre = b.genre),"
                  " (SELECT COUNT(*) FROM holds h JOIN books x ON x.book_id = h.book_id"
                  " WHERE x.genre = b.genre) FROM books b GROUP BY b.genre"),
        trap_sql=("SELECT b.genre, COUNT(c.copy_id), COUNT(h.hold_id) FROM books b"
                  " LEFT JOIN copies c ON c.book_id = b.book_id"
                  " LEFT JOIN holds h ON h.book_id = b.book_id GROUP BY b.genre"),
        note="Two children of one parent, joined at once, make a product:"
             " a book with four copies and ten holds becomes forty rows,"
             " and each count is multiplied by the other. Count each child"
             " on its own -- a correlated subquery per column, or two"
             " pre-aggregated CTEs joined on genre -- and only then put"
             " the numbers side by side.",
        claims=[("eight genres, more copies than holds in each",
                 lambda rows, c: len(rows) == 8
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM copies").fetchone()[0]
                 and sum(r[2] for r in rows) == 1500)],
    ),
    dict(
        id=10, ledger="Q856", concept="J2", tier="5 - Joins and grain",
        title="Borrowed away from home",
        prompt=(
            "For each HOME branch of the members: how many loans its"
            " members have taken, how many of those were of a copy held"
            " at a DIFFERENT branch, and the percentage to one decimal."
            " The copy's branch and the member's home branch are two"
            " foreign keys to the same table.\n\n"
            "Return: home_branch_id, loans, away, pct_away"
        ),
        solution=("SELECT m.home_branch_id, COUNT(*), SUM(c.branch_id <> m.home_branch_id),"
                  " ROUND(100.0 * SUM(c.branch_id <> m.home_branch_id) / COUNT(*), 1)"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " JOIN members m ON m.member_id = l.member_id GROUP BY m.home_branch_id"),
        trap_sql=("SELECT c.branch_id, COUNT(*), SUM(c.branch_id <> m.home_branch_id),"
                  " ROUND(100.0 * SUM(c.branch_id <> m.home_branch_id) / COUNT(*), 1)"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " JOIN members m ON m.member_id = l.member_id GROUP BY c.branch_id"),
        note="Two paths to branches, one through the copy and one through"
             " the member, and the comparison between them needs no third"
             " join. The grouping decides what the row means: by the"
             " member's home branch it is 'how far my members roam', by"
             " the copy's branch it is 'who borrows from this branch' --"
             " the same numbers in different rows.",
        claims=[("six branches, most loans away from home",
                 lambda rows, c: len(rows) == 6
                 and all(75 < r[3] < 90 for r in rows))],
    ),
    # ============================================== 6 Window functions
    dict(
        id=11, ledger="Q857", concept="W2", tier="6 - Window functions",
        title="The most borrowed title in each genre",
        prompt=(
            "For each genre, the title whose copies have been loaned the"
            " most times, with that count; ties by title alphabetically."
            " Loans attach to copies, copies to books.\n\n"
            "Return: genre, title, loans"
        ),
        solution=("SELECT genre, title, n FROM (SELECT b.genre, b.title, COUNT(*) n,"
                  " ROW_NUMBER() OVER (PARTITION BY b.genre ORDER BY COUNT(*) DESC, b.title) rn"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " JOIN books b ON b.book_id = c.book_id GROUP BY b.book_id) WHERE rn = 1"),
        trap_sql=("SELECT genre, title, n FROM (SELECT b.genre, b.title, COUNT(*) n,"
                  " ROW_NUMBER() OVER (PARTITION BY b.genre ORDER BY COUNT(*), b.title) rn"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " JOIN books b ON b.book_id = c.book_id GROUP BY b.book_id) WHERE rn = 1"),
        note="Aggregate to one row per book, then rank within the genre"
             " and keep the first: top-1 per group through two joins."
             " ORDER BY COUNT(*) inside the window is allowed because the"
             " window runs after GROUP BY. Without DESC the least borrowed"
             " title wins. The tie-break on title makes the answer"
             " deterministic even where two titles share a count.",
        claims=[("eight genres, around a hundred loans each",
                 lambda rows, c: len(rows) == 8
                 and all(80 < r[2] < 120 for r in rows))],
    ),
    dict(
        id=12, ledger="Q858", concept="W3", tier="6 - Window functions",
        title="Each branch's genre mix",
        prompt=(
            "For every branch (of the copy) and genre: how many loans,"
            " and what percentage of THAT BRANCH's loans they are, to one"
            " decimal. Each branch's eight shares add to 100.\n\n"
            "Return: branch_id, genre, loans, pct_of_branch"
        ),
        solution=("SELECT c.branch_id, b.genre, COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY c.branch_id), 1)"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " JOIN books b ON b.book_id = c.book_id GROUP BY c.branch_id, b.genre"),
        trap_sql=("SELECT c.branch_id, b.genre, COUNT(*),"
                  " ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " JOIN books b ON b.book_id = c.book_id GROUP BY c.branch_id, b.genre"),
        note="SUM(COUNT(*)) OVER (PARTITION BY branch) is the branch's"
             " total, repeated on each of its eight rows, so the division"
             " is a share of the branch. An empty OVER () is the whole"
             " library's total, and the shares add to 100 across all"
             " forty-eight rows instead of within each branch.",
        claims=[("forty-eight rows, each branch adding to 100",
                 lambda rows, c: len(rows) == 48
                 and all(abs(sum(r[3] for r in rows if r[0] == b) - 100) < 0.5
                         for b in range(1, 7)))],
    ),
    # ============================================= 7 Changing the data
    dict(
        id=13, ledger="Q859", concept="TRG", tier="7 - Changing the data",
        kind="script",
        title="No new loans while fines are owed",
        prompt=(
            "Write a BEFORE INSERT trigger on loans that refuses a loan"
            " -- RAISE(ABORT, ...) -- when the member's UNPAID fines add"
            " up to 500 pence or more. Fines hang off loans, so the sum"
            " joins fines to loans by member. After your script, the"
            " question inserts a loan of copy 1 for member 1149, who owes"
            " a lot, and a loan of copy 2 for member 11, whose fines are"
            " all paid.\n\n"
            "Checked: which of the two loans exist"
        ),
        solution=("CREATE TRIGGER no_loan_with_debt BEFORE INSERT ON loans\n"
                  "WHEN (SELECT COALESCE(SUM(f.amount_pence), 0) FROM fines f\n"
                  "      JOIN loans l ON l.loan_id = f.loan_id\n"
                  "      WHERE l.member_id = NEW.member_id AND f.paid_on IS NULL) >= 500\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'member has unpaid fines');\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER no_loan_with_debt BEFORE INSERT ON loans\n"
                  "WHEN (SELECT COALESCE(SUM(f.amount_pence), 0) FROM fines f\n"
                  "      JOIN loans l ON l.loan_id = f.loan_id\n"
                  "      WHERE l.member_id = NEW.member_id) >= 500\n"
                  "BEGIN\n"
                  "  SELECT RAISE(ABORT, 'member has unpaid fines');\n"
                  "END;"),
        driver_sql=("INSERT INTO loans (copy_id, member_id, loaned_on, due_on)"
                    " VALUES (1, 1149, '2026-07-01', '2026-07-22');\n"
                    "INSERT INTO loans (copy_id, member_id, loaned_on, due_on)"
                    " VALUES (2, 11, '2026-07-01', '2026-07-22');"),
        probe_sql=("SELECT member_id FROM loans WHERE loan_id > 23976 ORDER BY loan_id"),
        note="A rule that spans three tables is a trigger with a subquery"
             " in its WHEN: the row about to be inserted, NEW, supplies the"
             " member, and the sum is of that member's fines. The word"
             " that matters is UNPAID -- paid_on IS NULL -- and without it"
             " a member who settled every fine is refused along with the"
             " debtor. COALESCE(SUM(...), 0) handles a member with no"
             " fines at all, whose SUM is NULL.",
        claims=[("the debtor refused, the clean member served",
                 lambda rows, c: rows == [(11,)])],
    ),
    dict(
        id=14, ledger="Q860", concept="DML", tier="7 - Changing the data",
        kind="script",
        title="Write off the small change",
        prompt=(
            "Mark every UNPAID fine of 100 pence or less as paid on"
            " '2026-07-01' -- an amnesty on small debts -- and nothing"
            " else. Fines already paid keep their own paid_on.\n\n"
            "Checked: how many fines are still unpaid, what they add up"
            " to, and how many fines carry the amnesty date"
        ),
        solution=("UPDATE fines SET paid_on = '2026-07-01'"
                  " WHERE paid_on IS NULL AND amount_pence <= 100;"),
        trap_sql="UPDATE fines SET paid_on = '2026-07-01' WHERE amount_pence <= 100;",
        probe_sql=("SELECT (SELECT COUNT(*) FROM fines WHERE paid_on IS NULL),"
                   " (SELECT SUM(amount_pence) FROM fines WHERE paid_on IS NULL),"
                   " (SELECT COUNT(*) FROM fines WHERE paid_on = '2026-07-01')"),
        note="Two conditions, and the one that is easy to forget is paid_on"
             " IS NULL: without it the UPDATE rewrites the payment date of"
             " every small fine that was already paid, destroying history,"
             " while the unpaid count comes out the same. The probe checks"
             " how many rows carry the amnesty date for exactly that"
             " reason. An UPDATE's WHERE is about which rows, not just"
             " which values.",
        claims=[("a thousand or so still unpaid, 361 written off",
                 lambda rows, c: rows[0][2] == 361 and rows[0][0] == 1380 - 361)],
    ),
    dict(
        id=15, ledger="Q861", concept="VIEW", tier="7 - Changing the data",
        kind="script",
        title="What is actually on the shelf",
        prompt=(
            "Create a view `available_copies (copy_id, book_id, branch_id)`"
            " of the copies that can be borrowed right now: not withdrawn,"
            " and not out on a loan that has no returned_on.\n\n"
            "Checked: how many copies the view holds, and how many of"
            " them are withdrawn or out"
        ),
        solution=("CREATE VIEW available_copies AS\n"
                  "  SELECT c.copy_id, c.book_id, c.branch_id FROM copies c\n"
                  "  WHERE c.withdrawn_on IS NULL\n"
                  "    AND NOT EXISTS (SELECT 1 FROM loans l\n"
                  "                    WHERE l.copy_id = c.copy_id AND l.returned_on IS NULL);"),
        trap_sql=("CREATE VIEW available_copies AS\n"
                  "  SELECT c.copy_id, c.book_id, c.branch_id FROM copies c\n"
                  "  WHERE NOT EXISTS (SELECT 1 FROM loans l\n"
                  "                    WHERE l.copy_id = c.copy_id AND l.returned_on IS NULL);"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM available_copies),"
                   " (SELECT COUNT(*) FROM available_copies v JOIN copies c ON c.copy_id = v.copy_id"
                   " WHERE c.withdrawn_on IS NOT NULL OR EXISTS (SELECT 1 FROM loans l"
                   " WHERE l.copy_id = v.copy_id AND l.returned_on IS NULL))"),
        note="A view is the right home for a rule the whole library needs"
             " to agree on: 'available' means two things, and a query"
             " that remembers one of them puts withdrawn copies on the"
             " shelf. The NOT EXISTS against open loans is the interval"
             " test at the snapshot; the withdrawn_on IS NULL is the other"
             " half. The second probe column should be 0 -- nothing in"
             " the view fails either test.",
        claims=[("fourteen hundred or so available, none of them withdrawn or out",
                 lambda rows, c: rows == [(1425, 0)])],
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
