"""Run ad-hoc SQL against testdb and print the result as a table.

    python q.py "SELECT name, unit_cost FROM parts LIMIT 5"
    python q.py -f myquery.sql
    python q.py            # interactive; blank line runs, \\q quits

Read-only by default -- pass --write to allow INSERT/UPDATE/DELETE, so a
stray statement during practice cannot quietly mangle the data set.
"""

import argparse
import sys

import db

WRITE_KEYWORDS = ("insert", "update", "delete", "drop", "alter", "create", "replace")


def render(rows, headers):
    if not rows:
        return "(no rows)"
    table = [headers] + [["" if v is None else str(v) for v in r] for r in rows]
    widths = [max(len(row[i]) for row in table) for i in range(len(headers))]
    sep = "-+-".join("-" * w for w in widths)
    out = [" | ".join(h.ljust(w) for h, w in zip(headers, widths)), sep]
    out += [" | ".join(c.ljust(w) for c, w in zip(r, widths)) for r in table[1:]]
    out.append(f"({len(rows)} row{'s' if len(rows) != 1 else ''})")
    return "\n".join(out)


def run(sql, allow_write=False):
    if not allow_write:
        first = sql.strip().lstrip("(").split(None, 1)[0].lower() if sql.strip() else ""
        if first in WRITE_KEYWORDS:
            return f"refusing to run a {first.upper()} without --write"
    conn = db.connect()
    try:
        with conn, db.time_limit(conn):
            cur = conn.execute(sql)
            if cur.description is None:
                return f"ok ({cur.rowcount} row(s) affected)"
            return render(db.fetch_capped(cur), [d[0] for d in cur.description])
    except Exception as exc:
        # QueryTimeout lands here too, carrying its own explanation.
        return f"error: {exc}"
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("sql", nargs="?", help="SQL to run")
    ap.add_argument("-f", "--file", help="read SQL from a file")
    ap.add_argument("--write", action="store_true", help="allow statements that modify data")
    args = ap.parse_args()

    if args.file:
        print(run(open(args.file, encoding="utf-8").read(), args.write))
    elif args.sql:
        print(run(args.sql, args.write))
    else:
        print("testdb interactive. Blank line runs the buffer, \\q quits.")
        buf = []
        while True:
            try:
                line = input("... " if buf else "sql> ")
            except EOFError:
                break
            if line.strip() in (r"\q", "quit", "exit"):
                break
            if line.strip():
                buf.append(line)
                continue
            if buf:
                print(run("\n".join(buf), args.write))
                buf = []
    return 0


if __name__ == "__main__":
    sys.exit(main())
