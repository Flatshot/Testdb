"""Practice exercises: fifteen questions on the library schema.

The sixth set on the library (SEED 861), on six tiers NONE of the library
sets have used. JSON -- json_group_array with its own ORDER BY, json_each
to turn a JSON list into rows, json_object to build a record. LIKE and
GLOB -- a character class that only GLOB has, and the underscore that
LIKE treats as a wildcard. Date modifiers -- '-90 days' against '-3
months', 'weekday 0' for the Sunday that ends a week, and an age in whole
years that a difference of years gets wrong. Query plans -- two questions
graded on EXPLAIN QUERY PLAN, where the slow query is already in the
editor and returns the right rows. Aggregates over windows -- a window
over a GROUP BY to compare each group with the average group, and a share
of the branch that needs PARTITION BY. And three WRITABLE questions:

  * UPDATE ... FROM, where the condition on the other table meets a
    condition on this one
  * a DELETE of duplicates by ROW_NUMBER in a subquery
  * ALTER TABLE ADD COLUMN ... GENERATED ALWAYS AS, a column that computes
    itself

Each of those runs in a private in-memory copy of the database, so nothing
you write can reach the real file. The copy persists across Runs of one
question -- run an UPDATE, then a SELECT to see what it did -- and is
discarded by Reset or by moving to another question, so no question can
depend on what another one wrote. Check answer always grades a FRESH copy.
The question's `probe_sql` then reads the result, and that is what is
compared with the reference.

The two query-plan questions carry `plan_requires` / `plan_forbids`, checked
against EXPLAIN QUERY PLAN, and a `starter_sql` that opens in the editor:
correct, slow, and the thing to improve.
"""

import sqlite3

EXERCISES = [
    # ================================================================ 1 JSON
    dict(
        id=1, ledger="Q922", concept="JSN", tier="1 - JSON",
        title="Each branch's staff, as a JSON list",
        prompt=(
            "For each branch, its staff names as ONE JSON array, in"
            " alphabetical order of name: json_group_array with an ORDER"
            " BY inside its parentheses.\n\n"
            "Return: branch_id, names"
        ),
        solution="SELECT branch_id, json_group_array(name ORDER BY name) FROM staff GROUP BY branch_id",
        trap_sql="SELECT branch_id, json_group_array(name) FROM staff GROUP BY branch_id",
        note="json_group_array is GROUP_CONCAT's JSON cousin: it packs a"
             " group's values into a properly quoted array. Like"
             " GROUP_CONCAT it takes the rows in whatever order they"
             " arrive -- staff_id order here -- unless the ORDER BY goes"
             " inside the call. The result is TEXT that any JSON reader"
             " can parse.",
        claims=[("six arrays, each sorted and valid JSON",
                 lambda rows, c: len(rows) == 6
                 and all(c.execute("SELECT json_valid(?)", (r[1],)).fetchone()[0] == 1
                         and __import__('json').loads(r[1]) == sorted(__import__('json').loads(r[1]))
                         for r in rows))],
    ),
    dict(
        id=2, ledger="Q923", concept="JSN", tier="1 - JSON",
        title="A list of books, from JSON to rows",
        prompt=(
            "Given the JSON list '[587, 12, 40, 275]' of book ids, how"
            " many members are WAITING on each -- an open hold, neither"
            " fulfilled nor cancelled -- including 0 for a book nobody is"
            " waiting for. json_each() turns the list into rows with a"
            " `value` column.\n\n"
            "Return: book_id, waiting"
        ),
        solution=("SELECT value, (SELECT COUNT(*) FROM holds h WHERE h.book_id = value"
                  " AND h.fulfilled_on IS NULL AND h.cancelled_on IS NULL)"
                  " FROM json_each('[587, 12, 40, 275]')"),
        trap_sql=("SELECT value, (SELECT COUNT(*) FROM holds h WHERE h.book_id = value)"
                  " FROM json_each('[587, 12, 40, 275]')"),
        note="json_each is a table-valued function: it sits in FROM and"
             " yields one row per element, with the element in `value`."
             " That gives a list of ids a home in SQL without a temporary"
             " table or a long IN (...). The count is the usual open-hold"
             " test, correlated on value; counting every hold ever placed"
             " on the book is the trap from the first library set again.",
        claims=[("four books, 587 with seven waiting",
                 lambda rows, c: len(rows) == 4 and dict(rows)[587] == 7
                 and dict(rows)[12] == 0)],
    ),
    dict(
        id=3, ledger="Q924", concept="JSN", tier="1 - JSON",
        title="A card for each manager",
        prompt=(
            "For each manager, a JSON object with the keys id, name and"
            " branch holding their staff_id, name and branch_id -- built"
            " with json_object(key, value, key, value, ...).\n\n"
            "Return: staff_id, card"
        ),
        solution=("SELECT staff_id, json_object('id', staff_id, 'name', name, 'branch', branch_id)"
                  " FROM staff WHERE role = 'manager'"),
        trap_sql=("SELECT staff_id, json_array(staff_id, name, branch_id)"
                  " FROM staff WHERE role = 'manager'"),
        note="json_object takes keys and values in alternation and"
             " quotes the text values for you; json_array makes a list"
             " with no keys, which a reader cannot tell apart from any"
             " other list of three. Either is text, which is why the id"
             " is also returned as a plain column.",
        claims=[("five managers, every card a valid object",
                 lambda rows, c: len(rows) == 5
                 and all(c.execute("SELECT json_type(?)", (r[1],)).fetchone()[0] == 'object'
                         for r in rows))],
    ),
    # ======================================================= 2 LIKE and GLOB
    dict(
        id=4, ledger="Q925", concept="LIK", tier="2 - LIKE and GLOB",
        title="Titles that begin with a vowel",
        prompt=(
            "How many titles begin with each capital vowel -- A, E, I, O"
            " or U -- one row per letter that occurs. GLOB has a"
            " character class, [AEIOU], that LIKE does not, and GLOB is"
            " case-sensitive.\n\n"
            "Return: letter, titles"
        ),
        solution="SELECT SUBSTR(title, 1, 1), COUNT(*) FROM books WHERE title GLOB '[AEIOU]*' GROUP BY 1",
        trap_sql="SELECT SUBSTR(title, 1, 1), COUNT(*) FROM books WHERE title GLOB '[aeiou]*' GROUP BY 1",
        note="GLOB uses * and ? where LIKE uses % and _, adds [...] for a"
             " set of characters, and matches case EXACTLY -- so [aeiou]"
             " finds no title at all, because every title is capitalised."
             " LIKE would need five ORs and would also match a title"
             " beginning with a lower-case vowel, if there were one.",
        claims=[("four vowels, A by far the commonest",
                 lambda rows, c: len(rows) == 4
                 and max(rows, key=lambda r: r[1])[0] == 'A'
                 and sum(r[1] for r in rows) == 133)],
    ),
    dict(
        id=5, ledger="Q926", concept="LIK", tier="2 - LIKE and GLOB",
        title="The LS1x districts",
        prompt=(
            "How many members live in each postcode area of exactly four"
            " characters beginning 'LS1' -- LS10 to LS19 -- but NOT in"
            " 'LS1' itself. In LIKE, _ matches exactly one character.\n\n"
            "Return: postcode_area, members"
        ),
        solution="SELECT postcode_area, COUNT(*) FROM members WHERE postcode_area LIKE 'LS1_' GROUP BY 1",
        trap_sql="SELECT postcode_area, COUNT(*) FROM members WHERE postcode_area LIKE 'LS1%' GROUP BY 1",
        note="% matches any number of characters including none, so"
             " 'LS1%' takes in LS1 as well as the LS1x districts. _"
             " matches exactly one, which is the length test the"
             " question wants. The same thing in GLOB is 'LS1?'. Six"
             " districts in the data.",
        claims=[("six districts, LS1 not among them",
                 lambda rows, c: len(rows) == 6 and all(len(r[0]) == 4 for r in rows))],
    ),
    # ====================================================== 3 Date modifiers
    dict(
        id=6, ledger="Q927", concept="D2", tier="3 - Date modifiers",
        title="Fines from the last ninety days",
        prompt=(
            "Fines issued in the ninety days ending 2026-06-30 -- strictly"
            " after date('2026-06-30', '-90 days') -- split into unpaid"
            " and paid: a 0/1 flag for paid, the count, and the pence.\n\n"
            "Return: paid, fines, pence"
        ),
        solution=("SELECT paid_on IS NOT NULL, COUNT(*), SUM(amount_pence) FROM fines"
                  " WHERE issued_on > date('2026-06-30', '-90 days') GROUP BY 1"),
        trap_sql=("SELECT paid_on IS NOT NULL, COUNT(*), SUM(amount_pence) FROM fines"
                  " WHERE issued_on > date('2026-06-30', '-3 months') GROUP BY 1"),
        note="'-90 days' and '-3 months' are not the same modifier: from"
             " 30 June, ninety days back is 1 April and three months back"
             " is 30 March, and the two extra days carry a few fines"
             " with them. Say which one you mean; a question that says"
             " ninety days means days.",
        claims=[("two rows, seven hundred or so fines in all",
                 lambda rows, c: len(rows) == 2 and 700 < sum(r[1] for r in rows) < 740)],
    ),
    dict(
        id=7, ledger="Q928", concept="D2", tier="3 - Date modifiers",
        title="Weeks ending on a Sunday",
        prompt=(
            "For the loans started from 2026-01-01 to 2026-03-31: how"
            " many started in each week, labelled by the SUNDAY that ends"
            " it -- date(loaned_on, 'weekday 0') gives the next Sunday on"
            " or after a date. Fourteen weeks, the first and last of them"
            " partial.\n\n"
            "Return: week_ending, loans"
        ),
        solution=("SELECT date(loaned_on, 'weekday 0'), COUNT(*) FROM loans"
                  " WHERE loaned_on BETWEEN '2026-01-01' AND '2026-03-31' GROUP BY 1"),
        trap_sql=("SELECT date(loaned_on, 'weekday 1'), COUNT(*) FROM loans"
                  " WHERE loaned_on BETWEEN '2026-01-01' AND '2026-03-31' GROUP BY 1"),
        note="'weekday N' moves a date FORWARD to the next day with that"
             " weekday number, 0 for Sunday, staying put if it already"
             " is one -- so every day of a Monday-to-Sunday week lands on"
             " the same Sunday. 'weekday 1' lands on Mondays, grouping"
             " Tuesday-to-Monday weeks instead, and the labels are the"
             " wrong days.",
        claims=[("fourteen Sundays",
                 lambda rows, c: len(rows) == 14
                 and all(c.execute("SELECT strftime('%w', ?)", (r[0],)).fetchone()[0] == '0'
                         for r in rows)
                 and sum(r[1] for r in rows) ==
                 c.execute("SELECT COUNT(*) FROM loans WHERE loaned_on BETWEEN '2026-01-01'"
                           " AND '2026-03-31'").fetchone()[0])],
    ),
    dict(
        id=8, ledger="Q929", concept="D2", tier="3 - Date modifiers",
        title="Members by decade of age",
        prompt=(
            "How many members fall in each decade of age on 2026-06-30:"
            " 0 for under ten, 10 for ten to nineteen, and so on. An age"
            " in whole years is the difference in years MINUS ONE when"
            " the birthday has not yet come round -- compare the"
            " '%m-%d' parts.\n\n"
            "Return: decade, members"
        ),
        solution=("SELECT (CAST(strftime('%Y', '2026-06-30') AS INTEGER) - CAST(strftime('%Y', born_on) AS INTEGER)"
                  " - (strftime('%m-%d', '2026-06-30') < strftime('%m-%d', born_on))) / 10 * 10, COUNT(*)"
                  " FROM members GROUP BY 1"),
        trap_sql=("SELECT (CAST(strftime('%Y', '2026-06-30') AS INTEGER) - CAST(strftime('%Y', born_on) AS INTEGER))"
                  " / 10 * 10, COUNT(*) FROM members GROUP BY 1"),
        note="Subtracting years says a member born in December 1996 is"
             " 30 in June 2026, when they are still 29. The comparison of"
             " the month-and-day strings is 1 when the birthday is still"
             " to come, and subtracting it fixes the age -- about half of"
             " the members shift down a year, and some of them across a"
             " decade boundary.",
        claims=[("ten decades, 0 to 90",
                 lambda rows, c: sorted(r[0] for r in rows) == list(range(0, 100, 10))
                 and sum(r[1] for r in rows) == 1500)],
    ),
    # ========================================================= 4 Query plans
    dict(
        id=9, ledger="Q930", concept="X5", tier="4 - Query plans",
        title="Let the index find the member",
        prompt=(
            "Member 1149's loans: loan_id and loaned_on. The query in the"
            " editor is correct and reads every one of the 24,000 loans."
            " There is an index on loans(member_id); write the WHERE so"
            " that SQLite can use it. Your plan must mention"
            " idx_loans_member.\n\n"
            "Return: loan_id, loaned_on"
        ),
        starter_sql="SELECT loan_id, loaned_on FROM loans WHERE member_id + 0 = 1149",
        solution="SELECT loan_id, loaned_on FROM loans WHERE member_id = 1149",
        trap_sql="SELECT loan_id, loaned_on FROM loans WHERE CAST(member_id AS TEXT) = '1149'",
        note="An index can only be searched on the column AS STORED."
             " Wrap the column in arithmetic, a CAST or a function and the"
             " index no longer applies, because SQLite would have to"
             " compute the expression for every row to know which match"
             " -- which is a full scan. The rows are identical either"
             " way; only EXPLAIN QUERY PLAN tells the two apart.",
        plan_requires=("idx_loans_member",),
        claims=[("two hundred or so loans -- 1149 is a heavy reader",
                 lambda rows, c: 150 < len(rows) < 300)],
    ),
    dict(
        id=10, ledger="Q931", concept="X5", tier="4 - Query plans",
        title="A title lookup that ignores case, through the index",
        prompt=(
            "The book whose title is 'the glass path' in any mix of case:"
            " book_id and title. The query in the editor lower-cases"
            " every title to compare, which scans the table. The index"
            " idx_books_title is declared COLLATE NOCASE, so a comparison"
            " that asks for that collation can SEARCH it: your plan must"
            " say SEARCH, not SCAN.\n\n"
            "Return: book_id, title"
        ),
        starter_sql="SELECT book_id, title FROM books WHERE LOWER(title) = 'the glass path'",
        solution="SELECT book_id, title FROM books WHERE title = 'the glass path' COLLATE NOCASE",
        trap_sql="SELECT book_id, title FROM books WHERE UPPER(title) = 'THE GLASS PATH'",
        note="An index built with COLLATE NOCASE is ordered case-"
             "insensitively, and a comparison that asks for the same"
             " collation can binary-search it. LOWER(title) or UPPER("
             "title) is an expression, not the column, so the index is"
             " useless however the comparison is spelled. A LIKE with no"
             " leading wildcard can use this index too, because LIKE is"
             " case-insensitive and so is the index -- a rare case where"
             " LIKE is as fast as =.",
        plan_requires=("SEARCH books",),
        plan_forbids=("SCAN",),
        claims=[("one book, The Glass Path",
                 lambda rows, c: rows == [(54, 'The Glass Path')])],
    ),
    # ============================================= 5 Aggregates over windows
    dict(
        id=11, ledger="Q932", concept="W3", tier="5 - Aggregates over windows",
        title="Genres busier than the average genre",
        prompt=(
            "Genres whose loan count is above the AVERAGE genre's loan"
            " count -- the average of the eight per-genre totals. Group"
            " first, then a window AVG over the grouped counts, then"
            " filter in an outer query.\n\n"
            "Return: genre, loans"
        ),
        solution=("SELECT genre, n FROM (SELECT b.genre, COUNT(*) AS n, AVG(COUNT(*)) OVER () AS avg_n"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id JOIN books b ON b.book_id = c.book_id"
                  " GROUP BY b.genre) WHERE n > avg_n"),
        trap_sql=("SELECT genre, n FROM (SELECT b.genre, COUNT(*) AS n,"
                  " AVG(COUNT(*)) OVER (PARTITION BY b.genre) AS avg_n"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id JOIN books b ON b.book_id = c.book_id"
                  " GROUP BY b.genre) WHERE n > avg_n"),
        note="AVG(COUNT(*)) OVER () is a window over the GROUPED rows:"
             " eight genre totals, averaged. PARTITION BY genre makes"
             " each partition a single row, so the 'average' is the"
             " genre's own count and nothing is above it. A HAVING cannot"
             " do this at all -- HAVING sees one group at a time, and the"
             " comparison needs all of them.",
        claims=[("two genres, fiction and children",
                 lambda rows, c: {r[0] for r in rows} == {'fiction', 'children'})],
    ),
    dict(
        id=12, ledger="Q933", concept="W3", tier="5 - Aggregates over windows",
        title="A genre that is a fifth of its branch",
        prompt=(
            "For each branch and genre: the genre's share of that"
            " BRANCH's loans as a percentage to one decimal, keeping only"
            " the pairs above 20 per cent. The branch total is a window"
            " SUM over the grouped counts, partitioned by branch.\n\n"
            "Return: branch_id, genre, pct"
        ),
        solution=("SELECT branch_id, genre, pct FROM (SELECT c.branch_id, b.genre,"
                  " ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY c.branch_id), 1) AS pct"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id JOIN books b ON b.book_id = c.book_id"
                  " GROUP BY c.branch_id, b.genre) WHERE pct > 20"),
        trap_sql=("SELECT branch_id, genre, pct FROM (SELECT c.branch_id, b.genre,"
                  " ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct"
                  " FROM loans l JOIN copies c ON c.copy_id = l.copy_id JOIN books b ON b.book_id = c.book_id"
                  " GROUP BY c.branch_id, b.genre) WHERE pct > 20"),
        note="SUM(COUNT(*)) OVER () is the grand total of all loans, so"
             " every share is a share of the whole service and nothing"
             " reaches 20 per cent. PARTITION BY branch_id restarts the"
             " sum per branch. The filter has to be an outer WHERE: a"
             " window value cannot be tested in the HAVING of the query"
             " that computes it.",
        claims=[("seven pairs, fiction at every branch",
                 lambda rows, c: len(rows) == 7
                 and sum(r[1] == 'fiction' for r in rows) == 6
                 and all(r[2] > 20 for r in rows))],
    ),
    # ================================================= 6 Changing the data
    dict(
        id=13, ledger="Q934", concept="DML", tier="6 - Changing the data",
        kind="script",
        title="A week's grace at Old Town",
        prompt=(
            "Old Town (branch 6) is closing for a week. Give every loan"
            " that is still OUT on one of its copies seven more days:"
            " due_on = date(due_on, '+7 days'). Use UPDATE ... FROM to"
            " bring copies into the WHERE. Returned loans and other"
            " branches' loans are untouched.\n\n"
            "Checked: the total loan length in days of Old Town's open"
            " loans, of its returned loans, and of open loans elsewhere"
        ),
        solution=("UPDATE loans SET due_on = date(due_on, '+7 days')"
                  " FROM copies WHERE copies.copy_id = loans.copy_id"
                  " AND copies.branch_id = 6 AND loans.returned_on IS NULL;"),
        trap_sql=("UPDATE loans SET due_on = date(due_on, '+7 days')"
                  " FROM copies WHERE copies.copy_id = loans.copy_id"
                  " AND copies.branch_id = 6;"),
        probe_sql=("SELECT (SELECT SUM(julianday(l.due_on) - julianday(l.loaned_on)) FROM loans l"
                   " JOIN copies c ON c.copy_id = l.copy_id WHERE c.branch_id = 6 AND l.returned_on IS NULL),"
                   " (SELECT SUM(julianday(l.due_on) - julianday(l.loaned_on)) FROM loans l"
                   " JOIN copies c ON c.copy_id = l.copy_id WHERE c.branch_id = 6 AND l.returned_on IS NOT NULL),"
                   " (SELECT SUM(julianday(l.due_on) - julianday(l.loaned_on)) FROM loans l"
                   " JOIN copies c ON c.copy_id = l.copy_id WHERE c.branch_id <> 6 AND l.returned_on IS NULL)"),
        note="UPDATE ... FROM joins another table into the update, so a"
             " condition on copies can decide which loans change -- the"
             " alternative is a subquery in the WHERE. The condition on"
             " loans itself, returned_on IS NULL, is the one that keeps"
             " history intact: without it two thousand finished loans at"
             " Old Town get a due date they never had.",
        claims=[("open loans at Old Town a week longer, nothing else moved",
                 lambda rows, c: rows == [(3962.0, 109487.0, 17507.0)])],
    ),
    dict(
        id=14, ledger="Q935", concept="DML", tier="6 - Changing the data",
        kind="script",
        title="One hold per member per book, the earliest kept",
        prompt=(
            "Eight members hold the same book twice. Delete the LATER"
            " hold of each such pair -- by placed_at -- keeping the"
            " earliest, with ROW_NUMBER over (member_id, book_id) in a"
            " subquery that picks the hold_ids to delete.\n\n"
            "Checked: how many holds remain, the sum of their hold_ids,"
            " and how many (member, book) pairs still repeat"
        ),
        solution=("DELETE FROM holds WHERE hold_id IN ("
                  "SELECT hold_id FROM (SELECT hold_id, ROW_NUMBER() OVER"
                  " (PARTITION BY member_id, book_id ORDER BY placed_at) AS rn FROM holds)"
                  " WHERE rn > 1);"),
        trap_sql=("DELETE FROM holds WHERE hold_id IN ("
                  "SELECT hold_id FROM (SELECT hold_id, ROW_NUMBER() OVER"
                  " (PARTITION BY member_id, book_id ORDER BY placed_at DESC) AS rn FROM holds)"
                  " WHERE rn > 1);"),
        probe_sql=("SELECT COUNT(*), SUM(hold_id),"
                   " (SELECT COUNT(*) FROM (SELECT 1 FROM holds GROUP BY member_id, book_id HAVING COUNT(*) > 1))"
                   " FROM holds"),
        note="DELETE has no window clause of its own, so the numbering"
             " happens in a subquery and the DELETE takes the ids it"
             " produces. ORDER BY placed_at makes the earliest hold"
             " number 1, the one that survives; DESC keeps the latest"
             " instead, which deletes the same NUMBER of rows but not the"
             " same rows -- which is why the probe sums the ids.",
        claims=[("eight gone, no pair repeats",
                 lambda rows, c: rows == [(1492, 1118443, 0)])],
    ),
    dict(
        id=15, ledger="Q936", concept="DDL", tier="6 - Changing the data",
        kind="script",
        title="A column that computes itself",
        prompt=(
            "Add a VIRTUAL generated column `size` to books: 'short' under"
            " 200 pages, 'medium' under 500, 'long' otherwise -- ALTER"
            " TABLE books ADD COLUMN size TEXT GENERATED ALWAYS AS (...)"
            " VIRTUAL. Nothing is stored; the value is computed from"
            " pages whenever it is read.\n\n"
            "Checked: how many books of each size"
        ),
        solution=("ALTER TABLE books ADD COLUMN size TEXT GENERATED ALWAYS AS"
                  " (CASE WHEN pages < 200 THEN 'short' WHEN pages < 500 THEN 'medium' ELSE 'long' END) VIRTUAL;"),
        trap_sql=("ALTER TABLE books ADD COLUMN size TEXT GENERATED ALWAYS AS"
                  " (CASE WHEN pages < 500 THEN 'medium' WHEN pages < 200 THEN 'short' ELSE 'long' END) VIRTUAL;"),
        probe_sql="SELECT size, COUNT(*) FROM books GROUP BY size ORDER BY size",
        note="A generated column is an expression that behaves like a"
             " column: it can be selected, filtered and indexed, and it"
             " can never disagree with pages because it is pages. Only"
             " VIRTUAL ones can be added by ALTER TABLE; a STORED one"
             " needs the table to be created with it. The CASE inside"
             " obeys the usual rule -- narrowest WHEN first.",
        claims=[("short, medium and long, six hundred in all",
                 lambda rows, c: rows == [('long', 283), ('medium', 214), ('short', 103)])],
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
