"""SQLite connection handling for testdb.

Every caller should go through connect() so the same pragmas are applied on
each connection. Paths are resolved relative to this file, not the current
working directory, so the database is the same one no matter where you run from.
"""

import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB_PATH = HERE / "testdb.db"
SCHEMA_PATH = HERE / "schema.sql"

# A recursive CTE whose step never stops runs forever. busy_timeout does not
# help -- that governs lock contention, not how long a statement may run.
# The 30 reference solutions together take about 180ms against the current
# data, so this is roughly two orders of magnitude above anything legitimate --
# but it is deliberately generous rather than tight, because exploring a
# 67,000-row table by hand turns up slow queries that are not mistakes.
QUERY_TIMEOUT_SECONDS = 15.0

# How many SQLite virtual-machine steps between deadline checks. Small enough
# that the abort feels immediate, large enough that the callback is noise.
PROGRESS_STEPS = 10_000

# The timeout alone bounds the spin but not the memory: a runaway CTE feeds
# fetchall() at a few hundred MB a second, so fifteen seconds is several
# gigabytes before the deadline fires. Stop reading rows well before that.
#
# This has to sit ABOVE the largest table, not merely above the largest
# expected ANSWER -- otherwise "SELECT * FROM observations" trips a guard meant
# for runaways. The biggest table in any schema this repo has had held under
# 100,000 rows, so 250,000 leaves room to browse any table whole (and to join
# a couple of them) while still catching an unbounded recursion long before
# memory matters.
MAX_ROWS = 250_000


def connect(db_path=None):
    """Open a connection with the pragmas this project relies on.

    journal_mode=WAL is stored in the database file, but foreign_keys and
    busy_timeout are per-connection and reset every time, so they have to be
    set here on each connect -- foreign keys are off by default in SQLite and
    fail silently if you forget.
    """
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


class QueryTimeout(Exception):
    """A statement ran past QUERY_TIMEOUT_SECONDS and was interrupted."""


class TooManyRows(Exception):
    """A statement produced more than MAX_ROWS rows and was cut off."""


def fetch_capped(cur, max_rows=MAX_ROWS):
    """fetchall(), but refusing to build a list without end.

    Reads one row past the cap so the difference between 'exactly at the
    limit' and 'runaway' is knowable rather than guessed.
    """
    rows = cur.fetchmany(max_rows + 1)
    if len(rows) > max_rows:
        raise TooManyRows(
            f"query produced more than {max_rows:,} rows and was stopped -- if"
            f" it uses WITH RECURSIVE, check the step has a stop condition")
    return rows


@contextmanager
def time_limit(conn, seconds=QUERY_TIMEOUT_SECONDS):
    """Abort any statement on conn that runs longer than `seconds`.

    SQLite calls the progress handler every PROGRESS_STEPS virtual-machine
    instructions; returning non-zero aborts the running statement. That is the
    only way out of a runaway recursive CTE -- without it the query never
    returns, and fetchall() grows the row list at a few hundred MB a second
    until the process dies.

    The deadline is per-block, not per-connection, so it has to be re-armed
    around each statement. sqlite3 reports the abort as a plain
    OperationalError('interrupted'), which is indistinguishable from other
    errors at the call site, so it is re-raised here as QueryTimeout.
    """
    deadline = time.monotonic() + seconds
    conn.set_progress_handler(
        lambda: 1 if time.monotonic() > deadline else 0, PROGRESS_STEPS)
    try:
        yield
    except sqlite3.OperationalError as exc:
        if "interrupted" in str(exc).lower() and time.monotonic() > deadline:
            raise QueryTimeout(
                f"query ran longer than {seconds:g}s and was stopped -- if it"
                f" uses WITH RECURSIVE, check the step has a stop condition"
            ) from exc
        raise
    finally:
        conn.set_progress_handler(None, 0)


def sandbox(db_path=None):
    """A private, writable, in-memory copy of the database.

    The writable questions ask for INSERT, UPDATE, DELETE, triggers and views,
    and those have to run somewhere that is not the practice database. This
    copies the whole file into memory -- a few milliseconds for 11MB -- so
    nothing a script does can outlive the copy. The GUI keeps one per
    question across Runs and drops it on Reset or a change of question;
    grading always takes a fresh one.

    ATTACH is denied so a script cannot reach the real file by name. Foreign
    keys are on, as in connect(), so a DELETE that would orphan rows fails the
    way it should rather than silently succeeding.
    """
    src = sqlite3.connect(f"file:{db_path or DB_PATH}?mode=ro", uri=True)
    try:
        # isolation_level=None is autocommit: the module opens no transaction
        # of its own, so a script's BEGIN, SAVEPOINT, ROLLBACK and COMMIT run
        # exactly as written instead of colliding with an implicit one.
        conn = sqlite3.connect(":memory:", isolation_level=None)
        src.backup(conn)
    finally:
        src.close()
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.set_authorizer(
        lambda action, *_: sqlite3.SQLITE_DENY
        if action == sqlite3.SQLITE_ATTACH else sqlite3.SQLITE_OK)
    return conn


def split_statements(script):
    """Split a script into complete statements, respecting trigger bodies.

    Splitting on ';' breaks CREATE TRIGGER, whose BEGIN ... END holds
    semicolons of its own. sqlite3.complete_statement knows the grammar, so
    lines are accumulated until it says the buffer is a whole statement.
    """
    out, buf = [], ""
    for line in script.splitlines(keepends=True):
        buf += line
        if sqlite3.complete_statement(buf):
            out.append(buf.strip())
            buf = ""
    if buf.strip():
        out.append(buf.strip().rstrip(";") + ";")
    return [s for s in out if s.strip(";").strip()]


def run_script(conn, script, seconds=QUERY_TIMEOUT_SECONDS):
    """Run each statement of `script` on conn, under the time limit.

    Returns (statements, changes, last_rows, last_headers): how many
    statements ran, how many rows the DML touched, and the result of the last
    statement if it produced one -- so a script that ends in a SELECT shows
    what it did. Errors propagate: a failed statement is the caller's news.
    """
    statements = split_statements(script)
    before = conn.total_changes
    last_rows, last_headers = None, None
    for stmt in statements:
        with time_limit(conn, seconds):
            cur = conn.execute(stmt)
            if cur.description is not None:
                last_headers = [d[0] for d in cur.description]
                last_rows = fetch_capped(cur)
            else:
                last_rows, last_headers = None, None
    return len(statements), conn.total_changes - before, last_rows, last_headers


@contextmanager
def transaction(db_path=None):
    """Connection that commits on clean exit and rolls back on exception."""
    conn = connect(db_path)
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db(db_path=None):
    """Apply schema.sql. Idempotent -- safe to call on every startup."""
    conn = connect(db_path)
    try:
        with conn:
            conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"initialized {DB_PATH}")
