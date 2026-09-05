"""Practice exercises with reference solutions, used by the GUI to grade answers.

These 30 questions (ledger Q312-Q341) run on the college schema, re-seeded
(SEED 257 -> 293) so every name, date, mark and amount differs from the last
set. The tables are unchanged.

Same structure as Q282-Q311 -- graded easy to hard, with the tier names as the
stages of the ramp rather than concept labels:

  1 Warm-up                 6  single table, no joins at all
  2 First joins             6  two tables, outer joins, EXISTS
  3 Recursion               4  kept gentle
  4 Dates, sets and pivots  6
  5 Window functions        5
  6 Grain and correlation   3

Same difficulty too: one concept per question, and every prompt states its
grain. What is new is the QUESTIONS -- every one targets its concept through a
different table or relationship than last time, so none of them is the previous
set with the numbers changed.

The four recursion questions stay at the gentle end, but each is now a
different SHAPE rather than the same walk from four starting points:

  13  down a tree from its root       15 rows; a single join gives only 3
  14  down a straight chain           two hops, no branching anywhere
  15  up a branching chain            one course, five things blocked by it
  16  a walk that includes its own    the anchor is the course itself, and
      starting row                    UNION vs UNION ALL changes the answer

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

EXERCISES = [
    # ============================================================ 1 Warm-up
    dict(
        id=1, ledger="Q312", concept="A2", tier="1 - Warm-up",
        title="Staffed and unstaffed",
        prompt=(
            "One row per delivery mode: how many sections use it, and how many"
            " of those have an instructor assigned.\n\n"
            "Some sections are scheduled but not yet staffed, so the two counts"
            " differ in every mode. One table, no joins.\n\n"
            "Return: delivery, sections, staffed"
        ),
        solution=(
            "SELECT delivery, COUNT(*), COUNT(instructor_id)"
            " FROM sections GROUP BY delivery"
        ),
        trap_sql=(
            "SELECT delivery, COUNT(*), COUNT(*) FROM sections GROUP BY delivery"
        ),
        note="COUNT(*) counts rows. COUNT(column) counts rows where that column"
             " is not NULL. That one difference is the cheapest way to ask 'how"
             " many of these have a value' -- no CASE, no subquery. It is also"
             " why COUNT(a column) after a LEFT JOIN gives a real zero instead"
             " of a phantom 1.",
        claims=[
            ("three modes, 85 sections, 73 staffed",
             lambda rows, c: len(rows) == 3
             and sum(r[1] for r in rows) == 85
             and sum(r[2] for r in rows) == 73),
        ],
    ),
    dict(
        id=2, ledger="Q313", concept="A3", tier="1 - Warm-up",
        title="Which assessment kinds cluster in 2026",
        prompt=(
            "Counting only assessments due on or after 2026-01-01, one row per"
            " kind, keeping the kinds with at least 15 of them.\n\n"
            "Two of the four kinds clear the bar. One table, no joins.\n\n"
            "Return: kind, assessments"
        ),
        solution=(
            "SELECT kind, COUNT(*) FROM assessments"
            " WHERE due_on >= '2026-01-01'"
            " GROUP BY kind HAVING COUNT(*) >= 15"
        ),
        trap_sql=(
            "SELECT kind, COUNT(*) FROM assessments GROUP BY kind"
            " HAVING due_on >= '2026-01-01' AND COUNT(*) >= 15"
        ),
        note="WHERE throws away ROWS before grouping; HAVING throws away GROUPS"
             " after. The date test is about a row, so it belongs in WHERE. Put"
             " it in HAVING and SQLite does not complain -- it picks one"
             " arbitrary row's due_on to test, and every count you get back is"
             " over all history rather than 2026.",
        claims=[
            ("two kinds clear 15 in 2026",
             lambda rows, c: len(rows) == 2 and all(r[1] >= 15 for r in rows)),
        ],
    ),
    dict(
        id=3, ledger="Q314", concept="general", tier="1 - Warm-up",
        title="Instructors by pay band",
        prompt=(
            "Put every instructor into one of three bands by hourly_rate and"
            " count them:\n"
            "  'senior'   70 or more\n"
            "  'standard' 50 up to but not including 70\n"
            "  'junior'   everything else\n\n"
            "All 16 instructors land in exactly one band.\n\n"
            "Return: band, instructors"
        ),
        solution=(
            "SELECT CASE WHEN hourly_rate >= 70 THEN 'senior'"
            " WHEN hourly_rate >= 50 THEN 'standard'"
            " ELSE 'junior' END, COUNT(*) FROM instructors GROUP BY 1"
        ),
        trap_sql=(
            "SELECT CASE WHEN hourly_rate >= 50 THEN 'standard'"
            " WHEN hourly_rate >= 70 THEN 'senior'"
            " ELSE 'junior' END, COUNT(*) FROM instructors GROUP BY 1"
        ),
        note="CASE is first-match-wins, so the order of the WHEN branches is"
             " part of the logic, not a matter of taste. Test the narrowest"
             " band first. Put the 50 test ahead of the 70 test and every"
             " senior matches it on the way past -- the 'senior' branch becomes"
             " unreachable and never appears at all. The check that catches it"
             " is arithmetic: do the bands sum to 16?",
        claims=[
            ("three bands covering all 16 instructors",
             lambda rows, c: len(rows) == 3
             and sum(r[1] for r in rows) == 16),
        ],
    ),
    dict(
        id=4, ledger="Q315", concept="C7", tier="1 - Warm-up",
        title="Graded, dropped, or still going",
        prompt=(
            "Classify every enrolment into one of three states and count"
            " them:\n"
            "  'graded'      if grade has a value\n"
            "  'dropped'     if it has no grade and status is withdrawn\n"
            "  'in progress' otherwise\n\n"
            "All 550 enrolments land in exactly one state.\n\n"
            "Return: state, enrolments"
        ),
        solution=(
            "SELECT CASE WHEN grade IS NOT NULL THEN 'graded'"
            " WHEN status = 'withdrawn' THEN 'dropped'"
            " ELSE 'in progress' END, COUNT(*) FROM enrolments GROUP BY 1"
        ),
        trap_sql=(
            "SELECT CASE WHEN grade <> NULL THEN 'graded'"
            " WHEN status = 'withdrawn' THEN 'dropped'"
            " ELSE 'in progress' END, COUNT(*) FROM enrolments GROUP BY 1"
        ),
        note="<> NULL is never true, and neither is = NULL. Both evaluate to"
             " NULL, which CASE treats as not-matched, so that branch can never"
             " fire and every graded enrolment falls through to a later one."
             " The only tests that work on a NULL are IS NULL and IS NOT NULL.",
        claims=[
            ("three states covering all 550 enrolments",
             lambda rows, c: len(rows) == 3
             and sum(r[1] for r in rows) == 550),
            ("graded matches the rows that have a grade",
             lambda rows, c: dict(rows)["graded"] == c.execute(
                 "SELECT COUNT(*) FROM enrolments WHERE grade IS NOT NULL"
             ).fetchone()[0]),
        ],
    ),
    dict(
        id=5, ledger="Q316", concept="C7", tier="1 - Warm-up",
        title="Everyone not on the top pay grade",
        prompt=(
            "Count instructors by pay grade, excluding grade 5, and counting"
            " the ones with NO pay grade recorded as 'none'.\n\n"
            "15 of the 16 instructors are not on grade 5 -- seven of them"
            " because they have no grade at all.\n\n"
            "Return: grade, instructors  (text: '1'..'4' or 'none')"
        ),
        solution=(
            "SELECT COALESCE(CAST(pay_grade AS TEXT), 'none'), COUNT(*)"
            " FROM instructors WHERE pay_grade IS NOT 5 GROUP BY 1"
        ),
        trap_sql=(
            "SELECT COALESCE(CAST(pay_grade AS TEXT), 'none'), COUNT(*)"
            " FROM instructors WHERE pay_grade <> 5 GROUP BY 1"
        ),
        note="pay_grade <> 5 drops the seven ungraded instructors without a"
             " word, because NULL <> 5 is NULL rather than true. ANY comparison"
             " on a nullable column silently excludes the NULLs. SQLite's IS"
             " NOT is null-safe and reads the way you meant it; the portable"
             " spelling is (pay_grade IS NULL OR pay_grade <> 5).",
        claims=[
            ("15 instructors, seven of them ungraded",
             lambda rows, c: sum(r[1] for r in rows) == 15
             and dict(rows)["none"] == 7),
        ],
    ),
    dict(
        id=6, ledger="Q317", concept="A2", tier="1 - Warm-up",
        title="Average copies held, where it is known",
        prompt=(
            "One row per required flag (0 and 1): how many reading-list entries"
            " have it, how many of those record a copies_held figure, and the"
            " average of the figures that exist.\n\n"
            "Plenty of entries have no copy target set. The average must be"
            " over the recorded ones only. One table, no joins.\n\n"
            "Return: required, entries, with_copies, avg_copies"
        ),
        solution=(
            "SELECT required, COUNT(*), COUNT(copies_held),"
            " ROUND(AVG(copies_held), 2) FROM course_books GROUP BY required"
        ),
        trap_sql=(
            "SELECT required, COUNT(*), COUNT(copies_held),"
            " ROUND(SUM(copies_held) * 1.0 / COUNT(*), 2)"
            " FROM course_books GROUP BY required"
        ),
        note="AVG already ignores NULLs -- it divides by the number of non-NULL"
             " values, not by the number of rows. Rebuilding it as SUM/COUNT(*)"
             " quietly puts the entries with no target into the denominator and"
             " drags both averages down. If you ever do want SUM over rows"
             " rather than values, write SUM(COALESCE(copies_held, 0)) and say"
             " so.",
        claims=[
            ("two rows, each with fewer recorded than total",
             lambda rows, c: len(rows) == 2
             and all(r[2] < r[1] for r in rows)),
        ],
    ),
    # ======================================================= 2 First joins
    dict(
        id=7, ledger="Q318", concept="J2", tier="2 - First joins",
        title="Every student, enrolled or not",
        prompt=(
            "One row for every student on the books: id, name, and how many"
            " enrolments they have made.\n\n"
            "Nine students have never enrolled on anything. They must appear"
            " with 0, so all 60 students come back.\n\n"
            "Return: student_id, name, enrolments"
        ),
        solution=(
            "SELECT st.student_id, st.name, COUNT(e.enrolment_id)"
            " FROM students st LEFT JOIN enrolments e"
            " ON e.student_id = st.student_id GROUP BY 1, 2"
        ),
        trap_sql=(
            "SELECT st.student_id, st.name, COUNT(e.enrolment_id)"
            " FROM students st JOIN enrolments e"
            " ON e.student_id = st.student_id GROUP BY 1, 2"
        ),
        note="An inner join can only return students who matched, so the nine"
             " who never enrolled vanish rather than showing 0 -- and 'the ones"
             " with none' is usually what the question is really about. Note"
             " the pairing: LEFT JOIN plus COUNT(a column from the right side)."
             " COUNT(*) there would give those nine a 1.",
        claims=[
            ("all 60 students, nine with none",
             lambda rows, c: len(rows) == 60
             and sum(1 for r in rows if r[2] == 0) == 9),
        ],
    ),
    dict(
        id=8, ledger="Q319", concept="J2", tier="2 - First joins",
        title="Level-4 courses per department",
        prompt=(
            "One row for every department: id, name, and how many LEVEL-4"
            " courses it owns.\n\n"
            "Only three departments run anything at level 4. The other six must"
            " appear with 0, so all 9 departments come back.\n\n"
            "Return: department_id, name, level4_courses"
        ),
        solution=(
            "SELECT d.department_id, d.name, COUNT(c.course_id)"
            " FROM departments d LEFT JOIN courses c"
            " ON c.department_id = d.department_id AND c.level = 4"
            " GROUP BY 1, 2"
        ),
        trap_sql=(
            "SELECT d.department_id, d.name, COUNT(c.course_id)"
            " FROM departments d LEFT JOIN courses c"
            " ON c.department_id = d.department_id"
            " WHERE c.level = 4 GROUP BY 1, 2"
        ),
        note="A condition on the right-hand table has to go in the ON clause of"
             " a LEFT JOIN. In WHERE it runs AFTER the join has padded the"
             " unmatched departments with NULLs, and NULL = 4 is not true, so"
             " those rows are filtered straight back out and the outer join"
             " silently becomes an inner one -- three rows instead of nine.",
        claims=[
            ("all 9 departments, six with none",
             lambda rows, c: len(rows) == 9
             and sum(1 for r in rows if r[2] == 0) == 6),
        ],
    ),
    dict(
        id=9, ledger="Q320", concept="J1", tier="2 - First joins",
        title="Room clashes",
        prompt=(
            "Pairs of sections booked into the same room in the same term.\n\n"
            "Each pair once, not twice, and no section paired with itself."
            " Order each pair so that section_a is the LOWER section_id. There"
            " are 51 pairs.\n\n"
            "Return: term_id, room, section_a, section_b"
        ),
        solution=(
            "SELECT a.term_id, a.room, a.section_id, b.section_id"
            " FROM sections a JOIN sections b ON b.room = a.room"
            " AND b.term_id = a.term_id AND b.section_id > a.section_id"
        ),
        trap_sql=(
            "SELECT a.term_id, a.room, a.section_id, b.section_id"
            " FROM sections a JOIN sections b ON b.room = a.room"
            " AND b.term_id = a.term_id AND b.section_id <> a.section_id"
        ),
        note="<> only stops a row pairing with itself; it still lets each pair"
             " through in both directions, so you get exactly twice as many"
             " rows as there are pairs. Use > (or <) on the id instead: it"
             " excludes the self-match AND fixes an order, so only one of the"
             " two directions survives.",
        claims=[
            ("51 pairs, none a mirror of another",
             lambda rows, c: len(rows) == 51
             and len({frozenset((r[2], r[3])) for r in rows}) == 51),
            ("section_a is always the lower id",
             lambda rows, c: all(r[2] < r[3] for r in rows)),
        ],
    ),
    dict(
        id=10, ledger="Q321", concept="J2", tier="2 - First joins",
        title="Students who never enrolled",
        prompt=(
            "Every student who has never enrolled on anything at all.\n\n"
            "Write it as an outer join that keeps the non-matches, rather than"
            " with NOT IN. There are 9 such students.\n\n"
            "Return: student_id, name"
        ),
        solution=(
            "SELECT st.student_id, st.name FROM students st"
            " LEFT JOIN enrolments e ON e.student_id = st.student_id"
            " WHERE e.enrolment_id IS NULL"
        ),
        trap_sql=(
            "SELECT st.student_id, st.name FROM students st"
            " LEFT JOIN enrolments e ON e.student_id = st.student_id"
            " AND e.enrolment_id IS NULL"
        ),
        note="The anti-join is two halves and both matter: LEFT JOIN to keep"
             " the unmatched students, then WHERE <right column> IS NULL to"
             " keep ONLY those. Moving that test into ON changes its meaning"
             " entirely -- it becomes part of what counts as a match, matches"
             " nothing, and hands back all 60 students. This is question 7 with"
             " the survivors filtered rather than counted.",
        claims=[
            ("9 students, none of them in enrolments",
             lambda rows, c: len(rows) == 9
             and not {r[0] for r in rows} & {
                 x[0] for x in c.execute(
                     "SELECT DISTINCT student_id FROM enrolments")}),
        ],
    ),
    dict(
        id=11, ledger="Q322", concept="E1", tier="2 - First joins",
        title="Courses with an unstaffed section",
        prompt=(
            "Every course that has at least one section with no instructor"
            " assigned.\n\n"
            "One row per course, however many unstaffed sections it has -- and"
            " some have more than one. Nine courses qualify.\n\n"
            "Return: course_id, code"
        ),
        solution=(
            "SELECT c.course_id, c.code FROM courses c"
            " WHERE EXISTS (SELECT 1 FROM sections s"
            " WHERE s.course_id = c.course_id AND s.instructor_id IS NULL)"
        ),
        trap_sql=(
            "SELECT c.course_id, c.code FROM courses c"
            " JOIN sections s ON s.course_id = c.course_id"
            " WHERE s.instructor_id IS NULL"
        ),
        note="Joining down to sections to answer a question ABOUT courses"
             " changes the grain: you get one row per unstaffed section, so a"
             " course with two of them appears twice. EXISTS asks the question"
             " without changing what a row is -- it returns yes or no and stops"
             " at the first hit. SELECT DISTINCT would patch the join, but"
             " EXISTS says what you meant.",
        claims=[
            ("nine courses, none listed twice",
             lambda rows, c: len(rows) == 9
             and len({r[0] for r in rows}) == 9),
            ("some course has two unstaffed sections",
             lambda rows, c: c.execute(
                 "SELECT MAX(n) FROM (SELECT COUNT(*) n FROM sections"
                 " WHERE instructor_id IS NULL GROUP BY course_id)"
             ).fetchone()[0] > 1),
        ],
    ),
    dict(
        id=12, ledger="Q323", concept="E1", tier="2 - First joins",
        title="Instructors who mentor nobody",
        prompt=(
            "Every instructor who is nobody's mentor. Twelve of the sixteen"
            " qualify.\n\n"
            "Watch out: one instructor -- the one at the top -- has no mentor"
            " themselves, so mentor_id contains a NULL. That is what makes the"
            " obvious answer wrong.\n\n"
            "Return: instructor_id, name"
        ),
        solution=(
            "SELECT i.instructor_id, i.name FROM instructors i"
            " WHERE NOT EXISTS (SELECT 1 FROM instructors x"
            " WHERE x.mentor_id = i.instructor_id)"
        ),
        trap_sql=(
            "SELECT i.instructor_id, i.name FROM instructors i"
            " WHERE i.instructor_id NOT IN (SELECT mentor_id FROM instructors)"
        ),
        note="NOT IN over a list containing even one NULL returns no rows at"
             " all. 'Is 7 not in (3, 5, NULL)?' -- SQL cannot say no, because"
             " NULL might have been 7, so the answer is NULL and nothing"
             " passes. NOT EXISTS has no such hole. Either use NOT EXISTS, or"
             " add WHERE mentor_id IS NOT NULL inside the subquery.",
        claims=[
            ("twelve instructors, and mentor_id really does contain a NULL",
             lambda rows, c: len(rows) == 12 and c.execute(
                 "SELECT COUNT(*) FROM instructors WHERE mentor_id IS NULL"
             ).fetchone()[0] == 1),
        ],
    ),
    # ========================================================= 3 Recursion
    dict(
        id=13, ledger="Q324", concept="R1", tier="3 - Recursion",
        title="Everyone under Margaret Ashworth",
        prompt=(
            "Margaret Ashworth is the one instructor with no mentor. List"
            " everyone below her: the people she mentors, the people they"
            " mentor, and so on.\n\n"
            "Fifteen rows -- everyone except Margaret herself. Only three are"
            " her direct mentees, which is why a single join is not enough.\n\n"
            "Return: instructor_id, name"
        ),
        solution=(
            "WITH RECURSIVE below(id, name) AS ("
            " SELECT instructor_id, name FROM instructors"
            " WHERE mentor_id = (SELECT instructor_id FROM instructors"
            " WHERE name = 'Margaret Ashworth')"
            " UNION ALL"
            " SELECT i.instructor_id, i.name FROM instructors i"
            " JOIN below b ON i.mentor_id = b.id)"
            " SELECT id, name FROM below"
        ),
        trap_sql=(
            "SELECT i.instructor_id, i.name FROM instructors i"
            " WHERE i.mentor_id = (SELECT instructor_id FROM instructors"
            " WHERE name = 'Margaret Ashworth')"
        ),
        note="The plain query gives her three DIRECT mentees and stops. The"
             " recursion carries on down: each pass takes whoever was found"
             " last time and looks for people mentored by them, until a pass"
             " finds nobody. Anchor is one lookup; step is one join back to the"
             " CTE. That is the whole mechanism.",
        claims=[
            ("15 rows, and Margaret is not one of them",
             lambda rows, c: len(rows) == 15
             and not any(r[1] == 'Margaret Ashworth' for r in rows)),
            ("only three are direct mentees, so one join would miss twelve",
             lambda rows, c: c.execute(
                 "SELECT COUNT(*) FROM instructors WHERE mentor_id ="
                 " (SELECT instructor_id FROM instructors"
                 " WHERE name = 'Margaret Ashworth')").fetchone()[0] == 3),
        ],
    ),
    dict(
        id=14, ledger="Q325", concept="R1", tier="3 - Recursion",
        title="What Audit and Assurance needs",
        prompt=(
            "Course ACC301 'Audit and Assurance' has a prerequisite, and that"
            " has one of its own. List every course ACC301 depends on, at any"
            " depth.\n\n"
            "This chain is a straight line -- exactly one prerequisite at each"
            " hop -- so it is two rows. ACC301 itself is not in the answer.\n\n"
            "Return: code, title"
        ),
        solution=(
            "WITH RECURSIVE need(id) AS ("
            " SELECT requires_course_id FROM prerequisites"
            " WHERE course_id = (SELECT course_id FROM courses"
            " WHERE code = 'ACC301')"
            " UNION"
            " SELECT p.requires_course_id FROM prerequisites p"
            " JOIN need n ON p.course_id = n.id)"
            " SELECT c.code, c.title FROM courses c"
            " JOIN need ON need.id = c.course_id"
        ),
        trap_sql=(
            "SELECT c.code, c.title FROM prerequisites p"
            " JOIN courses c ON c.course_id = p.requires_course_id"
            " WHERE p.course_id = (SELECT course_id FROM courses"
            " WHERE code = 'ACC301')"
        ),
        note="A single join to prerequisites gives the DIRECT requirement and"
             " stops -- one row, where the answer is two. Same mechanism as"
             " question 13, pointed at a different table and travelling the"
             " other way: down a chain of requirements instead of down a tree"
             " of people.",
        claims=[
            ("two courses, and ACC301 is not one of them",
             lambda rows, c: len(rows) == 2
             and not any(r[0] == 'ACC301' for r in rows)),
            ("ACC301 has exactly one direct prerequisite",
             lambda rows, c: c.execute(
                 "SELECT COUNT(*) FROM prerequisites WHERE course_id ="
                 " (SELECT course_id FROM courses WHERE code = 'ACC301')"
             ).fetchone()[0] == 1),
        ],
    ),
    dict(
        id=15, ledger="Q326", concept="R1", tier="3 - Recursion",
        title="What is blocked by Computer Systems",
        prompt=(
            "The other way round. Every course that requires CMP110 'Computer"
            " Systems', directly or indirectly -- everything a student could"
            " not take until they had passed it.\n\n"
            "Five courses, and the chain branches: two require it directly, and"
            " the rest come through those.\n\n"
            "Return: code, title"
        ),
        solution=(
            "WITH RECURSIVE blocked(id) AS ("
            " SELECT course_id FROM prerequisites"
            " WHERE requires_course_id = (SELECT course_id FROM courses"
            " WHERE code = 'CMP110')"
            " UNION"
            " SELECT p.course_id FROM prerequisites p"
            " JOIN blocked b ON p.requires_course_id = b.id)"
            " SELECT c.code, c.title FROM courses c"
            " JOIN blocked ON blocked.id = c.course_id"
        ),
        trap_sql=(
            "WITH RECURSIVE blocked(id) AS ("
            " SELECT requires_course_id FROM prerequisites"
            " WHERE course_id = (SELECT course_id FROM courses"
            " WHERE code = 'CMP110')"
            " UNION"
            " SELECT p.requires_course_id FROM prerequisites p"
            " JOIN blocked b ON p.course_id = b.id)"
            " SELECT c.code, c.title FROM courses c"
            " JOIN blocked ON blocked.id = c.course_id"
        ),
        note="A prerequisites row reads 'course_id requires"
             " requires_course_id'. Question 14 started from course_id and"
             " collected requires_course_id; this one starts from"
             " requires_course_id and collects course_id. Swap the two columns"
             " in BOTH the anchor and the step and the same query walks the"
             " other way. Swap only one and you walk a hop out then back,"
             " which is why the trap returns nothing at all.",
        claims=[
            ("five courses, all at a higher level than CMP110",
             lambda rows, c: len(rows) == 5),
            ("exactly two require it directly",
             lambda rows, c: c.execute(
                 "SELECT COUNT(*) FROM prerequisites WHERE requires_course_id ="
                 " (SELECT course_id FROM courses WHERE code = 'CMP110')"
             ).fetchone()[0] == 2),
        ],
    ),
    dict(
        id=16, ledger="Q327", concept="R1", tier="3 - Recursion",
        title="A full study plan for Machine Learning",
        prompt=(
            "Everything a student must pass to finish CMP401 'Machine"
            " Learning' -- every course it depends on at any depth, AND CMP401"
            " itself.\n\n"
            "Six courses. Unlike question 14 this one branches, and one course"
            " is reachable by two different routes but must still appear"
            " once.\n\n"
            "Return: code, title"
        ),
        solution=(
            "WITH RECURSIVE plan(id) AS ("
            " SELECT course_id FROM courses WHERE code = 'CMP401'"
            " UNION"
            " SELECT p.requires_course_id FROM prerequisites p"
            " JOIN plan ON p.course_id = plan.id)"
            " SELECT c.code, c.title FROM courses c"
            " JOIN plan ON plan.id = c.course_id"
        ),
        trap_sql=(
            "WITH RECURSIVE plan(id) AS ("
            " SELECT course_id FROM courses WHERE code = 'CMP401'"
            " UNION ALL"
            " SELECT p.requires_course_id FROM prerequisites p"
            " JOIN plan ON p.course_id = plan.id)"
            " SELECT c.code, c.title FROM courses c"
            " JOIN plan ON plan.id = c.course_id"
        ),
        note="Two things are new here. The anchor is the course ITSELF rather"
             " than its prerequisites, which is how the starting row ends up in"
             " the answer -- and it works because the step happens to expand it"
             " on the first pass anyway. And this is where UNION and UNION ALL"
             " stop agreeing: CMP201 is reachable both directly and through"
             " CMP301, so UNION ALL walks it twice and returns 8 rows. UNION"
             " discards a row it has already produced.",
        claims=[
            ("six courses, CMP401 among them",
             lambda rows, c: len(rows) == 6
             and any(r[0] == 'CMP401' for r in rows)),
            ("UNION ALL really would produce more rows here",
             lambda rows, c: c.execute(
                 "WITH RECURSIVE p2(id) AS (SELECT course_id FROM courses"
                 " WHERE code = 'CMP401' UNION ALL SELECT p.requires_course_id"
                 " FROM prerequisites p JOIN p2 ON p.course_id = p2.id)"
                 " SELECT COUNT(*) FROM p2").fetchone()[0] > 6),
        ],
    ),
    # ============================================ 4 Dates, sets and pivots
    dict(
        id=17, ledger="Q328", concept="D1", tier="4 - Dates, sets and pivots",
        title="How long each term runs",
        prompt=(
            "One row per term: its name, and how many whole days it lasts from"
            " starts_on to ends_on.\n\n"
            "All six terms appear, and every length is a whole number between"
            " 70 and 90.\n\n"
            "Return: term_id, name, days"
        ),
        solution=(
            "SELECT term_id, name,"
            " CAST(julianday(ends_on) - julianday(starts_on) AS INTEGER)"
            " FROM terms"
        ),
        trap_sql=(
            "SELECT term_id, name, ends_on - starts_on FROM terms"
        ),
        note="Dates in SQLite are TEXT. Subtracting one from another does not"
             " subtract dates -- SQLite coerces each string to a number, which"
             " reads '2026-04-02' as 2026 and stops at the dash, so the answer"
             " is the difference in YEARS, usually 0. julianday() turns a date"
             " into a day number, and the difference between two of those is"
             " days.",
        claims=[
            ("six terms, each 70 to 90 days",
             lambda rows, c: len(rows) == 6
             and all(70 <= r[2] <= 90 for r in rows)),
        ],
    ),
    dict(
        id=18, ledger="Q329", concept="D1", tier="4 - Dates, sets and pivots",
        title="Enrolments by month",
        prompt=(
            "One row per calendar month in which any enrolment was made: the"
            " month as 'YYYY-MM', and how many were made in it.\n\n"
            "The data spans two academic years, so the same month name recurs"
            " and the two must not be added together. There are 14 such"
            " months.\n\n"
            "Return: month, enrolments"
        ),
        solution=(
            "SELECT strftime('%Y-%m', enrolled_on), COUNT(*)"
            " FROM enrolments GROUP BY 1"
        ),
        trap_sql=(
            "SELECT strftime('%m', enrolled_on), COUNT(*)"
            " FROM enrolments GROUP BY 1"
        ),
        note="%m alone is the month number with no year attached, so the two"
             " Januaries collapse into one row and you get 7 rows out of a data"
             " set covering 14 months. Grouping by a date always needs every"
             " component down to the level you want. The quickest sanity check"
             " is the row count.",
        claims=[
            ("14 months, twice what %m would give",
             lambda rows, c: len(rows) == 14),
            ("the counts total every enrolment",
             lambda rows, c: sum(r[1] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM enrolments").fetchone()[0]),
        ],
    ),
    dict(
        id=19, ledger="Q330", concept="D1", tier="4 - Dates, sets and pivots",
        title="Deadlines after the term ends",
        prompt=(
            "Assessments whose due date falls AFTER the end of the term their"
            " section runs in.\n\n"
            "The due date is on the assessment; the end date is on the term,"
            " reached through the section. There are 13.\n\n"
            "Return: assessment_id, title, due_on, ends_on"
        ),
        solution=(
            "SELECT a.assessment_id, a.title, a.due_on, t.ends_on"
            " FROM assessments a"
            " JOIN sections s ON s.section_id = a.section_id"
            " JOIN terms t ON t.term_id = s.term_id"
            " WHERE julianday(a.due_on) > julianday(t.ends_on)"
        ),
        trap_sql=(
            "SELECT a.assessment_id, a.title, a.due_on, t.ends_on"
            " FROM assessments a"
            " JOIN sections s ON s.section_id = a.section_id"
            " JOIN terms t ON t.term_id = s.term_id"
            " WHERE (a.due_on - t.ends_on) > 0"
        ),
        note="Two ISO dates compare correctly as plain strings, so"
             " a.due_on > t.ends_on would also have been right here --"
             " '2025-12-20' really is greater than '2025-12-13' alphabetically."
             " What is never right is ARITHMETIC on them. The trap subtracts,"
             " which coerces both to years and compares 2025 - 2025 = 0,"
             " finding only the deadlines that crossed into a new year.",
        claims=[
            ("13 rows, every one genuinely past its term end",
             lambda rows, c: len(rows) == 13
             and all(r[2] > r[3] for r in rows)),
        ],
    ),
    dict(
        id=20, ledger="Q331", concept="S1", tier="4 - Dates, sets and pivots",
        title="First-year reading that never reappears",
        prompt=(
            "Textbooks that appear on a LEVEL-1 course's reading list but on no"
            " LEVEL-3 course's list.\n\n"
            "Eight books qualify. A book on both a level-1 and a level-3 course"
            " is excluded, even if the two are in different departments.\n\n"
            "Return: book_id, title"
        ),
        solution=(
            "SELECT b.book_id, b.title FROM textbooks b WHERE b.book_id IN ("
            " SELECT cb.book_id FROM course_books cb"
            " JOIN courses c ON c.course_id = cb.course_id WHERE c.level = 1"
            " EXCEPT"
            " SELECT cb.book_id FROM course_books cb"
            " JOIN courses c ON c.course_id = cb.course_id WHERE c.level = 3)"
        ),
        trap_sql=(
            "SELECT b.book_id, b.title FROM textbooks b WHERE b.book_id IN ("
            " SELECT cb.book_id FROM course_books cb"
            " JOIN courses c ON c.course_id = cb.course_id WHERE c.level = 3"
            " EXCEPT"
            " SELECT cb.book_id FROM course_books cb"
            " JOIN courses c ON c.course_id = cb.course_id WHERE c.level = 1)"
        ),
        note="EXCEPT is directional: A EXCEPT B is what is in A and not in B,"
             " and swapping the two asks the opposite question -- here, books"
             " on a level-3 list but no level-1 one. That returns a plausible"
             " number of plausible-looking rows, which is what makes it"
             " dangerous: nothing about the result says you asked it backwards."
             " EXCEPT also dedupes, so no DISTINCT is needed.",
        claims=[
            ("eight books, none of them on a level-3 list",
             lambda rows, c: len(rows) == 8
             and not {r[0] for r in rows} & {
                 x[0] for x in c.execute(
                     "SELECT cb.book_id FROM course_books cb JOIN courses c"
                     " ON c.course_id = cb.course_id WHERE c.level = 3")}),
        ],
    ),
    dict(
        id=21, ledger="Q332", concept="S1", tier="4 - Dates, sets and pivots",
        title="Students who have both finished and dropped",
        prompt=(
            "Students who have BOTH completed at least one enrolment AND"
            " withdrawn from at least one.\n\n"
            "The two need not be the same course. 37 students qualify.\n\n"
            "Return: student_id, name"
        ),
        solution=(
            "SELECT st.student_id, st.name FROM students st"
            " WHERE st.student_id IN ("
            " SELECT student_id FROM enrolments WHERE status = 'completed'"
            " INTERSECT"
            " SELECT student_id FROM enrolments WHERE status = 'withdrawn')"
        ),
        trap_sql=(
            "SELECT st.student_id, st.name FROM students st"
            " WHERE st.student_id IN ("
            " SELECT student_id FROM enrolments WHERE status = 'completed'"
            " UNION"
            " SELECT student_id FROM enrolments WHERE status = 'withdrawn')"
        ),
        note="INTERSECT keeps rows present in BOTH sides; UNION keeps rows"
             " present in EITHER. 'And' in English means INTERSECT here even"
             " though the sentence contains an 'and' -- because the two"
             " conditions apply to the same student, rather than being two"
             " lists to add together. Both dedupe, so neither needs a DISTINCT.",
        claims=[
            ("37 students, each with both a completion and a withdrawal",
             lambda rows, c: len(rows) == 37 and all(
                 c.execute("SELECT COUNT(DISTINCT status) FROM enrolments"
                           " WHERE student_id = ? AND status IN"
                           " ('completed', 'withdrawn')",
                           (r[0],)).fetchone()[0] == 2 for r in rows)),
        ],
    ),
    dict(
        id=22, ledger="Q333", concept="A1", tier="4 - Dates, sets and pivots",
        title="Assessment kinds by term",
        prompt=(
            "One row per term, with the number of its assessments of each kind"
            " side by side as columns.\n\n"
            "All six terms appear, and the four columns together account for"
            " every assessment.\n\n"
            "Return: term_id, name, essay, exam, project, practical"
        ),
        solution=(
            "SELECT t.term_id, t.name,"
            " SUM(CASE WHEN a.kind = 'essay' THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN a.kind = 'exam' THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN a.kind = 'project' THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN a.kind = 'practical' THEN 1 ELSE 0 END)"
            " FROM terms t JOIN sections s ON s.term_id = t.term_id"
            " JOIN assessments a ON a.section_id = s.section_id"
            " GROUP BY 1, 2"
        ),
        trap_sql=(
            "SELECT t.term_id, t.name,"
            " COUNT(CASE WHEN a.kind = 'essay' THEN 1 ELSE 0 END),"
            " COUNT(CASE WHEN a.kind = 'exam' THEN 1 ELSE 0 END),"
            " COUNT(CASE WHEN a.kind = 'project' THEN 1 ELSE 0 END),"
            " COUNT(CASE WHEN a.kind = 'practical' THEN 1 ELSE 0 END)"
            " FROM terms t JOIN sections s ON s.term_id = t.term_id"
            " JOIN assessments a ON a.section_id = s.section_id"
            " GROUP BY 1, 2"
        ),
        note="Pick ONE of two shapes and stick to it: SUM(CASE WHEN c THEN 1"
             " ELSE 0 END) or COUNT(CASE WHEN c THEN 1 END). The mixture in the"
             " trap -- COUNT over an ELSE 0 -- counts every row, because 0 is a"
             " value and COUNT only skips NULL. All four columns come back"
             " identical to the row count, which is the tell.",
        claims=[
            ("six terms, and the columns total every assessment",
             lambda rows, c: len(rows) == 6
             and sum(r[2] + r[3] + r[4] + r[5] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM assessments").fetchone()[0]),
        ],
    ),
    # ================================================== 5 Window functions
    dict(
        id=23, ledger="Q334", concept="W3", tier="5 - Window functions",
        title="Month on month",
        prompt=(
            "One row per calendar month in which any enrolment was made: the"
            " month as 'YYYY-MM', how many were made, and the change from the"
            " month before.\n\n"
            "The earliest month has nothing before it, so its change is NULL --"
            " leave it NULL rather than turning it into 0. 14 months.\n\n"
            "Return: month, enrolments, change"
        ),
        solution=(
            "WITH m AS (SELECT strftime('%Y-%m', enrolled_on) AS mth,"
            " COUNT(*) AS n FROM enrolments GROUP BY 1)"
            " SELECT mth, n, n - LAG(n) OVER (ORDER BY mth) FROM m"
        ),
        trap_sql=(
            "WITH m AS (SELECT strftime('%Y-%m', enrolled_on) AS mth,"
            " COUNT(*) AS n FROM enrolments GROUP BY 1)"
            " SELECT mth, n, n - LAG(n) OVER (PARTITION BY mth ORDER BY mth)"
            " FROM m"
        ),
        note="PARTITION BY mth puts every month in a window of its own, so LAG"
             " looks for a previous row inside a one-row window and finds"
             " nothing: every change comes back NULL. Partition by what the"
             " rows have in COMMON and order by what separates them. Here there"
             " is one series, so there is no PARTITION at all.",
        claims=[
            ("14 months, exactly one NULL change",
             lambda rows, c: len(rows) == 14
             and sum(1 for r in rows if r[2] is None) == 1),
        ],
    ),
    dict(
        id=24, ledger="Q335", concept="W1", tier="5 - Window functions",
        title="Enrolments so far",
        prompt=(
            "One row per term, in term order: the term name, how many"
            " enrolments were made on its sections, and the running total of"
            " enrolments up to and including that term.\n\n"
            "The running total on the last term equals every enrolment in the"
            " table. All six terms appear.\n\n"
            "Return: term_id, name, enrolments, running_total"
        ),
        solution=(
            "WITH t AS (SELECT te.term_id, te.name, COUNT(e.enrolment_id) AS n"
            " FROM terms te LEFT JOIN sections s ON s.term_id = te.term_id"
            " LEFT JOIN enrolments e ON e.section_id = s.section_id"
            " GROUP BY 1, 2)"
            " SELECT term_id, name, n, SUM(n) OVER (ORDER BY term_id) FROM t"
        ),
        trap_sql=(
            "WITH t AS (SELECT te.term_id, te.name, COUNT(e.enrolment_id) AS n"
            " FROM terms te LEFT JOIN sections s ON s.term_id = te.term_id"
            " LEFT JOIN enrolments e ON e.section_id = s.section_id"
            " GROUP BY 1, 2)"
            " SELECT term_id, name, n, SUM(n) OVER () FROM t"
        ),
        note="ORDER BY inside OVER() is the whole difference. SUM(x) OVER ()"
             " with no ORDER BY sees every row at once and repeats the same"
             " grand total on every line; SUM(x) OVER (ORDER BY term_id) sees"
             " only rows up to the current one. A running total over positive"
             " numbers can only ever go up -- if yours is flat, there is no"
             " ORDER BY in the window.",
        claims=[
            ("six terms, last running total is every enrolment",
             lambda rows, c: len(rows) == 6
             and max(r[3] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM enrolments").fetchone()[0]),
        ],
    ),
    dict(
        id=25, ledger="Q336", concept="W3", tier="5 - Window functions",
        title="Share of the billing by status",
        prompt=(
            "One row per payment status: the status, the total amount billed"
            " under it, and that total as a percentage of everything"
            " billed.\n\n"
            "Four statuses, and the four percentages add up to 100.\n\n"
            "Return: status, billed, pct_of_total"
        ),
        solution=(
            "WITH s AS (SELECT status, SUM(amount) AS amt FROM payments"
            " GROUP BY 1)"
            " SELECT status, ROUND(amt, 2),"
            " ROUND(100.0 * amt / SUM(amt) OVER (), 2) FROM s"
        ),
        trap_sql=(
            "WITH s AS (SELECT status, SUM(amount) AS amt FROM payments"
            " GROUP BY 1)"
            " SELECT status, ROUND(amt, 2),"
            " ROUND(100.0 * amt / SUM(amt) OVER (PARTITION BY status), 2)"
            " FROM s"
        ),
        note="The mirror image of question 24. There you needed the window"
             " narrowed by ORDER BY; here you need it wide open. OVER () with"
             " nothing in it is every row, which is exactly the denominator a"
             " share needs. PARTITION BY status shrinks the window to the row"
             " itself, so every share comes out as 100%. Write 100.0, not 100 --"
             " integer division would truncate every answer.",
        claims=[
            ("four statuses summing to 100%",
             lambda rows, c: len(rows) == 4
             and abs(sum(r[2] for r in rows) - 100) < 0.05),
        ],
    ),
    dict(
        id=26, ledger="Q337", concept="W2", tier="5 - Window functions",
        title="Each student's first enrolment",
        prompt=(
            "For every student who has ever enrolled, their earliest enrolment"
            " by date. One row per student -- students who never enrolled do"
            " not appear, so 51 rows.\n\n"
            "Break ties on date by the lower enrolment_id, so each student's"
            " first is unambiguous.\n\n"
            "Return: student_id, enrolment_id, enrolled_on"
        ),
        solution=(
            "WITH r AS (SELECT student_id, enrolment_id, enrolled_on,"
            " ROW_NUMBER() OVER (PARTITION BY student_id"
            " ORDER BY enrolled_on, enrolment_id) AS rn FROM enrolments)"
            " SELECT student_id, enrolment_id, enrolled_on FROM r WHERE rn = 1"
        ),
        trap_sql=(
            "WITH r AS (SELECT student_id, enrolment_id, enrolled_on,"
            " ROW_NUMBER() OVER (ORDER BY enrolled_on, enrolment_id) AS rn"
            " FROM enrolments)"
            " SELECT student_id, enrolment_id, enrolled_on FROM r WHERE rn = 1"
        ),
        note="Without PARTITION BY the numbering runs straight through the"
             " whole table, so rn = 1 is the single earliest enrolment anywhere"
             " and you get one row instead of one per student. PARTITION BY"
             " restarts the count for each student -- it is the GROUP BY of the"
             " window world, except the detail rows survive.",
        claims=[
            ("51 students, one row each",
             lambda rows, c: len(rows) == 51
             and len({r[0] for r in rows}) == len(rows)),
        ],
    ),
    dict(
        id=27, ledger="Q338", concept="W2", tier="5 - Window functions",
        title="Top of each campus, ties and all",
        prompt=(
            "The highest mark achieved by students at each campus, and who got"
            " it. Only graded enrolments count.\n\n"
            "Every campus has students tied on its top mark, so the answer is 8"
            " rows across 4 campuses, not 4.\n\n"
            "Return: campus_id, student_id, name, grade"
        ),
        solution=(
            "WITH g AS (SELECT st.campus_id, st.student_id, st.name, e.grade,"
            " RANK() OVER (PARTITION BY st.campus_id ORDER BY e.grade DESC) rk"
            " FROM enrolments e JOIN students st"
            " ON st.student_id = e.student_id WHERE e.grade IS NOT NULL)"
            " SELECT campus_id, student_id, name, grade FROM g WHERE rk = 1"
        ),
        trap_sql=(
            "WITH g AS (SELECT st.campus_id, st.student_id, st.name, e.grade,"
            " ROW_NUMBER() OVER (PARTITION BY st.campus_id"
            " ORDER BY e.grade DESC) rk"
            " FROM enrolments e JOIN students st"
            " ON st.student_id = e.student_id WHERE e.grade IS NOT NULL)"
            " SELECT campus_id, student_id, name, grade FROM g WHERE rk = 1"
        ),
        note="ROW_NUMBER hands out 1, 2, 3 with no repeats, so on a tie it"
             " keeps one row arbitrarily and you silently lose the others. RANK"
             " gives tied rows the same number. ROW_NUMBER when you want"
             " exactly one row -- as in question 26 -- and RANK when you want"
             " everyone who earned the position. And do not reach for GROUP BY"
             " here: it would find the top mark but lose the name.",
        claims=[
            ("8 rows across 4 campuses, so every campus is tied",
             lambda rows, c: len(rows) == 8
             and len({r[0] for r in rows}) == 4),
        ],
    ),
    # ============================================= 6 Grain and correlation
    dict(
        id=28, ledger="Q339", concept="E2", tier="6 - Grain and correlation",
        title="Paid above their own department's average",
        prompt=(
            "Every instructor on a higher hourly_rate than the average for"
            " THEIR OWN department -- not higher than the average across the"
            " whole college.\n\n"
            "Seven qualify. Be careful: the college-wide version also returns"
            " seven, so a row count will not tell you which one you wrote.\n\n"
            "Return: instructor_id, name, department_id, hourly_rate"
        ),
        solution=(
            "SELECT i.instructor_id, i.name, i.department_id, i.hourly_rate"
            " FROM instructors i WHERE i.hourly_rate >"
            " (SELECT AVG(x.hourly_rate) FROM instructors x"
            " WHERE x.department_id = i.department_id)"
        ),
        trap_sql=(
            "SELECT i.instructor_id, i.name, i.department_id, i.hourly_rate"
            " FROM instructors i"
            " WHERE i.hourly_rate > (SELECT AVG(hourly_rate) FROM instructors)"
        ),
        note="The correlation is the single line WHERE x.department_id ="
             " i.department_id. Without it the subquery runs once and everyone"
             " is compared with the same number; with it the subquery is"
             " re-evaluated per row against that row's own department. A"
             " modestly paid instructor in a modestly paid department can beat"
             " their own average and lose to the college one -- which is"
             " exactly how two queries return the same COUNT and different"
             " people.",
        claims=[
            ("seven instructors, and the uncorrelated version returns a"
             " different seven",
             lambda rows, c: len(rows) == 7
             and {r[0] for r in rows} != {x[0] for x in c.execute(
                 "SELECT instructor_id FROM instructors WHERE hourly_rate >"
                 " (SELECT AVG(hourly_rate) FROM instructors)")}),
        ],
    ),
    dict(
        id=29, ledger="Q340", concept="C2", tier="6 - Grain and correlation",
        title="Enrolments and payments per student",
        prompt=(
            "One row per student: how many enrolments they have made, and how"
            " many payments have been billed to them.\n\n"
            "The two are independent -- a student can have many of one and none"
            " of the other. A student with none of something shows 0, not NULL."
            " All 60 students appear.\n\n"
            "Return: student_id, enrolments, payments"
        ),
        solution=(
            "SELECT st.student_id,"
            " (SELECT COUNT(*) FROM enrolments e"
            " WHERE e.student_id = st.student_id),"
            " (SELECT COUNT(*) FROM payments p"
            " WHERE p.student_id = st.student_id)"
            " FROM students st"
        ),
        trap_sql=(
            "SELECT st.student_id, COUNT(e.enrolment_id), COUNT(p.payment_id)"
            " FROM students st"
            " LEFT JOIN enrolments e ON e.student_id = st.student_id"
            " LEFT JOIN payments p ON p.student_id = st.student_id"
            " GROUP BY 1"
        ),
        note="Joining two child tables to the same parent multiplies them: a"
             " student with 18 enrolments and 4 payments produces 72 rows, so"
             " the enrolment count comes out 4x too big and the payment count"
             " 18x too big. COUNT(DISTINCT ...) would paper over it here, but a"
             " SUM could not. Two independent measures want two independent"
             " subqueries -- or two CTEs, each reduced to one row per student"
             " before they meet.",
        claims=[
            ("all 60 students, and both totals match their tables",
             lambda rows, c: len(rows) == 60
             and sum(r[1] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM enrolments").fetchone()[0]
             and sum(r[2] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM payments").fetchone()[0]),
        ],
    ),
    dict(
        id=30, ledger="Q341", concept="C2", tier="6 - Grain and correlation",
        title="Sections whose marking does not add up",
        prompt=(
            "An assessment's weight is its share of the section's final mark,"
            " so a section's weights should total 1. Find the sections where"
            " they do not.\n\n"
            "Round the total to 2 decimals before comparing, or floating-point"
            " noise will report almost every section. 20 of the 74 sections"
            " that have assessments are wrong.\n\n"
            "Return: section_id, total_weight"
        ),
        solution=(
            "SELECT section_id, ROUND(SUM(weight), 2) FROM assessments"
            " GROUP BY section_id HAVING ROUND(SUM(weight), 2) <> 1.0"
        ),
        trap_sql=(
            "SELECT a.section_id, ROUND(SUM(a.weight), 2) FROM assessments a"
            " JOIN enrolments e ON e.section_id = a.section_id"
            " GROUP BY a.section_id HAVING ROUND(SUM(a.weight), 2) <> 1.0"
        ),
        note="The question is about assessments only, so bringing enrolments"
             " into it multiplies every weight by the number of students on the"
             " section -- the sums explode and a different set of sections"
             " fails the test. Join only what the answer needs. Note too that"
             " HAVING is right here: the condition is about the GROUP's total,"
             " not about any individual row, which is the one thing WHERE"
             " cannot express.",
        claims=[
            ("20 sections, none of them totalling 1",
             lambda rows, c: len(rows) == 20
             and all(abs(r[1] - 1.0) > 0.001 for r in rows)),
            ("74 sections have assessments, so most are fine",
             lambda rows, c: c.execute(
                 "SELECT COUNT(DISTINCT section_id) FROM assessments"
             ).fetchone()[0] == 74),
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
