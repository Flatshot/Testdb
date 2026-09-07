-- Schema for testdb: a further-education college.
-- Applied by db.init_db(); every statement is safe to re-run.
--
-- The shape is chosen to punish specific mistakes, not just to model a college.
-- The central one is GRAIN: a section has TWO independent children, so a
-- question touching both in one query block is a trap.
--
--   sections 1--0..n enrolments   who is taking it, one row per student
--   sections 1--0..n assessments  what it is marked on, one row per piece
--
--        joining enrolments AND assessments multiplies BOTH:
--        20 students x 3 assessments = 60 rows, so COUNT(students) is 3x too
--        big and SUM(weight) is 20x too big. Each branch must be reduced to
--        one row per section BEFORE the two meet.
--
--   courses *--* courses via prerequisites
--                                 a real dependency GRAPH, not an org chart:
--                                 a course may require several others, and a
--                                 course may be required by several others.
--                                 Walking it needs a recursive CTE, and the
--                                 depth differs by which path you take.
--   campuses 1--n departments 1--n courses 1--n sections 1--n enrolments
--                                 a five-deep chain; counting departments
--                                 after joining down it needs DISTINCT
--   students 1--0..n enrolments   the other side of the many-to-many
--   students 1--0..n payments     second child of students, so joining
--                                 payments and enrolments fans out too
--   instructors --> instructors   self-reference; mentor_id NULL at the top
--   courses *--* textbooks via course_books   composite key, nullable columns
--   terms                         a closed date dimension, so "every term"
--                                 questions do not need a generated series --
--                                 but "every month" ones still do
--   nullable numeric columns      AVG skips NULLs; NULL eats arithmetic
--   INTEGER measures              integer division truncates in SQLite
--
-- Deliberate gaps: some courses are never scheduled, some sections have no
-- students, some have no assessments, some have neither, some sections have no
-- instructor assigned, some enrolments have no grade yet, some students never
-- enrol, some textbooks are on no reading list. Anti-joins and NULL handling
-- need something real to find.

CREATE TABLE IF NOT EXISTS campuses (
    campus_id INTEGER PRIMARY KEY,
    name      TEXT NOT NULL UNIQUE,
    city      TEXT NOT NULL,
    opened_on TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS departments (
    department_id INTEGER PRIMARY KEY,
    campus_id     INTEGER NOT NULL REFERENCES campuses(campus_id),
    name          TEXT    NOT NULL,
    faculty       TEXT    NOT NULL,
    annual_budget REAL    NOT NULL CHECK (annual_budget > 0)
);

CREATE TABLE IF NOT EXISTS instructors (
    instructor_id INTEGER PRIMARY KEY,
    department_id INTEGER NOT NULL REFERENCES departments(department_id),
    name          TEXT    NOT NULL,
    hired_on      TEXT    NOT NULL,
    -- NULL for the one instructor nobody mentors; a self-reference otherwise
    mentor_id     INTEGER REFERENCES instructors(instructor_id),
    hourly_rate   REAL    NOT NULL CHECK (hourly_rate > 0),
    -- NULL where no formal grade has been assigned yet
    pay_grade     INTEGER CHECK (pay_grade IS NULL
                                 OR pay_grade BETWEEN 1 AND 5)
);

CREATE TABLE IF NOT EXISTS students (
    student_id  INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL,
    campus_id   INTEGER NOT NULL REFERENCES campuses(campus_id),
    enrolled_on TEXT    NOT NULL,
    programme   TEXT    NOT NULL,
    -- NULL for applicants who have not yet been assigned a funding band
    funding_band TEXT CHECK (funding_band IS NULL
                             OR funding_band IN ('self', 'grant', 'sponsor'))
);

CREATE TABLE IF NOT EXISTS courses (
    course_id     INTEGER PRIMARY KEY,
    department_id INTEGER NOT NULL REFERENCES departments(department_id),
    code          TEXT    NOT NULL UNIQUE,
    title         TEXT    NOT NULL,
    credits       INTEGER NOT NULL CHECK (credits > 0),
    level         INTEGER NOT NULL CHECK (level BETWEEN 1 AND 4)
);

-- The dependency graph. A course may require many; a course may be required by
-- many. No row ever points a course at itself.
CREATE TABLE IF NOT EXISTS prerequisites (
    course_id          INTEGER NOT NULL REFERENCES courses(course_id),
    requires_course_id INTEGER NOT NULL REFERENCES courses(course_id),
    PRIMARY KEY (course_id, requires_course_id),
    CHECK (course_id <> requires_course_id)
);

CREATE TABLE IF NOT EXISTS terms (
    term_id   INTEGER PRIMARY KEY,
    name      TEXT NOT NULL UNIQUE,
    starts_on TEXT NOT NULL,
    ends_on   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sections (
    section_id    INTEGER PRIMARY KEY,
    course_id     INTEGER NOT NULL REFERENCES courses(course_id),
    term_id       INTEGER NOT NULL REFERENCES terms(term_id),
    -- NULL where the section is scheduled but not yet staffed
    instructor_id INTEGER REFERENCES instructors(instructor_id),
    room          TEXT    NOT NULL,
    capacity      INTEGER NOT NULL CHECK (capacity > 0),
    delivery      TEXT    NOT NULL CHECK (delivery IN ('in person', 'online',
                                                       'blended'))
);

CREATE TABLE IF NOT EXISTS enrolments (
    enrolment_id INTEGER PRIMARY KEY,
    section_id   INTEGER NOT NULL REFERENCES sections(section_id),
    student_id   INTEGER NOT NULL REFERENCES students(student_id),
    enrolled_on  TEXT    NOT NULL,
    status       TEXT    NOT NULL CHECK (status IN ('active', 'completed',
                                                    'withdrawn')),
    -- NULL while the enrolment is still active or was withdrawn
    grade        INTEGER CHECK (grade IS NULL OR grade BETWEEN 0 AND 100),
    UNIQUE (section_id, student_id)
);

CREATE TABLE IF NOT EXISTS assessments (
    assessment_id INTEGER PRIMARY KEY,
    section_id    INTEGER NOT NULL REFERENCES sections(section_id),
    title         TEXT    NOT NULL,
    kind          TEXT    NOT NULL CHECK (kind IN ('essay', 'exam', 'project',
                                                   'practical')),
    weight        REAL    NOT NULL CHECK (weight > 0 AND weight <= 1),
    due_on        TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS textbooks (
    book_id    INTEGER PRIMARY KEY,
    title      TEXT    NOT NULL,
    publisher  TEXT    NOT NULL,
    list_price REAL    NOT NULL CHECK (list_price >= 0),
    -- NULL where nobody has recorded the page count
    pages      INTEGER CHECK (pages IS NULL OR pages > 0)
);

CREATE TABLE IF NOT EXISTS course_books (
    course_id INTEGER NOT NULL REFERENCES courses(course_id),
    book_id   INTEGER NOT NULL REFERENCES textbooks(book_id),
    required  INTEGER NOT NULL CHECK (required IN (0, 1)),
    -- NULL where the department has not set a copy target for the library
    copies_held INTEGER CHECK (copies_held IS NULL OR copies_held >= 0),
    PRIMARY KEY (course_id, book_id)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(student_id),
    billed_on  TEXT    NOT NULL,
    amount     REAL    NOT NULL CHECK (amount >= 0),
    status     TEXT    NOT NULL CHECK (status IN ('PAID', 'DUE', 'LATE',
                                                  'WAIVED')),
    -- NULL unless the payment actually settled
    paid_on    TEXT
);

CREATE INDEX IF NOT EXISTS idx_dept_campus     ON departments(campus_id);
CREATE INDEX IF NOT EXISTS idx_instr_dept      ON instructors(department_id);
CREATE INDEX IF NOT EXISTS idx_instr_mentor    ON instructors(mentor_id);
CREATE INDEX IF NOT EXISTS idx_students_campus ON students(campus_id);
CREATE INDEX IF NOT EXISTS idx_courses_dept    ON courses(department_id);
CREATE INDEX IF NOT EXISTS idx_prereq_requires ON prerequisites(requires_course_id);
CREATE INDEX IF NOT EXISTS idx_sections_course ON sections(course_id);
CREATE INDEX IF NOT EXISTS idx_sections_term   ON sections(term_id);
CREATE INDEX IF NOT EXISTS idx_sections_instr  ON sections(instructor_id);
CREATE INDEX IF NOT EXISTS idx_enrol_section   ON enrolments(section_id);
CREATE INDEX IF NOT EXISTS idx_enrol_student   ON enrolments(student_id);
CREATE INDEX IF NOT EXISTS idx_enrol_date      ON enrolments(enrolled_on);
CREATE INDEX IF NOT EXISTS idx_assess_section  ON assessments(section_id);
CREATE INDEX IF NOT EXISTS idx_books_book      ON course_books(book_id);
CREATE INDEX IF NOT EXISTS idx_payments_stu    ON payments(student_id);

-- Indexes that exist so the efficiency questions have something to hit or
-- miss. Each one can be used or defeated depending on how a query is written,
-- which is the whole point: the index is not the thing that makes a query
-- fast, being ABLE to use it is.
--   students(name COLLATE NOCASE)
--                           a prefix LIKE can seek this; a leading % cannot.
--                           The NOCASE collation is required: LIKE is
--                           case-insensitive by default, so a BINARY index
--                           cannot serve it and SQLite falls back to a scan.
--   enrolments(status,grade) a composite -- usable from the LEFT only, so a
--                            filter on status alone seeks and one on grade
--                            alone does not
CREATE INDEX IF NOT EXISTS idx_students_name   ON students(name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_enrol_status    ON enrolments(status, grade);
