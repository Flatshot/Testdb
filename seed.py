"""Populate testdb with practice data for a public library service.

Deterministic: the RNG is seeded and no wall-clock dates are used, so running
this twice produces byte-identical data. Safe to re-run -- it drops every table
first, so a schema change is picked up.

    python seed.py

The gaps below are deliberate. Questions about anti-joins, NULL handling,
open intervals and COUNT need something real to find:

  * members who have never borrowed, and members with no postcode
  * books with no copies, copies never loaned, copies withdrawn
  * authors with no books in the catalogue
  * loans still out (returned_on NULL), some of them already overdue
  * holds still waiting -- neither fulfilled nor cancelled
  * fines unpaid
  * a branch with no manager
"""

import random
from datetime import date, datetime, timedelta

import db

SEED = 861

# Loans are spread across this window. The data ends at SNAPSHOT: a loan that
# would have come back after it is left open instead, a hold not yet dealt
# with by then is left waiting, and a fine not yet paid is left unpaid.
RANGE_START = date(2025, 1, 1)
RANGE_END = date(2026, 6, 30)
SNAPSHOT = RANGE_END

LOAN_DAYS = 21          # the standard loan
RENEWAL_DAYS = 14       # each renewal adds this to due_on
FINE_PER_DAY = 20       # pence per day late
FINE_CAP = 1000         # pence

TABLES = ["branches", "staff", "authors", "books", "copies", "members",
          "loans", "holds", "fines"]

BRANCHES = [("Central", "Leeds", "1902-05-12"), ("Northgate", "Leeds", "1961-09-01"),
            ("Riverside", "Wakefield", "1978-03-20"), ("Hilltop", "Bradford", "1994-11-04"),
            ("Eastfield", "Leeds", "2008-06-16"), ("Old Town", "Wakefield", "2019-02-25")]
NO_MANAGER = 6          # Old Town has no manager

FIRST = ["Aisha", "Bartholomew", "Cerys", "Dmitri", "Eleanor", "Farouk",
         "Grace", "Hamid", "Imogen", "Jonah", "Kwame", "Leila", "Marcus",
         "Nadia", "Oluwaseun", "Priya", "Quentin", "Rosa", "Samir", "Tamsin",
         "Umar", "Verity", "Wilfred", "Xiu", "Yusuf", "Zara"]
LAST = ["Achebe", "Baxter", "Chowdhury", "Dalgleish", "Ekwueme", "Fairweather",
        "Grzybowski", "Hollingsworth", "Iqbal", "Jankowski", "Khatri",
        "Lindqvist", "Mbeki", "Nakamura", "Okonjo", "Papadopoulos", "Quraishi",
        "Rasmussen", "Sowerby", "Tremblay", "Uddin", "Villanueva", "Whitcombe",
        "Yilmaz", "Zielinski"]
COUNTRIES = ["UK", "UK", "UK", "US", "US", "Ireland", "Nigeria", "India",
             "France", "Japan", "Canada", "Australia"]
GENRES = ["fiction", "fiction", "fiction", "history", "science", "children",
          "children", "poetry", "biography", "travel", "cookery"]
ADJ = ["Silent", "Last", "Hidden", "Winter", "Glass", "Iron", "Blue", "Lost",
       "Burning", "Northern", "Quiet", "Golden", "Paper", "Distant", "Broken",
       "Little", "Secret", "Wild", "Red", "Hollow", "Painted", "Salt", "Dark",
       "Green", "Early", "Long", "Small", "Bright", "Stone", "Open"]
NOUN = ["River", "House", "Garden", "Clock", "Map", "Harbour", "Orchard",
        "Letter", "Bridge", "Lantern", "Forest", "Island", "Road", "Tower",
        "Key", "Window", "Kitchen", "Mountain", "Voyage", "Season", "Door",
        "Library", "Market", "Shore", "Field", "Engine", "Bell", "Star",
        "Compass", "Path"]
FRAMES = ["The {a} {n}", "A {a} {n}", "{a} {n}", "The {n} of {a2} {n2}",
          "Notes from the {a} {n}", "{a} {n}s", "Beyond the {a} {n}",
          "A History of {a} {n}s", "The {a} {n} Cookbook", "Poems for a {a} {n}"]
POSTCODES = ["LS1", "LS2", "LS4", "LS6", "LS7", "LS8", "LS9", "LS11", "LS12",
             "LS13", "LS15", "LS16", "LS17", "BD3", "WF1"]


def _d(d):
    return d.isoformat()


def _title(rng, used):
    while True:
        f = rng.choice(FRAMES)
        t = f.format(a=rng.choice(ADJ), n=rng.choice(NOUN),
                     a2=rng.choice(ADJ), n2=rng.choice(NOUN))
        if t not in used:
            used.add(t)
            return t


def seed():
    rng = random.Random(SEED)
    conn = db.connect()
    try:
        with conn:
            conn.execute("PRAGMA foreign_keys=OFF")
            for t in [r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                    " AND name NOT LIKE 'sqlite_%'")]:
                conn.execute(f'DROP TABLE IF EXISTS "{t}"')
        conn.executescript(db.SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.execute("PRAGMA foreign_keys=ON")

        # ---- branches -----------------------------------------------------
        with conn:
            conn.executemany(
                "INSERT INTO branches (branch_id, name, town, opened_on) VALUES (?,?,?,?)",
                [(i + 1, n, t, o) for i, (n, t, o) in enumerate(BRANCHES)])

        # ---- staff: a manager at every branch but one ----------------------
        staff = []
        for b in range(1, len(BRANCHES) + 1):
            roles = (["librarian"] * 2 + ["assistant"] * 2) if b == NO_MANAGER \
                else (["manager"] + ["librarian"] * 2 + ["assistant"] * 2)
            if b == 1:
                roles += ["librarian", "assistant"]        # Central is bigger
            for role in roles:
                hired = RANGE_START - timedelta(days=rng.randint(200, 9000))
                pay = {"manager": rng.randint(38000, 46000),
                       "librarian": rng.randint(26000, 34000),
                       "assistant": rng.randint(20000, 24500)}[role]
                staff.append((f"{rng.choice(FIRST)} {rng.choice(LAST)}", b, role,
                              _d(hired), pay))
        with conn:
            conn.executemany(
                "INSERT INTO staff (name, branch_id, role, hired_on, salary)"
                " VALUES (?,?,?,?,?)", staff)

        # ---- authors: 120, of whom some have no books ---------------------
        authors = [(f"{rng.choice(FIRST)} {rng.choice(LAST)}", rng.randint(1850, 1990),
                    rng.choice(COUNTRIES)) for _ in range(120)]
        with conn:
            conn.executemany(
                "INSERT INTO authors (name, born_year, country) VALUES (?,?,?)", authors)
        unpublished = set(rng.sample(range(1, 121), 10))
        writers = [a for a in range(1, 121) if a not in unpublished]

        # ---- books: 600 titles --------------------------------------------
        used = set()
        books = []
        for _ in range(600):
            author = rng.choice(writers)
            born = authors[author - 1][1]
            year = min(2025, rng.randint(born + 25, born + 70))
            books.append((_title(rng, used), author, year, rng.choice(GENRES),
                          rng.randint(60, 900)))
        with conn:
            conn.executemany(
                "INSERT INTO books (title, author_id, published_year, genre, pages)"
                " VALUES (?,?,?,?,?)", books)
        no_copies = set(rng.sample(range(1, 601), 20))

        # ---- copies: 1 to 8 per book, spread over the branches ------------
        copies = []
        for book in range(1, 601):
            if book in no_copies:
                continue
            for _ in range(rng.choice([1, 2, 2, 3, 3, 4, 5, 6, 8])):
                acquired = RANGE_START - timedelta(days=rng.randint(30, 5000))
                cond = rng.choice(["good"] * 6 + ["worn"] * 3 + ["damaged"])
                withdrawn = None
                if rng.random() < 0.05:
                    withdrawn = _d(RANGE_START + timedelta(days=rng.randint(0, 540)))
                copies.append((book, rng.randint(1, len(BRANCHES)), _d(acquired),
                               cond, withdrawn))
        with conn:
            conn.executemany(
                "INSERT INTO copies (book_id, branch_id, acquired_on, condition,"
                " withdrawn_on) VALUES (?,?,?,?,?)", copies)

        # ---- members: 1500, some who never borrow --------------------------
        members = []
        for _ in range(1500):
            born = date(1930, 1, 1) + timedelta(days=rng.randint(0, 33000))
            joined = date(2015, 1, 1) + timedelta(days=rng.randint(0, 4000))
            joined = min(joined, SNAPSHOT)
            pc = None if rng.random() < 0.08 else rng.choice(POSTCODES)
            members.append((f"{rng.choice(FIRST)} {rng.choice(LAST)}", _d(born), _d(joined),
                            rng.randint(1, len(BRANCHES)), pc))
        with conn:
            conn.executemany(
                "INSERT INTO members (name, born_on, joined_on, home_branch_id,"
                " postcode_area) VALUES (?,?,?,?,?)", members)
        never = set(rng.sample(range(1, 1501), 200))
        borrowers = [m for m in range(1, 1501) if m not in never]
        # a few heavy readers, so top-N questions have a clear top
        heavy = rng.sample(borrowers, 30)

        # ---- loans: one copy at a time, with gaps between ------------------
        loans = []
        for cid, (book, branch, acquired, cond, withdrawn) in enumerate(copies, start=1):
            if rng.random() < 0.04:
                continue                                    # never loaned
            end = date.fromisoformat(withdrawn) if withdrawn else SNAPSHOT
            day = RANGE_START + timedelta(days=rng.randint(0, 60))
            while day < end:
                member = rng.choice(heavy) if rng.random() < 0.25 else rng.choice(borrowers)
                renewals = rng.choice([0, 0, 0, 1, 1, 2])
                due = day + timedelta(days=LOAN_DAYS + RENEWAL_DAYS * renewals)
                kept = int(rng.expovariate(1 / 16)) + 1
                kept = min(kept, 90)
                back = day + timedelta(days=kept)
                if back > SNAPSHOT:
                    back_s = None
                else:
                    back_s = _d(back)
                    if back > end:
                        break                               # withdrawn before return
                loans.append((cid, member, _d(day), _d(due), back_s, renewals))
                if back_s is None:
                    break
                day = back + timedelta(days=rng.randint(1, 60))
        with conn:
            conn.executemany(
                "INSERT INTO loans (copy_id, member_id, loaned_on, due_on, returned_on,"
                " renewals) VALUES (?,?,?,?,?,?)", loans)

        # ---- fines: a late return costs 20p a day, capped -----------------
        fines = []
        for lid, (cid, member, loaned, due, back, renewals) in enumerate(loans, start=1):
            if back is None:
                continue
            late = (date.fromisoformat(back) - date.fromisoformat(due)).days
            if late <= 0:
                continue
            amount = min(late * FINE_PER_DAY, FINE_CAP)
            paid = None
            if rng.random() < 0.7:
                pd = date.fromisoformat(back) + timedelta(days=rng.randint(0, 45))
                paid = _d(pd) if pd <= SNAPSHOT else None
            fines.append((lid, amount, back, paid))
        with conn:
            conn.executemany(
                "INSERT INTO fines (loan_id, amount_pence, issued_on, paid_on)"
                " VALUES (?,?,?,?)", fines)

        # ---- holds: queues on the popular books ----------------------------
        popular = rng.sample([b for b in range(1, 601) if b not in no_copies], 150)
        holds = []
        for _ in range(1500):
            book = rng.choice(popular)
            placed = datetime.combine(RANGE_START, datetime.min.time()) + timedelta(
                minutes=rng.randint(0, 546 * 24 * 60))
            fulfilled = cancelled = None
            r = rng.random()
            wait = timedelta(days=rng.randint(1, 40))
            if r < 0.6:
                when = (placed + wait).date()
                fulfilled = _d(when) if when <= SNAPSHOT else None
            elif r < 0.8:
                when = (placed + wait).date()
                cancelled = _d(when) if when <= SNAPSHOT else None
            holds.append((book, rng.choice(borrowers), placed.strftime("%Y-%m-%d %H:%M"),
                          rng.randint(1, len(BRANCHES)), fulfilled, cancelled))
        with conn:
            conn.executemany(
                "INSERT INTO holds (book_id, member_id, placed_at, branch_id,"
                " fulfilled_on, cancelled_on) VALUES (?,?,?,?,?,?)", holds)
    finally:
        conn.close()


def _counts():
    conn = db.connect()
    try:
        return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in TABLES}
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
    for t, n in _counts().items():
        print(f"  {t:>12}: {n:>7}")
    print(f"\nseeded {db.DB_PATH}")
