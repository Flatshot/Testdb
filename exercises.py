"""Practice exercises with reference solutions, used by the GUI to grade answers.

These 30 questions (ledger Q372-Q401) run on the college schema, re-seeded
(SEED 329 -> 365) and slightly larger again: 83,000 enrolments across 964
sections.

Harder than Q342-Q371 in two different ways.

The first 24 keep the same shape -- one concept per question, the prompt states
the grain -- but the SQL is longer and the traps are subtler. Several now need
two CTEs where one would previously have done.

The efficiency stage is where the difficulty really moves. Last time the fast
form was the obvious form: stop wrapping the column in a function and you were
done. These six are the opposite. In every one the naive query is the readable
one, and the fix is something you would not guess:

  25  add a predicate that filters NOTHING, to unlock a composite index
  26  change which COLUMNS you select, to keep the index covering
  27  reorder an ORDER BY to match the index's own column order
  28  rewrite COUNT(DISTINCT) as a grouped subquery to lose a sort
  29  prefer a correlated NOT EXISTS over a LEFT JOIN anti-join
  30  order by the driving table, not the joined one

Each still names the plan you are aiming for, so you know when you have got
there. What it does not tell you is how. Press F6, look at what the plan
actually says, and work backwards.

Five new indexes exist to make those possible -- see schema.sql. Several are
reachable only if the query is restructured, which is the point.

Each question carries:

  concept   the mistake or technique it drills
  solution  one correct answer
  trap_sql  the tempting WRONG query -- check_questions.py asserts the grader
            rejects it. For the efficiency questions the trap returns the RIGHT
            rows and is rejected on its plan.
  note      the lesson, shown in the GUI once you get it right
  claims    facts about the data the prompt asserts, re-checked against the
            live database so a prompt cannot quietly go stale

Grading compares your result as an unordered multiset of rows, floats rounded
to 2 decimals. Row order never matters; column order does.

Spoiler warning: the reference SQL is in this file.
"""

EXERCISES = [
    # ============================================================ 1 Warm-up
    dict(
        id=1, ledger="Q372", concept="A1", tier="1 - Warm-up",
        title="Funding mix by campus",
        prompt=(
            "One row per campus id, with the number of its students on each"
            " funding band as columns -- and a fourth column for those with no"
            " band recorded.\n\n"
            "The four columns must account for every student at that campus."
            " One table, no joins.\n\n"
            "Return: campus_id, self, grant, sponsor, unrecorded"
        ),
        solution=("SELECT campus_id,"
                  " SUM(CASE WHEN funding_band = 'self' THEN 1 ELSE 0 END),"
                  " SUM(CASE WHEN funding_band = 'grant' THEN 1 ELSE 0 END),"
                  " SUM(CASE WHEN funding_band = 'sponsor' THEN 1 ELSE 0 END),"
                  " SUM(CASE WHEN funding_band IS NULL THEN 1 ELSE 0 END)"
                  " FROM students GROUP BY campus_id"),
        trap_sql=("SELECT campus_id,"
                  " SUM(CASE WHEN funding_band = 'self' THEN 1 ELSE 0 END),"
                  " SUM(CASE WHEN funding_band = 'grant' THEN 1 ELSE 0 END),"
                  " SUM(CASE WHEN funding_band = 'sponsor' THEN 1 ELSE 0 END),"
                  " SUM(CASE WHEN funding_band = NULL THEN 1 ELSE 0 END)"
                  " FROM students GROUP BY campus_id"),
        note="Three of the four branches are ordinary equality tests and the"
             " fourth cannot be. funding_band = NULL is never true -- it"
             " evaluates to NULL, CASE treats that as no-match, and the column"
             " comes back 0 everywhere. The check is that the four columns sum"
             " to the campus total; with = NULL they fall short by exactly the"
             " number of unrecorded students.",
        claims=[("four campuses, columns totalling 4000 students",
                 lambda rows, c: len(rows) == 4
                 and sum(r[1] + r[2] + r[3] + r[4] for r in rows) == 4000),
                ("every campus has some unrecorded",
                 lambda rows, c: all(r[4] > 0 for r in rows))],
    ),
    dict(
        id=2, ledger="Q373", concept="A3", tier="1 - Warm-up",
        title="Busy days that were not all withdrawals",
        prompt=(
            "Dates on which more than 400 enrolments were made, where fewer"
            " than a fifth of them were withdrawn.\n\n"
            "Both conditions are about the day as a whole, not about individual"
            " rows. One table, no joins.\n\n"
            "Return: enrolled_on, enrolments, withdrawn"
        ),
        solution=("SELECT enrolled_on, COUNT(*),"
                  " SUM(CASE WHEN status = 'withdrawn' THEN 1 ELSE 0 END)"
                  " FROM enrolments GROUP BY enrolled_on"
                  " HAVING COUNT(*) > 400"
                  " AND SUM(CASE WHEN status = 'withdrawn' THEN 1 ELSE 0 END)"
                  " * 5 < COUNT(*)"),
        trap_sql=("SELECT enrolled_on, COUNT(*),"
                  " SUM(CASE WHEN status = 'withdrawn' THEN 1 ELSE 0 END)"
                  " FROM enrolments WHERE status <> 'withdrawn'"
                  " GROUP BY enrolled_on HAVING COUNT(*) > 400"),
        note="Both tests are about the GROUP, so both belong in HAVING, and"
             " HAVING can hold any expression over aggregates -- including"
             " arithmetic relating two of them. The trap tries to express 'not"
             " many withdrawals' as a WHERE filter, but that removes the"
             " withdrawn rows before counting, so COUNT(*) no longer means what"
             " the question asked and the ratio can never be computed at all."
             " Note the ratio is written as a multiplication to keep it in"
             " integers: x * 5 < n rather than x / n < 0.2.",
        claims=[("every row clears both bars",
                 lambda rows, c: len(rows) == 137
                 and all(r[1] > 400 and r[2] * 5 < r[1] for r in rows))],
    ),
    dict(
        id=3, ledger="Q374", concept="general", tier="1 - Warm-up",
        title="Grade bands, including the ungraded",
        prompt=(
            "Put every enrolment into one of four bands and count them:\n"
            "  'distinction' grade 70 or more\n"
            "  'pass'        grade 40 to 69\n"
            "  'fail'        grade below 40\n"
            "  'ungraded'    no grade recorded\n\n"
            "All 82,911 enrolments land in exactly one band.\n\n"
            "Return: band, enrolments"
        ),
        solution=("SELECT CASE WHEN grade IS NULL THEN 'ungraded'"
                  " WHEN grade >= 70 THEN 'distinction'"
                  " WHEN grade >= 40 THEN 'pass'"
                  " ELSE 'fail' END, COUNT(*) FROM enrolments GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN grade >= 70 THEN 'distinction'"
                  " WHEN grade >= 40 THEN 'pass'"
                  " ELSE 'fail' END, COUNT(*) FROM enrolments GROUP BY 1"),
        note="The trap has no ungraded branch, so its ELSE quietly swallows"
             " every enrolment with no grade and reports 26,527 failures that"
             " were never marked. NULL does not compare as less than 40 -- it"
             " does not compare at all, so those rows fall through every WHEN"
             " and land wherever ELSE points. Test IS NULL FIRST: it is the"
             " only branch that can catch them deliberately.",
        claims=[("four bands covering all 82,911 enrolments",
                 lambda rows, c: len(rows) == 4
                 and sum(r[1] for r in rows) == 82911)],
    ),
    dict(
        id=4, ledger="Q375", concept="A2", tier="1 - Warm-up",
        title="Marks by band, and how many carry one",
        prompt=(
            "One row per enrolment status: how many enrolments have it, how"
            " many carry a grade, the average grade, and the average computed"
            " over ALL of that status's rows treating a missing grade as"
            " zero.\n\n"
            "Two of the statuses have no grades at all, so their true average"
            " is NULL while their zero-filled average is 0.\n\n"
            "Return: status, enrolments, graded, avg_grade, avg_with_zeros"
        ),
        solution=("SELECT status, COUNT(*), COUNT(grade),"
                  " ROUND(AVG(grade), 2),"
                  " ROUND(AVG(COALESCE(grade, 0)), 2)"
                  " FROM enrolments GROUP BY status"),
        trap_sql=("SELECT status, COUNT(*), COUNT(grade),"
                  " ROUND(AVG(grade), 2), ROUND(AVG(grade), 2)"
                  " FROM enrolments GROUP BY status"),
        note="This is the two behaviours side by side. AVG(grade) divides by"
             " the number of NON-NULL grades; AVG(COALESCE(grade, 0)) turns"
             " every missing grade into a real 0 first, so it divides by every"
             " row and gives a very different number. Neither is wrong -- they"
             " answer different questions. What is wrong is not knowing which"
             " one you asked for.",
        claims=[("three statuses, two with a NULL true average",
                 lambda rows, c: len(rows) == 3
                 and sum(1 for r in rows if r[3] is None) == 2),
                ("the zero-filled average is never NULL",
                 lambda rows, c: all(r[4] is not None for r in rows))],
    ),
    # ======================================================= 2 First joins
    dict(
        id=5, ledger="Q376", concept="J2", tier="2 - First joins",
        title="Online teaching per course",
        prompt=(
            "One row for every course: id, code, and how many of its sections"
            " are delivered ONLINE.\n\n"
            "Six courses have none. They must appear with 0, so all 34 courses"
            " come back.\n\n"
            "Return: course_id, code, online_sections"
        ),
        solution=("SELECT c.course_id, c.code, COUNT(s.section_id)"
                  " FROM courses c LEFT JOIN sections s"
                  " ON s.course_id = c.course_id AND s.delivery = 'online'"
                  " GROUP BY 1, 2"),
        trap_sql=("SELECT c.course_id, c.code, COUNT(s.section_id)"
                  " FROM courses c LEFT JOIN sections s"
                  " ON s.course_id = c.course_id"
                  " WHERE s.delivery = 'online' GROUP BY 1, 2"),
        note="A condition on the right-hand table has to go in the ON clause of"
             " a LEFT JOIN. In WHERE it runs AFTER the join has padded the"
             " unmatched courses with NULLs, and NULL = 'online' is not true,"
             " so those rows are filtered back out and the outer join silently"
             " becomes an inner one. Pair it with COUNT(a right-side column),"
             " or the six courses with none would report 1.",
        claims=[("all 34 courses, six with none",
                 lambda rows, c: len(rows) == 34
                 and sum(1 for r in rows if r[2] == 0) == 6)],
    ),
    dict(
        id=6, ledger="Q377", concept="E1", tier="2 - First joins",
        title="Straight to level 4",
        prompt=(
            "Students who have enrolled on a LEVEL-4 course but never on a"
            " level-1 one.\n\n"
            "Courses sit under sections, which carry the enrolment. Exactly one"
            " student qualifies out of the 2,687 who have taken anything at"
            " level 4.\n\n"
            "Return: student_id, name"
        ),
        solution=("SELECT st.student_id, st.name FROM students st"
                  " WHERE EXISTS (SELECT 1 FROM enrolments e"
                  " JOIN sections s ON s.section_id = e.section_id"
                  " JOIN courses c ON c.course_id = s.course_id"
                  " WHERE e.student_id = st.student_id AND c.level = 4)"
                  " AND NOT EXISTS (SELECT 1 FROM enrolments e"
                  " JOIN sections s ON s.section_id = e.section_id"
                  " JOIN courses c ON c.course_id = s.course_id"
                  " WHERE e.student_id = st.student_id AND c.level = 1)"),
        trap_sql=("SELECT DISTINCT st.student_id, st.name FROM students st"
                  " JOIN enrolments e ON e.student_id = st.student_id"
                  " JOIN sections s ON s.section_id = e.section_id"
                  " JOIN courses c ON c.course_id = s.course_id"
                  " WHERE c.level = 4 AND c.level <> 1"),
        note="'Has taken a level-4 course' and 'has never taken a level-1 one'"
             " are statements about the STUDENT, and only the first can be"
             " expressed as a join. A join filters rows: c.level = 4 AND"
             " c.level <> 1 asks for a single enrolment that is both, which"
             " every level-4 enrolment satisfies -- so the second condition"
             " does nothing at all. 'Never' needs NOT EXISTS, which asks about"
             " the student's whole set of enrolments rather than about one row.",
        claims=[("exactly one student, and 2,687 have taken level 4",
                 lambda rows, c: len(rows) == 1 and c.execute(
                     "SELECT COUNT(DISTINCT e.student_id) FROM enrolments e"
                     " JOIN sections s ON s.section_id = e.section_id"
                     " JOIN courses c ON c.course_id = s.course_id"
                     " WHERE c.level = 4").fetchone()[0] == 2687),
                ("that student really has no level-1 enrolment",
                 lambda rows, c: c.execute(
                     "SELECT COUNT(*) FROM enrolments e"
                     " JOIN sections s ON s.section_id = e.section_id"
                     " JOIN courses c ON c.course_id = s.course_id"
                     " WHERE e.student_id = ? AND c.level = 1",
                     (rows[0][0],)).fetchone()[0] == 0)],
    ),
    dict(
        id=7, ledger="Q378", concept="J1", tier="2 - First joins",
        title="Courses that sit alongside each other",
        prompt=(
            "Pairs of courses in the same department at the same level, where"
            " the two carry a DIFFERENT number of credits.\n\n"
            "Each pair once, ordered so code_a belongs to the lower"
            " course_id.\n\n"
            "Return: department_id, code_a, code_b"
        ),
        solution=("SELECT a.department_id, a.code, b.code FROM courses a"
                  " JOIN courses b ON b.department_id = a.department_id"
                  " AND b.level = a.level AND b.course_id > a.course_id"
                  " AND b.credits <> a.credits"),
        trap_sql=("SELECT a.department_id, a.code, b.code FROM courses a"
                  " JOIN courses b ON b.department_id = a.department_id"
                  " AND b.level = a.level AND b.course_id <> a.course_id"
                  " AND b.credits <> a.credits"),
        note="Two inequalities doing different jobs. b.credits <> a.credits is"
             " a genuine filter on which pairs qualify. b.course_id > a.course_id"
             " is not a filter at all -- it is what stops each pair appearing"
             " twice, and it has to be > rather than <>, because <> lets both"
             " directions through.",
        claims=[("no pair is a mirror of another, and all differ in credits",
                 lambda rows, c: len(rows) > 0
                 and len({frozenset((r[1], r[2])) for r in rows}) == len(rows))],
    ),
    dict(
        id=8, ledger="Q379", concept="J2", tier="2 - First joins",
        title="Courses nobody has scheduled",
        prompt=(
            "Every course that has never had a section scheduled.\n\n"
            "Write it as an outer join that keeps the non-matches, rather than"
            " with NOT IN. There are 6.\n\n"
            "Return: course_id, code"
        ),
        solution=("SELECT c.course_id, c.code FROM courses c"
                  " LEFT JOIN sections s ON s.course_id = c.course_id"
                  " WHERE s.section_id IS NULL"),
        trap_sql=("SELECT c.course_id, c.code FROM courses c"
                  " LEFT JOIN sections s ON s.course_id = c.course_id"
                  " AND s.section_id IS NULL"),
        note="The anti-join is two halves and both matter: LEFT JOIN to keep"
             " the unmatched courses, then WHERE <right column> IS NULL to keep"
             " ONLY those. Moving that test into ON changes its meaning -- it"
             " becomes part of what counts as a match, matches nothing, and"
             " hands back all 34 courses.",
        claims=[("6 courses, none of them in sections",
                 lambda rows, c: len(rows) == 6
                 and not {r[0] for r in rows} & {
                     x[0] for x in c.execute(
                         "SELECT DISTINCT course_id FROM sections")})],
    ),
    dict(
        id=9, ledger="Q380", concept="E1", tier="2 - First joins",
        title="Instructors who mentor nobody",
        prompt=(
            "Every instructor who is nobody's mentor. Twelve of the sixteen"
            " qualify.\n\n"
            "mentor_id contains a NULL, for the instructor at the top, which is"
            " what makes the obvious answer wrong.\n\n"
            "Return: instructor_id, name"
        ),
        solution=("SELECT i.instructor_id, i.name FROM instructors i"
                  " WHERE NOT EXISTS (SELECT 1 FROM instructors x"
                  " WHERE x.mentor_id = i.instructor_id)"),
        trap_sql=("SELECT i.instructor_id, i.name FROM instructors i"
                  " WHERE i.instructor_id NOT IN"
                  " (SELECT mentor_id FROM instructors)"),
        note="NOT IN over a list containing even one NULL returns no rows at"
             " all. SQL cannot rule out that the NULL was the value you are"
             " looking for, so the answer is NULL and nothing passes. NOT"
             " EXISTS has no such hole -- and note that this is a correctness"
             " difference, not a stylistic one.",
        claims=[("twelve instructors",
                 lambda rows, c: len(rows) == 12)],
    ),
    # ========================================================= 3 Recursion
    dict(
        id=10, ledger="Q381", concept="R1", tier="3 - Recursion",
        title="Everyone under Margaret Ashworth, with their depth",
        prompt=(
            "Everyone below Margaret Ashworth in the mentoring tree, with how"
            " many levels below her they sit.\n\n"
            "Her direct mentees are 1, their mentees 2, and so on. Fifteen"
            " rows; Margaret herself is not among them.\n\n"
            "Return: instructor_id, name, depth"
        ),
        solution=("WITH RECURSIVE below(id, name, depth) AS ("
                  " SELECT instructor_id, name, 1 FROM instructors"
                  " WHERE mentor_id = (SELECT instructor_id FROM instructors"
                  " WHERE name = 'Margaret Ashworth')"
                  " UNION ALL"
                  " SELECT i.instructor_id, i.name, b.depth + 1"
                  " FROM instructors i JOIN below b ON i.mentor_id = b.id)"
                  " SELECT id, name, depth FROM below"),
        trap_sql=("SELECT i.instructor_id, i.name, 1 FROM instructors i"
                  " WHERE i.mentor_id = (SELECT instructor_id FROM instructors"
                  " WHERE name = 'Margaret Ashworth')"),
        note="The depth counter is the new part, and it shows what a recursive"
             " CTE actually carries: each row remembers a value computed from"
             " the row it came from, b.depth + 1. There is no other memory"
             " available -- a step cannot see anything except the previous"
             " pass's rows and the tables it joins.",
        claims=[("15 rows, depths starting at 1",
                 lambda rows, c: len(rows) == 15
                 and min(r[2] for r in rows) == 1),
                ("only three are at depth 1",
                 lambda rows, c: sum(1 for r in rows if r[2] == 1) == 3)],
    ),
    dict(
        id=11, ledger="Q382", concept="R1", tier="3 - Recursion",
        title="What Machine Learning needs, and how far back",
        prompt=(
            "Every course CMP401 depends on, at any depth, with the FEWEST hops"
            " from CMP401 to that course.\n\n"
            "A course reachable both directly and through another counts as 1."
            " CMP401 itself is not in the answer.\n\n"
            "Return: code, hops"
        ),
        solution=("WITH RECURSIVE need(id, hops) AS ("
                  " SELECT requires_course_id, 1 FROM prerequisites"
                  " WHERE course_id = (SELECT course_id FROM courses"
                  " WHERE code = 'CMP401')"
                  " UNION ALL"
                  " SELECT p.requires_course_id, n.hops + 1"
                  " FROM prerequisites p JOIN need n ON p.course_id = n.id)"
                  " SELECT c.code, MIN(n.hops) FROM need n"
                  " JOIN courses c ON c.course_id = n.id GROUP BY c.code"),
        trap_sql=("SELECT c.code, 1 FROM prerequisites p"
                  " JOIN courses c ON c.course_id = p.requires_course_id"
                  " WHERE p.course_id = (SELECT course_id FROM courses"
                  " WHERE code = 'CMP401')"),
        note="Two things at once: the walk, and a counter carried through it."
             " A single join gives the direct prerequisites at 1 hop and stops."
             " The MIN in the outer query matters as soon as a course is"
             " reachable by two routes of different lengths -- it is not so in"
             " this data, but writing MAX instead would be a different question"
             " and you should know which one you asked.",
        claims=[("every hop count is at least 1",
                 lambda rows, c: len(rows) > 0
                 and min(r[1] for r in rows) == 1),
                ("no course is listed twice",
                 lambda rows, c: len({r[0] for r in rows}) == len(rows))],
    ),
    dict(
        id=12, ledger="Q383", concept="R1", tier="3 - Recursion",
        title="What is blocked by Programming Foundations",
        prompt=(
            "Every course that requires CMP101 'Programming Foundations',"
            " directly or indirectly.\n\n"
            "Travel the other way along prerequisites from question 11.\n\n"
            "Return: code, title"
        ),
        solution=("WITH RECURSIVE blocked(id) AS ("
                  " SELECT course_id FROM prerequisites"
                  " WHERE requires_course_id = (SELECT course_id FROM courses"
                  " WHERE code = 'CMP101')"
                  " UNION"
                  " SELECT p.course_id FROM prerequisites p"
                  " JOIN blocked b ON p.requires_course_id = b.id)"
                  " SELECT c.code, c.title FROM courses c"
                  " JOIN blocked ON blocked.id = c.course_id"),
        trap_sql=("WITH RECURSIVE blocked(id) AS ("
                  " SELECT requires_course_id FROM prerequisites"
                  " WHERE course_id = (SELECT course_id FROM courses"
                  " WHERE code = 'CMP101')"
                  " UNION"
                  " SELECT p.requires_course_id FROM prerequisites p"
                  " JOIN blocked b ON p.course_id = b.id)"
                  " SELECT c.code, c.title FROM courses c"
                  " JOIN blocked ON blocked.id = c.course_id"),
        note="A prerequisites row reads 'course_id requires"
             " requires_course_id'. Question 11 started from course_id and"
             " collected requires_course_id; this reverses BOTH -- the anchor's"
             " filter and the step's join. Reverse only one and you walk a hop"
             " out then straight back, which is why the trap returns nothing.",
        claims=[("more than one course, none of them CMP101",
                 lambda rows, c: len(rows) > 1
                 and not any(r[0] == 'CMP101' for r in rows))],
    ),
    dict(
        id=13, ledger="Q384", concept="R1", tier="3 - Recursion",
        title="Courses that depend on nothing",
        prompt=(
            "Starting from CMP401 and walking its prerequisites at any depth,"
            " which of the courses reached have NO prerequisites of their"
            " own -- the foundations of its dependency tree.\n\n"
            "CMP401 itself is excluded.\n\n"
            "Return: code, title"
        ),
        solution=("WITH RECURSIVE need(id) AS ("
                  " SELECT requires_course_id FROM prerequisites"
                  " WHERE course_id = (SELECT course_id FROM courses"
                  " WHERE code = 'CMP401')"
                  " UNION"
                  " SELECT p.requires_course_id FROM prerequisites p"
                  " JOIN need n ON p.course_id = n.id)"
                  " SELECT c.code, c.title FROM courses c JOIN need"
                  " ON need.id = c.course_id WHERE NOT EXISTS"
                  " (SELECT 1 FROM prerequisites q"
                  " WHERE q.course_id = c.course_id)"),
        trap_sql=("WITH RECURSIVE need(id) AS ("
                  " SELECT requires_course_id FROM prerequisites"
                  " WHERE course_id = (SELECT course_id FROM courses"
                  " WHERE code = 'CMP401')"
                  " UNION"
                  " SELECT p.requires_course_id FROM prerequisites p"
                  " JOIN need n ON p.course_id = n.id)"
                  " SELECT c.code, c.title FROM courses c JOIN need"
                  " ON need.id = c.course_id"),
        note="Two mechanisms in one query, and they stay separate: the"
             " recursion collects the set, then an ordinary NOT EXISTS filters"
             " it. It is tempting to try to make the recursion itself stop at"
             " the leaves, but it cannot know a course is a leaf until it has"
             " looked -- and by then it has already emitted it. Collect first,"
             " filter after.",
        claims=[("every course returned really has no prerequisites",
                 lambda rows, c: len(rows) > 0 and all(
                     c.execute("SELECT COUNT(*) FROM prerequisites p JOIN"
                               " courses c ON c.course_id = p.course_id"
                               " WHERE c.code = ?", (r[0],)).fetchone()[0] == 0
                     for r in rows))],
    ),
    # ============================================ 4 Dates, sets and pivots
    dict(
        id=14, ledger="Q385", concept="D1", tier="4 - Dates, sets and pivots",
        title="How much of each term had passed",
        prompt=(
            "One row per term: its name, its length in whole days, and the"
            " average number of whole days INTO the term at which its"
            " enrolments were made.\n\n"
            "An enrolment made before the term starts counts as a negative"
            " number of days. All six terms appear.\n\n"
            "Return: term_id, name, term_days, avg_days_in"
        ),
        solution=("SELECT t.term_id, t.name,"
                  " CAST(julianday(t.ends_on) - julianday(t.starts_on)"
                  " AS INTEGER),"
                  " ROUND(AVG(julianday(e.enrolled_on)"
                  " - julianday(t.starts_on)), 2)"
                  " FROM terms t JOIN sections s ON s.term_id = t.term_id"
                  " JOIN enrolments e ON e.section_id = s.section_id"
                  " GROUP BY 1, 2, 3"),
        trap_sql=("SELECT t.term_id, t.name,"
                  " CAST(t.ends_on - t.starts_on AS INTEGER),"
                  " ROUND(AVG(e.enrolled_on - t.starts_on), 2)"
                  " FROM terms t JOIN sections s ON s.term_id = t.term_id"
                  " JOIN enrolments e ON e.section_id = s.section_id"
                  " GROUP BY 1, 2, 3"),
        note="Dates are TEXT, so subtracting them coerces each string to a"
             " number -- '2026-04-02' reads as 2026 -- and you get a difference"
             " in years, almost always 0. julianday() converts to a day number"
             " first. Note the difference is taken INSIDE the AVG: averaging"
             " the dates and subtracting would be a different calculation, and"
             " julianday of an average is not the average of julianday.",
        claims=[("six terms, every length between 70 and 90 days",
                 lambda rows, c: len(rows) == 6
                 and all(70 <= r[2] <= 90 for r in rows))],
    ),
    dict(
        id=15, ledger="Q386", concept="D1", tier="4 - Dates, sets and pivots",
        title="The busiest month of each academic year",
        prompt=(
            "For each academic year -- taken as the calendar year of the"
            " enrolment date -- the single month with the most enrolments.\n\n"
            "Months are 'YYYY-MM'. One row per year present in the data.\n\n"
            "Return: year, month, enrolments"
        ),
        solution=("WITH m AS (SELECT strftime('%Y', enrolled_on) AS yr,"
                  " strftime('%Y-%m', enrolled_on) AS mth, COUNT(*) AS n"
                  " FROM enrolments GROUP BY 1, 2)"
                  " SELECT yr, mth, n FROM m WHERE n = (SELECT MAX(n)"
                  " FROM m m2 WHERE m2.yr = m.yr)"),
        trap_sql=("WITH m AS (SELECT strftime('%Y', enrolled_on) AS yr,"
                  " strftime('%Y-%m', enrolled_on) AS mth, COUNT(*) AS n"
                  " FROM enrolments GROUP BY 1, 2)"
                  " SELECT yr, mth, n FROM m WHERE n = (SELECT MAX(n) FROM m)"),
        note="The subquery has to be correlated to the year -- m2.yr = m.yr --"
             " or it finds the biggest month across ALL years and only that"
             " year appears. Two levels of date extraction in one query: %Y to"
             " group the years and %Y-%m to group the months, and the month"
             " must carry its year or two Januaries would merge.",
        claims=[("one row per year in the data",
                 lambda rows, c: len(rows) == c.execute(
                     "SELECT COUNT(DISTINCT strftime('%Y', enrolled_on))"
                     " FROM enrolments").fetchone()[0])],
    ),
    dict(
        id=16, ledger="Q387", concept="S1", tier="4 - Dates, sets and pivots",
        title="Billed in a month nobody enrolled",
        prompt=(
            "Months in which at least one payment was billed but NO enrolment"
            " was made. Months are 'YYYY-MM'. Nine qualify.\n\n"
            "Return: month"
        ),
        solution=("SELECT DISTINCT strftime('%Y-%m', billed_on) FROM payments"
                  " EXCEPT"
                  " SELECT DISTINCT strftime('%Y-%m', enrolled_on)"
                  " FROM enrolments"),
        trap_sql=("SELECT DISTINCT strftime('%Y-%m', enrolled_on)"
                  " FROM enrolments EXCEPT"
                  " SELECT DISTINCT strftime('%Y-%m', billed_on) FROM payments"),
        note="EXCEPT is directional: A EXCEPT B is what is in A and not in B."
             " The swap returns a different, equally plausible set of months --"
             " nothing about the result says you asked it backwards.",
        claims=[("nine months, none with any enrolment",
                 lambda rows, c: len(rows) == 9
                 and not {r[0] for r in rows} & {
                     x[0] for x in c.execute(
                         "SELECT DISTINCT strftime('%Y-%m', enrolled_on)"
                         " FROM enrolments")})],
    ),
    dict(
        id=17, ledger="Q388", concept="S1", tier="4 - Dates, sets and pivots",
        title="Books that changed their status between levels",
        prompt=(
            "Textbooks that are marked REQUIRED on at least one course and"
            " merely recommended (required = 0) on at least one other.\n\n"
            "Return: book_id, title"
        ),
        solution=("SELECT b.book_id, b.title FROM textbooks b"
                  " WHERE b.book_id IN ("
                  " SELECT book_id FROM course_books WHERE required = 1"
                  " INTERSECT"
                  " SELECT book_id FROM course_books WHERE required = 0)"),
        trap_sql=("SELECT b.book_id, b.title FROM textbooks b"
                  " WHERE b.book_id IN ("
                  " SELECT book_id FROM course_books WHERE required = 1"
                  " UNION"
                  " SELECT book_id FROM course_books WHERE required = 0)"),
        note="INTERSECT keeps rows on BOTH sides; UNION keeps rows on either."
             " The two conditions apply to the same book rather than being two"
             " lists to add together, which is what makes it an intersection"
             " even though the sentence contains an 'and'.",
        claims=[("every book returned is both required and not required"
                 " somewhere",
                 lambda rows, c: len(rows) > 0 and all(
                     c.execute("SELECT COUNT(DISTINCT required) FROM"
                               " course_books WHERE book_id = ?",
                               (r[0],)).fetchone()[0] == 2 for r in rows))],
    ),
    dict(
        id=18, ledger="Q389", concept="A1", tier="4 - Dates, sets and pivots",
        title="Status mix by term, as percentages",
        prompt=(
            "One row per term: the term name, and the percentage of its"
            " enrolments in each of the three statuses.\n\n"
            "The three percentages on each row add up to 100. All six terms"
            " appear.\n\n"
            "Return: term_id, name, pct_completed, pct_active, pct_withdrawn"
        ),
        solution=("SELECT t.term_id, t.name,"
                  " ROUND(100.0 * SUM(CASE WHEN e.status = 'completed'"
                  " THEN 1 ELSE 0 END) / COUNT(*), 2),"
                  " ROUND(100.0 * SUM(CASE WHEN e.status = 'active'"
                  " THEN 1 ELSE 0 END) / COUNT(*), 2),"
                  " ROUND(100.0 * SUM(CASE WHEN e.status = 'withdrawn'"
                  " THEN 1 ELSE 0 END) / COUNT(*), 2)"
                  " FROM terms t JOIN sections s ON s.term_id = t.term_id"
                  " JOIN enrolments e ON e.section_id = s.section_id"
                  " GROUP BY 1, 2"),
        trap_sql=("SELECT t.term_id, t.name,"
                  " ROUND(100 * SUM(CASE WHEN e.status = 'completed'"
                  " THEN 1 ELSE 0 END) / COUNT(*), 2),"
                  " ROUND(100 * SUM(CASE WHEN e.status = 'active'"
                  " THEN 1 ELSE 0 END) / COUNT(*), 2),"
                  " ROUND(100 * SUM(CASE WHEN e.status = 'withdrawn'"
                  " THEN 1 ELSE 0 END) / COUNT(*), 2)"
                  " FROM terms t JOIN sections s ON s.term_id = t.term_id"
                  " JOIN enrolments e ON e.section_id = s.section_id"
                  " GROUP BY 1, 2"),
        note="Both operands are integers, so 100 * x / n does the division in"
             " integers and truncates every percentage to a whole number --"
             " and the three then fail to add to 100. Writing 100.0 makes the"
             " whole expression float. ROUND cannot rescue it: by the time"
             " ROUND sees the value the decimals are already gone.",
        claims=[("six terms, percentages summing to 100 on each",
                 lambda rows, c: len(rows) == 6
                 and all(abs(r[2] + r[3] + r[4] - 100) < 0.05 for r in rows))],
    ),
    # ================================================== 5 Window functions
    dict(
        id=19, ledger="Q390", concept="W3", tier="5 - Window functions",
        title="Term on term, in percentage terms",
        prompt=(
            "One row per term in term order: the name, its enrolments, and the"
            " percentage change from the term before.\n\n"
            "The first term has nothing before it, so its change is NULL. A"
            " fall is negative.\n\n"
            "Return: term_id, name, enrolments, pct_change"
        ),
        solution=("WITH t AS (SELECT te.term_id, te.name,"
                  " COUNT(e.enrolment_id) AS n FROM terms te"
                  " LEFT JOIN sections s ON s.term_id = te.term_id"
                  " LEFT JOIN enrolments e ON e.section_id = s.section_id"
                  " GROUP BY 1, 2)"
                  " SELECT term_id, name, n,"
                  " ROUND(100.0 * (n - LAG(n) OVER (ORDER BY term_id))"
                  " / LAG(n) OVER (ORDER BY term_id), 2) FROM t"),
        trap_sql=("WITH t AS (SELECT te.term_id, te.name,"
                  " COUNT(e.enrolment_id) AS n FROM terms te"
                  " LEFT JOIN sections s ON s.term_id = te.term_id"
                  " LEFT JOIN enrolments e ON e.section_id = s.section_id"
                  " GROUP BY 1, 2)"
                  " SELECT term_id, name, n,"
                  " ROUND(100.0 * (n - LAG(n) OVER (ORDER BY term_id))"
                  " / n, 2) FROM t"),
        note="A percentage change divides by the PREVIOUS value, not the"
             " current one -- so LAG appears twice, once in the numerator and"
             " once as the denominator. The trap divides by n and produces"
             " plausible-looking numbers that are quietly the wrong base. The"
             " NULL on the first row comes for free either way, because"
             " anything arithmetic with NULL is NULL.",
        claims=[("six terms, exactly one NULL change",
                 lambda rows, c: len(rows) == 6
                 and sum(1 for r in rows if r[3] is None) == 1)],
    ),
    dict(
        id=20, ledger="Q391", concept="W1", tier="5 - Window functions",
        title="Cumulative share of enrolments",
        prompt=(
            "One row per term in term order: the name, its enrolments, the"
            " running total up to and including it, and that running total as a"
            " percentage of all enrolments.\n\n"
            "The last term's percentage is 100.\n\n"
            "Return: term_id, name, enrolments, running_total, pct_so_far"
        ),
        solution=("WITH t AS (SELECT te.term_id, te.name,"
                  " COUNT(e.enrolment_id) AS n FROM terms te"
                  " LEFT JOIN sections s ON s.term_id = te.term_id"
                  " LEFT JOIN enrolments e ON e.section_id = s.section_id"
                  " GROUP BY 1, 2)"
                  " SELECT term_id, name, n,"
                  " SUM(n) OVER (ORDER BY term_id),"
                  " ROUND(100.0 * SUM(n) OVER (ORDER BY term_id)"
                  " / SUM(n) OVER (), 2) FROM t"),
        trap_sql=("WITH t AS (SELECT te.term_id, te.name,"
                  " COUNT(e.enrolment_id) AS n FROM terms te"
                  " LEFT JOIN sections s ON s.term_id = te.term_id"
                  " LEFT JOIN enrolments e ON e.section_id = s.section_id"
                  " GROUP BY 1, 2)"
                  " SELECT term_id, name, n,"
                  " SUM(n) OVER (ORDER BY term_id),"
                  " ROUND(100.0 * SUM(n) OVER (ORDER BY term_id)"
                  " / SUM(n) OVER (ORDER BY term_id), 2) FROM t"),
        note="Two windows over the same column in one SELECT, doing opposite"
             " jobs: SUM(n) OVER (ORDER BY term_id) accumulates, SUM(n) OVER ()"
             " is the grand total. Use the accumulating one as the denominator"
             " and every row reads 100. Each OVER clause is independent -- they"
             " do not have to agree, and here they must not.",
        claims=[("six terms, last percentage is 100",
                 lambda rows, c: len(rows) == 6
                 and abs(max(r[4] for r in rows) - 100) < 0.01)],
    ),
    dict(
        id=21, ledger="Q392", concept="W2", tier="5 - Window functions",
        title="The two biggest courses in each faculty",
        prompt=(
            "For each faculty, the two courses with the most enrolments, with"
            " their rank.\n\n"
            "If two courses tie for second, both appear. Rank within the"
            " faculty, highest first.\n\n"
            "Return: faculty, code, enrolments, rank"
        ),
        solution=("WITH c AS (SELECT d.faculty, co.code, COUNT(*) AS n"
                  " FROM enrolments e"
                  " JOIN sections s ON s.section_id = e.section_id"
                  " JOIN courses co ON co.course_id = s.course_id"
                  " JOIN departments d ON d.department_id = co.department_id"
                  " GROUP BY 1, 2),"
                  " r AS (SELECT *, RANK() OVER (PARTITION BY faculty"
                  " ORDER BY n DESC) rk FROM c)"
                  " SELECT faculty, code, n, rk FROM r WHERE rk <= 2"),
        trap_sql=("WITH c AS (SELECT d.faculty, co.code, COUNT(*) AS n"
                  " FROM enrolments e"
                  " JOIN sections s ON s.section_id = e.section_id"
                  " JOIN courses co ON co.course_id = s.course_id"
                  " JOIN departments d ON d.department_id = co.department_id"
                  " GROUP BY 1, 2),"
                  " r AS (SELECT *, RANK() OVER (ORDER BY n DESC) rk"
                  " FROM c)"
                  " SELECT faculty, code, n, rk FROM r WHERE rk <= 2"),
        note="Without PARTITION BY the ranking runs across the whole result,"
             " so rk <= 2 gives the two biggest courses in the COLLEGE and both"
             " may come from one faculty. PARTITION BY restarts the numbering"
             " per group. Use RANK rather than ROW_NUMBER so that a tie at"
             " second place returns both courses instead of picking one"
             " arbitrarily -- there is no tie in this data, but the question"
             " asks for the ones that earned the position.",
        claims=[("four faculties, at least two rows each",
                 lambda rows, c: len({r[0] for r in rows}) == 4
                 and len(rows) >= 8)],
    ),
    dict(
        id=22, ledger="Q393", concept="W1", tier="5 - Window functions",
        title="Three-term rolling average",
        prompt=(
            "One row per term in order: the name, its enrolments, and the"
            " average over that term and the two before it.\n\n"
            "The first term averages just itself, the second two terms, and"
            " every term after that three.\n\n"
            "Return: term_id, name, enrolments, rolling_avg"
        ),
        solution=("WITH t AS (SELECT te.term_id, te.name,"
                  " COUNT(e.enrolment_id) AS n FROM terms te"
                  " LEFT JOIN sections s ON s.term_id = te.term_id"
                  " LEFT JOIN enrolments e ON e.section_id = s.section_id"
                  " GROUP BY 1, 2)"
                  " SELECT term_id, name, n,"
                  " ROUND(AVG(n) OVER (ORDER BY term_id"
                  " ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) FROM t"),
        trap_sql=("WITH t AS (SELECT te.term_id, te.name,"
                  " COUNT(e.enrolment_id) AS n FROM terms te"
                  " LEFT JOIN sections s ON s.term_id = te.term_id"
                  " LEFT JOIN enrolments e ON e.section_id = s.section_id"
                  " GROUP BY 1, 2)"
                  " SELECT term_id, name, n,"
                  " ROUND(AVG(n) OVER (ORDER BY term_id), 2) FROM t"),
        note="An OVER() with ORDER BY and no ROWS clause does not mean 'no"
             " frame' -- it means the default frame, everything from the start"
             " of the partition to the current row. That is a RUNNING average"
             " over all history, not a rolling one. ROWS BETWEEN 2 PRECEDING"
             " AND CURRENT ROW is what pins the window to three rows.",
        claims=[("six terms, and the first average equals the first count",
                 lambda rows, c: len(rows) == 6 and abs(
                     min(rows, key=lambda r: r[0])[3]
                     - min(rows, key=lambda r: r[0])[2]) < 0.01)],
    ),
    # ============================================= 6 Grain and correlation
    dict(
        id=23, ledger="Q394", concept="E2", tier="6 - Grain and correlation",
        title="Courses busier than their department's average",
        prompt=(
            "Courses whose enrolment count is above the average enrolment count"
            " of the courses in THEIR OWN department.\n\n"
            "Only courses with at least one enrolment take part, on both sides"
            " of the comparison.\n\n"
            "Return: code, department_id, enrolments"
        ),
        solution=("WITH c AS (SELECT co.course_id, co.code, co.department_id,"
                  " COUNT(*) AS n FROM enrolments e"
                  " JOIN sections s ON s.section_id = e.section_id"
                  " JOIN courses co ON co.course_id = s.course_id"
                  " GROUP BY 1, 2, 3)"
                  " SELECT code, department_id, n FROM c"
                  " WHERE n > (SELECT AVG(c2.n) FROM c c2"
                  " WHERE c2.department_id = c.department_id)"),
        trap_sql=("WITH c AS (SELECT co.course_id, co.code, co.department_id,"
                  " COUNT(*) AS n FROM enrolments e"
                  " JOIN sections s ON s.section_id = e.section_id"
                  " JOIN courses co ON co.course_id = s.course_id"
                  " GROUP BY 1, 2, 3)"
                  " SELECT code, department_id, n FROM c"
                  " WHERE n > (SELECT AVG(n) FROM c)"),
        note="The correlation is the one line WHERE c2.department_id ="
             " c.department_id. Without it every course is compared with the"
             " same college-wide number. Note the CTE is referenced twice, once"
             " as the outer source and once inside the subquery under a"
             " different alias -- that is what lets a query compare a row to"
             " its own group without computing the group twice by hand.",
        claims=[("every returned course beats its own department average",
                 lambda rows, c: len(rows) > 0
                 and len({r[1] for r in rows}) > 1)],
    ),
    dict(
        id=24, ledger="Q395", concept="C2", tier="6 - Grain and correlation",
        title="Three measures per term",
        prompt=(
            "One row per term: how many sections it has, how many enrolments"
            " were made on them, and how many assessments those sections"
            " set.\n\n"
            "Sections is the parent; the other two are independent children of"
            " it. All six terms appear.\n\n"
            "Return: term_id, sections, enrolments, assessments"
        ),
        solution=("SELECT t.term_id,"
                  " (SELECT COUNT(*) FROM sections s"
                  " WHERE s.term_id = t.term_id),"
                  " (SELECT COUNT(*) FROM enrolments e JOIN sections s"
                  " ON s.section_id = e.section_id WHERE s.term_id = t.term_id),"
                  " (SELECT COUNT(*) FROM assessments a JOIN sections s"
                  " ON s.section_id = a.section_id WHERE s.term_id = t.term_id)"
                  " FROM terms t"),
        trap_sql=("SELECT t.term_id, COUNT(DISTINCT s.section_id),"
                  " COUNT(e.enrolment_id), COUNT(a.assessment_id)"
                  " FROM terms t JOIN sections s ON s.term_id = t.term_id"
                  " LEFT JOIN enrolments e ON e.section_id = s.section_id"
                  " LEFT JOIN assessments a ON a.section_id = s.section_id"
                  " GROUP BY 1"),
        note="Three measures at three different grains. Joining both children"
             " multiplies them -- a section with 90 students and 3 assessments"
             " yields 270 rows -- so the enrolment count comes out 3x too big"
             " and the assessment count 90x. COUNT(DISTINCT) rescues the"
             " section count and nothing else, which is the dangerous part: one"
             " column looks right while the others are wrong.",
        claims=[("six terms, all three totals matching their tables",
                 lambda rows, c: len(rows) == 6
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM sections").fetchone()[0]
                 and sum(r[2] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM enrolments").fetchone()[0]
                 and sum(r[3] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM assessments").fetchone()[0])],
    ),
    # ================================================== 7 Query efficiency
    # Graded on the PLAN as well as the rows. Unlike the last set, the fast
    # form is NOT the obvious form in any of these.
    dict(
        id=25, ledger="Q396", concept="X3", tier="7 - Query efficiency",
        title="Make the query longer to make it faster",
        prompt=(
            "How many students are on the 'grant' funding band.\n\n"
            "There is an index on students(campus_id, funding_band). The"
            " obvious query cannot use it. Your plan must say SEARCH, not"
            " SCAN -- and the fix is to ADD something to the WHERE clause, not"
            " to change what is there.\n\n"
            "Return: one row, one column: the count"
        ),
        solution=("SELECT COUNT(*) FROM students"
                  " WHERE campus_id IN (1, 2, 3, 4) AND funding_band = 'grant'"),
        trap_sql=("SELECT COUNT(*) FROM students WHERE funding_band = 'grant'"),
        note="A composite index is usable only from the LEFT. Filtering on"
             " funding_band alone skips campus_id, so there is no range to"
             " seek and SQLite scans. Supplying campus_id -- even with a list"
             " of every value it can take, which removes no rows at all --"
             " gives the index its leading column and turns the scan into four"
             " small seeks. A predicate that filters nothing can still change"
             " the plan, which is the opposite of the usual intuition that"
             " less work means faster.",
        plan_forbids=("SCAN",),
        claims=[("one row, matching the plain count",
                 lambda rows, c: len(rows) == 1 and rows[0][0] == c.execute(
                     "SELECT COUNT(*) FROM students"
                     " WHERE funding_band = 'grant'").fetchone()[0])],
    ),
    dict(
        id=26, ledger="Q397", concept="X5", tier="7 - Query efficiency",
        title="Keep the index covering",
        prompt=(
            "Every withdrawn enrolment's status and grade.\n\n"
            "There is an index on enrolments(status, grade). Return ONLY what"
            " that index already holds and SQLite never has to open the table"
            " at all. Your plan must say COVERING INDEX.\n\n"
            "Return: status, grade"
        ),
        solution=("SELECT status, grade FROM enrolments"
                  " WHERE status = 'withdrawn'"),
        trap_sql=("SELECT status, grade FROM enrolments"
                  " WHERE status = 'withdrawn' AND enrolled_on IS NOT NULL"),
        note="A COVERING index is one that holds every column the query"
             " mentions, so the index alone answers it and the table is never"
             " touched. Add one column that is not in the index and SQLite must"
             " go back to the table for each matching row -- the plan drops the"
             " word COVERING and the query slows. Note the trap adds nothing to"
             " the OUTPUT: enrolled_on IS NOT NULL is true for every row, so"
             " the answer is identical. Merely MENTIONING a column outside the"
             " index is enough to lose the covering read, whether you select"
             " it or only filter on it.",
        plan_requires=("COVERING INDEX",),
        claims=[("every row is withdrawn",
                 lambda rows, c: len(rows) > 0
                 and all(r[0] == 'withdrawn' for r in rows))],
    ),
    dict(
        id=27, ledger="Q398", concept="X2", tier="7 - Query efficiency",
        title="Sort in the order the index is already in",
        prompt=(
            "The first 20 payments ordered by status and then by billing date,"
            " returning just the id.\n\n"
            "There is an index on payments(status, billed_on). Order by those"
            " two columns in the order the index holds them and no sort is"
            " needed at all. Your plan must NOT contain 'TEMP B-TREE'.\n\n"
            "Return: payment_id"
        ),
        solution=("SELECT payment_id FROM payments"
                  " ORDER BY status, billed_on LIMIT 20"),
        trap_sql=("SELECT payment_id FROM payments"
                  " ORDER BY status, billed_on || '' LIMIT 20"),
        note="An index is sorted, so an ORDER BY that matches its column order"
             " can be answered by walking it -- and with a LIMIT that means"
             " reading 20 entries instead of sorting 7,944 rows. The order"
             " matters as much as the columns: ORDER BY billed_on, status"
             " cannot use the same index, because the index is grouped by"
             " status first. Same columns, wrong sequence, temp b-tree.",
        plan_forbids=("TEMP B-TREE",),
        claims=[("twenty rows",
                 lambda rows, c: len(rows) == 20)],
    ),
    dict(
        id=28, ledger="Q399", concept="X6", tier="7 - Query efficiency",
        title="Group in the order the index is already in",
        prompt=(
            "How many payments were billed on each distinct date.\n\n"
            "GROUP BY normally sorts to bring each group together -- but"
            " payments(billed_on) is indexed, and an index is already grouped."
            " Your plan must NOT contain 'TEMP B-TREE'.\n\n"
            "Return: billed_on, payments"
        ),
        solution=("SELECT billed_on, COUNT(*) FROM payments"
                  " GROUP BY billed_on"),
        trap_sql=("SELECT billed_on, COUNT(*) FROM payments"
                  " GROUP BY billed_on || ''"),
        note="GROUP BY has the same relationship with indexes that ORDER BY"
             " does: both need rows brought together in order, and an index"
             " already holds them that way. The trap groups by an expression"
             " that produces identical values, and that is enough -- SQLite"
             " matches the indexed COLUMN, not the values the expression"
             " happens to yield, so it falls back to sorting all 7,944 rows"
             " into a temporary b-tree first.",
        plan_forbids=("TEMP B-TREE",),
        claims=[("one row per distinct billing date",
                 lambda rows, c: len(rows) == c.execute(
                     "SELECT COUNT(DISTINCT billed_on) FROM payments"
                 ).fetchone()[0]),
                ("the counts total every payment",
                 lambda rows, c: sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM payments").fetchone()[0])],
    ),
    dict(
        id=29, ledger="Q400", concept="X7", tier="7 - Query efficiency",
        title="The anti-join that should not be a join",
        prompt=(
            "How many students have never enrolled on anything.\n\n"
            "The LEFT JOIN ... IS NULL form works and is three times slower,"
            " because it joins 83,000 rows to throw nearly all of them away."
            " Write the form that asks the question per student instead: your"
            " plan must contain 'CORRELATED SCALAR SUBQUERY'.\n\n"
            "Return: one row, one column: the count"
        ),
        solution=("SELECT COUNT(*) FROM students s WHERE NOT EXISTS"
                  " (SELECT 1 FROM enrolments e"
                  " WHERE e.student_id = s.student_id)"),
        trap_sql=("SELECT COUNT(*) FROM students s"
                  " LEFT JOIN enrolments e ON e.student_id = s.student_id"
                  " WHERE e.enrolment_id IS NULL"),
        note="This one runs against the usual advice, which is why it is here."
             " A LEFT JOIN anti-join has to build the whole join and then"
             " discard every row that matched -- 83,000 rows to find 572"
             " students. NOT EXISTS asks one indexed question per student and"
             " stops at the first hit, so it touches 4,000 rows and no more."
             " 'Rewrite the correlated subquery as a join' is a good default"
             " and this is where it is wrong.",
        plan_requires=("CORRELATED SCALAR SUBQUERY",),
        claims=[("one row, matching the anti-join count",
                 lambda rows, c: len(rows) == 1 and rows[0][0] == c.execute(
                     "SELECT COUNT(*) FROM students s LEFT JOIN enrolments e"
                     " ON e.student_id = s.student_id"
                     " WHERE e.enrolment_id IS NULL").fetchone()[0])],
    ),
    dict(
        id=30, ledger="Q401", concept="X2", tier="7 - Query efficiency",
        title="Order by the table you are driving",
        prompt=(
            "The 20 earliest enrolments that belong to a student, returning the"
            " enrolment id.\n\n"
            "Every enrolment has a student, so the join changes nothing about"
            " WHICH rows come back -- but ordering by a column of the joined"
            " table forces a sort of all 83,000. Order by the driving table's"
            " indexed column instead. Your plan must NOT contain 'TEMP"
            " B-TREE'.\n\n"
            "Return: enrolment_id"
        ),
        solution=("SELECT e.enrolment_id FROM enrolments e"
                  " JOIN students s ON s.student_id = e.student_id"
                  " ORDER BY e.enrolled_on, e.enrolment_id LIMIT 20"),
        trap_sql=("SELECT e.enrolment_id FROM enrolments e"
                  " JOIN students s ON s.student_id = e.student_id"
                  " ORDER BY e.enrolled_on || '', e.enrolment_id LIMIT 20"),
        note="In a join, only ONE table can be walked in index order -- the one"
             " SQLite drives the join from. Order by a column of that table and"
             " the LIMIT can stop early; order by anything else, including any"
             " expression over it, and every joined row must be produced and"
             " sorted before the first result is known. Which table is being"
             " driven is the first line of the plan, so F6 tells you which"
             " column you are allowed to sort by for free.",
        plan_forbids=("TEMP B-TREE",),
        claims=[("twenty rows in ascending id order within the earliest dates",
                 lambda rows, c: len(rows) == 20)],
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
