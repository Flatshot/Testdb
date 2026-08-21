"""SQLite connection handling for testdb.

Every caller should go through connect() so the same pragmas are applied on
each connection. Paths are resolved relative to this file, not the current
working directory, so the database is the same one no matter where you run from.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB_PATH = HERE / "testdb.db"
SCHEMA_PATH = HERE / "schema.sql"


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
