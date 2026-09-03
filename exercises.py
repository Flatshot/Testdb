"""Practice exercises with reference solutions, used by the GUI to grade answers.

These 30 questions (ledger Q252-Q281) run on a NEW schema. The repair-depot
tables are gone; this is a further-education college, and the point of the
change is that five sets in a row on the same fourteen tables had made the
joins muscle memory. Read schema.sql before you start -- the relationships are
not the ones you are used to.

The difficulty is pitched at the same level as Q222-Q251, and the same two
rules apply:

  * one concept each. No question stacks a window function on top of a
    self-join on top of a date trick.
  * the prompt states the grain. "One row per course", "all 34 come back".

Coverage is even this time rather than weighted to one tier:

  recursion           4  a real dependency GRAPH, not a fifth org chart
  window functions    4  ranking with ties, LAG, running total, share
  joins               4  outer joins that keep zeroes, self-joins, anti-joins
  aggregation         4  COUNT(*) vs COUNT(col), WHERE vs HAVING, pivots
  subqueries/EXISTS   3  EXISTS, NOT EXISTS vs NOT IN, correlation
  dates               3  julianday, date comparison across a join, %m vs %Y-%m
  set operations      2  EXCEPT is directional, INTERSECT is not UNION
  NULLs               2  = NULL never matches, <> silently drops rows
  grain               2  two child tables fan out; SUM(a*b) is not SUM(a)*b
  general             2  CASE branch order, DISTINCT down a deep chain

The four recursion questions deliberately avoid the supervisor-chain shape
that the last three sets leaned on. `prerequisites` is a genuine directed
graph: a course can require several others AND be required by several others,
so the same course is reachable by more than one path and a plain UNION ALL
walk would visit it twice. Only one of the four is a hierarchy at all; the
others generate a month series and measure depth.

Each question carries:

  concept   the mistake or technique it drills
  solution  one correct answer
  trap_sql  the tempting WRONG query -- check_questions.py asserts the grader
            rejects it, which is what proves the question actually has teeth
  note      the lesson, shown in the GUI once you get it right
  claims    optional facts about the data that the prompt asserts, re-checked
            against the live database so a prompt cannot quietly go stale

Grading compares your result against the reference as an unordered multiset of
rows, with floats rounded to 2 decimals. Row order never matters and you do not
need to remember ROUND(). Column count and values do matter -- each prompt
states exactly what to return.

Spoiler warning: the reference SQL is in this file.
"""

# The month the data is treated as ending. Fixed rather than taken from the
# clock, so a question means the same thing next month as it does today.
CUTOFF = "2026-06-30"

# The month spine the generated-series question reuses: the full span of
# enrolled_on, gaps included. Written once so a date change cannot drift.
SPINE = ("WITH RECURSIVE m(mth) AS (SELECT '2024-08' UNION ALL"
         " SELECT strftime('%Y-%m', date(mth || '-01', '+1 month'))"
         " FROM m WHERE mth < '2026-05')")

EXERCISES = [
    # ------------------------------------------------------------ recursion
    dict(
        id=1, ledger="Q252", concept="R1", tier="Recursion",
        title="Everything Machine Learning depends on",
        prompt=(
            "Course CMP401 'Machine Learning' has prerequisites, and those have"
            " prerequisites of their own. List every course it depends on, at"
            " any depth.\n\n"
            "Five courses qualify. Two are direct prerequisites; the rest are"
            " reached through them. CMP401 itself is not in the answer.\n\n"
            "Return: course_id, code, title"
        ),
        solution=(
            "WITH RECURSIVE need(id) AS ("
            " SELECT requires_course_id FROM prerequisites"
            " WHERE course_id = (SELECT course_id FROM courses"
            " WHERE code = 'CMP401')"
            " UNION"
            " SELECT p.requires_course_id FROM prerequisites p"
            " JOIN need n ON p.course_id = n.id)"
            " SELECT c.course_id, c.code, c.title FROM courses c"
            " JOIN need ON need.id = c.course_id"
        ),
        trap_sql=(
            "SELECT c.course_id, c.code, c.title FROM prerequisites p"
            " JOIN courses c ON c.course_id = p.requires_course_id"
            " WHERE p.course_id = (SELECT course_id FROM courses"
            " WHERE code = 'CMP401')"
        ),
        note="A single join to prerequisites gives you the DIRECT requirements"
             " and stops. The recursion is what follows each of those onward"
             " until nothing new turns up. Note UNION rather than UNION ALL:"
             " this is a graph, not a tree, so the same course is reachable by"
             " more than one path and UNION ALL would list it twice.",
        claims=[
            ("five courses, and CMP401 is not one of them",
             lambda rows, c: len(rows) == 5
             and not any(r[1] == 'CMP401' for r in rows)),
            ("only two of them are direct prerequisites",
             lambda rows, c: c.execute(
                 "SELECT COUNT(*) FROM prerequisites WHERE course_id ="
                 " (SELECT course_id FROM courses WHERE code = 'CMP401')"
             ).fetchone()[0] == 2),
        ],
    ),
    dict(
        id=2, ledger="Q253", concept="R1", tier="Recursion",
        title="How deep does the chain go",
        prompt=(
            "For every course that has at least one prerequisite, how many hops"
            " it is from that course to its most distant prerequisite.\n\n"
            "A course whose prerequisites have none of their own is 1. If any"
            " path runs three courses back, it is 3. Where two paths differ in"
            " length, take the longer.\n\n"
            "Return: course_id, code, depth"
        ),
        solution=(
            "WITH RECURSIVE w(start, id, d) AS ("
            " SELECT course_id, requires_course_id, 1 FROM prerequisites"
            " UNION ALL"
            " SELECT w.start, p.requires_course_id, w.d + 1"
            " FROM w JOIN prerequisites p ON p.course_id = w.id)"
            " SELECT c.course_id, c.code, MAX(w.d) FROM w"
            " JOIN courses c ON c.course_id = w.start"
            " GROUP BY 1, 2"
        ),
        trap_sql=(
            "SELECT c.course_id, c.code, COUNT(*) FROM prerequisites p"
            " JOIN courses c ON c.course_id = p.course_id"
            " GROUP BY 1, 2"
        ),
        note="Counting the rows in prerequisites gives how many courses this"
             " one requires DIRECTLY -- a width, not a depth. Depth needs the"
             " walk: carry the starting course along in the recursion so every"
             " row knows where it came from, add 1 at each hop, then take the"
             " MAX per start. Here UNION ALL is right: a course reached twice"
             " by paths of different lengths must be counted at both.",
        claims=[
            ("every course with a prerequisite appears, 23 of them",
             lambda rows, c: len(rows) == c.execute(
                 "SELECT COUNT(DISTINCT course_id) FROM prerequisites"
             ).fetchone()[0]),
            ("the deepest chain is 3 hops",
             lambda rows, c: max(r[2] for r in rows) == 3),
        ],
    ),
    dict(
        id=3, ledger="Q254", concept="R2", tier="Recursion",
        title="Every month, including the quiet ones",
        prompt=(
            "How many enrolments were made in each month from 2024-08 to"
            " 2026-05 inclusive, as 'YYYY-MM'.\n\n"
            "Nobody enrols in August or over the summer, so several months have"
            " none. Those months must still appear, with 0. That is 22 rows,"
            " not the 14 a GROUP BY gives you.\n\n"
            "Return: month, enrolments"
        ),
        solution=(
            SPINE +
            " SELECT m.mth, COUNT(e.enrolment_id) FROM m"
            " LEFT JOIN enrolments e"
            " ON strftime('%Y-%m', e.enrolled_on) = m.mth"
            " GROUP BY m.mth"
        ),
        trap_sql=(
            "SELECT strftime('%Y-%m', enrolled_on), COUNT(*)"
            " FROM enrolments GROUP BY 1"
        ),
        note="GROUP BY can only return groups the data already contains, so a"
             " month with no enrolments does not exist to be returned -- and a"
             " gap you cannot see is the kind that gets missed. Generate the"
             " series first, then LEFT JOIN the data onto it. COUNT(a column"
             " from the right side) is what turns the empty months into 0"
             " rather than 1.",
        claims=[
            ("22 months, and 8 of them are empty",
             lambda rows, c: len(rows) == 22
             and sum(1 for r in rows if r[1] == 0) == 8),
            ("the counts still total every enrolment",
             lambda rows, c: sum(r[1] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM enrolments").fetchone()[0]),
        ],
    ),
    dict(
        id=4, ledger="Q255", concept="R1", tier="Recursion",
        title="How far below the top",
        prompt=(
            "Every instructor, with how many levels below the top of the"
            " mentoring tree they sit.\n\n"
            "One instructor has no mentor -- they are level 0. Anyone mentored"
            " by them is 1, anyone mentored by those is 2. All 16 appear.\n\n"
            "Return: instructor_id, name, level"
        ),
        solution=(
            "WITH RECURSIVE t(id, name, lvl) AS ("
            " SELECT instructor_id, name, 0 FROM instructors"
            " WHERE mentor_id IS NULL"
            " UNION ALL"
            " SELECT i.instructor_id, i.name, t.lvl + 1"
            " FROM instructors i JOIN t ON i.mentor_id = t.id)"
            " SELECT id, name, lvl FROM t"
        ),
        trap_sql=(
            "SELECT i.instructor_id, i.name,"
            " CASE WHEN i.mentor_id IS NULL THEN 0 ELSE 1 END"
            " FROM instructors i"
        ),
        note="A single self-join, or a CASE on mentor_id, can only tell the top"
             " from everyone else -- it cannot distinguish level 1 from level 2,"
             " because that depends on the mentor's own level. The anchor here"
             " is the row with no mentor, seeded at 0, and each step inherits"
             " lvl + 1 from whoever it joined to.",
        claims=[
            ("all 16 instructors, exactly one at level 0",
             lambda rows, c: len(rows) == 16
             and sum(1 for r in rows if r[2] == 0) == 1),
            ("the tree is three levels deep",
             lambda rows, c: max(r[2] for r in rows) == 2),
        ],
    ),
    # ---------------------------------------------------- window functions
    dict(
        id=5, ledger="Q256", concept="W2", tier="Window functions",
        title="Top of each programme, ties and all",
        prompt=(
            "The highest mark achieved in each programme, and who got it."
            " Only graded enrolments count.\n\n"
            "Three programmes have two students tied on the top mark. Both"
            " must appear, so the answer is 12 rows across 9 programmes.\n\n"
            "Return: programme, student_id, name, grade"
        ),
        solution=(
            "WITH g AS (SELECT st.programme, st.student_id, st.name, e.grade,"
            " RANK() OVER (PARTITION BY st.programme ORDER BY e.grade DESC) rk"
            " FROM enrolments e JOIN students st"
            " ON st.student_id = e.student_id WHERE e.grade IS NOT NULL)"
            " SELECT programme, student_id, name, grade FROM g WHERE rk = 1"
        ),
        trap_sql=(
            "WITH g AS (SELECT st.programme, st.student_id, st.name, e.grade,"
            " ROW_NUMBER() OVER (PARTITION BY st.programme"
            " ORDER BY e.grade DESC) rk"
            " FROM enrolments e JOIN students st"
            " ON st.student_id = e.student_id WHERE e.grade IS NOT NULL)"
            " SELECT programme, student_id, name, grade FROM g WHERE rk = 1"
        ),
        note="ROW_NUMBER hands out 1, 2, 3 with no repeats, so on a tie it"
             " keeps one row arbitrarily and you silently lose the other. RANK"
             " gives tied rows the same number. ROW_NUMBER when you want"
             " exactly one row; RANK when you want everyone who earned the"
             " position.",
        claims=[
            ("12 rows across 9 programmes, so three are tied",
             lambda rows, c: len(rows) == 12
             and len({r[0] for r in rows}) == 9),
        ],
    ),
    dict(
        id=6, ledger="Q257", concept="W3", tier="Window functions",
        title="Term on term",
        prompt=(
            "One row per term, in term order: the term name, how many"
            " enrolments were made on its sections, and the change from the"
            " term before.\n\n"
            "The first term has nothing before it, so its change is NULL --"
            " leave it NULL rather than turning it into 0. All six terms"
            " appear.\n\n"
            "Return: term_id, name, enrolments, change"
        ),
        solution=(
            "WITH t AS (SELECT te.term_id, te.name,"
            " COUNT(e.enrolment_id) AS n FROM terms te"
            " LEFT JOIN sections s ON s.term_id = te.term_id"
            " LEFT JOIN enrolments e ON e.section_id = s.section_id"
            " GROUP BY 1, 2)"
            " SELECT term_id, name, n, n - LAG(n) OVER (ORDER BY term_id)"
            " FROM t"
        ),
        trap_sql=(
            "WITH t AS (SELECT te.term_id, te.name,"
            " COUNT(e.enrolment_id) AS n FROM terms te"
            " LEFT JOIN sections s ON s.term_id = te.term_id"
            " LEFT JOIN enrolments e ON e.section_id = s.section_id"
            " GROUP BY 1, 2)"
            " SELECT term_id, name, n,"
            " n - LAG(n) OVER (PARTITION BY term_id ORDER BY term_id) FROM t"
        ),
        note="PARTITION BY term_id puts every term in a window of its own, so"
             " LAG looks for a previous row inside a one-row window and finds"
             " nothing: every change comes back NULL. Partition by what the"
             " rows have in COMMON and order by what separates them. Here there"
             " is one series, so there is no PARTITION at all.",
        claims=[
            ("six terms, exactly one NULL change",
             lambda rows, c: len(rows) == 6
             and sum(1 for r in rows if r[3] is None) == 1),
        ],
    ),
    dict(
        id=7, ledger="Q258", concept="W1", tier="Window functions",
        title="Billed so far",
        prompt=(
            "One row per calendar month in which anything was billed: the"
            " month as 'YYYY-MM', the amount billed in it, and the running"
            " total of everything billed up to and including that month.\n\n"
            "The running total on the last month equals the total of every"
            " payment row in the table.\n\n"
            "Return: month, month_total, running_total"
        ),
        solution=(
            "WITH m AS (SELECT strftime('%Y-%m', billed_on) AS mth,"
            " SUM(amount) AS total FROM payments GROUP BY 1)"
            " SELECT mth, ROUND(total, 2),"
            " ROUND(SUM(total) OVER (ORDER BY mth), 2) FROM m"
        ),
        trap_sql=(
            "WITH m AS (SELECT strftime('%Y-%m', billed_on) AS mth,"
            " SUM(amount) AS total FROM payments GROUP BY 1)"
            " SELECT mth, ROUND(total, 2), ROUND(SUM(total) OVER (), 2) FROM m"
        ),
        note="ORDER BY inside OVER() is the whole difference. SUM(x) OVER ()"
             " with no ORDER BY sees every row at once and repeats the same"
             " grand total on every line; SUM(x) OVER (ORDER BY mth) sees only"
             " rows up to the current one. A running total over positive"
             " numbers can only ever go up -- if yours dips, it is not one.",
        claims=[
            ("22 months, and the last running total is every payment",
             lambda rows, c: len(rows) == 22
             and abs(max(r[2] for r in rows) - c.execute(
                 "SELECT SUM(amount) FROM payments").fetchone()[0]) < 0.01),
        ],
    ),
    dict(
        id=8, ledger="Q259", concept="W3", tier="Window functions",
        title="Share of the enrolments by faculty",
        prompt=(
            "One row per faculty: the faculty, how many enrolments its"
            " departments' courses attracted, and that count as a percentage"
            " of all enrolments.\n\n"
            "Four faculties, and the four percentages add up to 100.\n\n"
            "Return: faculty, enrolments, pct_of_total"
        ),
        solution=(
            "WITH f AS (SELECT d.faculty, COUNT(*) AS n FROM enrolments e"
            " JOIN sections s ON s.section_id = e.section_id"
            " JOIN courses co ON co.course_id = s.course_id"
            " JOIN departments d ON d.department_id = co.department_id"
            " GROUP BY 1)"
            " SELECT faculty, n, ROUND(100.0 * n / SUM(n) OVER (), 2) FROM f"
        ),
        trap_sql=(
            "WITH f AS (SELECT d.faculty, COUNT(*) AS n FROM enrolments e"
            " JOIN sections s ON s.section_id = e.section_id"
            " JOIN courses co ON co.course_id = s.course_id"
            " JOIN departments d ON d.department_id = co.department_id"
            " GROUP BY 1)"
            " SELECT faculty, n,"
            " ROUND(100.0 * n / SUM(n) OVER (PARTITION BY faculty), 2) FROM f"
        ),
        note="The mirror image of question 7. There you needed the window"
             " narrowed by ORDER BY; here you need it wide open. OVER () with"
             " nothing in it is every row, which is exactly the denominator a"
             " share needs. PARTITION BY faculty shrinks the window to the row"
             " itself, so every share comes out as 100%.",
        claims=[
            ("four faculties summing to 100%",
             lambda rows, c: len(rows) == 4
             and abs(sum(r[2] for r in rows) - 100) < 0.05),
            ("the counts total every enrolment",
             lambda rows, c: sum(r[1] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM enrolments").fetchone()[0]),
        ],
    ),
    # ---------------------------------------------------------------- joins
    dict(
        id=9, ledger="Q260", concept="J2", tier="Joins",
        title="Every course, scheduled or not",
        prompt=(
            "One row for every course in the catalogue: its id, code, and how"
            " many sections have ever been scheduled for it.\n\n"
            "Six courses have never been scheduled. They must appear with 0,"
            " so all 34 courses come back.\n\n"
            "Return: course_id, code, sections"
        ),
        solution=(
            "SELECT c.course_id, c.code, COUNT(s.section_id) FROM courses c"
            " LEFT JOIN sections s ON s.course_id = c.course_id"
            " GROUP BY 1, 2"
        ),
        trap_sql=(
            "SELECT c.course_id, c.code, COUNT(s.section_id) FROM courses c"
            " JOIN sections s ON s.course_id = c.course_id GROUP BY 1, 2"
        ),
        note="An inner join can only return courses that matched, so the six"
             " unscheduled ones vanish rather than showing 0 -- and 'the ones"
             " with none' is usually what the question is really about. Note"
             " the pairing: LEFT JOIN plus COUNT(a column from the right side)."
             " COUNT(*) there would give the unscheduled courses a 1.",
        claims=[
            ("all 34 courses, six with none",
             lambda rows, c: len(rows) == 34
             and sum(1 for r in rows if r[2] == 0) == 6),
        ],
    ),
    dict(
        id=10, ledger="Q261", concept="J2", tier="Joins",
        title="Withdrawals per section",
        prompt=(
            "One row for every section: its id, its room, and how many of its"
            " enrolments were WITHDRAWN.\n\n"
            "Most sections have none. They must appear with 0, so all 84"
            " sections come back.\n\n"
            "Return: section_id, room, withdrawals"
        ),
        solution=(
            "SELECT s.section_id, s.room, COUNT(e.enrolment_id) FROM sections s"
            " LEFT JOIN enrolments e ON e.section_id = s.section_id"
            " AND e.status = 'withdrawn' GROUP BY 1, 2"
        ),
        trap_sql=(
            "SELECT s.section_id, s.room, COUNT(e.enrolment_id) FROM sections s"
            " LEFT JOIN enrolments e ON e.section_id = s.section_id"
            " WHERE e.status = 'withdrawn' GROUP BY 1, 2"
        ),
        note="A condition on the right-hand table has to go in the ON clause of"
             " a LEFT JOIN. In WHERE it runs AFTER the join has padded the"
             " unmatched sections with NULLs, and NULL = 'withdrawn' is not"
             " true, so those rows are filtered straight back out and the outer"
             " join silently becomes an inner one.",
        claims=[
            ("all 84 sections, and the withdrawals total the table",
             lambda rows, c: len(rows) == 84
             and sum(r[2] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM enrolments WHERE status = 'withdrawn'"
             ).fetchone()[0]),
        ],
    ),
    dict(
        id=11, ledger="Q262", concept="J1", tier="Joins",
        title="Classmates on the same programme",
        prompt=(
            "Pairs of students on the same programme at the same campus.\n\n"
            "Each pair once, not twice: Ann with Bob, never also Bob with Ann,"
            " and nobody paired with themselves. Order each pair so that"
            " student_a is the LOWER student_id. There are 52 pairs.\n\n"
            "Return: programme, student_a, student_b"
        ),
        solution=(
            "SELECT a.programme, a.student_id, b.student_id FROM students a"
            " JOIN students b ON b.programme = a.programme"
            " AND b.campus_id = a.campus_id"
            " AND b.student_id > a.student_id"
        ),
        trap_sql=(
            "SELECT a.programme, a.student_id, b.student_id FROM students a"
            " JOIN students b ON b.programme = a.programme"
            " AND b.campus_id = a.campus_id"
            " AND b.student_id <> a.student_id"
        ),
        note="<> only stops a row pairing with itself; it still lets each pair"
             " through in both directions, so you get exactly twice as many"
             " rows as there are pairs. Use > (or <) on the id instead: it"
             " excludes the self-match AND fixes an order, so only one of the"
             " two directions survives.",
        claims=[
            ("52 pairs, none of them a mirror of another",
             lambda rows, c: len(rows) == 52
             and len({frozenset((r[1], r[2])) for r in rows}) == 52),
            ("student_a is always the lower id",
             lambda rows, c: all(r[1] < r[2] for r in rows)),
        ],
    ),
    dict(
        id=12, ledger="Q263", concept="J2", tier="Joins",
        title="Textbooks nobody assigns",
        prompt=(
            "Every textbook that appears on no course reading list at all.\n\n"
            "Write it as an outer join that keeps the non-matches, rather than"
            " with NOT IN. There are 7 such books.\n\n"
            "Return: book_id, title"
        ),
        solution=(
            "SELECT b.book_id, b.title FROM textbooks b"
            " LEFT JOIN course_books cb ON cb.book_id = b.book_id"
            " WHERE cb.book_id IS NULL"
        ),
        trap_sql=(
            "SELECT b.book_id, b.title FROM textbooks b"
            " LEFT JOIN course_books cb ON cb.book_id = b.book_id"
            " AND cb.book_id IS NULL"
        ),
        note="The anti-join is two halves and both matter: LEFT JOIN to keep"
             " the unmatched books, then WHERE <right column> IS NULL to keep"
             " ONLY those. Moving that test into ON changes its meaning"
             " entirely -- it becomes part of what counts as a match, matches"
             " nothing, and hands back all 30 books.",
        claims=[
            ("7 books, none of them on any reading list",
             lambda rows, c: len(rows) == 7
             and not {r[0] for r in rows} & {
                 x[0] for x in c.execute(
                     "SELECT DISTINCT book_id FROM course_books")}),
        ],
    ),
    # --------------------------------------------------------- aggregation
    dict(
        id=13, ledger="Q264", concept="A2", tier="Aggregation",
        title="Graded and not",
        prompt=(
            "One row per term: its name, how many enrolments were made on its"
            " sections, and how many of those carry a grade.\n\n"
            "Active and withdrawn enrolments have no grade, so the two counts"
            " differ in every term.\n\n"
            "Return: term_id, name, enrolments, graded"
        ),
        solution=(
            "SELECT te.term_id, te.name, COUNT(*), COUNT(e.grade)"
            " FROM terms te JOIN sections s ON s.term_id = te.term_id"
            " JOIN enrolments e ON e.section_id = s.section_id"
            " GROUP BY 1, 2"
        ),
        trap_sql=(
            "SELECT te.term_id, te.name, COUNT(*), COUNT(*)"
            " FROM terms te JOIN sections s ON s.term_id = te.term_id"
            " JOIN enrolments e ON e.section_id = s.section_id"
            " GROUP BY 1, 2"
        ),
        note="COUNT(*) counts rows. COUNT(column) counts rows where that column"
             " is not NULL. That single difference is the cheapest way to count"
             " 'how many of these have a value' -- no CASE, no subquery. It is"
             " also why COUNT(some_column) after a LEFT JOIN gives a genuine"
             " zero instead of a phantom 1.",
        claims=[
            ("six terms, and graded is below total in every one",
             lambda rows, c: len(rows) == 6
             and all(r[3] < r[2] for r in rows)),
        ],
    ),
    dict(
        id=14, ledger="Q265", concept="A3", tier="Aggregation",
        title="Which programmes were busy in 2026",
        prompt=(
            "Counting only enrolments made on or after 2026-01-01, one row per"
            " programme, keeping the programmes with at least 10 of them.\n\n"
            "Six of the nine programmes clear the bar.\n\n"
            "Return: programme, enrolments"
        ),
        solution=(
            "SELECT st.programme, COUNT(*) FROM enrolments e"
            " JOIN students st ON st.student_id = e.student_id"
            " WHERE e.enrolled_on >= '2026-01-01'"
            " GROUP BY 1 HAVING COUNT(*) >= 10"
        ),
        trap_sql=(
            "SELECT st.programme, COUNT(*) FROM enrolments e"
            " JOIN students st ON st.student_id = e.student_id"
            " GROUP BY 1"
            " HAVING e.enrolled_on >= '2026-01-01' AND COUNT(*) >= 10"
        ),
        note="WHERE throws away ROWS before grouping; HAVING throws away GROUPS"
             " after. The date test is about a row, so it belongs in WHERE."
             " Put it in HAVING and SQLite does not complain -- it picks one"
             " arbitrary row's enrolled_on to test, and every count you get"
             " back is over all history rather than 2026.",
        claims=[
            ("six programmes clear 10 in 2026",
             lambda rows, c: len(rows) == 6 and all(r[1] >= 10 for r in rows)),
        ],
    ),
    dict(
        id=15, ledger="Q266", concept="A1", tier="Aggregation",
        title="Enrolment status by delivery mode",
        prompt=(
            "One row per delivery mode, with the number of its enrolments in"
            " each of the three statuses side by side as columns.\n\n"
            "Three delivery modes, and the three columns together account for"
            " every enrolment.\n\n"
            "Return: delivery, completed, active, withdrawn"
        ),
        solution=(
            "SELECT s.delivery,"
            " SUM(CASE WHEN e.status = 'completed' THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN e.status = 'active' THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN e.status = 'withdrawn' THEN 1 ELSE 0 END)"
            " FROM sections s JOIN enrolments e"
            " ON e.section_id = s.section_id GROUP BY 1"
        ),
        trap_sql=(
            "SELECT s.delivery,"
            " COUNT(CASE WHEN e.status = 'completed' THEN 1 ELSE 0 END),"
            " COUNT(CASE WHEN e.status = 'active' THEN 1 ELSE 0 END),"
            " COUNT(CASE WHEN e.status = 'withdrawn' THEN 1 ELSE 0 END)"
            " FROM sections s JOIN enrolments e"
            " ON e.section_id = s.section_id GROUP BY 1"
        ),
        note="Pick ONE of two shapes and stick to it: SUM(CASE WHEN c THEN 1"
             " ELSE 0 END) or COUNT(CASE WHEN c THEN 1 END). The mixture in the"
             " trap -- COUNT over an ELSE 0 -- counts every row, because 0 is a"
             " value and COUNT only skips NULL. All three columns come back"
             " identical to the row count, which is the tell.",
        claims=[
            ("three modes, and the columns total every enrolment",
             lambda rows, c: len(rows) == 3
             and sum(r[1] + r[2] + r[3] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM enrolments").fetchone()[0]),
        ],
    ),
    dict(
        id=16, ledger="Q267", concept="A2", tier="Aggregation",
        title="Average mark, where there is one",
        prompt=(
            "One row per programme: how many enrolments its students made, how"
            " many of those carry a grade, and the average of the grades that"
            " exist.\n\n"
            "Only completed enrolments are graded, so in every programme the"
            " average must be over the graded ones alone -- not over everyone"
            " enrolled. All nine programmes appear.\n\n"
            "Return: programme, enrolments, graded, avg_grade"
        ),
        solution=(
            "SELECT st.programme, COUNT(*), COUNT(e.grade),"
            " ROUND(AVG(e.grade), 2) FROM enrolments e"
            " JOIN students st ON st.student_id = e.student_id GROUP BY 1"
        ),
        trap_sql=(
            "SELECT st.programme, COUNT(*), COUNT(e.grade),"
            " ROUND(SUM(e.grade) * 1.0 / COUNT(*), 2) FROM enrolments e"
            " JOIN students st ON st.student_id = e.student_id GROUP BY 1"
        ),
        note="AVG already ignores NULLs -- it divides by the number of non-NULL"
             " values, not by the number of rows. Rebuilding it as SUM/COUNT(*)"
             " quietly puts the ungraded enrolments into the denominator and"
             " drags every average down by about a third here. If you ever do"
             " want SUM over rows rather than values, that is"
             " SUM(COALESCE(grade, 0)) and say so.",
        claims=[
            ("nine programmes, each with fewer graded than enrolled",
             lambda rows, c: len(rows) == 9
             and all(r[2] < r[1] for r in rows)),
            ("every average sits well above the SUM/COUNT(*) version",
             lambda rows, c: all(r[3] > 55 for r in rows)),
        ],
    ),
    # ------------------------------------------------- subqueries & EXISTS
    dict(
        id=17, ledger="Q268", concept="E1", tier="Subqueries & EXISTS",
        title="Students who have reached level 4",
        prompt=(
            "Every student who has ever enrolled on a level-4 course.\n\n"
            "Courses sit under sections and sections carry the enrolment. One"
            " row per student, however many level-4 courses they took -- and"
            " several took more than one.\n\n"
            "Return: student_id, name"
        ),
        solution=(
            "SELECT st.student_id, st.name FROM students st"
            " WHERE EXISTS (SELECT 1 FROM enrolments e"
            " JOIN sections s ON s.section_id = e.section_id"
            " JOIN courses c ON c.course_id = s.course_id"
            " WHERE e.student_id = st.student_id AND c.level = 4)"
        ),
        trap_sql=(
            "SELECT st.student_id, st.name FROM students st"
            " JOIN enrolments e ON e.student_id = st.student_id"
            " JOIN sections s ON s.section_id = e.section_id"
            " JOIN courses c ON c.course_id = s.course_id"
            " WHERE c.level = 4"
        ),
        note="Joining down to courses to answer a question ABOUT students"
             " changes the grain: you get one row per qualifying enrolment, so"
             " a student who took two level-4 courses appears twice. EXISTS"
             " asks the question without changing what a row is -- it returns"
             " yes or no and stops at the first hit. SELECT DISTINCT would"
             " patch the join, but EXISTS says what you meant.",
        claims=[
            ("no student is listed twice",
             lambda rows, c: len({r[0] for r in rows}) == len(rows)),
            ("at least one student took two, so a plain join would double up",
             lambda rows, c: c.execute(
                 "SELECT MAX(n) FROM (SELECT COUNT(*) n FROM enrolments e"
                 " JOIN sections s ON s.section_id = e.section_id"
                 " JOIN courses c ON c.course_id = s.course_id"
                 " WHERE c.level = 4 GROUP BY e.student_id)").fetchone()[0] > 1),
        ],
    ),
    dict(
        id=18, ledger="Q269", concept="E1", tier="Subqueries & EXISTS",
        title="Never taught online",
        prompt=(
            "Every instructor who has never taught a section delivered"
            " ONLINE. Two of the sixteen qualify.\n\n"
            "Watch out: some online sections have no instructor assigned at"
            " all, which is what makes the obvious answer wrong.\n\n"
            "Return: instructor_id, name"
        ),
        solution=(
            "SELECT i.instructor_id, i.name FROM instructors i"
            " WHERE NOT EXISTS (SELECT 1 FROM sections s"
            " WHERE s.instructor_id = i.instructor_id"
            " AND s.delivery = 'online')"
        ),
        trap_sql=(
            "SELECT i.instructor_id, i.name FROM instructors i"
            " WHERE i.instructor_id NOT IN"
            " (SELECT instructor_id FROM sections WHERE delivery = 'online')"
        ),
        note="NOT IN over a list containing even one NULL returns no rows at"
             " all. 'Is 7 not in (3, 5, NULL)?' -- SQL cannot say no, because"
             " NULL might have been 7, so the answer is NULL and nothing"
             " passes. NOT EXISTS has no such hole. Either use NOT EXISTS, or"
             " add WHERE instructor_id IS NOT NULL inside the subquery.",
        claims=[
            ("two instructors, and some online sections are unstaffed",
             lambda rows, c: len(rows) == 2 and c.execute(
                 "SELECT COUNT(*) FROM sections WHERE delivery = 'online'"
                 " AND instructor_id IS NULL").fetchone()[0] > 0),
        ],
    ),
    dict(
        id=19, ledger="Q270", concept="E2", tier="Subqueries & EXISTS",
        title="Dear for its own publisher",
        prompt=(
            "Every textbook priced above the average list_price of the books"
            " from ITS OWN publisher -- not above the average across the whole"
            " catalogue.\n\n"
            "One row per book.\n\n"
            "Return: book_id, title, publisher, list_price"
        ),
        solution=(
            "SELECT b.book_id, b.title, b.publisher, b.list_price"
            " FROM textbooks b WHERE b.list_price >"
            " (SELECT AVG(b2.list_price) FROM textbooks b2"
            " WHERE b2.publisher = b.publisher)"
        ),
        trap_sql=(
            "SELECT b.book_id, b.title, b.publisher, b.list_price"
            " FROM textbooks b"
            " WHERE b.list_price > (SELECT AVG(list_price) FROM textbooks)"
        ),
        note="The correlation is the single line WHERE b2.publisher ="
             " b.publisher. Without it the subquery runs once and every book is"
             " compared with the same number; with it the subquery is"
             " re-evaluated per row against that row's own publisher. A cheap"
             " book from a cheap publisher can beat its own average and lose to"
             " the global one, which is why the two answers differ.",
        claims=[
            ("every publisher contributes at least one book",
             lambda rows, c: len({r[2] for r in rows}) == 5),
        ],
    ),
    # ---------------------------------------------------------------- dates
    dict(
        id=20, ledger="Q271", concept="D1", tier="Dates",
        title="The five slowest payments to settle",
        prompt=(
            "The five settled payments that took the longest from being billed"
            " to being paid, longest first.\n\n"
            "Days must be a whole number. Break ties on days by payment_id"
            " ascending, so the five are unambiguous.\n\n"
            "Return: payment_id, billed_on, paid_on, days"
        ),
        solution=(
            "SELECT payment_id, billed_on, paid_on,"
            " CAST(julianday(paid_on) - julianday(billed_on) AS INTEGER)"
            " AS days FROM payments WHERE paid_on IS NOT NULL"
            " ORDER BY days DESC, payment_id LIMIT 5"
        ),
        trap_sql=(
            "SELECT payment_id, billed_on, paid_on,"
            " paid_on - billed_on AS days FROM payments"
            " WHERE paid_on IS NOT NULL ORDER BY days DESC, payment_id LIMIT 5"
        ),
        note="Dates in SQLite are TEXT. Subtracting one from another does not"
             " subtract dates -- SQLite coerces each string to a number, which"
             " reads '2026-06-30' as 2026 and stops at the dash, so the answer"
             " is the difference in YEARS, usually 0. julianday() turns a date"
             " into a day number, and the difference between two of those is"
             " days.",
        claims=[
            ("five rows, all with a positive whole number of days",
             lambda rows, c: len(rows) == 5
             and all(isinstance(r[3], int) and r[3] > 0 for r in rows)),
        ],
    ),
    dict(
        id=21, ledger="Q272", concept="D1", tier="Dates",
        title="Enrolled before the term began",
        prompt=(
            "How many enrolments were made BEFORE their term's start date,"
            " broken down by term.\n\n"
            "The enrolment date is on the enrolment; the start date is on the"
            " term, reached through the section. All six terms have some.\n\n"
            "Return: term_id, name, early_enrolments"
        ),
        solution=(
            "SELECT t.term_id, t.name, COUNT(*) FROM enrolments e"
            " JOIN sections s ON s.section_id = e.section_id"
            " JOIN terms t ON t.term_id = s.term_id"
            " WHERE julianday(e.enrolled_on) < julianday(t.starts_on)"
            " GROUP BY 1, 2"
        ),
        trap_sql=(
            "SELECT t.term_id, t.name, COUNT(*) FROM enrolments e"
            " JOIN sections s ON s.section_id = e.section_id"
            " JOIN terms t ON t.term_id = s.term_id"
            " WHERE (e.enrolled_on - t.starts_on) < 0 GROUP BY 1, 2"
        ),
        note="Two ISO dates compare correctly as plain strings, so"
             " e.enrolled_on < t.starts_on would also have been right here --"
             " '2025-01-04' really is less than '2025-01-13' alphabetically."
             " What is never right is ARITHMETIC on them. The trap subtracts,"
             " which coerces both to years and compares 2025 - 2025 = 0,"
             " quietly finding only the enrolments that crossed a new year.",
        claims=[
            ("all six terms, and the total is under every enrolment",
             lambda rows, c: len(rows) == 6
             and 0 < sum(r[2] for r in rows) < c.execute(
                 "SELECT COUNT(*) FROM enrolments").fetchone()[0]),
        ],
    ),
    dict(
        id=22, ledger="Q273", concept="D1", tier="Dates",
        title="Assessment deadlines by month",
        prompt=(
            "One row per calendar month in which any assessment falls due: the"
            " month as 'YYYY-MM', and how many are due in it.\n\n"
            "The data spans two academic years, so November 2024 and November"
            " 2025 are different months and must not be added together. There"
            " are 18 such months.\n\n"
            "Return: month, assessments"
        ),
        solution=(
            "SELECT strftime('%Y-%m', due_on), COUNT(*)"
            " FROM assessments GROUP BY 1"
        ),
        trap_sql=(
            "SELECT strftime('%m', due_on), COUNT(*)"
            " FROM assessments GROUP BY 1"
        ),
        note="%m alone is the month number with no year attached, so the two"
             " Novembers collapse into one row and you get at most twelve rows"
             " out of a data set covering two years. Grouping by a date always"
             " needs every component down to the level you want. The quickest"
             " sanity check is the row count.",
        claims=[
            ("18 months, more than a single year could produce",
             lambda rows, c: len(rows) == 18),
            ("the counts total every assessment",
             lambda rows, c: sum(r[1] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM assessments").fetchone()[0]),
        ],
    ),
    # -------------------------------------------------------------- NULLs
    dict(
        id=23, ledger="Q274", concept="C7", tier="NULLs",
        title="Settled, outstanding, or waived",
        prompt=(
            "Classify every payment into one of three states and count them:\n"
            "  'settled'     if paid_on has a date\n"
            "  'waived'      if it has no paid_on and status is WAIVED\n"
            "  'outstanding' otherwise\n\n"
            "All 136 payments land in exactly one state.\n\n"
            "Return: state, payments"
        ),
        solution=(
            "SELECT CASE WHEN paid_on IS NOT NULL THEN 'settled'"
            " WHEN status = 'WAIVED' THEN 'waived'"
            " ELSE 'outstanding' END, COUNT(*) FROM payments GROUP BY 1"
        ),
        trap_sql=(
            "SELECT CASE WHEN paid_on <> NULL THEN 'settled'"
            " WHEN status = 'WAIVED' THEN 'waived'"
            " ELSE 'outstanding' END, COUNT(*) FROM payments GROUP BY 1"
        ),
        note="<> NULL is never true -- and neither is = NULL. Both evaluate to"
             " NULL, which CASE treats as not-matched, so that branch can never"
             " fire and every settled payment falls through to a later one."
             " The only tests that work are IS NULL and IS NOT NULL.",
        claims=[
            ("three states covering all 136 payments",
             lambda rows, c: len(rows) == 3
             and sum(r[1] for r in rows) == 136),
            ("the settled count matches the rows with a paid_on",
             lambda rows, c: dict(rows)["settled"] == c.execute(
                 "SELECT COUNT(*) FROM payments WHERE paid_on IS NOT NULL"
             ).fetchone()[0]),
        ],
    ),
    dict(
        id=24, ledger="Q275", concept="C7", tier="NULLs",
        title="Everyone not funding themselves",
        prompt=(
            "Count students by funding band, excluding the self-funded, and"
            " counting the ones with NO funding band recorded as 'none'.\n\n"
            "41 of the 60 students are not self-funded -- seven of them because"
            " they have no band at all.\n\n"
            "Return: band, students  (band is 'grant', 'sponsor' or 'none')"
        ),
        solution=(
            "SELECT COALESCE(funding_band, 'none'), COUNT(*) FROM students"
            " WHERE funding_band IS NOT 'self' GROUP BY 1"
        ),
        trap_sql=(
            "SELECT COALESCE(funding_band, 'none'), COUNT(*) FROM students"
            " WHERE funding_band <> 'self' GROUP BY 1"
        ),
        note="funding_band <> 'self' drops the seven unrecorded students"
             " without a word, because NULL <> 'self' is NULL rather than true."
             " Any comparison on a nullable column silently excludes the NULLs."
             " SQLite's IS NOT is null-safe and reads the way you meant it; the"
             " portable spelling is"
             " (funding_band IS NULL OR funding_band <> 'self').",
        claims=[
            ("41 students in three bands, seven of them unrecorded",
             lambda rows, c: sum(r[1] for r in rows) == 41
             and len(rows) == 3 and dict(rows)["none"] == 7),
        ],
    ),
    # ----------------------------------------------------- set operations
    dict(
        id=25, ledger="Q276", concept="S1", tier="Set operations",
        title="Billed in a month nobody enrolled",
        prompt=(
            "Months in which at least one payment was billed but NO enrolment"
            " was made. Months are 'YYYY-MM'.\n\n"
            "Billing runs all year while enrolment clusters around the terms,"
            " so this catches the quiet months. Nine qualify.\n\n"
            "Return: month"
        ),
        solution=(
            "SELECT DISTINCT strftime('%Y-%m', billed_on) FROM payments"
            " EXCEPT"
            " SELECT DISTINCT strftime('%Y-%m', enrolled_on) FROM enrolments"
        ),
        trap_sql=(
            "SELECT DISTINCT strftime('%Y-%m', enrolled_on) FROM enrolments"
            " EXCEPT"
            " SELECT DISTINCT strftime('%Y-%m', billed_on) FROM payments"
        ),
        note="EXCEPT is directional: A EXCEPT B is what is in A and not in B,"
             " and swapping the two asks the opposite question. Here the swap"
             " asks which months took enrolments but billed nothing, and the"
             " answer is a single different month -- a plausible-looking result"
             " that is simply the wrong question.",
        claims=[
            ("nine months, none of which has any enrolment",
             lambda rows, c: len(rows) == 9
             and not {r[0] for r in rows} & {
                 x[0] for x in c.execute(
                     "SELECT DISTINCT strftime('%Y-%m', enrolled_on)"
                     " FROM enrolments")}),
        ],
    ),
    dict(
        id=26, ledger="Q277", concept="S1", tier="Set operations",
        title="Required reading on a first-year course",
        prompt=(
            "Textbooks that are BOTH marked required (required = 1) on some"
            " course AND appear on the reading list of a level-1 course.\n\n"
            "The two need not be the same course: a book required on a level-3"
            " course and merely recommended on a level-1 one still counts."
            " Fifteen books qualify.\n\n"
            "Return: book_id, title"
        ),
        solution=(
            "SELECT b.book_id, b.title FROM textbooks b WHERE b.book_id IN ("
            " SELECT book_id FROM course_books WHERE required = 1"
            " INTERSECT"
            " SELECT cb.book_id FROM course_books cb"
            " JOIN courses c ON c.course_id = cb.course_id WHERE c.level = 1)"
        ),
        trap_sql=(
            "SELECT b.book_id, b.title FROM textbooks b WHERE b.book_id IN ("
            " SELECT book_id FROM course_books WHERE required = 1"
            " UNION"
            " SELECT cb.book_id FROM course_books cb"
            " JOIN courses c ON c.course_id = cb.course_id WHERE c.level = 1)"
        ),
        note="INTERSECT keeps rows present in BOTH sides; UNION keeps rows"
             " present in EITHER. 'And' in English means INTERSECT here even"
             " though the sentence contains an 'and', which is the usual place"
             " this goes wrong. Both operators dedupe, so neither needs a"
             " DISTINCT of its own.",
        claims=[
            ("fifteen books, each required somewhere",
             lambda rows, c: len(rows) == 15 and all(
                 c.execute("SELECT COUNT(*) FROM course_books WHERE book_id = ?"
                           " AND required = 1", (r[0],)).fetchone()[0] > 0
                 for r in rows)),
        ],
    ),
    # -------------------------------------------------------------- grain
    dict(
        id=27, ledger="Q278", concept="C2", tier="Grain",
        title="Students and assessments on each section",
        prompt=(
            "One row per section: how many students are enrolled on it, and how"
            " many assessments it has.\n\n"
            "The two are independent -- a section can have many of one and none"
            " of the other. A section with none of something shows 0, not NULL."
            " All 84 sections appear.\n\n"
            "Return: section_id, students, assessments"
        ),
        solution=(
            "SELECT s.section_id,"
            " (SELECT COUNT(*) FROM enrolments e"
            " WHERE e.section_id = s.section_id),"
            " (SELECT COUNT(*) FROM assessments a"
            " WHERE a.section_id = s.section_id)"
            " FROM sections s"
        ),
        trap_sql=(
            "SELECT s.section_id, COUNT(e.enrolment_id),"
            " COUNT(a.assessment_id) FROM sections s"
            " LEFT JOIN enrolments e ON e.section_id = s.section_id"
            " LEFT JOIN assessments a ON a.section_id = s.section_id"
            " GROUP BY 1"
        ),
        note="Joining two child tables to the same parent multiplies them: a"
             " section with 10 students and 3 assessments produces 30 rows, so"
             " the student count comes out 3x too big and the assessment count"
             " 10x too big. COUNT(DISTINCT ...) would paper over it here, but"
             " a SUM could not. Two independent measures want two independent"
             " subqueries -- or two CTEs, each aggregated to one row per"
             " section before they meet.",
        claims=[
            ("all 84 sections, and both totals match their tables",
             lambda rows, c: len(rows) == 84
             and sum(r[1] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM enrolments").fetchone()[0]
             and sum(r[2] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM assessments").fetchone()[0]),
        ],
    ),
    dict(
        id=28, ledger="Q279", concept="C2", tier="Grain",
        title="What the library spent by publisher",
        prompt=(
            "One row per publisher, with the total value of the library copies"
            " held across all reading lists.\n\n"
            "Each course_books row is worth copies_held * list_price. Rows with"
            " no copies_held recorded contribute nothing. Every line must be"
            " priced on its own copies and its own book.\n\n"
            "Return: publisher, value"
        ),
        solution=(
            "SELECT b.publisher, ROUND(SUM(cb.copies_held * b.list_price), 2)"
            " FROM course_books cb JOIN textbooks b ON b.book_id = cb.book_id"
            " GROUP BY 1"
        ),
        trap_sql=(
            "SELECT b.publisher, ROUND(SUM(cb.copies_held)"
            " * AVG(b.list_price), 2)"
            " FROM course_books cb JOIN textbooks b ON b.book_id = cb.book_id"
            " GROUP BY 1"
        ),
        note="Do the arithmetic inside the aggregate, one row at a time, then"
             " add up: SUM(a * b), not SUM(a) * AVG(b). The two agree only if"
             " every row carries the same price, which is never true -- an"
             " expensive book held once and a cheap one held twenty times get"
             " averaged into a price neither of them has.",
        claims=[
            ("five publishers, and the total matches the whole join",
             lambda rows, c: len(rows) == 5 and abs(
                 sum(r[1] for r in rows) - c.execute(
                     "SELECT SUM(cb.copies_held * b.list_price)"
                     " FROM course_books cb JOIN textbooks b"
                     " ON b.book_id = cb.book_id").fetchone()[0]) < 0.5),
        ],
    ),
    # ------------------------------------------------------------ general
    dict(
        id=29, ledger="Q280", concept="general", tier="General",
        title="Courses by credit band",
        prompt=(
            "Put every course into one of three bands by credits and count"
            " them:\n"
            "  'major'    30 credits or more\n"
            "  'standard' 15 to 29 credits\n"
            "  'short'    everything else\n\n"
            "All 34 courses land in exactly one band.\n\n"
            "Return: band, courses"
        ),
        solution=(
            "SELECT CASE WHEN credits >= 30 THEN 'major'"
            " WHEN credits >= 15 THEN 'standard'"
            " ELSE 'short' END, COUNT(*) FROM courses GROUP BY 1"
        ),
        trap_sql=(
            "SELECT CASE WHEN credits >= 15 THEN 'standard'"
            " WHEN credits >= 30 THEN 'major'"
            " ELSE 'short' END, COUNT(*) FROM courses GROUP BY 1"
        ),
        note="CASE is first-match-wins, so the order of the WHEN branches is"
             " part of the logic, not a matter of taste. Test the narrowest"
             " band first. Put the 15 test ahead of the 30 test and every"
             " 30-credit course matches it on the way past -- the 'major'"
             " branch is unreachable and never appears at all. The check that"
             " catches it is arithmetic: do the bands sum to 34?",
        claims=[
            ("three bands covering all 34 courses",
             lambda rows, c: len(rows) == 3
             and sum(r[1] for r in rows) == 34),
        ],
    ),
    dict(
        id=30, ledger="Q281", concept="C2", tier="General",
        title="How many departments does each campus actually run",
        prompt=(
            "One row per campus: its name, how many DISTINCT departments have"
            " had a section scheduled, and how many sections that was in"
            " total.\n\n"
            "The path runs campus -> department -> course -> section, so the"
            " same department is reached once per section. All four campuses"
            " appear, and no campus has more than three departments.\n\n"
            "Return: name, departments, sections"
        ),
        solution=(
            "SELECT cm.name, COUNT(DISTINCT d.department_id),"
            " COUNT(s.section_id) FROM campuses cm"
            " JOIN departments d ON d.campus_id = cm.campus_id"
            " JOIN courses co ON co.department_id = d.department_id"
            " JOIN sections s ON s.course_id = co.course_id"
            " GROUP BY 1"
        ),
        trap_sql=(
            "SELECT cm.name, COUNT(d.department_id), COUNT(s.section_id)"
            " FROM campuses cm"
            " JOIN departments d ON d.campus_id = cm.campus_id"
            " JOIN courses co ON co.department_id = d.department_id"
            " JOIN sections s ON s.course_id = co.course_id"
            " GROUP BY 1"
        ),
        note="Once you join down a chain, the parent repeats once per leaf --"
             " so COUNT(department_id) counts sections, not departments, and"
             " comes back identical to the section count. Counting anything"
             " above the grain of the joined row needs DISTINCT. The tell is"
             " two columns that should differ coming back equal.",
        claims=[
            ("four campuses, none running more than three departments",
             lambda rows, c: len(rows) == 4
             and max(r[1] for r in rows) <= 3),
            ("the section counts total every scheduled section",
             lambda rows, c: sum(r[2] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM sections").fetchone()[0]),
        ],
    ),
]

BY_ID = {ex["id"]: ex for ex in EXERCISES}
TIERS = list(dict.fromkeys(ex["tier"] for ex in EXERCISES))


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
        detail += f"\n  Expected but missing:  {missing[0]}"
    if unexpected:
        detail += f"\n  Returned but wrong:    {unexpected[0]}"
    return False, (f"Right row count ({len(got)}), but the values differ "
                   f"in {len(missing)} row(s).{detail}")
