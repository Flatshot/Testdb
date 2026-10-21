"""Practice exercises: fifteen questions on the library schema.

The thirteenth set on the library (SEED 861), two tools per question, with
the TIERS named by task rather than by tool. Queues -- the holds: a
position by ROW_NUMBER with a wait by julianday, queue lengths beside an
availability EXISTS, fulfilment by month of placement. Money owed -- the
fines: the biggest debtors with a cumulative share, how fast fines are
paid by CASE over a date difference, members who owe more than they have
paid by two conditional SUMs in HAVING. Stock on the shelf -- the copies:
availability as a SUM of a two-part test, books held at one branch only
through a bare column, condition shares as a JSON object. Who reads what
-- the members: a favourite genre by ROW_NUMBER over a grouped CTE,
readers of every genre, loans per member by age band with the
never-borrowers kept. And three WRITABLE questions in two steps each:

  * a trigger that fulfils the oldest waiting hold when a copy comes back
  * an UPDATE that caps a fine, scoped by a join through a subquery
  * an INSERT ... SELECT driven by a HAVING and a NOT EXISTS

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
    # =============================================================== 1 Queues
    dict(
        id=1, ledger="Q1027", concept="W2", tier="1 - Queues",
        title="The queue for book 587, with the wait so far",
        prompt=(
            "The open holds on book 587 -- fulfilled_on and cancelled_on"
            " both NULL -- each with its position in the queue, 1 for the"
            " earliest placed_at, and the whole days it has waited up to"
            " 2026-06-30. ROW_NUMBER for the position, julianday for the"
            " wait.\n\n"
            "Return: hold_id, position, days_waiting"
        ),
        solution=("SELECT hold_id, ROW_NUMBER() OVER (ORDER BY placed_at),"
                  " CAST(julianday('2026-06-30') - julianday(placed_at) AS INTEGER)"
                  " FROM holds WHERE book_id = 587 AND fulfilled_on IS NULL AND cancelled_on IS NULL"),
        trap_sql=("SELECT hold_id, ROW_NUMBER() OVER (ORDER BY placed_at DESC),"
                  " CAST(julianday('2026-06-30') - julianday(placed_at) AS INTEGER)"
                  " FROM holds WHERE book_id = 587 AND fulfilled_on IS NULL AND cancelled_on IS NULL"),
        note="A queue is a window ordered by arrival: the earliest"
             " placed_at is position 1, so the ORDER BY is ascending, and"
             " DESC puts the newest arrival at the front. julianday"
             " against the end of the data gives the wait, and CAST"
             " drops the fraction the time of day leaves.",
        claims=[("seven in the queue, the first waiting over a year",
                 lambda rows, c: len(rows) == 7 and max(r[2] for r in rows) > 500
                 and min(rows, key=lambda r: r[1])[2] == max(r[2] for r in rows))],
    ),
    dict(
        id=2, ledger="Q1028", concept="E1", tier="1 - Queues",
        title="Long queues, and whether a copy is free",
        prompt=(
            "Books with three or more open holds: book_id, how many are"
            " waiting, and 1 or 0 for whether a copy of the book is"
            " available right now -- not withdrawn and with no open loan."
            " A GROUP BY with HAVING over holds, and an EXISTS in the"
            " SELECT list that contains a NOT EXISTS.\n\n"
            "Return: book_id, waiting, has_available"
        ),
        solution=("SELECT h.book_id, COUNT(*), EXISTS (SELECT 1 FROM copies c WHERE c.book_id = h.book_id"
                  " AND c.withdrawn_on IS NULL AND NOT EXISTS (SELECT 1 FROM loans l WHERE l.copy_id = c.copy_id"
                  " AND l.returned_on IS NULL)) FROM holds h"
                  " WHERE h.fulfilled_on IS NULL AND h.cancelled_on IS NULL GROUP BY h.book_id HAVING COUNT(*) >= 3"),
        trap_sql=("SELECT h.book_id, COUNT(*), EXISTS (SELECT 1 FROM copies c WHERE c.book_id = h.book_id"
                  " AND NOT EXISTS (SELECT 1 FROM loans l WHERE l.copy_id = c.copy_id"
                  " AND l.returned_on IS NULL)) FROM holds h"
                  " WHERE h.fulfilled_on IS NULL AND h.cancelled_on IS NULL GROUP BY h.book_id HAVING COUNT(*) >= 3"),
        note="An EXISTS can sit in the SELECT list of a grouped query"
             " when it refers only to the grouping column, and it returns"
             " 1 or 0. 'Available' is two conditions, and a withdrawn"
             " copy has no open loan precisely because it cannot be lent"
             " -- so without the withdrawn test one book looks available"
             " that is not.",
        claims=[("fifty-six long queues, three with nothing available",
                 lambda rows, c: len(rows) == 56 and sum(r[2] == 0 for r in rows) == 3
                 and all(r[1] >= 3 for r in rows))],
    ),
    dict(
        id=3, ledger="Q1029", concept="D1", tier="1 - Queues",
        title="How long holds took, by the month they were placed",
        prompt=(
            "For each month holds were placed -- strftime of placed_at --"
            " how many of those holds have been fulfilled, and their"
            " average wait in days to one decimal: AVG of julianday("
            "fulfilled_on) minus julianday(placed_at), which skips the"
            " holds never fulfilled on its own.\n\n"
            "Return: month, fulfilled, avg_days"
        ),
        solution=("SELECT strftime('%Y-%m', placed_at), COUNT(fulfilled_on),"
                  " ROUND(AVG(julianday(fulfilled_on) - julianday(placed_at)), 1) FROM holds GROUP BY 1"),
        trap_sql=("SELECT strftime('%Y-%m', placed_at), COUNT(fulfilled_on),"
                  " ROUND(AVG(julianday(placed_at) - julianday(fulfilled_on)), 1) FROM holds GROUP BY 1"),
        note="Two date tools: strftime to group, julianday to measure."
             " The subtraction has to run end minus start, or every wait"
             " is negative. COUNT(fulfilled_on) and AVG over the"
             " fulfilled_on difference agree on which holds count,"
             " because both ignore the NULLs of the open and cancelled"
             " ones.",
        claims=[("eighteen months, waits of two to three weeks",
                 lambda rows, c: len(rows) == 18 and all(10 < r[2] < 30 for r in rows if r[2] is not None)
                 and sum(r[1] for r in rows) == 863)],
    ),
    # =========================================================== 2 Money owed
    dict(
        id=4, ledger="Q1030", concept="W1", tier="2 - Money owed",
        title="The five biggest debtors and their share of the debt",
        prompt=(
            "The five members who owe the most in unpaid fines, ties by"
            " lower member_id: member_id, pence owed, and the cumulative"
            " percentage of ALL unpaid pence that the debtors so far"
            " account for, to one decimal. A CTE of unpaid totals per"
            " member, a running SUM ordered by owed descending, the"
            " grand total as a scalar subquery, and LIMIT 5.\n\n"
            "Return: member_id, owed, cum_pct"
        ),
        solution=("WITH d AS (SELECT l.member_id, SUM(f.amount_pence) AS owed FROM fines f"
                  " JOIN loans l ON l.loan_id = f.loan_id WHERE f.paid_on IS NULL GROUP BY l.member_id)"
                  " SELECT member_id, owed, ROUND(100.0 * SUM(owed) OVER (ORDER BY owed DESC, member_id)"
                  " / (SELECT SUM(owed) FROM d), 1) FROM d ORDER BY owed DESC, member_id LIMIT 5"),
        trap_sql=("WITH d AS (SELECT l.member_id, SUM(f.amount_pence) AS owed FROM fines f"
                  " JOIN loans l ON l.loan_id = f.loan_id WHERE f.paid_on IS NULL GROUP BY l.member_id)"
                  " SELECT member_id, owed, ROUND(100.0 * SUM(owed) OVER ()"
                  " / (SELECT SUM(owed) FROM d), 1) FROM d ORDER BY owed DESC, member_id LIMIT 5"),
        note="The running SUM needs an ORDER BY in its window to be"
             " running; OVER () is the grand total on every row, and"
             " every cumulative share reads 100. The window runs over ALL"
             " debtors before LIMIT keeps five, which is right: the share"
             " is of the whole debt, not of the top five's.",
        claims=[("five debtors, 1149 first, together under a tenth of the debt",
                 lambda rows, c: len(rows) == 5 and rows[0][0] == 1149 if False else
                 len(rows) == 5 and max(r[2] for r in rows) < 10 and (1149, 6480, 1.6) in rows)],
    ),
    dict(
        id=5, ledger="Q1031", concept="C7", tier="2 - Money owed",
        title="How quickly fines get paid",
        prompt=(
            "Every fine in one of three classes with its count: 'unpaid'"
            " when paid_on is NULL, 'within a week' when paid within 7"
            " days of issue -- julianday(paid_on) minus julianday("
            "issued_on) at most 7 -- and 'later' otherwise. The NULL test"
            " goes first in the CASE.\n\n"
            "Return: speed, fines"
        ),
        solution=("SELECT CASE WHEN paid_on IS NULL THEN 'unpaid'"
                  " WHEN julianday(paid_on) - julianday(issued_on) <= 7 THEN 'within a week'"
                  " ELSE 'later' END, COUNT(*) FROM fines GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN julianday(paid_on) - julianday(issued_on) <= 7 THEN 'within a week'"
                  " ELSE 'later' END, COUNT(*) FROM fines GROUP BY 1"),
        note="An unpaid fine has no paid_on, so its date difference is"
             " NULL, and NULL <= 7 is neither true nor false: the CASE"
             " passes it by and the ELSE catches it, labelling 1,380"
             " unpaid fines as paid 'later'. The IS NULL test has to be"
             " a branch of its own, and first is the safe place for it.",
        claims=[("three classes, most paid fines paid later than a week",
                 lambda rows, c: len(rows) == 3 and dict(rows)['unpaid'] == 1380
                 and dict(rows)['later'] > dict(rows)['within a week'])],
    ),
    dict(
        id=6, ledger="Q1032", concept="A3", tier="2 - Money owed",
        title="Members who owe more than they have ever paid",
        prompt=(
            "Members whose UNPAID fines add up to more pence than their"
            " PAID fines: member_id, unpaid pence, paid pence. Two"
            " conditional SUMs -- CASE on paid_on, ELSE 0 -- and a HAVING"
            " that compares them.\n\n"
            "Return: member_id, unpaid_pence, paid_pence"
        ),
        solution=("SELECT l.member_id, SUM(CASE WHEN f.paid_on IS NULL THEN f.amount_pence ELSE 0 END),"
                  " SUM(CASE WHEN f.paid_on IS NOT NULL THEN f.amount_pence ELSE 0 END)"
                  " FROM fines f JOIN loans l ON l.loan_id = f.loan_id GROUP BY l.member_id"
                  " HAVING SUM(CASE WHEN f.paid_on IS NULL THEN f.amount_pence ELSE 0 END)"
                  " > SUM(CASE WHEN f.paid_on IS NOT NULL THEN f.amount_pence ELSE 0 END)"),
        trap_sql=("SELECT l.member_id, SUM(CASE WHEN f.paid_on IS NULL THEN f.amount_pence ELSE 0 END),"
                  " SUM(CASE WHEN f.paid_on IS NOT NULL THEN f.amount_pence ELSE 0 END)"
                  " FROM fines f JOIN loans l ON l.loan_id = f.loan_id GROUP BY l.member_id"
                  " HAVING SUM(f.paid_on IS NULL) > SUM(f.paid_on IS NOT NULL)"),
        note="Two conditional SUMs split one column two ways in a single"
             " pass, and the HAVING compares the two aggregates. SUM of"
             " the boolean counts fines rather than pence, so a member"
             " with one big unpaid fine and three small paid ones is"
             " left out -- the question is about money, not counts. ELSE"
             " 0 matters: a member with nothing paid needs a 0, not a"
             " NULL, to compare against.",
        claims=[("three hundred and seventy or so members",
                 lambda rows, c: 350 < len(rows) < 390 and all(r[1] > r[2] for r in rows))],
    ),
    # ==================================================== 3 Stock on the shelf
    dict(
        id=7, ledger="Q1033", concept="INT", tier="3 - Stock on the shelf",
        title="Children's books available at each branch",
        prompt=(
            "For each branch, how many of its children's copies are"
            " available right now: not withdrawn, and with no loan whose"
            " returned_on is NULL. A join to books for the genre, and a"
            " SUM over the two-part test with the NOT EXISTS inside it.\n\n"
            "Return: branch_id, available"
        ),
        solution=("SELECT c.branch_id, SUM(c.withdrawn_on IS NULL AND NOT EXISTS ("
                  "SELECT 1 FROM loans l WHERE l.copy_id = c.copy_id AND l.returned_on IS NULL))"
                  " FROM copies c JOIN books b ON b.book_id = c.book_id WHERE b.genre = 'children' GROUP BY c.branch_id"),
        trap_sql=("SELECT c.branch_id, SUM(NOT EXISTS ("
                  "SELECT 1 FROM loans l WHERE l.copy_id = c.copy_id AND l.returned_on IS NULL))"
                  " FROM copies c JOIN books b ON b.book_id = c.book_id WHERE b.genre = 'children' GROUP BY c.branch_id"),
        note="SUM of a boolean counts the copies for which it holds, and"
             " the boolean here is both halves of 'available' joined"
             " with AND. Dropping the withdrawn half counts the"
             " withdrawn children's copies as on the shelf -- they have"
             " no open loan, after all -- and every branch gains a few.",
        claims=[("six branches, thirty to fifty each",
                 lambda rows, c: len(rows) == 6 and all(30 <= r[1] <= 55 for r in rows))],
    ),
    dict(
        id=8, ledger="Q1034", concept="BARE", tier="3 - Stock on the shelf",
        title="Books held at one branch only",
        prompt=(
            "Books all of whose copies are at a SINGLE branch, however"
            " many copies: book_id, that branch's name, and the copy"
            " count. GROUP BY book with HAVING COUNT(DISTINCT branch_id)"
            " = 1, MIN(branch_id) to name the branch -- every copy's"
            " branch is the same one -- joined to branches.\n\n"
            "Return: book_id, branch_name, copies"
        ),
        solution=("SELECT c.book_id, br.name, COUNT(*) FROM copies c"
                  " JOIN branches br ON br.branch_id = c.branch_id"
                  " GROUP BY c.book_id HAVING COUNT(DISTINCT c.branch_id) = 1"),
        trap_sql=("SELECT c.book_id, br.name, COUNT(*) FROM copies c"
                  " JOIN branches br ON br.branch_id = c.branch_id"
                  " GROUP BY c.book_id HAVING COUNT(*) = 1"),
        note="COUNT(DISTINCT branch_id) = 1 says one branch; COUNT(*) = 1"
             " says one copy, a smaller and different set. With every copy"
             " at the same branch, the branch name is the same on every"
             " row of the group, so SQLite's bare column returns it"
             " safely -- MIN(br.name) would say the same explicitly.",
        claims=[("eighty-eight single-branch books, some with several copies",
                 lambda rows, c: len(rows) == 88 and max(r[2] for r in rows) > 1)],
    ),
    dict(
        id=9, ledger="Q1035", concept="JSN", tier="3 - Stock on the shelf",
        title="Each branch's condition mix, as JSON percentages",
        prompt=(
            "For each branch, a JSON object whose keys are the conditions"
            " and whose values are the percentage of the branch's copies"
            " in that condition, to one decimal. A CTE counting copies per"
            " branch and condition, a window SUM partitioned by branch"
            " for the denominator, then json_group_object grouped by"
            " branch with the CTE ordered by branch_id, condition.\n\n"
            "Return: branch_id, mix"
        ),
        solution=("WITH t AS (SELECT branch_id, condition, COUNT(*) AS n FROM copies GROUP BY branch_id, condition),"
                  " s AS (SELECT branch_id, condition, ROUND(100.0 * n / SUM(n) OVER (PARTITION BY branch_id), 1) AS pct FROM t)"
                  " SELECT branch_id, json_group_object(condition, pct) FROM s GROUP BY branch_id"),
        trap_sql=("WITH t AS (SELECT branch_id, condition, COUNT(*) AS n FROM copies GROUP BY branch_id, condition),"
                  " s AS (SELECT branch_id, condition, ROUND(100.0 * n / SUM(n) OVER (), 1) AS pct FROM t)"
                  " SELECT branch_id, json_group_object(condition, pct) FROM s GROUP BY branch_id"),
        note="Three layers again: count, share by window, pack. The"
             " window's PARTITION BY branch_id is what makes each branch's"
             " percentages add up to a hundred; without it the denominator"
             " is all 2,226 copies and each branch's three numbers sum to"
             " about sixteen. json_group_object keeps the keys in the"
             " order the rows arrive.",
        claims=[("six objects whose three percentages add up to a hundred",
                 lambda rows, c: len(rows) == 6
                 and all(99.5 < sum(__import__('json').loads(r[1]).values()) < 100.5 for r in rows))],
    ),
    # ======================================================= 4 Who reads what
    dict(
        id=10, ledger="Q1036", concept="W2", tier="4 - Who reads what",
        title="Each Old Town regular's favourite genre",
        prompt=(
            "For each member of branch 6 with at least 10 loans: the"
            " genre they have borrowed most, ties by genre name, and how"
            " many loans of it. A CTE of loans per member and genre, a"
            " window SUM for the member's total and ROW_NUMBER for the"
            " ranking, then rank 1 where the total is 10 or more.\n\n"
            "Return: member_id, genre, loans"
        ),
        solution=("WITH g AS (SELECT l.member_id, b.genre, COUNT(*) AS n FROM loans l"
                  " JOIN copies c ON c.copy_id = l.copy_id JOIN books b ON b.book_id = c.book_id"
                  " JOIN members m ON m.member_id = l.member_id WHERE m.home_branch_id = 6 GROUP BY l.member_id, b.genre),"
                  " r AS (SELECT member_id, genre, n, ROW_NUMBER() OVER (PARTITION BY member_id ORDER BY n DESC, genre) AS rn,"
                  " SUM(n) OVER (PARTITION BY member_id) AS total FROM g)"
                  " SELECT member_id, genre, n FROM r WHERE rn = 1 AND total >= 10"),
        trap_sql=("WITH g AS (SELECT l.member_id, b.genre, COUNT(*) AS n FROM loans l"
                  " JOIN copies c ON c.copy_id = l.copy_id JOIN books b ON b.book_id = c.book_id"
                  " JOIN members m ON m.member_id = l.member_id WHERE m.home_branch_id = 6 GROUP BY l.member_id, b.genre),"
                  " r AS (SELECT member_id, genre, n, ROW_NUMBER() OVER (PARTITION BY member_id ORDER BY n, genre) AS rn,"
                  " SUM(n) OVER (PARTITION BY member_id) AS total FROM g)"
                  " SELECT member_id, genre, n FROM r WHERE rn = 1 AND total >= 10"),
        note="Two windows over the same grouped CTE, one ranking and one"
             " totalling, both partitioned by member. The ranking's ORDER"
             " BY decides what 'favourite' means -- n DESC for the most,"
             " and ascending gives the genre they touched least. The"
             " total lets the 10-loan threshold be tested in the same"
             " pass.",
        claims=[("two hundred and fifteen regulars",
                 lambda rows, c: len(rows) == 215 and len({r[0] for r in rows}) == 215)],
    ),
    dict(
        id=11, ledger="Q1037", concept="A3", tier="4 - Who reads what",
        title="Readers of every genre",
        prompt=(
            "Members who have borrowed from ALL eight genres: member_id"
            " and their total loans. Two joins to reach the genre, a"
            " GROUP BY member, and HAVING COUNT(DISTINCT genre) = 8 --"
            " or equal to the number of genres as a subquery.\n\n"
            "Return: member_id, loans"
        ),
        solution=("SELECT l.member_id, COUNT(*) FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " JOIN books b ON b.book_id = c.book_id GROUP BY l.member_id"
                  " HAVING COUNT(DISTINCT b.genre) = (SELECT COUNT(DISTINCT genre) FROM books)"),
        trap_sql=("SELECT l.member_id, COUNT(*) FROM loans l JOIN copies c ON c.copy_id = l.copy_id"
                  " JOIN books b ON b.book_id = c.book_id GROUP BY l.member_id"
                  " HAVING COUNT(b.genre) = (SELECT COUNT(DISTINCT genre) FROM books)"),
        note="COUNT(DISTINCT genre) counts the different genres a member"
             " has touched; COUNT(genre) counts loans, so the trap"
             " returns the members with exactly eight loans instead. The"
             " scalar subquery keeps the 8 honest if a genre is ever added.",
        claims=[("a few hundred members, none under eight loans",
                 lambda rows, c: 200 < len(rows) < 800 and all(r[1] >= 8 for r in rows))],
    ),
    dict(
        id=12, ledger="Q1038", concept="J2", tier="4 - Who reads what",
        title="Loans per member, by age band",
        prompt=(
            "Members in three age bands by year of birth against 2026 --"
            " 'under 30', '30 to 59', '60 and over' -- with how many"
            " members each band has and their average loans per member"
            " to one decimal, counting the members with NO loans as 0. A"
            " CTE per member with the band and a LEFT JOIN count, then a"
            " GROUP BY the band.\n\n"
            "Return: band, members, avg_loans"
        ),
        solution=("WITH per AS (SELECT m.member_id,"
                  " CASE WHEN 2026 - CAST(strftime('%Y', m.born_on) AS INTEGER) < 30 THEN 'under 30'"
                  " WHEN 2026 - CAST(strftime('%Y', m.born_on) AS INTEGER) < 60 THEN '30 to 59' ELSE '60 and over' END AS band,"
                  " COUNT(l.loan_id) AS n FROM members m LEFT JOIN loans l ON l.member_id = m.member_id GROUP BY m.member_id)"
                  " SELECT band, COUNT(*), ROUND(AVG(n), 1) FROM per GROUP BY band"),
        trap_sql=("WITH per AS (SELECT m.member_id,"
                  " CASE WHEN 2026 - CAST(strftime('%Y', m.born_on) AS INTEGER) < 30 THEN 'under 30'"
                  " WHEN 2026 - CAST(strftime('%Y', m.born_on) AS INTEGER) < 60 THEN '30 to 59' ELSE '60 and over' END AS band,"
                  " COUNT(l.loan_id) AS n FROM members m JOIN loans l ON l.member_id = m.member_id GROUP BY m.member_id)"
                  " SELECT band, COUNT(*), ROUND(AVG(n), 1) FROM per GROUP BY band"),
        note="The LEFT JOIN is what keeps the two hundred members with no"
             " loans in the CTE with a count of 0, so they pull each"
             " band's average down as they should; an inner join drops"
             " them and both the member counts and the averages come out"
             " too high. The CASE bands by a year difference, which is"
             " good enough for a band ten years wide.",
        claims=[("three bands adding up to 1,500 members",
                 lambda rows, c: len(rows) == 3 and sum(r[1] for r in rows) == 1500
                 and all(10 < r[2] < 25 for r in rows))],
    ),
    # ================================================= 5 Changing the data
    dict(
        id=13, ledger="Q1039", concept="TRG", tier="5 - Changing the data",
        kind="script",
        title="A returned copy goes to the front of the queue",
        prompt=(
            "Write an AFTER UPDATE OF returned_on trigger on loans that,"
            " when a loan is marked returned, marks as fulfilled -- with"
            " fulfilled_on = NEW.returned_on -- the OLDEST open hold on"
            " that copy's book AT THE COPY'S BRANCH, if there is one, and"
            " only that one: an UPDATE of holds whose WHERE picks the"
            " hold_id with a subquery ordered by placed_at LIMIT 1. The"
            " question then returns loan 19031 on 2026-07-01.\n\n"
            "Checked: how many of the book's holds are still open, and"
            " the oldest hold at that branch's fulfilled_on"
        ),
        solution=("CREATE TRIGGER fulfil_on_return AFTER UPDATE OF returned_on ON loans\n"
                  "WHEN NEW.returned_on IS NOT NULL\n"
                  "BEGIN\n"
                  "  UPDATE holds SET fulfilled_on = NEW.returned_on\n"
                  "  WHERE hold_id = (SELECT h.hold_id FROM holds h JOIN copies c ON c.copy_id = NEW.copy_id\n"
                  "                   WHERE h.book_id = c.book_id AND h.branch_id = c.branch_id\n"
                  "                     AND h.fulfilled_on IS NULL AND h.cancelled_on IS NULL\n"
                  "                   ORDER BY h.placed_at LIMIT 1);\n"
                  "END;"),
        trap_sql=("CREATE TRIGGER fulfil_on_return AFTER UPDATE OF returned_on ON loans\n"
                  "WHEN NEW.returned_on IS NOT NULL\n"
                  "BEGIN\n"
                  "  UPDATE holds SET fulfilled_on = NEW.returned_on\n"
                  "  WHERE book_id = (SELECT book_id FROM copies WHERE copy_id = NEW.copy_id)\n"
                  "    AND fulfilled_on IS NULL AND cancelled_on IS NULL;\n"
                  "END;"),
        driver_sql="UPDATE loans SET returned_on = '2026-07-01' WHERE loan_id = 19031;",
        probe_sql=("SELECT (SELECT COUNT(*) FROM holds WHERE book_id = 480 AND fulfilled_on IS NULL AND cancelled_on IS NULL),"
                   " (SELECT fulfilled_on FROM holds WHERE book_id = 480 AND branch_id = 5 AND cancelled_on IS NULL"
                   " ORDER BY placed_at LIMIT 1)"),
        note="The trigger body is an ordinary UPDATE, and the work is in"
             " its WHERE: a subquery that finds the copy's book and"
             " branch from NEW.copy_id, keeps the open holds there,"
             " orders them by placed_at and takes one. Fulfilling every"
             " open hold on the book hands one copy to five people at"
             " two branches.",
        claims=[("one hold fulfilled, four still waiting",
                 lambda rows, c: rows == [(4, '2026-07-01')])],
    ),
    dict(
        id=14, ledger="Q1040", concept="DML", tier="5 - Changing the data",
        kind="script",
        title="A cap on old members' unpaid fines",
        prompt=(
            "Members who joined before 2016 get their UNPAID fines capped"
            " at 500 pence: set amount_pence to MIN(amount_pence, 500)"
            " for those fines only. The member is two joins away from a"
            " fine, so the WHERE uses a subquery over loans and members;"
            " paid fines and newer members are untouched.\n\n"
            "Checked: the count and total of unpaid fines, and the total"
            " of paid fines"
        ),
        solution=("UPDATE fines SET amount_pence = MIN(amount_pence, 500)"
                  " WHERE paid_on IS NULL AND loan_id IN ("
                  "SELECT l.loan_id FROM loans l JOIN members m ON m.member_id = l.member_id"
                  " WHERE m.joined_on < '2016-01-01');"),
        trap_sql=("UPDATE fines SET amount_pence = MIN(amount_pence, 500)"
                  " WHERE loan_id IN ("
                  "SELECT l.loan_id FROM loans l JOIN members m ON m.member_id = l.member_id"
                  " WHERE m.joined_on < '2016-01-01');"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM fines WHERE paid_on IS NULL),"
                   " (SELECT SUM(amount_pence) FROM fines WHERE paid_on IS NULL),"
                   " (SELECT SUM(amount_pence) FROM fines WHERE paid_on IS NOT NULL)"),
        note="UPDATE has no JOIN of its own in this form, so the"
             " membership test travels through IN (SELECT loan_id ...),"
             " which is where the join to members lives. The two-argument"
             " MIN is the scalar cap. paid_on IS NULL is the half of the"
             " WHERE that protects history: a paid fine's amount is a"
             " record of what was paid.",
        claims=[("unpaid total down, paid total unchanged",
                 lambda rows, c: rows[0][0] == 1380 and rows[0][2] == 808400
                 and rows[0][1] == 414960 - (21900 - 27 * 500))],
    ),
    dict(
        id=15, ledger="Q1041", concept="DML", tier="5 - Changing the data",
        kind="script",
        title="Order a copy for every hopeless queue",
        prompt=(
            "For every book with three or more open holds and NO"
            " available copy -- none that is not withdrawn and free of"
            " open loans -- add one copy at Central (branch 1), acquired"
            " '2026-07-01', condition 'good'. One INSERT ... SELECT whose"
            " source is a grouped subquery with HAVING, filtered by a"
            " NOT EXISTS over copies.\n\n"
            "Checked: how many copies were acquired on 2026-07-01, and"
            " how many books with three or more open holds still have"
            " no available copy"
        ),
        solution=("INSERT INTO copies (book_id, branch_id, acquired_on, condition)"
                  " SELECT t.book_id, 1, '2026-07-01', 'good' FROM ("
                  "SELECT book_id FROM holds WHERE fulfilled_on IS NULL AND cancelled_on IS NULL"
                  " GROUP BY book_id HAVING COUNT(*) >= 3) t"
                  " WHERE NOT EXISTS (SELECT 1 FROM copies c WHERE c.book_id = t.book_id AND c.withdrawn_on IS NULL"
                  " AND NOT EXISTS (SELECT 1 FROM loans l WHERE l.copy_id = c.copy_id AND l.returned_on IS NULL));"),
        trap_sql=("INSERT INTO copies (book_id, branch_id, acquired_on, condition)"
                  " SELECT t.book_id, 1, '2026-07-01', 'good' FROM ("
                  "SELECT book_id FROM holds WHERE fulfilled_on IS NULL AND cancelled_on IS NULL"
                  " GROUP BY book_id HAVING COUNT(*) >= 3) t;"),
        probe_sql=("SELECT (SELECT COUNT(*) FROM copies WHERE acquired_on = '2026-07-01'),"
                   " (SELECT COUNT(*) FROM (SELECT book_id FROM holds WHERE fulfilled_on IS NULL AND cancelled_on IS NULL"
                   " GROUP BY book_id HAVING COUNT(*) >= 3) t WHERE NOT EXISTS (SELECT 1 FROM copies c"
                   " WHERE c.book_id = t.book_id AND c.withdrawn_on IS NULL AND NOT EXISTS ("
                   "SELECT 1 FROM loans l WHERE l.copy_id = c.copy_id AND l.returned_on IS NULL)))"),
        note="The SELECT that feeds an INSERT can be as elaborate as any"
             " other: a grouped subquery in FROM, a HAVING inside it, and"
             " a correlated NOT EXISTS outside. The availability test is"
             " what makes the order a sensible one -- fifty-three of the"
             " fifty-six long queues already have a copy on a shelf"
             " somewhere, and only three need stock bought.",
        claims=[("three copies bought, no hopeless queue left",
                 lambda rows, c: rows == [(3, 0)])],
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
