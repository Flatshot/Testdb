"""Populate testdb with practice data for a further-education college.

Deterministic: the RNG is seeded and no wall-clock dates are used, so running
this twice produces byte-identical data. Safe to re-run -- it drops and
recreates the tables first, so a schema change is picked up.

    python seed.py

The gaps below are deliberate, not sloppiness. Questions about anti-joins,
NULL handling and COUNT need something real to find:

  * courses that are never scheduled, and courses with no prerequisites
  * sections with enrolments but no assessments, assessments but no
    enrolments, and neither
  * sections scheduled but not staffed (instructor_id NULL)
  * enrolments still active or withdrawn, so grade is NULL
  * students who never enrol on anything
  * textbooks on nobody's reading list
  * instructors with no formal pay grade, students with no funding band
  * payments waived or still due, so paid_on is NULL
  * an August gap every year, so "every month" needs a generated series
"""

import random
from datetime import date, timedelta

import db

SEED = 293

# Tables in dependency order; dropped in reverse so foreign keys stay satisfied.
TABLES = [
    "campuses",
    "departments",
    "instructors",
    "students",
    "courses",
    "prerequisites",
    "terms",
    "sections",
    "enrolments",
    "assessments",
    "textbooks",
    "course_books",
    "payments",
]

CAMPUSES = [
    ("Riverside", "Leeds", "2004-09-01"),
    ("Northgate", "Sheffield", "2009-09-01"),
    ("Kingsway", "Nottingham", "2013-09-01"),
    ("Harbour Point", "Hull", "2018-09-01"),
]

# (name, faculty, campus index)
DEPARTMENTS = [
    ("Computing", "Science & Technology", 0),
    ("Engineering", "Science & Technology", 0),
    ("Mathematics", "Science & Technology", 1),
    ("Business", "Business & Law", 1),
    ("Accounting", "Business & Law", 2),
    ("Design", "Arts & Humanities", 2),
    ("Languages", "Arts & Humanities", 3),
    ("Health Sciences", "Health & Care", 3),
    ("Nursing", "Health & Care", 0),
]

INSTRUCTOR_NAMES = [
    "Margaret Ashworth", "Devan Rao", "Sinead Fahey", "Peter Nowak",
    "Amara Diallo", "Joachim Brandt", "Ruth Ellery", "Yusuf Demir",
    "Clara Bassett", "Hiro Tanabe", "Ingrid Solberg", "Femi Adeyemi",
    "Rosalind Vane", "Tomas Kucera", "Bridget Moloney", "Anil Chaudhary",
]

STUDENT_FIRST = [
    "Alice", "Bilal", "Chloe", "Dmitri", "Esme", "Farhan", "Gemma", "Hugo",
    "Isla", "Jonah", "Kiera", "Lucas", "Maya", "Niall", "Orla", "Pavel",
    "Quinn", "Rhys", "Sofia", "Tariq", "Una", "Viktor", "Wren", "Xiomara",
    "Yannick", "Zara",
]
STUDENT_LAST = [
    "Attwood", "Barrow", "Chandra", "Doherty", "Ekstrom", "Fitzgerald",
    "Gallagher", "Hollis", "Ibrahim", "Jarvis", "Kowalski", "Lindqvist",
    "Mensah", "Novak", "Ogilvie", "Pereira", "Quinlan", "Rasmussen",
    "Sandoval", "Thackeray", "Uddin", "Voss", "Whitlock", "Yates",
]

PROGRAMMES = [
    "BSc Computing", "BEng Engineering", "BSc Mathematics",
    "BA Business", "BA Accounting", "BA Design", "BA Languages",
    "BSc Health Sciences", "BSc Nursing",
]

# (department index, level, code stem, title)
COURSES = [
    (0, 1, "CMP101", "Programming Foundations"),
    (0, 1, "CMP110", "Computer Systems"),
    (0, 2, "CMP201", "Data Structures"),
    (0, 2, "CMP210", "Databases"),
    (0, 3, "CMP301", "Algorithms"),
    (0, 3, "CMP310", "Distributed Systems"),
    (0, 4, "CMP401", "Machine Learning"),
    (1, 1, "ENG101", "Statics and Dynamics"),
    (1, 2, "ENG201", "Thermofluids"),
    (1, 3, "ENG301", "Control Engineering"),
    (1, 4, "ENG401", "Systems Design"),
    (2, 1, "MTH101", "Calculus"),
    (2, 1, "MTH110", "Linear Algebra"),
    (2, 2, "MTH201", "Probability"),
    (2, 3, "MTH301", "Numerical Methods"),
    (2, 4, "MTH401", "Stochastic Processes"),
    (3, 1, "BUS101", "Principles of Management"),
    (3, 2, "BUS201", "Operations"),
    (3, 3, "BUS301", "Strategy"),
    (4, 1, "ACC101", "Financial Accounting"),
    (4, 2, "ACC201", "Management Accounting"),
    (4, 3, "ACC301", "Audit and Assurance"),
    (5, 1, "DES101", "Visual Communication"),
    (5, 2, "DES201", "Typography"),
    (5, 3, "DES301", "Interaction Design"),
    (6, 1, "LAN101", "Spanish I"),
    (6, 2, "LAN201", "Spanish II"),
    (6, 3, "LAN301", "Translation Studies"),
    (7, 1, "HSC101", "Human Physiology"),
    (7, 2, "HSC201", "Public Health"),
    (7, 3, "HSC301", "Epidemiology"),
    (8, 1, "NUR101", "Foundations of Nursing"),
    (8, 2, "NUR201", "Clinical Practice"),
    (8, 3, "NUR301", "Acute Care"),
]

TERMS = [
    ("Autumn 2024", "2024-09-16", "2024-12-13"),
    ("Spring 2025", "2025-01-13", "2025-04-04"),
    ("Summer 2025", "2025-04-21", "2025-07-04"),
    ("Autumn 2025", "2025-09-15", "2025-12-12"),
    ("Spring 2026", "2026-01-12", "2026-04-02"),
    ("Summer 2026", "2026-04-20", "2026-07-03"),
]

ROOMS = ["A1.04", "A2.11", "B1.02", "B3.07", "C2.15", "D1.01", "D4.20",
         "Lab 1", "Lab 2", "Studio A"]
DELIVERY = ["in person", "online", "blended"]
ASSESSMENT_KINDS = ["essay", "exam", "project", "practical"]
FUNDING = ["self", "grant", "sponsor"]

BOOK_TITLES = [
    "Foundations of Computation", "The Pragmatic Engineer",
    "Discrete Mathematics in Practice", "Database Design Handbook",
    "Algorithms Illustrated", "Statistical Inference",
    "Thermodynamics for Engineers", "Control Theory Primer",
    "Management in Context", "Operations and Supply", "Strategy Cases",
    "Financial Reporting Standards", "Cost and Management Accounting",
    "Auditing Principles", "Grid Systems in Design", "Type and Layout",
    "Designing Interfaces", "Spanish Grammar in Use",
    "Advanced Spanish Composition", "Theories of Translation",
    "Anatomy and Physiology", "Public Health Foundations",
    "Epidemiology at a Glance", "Clinical Nursing Skills",
    "Acute Care Essentials", "Research Methods", "Academic Writing",
    "Data Visualisation", "Numerical Recipes", "Ethics in Practice",
]
PUBLISHERS = ["Aldgate Press", "Brookfield", "Cormorant Academic",
              "Deverell & Sons", "Eastgate"]


def _random_date(rng, start, end):
    return start + timedelta(days=rng.randrange((end - start).days + 1))


def _iso(d):
    return d.isoformat()


def seed():
    rng = random.Random(SEED)

    conn = db.connect()
    try:
        with conn:
            # Drop rather than DELETE so schema changes are picked up. Drop
            # EVERY table, not just the ones in TABLES -- when the schema is
            # replaced wholesale, tables from the previous one are otherwise
            # left behind in the file and show up in any schema browser.
            conn.execute("PRAGMA foreign_keys=OFF")
            existing = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
                " AND name NOT LIKE 'sqlite_%'")]
            for table in existing:
                conn.execute(f'DROP TABLE IF EXISTS "{table}"')
        conn.executescript(db.SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.execute("PRAGMA foreign_keys=ON")

        with conn:
            # --------------------------------------------------------- campuses
            conn.executemany(
                "INSERT INTO campuses (campus_id, name, city, opened_on)"
                " VALUES (?, ?, ?, ?)",
                [(i, n, c, o) for i, (n, c, o) in enumerate(CAMPUSES, 1)])

            # ------------------------------------------------------ departments
            dept_rows = []
            for did, (name, faculty, ci) in enumerate(DEPARTMENTS, 1):
                budget = round(rng.uniform(180_000, 940_000), 2)
                dept_rows.append((did, ci + 1, name, faculty, budget))
            conn.executemany(
                "INSERT INTO departments (department_id, campus_id, name,"
                " faculty, annual_budget) VALUES (?, ?, ?, ?, ?)", dept_rows)

            # ------------------------------------------------------ instructors
            # A three-level mentoring tree: one root, three who report to the
            # root, everyone else under those. Deep enough that a single
            # self-join cannot reach the bottom.
            instr_rows = []
            for iid, name in enumerate(INSTRUCTOR_NAMES, 1):
                dept = rng.randrange(1, len(DEPARTMENTS) + 1)
                hired = _random_date(rng, date(2011, 1, 1), date(2024, 6, 30))
                if iid == 1:
                    mentor = None
                elif iid <= 4:
                    mentor = 1
                else:
                    mentor = rng.randrange(2, 5)
                rate = round(rng.uniform(38.0, 82.0), 2)
                # A quarter have never been formally graded -- NULL, not 1.
                grade = None if rng.random() < 0.25 else rng.randrange(1, 6)
                instr_rows.append((iid, dept, name, _iso(hired), mentor,
                                   rate, grade))
            conn.executemany(
                "INSERT INTO instructors (instructor_id, department_id, name,"
                " hired_on, mentor_id, hourly_rate, pay_grade)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)", instr_rows)

            # --------------------------------------------------------- students
            student_rows = []
            used = set()
            for sid in range(1, 61):
                while True:
                    name = (STUDENT_FIRST[rng.randrange(len(STUDENT_FIRST))]
                            + " "
                            + STUDENT_LAST[rng.randrange(len(STUDENT_LAST))])
                    if name not in used:
                        used.add(name)
                        break
                campus = rng.randrange(1, len(CAMPUSES) + 1)
                joined = _random_date(rng, date(2024, 8, 1), date(2026, 4, 1))
                programme = PROGRAMMES[rng.randrange(len(PROGRAMMES))]
                # A sixth have no funding band recorded yet.
                band = None if rng.random() < 0.17 else FUNDING[rng.randrange(3)]
                student_rows.append((sid, name, campus, _iso(joined),
                                     programme, band))
            conn.executemany(
                "INSERT INTO students (student_id, name, campus_id,"
                " enrolled_on, programme, funding_band)"
                " VALUES (?, ?, ?, ?, ?, ?)", student_rows)

            # ---------------------------------------------------------- courses
            course_rows = []
            for cid, (di, level, code, title) in enumerate(COURSES, 1):
                credits = rng.choice([10, 15, 20, 30])
                course_rows.append((cid, di + 1, code, title, credits, level))
            conn.executemany(
                "INSERT INTO courses (course_id, department_id, code, title,"
                " credits, level) VALUES (?, ?, ?, ?, ?, ?)", course_rows)

            # ---------------------------------------------------- prerequisites
            # A course may only require STRICTLY lower levels, which makes the
            # graph acyclic by construction -- a recursive walk always ends.
            by_dept_level = {}
            for cid, (di, level, _code, _t) in enumerate(COURSES, 1):
                by_dept_level.setdefault((di, level), []).append(cid)
            prereq_rows = []
            for cid, (di, level, _code, _t) in enumerate(COURSES, 1):
                if level == 1:
                    continue
                # Always require something from the level immediately below, so
                # chains actually form: a level-4 course reaches level 1 in
                # three hops, which is what makes a recursive walk necessary
                # rather than decorative. Sometimes also reach further down,
                # so not every path from a course is the same length.
                direct = list(by_dept_level.get((di, level - 1), []))
                deeper = [c for lv in range(1, level - 1)
                          for c in by_dept_level.get((di, lv), [])]
                if direct:
                    rng.shuffle(direct)
                    prereq_rows.append((cid, direct[0]))
                if deeper and rng.random() < 0.45:
                    rng.shuffle(deeper)
                    prereq_rows.append((cid, deeper[0]))
            # Two cross-department requirements, so the graph is not just a set
            # of independent per-department chains.
            prereq_rows.append((7, 14))    # Machine Learning <- Probability
            prereq_rows.append((31, 14))   # Epidemiology     <- Probability
            conn.executemany(
                "INSERT INTO prerequisites (course_id, requires_course_id)"
                " VALUES (?, ?)", sorted(set(prereq_rows)))

            # ------------------------------------------------------------ terms
            conn.executemany(
                "INSERT INTO terms (term_id, name, starts_on, ends_on)"
                " VALUES (?, ?, ?, ?)",
                [(i, n, s, e) for i, (n, s, e) in enumerate(TERMS, 1)])

            # --------------------------------------------------------- sections
            # Five courses are never scheduled at all, so an anti-join has
            # something to find.
            never_scheduled = {6, 16, 22, 28, 34}
            section_rows = []
            sid = 0
            for tid in range(1, len(TERMS) + 1):
                for cid in range(1, len(COURSES) + 1):
                    if cid in never_scheduled:
                        continue
                    if rng.random() > 0.45:
                        continue
                    sid += 1
                    # One section in nine is scheduled but not yet staffed.
                    instr = (None if rng.random() < 0.11
                             else rng.randrange(1, len(INSTRUCTOR_NAMES) + 1))
                    section_rows.append((
                        sid, cid, tid, instr,
                        ROOMS[rng.randrange(len(ROOMS))],
                        rng.choice([18, 20, 24, 30, 36, 40]),
                        DELIVERY[rng.randrange(3)]))
            conn.executemany(
                "INSERT INTO sections (section_id, course_id, term_id,"
                " instructor_id, room, capacity, delivery)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)", section_rows)

            term_start = {i: date.fromisoformat(s)
                          for i, (_n, s, _e) in enumerate(TERMS, 1)}

            # ------------------------------------------------------- enrolments
            # Eight students never enrol on anything.
            enrollable = [s for s in range(1, 61) if s % 7 != 3][:52]
            enrol_rows = []
            eid = 0
            for s_id, c_id, t_id, *_rest in section_rows:
                # A tenth of sections take nobody at all.
                if rng.random() < 0.10:
                    continue
                take = rng.randrange(3, 12)
                for stu in rng.sample(enrollable, take):
                    eid += 1
                    start = term_start[t_id]
                    when = start + timedelta(days=rng.randrange(-21, 15))
                    roll = rng.random()
                    if roll < 0.68:
                        status, grade = "completed", rng.randrange(35, 99)
                    elif roll < 0.87:
                        status, grade = "active", None
                    else:
                        status, grade = "withdrawn", None
                    enrol_rows.append((eid, s_id, stu, _iso(when), status,
                                       grade))
            conn.executemany(
                "INSERT INTO enrolments (enrolment_id, section_id, student_id,"
                " enrolled_on, status, grade) VALUES (?, ?, ?, ?, ?, ?)",
                enrol_rows)

            # ------------------------------------------------------ assessments
            assess_rows = []
            aid = 0
            for s_id, _c, t_id, *_rest in section_rows:
                # A sixth of sections have no assessments recorded, which is a
                # DIFFERENT set from the ones with no students.
                if rng.random() < 0.16:
                    continue
                n = rng.randrange(2, 5)
                weights = [round(1.0 / n, 2)] * n
                for k in range(n):
                    aid += 1
                    kind = ASSESSMENT_KINDS[rng.randrange(4)]
                    due = term_start[t_id] + timedelta(
                        days=rng.randrange(28, 84))
                    assess_rows.append((
                        aid, s_id, f"{kind.title()} {k + 1}", kind,
                        weights[k], _iso(due)))
            conn.executemany(
                "INSERT INTO assessments (assessment_id, section_id, title,"
                " kind, weight, due_on) VALUES (?, ?, ?, ?, ?, ?)", assess_rows)

            # -------------------------------------------------------- textbooks
            book_rows = []
            for bid, title in enumerate(BOOK_TITLES, 1):
                price = round(rng.uniform(18.0, 145.0), 2)
                # A few have no page count recorded.
                pages = None if rng.random() < 0.12 else rng.randrange(180, 940)
                book_rows.append((bid, title,
                                  PUBLISHERS[rng.randrange(len(PUBLISHERS))],
                                  price, pages))
            conn.executemany(
                "INSERT INTO textbooks (book_id, title, publisher, list_price,"
                " pages) VALUES (?, ?, ?, ?, ?)", book_rows)

            # ----------------------------------------------------- course_books
            # Six textbooks end up on no reading list at all.
            listable = list(range(1, len(BOOK_TITLES) - 5))
            cb_rows = set()
            for cid in range(1, len(COURSES) + 1):
                if rng.random() < 0.12:
                    continue
                for bid in rng.sample(listable, rng.randrange(1, 4)):
                    cb_rows.add((cid, bid))
            cb_full = []
            for cid, bid in sorted(cb_rows):
                required = 1 if rng.random() < 0.6 else 0
                # A fifth have no library copy target set.
                copies = None if rng.random() < 0.20 else rng.randrange(0, 25)
                cb_full.append((cid, bid, required, copies))
            conn.executemany(
                "INSERT INTO course_books (course_id, book_id, required,"
                " copies_held) VALUES (?, ?, ?, ?)", cb_full)

            # --------------------------------------------------------- payments
            pay_rows = []
            pid = 0
            for stu in range(1, 61):
                for _ in range(rng.randrange(0, 5)):
                    pid += 1
                    billed = _random_date(rng, date(2024, 9, 1),
                                          date(2026, 6, 30))
                    amount = round(rng.uniform(120.0, 2400.0), 2)
                    roll = rng.random()
                    if roll < 0.62:
                        status = "PAID"
                        paid = _iso(billed + timedelta(
                            days=rng.randrange(1, 75)))
                    elif roll < 0.80:
                        status, paid = "DUE", None
                    elif roll < 0.96:
                        status, paid = "LATE", None
                    else:
                        status, paid = "WAIVED", None
                    pay_rows.append((pid, stu, _iso(billed), amount, status,
                                     paid))
            conn.executemany(
                "INSERT INTO payments (payment_id, student_id, billed_on,"
                " amount, status, paid_on) VALUES (?, ?, ?, ?, ?, ?)",
                pay_rows)
    finally:
        conn.close()

    return {t: n for t, n in _counts().items()}


def _counts():
    conn = db.connect()
    try:
        return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in TABLES}
    finally:
        conn.close()


if __name__ == "__main__":
    for table, n in seed().items():
        print(f"{table:>14}: {n:>5}")
    print(f"\nseeded {db.DB_PATH}")
