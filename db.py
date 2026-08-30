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
# help -- that governs lock contention, not how long a statement may run -- and
# the practice queries all finish in single-digit milliseconds, so a ceiling
# this far above them cannot fire on a legitimate answer.
QUERY_TIMEOUT_SECONDS = 5.0

# How many SQLite virtual-machine steps between deadline checks. Small enough
# that the abort feels immediate, large enough that the callback is noise.
PROGRESS_STEPS = 10_000

# The timeout alone bounds the spin but not the memory: a runaway CTE feeds
# fetchall() at a few hundred MB a second, so five seconds is still north of a
# gigabyte before the deadline fires. Stop reading rows well before that. The
# largest reference answer in the set is under 100 rows, so this is orders of
# magnitude above anything a real answer produces.
MAX_ROWS = 50_000


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
