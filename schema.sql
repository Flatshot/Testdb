-- Schema for testdb: a public library service.
-- Applied by db.init_db(); every statement is safe to re-run.
--
-- The fifth schema in this repo, after a college, a field-service workshop,
-- a railway and a district hospital. A library keeps the shapes the hospital
-- taught -- INTERVALS, open ends, a hierarchy of sorts -- and adds two of its
-- own: QUEUES and MONEY OWED.
--
--   loans                 loaned_on .. returned_on, with a due_on in between.
--                         NULL returned_on means the book is still out; a
--                         return after due_on is LATE, and a late return
--                         raises a fine
--   holds                 a QUEUE: members waiting for a book, ordered by
--                         placed_at, each hold ending in a fulfilment, a
--                         cancellation, or neither yet
--   fines                 money in whole pence, issued when a loan came back
--                         late, paid or not yet paid
--   copies                a book is a title; a copy is a physical thing at
--                         one branch, in some condition, perhaps withdrawn
--
-- Carried over on purpose, so familiar questions have a home:
--
--   books.author_id       one-to-many, with authors who have written nothing
--                         in this catalogue
--   members.home_branch_id, copies.branch_id
--                         two different foreign keys to the same table, so a
--                         loan can be AWAY from the member's home branch
--   staff.role            a category with a natural order ('manager' <
--                         'librarian' < 'assistant')
--   dates are 'YYYY-MM-DD' text; holds.placed_at is 'YYYY-MM-DD HH:MM'.
--                         julianday() turns either into a number.
--
-- Deliberate gaps: members who have never borrowed, books with no copies,
-- copies never loaned, copies withdrawn, authors with no books, loans not
-- yet returned, holds neither fulfilled nor cancelled, fines unpaid, a
-- branch with no manager, and members with no recorded postcode.

CREATE TABLE IF NOT EXISTS branches (
    branch_id INTEGER PRIMARY KEY,
    name      TEXT    NOT NULL UNIQUE,
    town      TEXT    NOT NULL,
    opened_on TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS staff (
    staff_id  INTEGER PRIMARY KEY,
    name      TEXT    NOT NULL,
    branch_id INTEGER NOT NULL REFERENCES branches(branch_id),
    role      TEXT    NOT NULL CHECK (role IN ('manager', 'librarian', 'assistant')),
    hired_on  TEXT    NOT NULL,
    -- annual salary in whole pounds
    salary    INTEGER NOT NULL CHECK (salary > 0)
);

CREATE TABLE IF NOT EXISTS authors (
    author_id INTEGER PRIMARY KEY,
    name      TEXT    NOT NULL,
    born_year INTEGER NOT NULL,
    country   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS books (
    book_id        INTEGER PRIMARY KEY,
    title          TEXT    NOT NULL,
    author_id      INTEGER NOT NULL REFERENCES authors(author_id),
    published_year INTEGER NOT NULL,
    genre          TEXT    NOT NULL CHECK (genre IN ('fiction', 'history', 'science',
                                                    'children', 'poetry', 'biography',
                                                    'travel', 'cookery')),
    pages          INTEGER NOT NULL CHECK (pages > 0)
);

CREATE TABLE IF NOT EXISTS copies (
    copy_id      INTEGER PRIMARY KEY,
    book_id      INTEGER NOT NULL REFERENCES books(book_id),
    branch_id    INTEGER NOT NULL REFERENCES branches(branch_id),
    acquired_on  TEXT    NOT NULL,
    condition    TEXT    NOT NULL CHECK (condition IN ('good', 'worn', 'damaged')),
    -- NULL while the copy is still on the shelves
    withdrawn_on TEXT
);

CREATE TABLE IF NOT EXISTS members (
    member_id      INTEGER PRIMARY KEY,
    name           TEXT    NOT NULL,
    born_on        TEXT    NOT NULL,
    joined_on      TEXT    NOT NULL,
    home_branch_id INTEGER NOT NULL REFERENCES branches(branch_id),
    -- NULL where never recorded
    postcode_area  TEXT
);

CREATE TABLE IF NOT EXISTS loans (
    loan_id     INTEGER PRIMARY KEY,
    copy_id     INTEGER NOT NULL REFERENCES copies(copy_id),
    member_id   INTEGER NOT NULL REFERENCES members(member_id),
    loaned_on   TEXT    NOT NULL,
    -- three weeks from the loan, plus two per renewal
    due_on      TEXT    NOT NULL,
    -- NULL while the book is still out
    returned_on TEXT,
    renewals    INTEGER NOT NULL DEFAULT 0 CHECK (renewals BETWEEN 0 AND 2)
);

CREATE TABLE IF NOT EXISTS holds (
    hold_id      INTEGER PRIMARY KEY,
    book_id      INTEGER NOT NULL REFERENCES books(book_id),
    member_id    INTEGER NOT NULL REFERENCES members(member_id),
    placed_at    TEXT    NOT NULL,
    -- the branch the member wants to collect from
    branch_id    INTEGER NOT NULL REFERENCES branches(branch_id),
    -- at most one of these is set; both NULL while the member is waiting
    fulfilled_on TEXT,
    cancelled_on TEXT,
    CHECK (fulfilled_on IS NULL OR cancelled_on IS NULL)
);

CREATE TABLE IF NOT EXISTS fines (
    fine_id      INTEGER PRIMARY KEY,
    loan_id      INTEGER NOT NULL REFERENCES loans(loan_id),
    -- whole pence: 20 a day late, capped
    amount_pence INTEGER NOT NULL CHECK (amount_pence > 0),
    issued_on    TEXT    NOT NULL,
    -- NULL while unpaid
    paid_on      TEXT
);

CREATE INDEX IF NOT EXISTS idx_staff_branch     ON staff(branch_id);
CREATE INDEX IF NOT EXISTS idx_books_author     ON books(author_id);
CREATE INDEX IF NOT EXISTS idx_books_title      ON books(title COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_copies_book      ON copies(book_id);
CREATE INDEX IF NOT EXISTS idx_copies_branch    ON copies(branch_id);
CREATE INDEX IF NOT EXISTS idx_members_branch   ON members(home_branch_id);
CREATE INDEX IF NOT EXISTS idx_loans_copy       ON loans(copy_id, loaned_on);
CREATE INDEX IF NOT EXISTS idx_loans_member     ON loans(member_id);
CREATE INDEX IF NOT EXISTS idx_loans_due        ON loans(due_on);
CREATE INDEX IF NOT EXISTS idx_holds_book       ON holds(book_id, placed_at);
CREATE INDEX IF NOT EXISTS idx_holds_member     ON holds(member_id);
CREATE INDEX IF NOT EXISTS idx_fines_loan       ON fines(loan_id);
