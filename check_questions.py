"""Guard the question set.

Structural checks (exercises.py vs QUESTIONS.md):
  * every exercise has a ledger id that exists in the ledger, plus a concept,
    a trap_sql and a note
  * no ledger id or title is used twice
  * every ledger row marked "ex N" points at an exercise that exists
  * ledger ids are unique and contiguous
  * any top-N question taking more than one row carries an ORDER BY tiebreak,
    since a tie at the boundary would otherwise make the answer ambiguous

Behavioural checks (against testdb.db, read-only):
  * every solution runs and returns at least one row
  * every trap_sql is graded WRONG -- a trap the grader accepts is a question
    that teaches nothing, and this is what catches it
  * every exercise carrying plan_requires/plan_forbids has a solution whose
    own EXPLAIN QUERY PLAN satisfies them, and a trap that violates them --
    efficiency questions return identical rows either way, so the plan is the
    only thing that can distinguish right from wrong
  * every claim a prompt makes about the data actually holds -- stated ranges,
    row counts, "these rows appear with 0". trap_sql proves a query wrong; only
    this catches a prompt that describes data the database does not contain

    py check_questions.py
"""

import re
import sqlite3
import textwrap
import sys
from pathlib import Path

import db
import exercises as ex

LEDGER = Path(__file__).resolve().parent / "QUESTIONS.md"
ROW = re.compile(r"^\|\s*(Q\d{3})\s*\|(.*?)\|(.*?)\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$")
TRAILING_LIMIT = re.compile(r"\bLIMIT\s+(\d+)\s*$", re.IGNORECASE)
ORDER_BY = re.compile(r"\bORDER\s+BY\b(.*?)\s+LIMIT\b", re.IGNORECASE | re.DOTALL)


def parse_ledger():
    """Return {id: {'gui': ...}} from every markdown table in the file."""
    rows = {}
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        m = ROW.match(line)
        if m:
            qid, _concept, _question, gui, _rest = m.groups()
            rows[qid] = {"gui": gui.strip()}
    return rows


def run(conn, sql):
    """(rows, error). A trap that errors counts as rejected, not as a pass.

    Time-limited: an authoring slip in a recursive step would otherwise hang
    the checker instead of reporting a broken question.
    """
    try:
        with db.time_limit(conn):
            return db.fetch_capped(conn.execute(sql)), None
    except (db.QueryTimeout, db.TooManyRows) as exc:
        return None, str(exc)
    except sqlite3.Error as exc:
        return None, str(exc)


def main():
    problems = []
    ledger = parse_ledger()
    if not ledger:
        print("could not parse any rows out of QUESTIONS.md")
        return 1

    nums = sorted(int(q[1:]) for q in ledger)
    if nums != list(range(1, len(nums) + 1)):
        problems.append(f"ledger ids are not contiguous from Q001: {nums[:3]}...{nums[-3:]}")

    seen_ids, seen_titles = {}, {}
    for e in ex.EXERCISES:
        qid = e.get("ledger")
        if not qid:
            problems.append(f"exercise {e['id']} ({e['title']}) has no ledger id")
        else:
            if qid not in ledger:
                problems.append(f"exercise {e['id']} points at {qid}, not in the ledger")
            if qid in seen_ids:
                problems.append(f"{qid} claimed by exercises {seen_ids[qid]} and {e['id']}")
            seen_ids[qid] = e["id"]
        # The GUI panel caps at QUESTION_MAX_LINES; a prompt past that would
        # have its tail hidden, and the tail is the "Return:" line.
        wrapped = sum(max(1, len(textwrap.wrap(line, 76)))
                      for line in e["prompt"].split("\n"))
        if wrapped > 14:
            problems.append(
                f"exercise {e['id']} prompt is {wrapped} lines wrapped at 76 cols; "
                f"the GUI panel would hide the tail, including the Return: line")
        if "Return:" not in e["prompt"]:
            problems.append(f"exercise {e['id']} prompt never says what to Return")

        for field in ("concept", "trap_sql", "note"):
            if not e.get(field):
                problems.append(f"exercise {e['id']} has no {field}")

        key = e["title"].strip().lower()
        if key in seen_titles:
            problems.append(f"duplicate title {e['title']!r} on {seen_titles[key]} and {e['id']}")
        seen_titles[key] = e["id"]

    # A top-N question ordered by a single key is ambiguous the moment two rows
    # tie at the cut-off: the engine may return either, so there is no one right
    # answer to grade against. LIMIT 1 is exempt -- verify those by hand.
    for e in ex.EXERCISES:
        sql = " ".join(e["solution"].split())
        m = TRAILING_LIMIT.search(sql)
        if not m or int(m.group(1)) <= 1:
            continue
        clause = ORDER_BY.search(sql)
        if not clause or "," not in clause.group(1):
            problems.append(
                f"exercise {e['id']} takes LIMIT {m.group(1)} with a single ORDER BY key; "
                f"a tie at the boundary would make the answer ambiguous")

    by_ex = {e["id"]: e.get("ledger") for e in ex.EXERCISES}
    for qid, row in ledger.items():
        m = re.fullmatch(r"ex\s*(\d+)", row["gui"])
        if not m:
            continue
        eid = int(m.group(1))
        if eid not in by_ex:
            problems.append(f"{qid} claims exercise {eid}, which does not exist")
        elif by_ex[eid] != qid:
            problems.append(f"{qid} claims exercise {eid}, but it points at {by_ex[eid]}")

    # --- behavioural ------------------------------------------------------
    conn = sqlite3.connect(f"file:{db.DB_PATH}?mode=ro", uri=True)
    traps_by_error = traps_by_result = claims_checked = 0
    traps_by_plan = plans_checked = 0
    try:
        for e in ex.EXERCISES:
            rows, err = run(conn, e["solution"])
            if err:
                problems.append(f"exercise {e['id']} solution failed: {err}")
                continue
            if not rows:
                problems.append(f"exercise {e['id']} solution returns no rows")

            # Claims assert that what the PROMPT says about the data is actually
            # true -- a stated range, a row count, a "these appear with 0" case.
            # trap_sql proves a query is wrong; nothing else checks whether the
            # question describes reality, and prompts have drifted from the data
            # twice now.
            for says, holds in e.get("claims", ()):
                try:
                    if not holds(rows, conn):
                        problems.append(
                            f"exercise {e['id']} ({e['title']}): prompt claim is FALSE "
                            f"-- {says}")
                    else:
                        claims_checked += 1
                except Exception as exc:
                    problems.append(
                        f"exercise {e['id']} claim {says!r} could not be evaluated: {exc}")

            # An efficiency question asserts something about the query PLAN,
            # because its slow and fast forms return identical rows. Check the
            # reference actually takes the route it demands -- otherwise the
            # question is unanswerable.
            if e.get("plan_requires") or e.get("plan_forbids"):
                ok, why = ex.plan_ok(e, ex.query_plan(conn, e["solution"]))
                if not ok:
                    problems.append(
                        f"exercise {e['id']} ({e['title']}): its own solution "
                        f"fails its plan assertion -- {why}")
                else:
                    plans_checked += 1

            trap_rows, trap_err = run(conn, e["trap_sql"])
            if trap_err:
                traps_by_error += 1
                continue
            passed, _ = ex.compare([tuple(r) for r in trap_rows], [tuple(r) for r in rows])
            if passed and (e.get("plan_requires") or e.get("plan_forbids")):
                # Returning the right rows is not enough for these: the trap is
                # SUPPOSED to return them, and be rejected on its plan.
                passed, _ = ex.plan_ok(e, ex.query_plan(conn, e["trap_sql"]))
                if not passed:
                    traps_by_plan += 1
                    continue
            if passed:
                problems.append(
                    f"exercise {e['id']} ({e['title']}): trap_sql grades as CORRECT, "
                    f"so the question does not actually test its concept")
            else:
                traps_by_result += 1
    finally:
        conn.close()

    linked = sum(1 for r in ledger.values() if r["gui"].startswith("ex"))
    print(f"ledger entries : {len(ledger)}")
    print(f"exercises      : {len(ex.EXERCISES)}")
    print(f"linked to GUI  : {linked}")
    print(f"traps rejected : "
          f"{traps_by_error + traps_by_result + traps_by_plan} / {len(ex.EXERCISES)} "
          f"({traps_by_error} by SQL error, {traps_by_result} by wrong result, "
          f"{traps_by_plan} by wrong query plan)")
    print(f"plan assertions: {plans_checked} solutions take the route they demand")
    print(f"prompt claims  : {claims_checked} verified against the data")

    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
