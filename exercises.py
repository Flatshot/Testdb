"""Practice exercises with reference solutions, used by the GUI to grade answers.

These 30 questions (ledger Q282-Q311) run on the college schema from the last
set, re-seeded (SEED 221 -> 257) so every name, date, mark and amount differs
and no remembered answer value carries over. The tables are the same, so the
schema you learned last time still applies.

What is different is the ORDER. The last set was grouped by concept, which put
all four recursion questions first -- so the hardest mechanism came before any
warm-up. This set is graded easy to hard instead, and the tier names are the
stages of that ramp rather than concept labels:

  1 Warm-up                 6  single table, no joins at all
  2 First joins             6  two tables, outer joins, EXISTS
  3 Recursion               4  deliberately the gentlest in the set
  4 Dates, sets and pivots  6
  5 Window functions        5
  6 Grain and correlation   3  the two that need the most care

Work them in order and each one leans on the one before. The concept each
question drills is still recorded in its `concept` field and in QUESTIONS.md.

The four recursion questions are all the SAME SHAPE on purpose: an anchor that
is one obvious row, and a step that is one join back to the CTE. No depth
counters, no generated series, no carrying labels down the tree. What varies is
only the direction of travel and the table:

  13  up a mentor chain          instructors, one hop at a time
  14  down a prerequisite chain  a course whose ancestry is a straight line
  15  up a prerequisite chain    the same table, the other column
  16  down a branching one       where UNION and UNION ALL finally differ

Difficulty is otherwise pitched where the last set was: one concept per
question, and every prompt states its grain.

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

# The date the data is treated as ending, and the cut-off the classification
# questions compare against. Fixed rather than taken from the clock.
CUTOFF = "2026-07-01"

EXERCISES = [
    # ============================================================ 1 Warm-up
    dict(
        id=1, ledger="Q282", concept="A2", tier="1 - Warm-up",
        title="Funding recorded, and not",
        prompt=(
            "One row per campus id: how many students it has, and how many of"
            " them have a funding band recorded.\n\n"
            "Twelve students company-wide have no funding_band, so the two"
            " counts differ. One table, no joins.\n\n"
            "Return: campus_id, students, with_band"
        ),
        solution=(
            "SELECT campus_id, COUNT(*), COUNT(funding_band)"
            " FROM students GROUP BY campus_id"
        ),
        trap_sql=(
            "SELECT campus_id, COUNT(*), COUNT(*)"
            " FROM students GROUP BY campus_id"
        ),
        note="COUNT(*) counts rows. COUNT(column) counts rows where that column"
             " is not NULL. That one difference is the cheapest way to ask 'how"
             " many of these have a value' -- no CASE, no subquery. It is also"
             " why COUNT(a column) after a LEFT JOIN gives a real zero instead"
             " of a phantom 1.",
        claims=[
            ("four campuses, 60 students, 48 with a band",
             lambda rows, c: len(rows) == 4
             and sum(r[1] for r in rows) == 60
             and sum(r[2] for r in rows) == 48),
        ],
    ),
    dict(
        id=2, ledger="Q283", concept="A3", tier="1 - Warm-up",
        title="Which payment statuses were common in 2025",
        prompt=(
            "Counting only payments billed during the 2025 calendar year, one"
            " row per status, keeping the statuses with at least 10 of them.\n\n"
            "Three of the four statuses clear the bar. One table, no joins.\n\n"
            "Return: status, payments"
        ),
        solution=(
            "SELECT status, COUNT(*) FROM payments"
            " WHERE billed_on >= '2025-01-01' AND billed_on < '2026-01-01'"
            " GROUP BY status HAVING COUNT(*) >= 10"
        ),
        trap_sql=(
            "SELECT status, COUNT(*) FROM payments GROUP BY status"
            " HAVING billed_on >= '2025-01-01' AND billed_on < '2026-01-01'"
            " AND COUNT(*) >= 10"
        ),
        note="WHERE throws away ROWS before grouping; HAVING throws away GROUPS"
             " after. The date test is about a row, so it belongs in WHERE. Put"
             " it in HAVING and SQLite does not complain -- it picks one"
             " arbitrary row's billed_on to test, and every count you get back"
             " is over all history rather than 2025.",
        claims=[
            ("three statuses clear 10 in 2025",
             lambda rows, c: len(rows) == 3 and all(r[1] >= 10 for r in rows)),
        ],
    ),
    dict(
        id=3, ledger="Q284", concept="general", tier="1 - Warm-up",
        title="Textbooks by price band",
        prompt=(
            "Put every textbook into one of three bands by list_price and count"
            " them:\n"
            "  'premium'  100 or more\n"
            "  'standard' 50 up to but not including 100\n"
            "  'budget'   everything else\n\n"
            "All 30 textbooks land in exactly one band.\n\n"
            "Return: band, textbooks"
        ),
        solution=(
            "SELECT CASE WHEN list_price >= 100 THEN 'premium'"
            " WHEN list_price >= 50 THEN 'standard'"
            " ELSE 'budget' END, COUNT(*) FROM textbooks GROUP BY 1"
        ),
        trap_sql=(
            "SELECT CASE WHEN list_price >= 50 THEN 'standard'"
            " WHEN list_price >= 100 THEN 'premium'"
            " ELSE 'budget' END, COUNT(*) FROM textbooks GROUP BY 1"
        ),
        note="CASE is first-match-wins, so the order of the WHEN branches is"
             " part of the logic, not a matter of taste. Test the narrowest"
             " band first. Put the 50 test ahead of the 100 test and every"
             " premium book matches it on the way past -- the 'premium' branch"
             " becomes unreachable and never appears at all. The check that"
             " catches it is arithmetic: do the bands sum to 30?",
        claims=[
            ("three bands covering all 30 textbooks",
             lambda rows, c: len(rows) == 3
             and sum(r[1] for r in rows) == 30),
        ],
    ),
    dict(
        id=4, ledger="Q285", concept="C7", tier="1 - Warm-up",
        title="Settled, waived, or still owing",
        prompt=(
            "Classify every payment into one of three states and count them:\n"
            "  'settled' if paid_on has a date\n"
            "  'waived'  if it has no paid_on and status is WAIVED\n"
            "  'owing'   otherwise\n\n"
            "All 122 payments land in exactly one state.\n\n"
            "Return: state, payments"
        ),
        solution=(
            "SELECT CASE WHEN paid_on IS NOT NULL THEN 'settled'"
            " WHEN status = 'WAIVED' THEN 'waived'"
            " ELSE 'owing' END, COUNT(*) FROM payments GROUP BY 1"
        ),
        trap_sql=(
            "SELECT CASE WHEN paid_on <> NULL THEN 'settled'"
            " WHEN status = 'WAIVED' THEN 'waived'"
            " ELSE 'owing' END, COUNT(*) FROM payments GROUP BY 1"
        ),
        note="<> NULL is never true, and neither is = NULL. Both evaluate to"
             " NULL, which CASE treats as not-matched, so that branch can never"
             " fire and every settled payment falls through to a later one. The"
             " only tests that work on a NULL are IS NULL and IS NOT NULL.",
        claims=[
            ("three states covering all 122 payments",
             lambda rows, c: len(rows) == 3
             and sum(r[1] for r in rows) == 122),
            ("settled matches the rows that have a paid_on",
             lambda rows, c: dict(rows)["settled"] == c.execute(
                 "SELECT COUNT(*) FROM payments WHERE paid_on IS NOT NULL"
             ).fetchone()[0]),
        ],
    ),
    dict(
        id=5, ledger="Q286", concept="C7", tier="1 - Warm-up",
        title="Everyone not funding themselves",
        prompt=(
            "Count students by funding band, excluding the self-funded, and"
            " counting the ones with NO band recorded as 'none'.\n\n"
            "46 of the 60 students are not self-funded -- twelve of them"
            " because they have no band at all.\n\n"
            "Return: band, students  ('grant', 'sponsor' or 'none')"
        ),
        solution=(
            "SELECT COALESCE(funding_band, 'none'), COUNT(*) FROM students"
            " WHERE funding_band IS NOT 'self' GROUP BY 1"
        ),
        trap_sql=(
            "SELECT COALESCE(funding_band, 'none'), COUNT(*) FROM students"
            " WHERE funding_band <> 'self' GROUP BY 1"
        ),
        note="funding_band <> 'self' drops the twelve unrecorded students"
             " without a word, because NULL <> 'self' is NULL rather than true."
             " ANY comparison on a nullable column silently excludes the NULLs."
             " SQLite's IS NOT is null-safe and reads the way you meant it; the"
             " portable spelling is"
             " (funding_band IS NULL OR funding_band <> 'self').",
        claims=[
            ("46 students in three bands, twelve unrecorded",
             lambda rows, c: sum(r[1] for r in rows) == 46
             and len(rows) == 3 and dict(rows)["none"] == 12),
        ],
    ),
    dict(
        id=6, ledger="Q287", concept="A2", tier="1 - Warm-up",
        title="Average page count, where it is known",
        prompt=(
            "One row per publisher: how many textbooks they have, how many of"
            " those record a page count, and the average of the page counts"
            " that exist.\n\n"
            "Three publishers have a book with no page count. The average must"
            " be over the recorded ones only. One table, no joins.\n\n"
            "Return: publisher, books, with_pages, avg_pages"
        ),
        solution=(
            "SELECT publisher, COUNT(*), COUNT(pages), ROUND(AVG(pages), 2)"
            " FROM textbooks GROUP BY publisher"
        ),
        trap_sql=(
            "SELECT publisher, COUNT(*), COUNT(pages),"
            " ROUND(SUM(pages) * 1.0 / COUNT(*), 2)"
            " FROM textbooks GROUP BY publisher"
        ),
        note="AVG already ignores NULLs -- it divides by the number of non-NULL"
             " values, not by the number of rows. Rebuilding it as SUM/COUNT(*)"
             " quietly puts the books with no page count into the denominator"
             " and drags those publishers' averages down. If you ever do want"
             " SUM over rows rather than values, write SUM(COALESCE(pages, 0))"
             " and say so.",
        claims=[
            ("five publishers, three of them missing a page count",
             lambda rows, c: len(rows) == 5
             and sum(1 for r in rows if r[2] < r[1]) == 3),
        ],
    ),
    # ======================================================= 2 First joins
    dict(
        id=7, ledger="Q288", concept="J2", tier="2 - First joins",
        title="Every course, scheduled or not",
        prompt=(
            "One row for every course in the catalogue: its id, code, and how"
            " many sections have ever been scheduled for it.\n\n"
            "Seven courses have never been scheduled. They must appear with 0,"
            " so all 34 courses come back.\n\n"
            "Return: course_id, code, sections"
        ),
        solution=(
            "SELECT c.course_id, c.code, COUNT(s.section_id) FROM courses c"
            " LEFT JOIN sections s ON s.course_id = c.course_id GROUP BY 1, 2"
        ),
        trap_sql=(
            "SELECT c.course_id, c.code, COUNT(s.section_id) FROM courses c"
            " JOIN sections s ON s.course_id = c.course_id GROUP BY 1, 2"
        ),
        note="An inner join can only return courses that matched, so the seven"
             " unscheduled ones vanish rather than showing 0 -- and 'the ones"
             " with none' is usually what the question is really about. Note"
             " the pairing: LEFT JOIN plus COUNT(a column from the right side)."
             " COUNT(*) there would give the unscheduled courses a 1.",
        claims=[
            ("all 34 courses, seven with none",
             lambda rows, c: len(rows) == 34
             and sum(1 for r in rows if r[2] == 0) == 7),
        ],
    ),
    dict(
        id=8, ledger="Q289", concept="J2", tier="2 - First joins",
        title="Online teaching per instructor",
        prompt=(
            "One row for every instructor: id, name, and how many sections they"
            " teach that are delivered ONLINE.\n\n"
            "Five instructors teach none. They must appear with 0, so all 16"
            " instructors come back.\n\n"
            "Return: instructor_id, name, online_sections"
        ),
        solution=(
            "SELECT i.instructor_id, i.name, COUNT(s.section_id)"
            " FROM instructors i LEFT JOIN sections s"
            " ON s.instructor_id = i.instructor_id AND s.delivery = 'online'"
            " GROUP BY 1, 2"
        ),
        trap_sql=(
            "SELECT i.instructor_id, i.name, COUNT(s.section_id)"
            " FROM instructors i LEFT JOIN sections s"
            " ON s.instructor_id = i.instructor_id"
            " WHERE s.delivery = 'online' GROUP BY 1, 2"
        ),
        note="A condition on the right-hand table has to go in the ON clause of"
             " a LEFT JOIN. In WHERE it runs AFTER the join has padded the"
             " unmatched instructors with NULLs, and NULL = 'online' is not"
             " true, so those rows are filtered straight back out and the outer"
             " join silently becomes an inner one.",
        claims=[
            ("all 16 instructors, five with none",
             lambda rows, c: len(rows) == 16
             and sum(1 for r in rows if r[2] == 0) == 5),
        ],
    ),
    dict(
        id=9, ledger="Q290", concept="J1", tier="2 - First joins",
        title="Courses that sit alongside each other",
        prompt=(
            "Pairs of courses in the same department at the same level.\n\n"
            "Each pair once, not twice, and no course paired with itself. Order"
            " each pair so that code_a belongs to the LOWER course_id. There"
            " are 4 pairs.\n\n"
            "Return: department_id, code_a, code_b"
        ),
        solution=(
            "SELECT a.department_id, a.code, b.code FROM courses a"
            " JOIN courses b ON b.department_id = a.department_id"
            " AND b.level = a.level AND b.course_id > a.course_id"
        ),
        trap_sql=(
            "SELECT a.department_id, a.code, b.code FROM courses a"
            " JOIN courses b ON b.department_id = a.department_id"
            " AND b.level = a.level AND b.course_id <> a.course_id"
        ),
        note="<> only stops a row pairing with itself; it still lets each pair"
             " through in both directions, so you get exactly twice as many"
             " rows as there are pairs. Use > (or <) on the id instead: it"
             " excludes the self-match AND fixes an order, so only one of the"
             " two directions survives.",
        claims=[
            ("four pairs, none a mirror of another",
             lambda rows, c: len(rows) == 4
             and len({frozenset((r[1], r[2])) for r in rows}) == 4),
        ],
    ),
    dict(
        id=10, ledger="Q291", concept="J2", tier="2 - First joins",
        title="Textbooks nobody assigns",
        prompt=(
            "Every textbook that appears on no course reading list at all.\n\n"
            "Write it as an outer join that keeps the non-matches, rather than"
            " with NOT IN. There are 6 such books.\n\n"
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
            ("6 books, none on any reading list",
             lambda rows, c: len(rows) == 6
             and not {r[0] for r in rows} & {
                 x[0] for x in c.execute(
                     "SELECT DISTINCT book_id FROM course_books")}),
        ],
    ),
    dict(
        id=11, ledger="Q292", concept="E1", tier="2 - First joins",
        title="Students who have reached level 4",
        prompt=(
            "Every student who has ever enrolled on a level-4 course.\n\n"
            "Courses sit under sections and sections carry the enrolment. One"
            " row per student, however many level-4 courses they took -- and"
            " some took two. 25 students qualify.\n\n"
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
            " JOIN courses c ON c.course_id = s.course_id WHERE c.level = 4"
        ),
        note="Joining down to courses to answer a question ABOUT students"
             " changes the grain: you get one row per qualifying enrolment, so"
             " a student who took two level-4 courses appears twice. EXISTS"
             " asks the question without changing what a row is -- it returns"
             " yes or no and stops at the first hit. SELECT DISTINCT would"
             " patch the join, but EXISTS says what you meant.",
        claims=[
            ("25 students, none listed twice",
             lambda rows, c: len(rows) == 25
             and len({r[0] for r in rows}) == 25),
            ("someone took two, so a plain join would double up",
             lambda rows, c: c.execute(
                 "SELECT MAX(n) FROM (SELECT COUNT(*) n FROM enrolments e"
                 " JOIN sections s ON s.section_id = e.section_id"
                 " JOIN courses c ON c.course_id = s.course_id"
                 " WHERE c.level = 4 GROUP BY e.student_id)").fetchone()[0] > 1),
        ],
    ),
    dict(
        id=12, ledger="Q293", concept="E1", tier="2 - First joins",
        title="Never taught online",
        prompt=(
            "Every instructor who has never taught a section delivered ONLINE."
            " Five of the sixteen qualify.\n\n"
            "Watch out: six online sections have no instructor assigned at all,"
            " which is what makes the obvious answer wrong.\n\n"
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
            ("five instructors, and some online sections are unstaffed",
             lambda rows, c: len(rows) == 5 and c.execute(
                 "SELECT COUNT(*) FROM sections WHERE delivery = 'online'"
                 " AND instructor_id IS NULL").fetchone()[0] == 6),
        ],
    ),
    # ========================================================= 3 Recursion
    dict(
        id=13, ledger="Q294", concept="R1", tier="3 - Recursion",
        title="Anil Chaudhary's line of mentors",
        prompt=(
            "Anil Chaudhary, then their mentor, then that person's mentor, and"
            " so on up to the instructor who has no mentor.\n\n"
            "Three rows: Anil themselves, then two above. Start with Anil in"
            " the anchor and follow mentor_id upward one hop at a time.\n\n"
            "Return: instructor_id, name"
        ),
        solution=(
            "WITH RECURSIVE up(id, name, mentor) AS ("
            " SELECT instructor_id, name, mentor_id FROM instructors"
            " WHERE name = 'Anil Chaudhary'"
            " UNION ALL"
            " SELECT i.instructor_id, i.name, i.mentor_id FROM instructors i"
            " JOIN up ON i.instructor_id = up.mentor)"
            " SELECT id, name FROM up"
        ),
        trap_sql=(
            "SELECT i.instructor_id, i.name FROM instructors i"
            " WHERE i.name = 'Anil Chaudhary'"
            " UNION ALL"
            " SELECT m.instructor_id, m.name FROM instructors i"
            " JOIN instructors m ON m.instructor_id = i.mentor_id"
            " WHERE i.name = 'Anil Chaudhary'"
        ),
        note="The gentlest shape there is: the anchor is one row, and the step"
             " is one join back to the CTE. Each pass climbs exactly one level"
             " and stops when it reaches the instructor whose mentor_id is"
             " NULL, because the join then matches nothing. A hand-written"
             " self-join gets you two rows and cannot reach the third without"
             " you adding another join by hand for every level.",
        claims=[
            ("three rows, ending at the instructor with no mentor",
             lambda rows, c: len(rows) == 3
             and c.execute("SELECT mentor_id FROM instructors WHERE"
                           " instructor_id = ?",
                           (rows[-1][0],)).fetchone()[0] is None),
        ],
    ),
    dict(
        id=14, ledger="Q295", concept="R1", tier="3 - Recursion",
        title="What Interaction Design needs, all the way down",
        prompt=(
            "Course DES301 'Interaction Design' has a prerequisite, and that"
            " has one of its own. List every course DES301 depends on, at any"
            " depth.\n\n"
            "This chain is a straight line -- exactly one prerequisite at each"
            " hop -- so it is two rows. DES301 itself is not in the answer.\n\n"
            "Return: code, title"
        ),
        solution=(
            "WITH RECURSIVE need(id) AS ("
            " SELECT requires_course_id FROM prerequisites"
            " WHERE course_id = (SELECT course_id FROM courses"
            " WHERE code = 'DES301')"
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
            " WHERE code = 'DES301')"
        ),
        note="A single join to prerequisites gives the DIRECT requirement and"
             " stops -- one row, where the answer is two. The recursion follows"
             " that first result onward. Same shape as question 13, pointed at"
             " a different table: anchor is one lookup, step is one join back"
             " to the CTE.",
        claims=[
            ("two courses, and DES301 is not one of them",
             lambda rows, c: len(rows) == 2
             and not any(r[0] == 'DES301' for r in rows)),
            ("DES301 has exactly one direct prerequisite",
             lambda rows, c: c.execute(
                 "SELECT COUNT(*) FROM prerequisites WHERE course_id ="
                 " (SELECT course_id FROM courses WHERE code = 'DES301')"
             ).fetchone()[0] == 1),
        ],
    ),
    dict(
        id=15, ledger="Q296", concept="R1", tier="3 - Recursion",
        title="What is blocked by Visual Communication",
        prompt=(
            "The other way round. Every course that requires DES101 'Visual"
            " Communication', directly or indirectly -- that is, every course a"
            " student could not take until they had passed it.\n\n"
            "Two courses. Same table and same shape as question 14, but you"
            " travel along the other column.\n\n"
            "Return: code, title"
        ),
        solution=(
            "WITH RECURSIVE blocked(id) AS ("
            " SELECT course_id FROM prerequisites"
            " WHERE requires_course_id = (SELECT course_id FROM courses"
            " WHERE code = 'DES101')"
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
            " WHERE code = 'DES101')"
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
             " other way. Get it half-swapped and you walk in one direction"
             " then the other, which is why the trap returns nothing at all.",
        claims=[
            ("two courses, both of which really do require DES101 eventually",
             lambda rows, c: len(rows) == 2),
        ],
    ),
    dict(
        id=16, ledger="Q297", concept="R1", tier="3 - Recursion",
        title="What Machine Learning needs, all the way down",
        prompt=(
            "The same question as 14, but on a course whose prerequisites"
            " branch: everything CMP401 'Machine Learning' depends on, at any"
            " depth.\n\n"
            "Five courses. Three are direct, and the rest are reached through"
            " them -- one course is reachable by TWO different paths and must"
            " still appear once.\n\n"
            "Return: code, title"
        ),
        solution=(
            "WITH RECURSIVE need(id) AS ("
            " SELECT requires_course_id FROM prerequisites"
            " WHERE course_id = (SELECT course_id FROM courses"
            " WHERE code = 'CMP401')"
            " UNION"
            " SELECT p.requires_course_id FROM prerequisites p"
            " JOIN need n ON p.course_id = n.id)"
            " SELECT c.code, c.title FROM courses c"
            " JOIN need ON need.id = c.course_id"
        ),
        trap_sql=(
            "WITH RECURSIVE need(id) AS ("
            " SELECT requires_course_id FROM prerequisites"
            " WHERE course_id = (SELECT course_id FROM courses"
            " WHERE code = 'CMP401')"
            " UNION ALL"
            " SELECT p.requires_course_id FROM prerequisites p"
            " JOIN need n ON p.course_id = n.id)"
            " SELECT c.code, c.title FROM courses c"
            " JOIN need ON need.id = c.course_id"
        ),
        note="This is where UNION and UNION ALL stop agreeing. CMP110 is"
             " reachable from CMP401 both through CMP201 and through CMP301, so"
             " UNION ALL walks it twice and the answer comes back with 8 rows"
             " instead of 5. UNION discards a row it has already produced and"
             " does not re-expand it. When you are collecting a SET of things,"
             " that is what you want; questions 13 and 14 were straight lines,"
             " so there it made no difference.",
        claims=[
            ("five courses, CMP401 not among them",
             lambda rows, c: len(rows) == 5
             and not any(r[0] == 'CMP401' for r in rows)),
            ("UNION ALL really would produce more rows here",
             lambda rows, c: c.execute(
                 "WITH RECURSIVE n(id) AS (SELECT requires_course_id FROM"
                 " prerequisites WHERE course_id = 7 UNION ALL SELECT"
                 " p.requires_course_id FROM prerequisites p JOIN n"
                 " ON p.course_id = n.id) SELECT COUNT(*) FROM n"
             ).fetchone()[0] > 5),
        ],
    ),
    # ============================================ 4 Dates, sets and pivots
    dict(
        id=17, ledger="Q298", concept="D1", tier="4 - Dates, sets and pivots",
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
            ("five rows, all a positive whole number of days",
             lambda rows, c: len(rows) == 5
             and all(isinstance(r[3], int) and r[3] > 0 for r in rows)),
        ],
    ),
    dict(
        id=18, ledger="Q299", concept="D1", tier="4 - Dates, sets and pivots",
        title="Assessment deadlines by month",
        prompt=(
            "One row per calendar month in which any assessment falls due: the"
            " month as 'YYYY-MM', and how many are due in it.\n\n"
            "The data spans two academic years, so the same month name recurs"
            " and the two must not be added together. There are 17 such"
            " months.\n\n"
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
            ("17 months, more than a single year could produce",
             lambda rows, c: len(rows) == 17),
            ("the counts total every assessment",
             lambda rows, c: sum(r[1] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM assessments").fetchone()[0]),
        ],
    ),
    dict(
        id=19, ledger="Q300", concept="D1", tier="4 - Dates, sets and pivots",
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
             " e.enrolled_on < t.starts_on would also have been right --"
             " '2025-01-04' really is less than '2025-01-13' alphabetically."
             " What is never right is ARITHMETIC on them. The trap subtracts,"
             " which coerces both to years and compares 2025 - 2025 = 0,"
             " quietly finding only the enrolments that crossed a new year.",
        claims=[
            ("all six terms, and fewer than every enrolment",
             lambda rows, c: len(rows) == 6
             and 0 < sum(r[2] for r in rows) < c.execute(
                 "SELECT COUNT(*) FROM enrolments").fetchone()[0]),
        ],
    ),
    dict(
        id=20, ledger="Q301", concept="S1", tier="4 - Dates, sets and pivots",
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
             " that is simply the wrong question. EXCEPT also dedupes on its"
             " own, so neither DISTINCT is strictly needed.",
        claims=[
            ("nine months, none with any enrolment",
             lambda rows, c: len(rows) == 9
             and not {r[0] for r in rows} & {
                 x[0] for x in c.execute(
                     "SELECT DISTINCT strftime('%Y-%m', enrolled_on)"
                     " FROM enrolments")}),
        ],
    ),
    dict(
        id=21, ledger="Q302", concept="S1", tier="4 - Dates, sets and pivots",
        title="Required reading on a first-year course",
        prompt=(
            "Textbooks that are BOTH marked required (required = 1) on some"
            " course AND appear on the reading list of a level-1 course.\n\n"
            "The two need not be the same course: a book required on a level-3"
            " course and merely recommended on a level-1 one still counts. Ten"
            " books qualify.\n\n"
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
             " though the sentence contains an 'and' -- because the two"
             " conditions apply to the same book, rather than being two lists"
             " to add together. Both operators dedupe, so neither needs a"
             " DISTINCT.",
        claims=[
            ("ten books, each required somewhere",
             lambda rows, c: len(rows) == 10 and all(
                 c.execute("SELECT COUNT(*) FROM course_books WHERE book_id = ?"
                           " AND required = 1", (r[0],)).fetchone()[0] > 0
                 for r in rows)),
        ],
    ),
    dict(
        id=22, ledger="Q303", concept="A1", tier="4 - Dates, sets and pivots",
        title="Enrolment status by term",
        prompt=(
            "One row per term, with the number of its enrolments in each of the"
            " three statuses side by side as columns.\n\n"
            "All six terms appear, and the three columns together account for"
            " every enrolment.\n\n"
            "Return: term_id, name, completed, active, withdrawn"
        ),
        solution=(
            "SELECT t.term_id, t.name,"
            " SUM(CASE WHEN e.status = 'completed' THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN e.status = 'active' THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN e.status = 'withdrawn' THEN 1 ELSE 0 END)"
            " FROM terms t JOIN sections s ON s.term_id = t.term_id"
            " JOIN enrolments e ON e.section_id = s.section_id"
            " GROUP BY 1, 2"
        ),
        trap_sql=(
            "SELECT t.term_id, t.name,"
            " COUNT(CASE WHEN e.status = 'completed' THEN 1 ELSE 0 END),"
            " COUNT(CASE WHEN e.status = 'active' THEN 1 ELSE 0 END),"
            " COUNT(CASE WHEN e.status = 'withdrawn' THEN 1 ELSE 0 END)"
            " FROM terms t JOIN sections s ON s.term_id = t.term_id"
            " JOIN enrolments e ON e.section_id = s.section_id"
            " GROUP BY 1, 2"
        ),
        note="Pick ONE of two shapes and stick to it: SUM(CASE WHEN c THEN 1"
             " ELSE 0 END) or COUNT(CASE WHEN c THEN 1 END). The mixture in the"
             " trap -- COUNT over an ELSE 0 -- counts every row, because 0 is a"
             " value and COUNT only skips NULL. All three columns come back"
             " identical to the row count, which is the tell.",
        claims=[
            ("six terms, and the columns total every enrolment",
             lambda rows, c: len(rows) == 6
             and sum(r[2] + r[3] + r[4] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM enrolments").fetchone()[0]),
        ],
    ),
    # ================================================== 5 Window functions
    dict(
        id=23, ledger="Q304", concept="W3", tier="5 - Window functions",
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
        id=24, ledger="Q305", concept="W1", tier="5 - Window functions",
        title="Billed so far",
        prompt=(
            "One row per calendar month in which anything was billed: the month"
            " as 'YYYY-MM', the amount billed in it, and the running total of"
            " everything billed up to and including that month.\n\n"
            "The running total on the last month equals the total of every"
            " payment in the table. 22 months.\n\n"
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
            ("22 months, last running total is every payment",
             lambda rows, c: len(rows) == 22
             and abs(max(r[2] for r in rows) - c.execute(
                 "SELECT SUM(amount) FROM payments").fetchone()[0]) < 0.01),
        ],
    ),
    dict(
        id=25, ledger="Q306", concept="W3", tier="5 - Window functions",
        title="Share of the enrolments by faculty",
        prompt=(
            "One row per faculty: the faculty, how many enrolments its"
            " departments' courses attracted, and that count as a percentage of"
            " all enrolments.\n\n"
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
        note="The mirror image of question 24. There you needed the window"
             " narrowed by ORDER BY; here you need it wide open. OVER () with"
             " nothing in it is every row, which is exactly the denominator a"
             " share needs. PARTITION BY faculty shrinks the window to the row"
             " itself, so every share comes out as 100%. Write 100.0, not 100 --"
             " integer division would truncate every answer.",
        claims=[
            ("four faculties summing to 100%",
             lambda rows, c: len(rows) == 4
             and abs(sum(r[2] for r in rows) - 100) < 0.05),
        ],
    ),
    dict(
        id=26, ledger="Q307", concept="W2", tier="5 - Window functions",
        title="The most recent run of each course",
        prompt=(
            "For every course that has ever been scheduled, its latest section"
            " by term. One row per course -- courses never scheduled do not"
            " appear, so 27 rows.\n\n"
            "No course runs twice in the same term, so 'latest' is never a"
            " tie.\n\n"
            "Return: course_id, section_id, term_id"
        ),
        solution=(
            "WITH r AS (SELECT course_id, section_id, term_id,"
            " ROW_NUMBER() OVER (PARTITION BY course_id"
            " ORDER BY term_id DESC) AS rn FROM sections)"
            " SELECT course_id, section_id, term_id FROM r WHERE rn = 1"
        ),
        trap_sql=(
            "WITH r AS (SELECT course_id, section_id, term_id,"
            " ROW_NUMBER() OVER (ORDER BY term_id DESC) AS rn FROM sections)"
            " SELECT course_id, section_id, term_id FROM r WHERE rn = 1"
        ),
        note="Without PARTITION BY the numbering runs straight through the"
             " whole table, so rn = 1 is the single latest section anywhere and"
             " you get one row instead of one per course. PARTITION BY restarts"
             " the count for each course -- it is the GROUP BY of the window"
             " world, except the detail rows survive.",
        claims=[
            ("27 courses, one row each",
             lambda rows, c: len(rows) == 27
             and len({r[0] for r in rows}) == len(rows)),
        ],
    ),
    dict(
        id=27, ledger="Q308", concept="W2", tier="5 - Window functions",
        title="Top of each programme, ties and all",
        prompt=(
            "The highest mark achieved in each programme, and who got it. Only"
            " graded enrolments count.\n\n"
            "Two programmes have two students tied on the top mark. Both must"
            " appear, so the answer is 11 rows across 9 programmes.\n\n"
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
             " exactly one row -- as in question 26 -- and RANK when you want"
             " everyone who earned the position.",
        claims=[
            ("11 rows across 9 programmes, so two are tied",
             lambda rows, c: len(rows) == 11
             and len({r[0] for r in rows}) == 9),
        ],
    ),
    # ============================================= 6 Grain and correlation
    dict(
        id=28, ledger="Q309", concept="E2", tier="6 - Grain and correlation",
        title="Bigger than its own department's average",
        prompt=(
            "Every course worth more credits than the average for ITS OWN"
            " department -- not more than the average across the whole"
            " catalogue.\n\n"
            "One row per course. Twelve qualify.\n\n"
            "Return: course_id, code, department_id, credits"
        ),
        solution=(
            "SELECT c.course_id, c.code, c.department_id, c.credits"
            " FROM courses c WHERE c.credits >"
            " (SELECT AVG(c2.credits) FROM courses c2"
            " WHERE c2.department_id = c.department_id)"
        ),
        trap_sql=(
            "SELECT c.course_id, c.code, c.department_id, c.credits"
            " FROM courses c"
            " WHERE c.credits > (SELECT AVG(credits) FROM courses)"
        ),
        note="The correlation is the single line WHERE c2.department_id ="
             " c.department_id. Without it the subquery runs once and every"
             " course is compared with the same number; with it the subquery is"
             " re-evaluated per row against that row's own department. A small"
             " course in a small department can beat its own average and lose"
             " to the global one, which is why the two answers differ.",
        claims=[
            ("twelve courses, from more than one department",
             lambda rows, c: len(rows) == 12
             and len({r[2] for r in rows}) > 1),
        ],
    ),
    dict(
        id=29, ledger="Q310", concept="C2", tier="6 - Grain and correlation",
        title="Students and assessments on each section",
        prompt=(
            "One row per section: how many students are enrolled on it, and how"
            " many assessments it has.\n\n"
            "The two are independent -- a section can have many of one and none"
            " of the other. A section with none of something shows 0, not NULL."
            " All 70 sections appear.\n\n"
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
             " 10x too big. COUNT(DISTINCT ...) would paper over it here, but a"
             " SUM could not. Two independent measures want two independent"
             " subqueries -- or two CTEs, each reduced to one row per section"
             " before they meet.",
        claims=[
            ("all 70 sections, and both totals match their tables",
             lambda rows, c: len(rows) == 70
             and sum(r[1] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM enrolments").fetchone()[0]
             and sum(r[2] for r in rows) == c.execute(
                 "SELECT COUNT(*) FROM assessments").fetchone()[0]),
        ],
    ),
    dict(
        id=30, ledger="Q311", concept="C2", tier="6 - Grain and correlation",
        title="What the library holds, by faculty",
        prompt=(
            "One row per faculty, with the total value of the library copies"
            " held on its courses' reading lists.\n\n"
            "Each course_books row is worth copies_held * list_price. Rows with"
            " no copies_held recorded contribute nothing. Every line must be"
            " priced on its own copies and its own book.\n\n"
            "Return: faculty, value"
        ),
        solution=(
            "SELECT d.faculty, ROUND(SUM(cb.copies_held * b.list_price), 2)"
            " FROM course_books cb"
            " JOIN textbooks b ON b.book_id = cb.book_id"
            " JOIN courses co ON co.course_id = cb.course_id"
            " JOIN departments d ON d.department_id = co.department_id"
            " GROUP BY 1"
        ),
        trap_sql=(
            "SELECT d.faculty,"
            " ROUND(SUM(cb.copies_held) * AVG(b.list_price), 2)"
            " FROM course_books cb"
            " JOIN textbooks b ON b.book_id = cb.book_id"
            " JOIN courses co ON co.course_id = cb.course_id"
            " JOIN departments d ON d.department_id = co.department_id"
            " GROUP BY 1"
        ),
        note="Do the arithmetic inside the aggregate, one row at a time, then"
             " add up: SUM(a * b), not SUM(a) * AVG(b). The two agree only if"
             " every row carries the same price, which is never true -- an"
             " expensive book held once and a cheap one held twenty times get"
             " averaged into a price neither of them has. This is the one that"
             " DISTINCT cannot rescue: unlike a count, a wrong SUM has no"
             " tidy-up available after the fact.",
        claims=[
            ("four faculties, and the total matches the whole join",
             lambda rows, c: len(rows) == 4 and abs(
                 sum(r[1] for r in rows) - c.execute(
                     "SELECT SUM(cb.copies_held * b.list_price)"
                     " FROM course_books cb JOIN textbooks b"
                     " ON b.book_id = cb.book_id").fetchone()[0]) < 0.5),
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
