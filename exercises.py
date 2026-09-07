"""Practice exercises with reference solutions, used by the GUI to grade answers.

These 30 questions (ledger Q342-Q371) run on the college schema, re-seeded and
**scaled up** (SEED 293 -> 329). The tables are the same; the volumes are not:

  students     60 ->  4,000
  sections     85 ->    774
  enrolments  550 -> 67,000
  payments    129 ->  7,800

That is the point of this set. At 550 rows every query returns instantly no
matter how it is written, so there is nothing to learn about cost. At 67,000 a
query that scans the table takes 10ms and one that seeks an index takes 0.8ms,
and the difference is visible.

Structure is the usual easy-to-hard ramp, with one new stage on the end:

  1 Warm-up                 4  single table, no joins
  2 First joins             5
  3 Recursion               4  still the gentlest in the set
  4 Dates, sets and pivots  5
  5 Window functions        4
  6 Grain and correlation   2
  7 Query efficiency        6  NEW

Because the tables are large, the earlier questions mostly aggregate to a
dimension -- per campus, per term, per faculty -- rather than listing rows.
"Top mark per campus" would now return 707 rows and teach nothing.

HOW THE EFFICIENCY QUESTIONS ARE GRADED
---------------------------------------
They cannot be graded on their result. The slow way and the fast way return
exactly the same rows -- that is what makes the mistake worth making. So those
six carry `plan_requires` / `plan_forbids`, checked against EXPLAIN QUERY PLAN,
and a right answer has to be correct AND arrive by the intended route. A
correct result reached by scanning 67,000 rows is marked wrong, with the plan
shown so you can see why.

Press F6 (or "Explain plan") on any query to see its plan and its timing. The
three words worth knowing:

  SCAN         every row of the table is read
  SEARCH       an index is used to jump straight to the matching rows
  TEMP B-TREE  the rows had to be sorted or grouped on the fly

Each question carries:

  concept   the mistake or technique it drills
  solution  one correct answer
  trap_sql  the tempting WRONG query -- check_questions.py asserts the grader
            rejects it, which is what proves the question actually has teeth.
            For the efficiency questions the trap returns the RIGHT rows and is
            rejected on its plan.
  note      the lesson, shown in the GUI once you get it right
  claims    optional facts about the data that the prompt asserts, re-checked
            against the live database so a prompt cannot quietly go stale

Grading compares your result against the reference as an unordered multiset of
rows, with floats rounded to 2 decimals. Row order never matters.

Spoiler warning: the reference SQL is in this file.
"""

EXERCISES = [
    # ============================================================ 1 Warm-up
    dict(
        id=1, ledger="Q342", concept="A2", tier="1 - Warm-up",
        title="Funding recorded, and not",
        prompt=(
            "One row per campus id: how many students it has, and how many of"
            " them have a funding band recorded.\n\n"
            "Some students have no funding_band, so the two counts differ at"
            " every campus. One table, no joins.\n\n"
            "Return: campus_id, students, with_band"
        ),
        solution=("SELECT campus_id, COUNT(*), COUNT(funding_band)"
                  " FROM students GROUP BY campus_id"),
        trap_sql=("SELECT campus_id, COUNT(*), COUNT(*)"
                  " FROM students GROUP BY campus_id"),
        note="COUNT(*) counts rows. COUNT(column) counts rows where that column"
             " is not NULL. That one difference is the cheapest way to ask 'how"
             " many of these have a value' -- no CASE, no subquery. It is also"
             " why COUNT(a column) after a LEFT JOIN gives a real zero instead"
             " of a phantom 1.",
        claims=[
            ("four campuses, 4000 students, fewer with a band",
             lambda rows, c: len(rows) == 4
             and sum(r[1] for r in rows) == 4000
             and sum(r[2] for r in rows) < 4000),
        ],
    ),
    dict(
        id=2, ledger="Q343", concept="A3", tier="1 - Warm-up",
        title="Which enrolment statuses were common in 2026",
        prompt=(
            "Counting only enrolments made on or after 2026-01-01, one row per"
            " status, keeping the statuses with at least 2,500 of them.\n\n"
            "Two of the three statuses clear the bar. One table, no joins.\n\n"
            "Return: status, enrolments"
        ),
        solution=("SELECT status, COUNT(*) FROM enrolments"
                  " WHERE enrolled_on >= '2026-01-01'"
                  " GROUP BY status HAVING COUNT(*) >= 2500"),
        trap_sql=("SELECT status, COUNT(*) FROM enrolments GROUP BY status"
                  " HAVING enrolled_on >= '2026-01-01' AND COUNT(*) >= 2500"),
        note="WHERE throws away ROWS before grouping; HAVING throws away GROUPS"
             " after. The date test is about a row, so it belongs in WHERE. Put"
             " it in HAVING and SQLite does not complain -- it picks one"
             " arbitrary row's enrolled_on to test, and every count you get"
             " back is over all history rather than 2026.",
        claims=[
            ("two statuses clear 2500 in 2026",
             lambda rows, c: len(rows) == 2 and all(r[1] >= 2500 for r in rows)),
        ],
    ),
    dict(
        id=3, ledger="Q344", concept="general", tier="1 - Warm-up",
        title="Sections by size",
        prompt=(
            "Put every section into one of three bands by capacity and count"
            " them:\n"
            "  'large'  120 or more\n"
            "  'medium' 60 up to but not including 120\n"
            "  'small'  everything else\n\n"
            "All 774 sections land in exactly one band.\n\n"
            "Return: band, sections"
        ),
        solution=("SELECT CASE WHEN capacity >= 120 THEN 'large'"
                  " WHEN capacity >= 60 THEN 'medium'"
                  " ELSE 'small' END, COUNT(*) FROM sections GROUP BY 1"),
        trap_sql=("SELECT CASE WHEN capacity >= 60 THEN 'medium'"
                  " WHEN capacity >= 120 THEN 'large'"
                  " ELSE 'small' END, COUNT(*) FROM sections GROUP BY 1"),
        note="CASE is first-match-wins, so the order of the WHEN branches is"
             " part of the logic, not a matter of taste. Test the narrowest"
             " band first. Put the 60 test ahead of the 120 test and every"
             " large section matches it on the way past -- the 'large' branch"
             " becomes unreachable and never appears at all. The check that"
             " catches it is arithmetic: do the bands sum to 774?",
        claims=[
            ("three bands covering all 774 sections",
             lambda rows, c: len(rows) == 3
             and sum(r[1] for r in rows) == 774),
        ],
    ),
    dict(
        id=4, ledger="Q345", concept="A2", tier="1 - Warm-up",
        title="Average mark, where there is one",
        prompt=(
            "One row per campus: how many enrolments its students made, how"
            " many of those carry a grade, and the average of the grades that"
            " exist.\n\n"
            "Only completed enrolments are graded, so the average must be over"
            " the graded ones alone -- not over everyone enrolled.\n\n"
            "Return: campus_id, enrolments, graded, avg_grade"
        ),
        solution=("SELECT st.campus_id, COUNT(*), COUNT(e.grade),"
                  " ROUND(AVG(e.grade), 2) FROM enrolments e"
                  " JOIN students st ON st.student_id = e.student_id"
                  " GROUP BY 1"),
        trap_sql=("SELECT st.campus_id, COUNT(*), COUNT(e.grade),"
                  " ROUND(SUM(e.grade) * 1.0 / COUNT(*), 2) FROM enrolments e"
                  " JOIN students st ON st.student_id = e.student_id"
                  " GROUP BY 1"),
        note="AVG already ignores NULLs -- it divides by the number of non-NULL"
             " values, not by the number of rows. Rebuilding it as SUM/COUNT(*)"
             " quietly puts the ungraded enrolments into the denominator and"
             " drags every average down by about a third. If you ever do want"
             " SUM over rows rather than values, write SUM(COALESCE(grade, 0))"
             " and say so.",
        claims=[
            ("four campuses, each with fewer graded than enrolled",
             lambda rows, c: len(rows) == 4
             and all(r[2] < r[1] for r in rows)),
            ("every average is a plausible mark",
             lambda rows, c: all(50 < r[3] < 80 for r in rows)),
        ],
    ),
    # ======================================================= 2 First joins
    dict(
        id=5, ledger="Q346", concept="J2", tier="2 - First joins",
        title="Every course, scheduled or not",
        prompt=(
            "One row for every course in the catalogue: its id, code, and how"
            " many sections have ever been scheduled for it.\n\n"
            "Five courses have never been scheduled. They must appear with 0,"
            " so all 34 courses come back.\n\n"
            "Return: course_id, code, sections"
        ),
        solution=("SELECT c.course_id, c.code, COUNT(s.section_id)"
                  " FROM courses c LEFT JOIN sections s"
                  " ON s.course_id = c.course_id GROUP BY 1, 2"),
        trap_sql=("SELECT c.course_id, c.code, COUNT(s.section_id)"
                  " FROM courses c JOIN sections s"
                  " ON s.course_id = c.course_id GROUP BY 1, 2"),
        note="An inner join can only return courses that matched, so the five"
             " unscheduled ones vanish rather than showing 0 -- and 'the ones"
             " with none' is usually what the question is really about. Note"
             " the pairing: LEFT JOIN plus COUNT(a column from the right side)."
             " COUNT(*) there would give those five a 1.",
        claims=[("all 34 courses, five with none",
                 lambda rows, c: len(rows) == 34
                 and sum(1 for r in rows if r[2] == 0) == 5)],
    ),
    dict(
        id=6, ledger="Q347", concept="J2", tier="2 - First joins",
        title="Online teaching per course",
        prompt=(
            "One row for every course: id, code, and how many of its sections"
            " are delivered ONLINE.\n\n"
            "Six courses have none -- five were never scheduled at all, and one"
            " runs only in person. They must appear with 0, so all 34 courses"
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
             " so those rows are filtered straight back out and the outer join"
             " silently becomes an inner one -- 28 rows instead of 34. Pair it"
             " with COUNT(a column from the right side), or the six courses"
             " with none would report 1.",
        claims=[("all 34 courses, six with none",
                 lambda rows, c: len(rows) == 34
                 and sum(1 for r in rows if r[2] == 0) == 6),
                ("an inner join would return only 28",
                 lambda rows, c: c.execute(
                     "SELECT COUNT(*) FROM (SELECT c.course_id FROM courses c"
                     " JOIN sections s ON s.course_id = c.course_id"
                     " WHERE s.delivery = 'online' GROUP BY 1)"
                 ).fetchone()[0] == 28)],
    ),
    dict(
        id=7, ledger="Q348", concept="J1", tier="2 - First joins",
        title="Courses that sit alongside each other",
        prompt=(
            "Pairs of courses in the same department at the same level.\n\n"
            "Each pair once, not twice, and no course paired with itself. Order"
            " each pair so that code_a belongs to the LOWER course_id. There"
            " are 4 pairs.\n\n"
            "Return: department_id, code_a, code_b"
        ),
        solution=("SELECT a.department_id, a.code, b.code FROM courses a"
                  " JOIN courses b ON b.department_id = a.department_id"
                  " AND b.level = a.level AND b.course_id > a.course_id"),
        trap_sql=("SELECT a.department_id, a.code, b.code FROM courses a"
                  " JOIN courses b ON b.department_id = a.department_id"
                  " AND b.level = a.level AND b.course_id <> a.course_id"),
        note="<> only stops a row pairing with itself; it still lets each pair"
             " through in both directions, so you get exactly twice as many"
             " rows as there are pairs. Use > (or <) on the id instead: it"
             " excludes the self-match AND fixes an order, so only one of the"
             " two directions survives.",
        claims=[("four pairs, none a mirror of another",
                 lambda rows, c: len(rows) == 4
                 and len({frozenset((r[1], r[2])) for r in rows}) == 4)],
    ),
    dict(
        id=8, ledger="Q349", concept="J2", tier="2 - First joins",
        title="Courses nobody has scheduled",
        prompt=(
            "Every course that has never had a section scheduled.\n\n"
            "Write it as an outer join that keeps the non-matches, rather than"
            " with NOT IN. There are 5 such courses.\n\n"
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
             " ONLY those. Moving that test into ON changes its meaning"
             " entirely -- it becomes part of what counts as a match, matches"
             " nothing, and hands back all 34 courses.",
        claims=[("5 courses, none of them in sections",
                 lambda rows, c: len(rows) == 5
                 and not {r[0] for r in rows} & {
                     x[0] for x in c.execute(
                         "SELECT DISTINCT course_id FROM sections")})],
    ),
    dict(
        id=9, ledger="Q350", concept="E1", tier="2 - First joins",
        title="Instructors who mentor nobody",
        prompt=(
            "Every instructor who is nobody's mentor. Twelve of the sixteen"
            " qualify.\n\n"
            "Watch out: one instructor -- the one at the top -- has no mentor"
            " themselves, so mentor_id contains a NULL. That is what makes the"
            " obvious answer wrong.\n\n"
            "Return: instructor_id, name"
        ),
        solution=("SELECT i.instructor_id, i.name FROM instructors i"
                  " WHERE NOT EXISTS (SELECT 1 FROM instructors x"
                  " WHERE x.mentor_id = i.instructor_id)"),
        trap_sql=("SELECT i.instructor_id, i.name FROM instructors i"
                  " WHERE i.instructor_id NOT IN"
                  " (SELECT mentor_id FROM instructors)"),
        note="NOT IN over a list containing even one NULL returns no rows at"
             " all. 'Is 7 not in (3, 5, NULL)?' -- SQL cannot say no, because"
             " NULL might have been 7, so the answer is NULL and nothing"
             " passes. NOT EXISTS has no such hole, and neither does a"
             " LEFT JOIN ... IS NULL anti-join.",
        claims=[("twelve instructors, and mentor_id really contains a NULL",
                 lambda rows, c: len(rows) == 12 and c.execute(
                     "SELECT COUNT(*) FROM instructors WHERE mentor_id IS NULL"
                 ).fetchone()[0] == 1)],
    ),
    # ========================================================= 3 Recursion
    dict(
        id=10, ledger="Q351", concept="R1", tier="3 - Recursion",
        title="Everyone under Margaret Ashworth",
        prompt=(
            "Margaret Ashworth is the one instructor with no mentor. List"
            " everyone below her: the people she mentors, the people they"
            " mentor, and so on.\n\n"
            "Fifteen rows -- everyone except Margaret. Only three are her"
            " direct mentees, which is why a single join is not enough.\n\n"
            "Return: instructor_id, name"
        ),
        solution=("WITH RECURSIVE below(id, name) AS ("
                  " SELECT instructor_id, name FROM instructors"
                  " WHERE mentor_id = (SELECT instructor_id FROM instructors"
                  " WHERE name = 'Margaret Ashworth')"
                  " UNION ALL"
                  " SELECT i.instructor_id, i.name FROM instructors i"
                  " JOIN below b ON i.mentor_id = b.id)"
                  " SELECT id, name FROM below"),
        trap_sql=("SELECT i.instructor_id, i.name FROM instructors i"
                  " WHERE i.mentor_id = (SELECT instructor_id FROM instructors"
                  " WHERE name = 'Margaret Ashworth')"),
        note="The plain query gives her three DIRECT mentees and stops. The"
             " recursion carries on down: each pass takes whoever was found"
             " last time and looks for people mentored by them, until a pass"
             " finds nobody. Anchor is one lookup; step is one join back to the"
             " CTE. Note the step's SELECT draws from `instructors`, not from"
             " `below` -- a step that only selects from the CTE cannot advance"
             " and will loop forever.",
        claims=[("15 rows, Margaret not among them",
                 lambda rows, c: len(rows) == 15
                 and not any(r[1] == 'Margaret Ashworth' for r in rows)),
                ("only three are direct mentees",
                 lambda rows, c: c.execute(
                     "SELECT COUNT(*) FROM instructors WHERE mentor_id ="
                     " (SELECT instructor_id FROM instructors"
                     " WHERE name = 'Margaret Ashworth')").fetchone()[0] == 3)],
    ),
    dict(
        id=11, ledger="Q352", concept="R1", tier="3 - Recursion",
        title="What Audit and Assurance needs",
        prompt=(
            "Course ACC301 'Audit and Assurance' has a prerequisite, and that"
            " has one of its own. List every course ACC301 depends on, at any"
            " depth.\n\n"
            "This chain is a straight line -- exactly one prerequisite at each"
            " hop -- so it is two rows. ACC301 itself is not in the answer.\n\n"
            "Return: code, title"
        ),
        solution=("WITH RECURSIVE need(id) AS ("
                  " SELECT requires_course_id FROM prerequisites"
                  " WHERE course_id = (SELECT course_id FROM courses"
                  " WHERE code = 'ACC301')"
                  " UNION"
                  " SELECT p.requires_course_id FROM prerequisites p"
                  " JOIN need n ON p.course_id = n.id)"
                  " SELECT c.code, c.title FROM courses c"
                  " JOIN need ON need.id = c.course_id"),
        trap_sql=("SELECT c.code, c.title FROM prerequisites p"
                  " JOIN courses c ON c.course_id = p.requires_course_id"
                  " WHERE p.course_id = (SELECT course_id FROM courses"
                  " WHERE code = 'ACC301')"),
        note="A single join to prerequisites gives the DIRECT requirement and"
             " stops -- one row, where the answer is two. Keep the CTE carrying"
             " ids only and join `courses` once at the end: carrying code and"
             " title through the walk means joining `courses` inside the step"
             " too, for information the traversal never uses.",
        claims=[("two courses, ACC301 not among them",
                 lambda rows, c: len(rows) == 2
                 and not any(r[0] == 'ACC301' for r in rows))],
    ),
    dict(
        id=12, ledger="Q353", concept="R1", tier="3 - Recursion",
        title="What is blocked by Programming Foundations",
        prompt=(
            "The other way round. Every course that requires CMP101"
            " 'Programming Foundations', directly or indirectly.\n\n"
            "Five courses, and the chain branches: three require it directly,"
            " and the rest come through those.\n\n"
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
             " collected requires_course_id; this one starts from"
             " requires_course_id and collects course_id. Swap the two columns"
             " in BOTH the anchor and the step. Swap only one and you walk a"
             " hop out then back, which is why the trap returns nothing.",
        claims=[("five courses",
                 lambda rows, c: len(rows) == 5)],
    ),
    dict(
        id=13, ledger="Q354", concept="R1", tier="3 - Recursion",
        title="A full study plan for Machine Learning",
        prompt=(
            "Everything a student must pass to finish CMP401 'Machine"
            " Learning' -- every course it depends on at any depth, AND CMP401"
            " itself.\n\n"
            "Seven courses. This one branches, and some courses are reachable"
            " by two different routes but must still appear once.\n\n"
            "Return: code, title"
        ),
        solution=("WITH RECURSIVE plan(id) AS ("
                  " SELECT course_id FROM courses WHERE code = 'CMP401'"
                  " UNION"
                  " SELECT p.requires_course_id FROM prerequisites p"
                  " JOIN plan ON p.course_id = plan.id)"
                  " SELECT c.code, c.title FROM courses c"
                  " JOIN plan ON plan.id = c.course_id"),
        trap_sql=("WITH RECURSIVE plan(id) AS ("
                  " SELECT course_id FROM courses WHERE code = 'CMP401'"
                  " UNION ALL"
                  " SELECT p.requires_course_id FROM prerequisites p"
                  " JOIN plan ON p.course_id = plan.id)"
                  " SELECT c.code, c.title FROM courses c"
                  " JOIN plan ON plan.id = c.course_id"),
        note="Two things are new. The anchor is the course ITSELF rather than"
             " its prerequisites, which is how the starting row ends up in the"
             " answer. And this is where UNION and UNION ALL stop agreeing:"
             " CMP201 is reachable both directly and through CMP301, so"
             " UNION ALL walks it twice and returns 9 rows. UNION discards a"
             " row it has already produced.",
        claims=[("seven courses, CMP401 among them",
                 lambda rows, c: len(rows) == 7
                 and any(r[0] == 'CMP401' for r in rows)),
                ("UNION ALL really would produce more rows",
                 lambda rows, c: c.execute(
                     "WITH RECURSIVE p2(id) AS (SELECT course_id FROM courses"
                     " WHERE code = 'CMP401' UNION ALL SELECT"
                     " p.requires_course_id FROM prerequisites p JOIN p2"
                     " ON p.course_id = p2.id) SELECT COUNT(*) FROM p2"
                 ).fetchone()[0] > 7)],
    ),
    # ============================================ 4 Dates, sets and pivots
    dict(
        id=14, ledger="Q355", concept="D1", tier="4 - Dates, sets and pivots",
        title="How long each term runs",
        prompt=(
            "One row per term: its name, and how many whole days it lasts from"
            " starts_on to ends_on.\n\n"
            "All six terms appear, and every length is between 70 and 90"
            " days.\n\n"
            "Return: term_id, name, days"
        ),
        solution=("SELECT term_id, name,"
                  " CAST(julianday(ends_on) - julianday(starts_on) AS INTEGER)"
                  " FROM terms"),
        trap_sql="SELECT term_id, name, ends_on - starts_on FROM terms",
        note="Dates in SQLite are TEXT. Subtracting one from another does not"
             " subtract dates -- SQLite coerces each string to a number, which"
             " reads '2026-04-02' as 2026 and stops at the dash, so the answer"
             " is the difference in YEARS, usually 0. julianday() turns a date"
             " into a day number, and the difference between two of those is"
             " days.",
        claims=[("six terms, each 70 to 90 days",
                 lambda rows, c: len(rows) == 6
                 and all(70 <= r[2] <= 90 for r in rows))],
    ),
    dict(
        id=15, ledger="Q356", concept="D1", tier="4 - Dates, sets and pivots",
        title="Enrolments by month",
        prompt=(
            "One row per calendar month in which any enrolment was made: the"
            " month as 'YYYY-MM', and how many were made in it.\n\n"
            "The data spans two academic years, so the same month name recurs"
            " and the two must not be added together. There are 14 such"
            " months.\n\n"
            "Return: month, enrolments"
        ),
        solution=("SELECT strftime('%Y-%m', enrolled_on), COUNT(*)"
                  " FROM enrolments GROUP BY 1"),
        trap_sql=("SELECT strftime('%m', enrolled_on), COUNT(*)"
                  " FROM enrolments GROUP BY 1"),
        note="%m alone is the month number with no year attached, so the two"
             " Januaries collapse into one row and you get 7 rows out of a data"
             " set covering 14 months. Grouping by a date always needs every"
             " component down to the level you want. The quickest sanity check"
             " is the row count.",
        claims=[("14 months, twice what %m would give",
                 lambda rows, c: len(rows) == 14),
                ("the counts total every enrolment",
                 lambda rows, c: sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM enrolments").fetchone()[0])],
    ),
    dict(
        id=16, ledger="Q357", concept="S1", tier="4 - Dates, sets and pivots",
        title="Billed in a month nobody enrolled",
        prompt=(
            "Months in which at least one payment was billed but NO enrolment"
            " was made. Months are 'YYYY-MM'.\n\n"
            "Billing runs all year while enrolment clusters around the terms."
            " Nine months qualify.\n\n"
            "Return: month"
        ),
        solution=("SELECT DISTINCT strftime('%Y-%m', billed_on) FROM payments"
                  " EXCEPT"
                  " SELECT DISTINCT strftime('%Y-%m', enrolled_on)"
                  " FROM enrolments"),
        trap_sql=("SELECT DISTINCT strftime('%Y-%m', enrolled_on)"
                  " FROM enrolments EXCEPT"
                  " SELECT DISTINCT strftime('%Y-%m', billed_on) FROM payments"),
        note="EXCEPT is directional: A EXCEPT B is what is in A and not in B,"
             " and swapping the two asks the opposite question. The swap here"
             " returns a different, equally plausible-looking set of months --"
             " nothing about the result tells you it answered backwards."
             " EXCEPT also dedupes, so neither DISTINCT is strictly needed.",
        claims=[("nine months, none with any enrolment",
                 lambda rows, c: len(rows) == 9
                 and not {r[0] for r in rows} & {
                     x[0] for x in c.execute(
                         "SELECT DISTINCT strftime('%Y-%m', enrolled_on)"
                         " FROM enrolments")})],
    ),
    dict(
        id=17, ledger="Q358", concept="S1", tier="4 - Dates, sets and pivots",
        title="Required reading on a first-year course",
        prompt=(
            "Textbooks that are BOTH marked required (required = 1) on some"
            " course AND appear on the reading list of a level-1 course.\n\n"
            "The two need not be the same course. Eleven books qualify.\n\n"
            "Return: book_id, title"
        ),
        solution=("SELECT b.book_id, b.title FROM textbooks b"
                  " WHERE b.book_id IN ("
                  " SELECT book_id FROM course_books WHERE required = 1"
                  " INTERSECT"
                  " SELECT cb.book_id FROM course_books cb"
                  " JOIN courses c ON c.course_id = cb.course_id"
                  " WHERE c.level = 1)"),
        trap_sql=("SELECT b.book_id, b.title FROM textbooks b"
                  " WHERE b.book_id IN ("
                  " SELECT book_id FROM course_books WHERE required = 1"
                  " UNION"
                  " SELECT cb.book_id FROM course_books cb"
                  " JOIN courses c ON c.course_id = cb.course_id"
                  " WHERE c.level = 1)"),
        note="INTERSECT keeps rows present in BOTH sides; UNION keeps rows"
             " present in EITHER. 'And' in English means INTERSECT here even"
             " though the sentence contains an 'and' -- because the two"
             " conditions apply to the same book, rather than being two lists"
             " to add together. Both dedupe, so neither needs a DISTINCT.",
        claims=[("eleven books, each required somewhere",
                 lambda rows, c: len(rows) == 11 and all(
                     c.execute("SELECT COUNT(*) FROM course_books"
                               " WHERE book_id = ? AND required = 1",
                               (r[0],)).fetchone()[0] > 0 for r in rows))],
    ),
    dict(
        id=18, ledger="Q359", concept="A1", tier="4 - Dates, sets and pivots",
        title="Enrolment status by term",
        prompt=(
            "One row per term, with the number of its enrolments in each of the"
            " three statuses side by side as columns.\n\n"
            "All six terms appear, and the three columns together account for"
            " every enrolment.\n\n"
            "Return: term_id, name, completed, active, withdrawn"
        ),
        solution=("SELECT t.term_id, t.name,"
                  " SUM(CASE WHEN e.status = 'completed' THEN 1 ELSE 0 END),"
                  " SUM(CASE WHEN e.status = 'active' THEN 1 ELSE 0 END),"
                  " SUM(CASE WHEN e.status = 'withdrawn' THEN 1 ELSE 0 END)"
                  " FROM terms t JOIN sections s ON s.term_id = t.term_id"
                  " JOIN enrolments e ON e.section_id = s.section_id"
                  " GROUP BY 1, 2"),
        trap_sql=("SELECT t.term_id, t.name,"
                  " COUNT(CASE WHEN e.status = 'completed' THEN 1 ELSE 0 END),"
                  " COUNT(CASE WHEN e.status = 'active' THEN 1 ELSE 0 END),"
                  " COUNT(CASE WHEN e.status = 'withdrawn' THEN 1 ELSE 0 END)"
                  " FROM terms t JOIN sections s ON s.term_id = t.term_id"
                  " JOIN enrolments e ON e.section_id = s.section_id"
                  " GROUP BY 1, 2"),
        note="Pick ONE of two shapes and stick to it: SUM(CASE WHEN c THEN 1"
             " ELSE 0 END) or COUNT(CASE WHEN c THEN 1 END). The mixture in the"
             " trap -- COUNT over an ELSE 0 -- counts every row, because 0 is a"
             " value and COUNT only skips NULL. All three columns come back"
             " identical to the row count, which is the tell.",
        claims=[("six terms, columns totalling every enrolment",
                 lambda rows, c: len(rows) == 6
                 and sum(r[2] + r[3] + r[4] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM enrolments").fetchone()[0])],
    ),
    # ================================================== 5 Window functions
    dict(
        id=19, ledger="Q360", concept="W3", tier="5 - Window functions",
        title="Term on term",
        prompt=(
            "One row per term, in term order: the term name, how many"
            " enrolments were made on its sections, and the change from the"
            " term before.\n\n"
            "The first term has nothing before it, so its change is NULL --"
            " leave it NULL. All six terms appear.\n\n"
            "Return: term_id, name, enrolments, change"
        ),
        solution=("WITH t AS (SELECT te.term_id, te.name,"
                  " COUNT(e.enrolment_id) AS n FROM terms te"
                  " LEFT JOIN sections s ON s.term_id = te.term_id"
                  " LEFT JOIN enrolments e ON e.section_id = s.section_id"
                  " GROUP BY 1, 2)"
                  " SELECT term_id, name, n,"
                  " n - LAG(n) OVER (ORDER BY term_id) FROM t"),
        trap_sql=("WITH t AS (SELECT te.term_id, te.name,"
                  " COUNT(e.enrolment_id) AS n FROM terms te"
                  " LEFT JOIN sections s ON s.term_id = te.term_id"
                  " LEFT JOIN enrolments e ON e.section_id = s.section_id"
                  " GROUP BY 1, 2)"
                  " SELECT term_id, name, n,"
                  " n - LAG(n) OVER (PARTITION BY term_id ORDER BY term_id)"
                  " FROM t"),
        note="PARTITION BY term_id puts every term in a window of its own, so"
             " LAG looks for a previous row inside a one-row window and finds"
             " nothing: every change comes back NULL. Partition by what the"
             " rows have in COMMON and order by what separates them. Here there"
             " is one series, so there is no PARTITION at all.",
        claims=[("six terms, exactly one NULL change",
                 lambda rows, c: len(rows) == 6
                 and sum(1 for r in rows if r[3] is None) == 1)],
    ),
    dict(
        id=20, ledger="Q361", concept="W1", tier="5 - Window functions",
        title="Enrolments so far",
        prompt=(
            "One row per term, in term order: the term name, how many"
            " enrolments were made on its sections, and the running total up to"
            " and including that term.\n\n"
            "The running total on the last term equals every enrolment in the"
            " table.\n\n"
            "Return: term_id, name, enrolments, running_total"
        ),
        solution=("WITH t AS (SELECT te.term_id, te.name,"
                  " COUNT(e.enrolment_id) AS n FROM terms te"
                  " LEFT JOIN sections s ON s.term_id = te.term_id"
                  " LEFT JOIN enrolments e ON e.section_id = s.section_id"
                  " GROUP BY 1, 2)"
                  " SELECT term_id, name, n,"
                  " SUM(n) OVER (ORDER BY term_id) FROM t"),
        trap_sql=("WITH t AS (SELECT te.term_id, te.name,"
                  " COUNT(e.enrolment_id) AS n FROM terms te"
                  " LEFT JOIN sections s ON s.term_id = te.term_id"
                  " LEFT JOIN enrolments e ON e.section_id = s.section_id"
                  " GROUP BY 1, 2)"
                  " SELECT term_id, name, n, SUM(n) OVER () FROM t"),
        note="ORDER BY inside OVER() is the whole difference. SUM(x) OVER ()"
             " with no ORDER BY sees every row at once and repeats the same"
             " grand total on every line; SUM(x) OVER (ORDER BY term_id) sees"
             " only rows up to the current one. A running total over positive"
             " numbers can only ever go up -- if yours is flat, there is no"
             " ORDER BY in the window.",
        claims=[("six terms, last running total is every enrolment",
                 lambda rows, c: len(rows) == 6
                 and max(r[3] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM enrolments").fetchone()[0])],
    ),
    dict(
        id=21, ledger="Q362", concept="W3", tier="5 - Window functions",
        title="Share of the enrolments by faculty",
        prompt=(
            "One row per faculty: the faculty, how many enrolments its"
            " departments' courses attracted, and that count as a percentage of"
            " all enrolments.\n\n"
            "Four faculties, and the four percentages add up to 100.\n\n"
            "Return: faculty, enrolments, pct_of_total"
        ),
        solution=("WITH f AS (SELECT d.faculty, COUNT(*) AS n FROM enrolments e"
                  " JOIN sections s ON s.section_id = e.section_id"
                  " JOIN courses co ON co.course_id = s.course_id"
                  " JOIN departments d ON d.department_id = co.department_id"
                  " GROUP BY 1)"
                  " SELECT faculty, n,"
                  " ROUND(100.0 * n / SUM(n) OVER (), 2) FROM f"),
        trap_sql=("WITH f AS (SELECT d.faculty, COUNT(*) AS n FROM enrolments e"
                  " JOIN sections s ON s.section_id = e.section_id"
                  " JOIN courses co ON co.course_id = s.course_id"
                  " JOIN departments d ON d.department_id = co.department_id"
                  " GROUP BY 1)"
                  " SELECT faculty, n,"
                  " ROUND(100.0 * n / SUM(n) OVER (PARTITION BY faculty), 2)"
                  " FROM f"),
        note="The mirror image of question 20. There you needed the window"
             " narrowed by ORDER BY; here you need it wide open. OVER () with"
             " nothing in it is every row, which is exactly the denominator a"
             " share needs. PARTITION BY faculty shrinks the window to the row"
             " itself, so every share comes out as 100%. Write 100.0, not 100.",
        claims=[("four faculties summing to 100%",
                 lambda rows, c: len(rows) == 4
                 and abs(sum(r[2] for r in rows) - 100) < 0.05)],
    ),
    dict(
        id=22, ledger="Q363", concept="W2", tier="5 - Window functions",
        title="The two biggest courses in each faculty",
        prompt=(
            "For each faculty, the two courses with the most enrolments.\n\n"
            "Rank within the faculty by enrolment count, highest first, and"
            " keep ranks 1 and 2. Four faculties, so 8 rows.\n\n"
            "Return: faculty, code, enrolments"
        ),
        solution=("WITH c AS (SELECT d.faculty, co.code, COUNT(*) AS n"
                  " FROM enrolments e"
                  " JOIN sections s ON s.section_id = e.section_id"
                  " JOIN courses co ON co.course_id = s.course_id"
                  " JOIN departments d ON d.department_id = co.department_id"
                  " GROUP BY 1, 2),"
                  " r AS (SELECT *, RANK() OVER (PARTITION BY faculty"
                  " ORDER BY n DESC) rk FROM c)"
                  " SELECT faculty, code, n FROM r WHERE rk <= 2"),
        trap_sql=("WITH c AS (SELECT d.faculty, co.code, COUNT(*) AS n"
                  " FROM enrolments e"
                  " JOIN sections s ON s.section_id = e.section_id"
                  " JOIN courses co ON co.course_id = s.course_id"
                  " JOIN departments d ON d.department_id = co.department_id"
                  " GROUP BY 1, 2),"
                  " r AS (SELECT *, RANK() OVER (ORDER BY n DESC) rk FROM c)"
                  " SELECT faculty, code, n FROM r WHERE rk <= 2"),
        note="Without PARTITION BY the ranking runs across the whole result, so"
             " rk <= 2 gives the two biggest courses in the COLLEGE rather than"
             " two per faculty -- and both may come from the same faculty."
             " PARTITION BY restarts the numbering for each group. Note the"
             " window's ORDER BY takes an aggregate, COUNT(*), which is legal"
             " because windows run after GROUP BY.",
        claims=[("8 rows across 4 faculties",
                 lambda rows, c: len(rows) == 8
                 and len({r[0] for r in rows}) == 4)],
    ),
    # ============================================= 6 Grain and correlation
    dict(
        id=23, ledger="Q364", concept="E2", tier="6 - Grain and correlation",
        title="Paid above their own department's average",
        prompt=(
            "Every instructor on a higher hourly_rate than the average for"
            " THEIR OWN department -- not higher than the college average.\n\n"
            "Seven qualify. Be careful: the college-wide version also returns"
            " seven, so a row count will not tell you which one you wrote.\n\n"
            "Return: instructor_id, name, department_id, hourly_rate"
        ),
        solution=("SELECT i.instructor_id, i.name, i.department_id,"
                  " i.hourly_rate FROM instructors i WHERE i.hourly_rate >"
                  " (SELECT AVG(x.hourly_rate) FROM instructors x"
                  " WHERE x.department_id = i.department_id)"),
        trap_sql=("SELECT i.instructor_id, i.name, i.department_id,"
                  " i.hourly_rate FROM instructors i WHERE i.hourly_rate >"
                  " (SELECT AVG(hourly_rate) FROM instructors)"),
        note="The correlation is the single line WHERE x.department_id ="
             " i.department_id. Without it the subquery runs once and everyone"
             " is compared with the same number; with it the subquery is"
             " re-evaluated per row against that row's own department. A"
             " modestly paid instructor in a modestly paid department can beat"
             " their own average and lose to the college one -- which is how"
             " two queries return the same COUNT and different people.",
        claims=[("seven instructors, a different seven from the global version",
                 lambda rows, c: len(rows) == 7
                 and {r[0] for r in rows} != {x[0] for x in c.execute(
                     "SELECT instructor_id FROM instructors WHERE hourly_rate >"
                     " (SELECT AVG(hourly_rate) FROM instructors)")})],
    ),
    dict(
        id=24, ledger="Q365", concept="C2", tier="6 - Grain and correlation",
        title="Enrolments and assessments per term",
        prompt=(
            "One row per term: how many enrolments were made on its sections,"
            " and how many assessments those sections set.\n\n"
            "Both hang off sections, but they are independent of each other."
            " All six terms appear.\n\n"
            "Return: term_id, enrolments, assessments"
        ),
        solution=("SELECT t.term_id,"
                  " (SELECT COUNT(*) FROM enrolments e"
                  " JOIN sections s ON s.section_id = e.section_id"
                  " WHERE s.term_id = t.term_id),"
                  " (SELECT COUNT(*) FROM assessments a"
                  " JOIN sections s ON s.section_id = a.section_id"
                  " WHERE s.term_id = t.term_id)"
                  " FROM terms t"),
        trap_sql=("SELECT t.term_id, COUNT(e.enrolment_id),"
                  " COUNT(a.assessment_id) FROM terms t"
                  " JOIN sections s ON s.term_id = t.term_id"
                  " LEFT JOIN enrolments e ON e.section_id = s.section_id"
                  " LEFT JOIN assessments a ON a.section_id = s.section_id"
                  " GROUP BY 1"),
        note="Joining two child tables to the same parent multiplies them: a"
             " section with 80 students and 3 assessments produces 240 rows, so"
             " the enrolment count comes out 3x too big and the assessment"
             " count 80x too big. COUNT(DISTINCT ...) would paper over it here,"
             " but a SUM could not. Two independent measures want two"
             " independent subqueries -- or two CTEs, each reduced to one row"
             " per term before they meet.",
        claims=[("six terms, and both totals match their tables",
                 lambda rows, c: len(rows) == 6
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM enrolments").fetchone()[0]
                 and sum(r[2] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM assessments").fetchone()[0])],
    ),
    # ================================================== 7 Query efficiency
    # These six are graded on their PLAN as well as their rows. Every trap
    # returns exactly the right answer -- and is rejected for how it got there.
    dict(
        id=25, ledger="Q366", concept="X1", tier="7 - Query efficiency",
        title="A year of enrolments, without scanning the table",
        prompt=(
            "How many enrolments were made during the 2025 calendar year.\n\n"
            "`enrolments.enrolled_on` is indexed. Write this so the index is"
            " USED -- your plan must say SEARCH, not SCAN. Press F6 to see"
            " it.\n\n"
            "Return: one row, one column: the count"
        ),
        solution=("SELECT COUNT(*) FROM enrolments"
                  " WHERE enrolled_on >= '2025-01-01'"
                  " AND enrolled_on < '2026-01-01'"),
        trap_sql=("SELECT COUNT(*) FROM enrolments"
                  " WHERE strftime('%Y', enrolled_on) = '2025'"),
        plan_forbids=("SCAN",),
        note="The rule behind all six of these: an index is on the COLUMN, not"
             " on expressions of it. The moment you wrap enrolled_on in"
             " strftime() the index cannot be used, because SQLite would have"
             " to compute the function for every row to find out which ones"
             " match -- which is precisely the scan you were avoiding. Rewrite"
             " the test as a RANGE on the bare column and the index works."
             " Same rows, ten times faster.",
        claims=[("one row, and it matches the 2025 total",
                 lambda rows, c: len(rows) == 1 and rows[0][0] == c.execute(
                     "SELECT COUNT(*) FROM enrolments WHERE"
                     " strftime('%Y', enrolled_on) = '2025'").fetchone()[0])],
    ),
    dict(
        id=26, ledger="Q367", concept="X1", tier="7 - Query efficiency",
        title="Names beginning with Sofia",
        prompt=(
            "Every student whose name starts with 'Sofia'. There are 156.\n\n"
            "`students.name` is indexed. Write this so the plan says SEARCH,"
            " not SCAN.\n\n"
            "Return: student_id, name"
        ),
        solution=("SELECT student_id, name FROM students"
                  " WHERE name LIKE 'Sofia%'"),
        trap_sql=("SELECT student_id, name FROM students"
                  " WHERE substr(name, 1, 5) = 'Sofia'"),
        plan_forbids=("SCAN",),
        note="LIKE with a trailing-only wildcard is index-friendly: 'Sofia%'"
             " becomes the range name >= 'Sofia' AND name < 'Sofib', which is"
             " exactly what a B-tree does well. Two things break it. A LEADING"
             " wildcard ('%Sofia') cannot -- no range starts an unknown number"
             " of characters in. And substr() is a function on the column, so"
             " it falls foul of question 25's rule. Worth knowing: this index"
             " is declared COLLATE NOCASE, because LIKE is case-insensitive by"
             " default and a plain index cannot serve it.",
        claims=[("156 students, all starting with Sofia",
                 lambda rows, c: len(rows) == 156
                 and all(r[1].startswith('Sofia') for r in rows))],
    ),
    dict(
        id=27, ledger="Q368", concept="X2", tier="7 - Query efficiency",
        title="Ten earliest enrolments, without sorting 67,000 rows",
        prompt=(
            "The ten earliest enrolments by date, earliest first. Break ties by"
            " the lower enrolment_id.\n\n"
            "`enrolled_on` is indexed, and an index is already in order --"
            " so this should not need a sort at all. Your plan must NOT contain"
            " 'TEMP B-TREE'.\n\n"
            "Return: enrolment_id, enrolled_on"
        ),
        solution=("SELECT enrolment_id, enrolled_on FROM enrolments"
                  " ORDER BY enrolled_on, enrolment_id LIMIT 10"),
        trap_sql=("SELECT enrolment_id, enrolled_on FROM enrolments"
                  " ORDER BY enrolled_on || '', enrolment_id LIMIT 10"),
        plan_forbids=("TEMP B-TREE",),
        note="'USE TEMP B-TREE FOR ORDER BY' means SQLite had to build a sorted"
             " copy of the rows before it could answer -- all 67,000 of them,"
             " to return 10. An index is already sorted, so ordering by the"
             " indexed column lets it walk the index and stop after ten. The"
             " trap sorts by enrolled_on || '', which is a different expression"
             " from the indexed column even though it has the same value: same"
             " rule as question 25, different clause.",
        claims=[("ten rows, in ascending date order",
                 lambda rows, c: len(rows) == 10
                 and [r[1] for r in rows] == sorted(r[1] for r in rows))],
    ),
    dict(
        id=28, ledger="Q369", concept="X3", tier="7 - Query efficiency",
        title="Withdrawals, using the composite index",
        prompt=(
            "How many enrolments have status 'withdrawn'.\n\n"
            "There is an index on enrolments(status, grade) -- status first."
            " Write this so it is used: the plan must say SEARCH, not SCAN.\n\n"
            "Return: one row, one column: the count"
        ),
        solution="SELECT COUNT(*) FROM enrolments WHERE status = 'withdrawn'",
        trap_sql=("SELECT COUNT(*) FROM enrolments"
                  " WHERE status || '' = 'withdrawn'"),
        plan_forbids=("SCAN",),
        note="A composite index is usable from the LEFT only, like a phone book"
             " sorted by surname then first name: you can look up everyone"
             " called Ashworth, but not everyone called Margaret. So"
             " (status, grade) serves a filter on status, and a filter on grade"
             " ALONE has to scan -- try it with F6 and watch the plan change."
             " The trap fails for the older reason: || '' is an expression, and"
             " the index is on the bare column.",
        claims=[("one row, matching the withdrawn total",
                 lambda rows, c: len(rows) == 1 and rows[0][0] == c.execute(
                     "SELECT COUNT(*) FROM enrolments"
                     " WHERE status = 'withdrawn'").fetchone()[0])],
    ),
    dict(
        id=29, ledger="Q370", concept="X2", tier="7 - Query efficiency",
        title="Enrolments per day, without a temporary sort",
        prompt=(
            "How many enrolments were made on each distinct date, over the"
            " whole data set.\n\n"
            "GROUP BY normally sorts to collect the groups together -- but if"
            " you group by an INDEXED column it can read them in order instead."
            " Your plan must NOT contain 'TEMP B-TREE'.\n\n"
            "Return: enrolled_on, enrolments"
        ),
        solution=("SELECT enrolled_on, COUNT(*) FROM enrolments"
                  " GROUP BY enrolled_on"),
        trap_sql=("SELECT enrolled_on, COUNT(*) FROM enrolments"
                  " GROUP BY enrolled_on || ''"),
        plan_forbids=("TEMP B-TREE",),
        note="GROUP BY has the same relationship with indexes that ORDER BY"
             " does, and for the same reason: both need rows brought together"
             " in order, and an index already holds them that way. When it"
             " cannot use one you get 'USE TEMP B-TREE FOR GROUP BY' and a"
             " sort of the whole table. Seven times slower here for an"
             " identical answer.",
        claims=[("216 distinct days, and the counts total every enrolment",
                 lambda rows, c: len(rows) == 216
                 and sum(r[1] for r in rows) == c.execute(
                     "SELECT COUNT(*) FROM enrolments").fetchone()[0])],
    ),
    dict(
        id=30, ledger="Q371", concept="X4", tier="7 - Query efficiency",
        title="What blocking an index does to a join",
        prompt=(
            "How many enrolments belong to students whose name starts with"
            " 'Sofia'.\n\n"
            "This is question 26's filter, now driving a join against 67,000"
            " enrolments. Written so the index on students.name is usable, it"
            " is over a hundred times faster. Your plan must not contain"
            " 'SCAN'.\n\n"
            "Return: one row, one column: the count"
        ),
        solution=("SELECT COUNT(*) FROM enrolments e"
                  " JOIN students s ON s.student_id = e.student_id"
                  " WHERE s.name LIKE 'Sofia%'"),
        trap_sql=("SELECT COUNT(*) FROM enrolments e"
                  " JOIN students s ON s.student_id = e.student_id"
                  " WHERE upper(s.name) LIKE 'SOFIA%'"),
        plan_forbids=("SCAN",),
        note="This is the one that shows why any of it matters. Blocking the"
             " index does not just slow one lookup down -- it changes the"
             " STRATEGY. With the index usable, SQLite starts from students,"
             " finds 156 of them, and seeks their enrolments: 0.08ms. With"
             " upper() in the way it cannot start there, so it scans all 67,000"
             " enrolments and looks up each student in turn: 12ms, 150 times"
             " slower, for the same number. Press F6 on both and compare the"
             " first line of each plan -- the table named there is the one"
             " being driven.",
        claims=[("one row, matching the direct count",
                 lambda rows, c: len(rows) == 1 and rows[0][0] == c.execute(
                     "SELECT COUNT(*) FROM enrolments e JOIN students s"
                     " ON s.student_id = e.student_id"
                     " WHERE s.name LIKE 'Sofia%'").fetchone()[0])],
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
